# ═══════════════════════════════════════════════════════
#  Henriquix20 Encoder — encoder.py
#  Direct file copy (no FFmpeg re-encode).
#  The patch is applied separately by patcher.py.
# ═══════════════════════════════════════════════════════

import os
import subprocess
from config import OUTPUT_SUFFIX


def check_ffmpeg():
    """Check if FFmpeg is available (used only for optional encode mode)."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_output_path(input_path, output_dir=None):
    """Return output file path with _hx20 suffix."""
    folder   = output_dir if output_dir and output_dir != "same" else os.path.dirname(os.path.abspath(input_path))
    basename = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(folder, f"{basename}{OUTPUT_SUFFIX}.mp4")


def copy_file(input_path, output_path, log_cb=None, progress_cb=None):
    """
    Copy file byte-for-byte — no re-encoding, no quality loss.
    The patch will be applied on top of this copy.
    """
    def log(msg):
        if log_cb: log_cb(msg)

    log("Copying file (no re-encode)...")

    try:
        total  = os.path.getsize(input_path)
        copied = 0
        chunk  = 1024 * 1024 * 4   # 4 MB chunks

        with open(input_path, 'rb') as src, open(output_path, 'wb') as dst:
            while True:
                data = src.read(chunk)
                if not data:
                    break
                dst.write(data)
                copied += len(data)
                if progress_cb and total > 0:
                    pct = min((copied / total) * 85, 85)
                    progress_cb(pct)

        log("Copy complete.")
        return True

    except Exception as e:
        log(f"ERROR during copy: {e}")
        return False
