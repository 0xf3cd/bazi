# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import hashlib
import importlib.util
import io
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import venv
import zipfile

from pathlib import Path
from typing import Literal
from unittest.mock import Mock

import pytest

import run_package_checks as package_checks

from run_package_checks import (
  ROOT, RUNTIME_DATA, Environment, Installer, _INSTALLATION, build_context, check_description,
  check_packages, check_wheel, collect_environment, observe_build_installer, outer_installers, pip_version,
  run, source_files, source_identity,
)


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
  ('wrong-description', True), ('wrong-description-type', True),
])
def test_wheel_roster(tmp_path: Path, change: str, rejected: bool) -> None:
  readme = b'# Bazi\n'
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
    header = b'Description-Content-Type: text/plain' if change == 'wrong-description-type' else b'Description-Content-Type: text/markdown'
    body = b'Wrong README\n' if change == 'wrong-description' else readme
    archive.writestr('bazi-1.0.0.dist-info/METADATA', header + b'\n\n' + body)
    for name in ('WHEEL', 'top_level.txt', 'RECORD'):
      archive.writestr('bazi-1.0.0.dist-info/' + name, b'')
    archive.writestr('bazi-1.0.0.dist-info/licenses/LICENSE', b'license')
    if change == 'zip-comment':
      archive.comment = b'Harmless archive comment'
    elif change == 'duplicate':
      with pytest.warns(UserWarning, match='Duplicate name'):
        archive.writestr('bazi/__init__.py', b'')
  if rejected:
    message = r'Duplicate wheel members: .*bazi/__init__\.py' if change == 'duplicate' else ('Description' if change.startswith('wrong-description') else 'Wheel (file roster mismatch|bytes differ)')
    with pytest.raises(ValueError, match=message):
      check_wheel(wheel, expected, licenses, readme)
  else:
    check_wheel(wheel, expected, licenses, readme)


@pytest.mark.parametrize('header, body, accepted', [
  (b'Description-Content-Type: text/markdown', b'# Bazi\n', True),
  (b'description-content-type: text/markdown', b'# Bazi\n', True),
  (b'Description-Content-Type: text/plain', b'# Bazi\n', False),
  (b'', b'# Bazi\n', False),
  (b'Description-Content-Type: text/markdown\nDescription-Content-Type: text/plain', b'# Bazi\n', False),
  (b'Description-Content-Type: text/markdown', b'Wrong README\n', False),
  (b'Description-Content-Type: text/markdown', b'# Bazi\n\n', False),
  (b'Description-Content-Type: text/markdown', b'', False),
  (b'Description-Content-Type: text/markdown', b'# Bazi', False),
])
def test_description_source_and_content_type(header: bytes, body: bytes, accepted: bool) -> None:
  content = b'Metadata-Version: 2.4' + (b'\n' + header if header else b'') + b'\n\n' + body
  if accepted:
    check_description(content, b'# Bazi\n', 'artifact')
  else:
    with pytest.raises(ValueError, match='Description'):
      check_description(content, b'# Bazi\n', 'artifact')


@pytest.mark.parametrize('metadata_newline, source', [
  (b'\n', b'# Bazi\r\n'), (b'\r\n', b'# Bazi\n'),
  (b'\r\n', b'# Bazi\r\n'), (b'\n', b'# Bazi'),
])
def test_description_accepts_builder_newlines(metadata_newline: bytes, source: bytes) -> None:
  content = metadata_newline.join((
    b'Metadata-Version: 2.4', b'Description-Content-Type: text/markdown', b'', b'# Bazi', b'',
  ))
  check_description(content, source, 'artifact')


def test_description_rejects_missing_separator() -> None:
  content = b'Metadata-Version: 2.4\nDescription-Content-Type: text/markdown'
  with pytest.raises(ValueError, match='Description content type mismatch'):
    check_description(content, b'', 'artifact')


def test_real_subprocess_failure(tmp_path: Path) -> None:
  run([sys.executable, '-I', '-c', 'print("positive subprocess control")'], tmp_path)
  with pytest.raises(subprocess.CalledProcessError) as caught:
    run([sys.executable, '-I', '-c', 'import sys; print("reached failure control"); sys.exit(7)'], tmp_path)
  assert caught.value.returncode == 7


@pytest.mark.parametrize('version', ['25.0.1', '25.1rc1', '25.0.1.dev0', '25.0.1.post1', '25.0.1+vendor.1'])
def test_pip_versions_discard_paths(version: str) -> None:
  assert pip_version(f'pip {version} from C:\\with space\\pip (python 3.12)') == version


@pytest.mark.parametrize('line', ['pip file:///private from /pip (python 3.12)', 'pip not-a-version from /pip (python 3.12)', 'warning', ''])
def test_pip_output_rejects_invalid_values(line: str) -> None:
  with pytest.raises(ValueError):
    pip_version(line)


@pytest.mark.parametrize('count', [0, 1, 2, 3, 4])
def test_outer_receipt_roster(tmp_path: Path, count: int) -> None:
  receipt = tmp_path / 'receipt'
  receipt.write_text('pip 25.0.1 from /synthetic-private/pip (python 3.12)\n' * count, encoding='utf-8')
  if count == 3:
    assert outer_installers(receipt) == [{'name': 'pip', 'version': '25.0.1', 'scope': 'runner'}]
  else:
    with pytest.raises(ValueError, match='three outer'):
      outer_installers(receipt)
  receipt.unlink()
  with pytest.raises(FileNotFoundError):
    outer_installers(receipt)


def test_build_context_restores_state(monkeypatch: pytest.MonkeyPatch) -> None:
  logger = logging.getLogger('build')
  level, handlers = logger.level, tuple(logger.handlers)
  for name in ('PYTHONPATH', 'PYTHONHOME', 'MYPYPATH'):
    monkeypatch.setenv(name, 'synthetic-private-placeholder')
  with pytest.raises(RuntimeError), build_context():
    assert all(name not in os.environ for name in ('PYTHONPATH', 'PYTHONHOME', 'MYPYPATH'))
    assert len(logger.handlers) == len(handlers) + 1
    raise RuntimeError('cleanup control')
  assert logger.level == level and tuple(logger.handlers) == handlers
  assert all(os.environ[name] == 'synthetic-private-placeholder' for name in ('PYTHONPATH', 'PYTHONHOME', 'MYPYPATH'))


def test_observer_rejects_unknown_and_restores(monkeypatch: pytest.MonkeyPatch) -> None:
  records: list[Installer] = []
  token = _INSTALLATION.set(('target-python', records))
  try:
    with pytest.raises(ValueError, match='Unsupported build'):
      observe_build_installer('subprocess.Popen', ('unknown', ['unknown'], None, None))
    with pytest.raises(TypeError, match='Unsupported build'):
      observe_build_installer('subprocess.Popen', ('unknown', 'unknown', None, None))
    def fail(*args: object, **kwargs: object) -> str:
      assert _INSTALLATION.get() is None
      raise RuntimeError('query failed')
    monkeypatch.setattr(subprocess, 'check_output', fail)
    with pytest.raises(RuntimeError, match='query failed'):
      observe_build_installer('subprocess.Popen', ('target-python', ['target-python', '-Im', 'pip', 'install'], None, None))
    assert _INSTALLATION.get() == ('target-python', records)
  finally:
    _INSTALLATION.reset(token)
  assert _INSTALLATION.get() is None and records == []


@pytest.mark.parametrize('scope', ['runner', 'target'])
@pytest.mark.parametrize('serialized', [False, True])
def test_installer_commandline_keeps_identity(
  monkeypatch: pytest.MonkeyPatch, scope: Literal['runner', 'target'], serialized: bool,
) -> None:
  python = 'C:\\target space\\python.exe'
  prefix = [sys.executable, '-m', 'pip', '--python', python] if scope == 'runner' else [python, '-Im', 'pip']
  command = [*prefix, 'install', '--no-input', '-r', 'C:\\requirements space\\input.txt']
  records: list[Installer] = []
  query = Mock(return_value='pip 25.0.1 from discarded path (python 3.12)')
  monkeypatch.setattr(subprocess, 'check_output', query)
  token = _INSTALLATION.set((python, records))
  try:
    observe_build_installer('subprocess.Popen', (prefix[0], subprocess.list2cmdline(command) if serialized else command, None, None))
    assert _INSTALLATION.get() == (python, records)
  finally:
    _INSTALLATION.reset(token)
  assert records == [{'name': 'pip', 'version': '25.0.1', 'scope': scope}]
  query_prefix = [sys.executable, '-m', 'pip'] if scope == 'runner' else prefix
  assert query.call_count == 1 and query.call_args.args[0] == [*query_prefix, '--version']


@pytest.mark.parametrize('change', ['other-python', 'other-target', 'not-install', 'install-suffix'])
def test_commandline_rejects_unknown(change: str) -> None:
  python = 'C:\\target space\\python.exe'
  command = [sys.executable, '-m', 'pip', '--python', python, 'install', '-r', 'input.txt']
  if change == 'other-python':
    command[0] += '-other'
  elif change == 'other-target':
    command[4] += '-other'
  elif change == 'not-install':
    command[5] = 'uninstall'
  elif change == 'install-suffix':
    command[5] = 'installer'
  token = _INSTALLATION.set((python, []))
  try:
    with pytest.raises(TypeError, match='^Unsupported build installer invocation$'):
      observe_build_installer('subprocess.Popen', (command[0], subprocess.list2cmdline(command), None, None))
  finally:
    _INSTALLATION.reset(token)


@pytest.mark.parametrize('change', ['none', 'dirty', 'ignored', 'no-git', 'untracked', 'nested'])
def test_source_identity_requires_tracked_input(tmp_path: Path, change: str) -> None:
  subprocess.run(['git', 'init', str(tmp_path)], capture_output=True, check=True)
  (tmp_path / 'input.py').write_text('X = 1\n', encoding='utf-8')
  (tmp_path / '.gitignore').write_text('lib/\n', encoding='utf-8')
  # Synthetic history uses plumbing so local signing and credentials are never invoked.
  subprocess.run(['git', 'add', 'input.py', '.gitignore'], cwd=tmp_path, check=True)
  tree = subprocess.check_output(['git', 'write-tree'], cwd=tmp_path, text=True).strip()
  content = f'tree {tree}\nauthor Fixture <fixture@example.invalid> 1000000000 +0000\ncommitter Fixture <fixture@example.invalid> 1000000000 +0000\n\nfixture\n'
  commit = subprocess.check_output(['git', 'hash-object', '-t', 'commit', '-w', '--stdin'], input=content.encode('utf-8'), cwd=tmp_path).decode('ascii').strip()
  subprocess.run(['git', 'update-ref', 'HEAD', commit], cwd=tmp_path, check=True)
  files: tuple[str, ...] = ('input.py',)
  if change == 'dirty':
    (tmp_path / 'input.py').write_text('X = 2\n', encoding='utf-8')
  elif change == 'ignored':
    (tmp_path / 'lib').mkdir()
    (tmp_path / 'lib/extra.py').write_text('X = 3\n', encoding='utf-8')
    files += ('lib/extra.py',)
  elif change == 'no-git':
    (tmp_path / '.git').rename(tmp_path / 'git-data')
  elif change == 'untracked':
    (tmp_path / 'not-an-input').write_text('untracked', encoding='utf-8')
  elif change == 'nested':
    (tmp_path / 'nested').mkdir()
    tmp_path /= 'nested'
  if change == 'none':
    assert source_identity(tmp_path, files) == commit
  elif change == 'no-git':
    # A test temp root can itself be inside another checkout.
    parent = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=tmp_path, capture_output=True, text=True, check=False)
    if parent.returncode:
      with pytest.raises(subprocess.CalledProcessError) as caught:
        source_identity(tmp_path, files)
      assert caught.value.cmd == ['git', 'rev-parse', '--show-toplevel']
    else:
      with pytest.raises(ValueError, match='^Environment export requires a source checkout$'):
        source_identity(tmp_path, files)
  else:
    message = {'dirty': 'a clean source checkout', 'untracked': 'a clean source checkout',
      'ignored': 'tracked source inputs', 'nested': 'a source checkout'}[change]
    with pytest.raises(ValueError, match='Environment export requires ' + message + '$'):
      source_identity(tmp_path, files)


def test_output_conflicts_precede_build(tmp_path: Path) -> None:
  output = tmp_path / 'output'
  output.mkdir()
  (output / 'existing').write_text('keep', encoding='utf-8')
  with pytest.raises(ValueError, match='Output directory'):
    check_packages(tmp_path / 'no-source', tmp_path / 'no-work', output)
  report = tmp_path / 'report.json'
  report.write_text('keep', encoding='utf-8')
  with pytest.raises(ValueError, match='report must not exist'):
    check_packages(tmp_path / 'no-source', tmp_path / 'no-work', None, report)
  assert report.read_text() == 'keep' and (output / 'existing').read_text() == 'keep'


@pytest.mark.parametrize('kind', ['wheel', 'sdist'])
@pytest.mark.parametrize('runner_pip', [False, True])
@pytest.mark.skipif(importlib.util.find_spec('build') is None, reason='The partial PyPy job does not install build tools.')
def test_real_build_environment_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: Literal['wheel', 'sdist'], runner_pip: bool) -> None:
  source, wheels = tmp_path / 'source', tmp_path / 'wheels'
  source.mkdir()
  wheels.mkdir()
  for name, version, dependency in (('statdep', '1.0', ''), ('dynreq', '2.0', 'Requires-Dist: trans==3.0\n'), ('trans', '3.0', ''), ('pip', '99.0', '')):
    with zipfile.ZipFile(wheels / f'{name}-{version}-py3-none-any.whl', 'w') as archive:
      archive.writestr(f'{name}-{version}.dist-info/METADATA', f'Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n{dependency}')
      archive.writestr(f'{name}-{version}.dist-info/WHEEL', 'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n')
      archive.writestr(f'{name}-{version}.dist-info/RECORD', '')
  (source / 'pyproject.toml').write_text('[build-system]\nrequires = ["statdep==1.0"]\nbuild-backend = "backend"\nbackend-path = ["."]\n', encoding='utf-8')
  (source / 'backend.py').write_text('''from pathlib import Path
def get_requires_for_build_wheel(config_settings=None):
  return ['dynreq==2.0', 'pip==99.0']
def get_requires_for_build_sdist(config_settings=None):
  return ['trans==3.0', 'pip==99.0']
def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
  path = Path(wheel_directory) / 'fixture-1.0-py3-none-any.whl'
  path.write_bytes(b'wheel')
  return path.name
def build_sdist(sdist_directory, config_settings=None):
  path = Path(sdist_directory) / 'fixture-1.0.tar.gz'
  path.write_bytes(b'sdist')
  return path.name
''', encoding='utf-8')
  for name, value in {'PIP_NO_INDEX': '1', 'PIP_CONFIG_FILE': os.devnull, 'PIP_FIND_LINKS': str(wheels),
    'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'TMPDIR': str(tmp_path)}.items():
    monkeypatch.setenv(name, value)
  outer = tmp_path / 'outer'
  venv.EnvBuilder(with_pip=runner_pip).create(outer)
  python = outer / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
  site = Path(subprocess.check_output([str(python), '-I', '-c', 'import sysconfig; print(sysconfig.get_paths()["purelib"])'], text=True).strip())
  for name in ('build', 'packaging', 'pyproject_hooks'):
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.submodule_search_locations is not None
    shutil.copytree(next(iter(spec.submodule_search_locations)), site / name, ignore=shutil.ignore_patterns('__pycache__'))
  script = '''import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import run_package_checks as checks
environments = []
paths = []
original = checks.collect_environment
def collect(python, role, installers):
  paths.append(Path(python))
  return original(python, role, installers)
checks.collect_environment = collect
work = Path(sys.argv[2])
checks.build_artifact(work / 'source', work / 'out', sys.argv[3], 'synthetic', work, environments)
assert paths and all(not path.exists() for path in paths)
print('RESULT ' + json.dumps(environments))
'''
  result = subprocess.run([str(python), '-I', '-c', script, str(ROOT), str(tmp_path), kind], capture_output=True, text=True, env=dict(os.environ), check=False)
  assert result.returncode == 0, result.stdout + result.stderr
  records = json.loads(next(line.removeprefix('RESULT ') for line in result.stdout.splitlines() if line.startswith('RESULT ')))
  record, = records
  assert record['distributions']['statdep'] == '1.0'
  assert record['distributions']['trans'] == '3.0'
  assert ('dynreq' in record['distributions']) == (kind == 'wheel')
  assert record['distributions']['pip'] == '99.0'
  assert {installer['scope'] for installer in record['installers']} == {'runner' if runner_pip else 'target'}
  assert all(installer['version'] != '99.0' for installer in record['installers'])
  encoded = json.dumps(record)
  assert str(tmp_path) not in encoded and 'direct_url' not in encoded


def test_collector_uses_target_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  venv.EnvBuilder(with_pip=True).create(tmp_path / 'target')
  python = tmp_path / 'target' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
  records: list[Installer] = [{'name': 'pip', 'version': '25.0.1', 'scope': 'target'}]
  monkeypatch.setenv('SYNTHETIC_PRIVATE', str(tmp_path))
  record = collect_environment(str(python), 'consumer', records)
  assert 'pip' in record['distributions'] and 'mypy' not in record['distributions']
  assert set(record) == {'role', 'python', 'platform', 'distributions', 'installers'}
  assert str(tmp_path) not in json.dumps(record) and 'SYNTHETIC_PRIVATE' not in json.dumps(record)
  with pytest.raises(ValueError, match='Missing installer'):
    collect_environment(str(python), 'consumer', [])


@pytest.mark.parametrize('change', ['report-only', 'receipt-only', 'no-pair', 'inside-source', 'inside-pair', 'same-path'])
def test_export_arguments_rejected(
  tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], change: str,
) -> None:
  root = tmp_path / 'checkout'
  monkeypatch.setattr(package_checks, 'ROOT', root)
  output, report, receipt = (tmp_path / name for name in ('pair', 'report.json', 'receipt.txt'))
  options = ['--output-dir', str(output), '--environment-report', str(report), '--outer-installer-report', str(receipt)]
  if change == 'report-only':
    options = options[:4]
  elif change == 'receipt-only':
    options = options[:2] + options[4:]
  elif change == 'no-pair':
    options = options[2:]
  elif change == 'inside-source':
    options[3] = str(root / 'environment-report.json')
  elif change == 'inside-pair':
    options[3] = str(output / 'report.json')
  elif change == 'same-path':
    options[3] = str(receipt)
  monkeypatch.setattr(sys, 'argv', ['run_package_checks.py', *options])
  message = ('Environment export requires --output-dir, --environment-report and --outer-installer-report together'
    if change in ('report-only', 'receipt-only', 'no-pair') else
    'Environment report and installer receipt must be different files' if change == 'same-path' else
    'Environment reports must stay outside the source checkout and artifact directory')
  if change in ('report-only', 'receipt-only', 'no-pair'):
    with pytest.raises(SystemExit) as caught:
      package_checks.main()
    assert caught.value.code == 2
    assert message in capsys.readouterr().err
  else:
    with pytest.raises(ValueError, match='^' + message + '$'):
      package_checks.main()
  assert not output.exists() and not report.exists()


def test_outer_receipt_versions_and_bad_line(tmp_path: Path) -> None:
  receipt = tmp_path / 'receipt'
  receipt.write_text(''.join(f'pip {version} from /discarded path/pip (python 3.12)\n'
    for version in ('25.0.1', '25.1rc1', '25.1rc1')), encoding='utf-8')
  assert outer_installers(receipt) == [{'name': 'pip', 'version': version, 'scope': 'runner'} for version in ('25.0.1', '25.1rc1')]
  receipt.write_text(receipt.read_text().replace('25.1rc1', 'file:///private'), encoding='utf-8')
  with pytest.raises(ValueError):
    outer_installers(receipt)


@pytest.mark.parametrize('change', [
  'none', 'identity-changed', 'source-changed', 'report-race', 'role-missing',
  'typing-internal-error', 'typing-missing-kongwang',
])
def test_export_flow_and_failure_boundaries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str) -> None:
  root, work, output = (tmp_path / name for name in ('checkout', 'work', 'dist'))
  root.mkdir()
  work.mkdir()
  source = {'README.md': b'# Fixture\n', 'pyproject.toml': b'[project]\nversion="1.0.0"\n',
    'LICENSE': b'license', 'THIRD_PARTY_NOTICES.md': b'notices', 'bazi/fixture.py': b'X = 1\n',
    'tests/package_smoke.py': b'# Fixture consumer\n'}
  for name, content in source.items():
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
  monkeypatch.setattr(package_checks, 'source_files', lambda directory: tuple(source))
  identity = Mock(side_effect=['a' * 40, 'b' * 40 if change == 'identity-changed' else 'a' * 40])
  monkeypatch.setattr(package_checks, 'source_identity', identity)
  version = Mock(return_value='2.4.0')
  monkeypatch.setattr(package_checks.importlib.metadata, 'version', version)
  states: dict[str, dict[str, str]] = {}
  observations: list[str] = []
  report = tmp_path / 'report.json'
  receipt = tmp_path / 'receipt.txt'
  receipt.write_text(''.join(f'pip {version} from /discarded path/pip (python 3.12)\n'
    for version in ('25.0.1', '25.1rc1', '25.1rc1')), encoding='utf-8')

  def collect(python: str, role: str, installers: list[Installer]) -> Environment:
    observations.append(role)
    distributions = states[python].copy() if role != 'outer' else {'outer-only': '1.0'}
    if role == 'outer':
      if change == 'source-changed':
        (root / 'bazi/fixture.py').write_bytes(b'X = 2\n')
      elif change == 'report-race':
        report.write_text('keep competing file', encoding='utf-8')
    return {'role': role, 'python': {'implementation': 'CPython', 'version': '3.12.13'},
      'platform': {'system': 'Linux', 'machine': 'x86_64'}, 'distributions': distributions,
      'installers': list(installers)}
  monkeypatch.setattr(package_checks, 'collect_environment', collect)

  def build(source_dir: Path, directory: Path, kind: str, role: str, cwd: Path, environments: list[Environment] | None) -> None:
    directory.mkdir()
    metadata = b'Description-Content-Type: text/markdown\n\n' + source['README.md']
    if kind == 'sdist':
      generated = {'PKG-INFO': metadata, 'setup.cfg': b''} | {
        'bazi.egg-info/' + name: b'' for name in ('PKG-INFO', 'SOURCES.txt', 'dependency_links.txt', 'top_level.txt')}
      with tarfile.open(directory / 'bazi-1.0.0.tar.gz', 'w:gz') as archive:
        for name, content in {**source, **generated}.items():
          item = tarfile.TarInfo('bazi-1.0.0/' + name)
          item.size = len(content)
          archive.addfile(item, io.BytesIO(content))
    else:
      with zipfile.ZipFile(directory / 'bazi-1.0.0-py3-none-any.whl', 'w') as archive:
        archive.comment = role.encode('utf-8')
        archive.writestr('bazi/fixture.py', source['bazi/fixture.py'])
        archive.writestr('bazi-1.0.0.dist-info/METADATA', metadata)
        for name in ('WHEEL', 'top_level.txt', 'RECORD'):
          archive.writestr('bazi-1.0.0.dist-info/' + name, b'')
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
          archive.writestr('bazi-1.0.0.dist-info/licenses/' + name, source[name])
    assert environments is not None
    if not (change == 'role-missing' and role == 'build-sdist'):
      states[role] = {'setuptools': '84.0.0'}
      environments.append(collect(role, role, [{'name': 'pip', 'version': '24.0', 'scope': 'runner'}]))
  monkeypatch.setattr(package_checks, 'build_artifact', build)
  monkeypatch.setattr(venv.EnvBuilder, 'create', lambda self, directory: directory.mkdir())

  def observe(prefix: list[str], scope: Literal['runner', 'target'], installers: list[Installer]) -> None:
    observations.append('pip:' + Path(prefix[0]).parent.parent.name)
    record: Installer = {'name': 'pip', 'version': '23.0', 'scope': scope}
    if record not in installers:
      installers.append(record)
  monkeypatch.setattr(package_checks, 'observe_pip', observe)

  def run_fixture(command: list[str], cwd: Path) -> None:
    if 'mypy' in command:
      assert command[1:5] == ['-I', '-X', 'utf8', '-m']
      assert '--show-traceback' in command and command[-1] == 'good.py'
    if 'pip' not in command:
      return
    python = command[0]
    if 'uninstall' in command:
      states[python].pop('setuptools')
    elif command[-1].endswith('.whl'):
      states[python] = {'bazi': '1.0', 'pip': '23.0', 'setuptools': '84.0.0',
        'wheel-origin': '1.0' if Path(command[-1]).parent.name == 'direct' else '2.0'}
    else:
      assert command[-1] == 'mypy==2.4.0'
      observations.append('install-mypy')
      states[python].update({'mypy': '2.4.0', 'typing-transitive': '1.0'})
  monkeypatch.setattr(package_checks, 'run', run_fixture)

  def diagnostics(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    command, = args
    assert isinstance(command, list) and command[-1] == 'bad.py' and '--show-traceback' in command
    assert command[1:5] == ['-I', '-X', 'utf8', '-m']
    bad = (work / 'consumer/bad.py').read_text(encoding='utf-8').splitlines()
    assert bad.count('KongwangResult(Zhu.YUE, target, ())') == 1
    assert 'KongwangResult(Zhu.月, target, ())' not in bad
    messages = ['[assignment] [arg-type] "None"']
    messages.extend(f'to "{name}"' for name in ('create', 'query', 'find_objects', 'search', 'filter_values',
      'criterion', 'LiunianObservation', 'TransitObservation', 'YearCoordinate', 'MonthCoordinate', 'DateCoordinate',
      'MomentCoordinate', 'LiunianPosition', 'ChartOccurrence', 'KongwangHit', 'KongwangResult', 'StarAppearance',
      'CriterionResult', 'EntryMatch', 'PremiseMatches', 'ConditionReferences',
      'evaluate_context', 'ContextResult', 'GanzhiYearMonth', 'from_dizhi', 'from_jie',
      'object_id', 'render', 'render_subject'))
    for owner, member, trigger in (
      ('Bazi', 'reference_datetime', 'local.reference_datetime = datetime.now()'),
      ('Bazi', 'month_jies', 'local.month_jies = ()'), ('GanzhiYearMonth', 'month', 'coordinate.month = 0'),
      ('KnowledgeSource', 'work', 'witness.work = "changed"'), ('CriterionInfo', 'definition', 'info.definition = "changed"'),
      ('ContextResult', 'bazi', 'matched.bazi = chart.bazi'),
    ):
      messages.append(f'bad.py:{bad.index(trigger) + 1}: error: Property "{member}" defined in "{owner}" is read-only  [misc]')
    for value, trigger in (('CriterionInfo', 'catalog["changed"] = info'), ('KnowledgeSource', 'knowledge.sources["editorial"] = witness')):
      messages.append(f'bad.py:{bad.index(trigger) + 1}: error: Unsupported target for indexed assignment ("frozendict[str, {value}]")  [index]')
    messages.extend(f'"{owner}" has no attribute "{member}"' for owner, member in
      (('BaziChart', 'json'), ('ContextResult', 'input_json'), ('ContextResult', 'export_json'), ('KnowledgeBase', 'export_json')))
    if change == 'typing-missing-kongwang':
      messages.remove('to "KongwangResult"')
    return subprocess.CompletedProcess([], 2 if change == 'typing-internal-error' else 1, '\n'.join(messages), '')
  monkeypatch.setattr(subprocess, 'run', diagnostics)
  if change == 'none':
    check_packages(root, work, output, report, receipt)
  else:
    exception = FileExistsError if change == 'report-race' else ValueError
    message = {'identity-changed': 'Source identity changed', 'source-changed': 'Source changed',
      'role-missing': 'Environment role roster mismatch', 'report-race': '',
      'typing-internal-error': 'Installed typing negative control did not reach both type checks',
      'typing-missing-kongwang': 'Installed typing negative control missed KongwangResult'}[change]
    with pytest.raises(exception, match=message or None):
      check_packages(root, work, output, report, receipt)
    if change == 'report-race':
      assert report.read_text() == 'keep competing file'
    else:
      assert not report.exists()
    return
  data = json.loads(report.read_text())
  assert data['schema_version'] == 1 and data['source_sha'] == 'a' * 40
  records = data['environments']
  assert [record['role'] for record in records] == ['outer', 'build-wheel-direct', 'build-sdist', 'build-wheel-rebuilt',
    'consumer-wheel-direct', 'consumer-wheel-rebuilt', 'consumer-typing']
  assert records[0]['installers'] == [{'name': 'pip', 'version': version, 'scope': 'runner'} for version in ('25.0.1', '25.1rc1')]
  assert records[4]['distributions'] == {'bazi': '1.0', 'pip': '23.0', 'wheel-origin': '1.0'}
  assert records[5]['distributions'] == {'bazi': '1.0', 'pip': '23.0', 'wheel-origin': '2.0'}
  assert records[6]['distributions'] == {**records[5]['distributions'], 'mypy': '2.4.0', 'typing-transitive': '1.0'}
  assert observations.index('install-mypy') < observations.index('consumer-typing')
  assert observations.count('pip:direct-venv') == observations.count('pip:rebuilt-venv') == 2
  assert observations.count('pip:typing-venv') == 3
  assert identity.call_count == 2
  version.assert_called_once_with('mypy')
  assert (work / 'direct/bazi-1.0.0-py3-none-any.whl').read_bytes() != (work / 'rebuilt/bazi-1.0.0-py3-none-any.whl').read_bytes()
  expected_pair = {'sdist': work / 'sdist/bazi-1.0.0.tar.gz', 'wheel': work / 'rebuilt/bazi-1.0.0-py3-none-any.whl'}
  assert data['pair'] == {kind: {'filename': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    for kind, path in expected_pair.items()}
  assert {path.name: path.read_bytes() for path in output.iterdir()} == {path.name: path.read_bytes() for path in expected_pair.values()}
  assert str(tmp_path) not in report.read_text()
  with pytest.raises(ValueError, match='^Environment report must not exist$'):
    check_packages(root, work, None, report, receipt)
