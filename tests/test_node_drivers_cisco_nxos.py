"""Tests for the Cisco NX-OS driver.

A scripted shell stands in for the box: every line sent gets the echo,
an answer looked up by command, and a prompt back — so the tests pin the
protocol the driver speaks (configure terminal, the lines, end, copy run
start) and what it makes of `% Invalid command`.
"""

from unittest.mock import patch

import pytest

from clab_tools.node.drivers.base import (
    ConfigFormat,
    ConfigLoadMethod,
    ConnectionParams,
)
from clab_tools.node.drivers.registry import DriverRegistry


class FakeShell:
    """A paramiko channel that answers from a script."""

    def __init__(self, answers=None, hostname="dc1-leaf1"):
        self.answers = answers or {}
        self.hostname = hostname
        self.sent = []
        self._buf = (f"\r\n*  Cisco in writing.   *\r\n*****\r\n\r"
                     f"{hostname}# ").encode()
        self.mode = ""          # "" | "(config)" | "(config-if)"
        self.closed = False

    def settimeout(self, t):
        pass

    def send(self, data):
        line = data.rstrip("\n")
        self.sent.append(line)
        answer = self.answers.get(line, "")
        if line == "configure terminal":
            self.mode = "(config)"
        elif line.startswith("interface ") and self.mode:
            self.mode = "(config-if)"
        elif line == "end":
            self.mode = ""
        # exactly what a real N9Kv sends: CRLF line ends and a BARE CR
        # before the prompt (the first driver hung on that CR, 2026-09-09)
        self._buf += (f"{line}\r\n" + (answer + "\r\n" if answer else "")
                      + f"\r{self.hostname}{self.mode}# ").encode()

    def recv_ready(self):
        return bool(self._buf)

    def recv(self, n):
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def close(self):
        self.closed = True


class FakeClient:
    def __init__(self, shell):
        self.shell = shell
        self.connect_kwargs = None
        self.closed = False

    def set_missing_host_key_policy(self, p):
        pass

    def connect(self, **kw):
        self.connect_kwargs = kw

    def invoke_shell(self, **kw):
        return self.shell

    def close(self):
        self.closed = True


@pytest.fixture
def params():
    return ConnectionParams(host="10.100.0.130", username="admin",
                            password="admin", port=22, timeout=5,
                            device_type="cisco_n9kv")


@pytest.fixture
def driver(params):
    """A connected driver over a fake shell; (driver, shell, client)."""
    from clab_tools.node.drivers.cisco_nxos import CiscoNxosDriver
    shell = FakeShell()
    client = FakeClient(shell)
    with patch("clab_tools.node.drivers.cisco_nxos.paramiko.SSHClient",
               return_value=client):
        d = CiscoNxosDriver(params)
        d.connect()
        yield d, shell, client
        d.disconnect()


def test_the_registry_dispatches_the_containerlab_kind(params):
    import clab_tools.node.drivers  # noqa: F401  (registers on import)
    from clab_tools.node.drivers.cisco_nxos import CiscoNxosDriver

    assert DriverRegistry.get_driver_by_device_type("cisco_n9kv") is CiscoNxosDriver
    assert DriverRegistry.get_driver_by_vendor("cisco") is CiscoNxosDriver
    d = DriverRegistry.create_driver(params)
    assert isinstance(d, CiscoNxosDriver)
    # and Juniper kinds still go to PyEZ
    j = DriverRegistry.get_driver_by_device_type("juniper_vjunosswitch")
    assert j is not None and j is not CiscoNxosDriver


def test_connect_uses_password_auth_and_sets_the_terminal(driver):
    d, shell, client = driver
    assert d.is_connected()
    kw = client.connect_kwargs
    assert kw["hostname"] == "10.100.0.130" and kw["username"] == "admin"
    assert kw["password"] == "admin" and kw["look_for_keys"] is False
    assert shell.sent[:2] == ["terminal length 0", "terminal width 511"]


def test_execute_command_strips_echo_and_prompt(params):
    from clab_tools.node.drivers.cisco_nxos import CiscoNxosDriver
    shell = FakeShell({"show hostname": "dc1-leaf1"})
    with patch("clab_tools.node.drivers.cisco_nxos.paramiko.SSHClient",
               return_value=FakeClient(shell)):
        d = CiscoNxosDriver(params)
        d.connect()
        r = d.execute_command("show hostname")
    assert r.exit_code == 0 and r.error is None
    assert r.output == "dc1-leaf1"


def test_execute_command_reports_a_rejected_command(params):
    from clab_tools.node.drivers.cisco_nxos import CiscoNxosDriver
    shell = FakeShell({"show bogus": "% Invalid command at '^' marker."})
    with patch("clab_tools.node.drivers.cisco_nxos.paramiko.SSHClient",
               return_value=FakeClient(shell)):
        d = CiscoNxosDriver(params)
        d.connect()
        r = d.execute_command("show bogus")
    assert r.exit_code == 1 and "Invalid command" in r.error


CONFIG = """!Command: show running-config
!Running configuration last done at: Mon Jan  1 00:00:00 2026
version 10.6(4) Bios:version
feature bgp
!
interface Ethernet1/1
  description EDITED
  no switchport

interface loopback0
  ip address 192.0.2.11/32
"""


def test_load_config_merge_sends_the_lines_and_saves(driver):
    d, shell, _ = driver
    r = d.load_config(CONFIG, ConfigFormat.TEXT, ConfigLoadMethod.MERGE)
    assert r.success, r.error
    assert "6 lines applied" in r.message
    sent = shell.sent[2:]          # after the terminal setup
    assert sent == ["configure terminal", "feature bgp",
                    "interface Ethernet1/1", "  description EDITED",
                    "  no switchport", "interface loopback0",
                    "  ip address 192.0.2.11/32", "end",
                    "copy running-config startup-config"]
    assert r.diff.startswith("feature bgp")


def test_load_config_names_the_rejected_line_and_does_not_claim_success(params):
    from clab_tools.node.drivers.cisco_nxos import CiscoNxosDriver
    shell = FakeShell({"  no shutdwn": "% Invalid command at '^' marker."})
    with patch("clab_tools.node.drivers.cisco_nxos.paramiko.SSHClient",
               return_value=FakeClient(shell)):
        d = CiscoNxosDriver(params)
        d.connect()
        r = d.load_config("interface Ethernet1/1\n  no shutdwn\n  description x\n")
    assert r.success is False
    assert "1 of 3 lines rejected" in r.message
    assert "no shutdwn" in r.error and "Invalid command" in r.error
    # nothing is saved when a line failed: the operator decides
    assert "copy running-config startup-config" not in shell.sent


@pytest.mark.parametrize("method", [ConfigLoadMethod.OVERRIDE,
                                    ConfigLoadMethod.REPLACE])
def test_override_and_replace_are_refused_before_touching_the_box(driver, method):
    d, shell, _ = driver
    r = d.load_config("feature bgp\n", ConfigFormat.TEXT, method)
    assert r.success is False
    assert method.value in r.error and "merge" in r.error
    assert shell.sent[2:] == []


def test_set_format_is_refused(driver):
    d, _, _ = driver
    r = d.load_config("set x", ConfigFormat.SET)
    assert r.success is False and "set" in r.error


def test_validate_config_is_the_offline_check_only(driver):
    d, _, _ = driver
    assert d.validate_config("feature bgp\n") == (True, None)
    ok, why = d.validate_config("!\n\n")
    assert ok is False and "no configuration" in why
    ok, why = d.validate_config("x", ConfigFormat.XML)
    assert ok is False


def test_get_facts_parses_show_version(params):
    from clab_tools.node.drivers.cisco_nxos import CiscoNxosDriver
    shell = FakeShell({"show version": (
        "Cisco Nexus Operating System (NX-OS) Software\n"
        "Software\n  NXOS: version 10.6(4)\nHardware\n"
        "  cisco Nexus9000 C9300v Chassis\n"
        "  Device name: dc1-leaf1\nKernel uptime is 0 day(s), 1 hour(s)")})
    with patch("clab_tools.node.drivers.cisco_nxos.paramiko.SSHClient",
               return_value=FakeClient(shell)):
        d = CiscoNxosDriver(params)
        d.connect()
        f = d.get_facts()
    assert f["vendor"] == "Cisco" and f["version"] == "10.6(4)"
    assert f["hostname"] == "dc1-leaf1"
    assert f["model"].startswith("Nexus9000")


def test_disconnect_closes_shell_and_client(driver):
    d, shell, client = driver
    d.disconnect()
    assert not d.is_connected() and shell.closed and client.closed


def test_rollback_is_honest(driver):
    d, _, _ = driver
    r = d.rollback_config()
    assert r.success is False and "checkpoint" in r.error
