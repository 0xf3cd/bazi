# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

# Every fixture below is synthetic: labels v99.* and repeated-letter commits are not published bazi versions.

import ast
import hashlib
import io
import json
import subprocess
import sys
import tarfile

from pathlib import Path
from typing import Self
from collections.abc import Callable, Mapping

import pytest

import run_docs_site
from run_docs_site import GENERATED, add_build, add_pending, digest, keep_current, mark_ready, read_manifest, read_tree, write_site


SCRIPT = Path(run_docs_site.__file__).resolve()
SYNTHETIC = b'SYNTHETIC FIXTURE - not a published bazi version\n'
DEV, V1, V2, V3 = 'dev', 'v99.0.0', 'v99.1.0', 'v99.2.0'
COMMITS = {DEV: 'a' * 40, V1: 'b' * 40, V2: 'c' * 40, V3: 'd' * 40}
ROOTS = {name.partition('/')[0] for name in GENERATED}


def build(label: str, commit: str | None = None, body: bytes = b'', **fields: object) -> dict[str, bytes]:
  metadata = {'version': label, 'commit': commit or COMMITS[label], 'dirty': False, 'python': '3.12.0', **fields}
  return {
    'index.html': SYNTHETIC + body, 'api/page.html': SYNTHETIC, '_static/style.css': b'/* synthetic */\n',
    '.buildinfo': b'synthetic\n', 'build.json': json.dumps(metadata).encode('utf-8'),
  }


def make_tar(path: Path, files: Mapping[str, bytes], extra: Callable[[tarfile.TarFile], None] | None = None) -> Path:
  with tarfile.open(path, 'w') as archive:
    for name, content in files.items():
      info = tarfile.TarInfo(name)
      info.size = len(content)
      archive.addfile(info, io.BytesIO(content))
    if extra is not None:
      extra(archive)
  return path


def publish(archive: Mapping[str, bytes] | None, candidate: Mapping[str, bytes], label: str, commit: str | None = None) -> tuple[str, dict[str, bytes]]:
  return add_build(archive, candidate, label, commit or COMMITS[label])


def ready(archive: Mapping[str, bytes], label: str) -> dict[str, bytes]:
  status, site = mark_ready(archive, label, state(archive, label).digest or '')
  assert status == 'promoted'
  return site


def state(site: Mapping[str, bytes], label: str) -> run_docs_site.Version:
  return next(entry for entry in read_manifest(site['versions.json']) if entry.label == label)


def latest(site: Mapping[str, bytes]) -> object:
  return json.loads(site['versions.json'])['latest']


def selector(site: Mapping[str, bytes]) -> str:
  return site['versions/index.html'].decode('utf-8')


def version_files(site: Mapping[str, bytes], *labels: str) -> dict[str, bytes]:
  return {name: content for name, content in site.items() if name.partition('/')[0] in labels}


@pytest.fixture
def archive() -> dict[str, bytes]:
  '''A synthetic archive holding dev and two releases, all archived but not yet read back.'''
  _, site = publish(None, build(DEV), DEV)
  _, site = publish(site, build(V1), V1)
  _, site = publish(site, build(V2), V2)
  return site


def test_dev_and_two_releases_are_retained(archive: dict[str, bytes]) -> None:
  entries = read_manifest(archive['versions.json'])
  assert [entry.label for entry in entries] == [DEV, V2, V1]
  assert [entry.commit for entry in entries] == [COMMITS[DEV], COMMITS[V2], COMMITS[V1]]
  assert {entry.state for entry in entries} == {'archived'}
  assert {name.partition('/')[0] for name in archive} == {DEV, V1, V2} | ROOTS
  for label in (DEV, V1, V2):
    assert {name for name in archive if name.startswith(label + '/')} == {f'{label}/{name}' for name in build(label)}
  assert archive['index.html'] == run_docs_site.ROOT_PAGE and b'url=versions/' in archive['index.html']


def test_archived_versions_listed_not_linked(archive: dict[str, bytes]) -> None:
  # The first archive commit must not compute latest or advertise unverified directories.
  page = selector(archive)
  assert latest(archive) is None
  assert f'<li id="{DEV}">开发版：文档待就绪</li>' in page
  for label in (V1, V2):
    assert f'<li id="{label}">{label}：文档待就绪</li>' in page
  assert '/index.html">' not in page and '最新发布' not in page
  assert '不表示该版软件没有发布' in page


def test_state_chain_pending_to_ready_latest() -> None:
  status, site = add_pending(None, V1)
  assert status == 'added' and state(site, V1) == (V1, 'pending', None, None)
  assert not any(name.startswith(V1 + '/') for name in site)
  assert f'<li id="{V1}">{V1}：文档待就绪</li>' in selector(site) and latest(site) is None

  status, site = publish(site, build(V1), V1)
  assert status == 'added' and state(site, V1).state == 'archived' and latest(site) is None
  assert f'<li id="{V1}">{V1}：文档待就绪</li>' in selector(site)
  first = version_files(site, V1)

  site = ready(site, V1)
  assert state(site, V1).state == 'ready' and latest(site) == V1
  assert f'<li id="{V1}"><a href="../{V1}/index.html">{V1}</a>（最新发布）' in selector(site)

  _, site = publish(site, build(V2), V2)
  assert state(site, V2).state == 'archived' and latest(site) == V1
  site = ready(site, V2)
  assert latest(site) == V2 and f'<a href="../{V1}/index.html">{V1}</a> · ' in selector(site)

  _, site = publish(site, build(DEV), DEV)
  site = ready(site, DEV)
  assert latest(site) == V2 and f'<a href="../{DEV}/index.html">开发版</a>（跟随 main 手动更新）' in selector(site)
  assert version_files(site, V1) == first
  assert [entry.label for entry in read_manifest(site['versions.json'])] == [DEV, V2, V1]


def test_latest_is_the_highest_ready_release() -> None:
  # v99.10.0 sorts numerically above v99.9.0, and an archived higher release does not count.
  labels = {'v99.9.0': '9' * 40, 'v99.10.0': 'e' * 40, 'v99.11.0': 'f' * 40}
  site = None
  for label, commit in labels.items():
    _, site = add_build(site, build(label, commit=commit), label, commit)
  assert site is not None
  site = ready(site, 'v99.9.0')
  assert latest(site) == 'v99.9.0'
  site = ready(site, 'v99.10.0')
  assert latest(site) == 'v99.10.0' and state(site, 'v99.11.0').state == 'archived'


def test_promotion_requires_the_read_back_digest(archive: dict[str, bytes]) -> None:
  with pytest.raises(ValueError, match='differs from its archived digest'):
    mark_ready(archive, V1, 'f' * 64)
  with pytest.raises(ValueError, match='differs from its archived digest'):
    mark_ready(archive, V1, '')
  with pytest.raises(ValueError, match='no archived directory'):
    mark_ready(archive, V3, 'f' * 64)
  _, pending = add_pending(archive, V3)
  with pytest.raises(ValueError, match='no archived directory'):
    mark_ready(pending, V3, digest({}))
  with pytest.raises(ValueError, match='no archived directory'):
    mark_ready(None, V1, 'f' * 64)
  site = ready(archive, V1)
  assert mark_ready(site, V1, state(site, V1).digest or '') == ('unchanged', site)


def test_pending_is_only_for_unarchived_releases(archive: dict[str, bytes]) -> None:
  with pytest.raises(ValueError, match='Expected vMAJOR.MINOR.PATCH'):
    add_pending(archive, DEV)
  with pytest.raises(ValueError, match='already archived'):
    add_pending(archive, V1)
  with pytest.raises(ValueError, match='already archived'):
    add_pending(ready(archive, V1), V1)
  _, site = add_pending(archive, V3)
  assert add_pending(site, V3) == ('unchanged', site)
  assert version_files(site, DEV, V1, V2) == version_files(archive, DEV, V1, V2)


def test_same_content_idempotent_keeps_state(archive: dict[str, bytes]) -> None:
  assert publish(archive, build(V1), V1) == ('unchanged', archive)
  assert publish(archive, build(DEV), DEV) == ('unchanged', archive)
  site = ready(archive, V1)
  assert publish(site, build(V1), V1) == ('unchanged', site)
  assert keep_current(site, V1) == ('unchanged', site)
  with pytest.raises(ValueError, match='is not in the archive'):
    keep_current(site, V3)


def test_published_release_is_never_replaced(archive: dict[str, bytes]) -> None:
  for site in (archive, ready(archive, V1)):
    with pytest.raises(ValueError, match='already archived with different content'):
      publish(site, build(V1, body=b'changed'), V1)
    with pytest.raises(ValueError, match='does not describe a clean build'):
      publish(site, build(V1, commit='d' * 40), V1)


def test_dev_replacement_returns_to_archived(archive: dict[str, bytes]) -> None:
  site = ready(ready(archive, DEV), V1)
  status, site = publish(site, build(DEV, commit='d' * 40, body=b'next'), DEV, 'd' * 40)
  assert status == 'replaced'
  assert site[f'{DEV}/index.html'] == SYNTHETIC + b'next'
  assert state(site, DEV) == (DEV, 'archived', 'd' * 40, digest(build(DEV, commit='d' * 40, body=b'next')))
  assert f'<li id="{DEV}">开发版：文档待就绪</li>' in selector(site) and latest(site) == V1
  assert version_files(site, V1, V2) == version_files(archive, V1, V2)


@pytest.mark.parametrize('change, message', [
  ('missing', 'build.json or index.html is missing'),
  ('no-index', 'build.json or index.html is missing'),
  ('extra-field', 'fields differ'),
  ('missing-field', 'fields differ'),
  ('version', 'does not describe a clean build'),
  ('commit', 'does not describe a clean build'),
  ('dirty', 'does not describe a clean build'),
  ('dirty-zero', 'does not describe a clean build'),
  ('python', 'does not describe a clean build'),
  ('duplicate-key', 'Duplicate JSON key'),
  ('not-json', 'Expecting value'),
  ('not-utf8', 'codec'),
  ('array', 'fields differ'),
])
def test_wrong_build_metadata_is_rejected(archive: dict[str, bytes], change: str, message: str) -> None:
  label = V3
  candidate = build(label)
  metadata = json.loads(candidate['build.json'])
  if change == 'missing':
    del candidate['build.json']
  elif change == 'no-index':
    del candidate['index.html']
  elif change == 'extra-field':
    metadata['sha'] = 'd' * 40
  elif change == 'missing-field':
    del metadata['python']
  elif change == 'version':
    metadata['version'] = V1
  elif change == 'commit':
    metadata['commit'] = 'e' * 40
  elif change in ('dirty', 'dirty-zero'):
    metadata['dirty'] = True if change == 'dirty' else 0
  elif change == 'python':
    metadata['python'] = 3.12
  if change not in ('missing', 'no-index'):
    candidate['build.json'] = json.dumps(metadata).encode('utf-8')
  if change == 'duplicate-key':
    candidate['build.json'] = candidate['build.json'][:-1] + f', "commit": "{"e" * 40}"}}'.encode()
  elif change == 'not-json':
    candidate['build.json'] = b''
  elif change == 'not-utf8':
    candidate['build.json'] = b'\xff'
  elif change == 'array':
    candidate['build.json'] = b'[]'
  with pytest.raises(ValueError, match=message):
    publish(archive, candidate, label)


@pytest.mark.parametrize('label', [
  'latest', 'versions', 'v1.0', 'v1.0.0.0', 'V1.0.0', 'v01.0.0', 'v1.0.0\n', '../v1.0.0', 'v1.0.0/', 'v١.0.0', 'v1١.0.0', '',
])
def test_invalid_labels_are_rejected(label: str) -> None:
  with pytest.raises(ValueError, match='Expected dev or vMAJOR'):
    add_build(None, build(DEV), label, COMMITS[DEV])
  with pytest.raises(ValueError, match='Expected vMAJOR'):
    add_pending(None, label)


@pytest.mark.parametrize('commit', ['a' * 39, 'A' * 40, 'g' * 40, 'a' * 40 + '\n', 'a' * 41])
def test_invalid_commits_are_rejected(commit: str) -> None:
  with pytest.raises(ValueError, match='40-hex commit'):
    add_build(None, build(DEV), DEV, commit)


def rewrite(archive: dict[str, bytes], manifest: dict[str, object]) -> None:
  # Same formatting as the generator, so only the edited meaning can make the archive non-canonical.
  archive['versions.json'] = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')


@pytest.mark.parametrize('change, message', [
  ('old-bytes', 'differs from its recorded digest'),
  ('old-extra-file', 'differs from its recorded digest'),
  ('old-commit', 'does not describe a clean build'),
  ('unlisted-directory', 'differ from the archived versions'),
  ('missing-directory', 'differ from the archived versions'),
  ('pending-with-directory', 'differ from the archived versions'),
  ('selector-extra-file', 'differ from the archived versions'),
  ('unknown-root-file', 'Unexpected archive root file'),
  ('no-manifest', 'no versions.json'),
  ('schema', 'Unsupported versions.json'),
  ('schema-bool', 'Unsupported versions.json'),
  ('no-latest', 'Unsupported versions.json'),
  ('extra-manifest-key', 'Unsupported versions.json'),
  ('entry-field', 'Invalid versions.json entry'),
  ('entry-type', 'Invalid commit or digest'),
  ('unknown-state', 'Invalid versions.json entry'),
  ('label-type', 'Invalid versions.json entry'),
  ('bad-digest', 'Invalid commit or digest'),
  ('ready-without-digest', 'Invalid commit or digest'),
  ('pending-with-commit', 'must not record a commit'),
  ('pending-dev', 'Expected vMAJOR'),
  ('bad-label', 'Expected dev or vMAJOR'),
  ('duplicate-label', 'Duplicate label'),
  ('hand-set-latest', 'Generated root files differ'),
  ('hand-set-ready', 'Generated root files differ'),
  ('reordered', 'Generated root files differ'),
  ('selector-edited', 'Generated root files differ'),
  ('root-page-missing', 'Generated root files differ'),
])
def test_wrong_archive_metadata_is_rejected(archive: dict[str, bytes], change: str, message: str) -> None:
  manifest = json.loads(archive['versions.json'])
  versions = manifest['versions']
  if change == 'old-bytes':
    archive[f'{V1}/api/page.html'] = b'edited by hand'
  elif change == 'old-extra-file':
    archive[f'{V1}/extra.html'] = b''
  elif change == 'old-commit':
    versions[2]['commit'] = 'e' * 40
  elif change == 'unlisted-directory':
    archive['v99.9.0/index.html'] = b''
  elif change == 'missing-directory':
    for name in [name for name in archive if name.startswith(V1 + '/')]:
      del archive[name]
  elif change == 'pending-with-directory':
    versions[2] |= {'state': 'pending', 'commit': None, 'digest': None}
  elif change == 'selector-extra-file':
    archive['versions/extra.html'] = b''
  elif change == 'unknown-root-file':
    archive['CNAME'] = b'example.com'
  elif change == 'no-manifest':
    del archive['versions.json']
  elif change == 'schema':
    manifest['schema'] = 2
  elif change == 'schema-bool':
    manifest['schema'] = True
  elif change == 'no-latest':
    del manifest['latest']
  elif change == 'extra-manifest-key':
    manifest['updated'] = '2026-10-17'
  elif change == 'entry-field':
    versions[1]['python'] = '3.12'
  elif change == 'entry-type':
    versions[1]['commit'] = None
  elif change == 'unknown-state':
    versions[1]['state'] = 'live'
  elif change == 'label-type':
    versions[1]['label'] = 99
  elif change == 'bad-digest':
    versions[1]['digest'] = 'f' * 63
  elif change == 'ready-without-digest':
    versions[1] |= {'state': 'ready', 'digest': None}
  elif change == 'pending-with-commit':
    versions[2]['state'] = 'pending'
  elif change == 'pending-dev':
    versions[0] |= {'state': 'pending', 'commit': None, 'digest': None}
  elif change == 'bad-label':
    versions[1]['label'] = 'latest'
  elif change == 'duplicate-label':
    versions.append(versions[1])
  elif change == 'hand-set-latest':
    manifest['latest'] = V2
  elif change == 'hand-set-ready':
    versions[1]['state'] = 'ready'
  elif change == 'reordered':
    versions.reverse()
  elif change == 'selector-edited':
    archive['versions/index.html'] = archive['versions/index.html'].replace(f'{V2}：文档待就绪'.encode(), f'<a href="../{V2}/index.html">{V2}</a>'.encode())
  elif change == 'root-page-missing':
    del archive['index.html']
  if 'versions.json' in archive and change not in ('old-bytes', 'old-extra-file', 'unlisted-directory', 'missing-directory', 'selector-extra-file', 'unknown-root-file', 'selector-edited', 'root-page-missing'):
    rewrite(archive, manifest)
  with pytest.raises(ValueError, match=message):
    publish(archive, build(DEV), DEV)
  with pytest.raises(ValueError, match=message):
    keep_current(archive, DEV)


def add_link(name: str, kind: bytes, target: str) -> Callable[[tarfile.TarFile], None]:
  def extra(archive: tarfile.TarFile) -> None:
    info = tarfile.TarInfo(name)
    info.type = kind
    info.linkname = target
    archive.addfile(info)
  return extra


def add_special(name: str, kind: bytes) -> Callable[[tarfile.TarFile], None]:
  def extra(archive: tarfile.TarFile) -> None:
    info = tarfile.TarInfo(name)
    info.type = kind
    archive.addfile(info)
  return extra


@pytest.mark.parametrize('names, extra, message', [
  (['../escape.html'], None, 'Unsafe archive path'),
  (['/etc/escape.html'], None, 'Unsafe archive path'),
  (['api/../../escape.html'], None, 'Unsafe archive path'),
  (['.git/config'], None, 'Unsafe archive path'),
  (['api/.GIT/hooks/post-checkout'], None, 'Unsafe archive path'),
  (['.gitattributes'], None, 'Unsafe archive path'),
  (['api/.gitmodules'], None, 'Unsafe archive path'),
  (['.github/workflows/x.yml'], None, 'Unsafe archive path'),
  (['api\\escape.html'], None, 'Unsafe archive path'),
  (['api/\x1b.html'], None, 'Unsafe archive path'),
  ([], add_link('api/link.html', tarfile.SYMTYPE, '/etc/passwd'), 'Only regular files'),
  ([], add_link('_static', tarfile.SYMTYPE, '../../outside'), 'Only regular files'),
  ([], add_link('api/hard.html', tarfile.LNKTYPE, 'index.html'), 'Only regular files'),
  ([], add_special('api/fifo', tarfile.FIFOTYPE), 'Only regular files'),
  ([], add_special('api/device', tarfile.CHRTYPE), 'Only regular files'),
  (['./index.html'], None, 'Duplicate or empty'),
  (['index.html/inner.html'], None, 'both a file and a directory'),
])
def test_unsafe_candidate_archives_are_rejected(tmp_path: Path, names: list[str], extra: Callable[[tarfile.TarFile], None] | None, message: str) -> None:
  files = {**build(DEV), **dict.fromkeys(names, b'attack')}
  path = make_tar(tmp_path / 'candidate.tar', files, extra)
  with pytest.raises(ValueError, match=message):
    read_tree(path)
  assert not (tmp_path / 'escape.html').exists() and not (tmp_path.parent / 'escape.html').exists()


def test_unsafe_existing_archive_is_rejected(tmp_path: Path, archive: dict[str, bytes]) -> None:
  path = make_tar(tmp_path / 'archive.tar', archive, add_link(f'{V1}/api/page.html', tarfile.SYMTYPE, '/etc/passwd'))
  with pytest.raises(ValueError, match='Only regular files'):
    read_tree(path)


def test_compressed_archives_are_rejected(tmp_path: Path) -> None:
  path = tmp_path / 'candidate.tar.gz'
  with tarfile.open(path, 'w:gz') as archive:
    archive.addfile(tarfile.TarInfo('index.html'), io.BytesIO(b''))
  with pytest.raises(tarfile.ReadError):
    read_tree(path)


def test_tar_round_trip_keeps_dotfiles_and_bytes(tmp_path: Path, archive: dict[str, bytes]) -> None:
  # The Pages upload must keep these hidden files; the workflow sets include-hidden-files for them.
  assert read_tree(make_tar(tmp_path / 'archive.tar', archive)) == archive
  assert {name for name in archive if any(part.startswith('.') for part in name.split('/'))} == {f'{label}/.buildinfo' for label in (DEV, V1, V2)}


def test_write_site_is_all_or_nothing(tmp_path: Path, archive: dict[str, bytes], monkeypatch: pytest.MonkeyPatch) -> None:
  output = tmp_path / 'site'
  write_site(archive, output)
  assert run_docs_site.read_directory(output) == archive
  with pytest.raises(ValueError, match='must not exist'):
    write_site(archive, output)

  second = tmp_path / 'second'
  written: list[Path] = []
  original = Path.open
  def failing_open(path: Path, mode: str = 'r', *args: object, **kwargs: object) -> object:
    if mode == 'xb':
      written.append(path)
      if len(written) == 3:
        raise OSError('synthetic disk failure')
    return original(path, mode, *args, **kwargs)  # type: ignore[call-overload] # Forward the original signature.
  monkeypatch.setattr(Path, 'open', failing_open)
  with pytest.raises(OSError, match='synthetic disk failure'):
    write_site(archive, second)
  monkeypatch.undo()
  assert len(written) == 3
  assert not second.exists()
  assert sorted(p.name for p in tmp_path.iterdir()) == ['site']


class Truncating:
  def __init__(self, stream: io.BufferedWriter) -> None:
    self.stream = stream

  def __enter__(self) -> Self:
    return self

  def __exit__(self, *exc: object) -> None:
    self.stream.close()

  def write(self, data: bytes) -> int:
    return self.stream.write(data[:-1])


def test_write_site_rejects_lossy_bytes(tmp_path: Path, archive: dict[str, bytes], monkeypatch: pytest.MonkeyPatch) -> None:
  original = Path.open
  def truncating_open(path: Path, mode: str = 'r', *args: object, **kwargs: object) -> object:
    stream = original(path, mode, *args, **kwargs)  # type: ignore[call-overload] # Forward the original signature.
    return Truncating(stream) if mode == 'xb' and path.name == 'versions.json' else stream
  monkeypatch.setattr(Path, 'open', truncating_open)
  with pytest.raises(ValueError, match='Written site differs'):
    write_site(archive, tmp_path / 'site')
  monkeypatch.undo()
  assert list(tmp_path.iterdir()) == []


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, check=False)


@pytest.mark.parametrize('args', [
  ['archive', '--archive', 'archive.tar', '--label', V1, '--output', 'site', '--candidate', 'changed.tar', '--commit', COMMITS[V1]],
  ['archive', '--archive', 'archive.tar', '--label', V2, '--output', 'site', '--candidate', 'v1.tar', '--commit', COMMITS[V2]],
  ['promote', '--archive', 'archive.tar', '--label', V1, '--output', 'site', '--verified-digest', 'f' * 64],
  ['promote', '--archive', 'archive.tar', '--label', V3, '--output', 'site', '--verified-digest', 'f' * 64],
  ['pending', '--archive', 'archive.tar', '--label', V1, '--output', 'site'],
  ['current', '--archive', 'archive.tar', '--label', V3, '--output', 'site'],
])
def test_failed_operation_keeps_old_archive(tmp_path: Path, archive: dict[str, bytes], args: list[str]) -> None:
  archive_tar = make_tar(tmp_path / 'archive.tar', archive)
  make_tar(tmp_path / 'changed.tar', build(V1, body=b'changed'))
  make_tar(tmp_path / 'v1.tar', build(V1))
  before = hashlib.sha256(archive_tar.read_bytes()).hexdigest()
  result = run_cli(tmp_path, *args)
  assert result.returncode == 1 and 'ValueError' in result.stderr
  assert not (tmp_path / 'site').exists()
  assert hashlib.sha256(archive_tar.read_bytes()).hexdigest() == before
  assert read_tree(archive_tar) == archive


def test_cli_transitions_into_new_directory(tmp_path: Path, archive: dict[str, bytes]) -> None:
  make_tar(tmp_path / 'archive.tar', archive)
  make_tar(tmp_path / 'candidate.tar', build(V3))
  result = run_cli(tmp_path, 'archive', '--archive', 'archive.tar', '--label', V3, '--output', 'one', '--candidate', 'candidate.tar', '--commit', COMMITS[V3])
  assert result.returncode == 0, result.stderr
  report = json.loads(result.stdout)
  assert report == {'status': 'added', 'label': V3, 'state': 'archived', 'commit': COMMITS[V3], 'digest': digest(build(V3)),
    'latest': None, 'versions': [DEV, V3, V2, V1]}
  one = run_docs_site.read_directory(tmp_path / 'one')
  assert version_files(one, DEV, V1, V2) == version_files(archive, DEV, V1, V2)

  make_tar(tmp_path / 'one.tar', one)
  result = run_cli(tmp_path, 'promote', '--archive', 'one.tar', '--label', V3, '--output', 'two', '--verified-digest', report['digest'])
  assert result.returncode == 0, result.stderr
  assert json.loads(result.stdout) | {'versions': None} == report | {'status': 'promoted', 'state': 'ready', 'latest': V3, 'versions': None}

  result = run_cli(tmp_path, 'pending', '--initialize', '--label', V1, '--output', 'three')
  assert result.returncode == 0, result.stderr
  assert json.loads(result.stdout) == {'status': 'added', 'label': V1, 'state': 'pending', 'commit': None, 'digest': None, 'latest': None, 'versions': [V1]}
  assert set(run_docs_site.read_directory(tmp_path / 'three')) == set(GENERATED)

  result = run_cli(tmp_path, 'current', '--archive', 'archive.tar', '--label', V1, '--output', 'four')
  assert result.returncode == 0, result.stderr
  assert run_docs_site.read_directory(tmp_path / 'four') == archive


@pytest.mark.parametrize('args', [
  [],
  ['archive', '--initialize', '--archive', 'archive.tar', '--label', DEV, '--output', 'site', '--candidate', 'candidate.tar', '--commit', COMMITS[DEV]],
  ['archive', '--label', DEV, '--output', 'site', '--candidate', 'candidate.tar', '--commit', COMMITS[DEV]],
  ['archive', '--initialize', '--label', DEV, '--output', 'site', '--commit', COMMITS[DEV]],
  ['promote', '--archive', 'archive.tar', '--label', DEV, '--output', 'site'],
  ['latest', '--archive', 'archive.tar', '--label', DEV, '--output', 'site'],
])
def test_cli_rejects_incomplete_operations(tmp_path: Path, args: list[str]) -> None:
  make_tar(tmp_path / 'archive.tar', {})
  make_tar(tmp_path / 'candidate.tar', build(DEV))
  result = run_cli(tmp_path, *args)
  assert result.returncode == 2
  assert not (tmp_path / 'site').exists()


def test_assembly_ignores_archive_member_order(archive: dict[str, bytes]) -> None:
  forward = publish(archive, build(V3), V3)
  backward = publish(dict(reversed(archive.items())), build(V3), V3)
  assert forward == backward


def test_assembler_imports_only_stdlib() -> None:
  # The privileged archive job runs this file with `python -I`; it must not need third-party or repository modules.
  tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))
  modules = {alias.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
  modules |= {node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
  assert modules <= sys.stdlib_module_names, sorted(modules - sys.stdlib_module_names)
