import os
import subprocess
from pathlib import Path

from ..app.utils.file_handlers import is_video_file  # noqa: F401 (re-exported for convenience)


def _resolve_executable(name: str) -> str:
    """Return a workspace-local executable when available, otherwise fall back to PATH."""
    candidates = []
    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = repo_root.parent
    local_candidates = [
        workspace_root / "bin" / "ffmpeg-build" / "ffmpeg-master-latest-win64-gpl" / "bin" / name,
        workspace_root / "bin" / "ffmpeg-build" / "ffmpeg-master-latest-win64-gpl" / "bin" / f"{name}.exe",
        workspace_root / "bin" / "ffmpeg-build" / "ffmpeg-master-latest-win64-gpl" / name,
        workspace_root / "bin" / "ffmpeg-build" / "ffmpeg-master-latest-win64-gpl" / f"{name}.exe",
        workspace_root / "bin" / "ffmpeg-portable" / name,
        workspace_root / "bin" / "ffmpeg-portable" / f"{name}.exe",
        workspace_root / "bin" / name,
        workspace_root / "bin" / f"{name}.exe",
    ]
    for candidate in local_candidates:
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    if os.name == "nt":
        return f"{name}.exe"
    return name


def probe_duration(path: Path) -> float:
    command = [
        _resolve_executable("ffprobe"), "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")
    return float(result.stdout.strip())


def extract_audio(input_path: Path, output_path: Path) -> Path:
    output_path = output_path.with_suffix(".wav")
    command = [
        _resolve_executable("ffmpeg"), "-y", "-i", str(input_path),
        "-ar", "16000", "-ac", "1",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg extraction failed: {result.stderr.strip()}")
    return output_path


def prepare_audio_file(upload_path: Path) -> Path:
    from ..app.utils.file_handlers import is_video_file as _is_video
    if _is_video(upload_path):
        audio_path = upload_path.parent / f"{upload_path.stem}_extracted.wav"
        return extract_audio(upload_path, audio_path)
    return upload_path
