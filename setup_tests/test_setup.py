"""Setup regression tests: no credentials, model calls, or package downloads."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import configure


class ConfigurationTests(unittest.TestCase):
    def test_json_dotenv_single_quotes_and_crlf(self):
        self.assertEqual(configure.parse_config('HR_AGENT_ENGINE="openai"\r\nOPENAI_API_KEY=local-demo\r\nHR_AGENT_MODEL=\'qwen3:4b\'\n')['HR_AGENT_MODEL'], 'qwen3:4b')

    def test_invalid_profile_never_echoes_value(self):
        marker = 'not-a-real-key-sensitive-marker'
        for text in [marker, 'OPENAI_API_KEY="'+marker]:
            with self.assertRaises(ValueError) as caught:
                configure.parse_config(text)
            self.assertNotIn(marker, str(caught.exception))

    def test_profile_switch_removes_other_provider_credentials(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(configure, 'ROOT', Path(directory)), patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-only'}, clear=False):
            (Path(directory)/'.env.local').write_text('HR_AGENT_ENGINE="openai"\nOPENAI_API_KEY="local-demo"\n', encoding='utf-8')
            configure.load_config('local')
            self.assertNotIn('ANTHROPIC_API_KEY', os.environ)
            self.assertEqual(os.environ['OPENAI_API_KEY'], 'local-demo')

    def test_bom_and_single_profile_auto_selection(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(configure, 'ROOT', Path(directory)), patch.dict(os.environ, {}, clear=False):
            (Path(directory)/'.env.local').write_text('\ufeffHR_AGENT_MODEL="qwen3:4b"\n', encoding='utf-8')
            configure.load_config()
            self.assertEqual(os.environ['HR_AGENT_MODEL'], 'qwen3:4b')

    def test_multiple_profiles_require_selection(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(configure, 'ROOT', Path(directory)):
            for name in ['api','local']:
                (Path(directory)/('.env.'+name)).write_text('', encoding='utf-8')
            with self.assertRaises(SystemExit):
                configure.load_config()

    def test_hidden_input_never_falls_back_to_echo(self):
        def unavailable(*args):
            warnings.warn('No hidden input', configure.getpass.GetPassWarning)
        with patch.object(configure.getpass, 'getpass', side_effect=unavailable):
            with self.assertRaises(SystemExit) as caught:
                configure.hidden_key('Key: ')
            self.assertIn('Hidden input is unavailable', str(caught.exception))

    def test_offline_launcher_does_not_read_broken_credentials(self):
        # A fake interpreter records launcher arguments without running an agent.
        import runpy
        with patch.object(sys, 'argv', ['launch.py', 'tests']), patch.object(configure, 'load_config', side_effect=AssertionError('must not load keys')), patch('subprocess.call', return_value=0), patch.object(Path, 'exists', return_value=True):
            with self.assertRaises(SystemExit) as caught:
                runpy.run_path(str(ROOT/'launch.py'), run_name='__main__')
            self.assertEqual(caught.exception.code, 0)

    def test_local_configuration_without_secret_input(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(configure, 'ROOT', Path(directory)), patch.object(sys, 'argv', ['configure.py','local']), patch('builtins.input', return_value=''), patch.object(configure, 'hidden_key', side_effect=AssertionError('local needs no key')), contextlib.redirect_stdout(io.StringIO()):
            configure.main()
            values=configure.parse_config((Path(directory)/'.env.local').read_text(encoding='utf-8'))
            self.assertEqual(values['OPENAI_BASE_URL'], 'http://127.0.0.1:11434/v1/')
            if os.name != 'nt':
                self.assertEqual((Path(directory)/'.env.local').stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
