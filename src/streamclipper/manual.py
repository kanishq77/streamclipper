"""Manual clip helpers shared by the dashboard CLI and the live ring-buffer capture path."""

import math
from pathlib import Path

from streamclipper.util import ToolError, run_cmd


def validate_window(start: float, end: float, max_duration: float = 600.0) -> tuple[float, float]:
    """Validate and normalize a manual clip time range."""
    try:
        a, b = float(start), float(end)
    except (TypeError, ValueError):
        raise ToolError("Start and end times must be numbers.", "enter seconds, e.g. 125 and 155") from None
    if not math.isfinite(a) or not math.isfinite(b):
        raise ToolError("Start and end times must be finite numbers.", "enter valid timestamps")
    if a < 0:
        raise ToolError("The start time cannot be negative.", "start at 0 seconds or later")
    if b <= a:
        raise ToolError("The end time must be after the start time.", "increase the end time")
    if b - a > max_duration:
        raise ToolError(f"Manual clips are limited to {max_duration:g} seconds for now.", "select a shorter range")
    return round(a, 3), round(b, 3)


def trim_video(source: Path, start: float, end: float, output: Path) -> Path:
    """Accurately trim a local video to a normalized H.264/AAC MP4."""
    a, b = validate_window(start, end)
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file():
        raise ToolError(f"Video file not found: {source}", "upload the video again or check the source path")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.stem + ".part.mp4")
    tmp.unlink(missing_ok=True)
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{a:.3f}", "-i", str(source), "-t", f"{b-a:.3f}",
            "-map", "0:v:0", "-map", "0:a:0?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", str(tmp),
        ],
        "manual clip export",
    )
    if not tmp.is_file() or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        raise ToolError("FFmpeg did not produce a clip.", "check that the selected time range contains video")
    tmp.replace(output)
    return output


def make_manual_clip(source: str, start: float, end: float, output: Path) -> Path:
    """Download an exact VOD URL slice with yt-dlp, or trim a local file with FFmpeg."""
    a, b = validate_window(start, end)
    if str(source).lower().startswith(("http://", "https://")):
        from streamclipper.download import download_slice

        return download_slice(source, a, b, output)
    return trim_video(Path(source), a, b, output)
