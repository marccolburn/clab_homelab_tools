"""Cisco NX-OS driver over an interactive ssh shell (paramiko).

NX-OS has no candidate configuration and no NETCONF-style load/commit
the way Junos does: configuration is a sequence of lines entered in
`configure terminal`, applied as they are typed, and persisted with
`copy running-config startup-config`. So this driver:

* MERGES only. `override`/`replace` are refused with a clear message —
  replacing a running config on NX-OS means `configure replace` from a
  file on bootflash, which is a different workflow (and a reload risk on
  a virtual switch). Removing a line means sending its `no` form.
* Treats any `%`-prefixed response (`% Invalid command`, `% Incomplete
  command`, `% Ambiguous command`) as a failed line and reports which
  line, so a typo in one place does not pass silently as "loaded".
* Persists after a successful load, which is what `load_config` means
  for the Juniper driver too (it commits).

It exists so `clab-tools node config -f configs/dc1-leaf1.txt --node
dc1-leaf1` works on a `cisco_n9kv` node the way it does on a vJunos one
— the kind is what the registry dispatches on.
"""

import logging
import re
import socket
import time
from typing import Any, Dict, List, Optional, Tuple

import paramiko

from clab_tools.node.drivers.base import (
    BaseNodeDriver,
    CommandResult,
    ConfigFormat,
    ConfigLoadMethod,
    ConfigResult,
    ConnectionParams,
)
from clab_tools.node.drivers.registry import register_driver

logger = logging.getLogger(__name__)

# `switch#`, `switch(config)#`, `switch(config-if)#`, `switch>` — the
# hostname may carry dots and dashes; a trailing space is optional
PROMPT_RE = re.compile(r"(?m)^[\w.\-]+(?:\([\w\-]+\))?[#>]\s*$")
ERROR_RE = re.compile(r"^\s*%\s*\S.*$|^\s*(?:ERROR|Invalid) .*$", re.M | re.I)
# lines that are comments or noise in a saved NX-OS config
SKIP_LINE_RE = re.compile(r"^\s*(?:!|#|$)")
# `show running-config` headers NX-OS emits above a saved config
HEADER_RE = re.compile(r"^\s*(?:!Command:|!Running configuration|!Time:|version \d)")


@register_driver("CiscoNxosDriver")
class CiscoNxosDriver(BaseNodeDriver):
    """NX-OS driver: ssh shell, `configure terminal`, `copy run start`."""

    def __init__(self, connection_params: ConnectionParams):
        super().__init__(connection_params)
        self.client: Optional[paramiko.SSHClient] = None
        self.shell = None
        self._read_timeout = float(connection_params.timeout or 30)

    # -- session -----------------------------------------------------------

    def connect(self) -> None:
        if self._connected:
            return
        p = self.connection_params
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            kwargs: Dict[str, Any] = {
                "hostname": p.host,
                "port": p.port,
                "username": p.username,
                "timeout": p.timeout or 30,
                "banner_timeout": p.timeout or 30,
                "auth_timeout": p.timeout or 30,
                "look_for_keys": False,
                "allow_agent": False,
            }
            if p.password:
                kwargs["password"] = p.password
            elif p.private_key_file:
                kwargs["key_filename"] = p.private_key_file
            client.connect(**kwargs)
            shell = client.invoke_shell(width=511, height=1000)
            shell.settimeout(self._read_timeout)
            self.client, self.shell = client, shell
            self._connected = True
            self._read_until_prompt()          # the login banner + first prompt
            self._send("terminal length 0")
            self._send("terminal width 511")
            logger.debug(f"Connected to {p.host} (NX-OS)")
        except (paramiko.SSHException, socket.error, OSError) as e:
            self.client, self.shell, self._connected = None, None, False
            raise ConnectionError(f"Failed to connect: {e}")

    def disconnect(self) -> None:
        if self.client is not None:
            try:
                if self.shell is not None:
                    self.shell.close()
                self.client.close()
                logger.debug(f"Disconnected from {self.connection_params.host}")
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Error during disconnect: {e}")
            finally:
                self.client, self.shell, self._connected = None, None, False

    def is_connected(self) -> bool:
        return self._connected and self.shell is not None

    @staticmethod
    def _normalise(text: str) -> str:
        """NX-OS ends lines with `\r\n` and, before a prompt, sends a BARE
        `\r` (`…\r\n\rdc1-leaf2# `). A multiline `^` only matches after
        `\n`, so the prompt after that `\r` was invisible and every line
        waited out the read timeout (found on the first real push,
        2026-09-09). Every `\r` becomes a line break before matching."""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _read_until_prompt(self, timeout: Optional[float] = None) -> str:
        """Everything the box says up to its next prompt."""
        deadline = time.time() + (timeout or self._read_timeout)
        buf = ""
        while True:
            if self.shell.recv_ready():
                chunk = self.shell.recv(65535)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="replace")
                if PROMPT_RE.search(self._normalise(buf).rstrip("\n") + "\n"):
                    break
                continue
            if time.time() > deadline:
                raise TimeoutError(
                    f"{self.connection_params.host}: no prompt within "
                    f"{timeout or self._read_timeout:.0f}s; last output: "
                    f"{buf[-200:]!r}")
            time.sleep(0.05)
        return self._normalise(buf)

    def _send(self, line: str, timeout: Optional[float] = None) -> str:
        """One line in, the box's answer out — echo and prompt stripped."""
        self.shell.send(line + "\n")
        out = self._read_until_prompt(timeout)
        lines = [l for l in out.split("\n") if l.strip()]
        # drop the echoed command (first line) and the trailing prompt
        if lines and lines[0].strip() == line.strip():
            lines = lines[1:]
        elif lines and line.strip() and lines[0].strip().endswith(line.strip()):
            lines = lines[1:]
        while lines and PROMPT_RE.match(lines[-1] + "\n"):
            lines.pop()
        return "\n".join(lines)

    # -- commands ------------------------------------------------------------

    def execute_command(
        self, command: str, timeout: Optional[int] = None
    ) -> CommandResult:
        if not self.is_connected():
            raise ConnectionError("Not connected to device")
        start = time.time()
        try:
            out = self._send(command, timeout=timeout)
            err = ERROR_RE.search(out)
            return CommandResult(
                node_name=self.connection_params.host,
                command=command,
                output=out.strip(),
                error=err.group(0).strip() if err else None,
                exit_code=1 if err else 0,
                duration=time.time() - start,
            )
        except (TimeoutError, socket.timeout, OSError) as e:
            return CommandResult(
                node_name=self.connection_params.host,
                command=command,
                output="",
                error=f"Command failed: {e}",
                exit_code=1,
                duration=time.time() - start,
            )

    def execute_commands(
        self, commands: List[str], timeout: Optional[int] = None
    ) -> List[CommandResult]:
        return [self.execute_command(c, timeout) for c in commands]

    # -- configuration --------------------------------------------------------

    @staticmethod
    def config_lines(config_content: str) -> List[str]:
        """The lines worth sending: comments, blank lines and the headers
        a saved running-config carries are dropped; indentation stays
        (NX-OS ignores it, and it keeps the diff readable)."""
        out = []
        for raw in config_content.splitlines():
            if SKIP_LINE_RE.match(raw) or HEADER_RE.match(raw):
                continue
            out.append(raw.rstrip())
        return out

    def load_config(
        self,
        config_content: str,
        format: ConfigFormat = ConfigFormat.TEXT,
        method: ConfigLoadMethod = ConfigLoadMethod.MERGE,
        commit_comment: Optional[str] = None,
    ) -> ConfigResult:
        if not self.is_connected():
            raise ConnectionError("Not connected to device")
        host = self.connection_params.host
        if format != ConfigFormat.TEXT:
            return ConfigResult(
                node_name=host, success=False,
                message="NX-OS takes CLI text only",
                error=f"format {format.value!r} is not an NX-OS configuration format",
            )
        if method != ConfigLoadMethod.MERGE:
            return ConfigResult(
                node_name=host, success=False,
                message="NX-OS has no candidate configuration",
                error=(f"method {method.value!r} is not supported on NX-OS: "
                       f"lines are applied as entered. Use merge, and send the "
                       f"`no` form of anything to remove."),
            )
        lines = self.config_lines(config_content)
        if not lines:
            return ConfigResult(node_name=host, success=True,
                                message="No configuration lines to load")
        failed: List[Tuple[str, str]] = []
        applied = 0
        try:
            out = self._send("configure terminal")
            if ERROR_RE.search(out):
                return ConfigResult(node_name=host, success=False,
                                    message="Could not enter configuration mode",
                                    error=out.strip())
            for ln in lines:
                out = self._send(ln)
                err = ERROR_RE.search(out)
                if err:
                    failed.append((ln.strip(), err.group(0).strip()))
                else:
                    applied += 1
            self._send("end")
        except (TimeoutError, socket.timeout, OSError) as e:
            return ConfigResult(node_name=host, success=False,
                                message="Configuration load failed",
                                error=str(e))
        if failed:
            detail = "; ".join(f"{l!r}: {e}" for l, e in failed[:10])
            if len(failed) > 10:
                detail += f"; … {len(failed) - 10} more"
            return ConfigResult(
                node_name=host, success=False,
                message=f"{len(failed)} of {len(lines)} lines rejected "
                        f"({applied} applied and still in the running config)",
                error=detail,
            )
        save = self.commit_config(commit_comment)
        if not save.success:
            return save
        return ConfigResult(
            node_name=host, success=True,
            message=f"{applied} lines applied and saved to startup-config",
            diff="\n".join(lines),
        )

    def load_config_from_file(
        self,
        device_file_path: str,
        format: ConfigFormat = ConfigFormat.TEXT,
        method: ConfigLoadMethod = ConfigLoadMethod.MERGE,
        commit_comment: Optional[str] = None,
    ) -> ConfigResult:
        """`copy <bootflash:file> running-config` — NX-OS's own merge from
        a file already on the box."""
        if not self.is_connected():
            raise ConnectionError("Not connected to device")
        host = self.connection_params.host
        if method != ConfigLoadMethod.MERGE:
            return ConfigResult(
                node_name=host, success=False,
                message="NX-OS has no candidate configuration",
                error=f"method {method.value!r} is not supported on NX-OS",
            )
        path = device_file_path
        if ":" not in path:
            path = f"bootflash:{path.lstrip('/')}"
        try:
            out = self._send(f"copy {path} running-config",
                             timeout=self._read_timeout * 4)
        except (TimeoutError, socket.timeout, OSError) as e:
            return ConfigResult(node_name=host, success=False,
                                message="Copy failed", error=str(e))
        err = ERROR_RE.search(out)
        if err or "No such file" in out:
            return ConfigResult(node_name=host, success=False,
                                message=f"copy {path} running-config failed",
                                error=(err.group(0) if err else out).strip())
        save = self.commit_config(commit_comment)
        if not save.success:
            return save
        return ConfigResult(node_name=host, success=True,
                            message=f"{path} merged and saved")

    def validate_config(
        self, config_content: str, format: ConfigFormat = ConfigFormat.TEXT
    ) -> Tuple[bool, Optional[str]]:
        """NX-OS cannot check a config without applying it; the only
        offline check is the format and that there is something to send."""
        if format != ConfigFormat.TEXT:
            return False, f"format {format.value!r} is not an NX-OS format"
        if not self.config_lines(config_content):
            return False, "no configuration lines"
        return True, None

    def get_config_diff(self) -> Optional[str]:
        return None                 # nothing pending: lines apply as typed

    def commit_config(
        self, comment: Optional[str] = None, confirm_timeout: Optional[int] = None
    ) -> ConfigResult:
        host = self.connection_params.host
        try:
            out = self._send("copy running-config startup-config",
                             timeout=self._read_timeout * 4)
        except (TimeoutError, socket.timeout, OSError) as e:
            return ConfigResult(node_name=host, success=False,
                                message="Save failed", error=str(e))
        if ERROR_RE.search(out) and "Copy complete" not in out:
            return ConfigResult(node_name=host, success=False,
                                message="copy running-config startup-config failed",
                                error=out.strip())
        return ConfigResult(node_name=host, success=True,
                            message="Saved to startup-config")

    def rollback_config(self, rollback_id: Optional[int] = None) -> ConfigResult:
        return ConfigResult(
            node_name=self.connection_params.host, success=False,
            message="Rollback is not supported on NX-OS through this driver",
            error="use `rollback running-config checkpoint <name>` on the box",
        )

    def get_facts(self) -> Dict[str, Any]:
        if not self.is_connected():
            raise ConnectionError("Not connected to device")
        try:
            out = self._send("show version")
        except (TimeoutError, socket.timeout, OSError) as e:
            logger.error(f"Failed to get facts: {e}")
            return {}
        facts: Dict[str, Any] = {"vendor": "Cisco", "os": "NX-OS"}
        for key, rx in (("version", r"NXOS:\s*version\s+(\S+)"),
                        ("hostname", r"Device name:\s*(\S+)"),
                        ("model", r"cisco\s+(Nexus\S*\s+\S+)"),
                        ("uptime", r"Kernel uptime is\s+(.+)")):
            m = re.search(rx, out)
            if m:
                facts[key] = m.group(1).strip()
        return facts

    # -- registry --------------------------------------------------------------

    @classmethod
    def get_supported_vendors(cls) -> List[str]:
        return ["cisco", "nxos", "cisco_nxos"]

    @classmethod
    def get_supported_device_types(cls) -> List[str]:
        # containerlab's kind and its vrnetlab alias
        return ["cisco_n9kv", "vr-n9kv", "cisco_nxos"]
