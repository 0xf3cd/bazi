'''发布工具：预检、封装、校验同次运行的工件，并执行已获授权的发布步骤。'''

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any, Final
from collections.abc import Callable


ENVIRONMENT_ROLES: Final[frozenset[str]] = frozenset({
  'outer', 'build-wheel-direct', 'build-sdist', 'build-wheel-rebuilt',
  'consumer-wheel-direct', 'consumer-wheel-rebuilt', 'consumer-typing',
})


def check_environment() -> None:
  '''要求正式发布来自本仓 main，且 release 环境已有审阅者和确切分支策略。'''
  if (os.environ['MODE'] != 'release' or os.environ['REPOSITORY'] != '0xf3cd/bazi'
      or os.environ['REF'] != 'refs/heads/main' or not re.fullmatch(r'[0-9a-f]{40}', os.environ['SHA'])):
    raise SystemExit('Real release requires the main dispatch SHA of 0xf3cd/bazi')
  def get(path: str) -> Any:
    request = urllib.request.Request('https://api.github.com/repos/0xf3cd/bazi/' + path,
      headers={'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=30) as response:
      return json.load(response)
  environment = get('environments/release')
  policies = get('environments/release/deployment-branch-policies?per_page=100')
  reviewers = [rule for rule in environment.get('protection_rules', [])
    if rule.get('type') == 'required_reviewers' and any(
      reviewer.get('type') in ('User', 'Team') and isinstance(reviewer.get('reviewer', {}).get('id'), int)
      and reviewer['reviewer']['id'] > 0 for reviewer in rule.get('reviewers', []))]
  if (environment.get('name') != 'release' or not reviewers
      or environment.get('deployment_branch_policy') != {'protected_branches': False, 'custom_branch_policies': True}
      or policies.get('total_count') != 1
      or [(p.get('name'), p.get('type')) for p in policies.get('branch_policies', [])] != [('main', 'branch')]):
    raise SystemExit('release must have required reviewers and exactly the main branch policy')


def verify_source() -> None:
  '''核对检出身份；正式发布只接受本仓 main，演练可使用其他 ref。'''
  mode, sha = os.environ['MODE'], os.environ['SHA']
  if mode not in ('rehearsal', 'release') or not re.fullmatch(r'[0-9a-f]{40}', sha):
    raise SystemExit('Invalid release mode or SHA')
  if mode == 'release' and (os.environ['REPOSITORY'], os.environ['REF']) != ('0xf3cd/bazi', 'refs/heads/main'):
    raise SystemExit('Real release is main-only')
  if subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() != sha:
    raise SystemExit('Checkout SHA differs from dispatch SHA')


def seal_bundle() -> None:
  '''将原受测工件、发布说明和白名单环境清单绑定到本次运行，并写入校验和。'''
  import tomllib

  version = tomllib.loads(Path('pyproject.toml').read_text())['project']['version']
  if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
    raise SystemExit('Use a stable three-part release version')
  bundle = Path(os.environ['RUNNER_TEMP']) / 'bundle'
  names = {f'bazi-{version}.tar.gz', f'bazi-{version}-py3-none-any.whl'}
  if {p.name for p in (bundle / 'dist').iterdir()} != names:
    raise SystemExit('Expected exactly the tested sdist and rebuilt wheel')
  if re.findall(r'^## (.*)$', Path('RELEASE_NOTES.md').read_text(encoding='utf-8'), re.MULTILINE)[:1] != [f'bazi {version}']:
    raise SystemExit(f'RELEASE_NOTES.md top section must be "## bazi {version}"')
  raw = Path(os.environ['RUNNER_TEMP']) / 'raw-environments.json'
  if not raw.is_file():
    raise SystemExit('Missing gate environment report')
  report = json.loads(raw.read_text(encoding='utf-8'))
  def keys(value: Any, expected: str) -> bool:
    return isinstance(value, dict) and set(value) == set(expected.split())
  if (not keys(report, 'schema_version source_sha pair environments')
      or type(report['schema_version']) is not int or report['schema_version'] != 1
      or report['source_sha'] != os.environ['SHA']):
    raise SystemExit('Gate environment schema or source mismatch')
  records = report['environments']
  if (not isinstance(records, list) or len(records) != len(ENVIRONMENT_ROLES)
      or any(not keys(record, 'role python platform distributions installers') for record in records)
      or any(not isinstance(record['role'], str) for record in records)
      or {record['role'] for record in records} != ENVIRONMENT_ROLES):
    raise SystemExit('Gate environment role roster mismatch')
  for record in records:
    if (not keys(record['python'], 'implementation version') or not keys(record['platform'], 'system machine')
        or any(not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', value)
          for value in (*record['python'].values(), *record['platform'].values()))
        or not isinstance(record['distributions'], dict)
        or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?', name)
          or not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.+!-]+', value)
          for name, value in record['distributions'].items())
        or not isinstance(record['installers'], list) or not record['installers']):
      raise SystemExit('Invalid gate environment fields')
    for installer in record['installers']:
      if (not keys(installer, 'name version scope') or installer['name'] != 'pip'
          or installer['scope'] not in ('runner', 'target') or not isinstance(installer['version'], str)
          or not re.fullmatch(r'[A-Za-z0-9_.+!-]+', installer['version'])):
        raise SystemExit('Invalid gate installer fields')
  pair = report['pair']
  if (not keys(pair, 'sdist wheel') or any(not keys(entry, 'filename sha256') for entry in pair.values())
      or pair != {kind: {'filename': name, 'sha256': hashlib.sha256((bundle / 'dist' / name).read_bytes()).hexdigest()}
        for kind, name in (('sdist', f'bazi-{version}.tar.gz'), ('wheel', f'bazi-{version}-py3-none-any.whl'))}):
    raise SystemExit('Gate environment pair differs from retained artifacts')
  shutil.copyfile('RELEASE_NOTES.md', bundle / 'RELEASE_NOTES.md')
  metadata = {'name': 'bazi', 'version': version, 'sha': os.environ['SHA'],
    'repository': os.environ['REPOSITORY'], 'run_id': os.environ['RUN_ID'], 'mode': os.environ['MODE']}
  (bundle / 'release.json').write_text(json.dumps(metadata, sort_keys=True) + '\n')
  (bundle / 'environments.json').write_text(json.dumps({**report, 'identity': metadata}, sort_keys=True) + '\n', encoding='utf-8')
  files = sorted([*(bundle / 'dist').iterdir(), bundle / 'RELEASE_NOTES.md', bundle / 'release.json', bundle / 'environments.json'], key=lambda p: p.relative_to(bundle).as_posix())
  checksums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(bundle).as_posix()}\n' for p in files)
  (bundle / 'SHA256SUMS').write_bytes(checksums.encode('utf-8'))
  with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
    output.write(f'version={version}\nmanifest-sha={hashlib.sha256(checksums.encode()).hexdigest()}\n')


def verify_bundle() -> None:
  '''在发布任务中核对确切文件集合、校验和及源码／运行／工件身份，不执行工件内容。'''
  version = os.environ['VERSION']
  if (os.environ['MODE'] != 'release' or os.environ['REPOSITORY'] != '0xf3cd/bazi'
      or os.environ['REF'] != 'refs/heads/main' or not re.fullmatch(r'[0-9a-f]{40}', os.environ['SHA'])
      or not re.fullmatch(r'[1-9][0-9]*', os.environ['ARTIFACT_ID'])
      or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version)):
    raise SystemExit('Invalid publication identity')
  root = Path('artifact')
  expected = {f'dist/bazi-{version}.tar.gz', f'dist/bazi-{version}-py3-none-any.whl', 'release.json', 'RELEASE_NOTES.md', 'environments.json'}
  if ({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} != expected | {'SHA256SUMS'}
      or any(p.is_symlink() for p in root.rglob('*'))):
    raise SystemExit('Unexpected release bundle files')
  checksums = (root / 'SHA256SUMS').read_bytes()
  if hashlib.sha256(checksums).hexdigest() != os.environ['MANIFEST_SHA']:
    raise SystemExit('Manifest differs from tested build')
  wanted = ''.join(f'{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n' for name in sorted(expected))
  if checksums.decode() != wanted:
    raise SystemExit('Release bundle checksum mismatch')
  metadata = json.loads((root / 'release.json').read_text())
  if metadata != {'name': 'bazi', 'version': version, 'sha': os.environ['SHA'], 'repository': '0xf3cd/bazi', 'run_id': os.environ['RUN_ID'], 'mode': 'release'}:
    raise SystemExit('Release metadata identity mismatch')
  report = json.loads((root / 'environments.json').read_text(encoding='utf-8'))
  if (not isinstance(report, dict) or set(report) != {'schema_version', 'source_sha', 'pair', 'environments', 'identity'}
      or type(report['schema_version']) is not int or report['schema_version'] != 1
      or report['identity'] != metadata or report['source_sha'] != os.environ['SHA']):
    raise SystemExit('Environment report identity mismatch')
  records = report['environments']
  if (not isinstance(records, list) or len(records) != len(ENVIRONMENT_ROLES)
      or any(not isinstance(record, dict) or not isinstance(record.get('role'), str) for record in records)
      or {record['role'] for record in records} != ENVIRONMENT_ROLES):
    raise SystemExit('Environment report role roster mismatch')
  if report['pair'] != {kind: {'filename': name, 'sha256': hashlib.sha256((root / 'dist' / name).read_bytes()).hexdigest()}
      for kind, name in (('sdist', f'bazi-{version}.tar.gz'), ('wheel', f'bazi-{version}-py3-none-any.whl'))}:
    raise SystemExit('Environment report pair mismatch')


def check_existing() -> None:
  '''拒绝已占用的版本、tag 或 Release；网络错误不当作不存在。'''
  version = os.environ['VERSION']
  urls = [f'https://pypi.org/pypi/bazi/{version}/json',
    f'https://api.github.com/repos/0xf3cd/bazi/git/ref/tags/v{version}',
    f'https://api.github.com/repos/0xf3cd/bazi/releases/tags/v{version}']
  for url in urls:
    try:
      with urllib.request.urlopen(url, timeout=30):
        pass
    except urllib.error.HTTPError as error:
      if error.code == 404:
        continue
      raise
    raise SystemExit('Version, tag or release already exists; deliberate recovery required')


def publish_github() -> None:
  '''核对 PyPI 原字节后创建 tag 和草稿，逐资产核摘要，最后发布；不覆盖已有对象。'''
  version, sha = os.environ['VERSION'], os.environ['SHA']
  with urllib.request.urlopen(f'https://pypi.org/pypi/bazi/{version}/json', timeout=30) as response:
    published = json.load(response)
  actual = {entry['filename']: entry['digests']['sha256'] for entry in published['urls']}
  expected = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('artifact/dist').iterdir()}
  if actual != expected:
    raise SystemExit('PyPI bytes differ from tested pair')
  base = 'https://api.github.com/repos/0xf3cd/bazi'
  headers = {'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
  for api_path in (f'/git/ref/tags/v{version}', f'/releases/tags/v{version}'):
    try:
      with urllib.request.urlopen(urllib.request.Request(base + api_path, headers=headers), timeout=30):
        pass
    except urllib.error.HTTPError as error:
      if error.code == 404:
        continue
      raise
    raise SystemExit('Existing tag/release; deliberate recovery required')
  body = re.split(r'^## .*$', Path('artifact/RELEASE_NOTES.md').read_text(encoding='utf-8'), flags=re.MULTILINE)[1].strip()
  def post(path: str, data: dict[str, object]) -> Any:
    request = urllib.request.Request(base + path, data=json.dumps(data).encode(), headers={**headers, 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=30) as response:
      return json.load(response)
  post('/git/refs', {'ref': f'refs/tags/v{version}', 'sha': sha})
  release = post('/releases', {'tag_name': f'v{version}', 'target_commitish': sha,
    'name': f'bazi {version}', 'body': body, 'draft': True})
  for path in sorted(p for p in Path('artifact').rglob('*') if p.is_file()):
    url = f'https://uploads.github.com/repos/0xf3cd/bazi/releases/{release["id"]}/assets?name={path.name}'
    request = urllib.request.Request(url, data=path.read_bytes(), headers={**headers, 'Content-Type': 'application/octet-stream'}, method='POST')
    with urllib.request.urlopen(request, timeout=60) as response:
      asset = json.load(response)
    if asset.get('digest') != 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest():
      raise SystemExit('Uploaded GitHub asset digest mismatch; release remains draft')
  request = urllib.request.Request(base + f'/releases/{release["id"]}', data=b'{"draft":false}', headers={**headers, 'Content-Type': 'application/json'}, method='PATCH')
  with urllib.request.urlopen(request, timeout=30):
    pass


def main() -> None:
  operations: dict[str, Callable[[], None]] = {
    'preflight': check_environment, 'source': verify_source, 'seal': seal_bundle,
    'verify': verify_bundle, 'check-existing': check_existing, 'publish': publish_github,
  }
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('operation', choices=operations, help='只执行对应 workflow 步骤；发布操作须另行取得授权。')
  operations[parser.parse_args().operation]()


if __name__ == '__main__':
  main()
