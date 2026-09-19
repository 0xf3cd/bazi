# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import hashlib
import io
import json
import re
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

import pytest
import yaml


WORKFLOW = yaml.safe_load((Path(__file__).parents[1] / '.github/workflows/release.yml').read_text(encoding='utf-8'))
SHA = 'a' * 40


def run_policy(code: str) -> None:
  exec(compile(code, '<release-policy>', 'exec'), {})  # noqa: S102 # Execute the actual checked-in policy with fixture-backed I/O.


def test_workflow_structure() -> None:
  # PyYAML's YAML 1.1 parser reads the YAML 1.2 key `on` as True.
  trigger = WORKFLOW[True]
  assert set(trigger) == {'workflow_dispatch'}
  assert set(trigger['workflow_dispatch']['inputs']) == {'mode'}
  assert trigger['workflow_dispatch']['inputs']['mode']['default'] == 'rehearsal'
  assert WORKFLOW['permissions'] == {}
  assert WORKFLOW['concurrency']['cancel-in-progress'] is False
  jobs = WORKFLOW['jobs']
  assert set(jobs) == {'preflight', 'build', 'pypi', 'github-release'}
  assert jobs['preflight']['permissions'] == {}
  assert jobs['build']['permissions'] == {'contents': 'read'}
  assert all('environment' not in jobs[name] for name in ('preflight', 'build'))
  assert jobs['preflight']['if'] == "inputs.mode == 'release'"
  assert "inputs.mode == 'rehearsal'" in jobs['build']['if']
  assert "needs.preflight.result == 'success'" in jobs['build']['if']
  assert jobs['pypi']['permissions'] == {'id-token': 'write'}
  assert jobs['github-release']['permissions'] == {'contents': 'write'}
  assert 'pypi' in jobs['github-release']['needs']
  assert "needs.pypi.result == 'success'" in jobs['github-release']['if']
  pins = {
    'actions/checkout': '3d3c42e5aac5ba805825da76410c181273ba90b1',
    'actions/setup-python': '5fda3b95a4ea91299a34e894583c3862153e4b97',
    'actions/upload-artifact': '043fb46d1a93c77aae656e7c1c64a875d1fc6a0a',
    'actions/download-artifact': '3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c',
    'pypa/gh-action-pypi-publish': 'dc37677b2e1c63e2034f94d8a5b11f265b73ba33',
  }
  for name, job in jobs.items():
    for step in job['steps']:
      if 'uses' in step:
        action, sha = step['uses'].split('@')
        assert pins[action] == sha
      if 'run' in step and step.get('shell') == 'python':
        compile(step['run'], '<release-policy>', 'exec')
    if name in ('pypi', 'github-release'):
      assert job['environment'] == 'release'
      for condition in ("inputs.mode == 'release'", "needs.preflight.result == 'success'", "github.repository == '0xf3cd/bazi'", "github.ref == 'refs/heads/main'"):
        assert condition in job['if']
      for step in job['steps']:
        action = step.get('uses', '').split('@')[0]
        assert action in ('', 'actions/download-artifact', 'pypa/gh-action-pypi-publish')
        assert not re.search(r'\b(import bazi|pip install|checkout|run_\w+\.py|subprocess|exec\(|eval\()', step.get('run', ''))
        if action == 'actions/download-artifact':
          assert step['with'] == {
            'artifact-ids': '${{ needs.build.outputs.artifact-id }}', 'path': 'artifact',
            'merge-multiple': True, 'digest-mismatch': 'error',
          }
        if action == 'pypa/gh-action-pypi-publish':
          assert step['with'] == {'packages-dir': 'artifact/dist/', 'skip-existing': False}
  checkout = jobs['build']['steps'][0]
  assert checkout['with']['ref'] == '${{ github.sha }}'
  assert checkout['with']['persist-credentials'] is False
  assert jobs['build']['outputs']['artifact-id'] == '${{ steps.upload.outputs.artifact-id }}'
  assert '--package-output-dir' in jobs['build']['steps'][4]['run']


@pytest.fixture
def release_env(monkeypatch: pytest.MonkeyPatch) -> None:
  for key, value in {'MODE': 'release', 'REPOSITORY': '0xf3cd/bazi', 'REF': 'refs/heads/main',
    'SHA': SHA, 'RUN_ID': '123', 'ARTIFACT_ID': '456', 'VERSION': '1.0.0'}.items():
    monkeypatch.setenv(key, value)


@pytest.mark.parametrize('change', ['none', 'missing', 'no-reviewer', 'empty-reviewer', 'wildcard', 'tag-policy', 'extra-branch', 'protected-only', 'ref', 'repo', 'sha', 'mode'])
def test_environment_preflight(monkeypatch: pytest.MonkeyPatch, release_env: None, change: str) -> None:
  environment = {'name': 'release', 'protection_rules': [{'type': 'required_reviewers',
    'prevent_self_review': False, 'reviewers': [{'type': 'User', 'reviewer': {'id': 123}}]}],
    'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True}}
  policies = {'total_count': 1, 'branch_policies': [{'name': 'main', 'type': 'branch'}]}
  if change == 'no-reviewer':
    environment['protection_rules'] = []
  elif change == 'empty-reviewer':
    environment['protection_rules'] = [{'type': 'required_reviewers', 'reviewers': []}]
  elif change == 'wildcard':
    policies['branch_policies'] = [{'name': '*', 'type': 'branch'}]
  elif change == 'tag-policy':
    policies['branch_policies'] = [{'name': 'main', 'type': 'tag'}]
  elif change == 'extra-branch':
    policies['total_count'] = 2
  elif change == 'protected-only':
    environment['deployment_branch_policy'] = {'protected_branches': True, 'custom_branch_policies': False}
  elif change in ('ref', 'repo', 'sha', 'mode'):
    monkeypatch.setenv({'ref': 'REF', 'repo': 'REPOSITORY', 'sha': 'SHA', 'mode': 'MODE'}[change], 'invalid')
  calls: list[str] = []
  def get(request: urllib.request.Request, timeout: int) -> io.BytesIO:
    assert request.get_method() == 'GET'
    assert timeout == 30
    calls.append(request.full_url)
    if change == 'missing':
      raise urllib.error.HTTPError(request.full_url, 404, 'Not Found', {}, None)  # type: ignore[arg-type] # Fixture has no response headers.
    value = policies if 'deployment-branch-policies?' in request.full_url else environment
    return io.BytesIO(json.dumps(value).encode())
  monkeypatch.setattr(urllib.request, 'urlopen', get)
  code = WORKFLOW['jobs']['preflight']['steps'][0]['run']
  if change == 'none':
    run_policy(code)
    assert len(calls) == 2
  else:
    with pytest.raises((SystemExit, urllib.error.HTTPError)):
      run_policy(code)


@pytest.mark.parametrize('change', ['none', 'checksum', 'manifest', 'id', 'sha', 'run', 'mode', 'extra', 'version'])
def test_bundle_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, release_env: None, change: str) -> None:
  monkeypatch.chdir(tmp_path)
  root = tmp_path / 'artifact'
  (root / 'dist').mkdir(parents=True)
  (root / 'dist/bazi-1.0.0.tar.gz').write_bytes(b'tested sdist')
  (root / 'dist/bazi-1.0.0-py3-none-any.whl').write_bytes(b'tested wheel')
  (root / 'RELEASE_NOTES.md').write_bytes(b'notes')
  metadata = {'name': 'bazi', 'version': '1.0.0', 'sha': SHA, 'repository': '0xf3cd/bazi', 'run_id': '123', 'mode': 'release'}
  if change == 'run':
    metadata['run_id'] = '999'
  (root / 'release.json').write_text(json.dumps(metadata), encoding='utf-8')
  files = sorted(p for p in root.rglob('*') if p.is_file())
  checksums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}\n' for p in files)
  (root / 'SHA256SUMS').write_text(checksums, encoding='utf-8')
  monkeypatch.setenv('MANIFEST_SHA', hashlib.sha256(checksums.encode()).hexdigest())
  if change == 'checksum':
    (root / 'dist/bazi-1.0.0.tar.gz').write_bytes(b'untested sdist')
  elif change == 'manifest':
    monkeypatch.setenv('MANIFEST_SHA', '0' * 64)
  elif change == 'id':
    monkeypatch.setenv('ARTIFACT_ID', 'arbitrary,123')
  elif change == 'sha':
    monkeypatch.setenv('SHA', 'b' * 40)
  elif change == 'mode':
    monkeypatch.setenv('MODE', 'rehearsal')
  elif change == 'extra':
    (root / 'unexpected.py').write_bytes(b'')
  elif change == 'version':
    monkeypatch.setenv('VERSION', '2.0.0')
  code = WORKFLOW['jobs']['pypi']['steps'][1]['run']
  assert code == WORKFLOW['jobs']['github-release']['steps'][1]['run']
  if change == 'none':
    run_policy(code)
  else:
    with pytest.raises(SystemExit):
      run_policy(code)


@pytest.mark.parametrize('existing', [None, 'pypi', 'git/ref', 'releases/tags', 'network-error'])
def test_existing_release_policy(monkeypatch: pytest.MonkeyPatch, release_env: None, existing: str | None) -> None:
  calls: list[str] = []
  def get(url: str, timeout: int) -> io.BytesIO:
    calls.append(url)
    if existing is not None and existing in url:
      return io.BytesIO(b'{}')
    raise urllib.error.HTTPError(url, 503 if existing == 'network-error' else 404, 'Fixture', {}, None)  # type: ignore[arg-type] # No headers needed.
  monkeypatch.setattr(urllib.request, 'urlopen', get)
  code = WORKFLOW['jobs']['pypi']['steps'][2]['run']
  if existing is None:
    run_policy(code)
    assert len(calls) == 3
  else:
    with pytest.raises((SystemExit, urllib.error.HTTPError)):
      run_policy(code)


@pytest.mark.parametrize('change', ['none', 'pypi-bytes', 'tag', 'release', 'tag-race', 'asset-bytes'])
def test_publication_api_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, release_env: None, change: str) -> None:
  monkeypatch.chdir(tmp_path)
  monkeypatch.setenv('GH_TOKEN', 'offline-fixture')
  root = tmp_path / 'artifact'
  (root / 'dist').mkdir(parents=True)
  (root / 'dist/bazi-1.0.0.tar.gz').write_bytes(b'tested sdist')
  (root / 'dist/bazi-1.0.0-py3-none-any.whl').write_bytes(b'tested wheel')
  (root / 'RELEASE_NOTES.md').write_text('Release notes', encoding='utf-8')
  writes: list[tuple[str, object]] = []
  def request(url: str | urllib.request.Request, timeout: int) -> io.BytesIO:
    address = url if isinstance(url, str) else url.full_url
    method = 'GET' if isinstance(url, str) else url.get_method()
    value: dict[str, Any] = {}
    if 'pypi.org' in address:
      value = {'urls': [{'filename': p.name, 'digests': {'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}}
        for p in (root / 'dist').iterdir()]}
      if change == 'pypi-bytes':
        value['urls'][0]['digests']['sha256'] = '0' * 64
    elif method == 'GET':
      if not ((change == 'tag' and '/git/ref/tags/' in address) or (change == 'release' and '/releases/tags/' in address)):
        raise urllib.error.HTTPError(address, 404, 'Fixture', {}, None)  # type: ignore[arg-type] # No headers needed.
    else:
      assert isinstance(url, urllib.request.Request) and isinstance(url.data, bytes)
      if address.endswith('/git/refs'):
        assert json.loads(url.data) == {'ref': 'refs/tags/v1.0.0', 'sha': SHA}
        if change == 'tag-race':
          raise urllib.error.HTTPError(address, 422, 'Already exists', {}, None)  # type: ignore[arg-type] # No headers needed.
      elif address.endswith('/releases'):
        assert json.loads(url.data) == {'tag_name': 'v1.0.0', 'target_commitish': SHA,
          'name': 'bazi 1.0.0', 'body': 'Release notes', 'draft': True}
        value = {'id': 1}
      elif '/assets?' in address:
        value = {'digest': 'sha256:' + ('0' * 64 if change == 'asset-bytes' else hashlib.sha256(url.data).hexdigest())}
      else:
        assert address.endswith('/releases/1') and method == 'PATCH'
        assert json.loads(url.data) == {'draft': False}
      writes.append((method, address))
    return io.BytesIO(json.dumps(value).encode())
  monkeypatch.setattr(urllib.request, 'urlopen', request)
  code = WORKFLOW['jobs']['github-release']['steps'][2]['run']
  if change == 'none':
    run_policy(code)
    assert [method for method, _ in writes] == ['POST'] * 5 + ['PATCH']
  else:
    with pytest.raises((SystemExit, urllib.error.HTTPError)):
      run_policy(code)
    assert not any(method == 'PATCH' for method, _ in writes)
    if change != 'asset-bytes':
      assert writes == []
