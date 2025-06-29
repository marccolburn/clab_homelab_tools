"""Configuration management for node operations."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Import drivers package to register all drivers
import clab_tools.node.drivers  # noqa: F401
from clab_tools.config.settings import get_settings
from clab_tools.db.models import Node
from clab_tools.node.drivers.base import (
    ConfigFormat,
    ConfigLoadMethod,
    ConfigResult,
    ConnectionParams,
)
from clab_tools.node.drivers.registry import DriverRegistry

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration operations across multiple nodes."""

    def __init__(self, quiet: bool = False):
        """Initialize config manager.

        Args:
            quiet: Suppress progress output
        """
        self.quiet = quiet
        self.console = Console()

    def load_config_from_file(
        self,
        nodes: List[Node],
        file_path: Path,
        format: ConfigFormat = ConfigFormat.TEXT,
        method: ConfigLoadMethod = ConfigLoadMethod.MERGE,
        dry_run: bool = False,
        commit_comment: Optional[str] = None,
        parallel: bool = True,
        max_workers: int = 5,
    ) -> List[ConfigResult]:
        """Load configuration from local file to nodes.

        Args:
            nodes: List of nodes
            file_path: Local file path
            format: Configuration format
            method: Load method
            dry_run: Validate only
            commit_comment: Commit comment
            parallel: Load in parallel
            max_workers: Maximum workers

        Returns:
            List of ConfigResult objects
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Read configuration content
        config_content = file_path.read_text()

        if parallel and len(nodes) > 1:
            return self._load_parallel(
                nodes,
                config_content,
                format,
                method,
                dry_run,
                commit_comment,
                max_workers,
            )
        else:
            return self._load_sequential(
                nodes,
                config_content,
                format,
                method,
                dry_run,
                commit_comment,
            )

    def load_config_from_device(
        self,
        nodes: List[Node],
        device_file_path: str,
        method: ConfigLoadMethod = ConfigLoadMethod.MERGE,
        dry_run: bool = False,
        commit_comment: Optional[str] = None,
        parallel: bool = True,
        max_workers: int = 5,
    ) -> List[ConfigResult]:
        """Load configuration from device file.

        Args:
            nodes: List of nodes
            device_file_path: Path on device
            method: Load method
            dry_run: Validate only
            commit_comment: Commit comment
            parallel: Load in parallel
            max_workers: Maximum workers

        Returns:
            List of ConfigResult objects
        """
        if parallel and len(nodes) > 1:
            return self._load_device_parallel(
                nodes, device_file_path, method, dry_run, commit_comment, max_workers
            )
        else:
            return self._load_device_sequential(
                nodes, device_file_path, method, dry_run, commit_comment
            )

    def _load_parallel(
        self,
        nodes: List[Node],
        config_content: str,
        format: ConfigFormat,
        method: ConfigLoadMethod,
        dry_run: bool,
        commit_comment: Optional[str],
        max_workers: int,
    ) -> List[ConfigResult]:
        """Load configuration in parallel.

        Args:
            nodes: List of nodes
            config_content: Configuration content
            format: Config format
            method: Load method
            dry_run: Validate only
            commit_comment: Commit comment
            max_workers: Maximum workers
            source: Source type for progress

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
            action = "Validating" if dry_run else "Loading"
            task = progress.add_task(
                f"{action} configuration on {len(nodes)} nodes...", total=len(nodes)
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_node = {
                    executor.submit(
                        self._load_on_node,
                        node,
                        config_content,
                        format,
                        method,
                        dry_run,
                        commit_comment,
                    ): node
                    for node in nodes
                }

                # Collect results
                for future in as_completed(future_to_node):
                    node = future_to_node[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append(
                            ConfigResult(
                                node_name=node.name,
                                success=False,
                                message="Configuration failed",
                                error=str(e),
                            )
                        )

                    progress.update(task, advance=1)

        return results

    def _load_sequential(
        self,
        nodes: List[Node],
        config_content: str,
        format: ConfigFormat,
        method: ConfigLoadMethod,
        dry_run: bool,
        commit_comment: Optional[str],
    ) -> List[ConfigResult]:
        """Load configuration sequentially.

        Args:
            nodes: List of nodes
            config_content: Configuration content
            format: Config format
            method: Load method
            dry_run: Validate only
            commit_comment: Commit comment
            source: Source type

        Returns:
            List of results
        """
        results = []

        for node in nodes:
            if not self.quiet:
                action = "Validating" if dry_run else "Loading"
                self.console.print(f"{action} configuration on {node.name}...")

            try:
                result = self._load_on_node(
                    node, config_content, format, method, dry_run, commit_comment
                )
                results.append(result)
            except Exception as e:
                results.append(
                    ConfigResult(
                        node_name=node.name,
                        success=False,
                        message="Configuration failed",
                        error=str(e),
                    )
                )

        return results

    def _load_device_parallel(
        self,
        nodes: List[Node],
        device_file_path: str,
        method: ConfigLoadMethod,
        dry_run: bool,
        commit_comment: Optional[str],
        max_workers: int,
    ) -> List[ConfigResult]:
        """Load from device file in parallel.

        Args:
            nodes: List of nodes
            device_file_path: Device file path
            method: Load method
            dry_run: Validate only
            commit_comment: Commit comment
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
            action = "Validating" if dry_run else "Loading"
            task = progress.add_task(
                f"{action} configuration from device file on {len(nodes)} nodes...",
                total=len(nodes),
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_node = {
                    executor.submit(
                        self._load_device_on_node,
                        node,
                        device_file_path,
                        method,
                        dry_run,
                        commit_comment,
                    ): node
                    for node in nodes
                }

                for future in as_completed(future_to_node):
                    node = future_to_node[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append(
                            ConfigResult(
                                node_name=node.name,
                                success=False,
                                message="Configuration failed",
                                error=str(e),
                            )
                        )

                    progress.update(task, advance=1)

        return results

    def _load_device_sequential(
        self,
        nodes: List[Node],
        device_file_path: str,
        method: ConfigLoadMethod,
        dry_run: bool,
        commit_comment: Optional[str],
    ) -> List[ConfigResult]:
        """Load from device file sequentially.

        Args:
            nodes: List of nodes
            device_file_path: Device file path
            method: Load method
            dry_run: Validate only
            commit_comment: Commit comment

        Returns:
            List of results
        """
        results = []

        for node in nodes:
            if not self.quiet:
                action = "Validating" if dry_run else "Loading"
                self.console.print(
                    f"{action} configuration from device file on {node.name}..."
                )

            try:
                result = self._load_device_on_node(
                    node, device_file_path, method, dry_run, commit_comment
                )
                results.append(result)
            except Exception as e:
                results.append(
                    ConfigResult(
                        node_name=node.name,
                        success=False,
                        message="Configuration failed",
                        error=str(e),
                    )
                )

        return results

    def _load_on_node(
        self,
        node: Node,
        config_content: str,
        format: ConfigFormat,
        method: ConfigLoadMethod,
        dry_run: bool,
        commit_comment: Optional[str],
    ) -> ConfigResult:
        """Load configuration on single node.

        Args:
            node: Node to configure
            config_content: Configuration content
            format: Config format
            method: Load method
            dry_run: Validate only
            commit_comment: Commit comment

        Returns:
            ConfigResult
        """
        # Get settings for fallback credentials
        settings = get_settings()

        # Resolve credentials with proper fallbacks
        username = (
            getattr(node, "username", None) or settings.node.default_username or "admin"
        )
        password = getattr(node, "password", None) or settings.node.default_password

        # Create connection parameters
        conn_params = ConnectionParams(
            host=node.mgmt_ip,
            username=username,
            password=password,
            port=getattr(node, "ssh_port", None) or settings.node.ssh_port or 22,
            timeout=settings.node.connection_timeout or 30,
            vendor=getattr(node, "vendor", None),
            device_type=node.kind,
        )

        # Get driver
        try:
            driver = DriverRegistry.create_driver(conn_params)
        except ValueError as e:
            return ConfigResult(
                node_name=node.name,
                success=False,
                message="No driver available",
                error=str(e),
            )

        # Load configuration
        try:
            with driver:
                if dry_run:
                    # Validate only
                    is_valid, error = driver.validate_config(config_content, format)
                    if is_valid:
                        return ConfigResult(
                            node_name=node.name,
                            success=True,
                            message="Configuration is valid",
                        )
                    else:
                        return ConfigResult(
                            node_name=node.name,
                            success=False,
                            message="Configuration validation failed",
                            error=error,
                        )
                else:
                    # Load and commit
                    return driver.load_config(
                        config_content, format, method, commit_comment
                    )
        except Exception as e:
            return ConfigResult(
                node_name=node.name,
                success=False,
                message="Configuration operation failed",
                error=str(e),
            )

    def _load_device_on_node(
        self,
        node: Node,
        device_file_path: str,
        method: ConfigLoadMethod,
        dry_run: bool,
        commit_comment: Optional[str],
    ) -> ConfigResult:
        """Load from device file on single node.

        Args:
            node: Node to configure
            device_file_path: Device file path
            method: Load method
            dry_run: Validate only
            commit_comment: Commit comment

        Returns:
            ConfigResult
        """
        # Get settings for fallback credentials
        settings = get_settings()

        # Resolve credentials with proper fallbacks
        username = (
            getattr(node, "username", None) or settings.node.default_username or "admin"
        )
        password = getattr(node, "password", None) or settings.node.default_password

        # Create connection parameters
        conn_params = ConnectionParams(
            host=node.mgmt_ip,
            username=username,
            password=password,
            port=getattr(node, "ssh_port", None) or settings.node.ssh_port or 22,
            timeout=settings.node.connection_timeout or 30,
            vendor=getattr(node, "vendor", None),
            device_type=node.kind,
        )

        # Get driver
        try:
            driver = DriverRegistry.create_driver(conn_params)
        except ValueError as e:
            return ConfigResult(
                node_name=node.name,
                success=False,
                message="No driver available",
                error=str(e),
            )

        # Load configuration
        try:
            with driver:
                if dry_run:
                    # For device files, we can't validate without loading
                    # So we load but don't commit
                    result = driver.load_config_from_file(
                        device_file_path, method, None
                    )
                    if result.success:
                        # Rollback the changes
                        driver.rollback_config()
                        return ConfigResult(
                            node_name=node.name,
                            success=True,
                            message="Configuration is valid (rolled back)",
                            diff=result.diff,
                        )
                    return result
                else:
                    return driver.load_config_from_file(
                        device_file_path, method, commit_comment
                    )
        except Exception as e:
            return ConfigResult(
                node_name=node.name,
                success=False,
                message="Configuration operation failed",
                error=str(e),
            )

    def format_results(
        self,
        results: List[ConfigResult],
        output_format: str = "text",
        show_diff: bool = True,
    ) -> str:
        """Format configuration results.

        Args:
            results: List of results
            output_format: Output format
            show_diff: Show configuration diffs

        Returns:
            Formatted output
        """
        if output_format == "json":
            return self._format_json(results)
        elif output_format == "table":
            return self._format_table(results)
        else:
            return self._format_text(results, show_diff)

    def _format_text(self, results: List[ConfigResult], show_diff: bool) -> str:
        """Format results as text.

        Args:
            results: Config results
            show_diff: Show diffs

        Returns:
            Formatted text
        """
        output = []

        for result in results:
            output.append(f"\n{'='*60}")
            output.append(f"Node: {result.node_name}")
            output.append(f"Status: {'Success' if result.success else 'Failed'}")
            output.append(f"Message: {result.message}")

            if result.error:
                output.append(f"Error: {result.error}")

            if show_diff and result.diff:
                output.append("\nConfiguration diff:")
                output.append(result.diff)

        output.append(f"\n{'='*60}")
        return "\n".join(output)

    def _format_table(self, results: List[ConfigResult]) -> str:
        """Format results as table.

        Args:
            results: Config results

        Returns:
            Formatted table
        """
        table = Table(title="Configuration Results")
        table.add_column("Node", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Message")
        table.add_column("Changes")

        for result in results:
            status = "✓" if result.success else "✗"
            changes = "Yes" if result.diff else "No"

            if not result.success:
                message = f"[red]{result.message}[/red]"
            else:
                message = result.message

            table.add_row(result.node_name, status, message, changes)

        # Capture table as string
        from io import StringIO

        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        console.print(table)
        return string_io.getvalue()

    def _format_json(self, results: List[ConfigResult]) -> str:
        """Format results as JSON.

        Args:
            results: Config results

        Returns:
            JSON string
        """
        data = []

        for result in results:
            data.append(
                {
                    "node": result.node_name,
                    "success": result.success,
                    "message": result.message,
                    "error": result.error,
                    "has_diff": result.diff is not None,
                    "diff": result.diff,
                }
            )

        return json.dumps(data, indent=2)

    def print_summary(self, results: List[ConfigResult]) -> None:
        """Print configuration summary.

        Args:
            results: Config results
        """
        if self.quiet:
            return

        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        self.console.print("\n[bold]Configuration Summary:[/bold]")
        self.console.print(f"  Total nodes: {total}")
        self.console.print(f"  [green]Successful: {successful}[/green]")
        if failed > 0:
            self.console.print(f"  [red]Failed: {failed}[/red]")

        # Show failed nodes
        if failed > 0:
            self.console.print("\n[bold red]Failed nodes:[/bold red]")
            for result in results:
                if not result.success:
                    self.console.print(
                        f"  - {result.node_name}: {result.error or result.message}"
                    )
