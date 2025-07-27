"""Command-line interface for Alexandria."""

import click
import sys
from pathlib import Path

from alexandria.config import Config
from alexandria.service import AlexandriaDaemon
from alexandria.core import MemoryDB


@click.group()
@click.version_option()
def cli():
    """Alexandria - Screenshot Recall Utility for Wayland."""
    pass


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--one-shot", is_flag=True, help="Take one screenshot and exit")
def daemon(debug, one_shot):
    """Run the Alexandria screenshot daemon."""
    if debug:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    daemon_instance = AlexandriaDaemon()

    if one_shot:
        daemon_instance.capture_and_process_screenshot()
        return

    try:
        daemon_instance.run()
    except KeyboardInterrupt:
        click.echo("Daemon stopped by user")
    except Exception as e:
        click.echo(f"Daemon error: {e}", err=True)
        sys.exit(1)


@cli.command()
def gui():
    """Launch the Alexandria GUI."""
    try:
        from alexandria.gui.main_window import main

        main()
    except ImportError as e:
        click.echo(f"GUI dependencies not available: {e}", err=True)
        click.echo("Please install GTK3 and PyGObject dependencies", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"GUI error: {e}", err=True)
        sys.exit(1)


@cli.command()
def status():
    """Show Alexandria daemon status."""
    try:
        daemon_instance = AlexandriaDaemon()
        status_info = daemon_instance.status()

        click.echo("Alexandria Status:")
        click.echo(f"  Running: {status_info['running']}")
        click.echo(f"  Config: {status_info['config_file']}")
        click.echo(f"  Database: {status_info['database_path']}")
        click.echo(f"  Screenshots: {status_info['screenshots_dir']}")
        click.echo(f"  Backend: {status_info['screenshot_backend']}")
        click.echo(f"  OCR Enabled: {status_info['ocr_enabled']}")
        click.echo(f"  Interval: {status_info['interval_minutes']} minutes")

        stats = status_info["statistics"]
        click.echo("\nStatistics:")
        click.echo(f"  Total Memories: {stats['total_memories']}")
        click.echo(f"  Private Memories: {stats['private_memories']}")
        click.echo(f"  Memories with Text: {stats['memories_with_text']}")

        if stats["oldest_memory"]:
            click.echo(f"  Oldest Memory: {stats['oldest_memory']}")
        if stats["newest_memory"]:
            click.echo(f"  Newest Memory: {stats['newest_memory']}")

    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("query", required=True)
@click.option("--limit", default=10, help="Maximum number of results")
def search(query, limit):
    """Search memories by text content."""
    try:
        config = Config()
        db = MemoryDB(f"sqlite:///{config.database_path}")

        memories = db.search_memories(query, limit=limit)

        if not memories:
            click.echo("No memories found.")
            return

        click.echo(f"Found {len(memories)} memories:")
        for memory in memories:
            click.echo(
                f"  {memory.id}: {memory.timestamp} - {memory.application_name or 'Unknown'}"
            )
            if memory.window_title:
                click.echo(f"    Title: {memory.window_title}")
            if memory.ocr_text:
                preview = (
                    memory.ocr_text[:100] + "..."
                    if len(memory.ocr_text) > 100
                    else memory.ocr_text
                )
                click.echo(f"    Text: {preview}")
            click.echo()

    except Exception as e:
        click.echo(f"Search error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--days", default=30, help="Delete memories older than N days")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def cleanup(days, confirm):
    """Clean up old memories."""
    try:
        config = Config()
        db = MemoryDB(f"sqlite:///{config.database_path}")

        if not confirm:
            click.confirm(f"Delete all memories older than {days} days?", abort=True)

        deleted_count = db.cleanup_old_memories(days)
        click.echo(f"Deleted {deleted_count} memories.")

    except click.Abort:
        click.echo("Cleanup cancelled.")
    except Exception as e:
        click.echo(f"Cleanup error: {e}", err=True)
        sys.exit(1)


@cli.command()
def config():
    """Show current configuration."""
    try:
        config_instance = Config()

        click.echo("Alexandria Configuration:")
        click.echo(f"  Config file: {config_instance.config_file}")
        click.echo(f"  Data directory: {config_instance.data_dir}")
        click.echo(f"  Cache directory: {config_instance.cache_dir}")
        click.echo(f"  Database: {config_instance.database_path}")

        click.echo("\nScreenshot Settings:")
        screenshot_config = config_instance.get("screenshot")
        for key, value in screenshot_config.items():
            click.echo(f"  {key}: {value}")

        click.echo("\nWayland Settings:")
        wayland_config = config_instance.get("wayland")
        for key, value in wayland_config.items():
            click.echo(f"  {key}: {value}")

        click.echo("\nOCR Settings:")
        ocr_config = config_instance.get("ocr")
        for key, value in ocr_config.items():
            click.echo(f"  {key}: {value}")

    except Exception as e:
        click.echo(f"Config error: {e}", err=True)
        sys.exit(1)


@cli.command()
def install():
    """Install Alexandria systemd service and desktop files."""
    try:
        config = Config()

        # Install systemd service
        systemd_dir = Path.home() / ".config" / "systemd" / "user"
        systemd_dir.mkdir(parents=True, exist_ok=True)

        service_source = (
            Path(__file__).parent.parent.parent / "systemd" / "alexandria.service"
        )
        service_dest = systemd_dir / "alexandria.service"

        if service_source.exists():
            import shutil

            shutil.copy2(service_source, service_dest)
            click.echo(f"Installed systemd service: {service_dest}")

        # Install desktop file
        desktop_dir = Path.home() / ".local" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)

        desktop_source = (
            Path(__file__).parent.parent.parent
            / "desktop"
            / "org.alexandria.recall.desktop"
        )
        desktop_dest = desktop_dir / "org.alexandria.recall.desktop"

        if desktop_source.exists():
            import shutil

            shutil.copy2(desktop_source, desktop_dest)
            click.echo(f"Installed desktop file: {desktop_dest}")

        click.echo("\nTo enable the service:")
        click.echo("  systemctl --user enable alexandria.service")
        click.echo("  systemctl --user start alexandria.service")

    except Exception as e:
        click.echo(f"Installation error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
