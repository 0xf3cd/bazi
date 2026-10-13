# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[2]
BLOCKS = tuple(re.findall(r'^```python\n(.*?)^```$', (ROOT / 'README.md').read_text(encoding='utf-8'), re.MULTILINE | re.DOTALL))


def test_readme_has_python_examples() -> None:
  assert BLOCKS


@pytest.mark.parametrize('block', BLOCKS, ids=[f'example-{index}' for index in range(len(BLOCKS))])
def test_readme_python_example(block: str, tmp_path: Path) -> None:
  result = subprocess.run(
    [sys.executable, '-B', '-c', block],
    cwd=tmp_path,
    env={**os.environ, 'PYTHONPATH': str(ROOT), 'PYTHONDONTWRITEBYTECODE': '1'},
    capture_output=True, text=True, encoding='utf-8', timeout=60, check=False,
  )
  assert result.returncode == 0, result.stdout + result.stderr
