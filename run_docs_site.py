'''维护版本站点归档：只读 tar，按一次状态变更核对后在新目录写出完整站点，不访问网络或 Git。'''

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import tarfile
import tempfile

from pathlib import Path, PurePosixPath
from typing import Any, Final, Literal, NamedTuple, get_args
from collections.abc import Mapping, Sequence


# 开发版固定在 dev/，每次归档整目录替换；发布版按 tag 名建目录，写入后只接受字节完全相同的重复归档。
DEV_LABEL: Final[str] = 'dev'
RELEASE_LABEL: Final[re.Pattern[str]] = re.compile(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)')
COMMIT: Final[re.Pattern[str]] = re.compile(r'[0-9a-f]{40}')
DIGEST: Final[re.Pattern[str]] = re.compile(r'[0-9a-f]{64}')
SOURCE_URL: Final[str] = 'https://github.com/0xf3cd/bazi/tree/'
SCHEMA_VERSION: Final[int] = 1
# 归档根目录只有版本目录和下列由本脚本从版本记录生成的文件；归档里的这三份须与重新生成的字节一致。
GENERATED: Final[frozenset[str]] = frozenset({'index.html', 'versions.json', 'versions/index.html'})
# 与 run_docs.py 写出的 build.json 字段一致；字段增减须同步此处，否则组装拒绝。
BUILD_FIELDS: Final[frozenset[str]] = frozenset({'version', 'commit', 'dirty', 'python'})

State = Literal['pending', 'archived', 'ready']
'''版本条目状态：pending 只登记待就绪、没有目录；archived 目录已归档、尚未回读；ready 已回读，选择页才给出链接。'''
STATES: Final[tuple[State, ...]] = get_args(State)


class Version(NamedTuple):
  '''versions.json 的一条记录：目录名、状态、源码提交与目录内容摘要；pending 条目没有后两项。'''
  label: str
  state: State
  commit: str | None
  digest: str | None


Archive = dict[str, tuple[Version, dict[str, bytes]]]
'''按目录名索引的版本记录与该版本目录内的文件；pending 版本的文件表为空。'''


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  '''JSON 对象不得有重复键，避免不同解析器各取一个值。'''
  result = dict(pairs)
  if len(result) != len(pairs):
    raise ValueError('Duplicate JSON key')
  return result


def load_json(content: bytes) -> object:
  value: object = json.loads(content.decode('utf-8'), object_pairs_hook=strict_object)
  return value


def check_release(label: str) -> None:
  if RELEASE_LABEL.fullmatch(label) is None:
    raise ValueError(f'Expected vMAJOR.MINOR.PATCH, got {label!r}')


def check_identity(label: str, commit: str) -> None:
  if label != DEV_LABEL and RELEASE_LABEL.fullmatch(label) is None:
    raise ValueError(f'Expected dev or vMAJOR.MINOR.PATCH, got {label!r}')
  if COMMIT.fullmatch(commit) is None:
    raise ValueError(f'Expected a 40-hex commit, got {commit!r}')


def label_key(label: str) -> tuple[int, ...]:
  '''排序键：开发版在前，发布版按版本号从新到旧。'''
  if label == DEV_LABEL:
    return ()
  return tuple(-int(part) for part in label[1:].split('.'))


def latest_release(entries: Sequence[Version]) -> str | None:
  '''最新发布：已回读（ready）发布版中版本号最大的一个；未回读的归档不参与。'''
  return min((entry.label for entry in entries if entry.state == 'ready' and entry.label != DEV_LABEL), key=label_key, default=None)


def digest(files: Mapping[str, bytes]) -> str:
  '''目录摘要：逐文件 sha256 清单的 sha256，清单格式同 release.yml 的 SHA256SUMS。'''
  listing = ''.join(f'{hashlib.sha256(files[name]).hexdigest()}  {name}\n' for name in sorted(files))
  return hashlib.sha256(listing.encode('utf-8')).hexdigest()


def check_name(name: str) -> str:
  '''返回规范化的相对路径；绝对路径、..、反斜杠、控制字符与 .git 开头的名字一律拒绝。

  Note:
    .gitattributes 等文件会改变 git archive 导出的字节，归档内不允许出现。
  '''
  path = PurePosixPath(name)
  if (path.is_absolute() or '\\' in name or any(ord(c) < 0x20 or ord(c) == 0x7f for c in name)
      or any(part == '..' or part.lower().startswith('.git') for part in path.parts)):
    raise ValueError(f'Unsafe archive path: {name!r}')
  return path.as_posix()


def read_tree(path: Path) -> dict[str, bytes]:
  '''读取未压缩 tar 中的普通文件；链接、设备、重复路径及文件与目录同名一律拒绝。'''
  files: dict[str, bytes] = {}
  with tarfile.open(path, mode='r:') as archive:
    for member in archive:
      name = check_name(member.name)
      if member.isdir():
        continue
      if not member.isreg():
        raise ValueError(f'Only regular files may be archived: {member.name!r}')
      if name == '.' or name in files:
        raise ValueError(f'Duplicate or empty archive path: {member.name!r}')
      stream = archive.extractfile(member)
      assert stream is not None
      files[name] = stream.read()
  for name in files:
    for parent in PurePosixPath(name).parents:
      if parent.as_posix() in files:
        raise ValueError(f'Archive path is both a file and a directory: {parent}')
  return files


def check_build(files: Mapping[str, bytes], label: str, commit: str) -> None:
  '''build.json 须声明同一版本、同一提交，且构建时工作树干净。'''
  if 'build.json' not in files or 'index.html' not in files:
    raise ValueError(f'{label}: build.json or index.html is missing')
  data = load_json(files['build.json'])
  if not isinstance(data, dict) or set(data) != BUILD_FIELDS:
    raise ValueError(f'{label}: build.json fields differ from {sorted(BUILD_FIELDS)}')
  if data['version'] != label or data['commit'] != commit or data['dirty'] is not False or not isinstance(data['python'], str):
    raise ValueError(f'{label}: build.json does not describe a clean build of {commit}')


def check_entry(item: object) -> Version:
  '''pending 只登记发布版，不带提交与摘要；archived 与 ready 须有 40 位提交和 64 位摘要。'''
  if (not isinstance(item, dict) or set(item) != set(Version._fields)
      or not isinstance(item['label'], str) or item['state'] not in STATES):
    raise ValueError(f'Invalid versions.json entry: {item!r}')
  entry = Version(**item)
  if entry.state == 'pending':
    check_release(entry.label)
    if entry.commit is not None or entry.digest is not None:
      raise ValueError(f'Pending {entry.label} must not record a commit or digest')
    return entry
  if not isinstance(entry.commit, str) or not isinstance(entry.digest, str) or DIGEST.fullmatch(entry.digest) is None:
    raise ValueError(f'Invalid commit or digest for {entry.label}')
  check_identity(entry.label, entry.commit)
  return entry


def read_manifest(content: bytes) -> list[Version]:
  data = load_json(content)
  if (not isinstance(data, dict) or set(data) != {'schema', 'latest', 'versions'} or type(data['schema']) is not int
      or data['schema'] != SCHEMA_VERSION or not isinstance(data['versions'], list)):
    raise ValueError('Unsupported versions.json')
  entries = [check_entry(item) for item in data['versions']]
  if len({entry.label for entry in entries}) != len(entries):
    raise ValueError('Duplicate label in versions.json')
  return entries


def render_manifest(entries: Sequence[Version]) -> bytes:
  data = {'schema': SCHEMA_VERSION, 'latest': latest_release(entries), 'versions': [entry._asdict() for entry in entries]}
  return (json.dumps(data, indent=2) + '\n').encode('utf-8')


def render_selector(entries: Sequence[Version]) -> bytes:
  '''版本选择页 versions/index.html：每个登记版本一行，锚点为目录名；只有 ready 版本给出链接。'''
  latest = latest_release(entries)
  rows = []
  for entry in entries:
    label = html.escape(entry.label)
    name = '开发版' if entry.label == DEV_LABEL else label
    if entry.state != 'ready' or entry.commit is None:
      rows.append(f'<li id="{label}">{name}：文档待就绪</li>\n')
      continue
    note = '（跟随 main 手动更新）' if entry.label == DEV_LABEL else '（最新发布）' if entry.label == latest else ''
    commit = html.escape(entry.commit)
    rows.append(
      f'<li id="{label}"><a href="../{label}/index.html">{name}</a>{note}'
      f' · 源码 <a href="{SOURCE_URL}{commit}"><code>{commit[:12]}</code></a></li>\n'
    )
  page = (
    '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>bazi 文档版本</title>\n'
    '</head>\n<body>\n<h1>bazi 文档版本</h1>\n'
    '<p>发布版文档按 tag 归档，归档后内容不再改变。</p>\n'
    '<p>“文档待就绪”表示该版文档还没有上线并通过核对，不表示该版软件没有发布。</p>\n'
    f'<ul>\n{"".join(rows)}</ul>\n<p><a href="../versions.json">versions.json</a></p>\n</body>\n</html>\n'
  )
  return page.encode('utf-8')


ROOT_PAGE: Final[bytes] = (
  '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
  '<meta http-equiv="refresh" content="0; url=versions/">\n<title>bazi 文档</title>\n'
  '</head>\n<body>\n<p><a href="versions/">bazi 文档版本</a></p>\n</body>\n</html>\n'
).encode()


def render_root(entries: Sequence[Version]) -> dict[str, bytes]:
  return {'index.html': ROOT_PAGE, 'versions.json': render_manifest(entries), 'versions/index.html': render_selector(entries)}


def load_archive(tree: Mapping[str, bytes]) -> Archive:
  '''拆分现有归档，逐版本核对 versions.json、目录摘要与 build.json，生成文件须与重新生成的一致；有任何不一致都拒绝。'''
  directories: dict[str, dict[str, bytes]] = {}
  for name, content in tree.items():
    if name in GENERATED:
      continue
    head, _, rest = name.partition('/')
    if not rest:
      raise ValueError(f'Unexpected archive root file: {name}')
    directories.setdefault(head, {})[rest] = content
  if 'versions.json' not in tree:
    raise ValueError('Archive has no versions.json')
  entries = read_manifest(tree['versions.json'])
  if set(directories) != {entry.label for entry in entries if entry.state != 'pending'}:
    raise ValueError(f'Archive directories {sorted(directories)} differ from the archived versions in versions.json')
  for entry in entries:
    if entry.commit is None:
      continue
    files = directories[entry.label]
    check_build(files, entry.label, entry.commit)
    if digest(files) != entry.digest:
      raise ValueError(f'Archived {entry.label} differs from its recorded digest')
  ordered = sorted(entries, key=lambda entry: label_key(entry.label))
  if {name: tree.get(name) for name in GENERATED} != render_root(ordered):
    raise ValueError('Generated root files differ from those rendered from versions.json')
  return {entry.label: (entry, directories.get(entry.label, {})) for entry in entries}


def open_archive(tree: Mapping[str, bytes] | None) -> Archive:
  return {} if tree is None else load_archive(tree)


def render_site(versions: Archive) -> dict[str, bytes]:
  ordered = sorted(versions.values(), key=lambda item: label_key(item[0].label))
  site = {f'{entry.label}/{name}': content for entry, files in ordered for name, content in files.items()}
  return site | render_root([entry for entry, _ in ordered])


def add_build(tree: Mapping[str, bytes] | None, candidate: Mapping[str, bytes], label: str, commit: str) -> tuple[str, dict[str, bytes]]:
  '''登记一次已检查的构建，状态为 archived；返回 (added | replaced | unchanged, 完整站点)。

  Note:
    未登记或 pending 的版本新增目录。已归档的发布版只接受字节完全相同的重复归档，状态保持不变；
    dev 内容不同时整目录替换，状态回到 archived，等新的回读结果。
  '''
  check_identity(label, commit)
  check_build(candidate, label, commit)
  versions = open_archive(tree)
  new = Version(label, 'archived', commit, digest(candidate))
  old = versions[label][0] if label in versions else None
  if old is None or old.state == 'pending':
    status = 'added'
  elif (old.commit, old.digest) == (new.commit, new.digest):
    return 'unchanged', render_site(versions)
  elif label == DEV_LABEL:
    status = 'replaced'
  else:
    raise ValueError(f'{label} is already archived with different content; published versions are never replaced')
  versions[label] = (new, dict(candidate))
  return status, render_site(versions)


def add_pending(tree: Mapping[str, bytes] | None, label: str) -> tuple[str, dict[str, bytes]]:
  '''登记一个文档待就绪的发布版：只进版本清单与选择页，不建目录；已归档的版本不能退回 pending。'''
  check_release(label)
  versions = open_archive(tree)
  if label not in versions:
    versions[label] = (Version(label, 'pending', None, None), {})
    return 'added', render_site(versions)
  if versions[label][0].state != 'pending':
    raise ValueError(f'{label} is already archived; it cannot become pending again')
  return 'unchanged', render_site(versions)


def mark_ready(tree: Mapping[str, bytes] | None, label: str, verified_digest: str) -> tuple[str, dict[str, bytes]]:
  '''回读核对线上字节之后，把 archived 版本标为 ready；最新发布随之重新取值。

  Note:
    verified_digest 由无写权限的回读 job 从线上字节算出，须等于归档记录的摘要；本函数不访问网络。
  '''
  versions = open_archive(tree)
  if label not in versions or versions[label][0].state == 'pending':
    raise ValueError(f'{label} has no archived directory to mark ready')
  entry, files = versions[label]
  if verified_digest != entry.digest:
    raise ValueError(f'Read-back digest of {label} differs from its archived digest')
  if entry.state == 'ready':
    return 'unchanged', render_site(versions)
  versions[label] = (entry._replace(state='ready'), files)
  return 'promoted', render_site(versions)


def keep_current(tree: Mapping[str, bytes] | None, label: str) -> tuple[str, dict[str, bytes]]:
  '''不改归档，只核对后重新写出现有站点，供部署或回读失败后重新部署。'''
  versions = open_archive(tree)
  if label not in versions:
    raise ValueError(f'{label} is not in the archive')
  return 'unchanged', render_site(versions)


def read_directory(root: Path) -> dict[str, bytes]:
  files: dict[str, bytes] = {}
  for directory, names, filenames in os.walk(root):
    for name in [*names, *filenames]:
      if (Path(directory) / name).is_symlink():
        raise ValueError(f'Unexpected symlink in written site: {name}')
    for name in filenames:
      path = Path(directory) / name
      files[path.relative_to(root).as_posix()] = path.read_bytes()
  return files


def write_site(site: Mapping[str, bytes], output: Path) -> None:
  '''先在同级临时目录写完并回读核对，再改名为 output；任何失败都不留下 output。'''
  if output.exists() or output.is_symlink():
    raise ValueError(f'Output must not exist: {output}')
  staging = Path(tempfile.mkdtemp(prefix='.site-', dir=output.parent))
  try:
    for name, content in site.items():
      path = staging / name
      path.parent.mkdir(parents=True, exist_ok=True)
      with path.open('xb') as stream:
        stream.write(content)
    if read_directory(staging) != dict(site):
      raise ValueError('Written site differs from the assembled site')
    staging.rename(output)
  except BaseException:
    shutil.rmtree(staging, ignore_errors=True)
    raise


def main() -> None:
  common = argparse.ArgumentParser(add_help=False)
  source = common.add_mutually_exclusive_group(required=True)
  source.add_argument('--archive', type=Path, help='现有归档分支的 git archive --format=tar 输出。')
  source.add_argument('--initialize', action='store_true', help='归档分支尚不存在，从空归档开始。')
  common.add_argument('--label', required=True, help='dev 或 vMAJOR.MINOR.PATCH。')
  common.add_argument('--output', type=Path, required=True, help='尚不存在的目录，写入完整新站点。')
  parser = argparse.ArgumentParser(description=__doc__)
  operations = parser.add_subparsers(dest='operation', required=True)
  build = operations.add_parser('archive', parents=[common], help='登记一次已检查的构建，状态为 archived。')
  build.add_argument('--candidate', type=Path, required=True, help='本次构建 HTML 目录的 tar，根目录含 build.json。')
  build.add_argument('--commit', required=True, help='由调用方独立核定的 40 位源码提交。')
  operations.add_parser('pending', parents=[common], help='登记文档待就绪的发布版。')
  promote = operations.add_parser('promote', parents=[common], help='回读通过后把 archived 版本标为 ready。')
  promote.add_argument('--verified-digest', required=True, help='回读 job 从线上字节算出的目录摘要。')
  operations.add_parser('current', parents=[common], help='不改归档，重新写出现有站点。')
  args = parser.parse_args()
  tree = None if args.initialize else read_tree(args.archive)
  if args.operation == 'archive':
    status, site = add_build(tree, read_tree(args.candidate), args.label, args.commit)
  elif args.operation == 'pending':
    status, site = add_pending(tree, args.label)
  elif args.operation == 'promote':
    status, site = mark_ready(tree, args.label, args.verified_digest)
  else:
    status, site = keep_current(tree, args.label)
  write_site(site, args.output.resolve())
  manifest = load_json(site['versions.json'])
  assert isinstance(manifest, dict)
  current = next(entry for entry in read_manifest(site['versions.json']) if entry.label == args.label)
  print(json.dumps({'status': status, **current._asdict(), 'latest': manifest['latest'], 'versions': [entry['label'] for entry in manifest['versions']]}, indent=2))


if __name__ == '__main__':
  main()
