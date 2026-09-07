import io
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native'))
import host


class HostTests(unittest.TestCase):
    def test_normalizes_supported_urls(self):
        for url in ['https://youtu.be/AbCdEf012_-?si=test', 'https://www.youtube.com/watch?v=AbCdEf012_-&list=abc', 'https://youtube.com/shorts/AbCdEf012_-']:
            self.assertEqual(host.validate_url(url), 'https://www.youtube.com/watch?v=AbCdEf012_-')

    def test_rejects_untrusted_urls(self):
        for url in ['http://youtu.be/AbCdEf012_-', 'https://youtube.com.evil.com/watch?v=AbCdEf012_-', 'https://evil@youtube.com/watch?v=AbCdEf012_-', 'https://youtube.com:444/watch?v=AbCdEf012_-', 'file:///etc/passwd', 'https://youtu.be/abc', None]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                host.validate_url(url)

    def test_round_trip_unicode_protocol(self):
        stream = io.BytesIO()
        host.write_message({'title': 'Vídeo'}, stream)
        stream.seek(0)
        self.assertEqual(host.read_message(stream), {'title': 'Vídeo'})

    def test_rejects_truncated_and_oversized_messages(self):
        for data in [b'\x01', struct.pack('<I', 100) + b'{}', struct.pack('<I', 1048577), struct.pack('<I', 2) + b'[]']:
            with self.subTest(data=data), self.assertRaises(ValueError):
                host.read_message(io.BytesIO(data))
        self.assertIsNone(host.read_message(io.BytesIO()))

    def test_quality_limits_use_distinct_output_names(self):
        names = []
        for quality in ['720', '2160']:
            command = host.build_command('https://youtu.be/AbCdEf012_-', quality, Path('/tmp/downloads'))
            name = command[command.index('-o') + 1]
            self.assertIn(f'max-{quality}p', name)
            names.append(name)
        self.assertNotEqual(names[0], names[1])

    def test_command_limits_height_and_merges_audio(self):
        cmd = host.build_command('https://youtu.be/AbCdEf012_-', '2160', Path('/tmp/downloads'))
        self.assertIn('bv*[height<=2160]+ba/b[height<=2160]', cmd)
        self.assertIn('--no-playlist', cmd)
        self.assertIn('--ignore-config', cmd)
        self.assertIn('--no-quiet', cmd)
        self.assertGreater(cmd.index('--no-quiet'), cmd.index('--print'))
        self.assertEqual(cmd[-2:], ['--', 'https://www.youtube.com/watch?v=AbCdEf012_-'])
        for quality in ['0', '9999', '2160; touch /tmp/bad', None]:
            with self.assertRaises(ValueError):
                host.build_command('https://youtu.be/AbCdEf012_-', quality, Path('/tmp'))

if __name__ == '__main__':
    unittest.main()
