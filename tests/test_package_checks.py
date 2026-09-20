# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import hashlib
import subprocess
import sys
import zipfile

from pathlib import Path

import pytest

from run_package_checks import ROOT, RUNTIME_DATA, check_wheel, run, source_files


def test_source_selection() -> None:
  files = set(source_files(ROOT))
  assert set(RUNTIME_DATA) <= files
  assert {f'bazi/calendar/hko_data/data/{year}.txt' for year in range(1901, 2101)} <= files
  assert {'bazi/py.typed', 'tests/package_smoke.py', '.github/workflows/release.yml'} <= files
  assert not any('/references/' in name or name.endswith('.ipynb') for name in files)
  assert {p.relative_to(ROOT).as_posix() for p in (ROOT / 'bazi').rglob('*.py')} <= files


@pytest.mark.parametrize('change, rejected', [
  ('none', False), ('zip-comment', False), ('missing-data', True),
  ('missing-typing', True), ('extra-source', True), ('changed-bytes', True),
  ('duplicate', True),
])
def test_wheel_roster(tmp_path: Path, change: str, rejected: bool) -> None:
  content = {'bazi/__init__.py': b'', 'bazi/py.typed': b'', RUNTIME_DATA[0]: b'calendar'}
  expected = {name: hashlib.sha256(value).hexdigest() for name, value in content.items()}
  licenses = {'LICENSE': hashlib.sha256(b'license').hexdigest()}
  if change == 'missing-data':
    del content[RUNTIME_DATA[0]]
  elif change == 'missing-typing':
    del content['bazi/py.typed']
  elif change == 'extra-source':
    content['src/__init__.py'] = b''
  elif change == 'changed-bytes':
    content[RUNTIME_DATA[0]] = b'different'
  wheel = tmp_path / 'bazi-1.0.0-py3-none-any.whl'
  with zipfile.ZipFile(wheel, 'w') as archive:
    for name, value in reversed(tuple(content.items())):
      archive.writestr(name, value)
    for name in ('METADATA', 'WHEEL', 'top_level.txt', 'RECORD'):
      archive.writestr('bazi-1.0.0.dist-info/' + name, '')
    archive.writestr('bazi-1.0.0.dist-info/licenses/LICENSE', b'license')
    if change == 'zip-comment':
      archive.comment = b'Harmless archive comment'
    elif change == 'duplicate':
      with pytest.warns(UserWarning, match='Duplicate name'):
        archive.writestr('bazi/__init__.py', b'')
  if rejected:
    message = r'Duplicate wheel members: .*bazi/__init__\.py' if change == 'duplicate' else 'Wheel (file roster mismatch|bytes differ)'
    with pytest.raises(ValueError, match=message):
      check_wheel(wheel, expected, licenses)
  else:
    check_wheel(wheel, expected, licenses)


def test_real_subprocess_failure(tmp_path: Path) -> None:
  run([sys.executable, '-I', '-c', 'print("positive subprocess control")'], tmp_path)
  with pytest.raises(subprocess.CalledProcessError) as caught:
    run([sys.executable, '-I', '-c', 'import sys; print("reached failure control"); sys.exit(7)'], tmp_path)
  assert caught.value.returncode == 7
