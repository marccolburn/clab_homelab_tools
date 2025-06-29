"""Command execution manager for node operations."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Import drivers package to register all drivers
import clab_tools.node.drivers  # noqa: F401
from clab_tools.db.models import Node
from clab_tools.node.drivers.base import CommandResult, ConnectionParams
from clab_tools.node.drivers.registry import DriverRegistry

logger = logging.getLogger(__name__)


class CommandManager:
    """Manages command execution across multiple nodes."""

    def __init__(self, quiet: bool = False):
        """Initialize command manager.

        Args:
            quiet: Suppress progress output
        """
        self.quiet = quiet
        self.console = Console()

    def execute_command(
        self,
        nodes: List[Node],
        command: str,
        timeout: Optional[int] = None,
        parallel: bool = True,
        max_workers: int = 10,
    ) -> List[CommandResult]:
        """Execute command on multiple nodes.

        Args:
            nodes: List of nodes to execute on
            command: Command to execute
            timeout: Command timeout in seconds
            parallel: Execute in parallel
            max_workers: Maximum parallel workers

        Returns:
            List of CommandResult objects
        """
        if not nodes:
            return []

        if parallel and len(nodes) > 1:
            return self._execute_parallel(nodes, command, timeout, max_workers)
        else:
            return self._execute_sequential(nodes, command, timeout)

    def _execute_parallel(
        self, nodes: List[Node], command: str, timeout: Optional[int], max_workers: int
    ) -> List[CommandResult]:
        """Execute command in parallel.

        Args:
            nodes: List of nodes
            command: Command to execute
            timeout: Command timeout
            max_workers: Maximum workers

        Returns:
            List of results
        """
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            disable=self.quiet,
        ) as progress:
            task = progress.add_task(
                f"Executing '{command}' on {len(nodes)} nodes...", total=len(nodes)
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_node = {
                    executor.submit(self._execute_on_node, node, command, timeout): node
                    for node in nodes
                }

                # Collect results
                for future in as_completed(future_to_node):
                    node = future_to_node[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        # Create error result
                        results.append(
                            CommandResult(
                                node_name=node.name,
                                command=command,
                                output="",
                                error=str(e),
                                exit_code=1,
                            )
                        )

                    progress.update(task, advance=1)

        return results

    def _execute_sequential(
        self, nodes: List[Node], command: str, timeout: Optional[int]
    ) -> List[CommandResult]:
        """Execute command sequentially.

        Args:
            nodes: List of nodes
            command: Command to execute
            timeout: Command timeout

        Returns:
            List of results
        """
        results = []

        for node in nodes:
            if not self.quiet:
                self.console.print(f"Executing on {node.name}...")

            try:
                result = self._execute_on_node(node, command, timeout)
                results.append(result)
            except Exception as e:
                results.append(
                    CommandResult(
                        node_name=node.name,
                        command=command,
                        output="",
                        error=str(e),
                        exit_code=1,
                    )
                )

        return results

    def _execute_on_node(
        self, node: Node, command: str, timeout: Optional[int]
    ) -> CommandResult:
        """Execute command on single node.

        Args:
            node: Node to execute on
            command: Command to execute
            timeout: Command timeout

        Returns:
            CommandResult
        """
        # Create connection parameters
        conn_params = ConnectionParams(
            host=node.mgmt_ip,
            username=node.username or "admin",
            password=node.password,
            port=node.ssh_port or 22,
            timeout=30,
            vendor=node.vendor,
            device_type=node.kind,
        )

        # Get appropriate driver
        try:
            driver = DriverRegistry.create_driver(conn_params)
        except ValueError as e:
            return CommandResult(
                node_name=node.name,
                command=command,
                output="",
                error=f"No driver available: {e}",
                exit_code=1,
            )

        # Execute command
        try:
            with driver:
                return driver.execute_command(command, timeout)
        except Exception as e:
            return CommandResult(
                node_name=node.name,
                command=command,
                output="",
                error=str(e),
                exit_code=1,
            )

    def format_results(
        self, results: List[CommandResult], output_format: str = "text"
    ) -> str:
        """Format command results for display.

        Args:
            results: List of command results
            output_format: Output format (text, table, json)

        Returns:
            Formatted output string
        """
        if output_format == "json":
            return self._format_json(results)
        elif output_format == "table":
            return self._format_table(results)
        else:
            return self._format_text(results)

    def _format_text(self, results: List[CommandResult]) -> str:
        """Format results as text.

        Args:
            results: Command results

        Returns:
            Formatted text
        """
        output = []

        for result in results:
            output.append(f"\n{'='*60}")
            output.append(f"Node: {result.node_name}")
            output.append(f"Command: {result.command}")
            output.append(f"Duration: {result.duration:.2f}s")

            if result.exit_code == 0:
                output.append("Status: Success")
                if result.output:
                    output.append(f"\nOutput:\n{result.output}")
            else:
                output.append(f"Status: Failed (exit code: {result.exit_code})")
                if result.error:
                    output.append(f"Error: {result.error}")

        output.append(f"\n{'='*60}")
        return "\n".join(output)

    def _format_table(self, results: List[CommandResult]) -> str:
        """Format results as table.

        Args:
            results: Command results

        Returns:
            Formatted table
        """
        table = Table(title="Command Execution Results")
        table.add_column("Node", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Output/Error")

        for result in results:
            status = "✓" if result.exit_code == 0 else "✗"
            duration = f"{result.duration:.2f}s"

            if result.exit_code == 0:
                output = (
                    result.output[:100] + "..."
                    if len(result.output) > 100
                    else result.output
                )
            else:
                output = f"[red]{result.error}[/red]"

            table.add_row(result.node_name, status, duration, output)

        # Use console to capture table as string
        from io import StringIO

        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        console.print(table)
        return string_io.getvalue()

    def _format_json(self, results: List[CommandResult]) -> str:
        """Format results as JSON.

        Args:
            results: Command results

        Returns:
            JSON string
        """
        data = []

        for result in results:
            data.append(
                {
                    "node": result.node_name,
                    "command": result.command,
                    "exit_code": result.exit_code,
                    "duration": result.duration,
                    "output": result.output,
                    "error": result.error,
                }
            )

        return json.dumps(data, indent=2)

    def print_summary(self, results: List[CommandResult]) -> None:
        """Print execution summary.

        Args:
            results: Command results
        """
        if self.quiet:
            return

        total = len(results)
        successful = sum(1 for r in results if r.exit_code == 0)
        failed = total - successful

        self.console.print("\n[bold]Execution Summary:[/bold]")
        self.console.print(f"  Total nodes: {total}")
        self.console.print(f"  [green]Successful: {successful}[/green]")
        if failed > 0:
            self.console.print(f"  [red]Failed: {failed}[/red]")

        # Show failed nodes
        if failed > 0:
            self.console.print("\n[bold red]Failed nodes:[/bold red]")
            for result in results:
                if result.exit_code != 0:
                    self.console.print(f"  - {result.node_name}: {result.error}")
