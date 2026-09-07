import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native'))
import host


class ProcessTests(unittest.TestCase):
    def test_real_process_frames_success_and_saves_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'ffmpeg').write_text('#!/bin/sh\nexit 0\n')
            (root / 'ffmpeg').chmod(0o700)
            (root / 'yt_dlp.py').write_text('''import json, pathlib, sys
folder = pathlib.Path(sys.argv[sys.argv.index('-P') + 1])
file = folder / 'test.mkv'
file.write_bytes(b'test fixture')
print('PROGRESS: 45.2%')
print('[Merger] Merging formats')
print('FILE:' + json.dumps(str(file)))
''')
            stream = io.BytesIO()
            host.write_message({'action': 'download', 'url': 'https://youtu.be/AbCdEf012_-', 'quality': '2160'}, stream)
            process = subprocess.run([sys.executable, str(Path(host.__file__))], input=stream.getvalue(), capture_output=True, env={**os.environ, 'HOME': directory, 'PYTHONPATH': directory, 'PATH': directory + os.pathsep + os.environ['PATH']}, timeout=10)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stderr, b'')
            result = io.BytesIO(process.stdout)
            messages = []
            while (message := host.read_message(result)) is not None:
                messages.append(message)
            self.assertEqual(messages[-1]['status'], 'done')
            self.assertEqual(messages[-1]['filename'], 'test.mkv')
            self.assertTrue(any(message.get('percent') == 45.2 for message in messages))
            self.assertTrue((root / 'Downloads/Free Video Downloader/test.mkv').is_file())

    def test_unknown_actions_are_sanitized(self):
        stream = io.BytesIO()
        host.write_message({'action': 'delete'}, stream)
        process = subprocess.run([sys.executable, str(Path(host.__file__))], input=stream.getvalue(), capture_output=True, timeout=10)
        message = host.read_message(io.BytesIO(process.stdout))
        self.assertEqual(message['status'], 'error')
        self.assertNotIn('Traceback', str(message))
        self.assertNotIn(str(Path.home()), str(message))


if __name__ == '__main__':
    unittest.main()
