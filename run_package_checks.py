'''Build and test installed artifacts without using checkout imports.'''

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import venv
import zipfile

from pathlib import Path
from typing import Final
from collections import Counter


ROOT: Final[Path] = Path(__file__).resolve().parent
# Independent resource oracle for the declarations in pyproject.toml and MANIFEST.in.
RUNTIME_DATA: Final[tuple[str, ...]] = (
  'bazi/calendar/hko_data/data/jieqi_encoded.bin',
  'bazi/calendar/hko_data/data/lunardate_encoded.bin',
  'bazi/calendar/celestial_data/data/jieqi_moments.txt',
  'bazi/calendar/celestial_data/data/lunar_years_algo1.txt',
  'bazi/calendar/celestial_data/data/lunar_years_algo2.txt',
)
SOURCE_FILES: Final[tuple[str, ...]] = (
  'pyproject.toml', 'MANIFEST.in', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
  'README.md', 'RELEASE_NOTES.md', 'RELEASING.md', 'Requirements.txt', 'ruff.toml',
  'run_tests.py', 'run_package_checks.py', 'run_demo.py', 'run_interpreter.py',
  'run_relationship_analyzer.py', '.github/workflows/release.yml',
  'bazi/py.typed', 'bazi/calendar/celestial_data/SCHEMA.md',
)


def sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(root: Path) -> tuple[str, ...]:
  files = set(SOURCE_FILES) | set(RUNTIME_DATA)
  files.update(path.relative_to(root).as_posix() for path in (root / 'bazi').rglob('*.py'))
  files.update(f'bazi/calendar/hko_data/data/{year}.txt' for year in range(1901, 2101))
  for path in (root / 'tests').rglob('*'):
    if path.suffix in ('.py', '.ini', '.txt', '.json') and '__pycache__' not in path.parts:
      files.add(path.relative_to(root).as_posix())
  for name in files:
    path = root / name
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
      raise ValueError(f'Invalid source input: {name}')
  return tuple(sorted(files))


def check_wheel(wheel: Path, expected: dict[str, str], licenses: dict[str, str]) -> None:
  with zipfile.ZipFile(wheel) as archive:
    names = archive.namelist()
    metadata_dir = wheel.name.split('-')[0] + '-' + wheel.name.split('-')[1] + '.dist-info/'
    metadata_files = {metadata_dir + name for name in ('METADATA', 'WHEEL', 'top_level.txt', 'RECORD')}
    license_files = {metadata_dir + 'licenses/' + name for name in licenses}
    if duplicates := sorted(name for name, count in Counter(names).items() if count > 1):
      raise ValueError(f'Duplicate wheel members: {wheel.name}: {duplicates}')
    if set(names) != set(expected) | metadata_files | license_files:
      raise ValueError(f'Wheel file roster mismatch: {wheel.name}: {set(names) ^ (set(expected) | metadata_files | license_files)}')
    for name, digest in expected.items():
      if hashlib.sha256(archive.read(name)).hexdigest() != digest:
        raise ValueError(f'Wheel bytes differ: {name}')
    for name, digest in licenses.items():
      if hashlib.sha256(archive.read(metadata_dir + 'licenses/' + name)).hexdigest() != digest:
        raise ValueError(f'License bytes differ: {name}')


def run(command: list[str], cwd: Path) -> None:
  print(f'RUN cwd={cwd} argv={command!r}', flush=True)
  env = {key: value for key, value in os.environ.items() if key not in ('PYTHONPATH', 'PYTHONHOME', 'MYPYPATH')}
  subprocess.run(command, cwd=cwd, env=env, check=True)


def consumer(directory: Path, wheel: Path) -> Path:
  venv.EnvBuilder(with_pip=True).create(directory)
  python = directory / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
  run([str(python), '-I', '-m', 'pip', 'install', '--no-index', '--no-deps', '--no-compile', str(wheel)], directory.parent)
  # Python 3.11's ensurepip also seeds setuptools; consumers need only pip and bazi.
  run([str(python), '-I', '-m', 'pip', 'uninstall', '-y', 'setuptools'], directory.parent)
  return python


def check_packages(root: Path, work: Path, output_dir: Path | None) -> None:
  files = source_files(root)
  before = {name: sha256(root / name) for name in files}
  project = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))['project']
  package = {name: digest for name, digest in before.items() if name.startswith('bazi/') and (name.endswith('.py') or name == 'bazi/py.typed' or name in RUNTIME_DATA)}
  licenses = {name: before[name] for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md')}
  stage = work / 'source'
  for name in files:
    target = stage / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / name, target)

  direct_dir, sdist_dir, rebuilt_dir = (work / name for name in ('direct', 'sdist', 'rebuilt'))
  for option, out in (('--wheel', direct_dir), ('--sdist', sdist_dir)):
    run([sys.executable, '-m', 'build', option, '--outdir', str(out), str(stage)], work)
  direct, = direct_dir.glob('*.whl')
  sdist, = sdist_dir.glob('*.tar.gz')
  extracted = work / 'extracted'
  with tarfile.open(sdist) as archive:
    members = [member for member in archive.getmembers() if not member.isdir()]
    prefix = f'bazi-{project["version"]}/'
    payload: dict[str, bytes] = {}
    for member in members:
      if not member.isfile() or not member.name.startswith(prefix) or '..' in Path(member.name).parts:
        raise ValueError(f'Unsafe sdist member: {member.name}')
      name = member.name.removeprefix(prefix)
      if name in payload:
        raise ValueError(f'Duplicate sdist member: {name}')
      stream = archive.extractfile(member)
      if stream is None:
        raise ValueError(f'Unreadable sdist member: {name}')
      payload[name] = stream.read()
    generated = {'PKG-INFO', 'setup.cfg'} | {f'bazi.egg-info/{name}' for name in ('PKG-INFO', 'SOURCES.txt', 'dependency_links.txt', 'top_level.txt')}
    if set(payload) != set(files) | generated:
      raise ValueError(f'Sdist file roster mismatch: {set(payload) ^ (set(files) | generated)}')
    for name, digest in before.items():
      if hashlib.sha256(payload[name]).hexdigest() != digest:
        raise ValueError(f'Sdist bytes differ: {name}')
    # Extract only verified regular members, never archive links or arbitrary paths.
    for name, content in payload.items():
      target = extracted / name
      target.parent.mkdir(parents=True, exist_ok=True)
      target.write_bytes(content)
  run([sys.executable, '-m', 'build', '--wheel', '--outdir', str(rebuilt_dir), str(extracted)], work)
  rebuilt, = rebuilt_dir.glob('*.whl')
  pair = {path: sha256(path) for path in (sdist, rebuilt)}
  run([sys.executable, '-m', 'twine', 'check', '--strict', str(direct), str(sdist), str(rebuilt)], work)

  foreign = work / 'consumer'
  foreign.mkdir()
  shutil.copyfile(root / 'tests/package_smoke.py', foreign / 'package_smoke.py')
  expected = {'package': package, 'licenses': licenses, 'version': project['version']}
  (foreign / 'expected.json').write_text(json.dumps(expected), encoding='utf-8')
  for label, wheel in (('direct', direct), ('rebuilt', rebuilt)):
    check_wheel(wheel, package, licenses)
    python = consumer(work / (label + '-venv'), wheel)
    for optimization in ([], ['-O']):
      run([str(python), '-I', '-B', *optimization, 'package_smoke.py', 'expected.json'], foreign)

  python = consumer(work / 'typing-venv', rebuilt)
  run([str(python), '-I', '-m', 'pip', 'install', 'mypy==' + importlib.metadata.version('mypy')], foreign)
  good = 'from datetime import datetime\nfrom bazi.bazi import Bazi\nfrom bazi.bazi_chart import BaziChart\nchart: BaziChart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), "male"))\n'
  (foreign / 'good.py').write_text(good, encoding='utf-8')
  (foreign / 'bad.py').write_text(good + 'wrong: int = chart\nBazi.create(42, "male")\n', encoding='utf-8')
  command = [str(python), '-I', '-m', 'mypy', '--strict', '--no-incremental', '--follow-imports=silent']
  run([*command, 'good.py'], foreign)
  result = subprocess.run(
    [*command, 'bad.py'],
    cwd=foreign,
    env={**os.environ, 'MYPYPATH': '', 'PYTHONPATH': ''},
    capture_output=True, text=True, encoding='utf-8', check=False,
  )
  print(result.stdout, end='')
  print(result.stderr, end='')
  if result.returncode != 1 or '[assignment]' not in result.stdout or '[arg-type]' not in result.stdout or 'import-untyped' in result.stdout or 'import-not-found' in result.stdout:
    raise ValueError('Installed typing negative control did not reach both type checks')

  for path, digest in pair.items():
    if sha256(path) != digest:
      raise ValueError(f'Tested artifact changed: {path.name}')
    print(f'TESTED {path.name} sha256={digest}', flush=True)
  if before != {name: sha256(root / name) for name in files}:
    raise ValueError('Source changed during artifact verification')
  if output_dir is not None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
      raise ValueError('Output directory must be empty')
    for path, digest in pair.items():
      destination = output_dir / path.name
      shutil.copyfile(path, destination)
      if sha256(destination) != digest:
        raise ValueError(f'Retained artifact changed: {path.name}')


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--output-dir', type=Path, help='Retain only the tested sdist and its tested rebuilt wheel in an empty external directory.')
  args = parser.parse_args()
  output_dir = args.output_dir.resolve() if args.output_dir is not None else None
  if output_dir is not None and output_dir.is_relative_to(ROOT):
    raise ValueError('Artifacts must stay outside the source checkout')
  with tempfile.TemporaryDirectory(prefix='bazi-package-') as temporary:
    work = Path(temporary).resolve()
    if work.is_relative_to(ROOT):
      raise ValueError('TMPDIR must be outside the source checkout')
    check_packages(ROOT, work, output_dir)


if __name__ == '__main__':
  main()
