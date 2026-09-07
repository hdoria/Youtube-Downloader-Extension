#!/usr/bin/env python3
"""Install a user-scoped Chrome Native Messaging host without sudo."""
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    if sys.platform != 'darwin':
        raise SystemExit('Este instalador atende macOS.')
    if len(sys.argv) != 2 or not re.fullmatch('[a-p]{32}', sys.argv[1]):
        raise SystemExit('Uso: python3 install_macos.py ID_DA_EXTENSAO (32 letras a-p)')
    ffmpeg = shutil.which('ffmpeg')
    node = shutil.which('node')
    if not ffmpeg or not node:
        raise SystemExit('Instale FFmpeg e Node.js antes: brew install ffmpeg node')
    root = Path.home() / '.local/share/free-video-downloader'
    root.mkdir(parents=True, exist_ok=True)
    python = root / 'venv/bin/python'
    if not python.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(root / 'venv')], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '--upgrade', 'yt-dlp[default]'], check=True)
    shutil.copy2(Path(__file__).with_name('host.py'), root / 'host.py')
    launcher = root / 'launch.sh'
    tool_path = ':'.join(dict.fromkeys([str(Path(ffmpeg).parent), str(Path(node).parent), '/usr/bin', '/bin']))
    launcher.write_text('#!/bin/sh\nexport PATH=' + shlex.quote(tool_path) + '\nexec ' + shlex.quote(str(python)) + ' ' + shlex.quote(str(root / 'host.py')) + '\n')
    launcher.chmod(0o700)
    manifest = {
        'name': 'com.hdoria.free_video_downloader',
        'description': 'Free Video Downloader local helper',
        'path': str(launcher), 'type': 'stdio',
        'allowed_origins': [f'chrome-extension://{sys.argv[1]}/'],
    }
    directory = Path.home() / 'Library/Application Support/Google/Chrome/NativeMessagingHosts'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'com.hdoria.free_video_downloader.json').write_text(json.dumps(manifest, indent=2))
    print('Auxiliar instalado. Recarregue a extensão no Chrome.')


if __name__ == '__main__':
    main()
