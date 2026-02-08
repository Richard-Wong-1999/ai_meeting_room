"""Animated splash screen for AI Meeting Room using Rich."""

import time

from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich.text import Text

from . import __version__
from .ui_helpers import clear_screen

# Cyan-to-magenta-to-cyan gradient (14 colors, one per art line)
GRADIENT_COLORS = [
    "#00d7ff",
    "#00afff",
    "#0087ff",
    "#5f5fff",
    "#875fff",
    "#af5fff",
    "#d75fff",
    "#ff5faf",
    "#d75fff",
    "#af5fff",
    "#875fff",
    "#5f5fff",
    "#0087ff",
    "#00d7ff",
]

# Block-letter ASCII art lines (without border characters)
ART_LINES = [
    r" █████╗ ██╗    ███╗   ███╗███████╗███████╗████████╗██╗███╗   ██╗ ██████╗ ",
    r"██╔══██╗██║    ████╗ ████║██╔════╝██╔════╝╚══██╔══╝██║████╗  ██║██╔════╝ ",
    r"███████║██║    ██╔████╔██║█████╗  █████╗     ██║   ██║██╔██╗ ██║██║  ███╗",
    r"██╔══██║██║    ██║╚██╔╝██║██╔══╝  ██╔══╝     ██║   ██║██║╚██╗██║██║   ██║",
    r"██║  ██║██║    ██║ ╚═╝ ██║███████╗███████╗   ██║   ██║██║ ╚████║╚██████╔╝",
    r"╚═╝  ╚═╝╚═╝    ╚═╝     ╚═╝╚══════╝╚══════╝   ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝ ",
    r"                                                                         ",
    r"                  ██████╗  ██████╗  ██████╗ ███╗   ███╗                  ",
    r"                  ██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║                  ",
    r"                  ██████╔╝██║   ██║██║   ██║██╔████╔██║                  ",
    r"                  ██╔══██╗██║   ██║██║   ██║██║╚██╔╝██║                  ",
    r"                  ██║  ██║╚██████╔╝╚██████╔╝██║ ╚═╝ ██║                  ",
    r"                  ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝                  ",
]

SUBTITLE = "多AI會議室"
LOADING_TEXT = "正在啟動...請稍候"


def _build_art_text(lines: list[str], num_lines: int | None = None) -> Text:
    """Build a Rich Text object with gradient-colored art lines.

    Args:
        lines: The ASCII art lines to render.
        num_lines: If given, only render this many lines (for reveal animation).
                   Remaining lines are replaced with blank lines to keep panel size stable.

    Returns:
        A Rich Text object with gradient styling applied.
    """
    text = Text()
    total = len(lines)
    visible = num_lines if num_lines is not None else total

    for i in range(total):
        if i < visible:
            color = GRADIENT_COLORS[i % len(GRADIENT_COLORS)]
            text.append(lines[i], style=Style(color=color, bold=True))
        else:
            # Blank line to maintain panel dimensions during reveal
            text.append(" " * len(lines[i]))
        if i < total - 1:
            text.append("\n")

    return text


def _build_splash_panel(art_text: Text, show_info: bool = True) -> Align:
    """Wrap art text in a styled Rich Panel.

    Args:
        art_text: The gradient-colored art text.
        show_info: Whether to append subtitle and version info below the art.

    Returns:
        A centered Align containing the Panel.
    """
    content = Text()
    content.append_text(art_text)

    if show_info:
        content.append("\n\n")
        # Centered subtitle
        subtitle_line = SUBTITLE.center(73)
        content.append(subtitle_line, style=Style(color="bright_yellow", bold=True))
        content.append("\n")
        # Centered version
        version_line = f"版本 {__version__}".center(73)
        content.append(version_line, style=Style(dim=True))

    panel = Panel(
        content,
        box=box.DOUBLE,
        border_style="bright_blue",
        padding=(1, 2),
    )
    return Align.center(panel)


def _animate_reveal(console: Console, duration: float) -> None:
    """Reveal art lines one-by-one inside a panel using Rich Live.

    Args:
        console: The Rich Console instance.
        duration: Total time for the reveal animation.
    """
    num_lines = len(ART_LINES)
    delay = duration / num_lines

    with Live(console=console, refresh_per_second=20, transient=True) as live:
        for i in range(1, num_lines + 1):
            art_text = _build_art_text(ART_LINES, num_lines=i)
            # Don't show info text until all lines revealed
            panel = _build_splash_panel(art_text, show_info=(i == num_lines))
            live.update(panel)
            time.sleep(delay)


def _animate_progress(console: Console, duration: float) -> None:
    """Show an animated progress bar with spinner.

    Args:
        console: The Rich Console instance.
        duration: Total time for the progress animation.
    """
    progress = Progress(
        SpinnerColumn("dots"),
        TextColumn("[bright_green]{task.description}[/bright_green]"),
        BarColumn(
            bar_width=40,
            style="grey37",
            complete_style="cyan",
            finished_style="bright_magenta",
        ),
        console=console,
    )

    with progress:
        task = progress.add_task(LOADING_TEXT, total=100)
        steps = 50
        step_delay = duration / steps
        for i in range(steps):
            progress.update(task, advance=100 / steps)
            time.sleep(step_delay)


def display_splash_screen(duration: float = 2.0) -> None:
    """Display the animated splash screen.

    Args:
        duration: Total display duration in seconds.
    """
    try:
        clear_screen()
        console = Console()

        # Short duration: static display only
        if duration < 0.5:
            art_text = _build_art_text(ART_LINES)
            panel = _build_splash_panel(art_text, show_info=True)
            console.print(panel)
            time.sleep(duration)
            return

        # Split time between reveal and progress phases
        reveal_time = min(duration * 0.4, 1.0)
        progress_time = duration - reveal_time

        # Phase 1: Line-by-line reveal
        _animate_reveal(console, reveal_time)

        # Print the final static panel (persists after Live ends)
        art_text = _build_art_text(ART_LINES)
        panel = _build_splash_panel(art_text, show_info=True)
        console.print(panel)

        # Phase 2: Progress bar
        _animate_progress(console, progress_time)

    except KeyboardInterrupt:
        # Allow user to skip splash screen
        pass
