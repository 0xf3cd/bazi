# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

# Policy tests for the documentation publishing workflow: structure, trust boundary and the inline policy code it runs.
# All repositories, tags, commits and sites here are synthetic; nothing touches the network or Git.

import base64
import hashlib
import io
import json
import re
import shlex
import shutil
import subprocess
import tarfile
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any, Final
from collections.abc import Callable, Mapping
from unittest.mock import Mock

import pytest
import yaml

import run_docs_site
from run_docs_site import RELEASE_LABEL, add_build, add_pending, mark_ready, read_manifest


WORKFLOWS = Path(__file__).parents[1] / '.github/workflows'
PUBLISH_TEXT = (WORKFLOWS / 'docs-publish.yml').read_text(encoding='utf-8')
PUBLISH = yaml.safe_load(PUBLISH_TEXT)
SHA, TAGGED, HEAD = 'a' * 40, 'b' * 40, '1' * 40
LIVE = 'https://0xf3cd.github.io/bazi/'
API, REPO = 'https://api.github.com', '/repos/0xf3cd/bazi'
STAGING, MOVED = 'docs-site-staging-7-1', '2' * 40
# The commit the archive job checked out as control/: nested sources, an executable, a symlink and a page at a path the site
# also uses. Initialization starts the staging branch here.
CONTROL = '3' * 40
CONTROL_TREE: Final[dict[str, bytes]] = {
  'README.md': b'synthetic source\n', 'run_tests.py': b'#!/usr/bin/env python3\n', 'docs/latest': b'index.rst',
  'bazi/calendar/__init__.py': b'', '.github/workflows/docs-publish.yml': b'name: synthetic\n', 'index.html': b'a control page'}
CONTROL_MODES: Final[dict[str, str]] = {'run_tests.py': '100755 blob', 'docs/latest': '120000 blob'}
COMMIT_STEP = 'Commit on a staging branch through GraphQL, check it, then fast-forward docs-site'
# The Pages actions are new to this repository; their tag-to-commit mapping was checked against upstream before pinning.
PAGES_PINS = frozenset({
  'actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0',
  'actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1',
})


def run_policy(code: str) -> None:
  exec(compile(code, '<docs-policy>', 'exec'), {})  # noqa: S102 # Execute the actual checked-in policy with fixture-backed I/O.


def step(job: str, name: str) -> dict[str, Any]:
  found: dict[str, Any] = next(item for item in PUBLISH['jobs'][job]['steps'] if item.get('name') == name)
  return found


def code(job: str, name: str) -> str:
  run: str = step(job, name)['run']
  return run


def outputs(path: Path) -> dict[str, str]:
  return dict(line.split('=', 1) for line in path.read_text(encoding='utf-8').splitlines())


def actions(job: str) -> list[str]:
  return [item['uses'].split('@')[0] for item in PUBLISH['jobs'][job]['steps'] if 'uses' in item]


def blob_id(content: bytes) -> str:
  return hashlib.sha1(b'blob %d\0' % len(content) + content).hexdigest()


def candidate(label: str, commit: str, body: bytes = b'') -> dict[str, bytes]:
  metadata = {'version': label, 'commit': commit, 'dirty': False, 'python': '3.12.0'}
  return {'index.html': b'SYNTHETIC ' + label.encode() + body, '_static/style.css': b'/* synthetic */\n',
    '.buildinfo': b'synthetic\n', 'build.json': json.dumps(metadata).encode()}


def tar_bytes(files: Mapping[str, bytes]) -> bytes:
  buffer = io.BytesIO()
  with tarfile.open(fileobj=buffer, mode='w') as archive:
    for name, content in sorted(files.items()):
      info = tarfile.TarInfo(name)
      info.size = len(content)
      archive.addfile(info, io.BytesIO(content))
  return buffer.getvalue()


def write_tree(root: Path, files: Mapping[str, bytes]) -> None:
  for name, content in files.items():
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_bytes(content)


def environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **values: str) -> Path:
  output = tmp_path / 'outputs'
  for key, value in {'GITHUB_OUTPUT': str(output), 'RUN_ID': '7', 'RUN_ATTEMPT': '1', **values}.items():
    monkeypatch.setenv(key, value)
  return output


@pytest.fixture
def site() -> dict[str, bytes]:
  '''Synthetic archive: dev ready, v99.0.0 archived but not read back, v99.1.0 pending.'''
  _, tree = add_build(None, candidate('dev', SHA), 'dev', SHA)
  tree = mark_ready(tree, 'dev', run_docs_site.digest(candidate('dev', SHA)))[1]
  _, tree = add_build(tree, candidate('v99.0.0', TAGGED), 'v99.0.0', TAGGED)
  _, tree = add_pending(tree, 'v99.1.0')
  return tree


def test_publish_workflow_structure() -> None:
  # PyYAML's YAML 1.1 parser reads the YAML 1.2 key `on` as True.
  trigger = PUBLISH[True]
  assert set(trigger) == {'workflow_dispatch'}
  inputs = trigger['workflow_dispatch']['inputs']
  assert set(inputs) == {'version', 'mode', 'initialize'}
  assert inputs['mode']['default'] == 'rehearsal' and inputs['mode']['options'] == ['rehearsal', 'publish', 'pending', 'promote', 'resume']
  assert inputs['initialize']['default'] is False
  assert PUBLISH['permissions'] == {}
  assert PUBLISH['concurrency'] == {'group': 'bazi-docs', 'cancel-in-progress': False}
  jobs = PUBLISH['jobs']
  assert {name: job['permissions'] for name, job in jobs.items()} == {
    'build': {'contents': 'read'}, 'check': {}, 'archive': {'contents': 'write'},
    'deploy': {'pages': 'write', 'id-token': 'write'}, 'readback': {}}
  assert {name: job.get('needs') for name, job in jobs.items()} == {
    'build': None, 'check': None, 'archive': ['build', 'check'], 'deploy': ['archive'], 'readback': ['archive', 'deploy']}
  assert {name: actions(name) for name in jobs} == {
    'build': ['actions/checkout', 'actions/setup-python', 'actions/upload-artifact'], 'check': [],
    'archive': ['actions/checkout', 'actions/download-artifact', 'actions/upload-pages-artifact'],
    'deploy': ['actions/deploy-pages'], 'readback': []}
  assert [name for name, job in jobs.items() if 'environment' in job] == ['deploy']
  assert jobs['deploy']['environment'] == {'name': 'github-pages', 'url': '${{ steps.deployment.outputs.page_url }}'}

  assert jobs['build']['if'] == "inputs.mode == 'rehearsal' || inputs.mode == 'publish'"
  assert jobs['check']['if'] == "inputs.mode == 'promote'"
  for name in ('archive', 'deploy', 'readback'):
    assert jobs[name]['if'].startswith('${{ !cancelled() && ')
  for condition in ("github.repository == '0xf3cd/bazi'", "github.ref == 'refs/heads/main'",
      "(inputs.mode == 'publish' && needs.build.result == 'success')", "(inputs.mode == 'promote' && needs.check.result == 'success')"):
    assert condition in jobs['archive']['if']
  for condition in ("needs.archive.result == 'success'", "github.repository == '0xf3cd/bazi'", "github.ref == 'refs/heads/main'"):
    assert condition in jobs['deploy']['if']
  assert "needs.deploy.result == 'success'" in jobs['readback']['if']

  # The archive job re-derives identity with the same step instead of trusting build outputs.
  assert jobs['build']['steps'][0] == jobs['archive']['steps'][0] == step('build', 'Resolve documentation source identity')
  assert jobs['build']['steps'][0]['if'] == jobs['build']['if']
  # Promotion consumes only what the no-permission check read from the live site.
  assert jobs['check']['steps'] == jobs['readback']['steps']
  assert jobs['check']['env'] == {'LABEL': '${{ inputs.version }}', 'COMMIT': ''}
  assert jobs['readback']['env'] == {'LABEL': '${{ inputs.version }}', 'COMMIT': '${{ needs.archive.outputs.commit }}'}
  assert step('archive', 'Read the archive branch')['env']['EXPECTED'] == '${{ needs.check.outputs.commit }}'
  assert step('archive', 'Apply the requested archive change')['env']['DIGEST'] == '${{ needs.check.outputs.digest }}'
  assert jobs['archive']['outputs'] == {'commit': '${{ steps.commit.outputs.commit }}'}
  assert step('archive', COMMIT_STEP)['env']['GH_TOKEN'] == '${{ github.token }}'
  # Initialization starts from the commit this job checked out as control/, not from any branch named by an input.
  assert step('archive', COMMIT_STEP)['env']['CONTROL'] == jobs['archive']['steps'][1]['with']['ref'] == '${{ github.sha }}'

  assert jobs['build']['steps'][1]['with'] == {'ref': '${{ steps.identity.outputs.ref }}', 'persist-credentials': False}
  assert jobs['archive']['steps'][1]['with'] == {'ref': '${{ github.sha }}', 'path': 'control', 'persist-credentials': False}
  assert jobs['archive']['steps'][2] == {'uses': jobs['archive']['steps'][2]['uses'], 'if': "inputs.mode == 'publish'", 'with': {
    'artifact-ids': '${{ needs.build.outputs.artifact-id }}', 'path': 'candidate', 'merge-multiple': True, 'digest-mismatch': 'error'}}
  # Hidden files such as .buildinfo are part of every version digest, so the Pages upload must keep them.
  upload = jobs['archive']['steps'][-1]
  assert upload['uses'].startswith('actions/upload-pages-artifact@')
  assert upload['with'] == {'path': 'site/', 'include-hidden-files': True, 'retention-days': 1}
  deploy = jobs['deploy']['steps']
  assert deploy[0]['name'] == 'Refuse to deploy a superseded archive' and deploy[-1] == {'uses': deploy[-1]['uses'], 'id': 'deployment'}
  assert '-I' in code('archive', 'Apply the requested archive change')
  # The privileged jobs install nothing and never run the built candidate.
  for name in ('archive', 'deploy'):
    for item in jobs[name]['steps']:
      assert not re.search(r'\b(pip|run_docs\.py|import bazi|candidate/(?!site\.tar))', item.get('run', ''))


def test_trust_boundary() -> None:
  text = json.dumps(PUBLISH)
  assert 'pull_request_target' not in text and 'workflow_run' not in text and 'secrets.' not in text
  for job in PUBLISH['jobs'].values():
    assert 'permissions' in job
    for item in job['steps']:
      # Inputs and contexts reach scripts only through env, never by template expansion.
      assert '${{' not in item.get('run', '')
      if 'actions/checkout' in item.get('uses', ''):
        assert item['with']['persist-credentials'] is False


def uses_lines(text: str) -> list[str]:
  return re.findall(r'^ *(?:- )?uses: (.*)$', text, re.MULTILINE)


def test_actions_use_existing_or_pinned_pages() -> None:
  existing = {line for path in WORKFLOWS.iterdir() if path.name != 'docs-publish.yml' for line in uses_lines(path.read_text(encoding='utf-8'))}
  lines = set(uses_lines(PUBLISH_TEXT))
  assert lines - existing == PAGES_PINS, sorted(lines - existing)
  # configure-pages could enable Pages with another token; the deployment does not need it.
  assert 'configure-pages' not in PUBLISH_TEXT


def test_workflow_never_touches_releases_or_tags() -> None:
  # Recovery reruns only the documentation stage: no PyPI upload, tag write or force update exists here.
  for forbidden in ('pypi', 'git push', 'git tag', '/git/refs/tags', "'force': True", 'refs/heads/main'):
    assert forbidden not in PUBLISH_TEXT.replace("github.ref == 'refs/heads/main'", '')


def test_workflow_makes_no_rest_commit() -> None:
  # Every commit comes from createCommitOnBranch and has its signature checked before docs-site points at it.
  assert '/git/commits' not in PUBLISH_TEXT and '/git/trees' not in PUBLISH_TEXT


def test_label_grammar_matches_the_assembler() -> None:
  assert f"re.fullmatch(r'{RELEASE_LABEL.pattern}', label)" in code('build', 'Resolve documentation source identity')


def check_python_ci(
  workflow: Mapping[str, Any], name: str, jobs: list[str], flags: set[str],
) -> None:
  for job in jobs:
    definition = workflow['jobs'][job]
    steps = definition['steps']
    matrix = definition.get('strategy', {}).get('matrix', {})
    versions = matrix.get('python-version')
    legs = matrix.get('include') or ([{'python-version': version} for version in versions] if versions else [
      {'python-version': next(item['with']['python-version'] for item in steps if 'setup-python@' in item.get('uses', ''))},
    ])
    if job == 'test-on-ubuntu':
      assert definition.get('name') == 'test-on-ubuntu (${{ matrix.python-version }})'
      expected = {'3.11', '3.12', '3.14'} if name == 'on_pull_request.yml' else {'3.11', '3.14'}
      assert {leg['python-version'] for leg in legs} == expected
    for leg in legs:
      version = leg['python-version']
      docs = tuple(map(int, version.split('.'))) >= (3, 12)
      commands = []
      installations = []
      for index, item in enumerate(steps):
        run = item.get('run', '')
        if 'pip install -r docs/requirements.txt' not in run and 'run_tests.py' not in run:
          continue
        condition = item.get('if')
        assert condition in (None, "matrix.python-version != '3.11'")
        if condition is not None and version == '3.11':
          continue
        if 'pip install -r docs/requirements.txt' in run:
          installations.append(index)
        for line in run.splitlines():
          if re.search(r'\brun_tests\.py\s+-', line):
            command = line.replace('${{ matrix.scope }}', leg.get('scope', ''))
            assert '${{' not in command
            commands.append((index, command))
      assert len(commands) == 1, (name, job, version, commands)
      index, command = commands[0]
      arguments = set(shlex.split(command))
      assert flags <= arguments, (name, job, version, command)
      assert ('--runtime-only' not in arguments) is docs, (name, job, version, command)
      assert bool(installations) is docs, (name, job, version, installations)
      assert all(installation < index for installation in installations)


@pytest.mark.parametrize('name, jobs, flags', [
  ('on_pull_request.yml', ['test-on-ubuntu', 'test-on-macos', 'test-on-windows'], {'-a', '-v'}),
  ('on_push.yml', ['test-on-ubuntu', 'test-on-macos', 'test-on-windows'], {'-ruff', '-mypy', '-d', '-osmoke'}),
  ('release.yml', ['build'], {'-a', '-v', '--package-output-dir'}),
])
def test_python_ci_keeps_runtime_and_docs_gates(
  name: str, jobs: list[str], flags: set[str],
) -> None:
  workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding='utf-8'))
  check_python_ci(workflow, name, jobs, flags)


@pytest.mark.parametrize('defect', ['no-min-docs', 'docs-on-311', 'skip-docs', 'no-docs-install', 'no-runtime-scope', 'changed-check-name'])
def test_python_ci_rejects_scope_regressions(defect: str) -> None:
  workflow = yaml.safe_load((WORKFLOWS / 'on_pull_request.yml').read_text(encoding='utf-8'))
  ubuntu = workflow['jobs']['test-on-ubuntu']
  legs = ubuntu['strategy']['matrix']['include']
  install = next(item for item in ubuntu['steps'] if 'pip install -r docs/requirements.txt' in item.get('run', ''))
  if defect == 'no-min-docs':
    legs[:] = [leg for leg in legs if leg['python-version'] != '3.12']
  elif defect == 'docs-on-311':
    del install['if']
  elif defect == 'skip-docs':
    next(leg for leg in legs if leg['python-version'] == '3.12')['scope'] = '--runtime-only'
  elif defect == 'no-docs-install':
    install['run'] = 'python --version'
  elif defect == 'no-runtime-scope':
    next(leg for leg in legs if leg['python-version'] == '3.11')['scope'] = ''
  else:
    del ubuntu['name']
  with pytest.raises(AssertionError):
    check_python_ci(workflow, 'on_pull_request.yml', ['test-on-ubuntu'], {'-a', '-v'})


@pytest.mark.parametrize('name', ['docs-publish.yml', 'release.yml'])
def test_doc_builders_use_supported_python(name: str) -> None:
  workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding='utf-8'))
  setup = next(item for item in workflow['jobs']['build']['steps'] if 'setup-python@' in item.get('uses', ''))
  assert tuple(map(int, setup['with']['python-version'].split('.'))) >= (3, 12)


def response(value: object) -> io.BytesIO:
  return io.BytesIO(json.dumps(value).encode())


@pytest.mark.parametrize('label, change, message', [
  ('dev', 'none', None),
  ('dev', 'sha', 'Invalid dispatch identity'),
  ('dev', 'repository', 'Invalid dispatch identity'),
  ('v99.0.0', 'none', None),
  ('v99.0.0', 'lightweight', None),
  ('v99.0.0', 'missing-tag', 'does not exist'),
  ('v99.0.0', 'draft', 'not a published release'),
  ('v99.0.0', 'prerelease', 'not a published release'),
  ('v99.0.0', 'no-asset', 'not a published release'),
  ('v99.0.0', 'asset-sha', 'does not name tag commit'),
  ('v99.0.0', 'asset-version', 'does not name tag commit'),
  ('v99.0.0', 'asset-repository', 'does not name tag commit'),
  ('v99.0.0', 'asset-mode', 'does not name tag commit'),
  ('v99.0.0', 'release-missing', 'HTTP Error 404'),
  ('latest', 'none', 'Expected dev or vMAJOR'),
  ('v99.0', 'none', 'Expected dev or vMAJOR'),
  ('refs/heads/main', 'none', 'Expected dev or vMAJOR'),
  ('v99.0.0\n', 'none', 'Expected dev or vMAJOR'),
])
def test_identity_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, change: str, message: str | None) -> None:
  output = environment(monkeypatch, tmp_path, LABEL=label, SHA=SHA, REPOSITORY='example/bazi')
  if change == 'sha':
    monkeypatch.setenv('SHA', 'main')
  elif change == 'repository':
    monkeypatch.setenv('REPOSITORY', 'example/bazi; rm -rf /')
  tags = {
    'none': f'{"c" * 40}\trefs/tags/v99.0.0\n{TAGGED}\trefs/tags/v99.0.0^{{}}\n',
    'lightweight': f'{TAGGED}\trefs/tags/v99.0.0\n',
    'missing-tag': '',
  }
  listing = Mock(return_value=tags.get(change, tags['none']))
  monkeypatch.setattr(subprocess, 'check_output', listing)
  metadata: dict[str, Any] = {'name': 'bazi', 'version': '99.0.0', 'sha': TAGGED, 'repository': 'example/bazi', 'run_id': '1', 'mode': 'release'}
  for case, (field, wrong) in {'asset-sha': ('sha', SHA), 'asset-version': ('version', '99.0.1'), 'asset-repository': ('repository', 'fork/bazi'), 'asset-mode': ('mode', 'rehearsal')}.items():
    if change == case:
      metadata[field] = wrong
  release = {'draft': change == 'draft', 'prerelease': change == 'prerelease',
    'assets': [] if change == 'no-asset' else [{'name': 'release.json', 'browser_download_url': 'https://example.invalid/release.json'}]}
  def get(request: urllib.request.Request, timeout: int) -> io.BytesIO:
    assert timeout == 30 and request.get_method() == 'GET'
    if request.full_url == 'https://api.github.com/repos/example/bazi/releases/tags/v99.0.0':
      if change == 'release-missing':
        raise urllib.error.HTTPError(request.full_url, 404, 'Not Found', {}, None)  # type: ignore[arg-type] # Fixture has no response headers.
      return response(release)
    assert request.full_url == 'https://example.invalid/release.json'
    return response(metadata)
  monkeypatch.setattr(urllib.request, 'urlopen', get)
  policy = code('build', 'Resolve documentation source identity')
  if message is not None:
    with pytest.raises((SystemExit, urllib.error.HTTPError), match=message):
      run_policy(policy)
    assert not output.exists()
    return
  run_policy(policy)
  if label == 'dev':
    assert outputs(output) == {'ref': SHA, 'commit': SHA}
    listing.assert_not_called()
  else:
    assert outputs(output) == {'ref': 'refs/tags/v99.0.0', 'commit': TAGGED}
    listing.assert_called_once_with(['git', 'ls-remote', 'https://github.com/example/bazi.git', 'refs/tags/v99.0.0', 'refs/tags/v99.0.0^{}'], text=True)


@pytest.mark.parametrize('change, message', [
  ('none', None),
  ('head', 'Checkout differs'),
  ('no-runner', 'ships no documentation runner'),
  ('no-checks', 'ships no documentation runner'),
  ('no-requirements', 'ships no documentation runner'),
])
def test_checkout_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str, message: str | None) -> None:
  monkeypatch.chdir(tmp_path)
  monkeypatch.setenv('LABEL', 'v99.0.0')
  monkeypatch.setenv('COMMIT', TAGGED)
  (tmp_path / 'docs').mkdir()
  for name in ('run_docs.py', 'run_doc_checks.py', 'docs/requirements.txt'):
    (tmp_path / name).write_text('', encoding='utf-8')
  removed = {'no-runner': 'run_docs.py', 'no-checks': 'run_doc_checks.py', 'no-requirements': 'docs/requirements.txt'}.get(change)
  if removed:
    (tmp_path / removed).unlink()
  monkeypatch.setattr(subprocess, 'check_output', Mock(return_value=(SHA if change == 'head' else TAGGED) + '\n'))
  policy = code('build', 'Verify checkout and documentation runner')
  if message is None:
    run_policy(policy)
  else:
    with pytest.raises(SystemExit, match=message):
      run_policy(policy)


class FakeGit:
  '''Answers the git commands of the inline steps from an in-memory branch; anything else runs for real.'''

  def __init__(self, commits: dict[str, dict[str, bytes]], head: str | None) -> None:
    # The repository always holds the control commit the archive job checked out.
    self.commits, self.head = {CONTROL: CONTROL_TREE} | commits, head
    self.fetched: str | None = None
    self.modes: dict[str, str] = {}
    self.control_modes = dict(CONTROL_MODES)
    self.export: Callable[[dict[str, bytes]], dict[str, bytes]] = dict
    self.ls_remote_code: int | None = None
    self.real_run: Callable[..., Any] = subprocess.run
    self.real_check_output: Callable[..., Any] = subprocess.check_output

  def listing(self) -> str:
    return f'{self.head}\trefs/heads/docs-site\n' if self.head else ''

  def tree(self, commit: str) -> dict[str, bytes]:
    return self.export(self.commits[commit])

  def run(self, command: list[str], **kwargs: Any) -> Any:
    if command[0] != 'git':
      return self.real_run(command, **kwargs)
    if command[1] == 'ls-remote':
      code = self.ls_remote_code if self.ls_remote_code is not None else 0 if self.head else 2
      return subprocess.CompletedProcess(command, code, self.listing(), '')
    if 'fetch' in command:
      self.fetched = self.head
    elif '--format=tar' in command:
      Path(command[command.index('-o') + 1]).write_bytes(tar_bytes(self.tree(command[-1])))
    return subprocess.CompletedProcess(command, 0, '', '')

  def check_output(self, command: list[str], **kwargs: Any) -> Any:
    if command[0] != 'git':
      return self.real_check_output(command, **kwargs)
    if command[1] == 'ls-remote':
      return self.listing()
    if 'rev-parse' in command:
      return f'{self.fetched}\n'
    if command[1:3] == ['-C', 'control']:
      # Of the control checkout only the full recursive listing of one commit is read.
      assert command[3:-1] == ['ls-tree', '-r', '-z', '--full-tree']
      return ''.join(f'{self.control_modes.get(name, "100644 blob")} {blob_id(content)}\t{name}\0' for name, content in sorted(self.commits[command[-1]].items()))
    if 'ls-tree' in command:
      return ''.join(f'{self.modes.get(name, "100644 blob")} {blob_id(content)}\t{name}\0' for name, content in sorted(self.commits[command[-1]].items()))
    assert '--format=tar' in command
    return tar_bytes(self.tree(command[-1]))


@pytest.mark.parametrize('change, message', [
  ('exists', None),
  ('absent', None),
  ('absent-without-initialize', 'initialize must be true exactly'),
  ('exists-with-initialize', 'initialize must be true exactly'),
  ('query-error', 'Cannot query'),
  ('expected', None),
  ('expected-mismatch', 'moved after the live check'),
  ('moved-while-read', 'moved while it was read'),
  ('symlink', 'not a regular file'),
  ('executable', 'not a regular file'),
  ('submodule', 'not a regular file'),
  ('export-ignore', 'differs from the archive tree'),
  ('export-subst', 'differs from the archive tree'),
])
def test_read_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: dict[str, bytes], change: str, message: str | None) -> None:
  monkeypatch.chdir(tmp_path)
  absent = change.startswith('absent')
  initialize = change in ('absent', 'exists-with-initialize')
  output = environment(monkeypatch, tmp_path, INITIALIZE='true' if initialize else 'false', EXPECTED=HEAD if change == 'expected' else '2' * 40 if change == 'expected-mismatch' else '')
  git = FakeGit({HEAD: site}, None if absent else HEAD)
  if change == 'query-error':
    git.ls_remote_code = 128
  elif change == 'moved-while-read':
    git.check_output = lambda command, **kwargs: '2' * 40 + '\n' if 'rev-parse' in command else FakeGit.check_output(git, command, **kwargs)  # type: ignore[method-assign] # Swap one answer.
  elif change in ('symlink', 'executable', 'submodule'):
    git.modes['v99.0.0/index.html'] = {'symlink': '120000 blob', 'executable': '100755 blob', 'submodule': '160000 commit'}[change]
  elif change == 'export-ignore':
    git.export = lambda tree: {name: content for name, content in tree.items() if name != 'v99.0.0/index.html'}
  elif change == 'export-subst':
    git.export = lambda tree: tree | {'v99.0.0/index.html': b'$Format:%H$ expanded'}
  monkeypatch.setattr(subprocess, 'run', git.run)
  monkeypatch.setattr(subprocess, 'check_output', git.check_output)
  policy = code('archive', 'Read the archive branch')
  if message is not None:
    with pytest.raises(SystemExit, match=message):
      run_policy(policy)
    assert not output.exists()
    return
  run_policy(policy)
  assert outputs(output) == {'parent': '' if absent else HEAD}
  assert json.loads((tmp_path / 'archive.json').read_text(encoding='utf-8')) == ({} if absent else {name: blob_id(content) for name, content in site.items()})
  if not absent:
    assert run_docs_site.read_tree(tmp_path / 'archive.tar') == site


@pytest.mark.parametrize('mode, parent, expected', [
  ('publish', HEAD, ['archive', '--archive', 'archive.tar', '--label', 'v99.0.0', '--output', 'site', '--candidate', 'candidate/site.tar', '--commit', TAGGED]),
  ('publish', '', ['archive', '--initialize', '--label', 'v99.0.0', '--output', 'site', '--candidate', 'candidate/site.tar', '--commit', TAGGED]),
  ('pending', HEAD, ['pending', '--archive', 'archive.tar', '--label', 'v99.0.0', '--output', 'site']),
  ('promote', HEAD, ['promote', '--archive', 'archive.tar', '--label', 'v99.0.0', '--output', 'site', '--verified-digest', 'f' * 64]),
  ('resume', HEAD, ['current', '--archive', 'archive.tar', '--label', 'v99.0.0', '--output', 'site']),
])
def test_apply_policy(monkeypatch: pytest.MonkeyPatch, mode: str, parent: str, expected: list[str]) -> None:
  for key, value in {'MODE': mode, 'LABEL': 'v99.0.0', 'COMMIT': TAGGED, 'DIGEST': 'f' * 64, 'PARENT': parent}.items():
    monkeypatch.setenv(key, value)
  assembler = Mock(return_value='{}')
  monkeypatch.setattr(subprocess, 'check_output', assembler)
  run_policy(code('archive', 'Apply the requested archive change'))
  command = assembler.call_args.args[0]
  assert command[1:4] == ['-I', '-B', 'control/run_docs_site.py'] and command[4:] == expected


def git_tree(files: Mapping[str, bytes], modes: Mapping[str, str] | None = None) -> str:
  '''Git tree id of a file table, built bottom-up per directory; written apart from the workflow's top-down helper.'''
  def depth(directory: str) -> int:
    return directory.count('/') + 1 if directory else 0
  directories: dict[str, list[tuple[bytes, bytes]]] = {}
  for path, content in files.items():
    parts = path.split('/')
    for end in range(len(parts)):
      directories.setdefault('/'.join(parts[:end]), [])
    directory, _, name = path.rpartition('/')
    mode = (modes or {}).get(path, '100644')
    directories[directory].append((name.encode(), f'{mode} {name}'.encode() + b'\0' + bytes.fromhex(blob_id(content))))
  oid = ''
  for directory in sorted(directories, key=depth, reverse=True):
    content = b''.join(entry for _, entry in sorted(directories[directory]))
    oid = hashlib.sha1(b'tree %d\0' % len(content) + content).hexdigest()
    if directory:
      parent, _, name = directory.rpartition('/')
      # Git orders a subtree as if its name ended with '/'.
      directories[parent].append((name.encode() + b'/', f'40000 {name}'.encode() + b'\0' + bytes.fromhex(oid)))
  return oid


def http_error(url: str, code: int, reason: str) -> urllib.error.HTTPError:
  return urllib.error.HTTPError(url, code, reason, {}, None)  # type: ignore[arg-type] # Fixture has no response headers.


# The GitSignature fields the step reads (published GraphQL schema). The schema says createCommitOnBranch commits are signed by
# GitHub "if supported"; tests choose the answer per case and show only how the step reacts to it.
SIGNED: Final[dict[str, bool]] = {'isValid': True, 'wasSignedByGitHub': True}


class FakeApi:
  '''The endpoints of the commit step over FakeGit's object store: refs, the GraphQL control commit lookup and createCommitOnBranch.

  Request and response shapes follow the published REST and GraphQL schemas; every platform answer is a per-test fixture choice.
  '''

  def __init__(self, git: FakeGit) -> None:
    self.git = git
    self.branches: dict[str, str] = {}  # Every branch but docs-site, whose head is git.head.
    self.parents: dict[str, list[str]] = {}
    self.calls: list[tuple[str, str, dict[str, Any]]] = []
    self.signature: dict[str, bool] | None = SIGNED
    # The control commit's signature: valid whether the user's own key or GitHub's made it. control_answer replaces the whole lookup.
    self.control_signature: dict[str, bool] | None = {'isValid': True}
    self.control_answer: dict[str, Any] | None = None
    self.stored: Callable[[dict[str, bytes]], dict[str, bytes]] = dict  # What the platform commits for the requested files.
    self.modes: dict[str, str] = {}
    self.reported_parent: str | None = None
    self.staging_moved: str | None = None  # Someone moves the staging branch right before the GraphQL call.
    self.moved: str | None = None  # Someone moves or creates docs-site right before this run does.
    self.fail: set[str] = set()

  def head(self, branch: str) -> str | None:
    return self.git.head if branch == 'docs-site' else self.branches.get(branch)

  def point(self, branch: str, sha: str) -> None:
    if branch == 'docs-site':
      self.git.head = sha
    else:
      self.branches[branch] = sha

  def __call__(self, request: urllib.request.Request, timeout: int) -> io.BytesIO:
    assert request.full_url.startswith(API) and request.get_header('Authorization') == 'Bearer offline-fixture' and timeout == 60
    method, path = request.get_method(), request.full_url.removeprefix(API)
    body = json.loads(request.data) if isinstance(request.data, bytes) else {}
    self.calls.append((method, path, body))
    if path == '/graphql':
      if body['query'].startswith('query('):
        return self.control_commit(body)
      return self.create_commit_on_branch(request.full_url, body)
    assert path.startswith(REPO + '/git/')
    path = path.removeprefix(REPO)
    if (method, path) == ('POST', '/git/refs'):
      # Only docs-site and this run's staging branch are ever written; main, release branches and tags are not.
      branch = body['ref'].removeprefix('refs/heads/')
      assert branch in ('docs-site', STAGING) and body['sha'] in self.git.commits
      if branch == 'docs-site' and self.moved is not None:
        self.git.head = self.moved
      if self.head(branch) is not None:
        raise http_error(request.full_url, 422, 'Reference already exists')
      self.point(branch, body['sha'])
      if branch == 'docs-site' and 'create-response-lost' in self.fail:
        raise http_error(request.full_url, 502, 'Bad Gateway')
      return response({'ref': body['ref'], 'object': {'sha': body['sha']}})
    if method == 'PATCH':
      assert path == '/git/refs/heads/docs-site' and body['force'] is False
      if self.moved is not None:
        self.git.head = self.moved
      if self.parents.get(body['sha']) != [self.git.head]:
        raise http_error(request.full_url, 422, 'Update is not a fast forward')
      self.git.head = body['sha']
      return response({'object': {'sha': body['sha']}})
    assert (method, path) == ('DELETE', f'/git/refs/heads/{STAGING}')
    if 'delete' in self.fail:
      raise http_error(request.full_url, 502, 'Bad Gateway')
    del self.branches[STAGING]
    return io.BytesIO(b'')

  def control_commit(self, body: dict[str, Any]) -> io.BytesIO:
    # Repository.object(oid) is a GitObject; the step selects a commit's oid and whether its signature is valid, nothing more.
    for selection in ('repository(owner: "0xf3cd", name: "bazi")', 'object(oid: $oid)', '... on Commit { oid signature { isValid } }'):
      assert selection in body['query']
    if self.control_answer is not None:
      return response(self.control_answer)
    oid = body['variables']['oid']
    found = {'oid': oid, 'signature': self.control_signature} if oid in self.git.commits else None
    return response({'data': {'repository': {'object': found}}})

  def create_commit_on_branch(self, url: str, body: dict[str, Any]) -> io.BytesIO:
    if 'graphql-unavailable' in self.fail:
      raise http_error(url, 502, 'Bad Gateway')
    query, change = body['query'], body['variables']['input']
    # The fake answers with the fields the step selects, so the step must select every field it checks.
    for selection in ('createCommitOnBranch(input: $input)', 'commit { oid', 'tree { oid }', 'parents(first: 2) { nodes { oid } }', 'signature { isValid wasSignedByGitHub }'):
      assert selection in query
    assert set(change) == {'branch', 'expectedHeadOid', 'message', 'fileChanges'}
    assert change['branch'] == {'repositoryNameWithOwner': '0xf3cd/bazi', 'branchName': STAGING}
    if self.staging_moved is not None:
      self.branches[STAGING] = self.staging_moved
    head = self.head(STAGING)
    if head is None or change['expectedHeadOid'] != head:
      return response({'data': {'createCommitOnBranch': None}, 'errors': [{'type': 'STALE_DATA', 'message': 'Expected branch to point to the expected head'}]})
    additions, deletions = change['fileChanges']['additions'], change['fileChanges']['deletions']
    paths = [item['path'] for item in additions + deletions]
    # Schema: path values must be unique across all additions and deletions.
    assert len(paths) == len(set(paths))
    files = dict(self.git.commits[head])
    # Schema: a path to delete must exist on the branch, otherwise the commit is aborted with an error.
    if any(item['path'] not in files for item in deletions):
      return response({'data': {'createCommitOnBranch': None}, 'errors': [{'message': 'A path to delete does not exist'}]})
    for item in deletions:
      del files[item['path']]
    for item in additions:
      files[item['path']] = base64.b64decode(item['contents'], validate=True)
    files = self.stored(files)
    sha = hashlib.sha1(f'{head} {git_tree(files, self.modes)} {len(self.parents)}'.encode()).hexdigest()
    self.git.commits[sha], self.parents[sha] = files, [head]
    self.branches[STAGING] = sha
    if 'graphql-response-lost' in self.fail:
      raise http_error(url, 502, 'Bad Gateway')
    commit = {'oid': sha, 'tree': {'oid': git_tree(files, self.modes)}, 'parents': {'nodes': [{'oid': self.reported_parent or head}]}, 'signature': self.signature}
    return response({'data': {'createCommitOnBranch': {'commit': commit}}})


def commit_step(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, git: FakeGit, api: FakeApi, mode: str, label: str, old: Mapping[str, bytes], new: Mapping[str, bytes]) -> Path:
  monkeypatch.chdir(tmp_path)
  parent = git.head or ''
  output = environment(monkeypatch, tmp_path, MODE=mode, LABEL=label, PARENT=parent, CONTROL=CONTROL, GH_TOKEN='offline-fixture')
  shutil.rmtree(tmp_path / 'site', ignore_errors=True)
  write_tree(tmp_path / 'site', new)
  (tmp_path / 'archive.json').write_text(json.dumps({name: blob_id(content) for name, content in old.items()}), encoding='utf-8')
  monkeypatch.setattr(urllib.request, 'urlopen', api)
  monkeypatch.setattr(subprocess, 'check_output', git.check_output)
  run_policy(code('archive', COMMIT_STEP))
  return output


def changed(tree: Mapping[str, bytes], edits: Mapping[str, bytes | None]) -> dict[str, bytes]:
  result = dict(tree)
  for name, content in edits.items():
    if content is None:
      del result[name]
    else:
      result[name] = content
  return result


# A release with a page and a directory of the same stem (Git orders api.html before the api/ subtree), and a dev rebuild that drops a file.
RELEASE = changed(candidate('v99.2.0', 'c' * 40), {'api.html': b'page', 'api/index.html': b'subpage'})
DEV = changed(candidate('dev', 'd' * 40, b'next'), {'_static/style.css': None, 'search.html': b'new page'})


@pytest.mark.parametrize('case', ['publish-release', 'publish-dev', 'promote', 'pending', 'unchanged', 'initialize'])
def test_commit_policy_checks_staging_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: dict[str, bytes], case: str) -> None:
  old = {} if case == 'initialize' else site
  mode, label, new = {
    'publish-release': ('publish', 'v99.2.0', add_build(site, RELEASE, 'v99.2.0', 'c' * 40)[1]),
    'publish-dev': ('publish', 'dev', add_build(site, DEV, 'dev', 'd' * 40)[1]),
    'promote': ('promote', 'v99.0.0', mark_ready(site, 'v99.0.0', run_docs_site.digest(candidate('v99.0.0', TAGGED)))[1]),
    'pending': ('pending', 'v99.3.0', add_pending(site, 'v99.3.0')[1]),
    'unchanged': ('resume', 'dev', site),
    'initialize': ('pending', 'v99.1.0', add_pending(None, 'v99.1.0')[1]),
  }[case]
  git = FakeGit({HEAD: site}, None if case == 'initialize' else HEAD)
  api = FakeApi(git)
  output = commit_step(tmp_path, monkeypatch, git, api, mode, label, old, new)
  commit = outputs(output)['commit']
  if case == 'unchanged':
    assert commit == HEAD and api.calls == []
    return
  # docs-site holds exactly the assembled site and the staging branch is gone.
  assert git.head == commit and git.commits[commit] == new and api.branches == {}
  # Only initialization looks up the control commit; every other change is one GraphQL call.
  graphql = [body['variables'] for _, path, body in api.calls if path == '/graphql']
  assert len(graphql) == (2 if case == 'initialize' else 1)
  request = graphql[-1]['input']
  (base,) = api.parents[commit]
  assert request['expectedHeadOid'] == base == (CONTROL if case == 'initialize' else HEAD)
  assert request['message'] == {'headline': f'docs: {mode} {label}', 'body': 'Workflow run 7.'}
  # Only changed files are sent; files missing from the new site are deleted explicitly.
  additions = {item['path']: base64.b64decode(item['contents']) for item in request['fileChanges']['additions']}
  assert additions == {name: content for name, content in new.items() if old.get(name) != content}
  deletions = [item['path'] for item in request['fileChanges']['deletions']]
  if case == 'publish-dev':
    assert deletions == ['dev/_static/style.css']
  writes = [(method, path.removeprefix(REPO), body.get('ref')) for method, path, body in api.calls if path != '/graphql']
  update = ('PATCH', '/git/refs/heads/docs-site', None) if case != 'initialize' else ('POST', '/git/refs', 'refs/heads/docs-site')
  assert writes == [('POST', '/git/refs', f'refs/heads/{STAGING}'), update, ('DELETE', f'/git/refs/heads/{STAGING}', None)]
  if case == 'initialize':
    # The first archive commit deletes every control path the site does not overwrite.
    assert deletions == sorted(CONTROL_TREE.keys() - new.keys())
  else:
    assert deletions == sorted(old.keys() - new.keys())


@pytest.mark.parametrize('case, mode, label', [
  ('release-modified', 'publish', 'v99.0.0'),
  ('release-deleted', 'publish', 'v99.0.0'),
  ('other-version', 'publish', 'v99.2.0'),
  ('promote-touches-directory', 'promote', 'v99.0.0'),
  ('pending-touches-directory', 'pending', 'v99.1.0'),
  ('resume-changes-anything', 'resume', 'dev'),
  ('generated-deleted', 'promote', 'v99.0.0'),
  ('lookalike-directory', 'publish', 'v99.0.0'),
  ('unknown-root-file', 'publish', 'dev'),
])
def test_commit_policy_refuses_stray_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: dict[str, bytes], case: str, mode: str, label: str) -> None:
  new = {
    'release-modified': changed(site, {'v99.0.0/index.html': b'edited'}),
    'release-deleted': changed(site, {'v99.0.0/build.json': None}),
    'other-version': changed(site, {'v99.2.0/index.html': b'new', 'v99.0.0/index.html': b'edited'}),
    'promote-touches-directory': changed(site, {'v99.0.0/extra.html': b'new'}),
    'pending-touches-directory': changed(site, {'v99.1.0/index.html': b'new'}),
    'resume-changes-anything': changed(site, {'versions.json': b'{}'}),
    'generated-deleted': changed(site, {'versions/index.html': None}),
    'lookalike-directory': changed(site, {'v99.0.0.evil/index.html': b'new'}),
    'unknown-root-file': changed(site, {'CNAME': b'example.com'}),
  }[case]
  git = FakeGit({HEAD: site}, HEAD)
  api = FakeApi(git)
  with pytest.raises(SystemExit, match='Refusing archive change'):
    commit_step(tmp_path, monkeypatch, git, api, mode, label, site, new)
  assert api.calls == [] and git.head == HEAD


@pytest.mark.parametrize('case, message', [
  ('unsigned', 'did not sign the archive commit'),
  ('invalid-signature', 'did not sign the archive commit'),
  ('foreign-signature', 'did not sign the archive commit'),
  ('release-bytes-changed', 'tree that differs'),
  ('deletion-dropped', 'tree that differs'),
  ('executable', 'tree that differs'),
  ('other-parent', 'another parent'),
  ('staging-moved', 'createCommitOnBranch failed'),
  ('graphql-unavailable', 'HTTP Error 502'),
  ('graphql-response-lost', 'HTTP Error 502'),
  ('docs-site-moved', 'HTTP Error 422'),
])
def test_commit_policy_keeps_site_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: dict[str, bytes], case: str, message: str) -> None:
  new = add_build(site, DEV, 'dev', 'd' * 40)[1]
  git = FakeGit({HEAD: site, MOVED: site}, HEAD)
  api = FakeApi(git)
  if case in ('unsigned', 'invalid-signature', 'foreign-signature'):
    api.signature = {'unsigned': None, 'invalid-signature': SIGNED | {'isValid': False}, 'foreign-signature': SIGNED | {'wasSignedByGitHub': False}}[case]
  elif case == 'release-bytes-changed':
    api.stored = lambda files: changed(files, {'v99.0.0/index.html': b'edited'})
  elif case == 'deletion-dropped':
    api.stored = lambda files: files | {'dev/_static/style.css': site['dev/_static/style.css']}
  elif case == 'executable':
    api.modes = {'dev/search.html': '100755'}
  elif case == 'other-parent':
    api.reported_parent = MOVED
  elif case == 'staging-moved':
    api.staging_moved = MOVED
  elif case == 'docs-site-moved':
    api.moved = MOVED
  else:
    api.fail = {case}
  with pytest.raises((SystemExit, urllib.error.HTTPError), match=message):
    commit_step(tmp_path, monkeypatch, git, api, 'publish', 'dev', site, new)
  # docs-site keeps its head, or the head a concurrent writer gave it; the staging branch is deleted either way.
  assert git.head == (MOVED if case == 'docs-site-moved' else HEAD) and api.branches == {}
  docs_site_writes = [method for method, path, body in api.calls if path.endswith('/heads/docs-site') or body.get('ref') == 'refs/heads/docs-site']
  assert docs_site_writes == (['PATCH'] if case == 'docs-site-moved' else [])


INITIAL = add_build(None, candidate('dev', SHA), 'dev', SHA)[1]


@pytest.mark.parametrize('case, message', [
  ('valid-signature', None),
  ('replaced-mode-reset', None),
  ('invalid-signature', 'no valid signature on control commit'),
  ('unsigned', 'no valid signature on control commit'),
  ('other-oid', 'no valid signature on control commit'),
  ('not-found', 'no valid signature on control commit'),
  ('lookup-error', 'no valid signature on control commit'),
  ('deletion-dropped', 'tree that differs'),
  ('replaced-mode-kept', 'tree that differs'),
  ('staging-moved', 'createCommitOnBranch failed'),
])
def test_init_starts_from_signed_control_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str, message: str | None) -> None:
  git = FakeGit({}, None)
  api = FakeApi(git)
  if case in ('invalid-signature', 'unsigned'):
    api.control_signature = {'isValid': False} if case == 'invalid-signature' else None
  elif case in ('other-oid', 'not-found', 'lookup-error'):
    answers: dict[str, dict[str, Any]] = {
      'other-oid': {'data': {'repository': {'object': {'oid': MOVED, 'signature': {'isValid': True}}}}},
      'not-found': {'data': {'repository': {'object': None}}},
      'lookup-error': {'data': None, 'errors': [{'type': 'NOT_FOUND', 'message': 'Could not resolve to a Repository'}]}}
    api.control_answer = answers[case]
  elif case == 'deletion-dropped':
    # The platform leaves a control file behind; only the tree check notices.
    api.stored = lambda files: files | {'README.md': CONTROL_TREE['README.md']}
  elif case.startswith('replaced-mode'):
    # The control page the site overwrites is executable. Whether GitHub keeps that mode is not documented; the step holds either way.
    git.control_modes['index.html'] = '100755 blob'
    api.modes = {'index.html': '100755'} if case == 'replaced-mode-kept' else {}
  elif case == 'staging-moved':
    api.staging_moved = MOVED
  if message is not None:
    with pytest.raises(SystemExit, match=message):
      commit_step(tmp_path, monkeypatch, git, api, 'publish', 'dev', {}, INITIAL)
    # docs-site is never created and no staging branch is left.
    assert git.head is None and api.branches == {}
    assert not [body for _, path, body in api.calls if body.get('ref') == 'refs/heads/docs-site']
    if 'signature' in message:
      # Nothing is written before GitHub vouches for the control commit.
      assert [(method, path) for method, path, _ in api.calls] == [('POST', '/graphql')]
    return
  commit = outputs(commit_step(tmp_path, monkeypatch, git, api, 'publish', 'dev', {}, INITIAL))['commit']
  # docs-site holds exactly the site, and its first archive commit sits directly on the control commit.
  assert git.head == commit and git.commits[commit] == INITIAL and api.parents[commit] == [CONTROL] and api.branches == {}
  lookup, change = [body['variables'] for _, path, body in api.calls if path == '/graphql']
  assert lookup == {'oid': CONTROL} and change['input']['expectedHeadOid'] == CONTROL
  additions = {item['path']: base64.b64decode(item['contents']) for item in change['input']['fileChanges']['additions']}
  deletions = [item['path'] for item in change['input']['fileChanges']['deletions']]
  # The whole site is written and every other control path deleted; index.html exists on both sides and is only overwritten.
  assert additions == INITIAL and deletions == ['.github/workflows/docs-publish.yml', 'README.md', 'bazi/calendar/__init__.py', 'docs/latest', 'run_tests.py']
  calls = [(method, path.removeprefix(REPO), body.get('ref'), body.get('sha')) for method, path, body in api.calls]
  assert calls == [('POST', '/graphql', None, None), ('POST', '/git/refs', f'refs/heads/{STAGING}', CONTROL), ('POST', '/graphql', None, None),
    ('POST', '/git/refs', 'refs/heads/docs-site', commit), ('DELETE', f'/git/refs/heads/{STAGING}', None, None)]


def test_commit_policy_warns_if_branch_stays(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: dict[str, bytes], capsys: pytest.CaptureFixture[str]) -> None:
  new = add_build(site, DEV, 'dev', 'd' * 40)[1]
  git = FakeGit({HEAD: site}, HEAD)
  api = FakeApi(git)
  api.fail = {'delete'}
  commit = outputs(commit_step(tmp_path, monkeypatch, git, api, 'publish', 'dev', site, new))['commit']
  assert git.head == commit != HEAD and git.commits[commit] == new
  assert f'::warning::Staging branch {STAGING} was not deleted' in capsys.readouterr().out


@pytest.mark.parametrize('head, message', [(HEAD, None), ('2' * 40, 'docs-site moved'), ('', 'docs-site moved')])
def test_deploy_refuses_a_superseded_archive(monkeypatch: pytest.MonkeyPatch, head: str, message: str | None) -> None:
  monkeypatch.setenv('COMMIT', HEAD)
  query = Mock(return_value=f'{head}\trefs/heads/docs-site\n' if head else '')
  monkeypatch.setattr(subprocess, 'check_output', query)
  policy = code('deploy', 'Refuse to deploy a superseded archive')
  if message is None:
    run_policy(policy)
  else:
    with pytest.raises(SystemExit, match=message):
      run_policy(policy)
  query.assert_called_once_with(['git', 'ls-remote', '--heads', 'https://github.com/0xf3cd/bazi.git', 'refs/heads/docs-site'], text=True)


class FakePages:
  '''The live site: answers https GETs from a dict, optionally failing the first few attempts.'''

  def __init__(self, files: Mapping[str, bytes]) -> None:
    self.files = dict(files)
    self.misses = 0
    self.requests: list[str] = []

  def __call__(self, url: str, timeout: int) -> io.BytesIO:
    assert url.startswith(LIVE) and url.endswith('?run=7-1') and timeout == 30
    path = url.removeprefix(LIVE).removesuffix('?run=7-1')
    self.requests.append(path)
    if self.misses or path not in self.files:
      self.misses = max(self.misses - 1, 0)
      raise urllib.error.HTTPError(url, 404, 'Not Found', {}, None)  # type: ignore[arg-type] # Fixture has no response headers.
    return io.BytesIO(self.files[path])


def readback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, git: FakeGit, pages: FakePages, label: str, commit: str) -> dict[str, str]:
  monkeypatch.chdir(tmp_path)
  shutil.rmtree(tmp_path / 'expected', ignore_errors=True)
  output = environment(monkeypatch, tmp_path, LABEL=label, COMMIT=commit)
  output.unlink(missing_ok=True)
  monkeypatch.setattr(subprocess, 'run', git.run)
  monkeypatch.setattr(subprocess, 'check_output', git.check_output)
  monkeypatch.setattr(urllib.request, 'urlopen', pages)
  clock = iter(range(0, 10_000, 30))
  monkeypatch.setattr('time.monotonic', lambda: next(clock))
  monkeypatch.setattr('time.sleep', Mock())
  run_policy(code('readback', 'Read back the live site against the archive commit'))
  return outputs(output)


@pytest.mark.parametrize('change, label, message', [
  ('none', 'v99.0.0', None),
  ('check', 'v99.0.0', None),
  ('late', 'v99.0.0', None),
  ('pending-label', 'v99.1.0', None),
  ('own-file-differs', 'v99.0.0', 'still differs'),
  ('own-hidden-file-missing', 'v99.0.0', 'still differs'),
  ('manifest-differs', 'v99.0.0', 'still differs'),
  ('selector-differs', 'v99.0.0', 'still differs'),
  ('root-page-missing', 'v99.0.0', 'still differs'),
  ('retained-version-differs', 'v99.0.0', 'still differs'),
  ('retained-version-missing', 'v99.1.0', 'still differs'),
  ('retained-page-differs', 'v99.0.0', 'still differs'),
  ('retained-hidden-file-missing', 'v99.0.0', 'still differs'),
  ('retained-digest-differs', 'v99.0.0', 'Live dev digest differs'),
  ('own-digest-differs', 'v99.0.0', 'Live v99.0.0 digest differs'),
  ('branch-moved', 'v99.0.0', 'no longer points'),
  ('unknown-label', 'v99.9.0', 'not in the archive'),
])
def test_readback_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: dict[str, bytes], change: str, label: str, message: str | None) -> None:
  archive = site
  if change.endswith('digest-differs'):
    # The archive records a digest its own files do not have: byte equality with the archive alone would let it through.
    recorded = next(entry for entry in read_manifest(site['versions.json']) if entry.label == ('dev' if change.startswith('retained') else 'v99.0.0')).digest
    assert recorded is not None
    archive = changed(site, {'versions.json': site['versions.json'].replace(recorded.encode(), b'0' * 64)})
  git = FakeGit({HEAD: archive}, HEAD)
  if change == 'branch-moved':
    git.commits['2' * 40] = site
    git.head = '2' * 40
  edits: dict[str, dict[str, bytes | None]] = {
    'own-file-differs': {'v99.0.0/index.html': b'stale'}, 'own-hidden-file-missing': {'v99.0.0/.buildinfo': None},
    'manifest-differs': {'versions.json': b'{}'}, 'selector-differs': {'versions/index.html': b'old'}, 'root-page-missing': {'index.html': None},
    'retained-version-differs': {'dev/build.json': b'{}'}, 'retained-version-missing': {'v99.0.0/build.json': None},
    # The independent review's counterexample: a retained version's page is stale while its build.json still matches.
    'retained-page-differs': {'dev/index.html': b'stale bytes of a retained version'}, 'retained-hidden-file-missing': {'dev/.buildinfo': None},
  }
  pages = FakePages(changed(archive, edits.get(change, {})))
  if change == 'late':
    pages.misses = 2
  commit = '' if change == 'check' else HEAD
  if message is not None:
    with pytest.raises(SystemExit, match=message):
      readback(tmp_path, monkeypatch, git, pages, label, commit)
    assert not (tmp_path / 'outputs').exists()
    return
  result = readback(tmp_path, monkeypatch, git, pages, label, commit)
  entry = next(entry for entry in read_manifest(site['versions.json']) if entry.label == label)
  # The digest is recomputed from live bytes and must equal what the assembler recorded.
  assert result == {'commit': HEAD, 'digest': entry.digest or ''}
  # Every archived file is read back, whichever version is being checked.
  assert set(pages.requests) == set(site)


class Platform:
  '''One synthetic repository and Pages site driven through the real inline steps of every job.'''

  def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    self.tmp_path, self.monkeypatch = tmp_path, monkeypatch
    self.git = FakeGit({}, None)
    self.api = FakeApi(self.git)
    self.pages = FakePages({})
    self.runs = 0

  def job(self, name: str) -> Path:
    self.runs += 1
    path = self.tmp_path / f'{self.runs:02d}-{name}'
    path.mkdir()
    self.monkeypatch.chdir(path)
    return path

  def check(self, label: str) -> dict[str, str]:
    return readback(self.job('check'), self.monkeypatch, self.git, self.pages, label, '')

  def archive(self, mode: str, label: str, *, build: dict[str, bytes] | None = None, checked: Mapping[str, str] | None = None, initialize: bool | None = None) -> str:
    path = self.job('archive')
    output = environment(self.monkeypatch, path, INITIALIZE='true' if (self.git.head is None if initialize is None else initialize) else 'false',
      EXPECTED=(checked or {}).get('commit', ''), MODE=mode, LABEL=label, COMMIT=json.loads(build['build.json'])['commit'] if build else '',
      DIGEST=(checked or {}).get('digest', ''), CONTROL=CONTROL, GH_TOKEN='offline-fixture')
    (path / 'control').mkdir()
    shutil.copy(run_docs_site.__file__, path / 'control/run_docs_site.py')
    if build is not None:
      (path / 'candidate').mkdir()
      (path / 'candidate/site.tar').write_bytes(tar_bytes(build))
    self.monkeypatch.setattr(subprocess, 'run', self.git.run)
    self.monkeypatch.setattr(subprocess, 'check_output', self.git.check_output)
    self.monkeypatch.setattr(urllib.request, 'urlopen', self.api)
    run_policy(code('archive', 'Read the archive branch'))
    self.monkeypatch.setenv('PARENT', outputs(output)['parent'])
    run_policy(code('archive', 'Apply the requested archive change'))
    run_policy(code('archive', COMMIT_STEP))
    self.artifact = run_docs_site.read_directory(path / 'site')
    return outputs(output)['commit']

  def deploy(self, commit: str) -> None:
    self.job('deploy')
    self.monkeypatch.setenv('COMMIT', commit)
    self.monkeypatch.setattr(subprocess, 'check_output', self.git.check_output)
    run_policy(code('deploy', 'Refuse to deploy a superseded archive'))
    self.pages.files = dict(self.artifact)

  def readback(self, label: str, commit: str) -> dict[str, str]:
    return readback(self.job('readback'), self.monkeypatch, self.git, self.pages, label, commit)

  def manifest(self) -> dict[str, Any]:
    assert self.git.head is not None
    value: dict[str, Any] = json.loads(self.git.commits[self.git.head]['versions.json'])
    return value


def test_state_chain_through_the_workflow_steps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]) -> None:
  platform = Platform(tmp_path, monkeypatch)
  v1, v2 = candidate('v99.0.0', TAGGED), candidate('v99.1.0', 'c' * 40)

  # Declare v99.1.0 pending first; the selector anchor exists before any directory does.
  commit = platform.archive('pending', 'v99.1.0')
  platform.deploy(commit)
  assert platform.readback('v99.1.0', commit) == {'commit': commit, 'digest': ''}
  assert '<li id="v99.1.0">v99.1.0：文档待就绪</li>' in platform.pages.files['versions/index.html'].decode()

  # Archive and deploy v99.0.0: live and read back, still not ready and not latest.
  commit = platform.archive('publish', 'v99.0.0', build=v1)
  platform.deploy(commit)
  platform.readback('v99.0.0', commit)
  assert platform.manifest()['latest'] is None
  assert [(entry['label'], entry['state']) for entry in platform.manifest()['versions']] == [('v99.1.0', 'pending'), ('v99.0.0', 'archived')]
  with pytest.raises(subprocess.CalledProcessError):
    platform.archive('promote', 'v99.1.0', checked=platform.check('v99.1.0'))
  assert 'v99.1.0 has no archived directory to mark ready' in capfd.readouterr().err

  # Promotion needs a fresh live check; afterwards v99.0.0 is ready and latest.
  commit = platform.archive('promote', 'v99.0.0', checked=platform.check('v99.0.0'))
  platform.deploy(commit)
  platform.readback('v99.0.0', commit)
  assert platform.manifest()['latest'] == 'v99.0.0'

  # v99.1.0 is archived but its deployment fails: the live check cannot pass, so nothing is promoted.
  archived = platform.archive('publish', 'v99.1.0', build=v2)
  with pytest.raises(SystemExit, match='still differs'):
    platform.check('v99.1.0')
  assert platform.git.head == archived and platform.manifest()['latest'] == 'v99.0.0'

  # Retrying the same build changes nothing; a different build for the same tag is refused.
  assert platform.archive('publish', 'v99.1.0', build=v2) == archived
  with pytest.raises(subprocess.CalledProcessError):
    platform.archive('publish', 'v99.1.0', build=candidate('v99.1.0', 'c' * 40, b'rebuilt'))
  assert 'published versions are never replaced' in capfd.readouterr().err
  assert platform.git.head == archived

  # Resume redeploys the archive as it is; then promotion succeeds and latest moves.
  commit = platform.archive('resume', 'v99.1.0')
  assert commit == archived
  platform.deploy(commit)
  platform.readback('v99.1.0', commit)
  checked = platform.check('v99.1.0')

  # A concurrent dev publication moves the branch between the live check and promotion.
  moved = platform.archive('publish', 'dev', build=candidate('dev', SHA))
  with pytest.raises(SystemExit, match='moved after the live check'):
    platform.archive('promote', 'v99.1.0', checked=checked)
  # The older run must not redeploy its superseded archive either.
  with pytest.raises(SystemExit, match='docs-site moved'):
    platform.deploy(archived)
  platform.deploy(moved)
  commit = platform.archive('promote', 'v99.1.0', checked=platform.check('v99.1.0'))
  platform.deploy(commit)
  platform.readback('v99.1.0', commit)
  assert platform.manifest()['latest'] == 'v99.1.0'
  assert [(entry['label'], entry['state']) for entry in platform.manifest()['versions']] == [('dev', 'archived'), ('v99.1.0', 'ready'), ('v99.0.0', 'ready')]
  # Every release directory is still byte-identical to its first build, and no staging branch is left.
  live = platform.pages.files
  assert {name.partition('/')[2]: content for name, content in live.items() if name.startswith('v99.0.0/')} == v1
  assert {name.partition('/')[2]: content for name, content in live.items() if name.startswith('v99.1.0/')} == v2
  assert platform.api.branches == {}


@pytest.mark.parametrize('failure', ['control-unsigned', 'staging-moved', 'graphql-unavailable', 'unsigned', 'graphql-response-lost', 'create-response-lost', 'created-meanwhile'])
def test_interrupted_init_can_be_retried(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
  platform = Platform(tmp_path, monkeypatch)
  build = candidate('dev', SHA)
  if failure == 'control-unsigned':
    platform.api.control_signature = None
  elif failure == 'staging-moved':
    platform.api.staging_moved = MOVED
  elif failure == 'unsigned':
    platform.api.signature = None
  elif failure == 'created-meanwhile':
    platform.git.commits[MOVED] = {'index.html': b'another writer'}
    platform.api.moved = MOVED
  else:
    platform.api.fail = {failure}
  with pytest.raises((SystemExit, urllib.error.HTTPError)):
    platform.archive('publish', 'dev', build=build)
  # No staging branch is left; docs-site is absent, the concurrent writer's, or a first archive that passed every check.
  assert platform.api.branches == {}
  # The retry finds GitHub vouching for the control commit, as a dispatch from a signed main commit would.
  platform.api.signature, platform.api.control_signature, platform.api.moved, platform.api.staging_moved, platform.api.fail = SIGNED, {'isValid': True}, None, None, set()
  if failure == 'created-meanwhile':
    assert platform.git.head == MOVED
    return
  if failure == 'create-response-lost':
    commit = platform.git.head
    assert commit is not None and run_docs_site.load_archive(platform.git.commits[commit])['dev'][1] == build
    with pytest.raises(SystemExit, match='initialize must be true exactly'):
      platform.archive('publish', 'dev', build=build, initialize=True)
    # Dispatching again without initialize finds the build archived and writes nothing.
    calls = len(platform.api.calls)
    assert platform.archive('publish', 'dev', build=build) == commit and len(platform.api.calls) == calls
  else:
    assert platform.git.head is None
    commit = platform.archive('publish', 'dev', build=build)
  platform.deploy(commit)
  assert platform.readback('dev', commit) == {'commit': commit, 'digest': run_docs_site.digest(build)}
  assert platform.api.branches == {}
