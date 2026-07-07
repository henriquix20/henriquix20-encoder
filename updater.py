# ═══════════════════════════════════════════════════════
#  Henriquix20 Encoder — updater.py
#  Checks GitHub Releases for newer versions.
# ═══════════════════════════════════════════════════════

import threading
import urllib.request
import urllib.error
import json

from config import APP_VERSION, GITHUB_API, DOWNLOAD_URL


def _parse_version(v):
    """Convert '1.2.3' to (1, 2, 3) for comparison."""
    try:
        return tuple(int(x) for x in v.strip().lstrip('v').split('.'))
    except Exception:
        return (0, 0, 0)


def check_for_update(callback):
    """
    Checks GitHub API for latest release in a background thread.
    Calls callback(latest_version, download_url) if a newer version exists.
    Calls callback(None, None) if up to date or check fails.
    """
    def _check():
        try:
            req = urllib.request.Request(
                GITHUB_API,
                headers={'User-Agent': 'henriquix20-encoder-updater'}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            latest_tag = data.get('tag_name', '')
            latest_ver = _parse_version(latest_tag)
            current_ver = _parse_version(APP_VERSION)

            if latest_ver > current_ver:
                assets = data.get('assets', [])
                # Try to find a .exe asset
                dl_url = next(
                    (a['browser_download_url'] for a in assets
                     if a['name'].endswith('.exe')),
                    DOWNLOAD_URL  # fallback to releases page
                )
                callback(latest_tag, dl_url)
            else:
                callback(None, None)

        except Exception:
            callback(None, None)

    threading.Thread(target=_check, daemon=True).start()