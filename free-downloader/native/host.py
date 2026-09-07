#!/usr/bin/env python3
"""Native Messaging bridge. Stdout is exclusively framed JSON."""
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HOST_NAME = 'com.hdoria.free_video_downloader'
MAX_MESSAGE = 1024 * 1024
QUALITIES = {'720', '1080', '1440', '2160'}


def validate_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError('Cole um link válido do YouTube.')
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Use um link HTTPS do YouTube.')
    if parsed.hostname == 'youtu.be':
        video_id = parsed.path.removeprefix('/')
    elif parsed.hostname in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}:
        if parsed.path == '/watch':
            video_id = parse_qs(parsed.query).get('v', [''])[0]
        elif parsed.path.startswith(('/shorts/', '/live/')):
            video_id = parsed.path.split('/')[-1]
        else:
            video_id = ''
    else:
        video_id = ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
        raise ValueError('Cole o link de um vídeo do YouTube.')
    return f'https://www.youtube.com/watch?v={video_id}'


def read_message(stream):
    header = stream.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise ValueError('Mensagem incompleta.')
    size = struct.unpack('<I', header)[0]
    if not 0 < size <= MAX_MESSAGE:
        raise ValueError('Tamanho inválido.')
    payload = stream.read(size)
    if len(payload) != size:
        raise ValueError('Mensagem incompleta.')
    message = json.loads(payload.decode('utf-8'))
    if not isinstance(message, dict):
        raise ValueError('Mensagem inválida.')
    return message


def write_message(message, stream):
    payload = json.dumps(message, ensure_ascii=False).encode('utf-8')
    stream.write(struct.pack('<I', len(payload)))
    stream.write(payload)
    stream.flush()


def build_command(url, quality, output_dir):
    url = validate_url(url)
    if quality not in QUALITIES:
        raise ValueError('Qualidade inválida.')
    command = [sys.executable, '-m', 'yt_dlp', '--ignore-config', '--no-playlist',
               '--no-colors', '--newline', '--progress', '--no-simulate',
               '--socket-timeout', '30', '--retries', '3', '--no-overwrites',
               '-f', f'bv*[height<={quality}]+ba/b[height<={quality}]',
               '--merge-output-format', 'mkv', '--restrict-filenames',
               '-P', str(output_dir), '-o', f'%(title).160B [%(id)s] [max-{quality}p].%(ext)s',
               '--progress-template', 'download:PROGRESS:%(progress._percent_str)s',
               '--print', 'after_move:FILE:%(filepath)j', '--no-quiet']
    ffmpeg = shutil.which('ffmpeg')
    node = shutil.which('node')
    if ffmpeg:
        command += ['--ffmpeg-location', str(Path(ffmpeg).parent)]
    if node:
        command += ['--js-runtimes', f'node:{node}']
    return command + ['--', url]


def download(message, emit):
    output_dir = Path.home() / 'Downloads' / 'Free Video Downloader'
    command = build_command(message.get('url'), message.get('quality'), output_dir)
    if not shutil.which('ffmpeg'):
        raise ValueError('Instale o FFmpeg e execute novamente o instalador do auxiliar.')
    output_dir.mkdir(parents=True, exist_ok=True)
    emit({'status': 'running', 'message': 'Buscando vídeo e áudio…', 'percent': 0})
    final_file = None
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding='utf-8', errors='replace') as process:
        try:
            for line in process.stdout:
                if line.startswith('PROGRESS:'):
                    match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if match:
                        emit({'status': 'running', 'message': 'Baixando vídeo ou áudio…',
                              'percent': min(100, float(match.group(1)))})
                elif line.startswith('FILE:'):
                    final_file = Path(json.loads(line[5:]))
                elif line.startswith('[Merger]'):
                    emit({'status': 'running', 'message': 'Juntando vídeo e áudio…', 'percent': 100})
            result = process.wait()
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise
    if result or final_file is None or not final_file.is_file():
        emit({'status': 'error', 'message': 'Não foi possível baixar. O vídeo pode estar indisponível ou exigir login. Atualize o yt-dlp e tente novamente.'})
    else:
        emit({'status': 'done', 'message': 'Salvo em Downloads/Free Video Downloader.',
              'filename': final_file.name, 'percent': 100})


def main():
    emit = lambda message: write_message(message, sys.stdout.buffer)
    try:
        while (message := read_message(sys.stdin.buffer)) is not None:
            try:
                if message.get('action') != 'download':
                    raise ValueError('Ação inválida.')
                download(message, emit)
            except (ValueError, TypeError):
                emit({'status': 'error', 'message': 'Pedido inválido. Confira o link, a qualidade e a instalação do auxiliar.'})
            except OSError:
                emit({'status': 'error', 'message': 'Falha ao executar o auxiliar ou salvar o arquivo.'})
    except (ValueError, UnicodeError):
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
