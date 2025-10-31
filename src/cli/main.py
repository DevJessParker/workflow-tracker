"""Main CLI entry point."""

import click
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config_loader import Config
from src.graph.builder import WorkflowGraphBuilder
from src.graph.renderer import WorkflowRenderer
from src.integrations.confluence import ConfluencePublisher


console = Console()


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Workflow Tracker - Scan repositories for data workflow patterns.

    This tool analyzes C# and TypeScript/Angular code to identify and visualize
    data workflows including database operations, API calls, file I/O, and more.
    """
    pass


@cli.command()
@click.option('--repo', '-r', default=None, help='Path to repository to scan')
@click.option('--config', '-c', default=None, help='Path to configuration file')
@click.option('--output', '-o', default=None, help='Output directory')
@click.option('--format', '-f', multiple=True, help='Output format(s): html, png, svg, json, markdown')
@click.option('--publish/--no-publish', default=False, help='Publish to Confluence')
def scan(repo, config, output, format, publish):
    """Scan a repository and generate workflow visualizations.

    Example:

        workflow-tracker scan --repo /path/to/repo --format html --format json
    """
    try:
        # Load configuration
        cfg = Config(config)

        # Override with command line args
        if repo:
            cfg.config.setdefault('repository', {})['path'] = repo

        if output:
            cfg.config.setdefault('output', {})['directory'] = output

        if format:
            cfg.config.setdefault('output', {})['formats'] = list(format)

        # Get repository path
        repo_path = cfg.get_repository_path()

        if not os.path.exists(repo_path):
            console.print(f"[red]Error: Repository path not found: {repo_path}[/red]")
            sys.exit(1)

        console.print(f"\n[bold cyan]Workflow Tracker[/bold cyan]")
        console.print(f"Scanning repository: [yellow]{repo_path}[/yellow]\n")

        # Build workflow graph
        builder = WorkflowGraphBuilder(cfg.config)
        result = builder.build(repo_path)

        # Display results
        _display_results(result)

        # Render outputs
        console.print("\n" + "="*60)
        console.print("[bold]RENDERING OUTPUTS[/bold]")
        console.print("="*60)
        renderer = WorkflowRenderer(cfg.config)
        output_files = renderer.render(result)

        console.print("\n[bold green]✓ Scan complete![/bold green]")

        # Display output files
        console.print("\n[bold]Generated files:[/bold]")
        for fmt, file_path in output_files.items():
            if file_path:
                console.print(f"  • {fmt.upper()}: [cyan]{file_path}[/cyan]")

        # Publish to Confluence if requested
        if publish or cfg.is_ci_mode():
            console.print("\n[bold]Publishing to Confluence...[/bold]")

            confluence_config = cfg.get_confluence_config()

            # Validate Confluence config
            if not all([confluence_config.get('url'), confluence_config.get('username'),
                       confluence_config.get('api_token'), confluence_config.get('space_key')]):
                console.print("[red]Error: Confluence configuration incomplete.[/red]")
                console.print("Please set confluence.url, username, api_token, and space_key in your config.")
                sys.exit(1)

            publisher = ConfluencePublisher(confluence_config)
            page_url = publisher.publish(
                result,
                html_file=output_files.get('html'),
                markdown_file=output_files.get('markdown'),
                json_file=output_files.get('json')
            )

            console.print(f"\n[bold green]✓ Published to Confluence:[/bold green]")
            console.print(f"  {page_url}")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.option('--repo', '-r', default=None, help='Path to repository to scan')
@click.option('--config', '-c', default=None, help='Path to configuration file')
def gui(repo, config):
    """Launch the interactive GUI for workflow visualization.

    Example:

        workflow-tracker gui --repo /path/to/repo
    """
    try:
        # Import streamlit components
        import streamlit as st
        import subprocess

        # Set config
        os.environ['WORKFLOW_TRACKER_CONFIG'] = config or ''
        os.environ['WORKFLOW_TRACKER_REPO'] = repo or ''

        # Launch Streamlit app
        streamlit_app = Path(__file__).parent / 'streamlit_app.py'

        console.print("[bold cyan]Launching Workflow Tracker GUI...[/bold cyan]")
        console.print("The web interface will open in your browser.\n")

        subprocess.run([
            'streamlit', 'run',
            str(streamlit_app),
            '--server.headless', 'false'
        ])

    except ImportError:
        console.print("[red]Error: Streamlit not installed.[/red]")
        console.print("Install with: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error launching GUI: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
def init():
    """Initialize configuration file in the current directory.

    Creates a local configuration file from the example template.
    """
    import shutil

    source = Path(__file__).parent.parent.parent / 'config' / 'config.example.yaml'
    target = Path.cwd() / 'config' / 'local.yaml'

    # Create config directory if needed
    target.parent.mkdir(exist_ok=True)

    if target.exists():
        if not click.confirm(f'Configuration file already exists at {target}. Overwrite?'):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    shutil.copy(source, target)

    console.print(f"[green]✓ Created configuration file:[/green] {target}")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Edit config/local.yaml with your settings")
    console.print("2. Set your Confluence credentials")
    console.print("3. Run: workflow-tracker scan --repo /path/to/repo")


def _display_results(result):
    """Display scan results in a table."""
    from collections import Counter

    # Count nodes by type
    type_counts = Counter(node.type.value for node in result.graph.nodes)

    # Create table
    table = Table(title="Scan Results", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Files Scanned", str(result.files_scanned))
    table.add_row("Total Nodes", str(len(result.graph.nodes)))
    table.add_row("Total Edges", str(len(result.graph.edges)))
    table.add_row("Scan Time", f"{result.scan_time_seconds:.2f}s")

    if result.errors:
        table.add_row("Errors", str(len(result.errors)), style="red")

    console.print(table)

    # Display workflow type breakdown
    if type_counts:
        console.print("\n[bold]Workflow Operations Found:[/bold]")
        for workflow_type, count in sorted(type_counts.items()):
            type_display = workflow_type.replace('_', ' ').title()
            console.print(f"  • {type_display}: {count}")


if __name__ == '__main__':
    cli()
