import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'docs' / '_ext'))

from api_reference import generate_api
from run_docs_site import RELEASE_LABEL


def generate_readme_example(source: Path) -> None:
  '''从 README 的首个 Python 围栏及紧随其后的输出生成执行检查。'''
  tokens = MarkdownIt('commonmark').parse((ROOT / 'README.md').read_text(encoding='utf-8'))
  index = next((index for index, token in enumerate(tokens) if token.type == 'fence' and token.info.strip() == 'python'), None)
  if index is None or index + 1 == len(tokens):
    raise ValueError('README needs a Python example followed by its text output')
  code, expected = tokens[index:index + 2]
  if expected.type != 'fence' or expected.info.strip() != 'text':
    raise ValueError('README Python example must be followed by a text output fence')
  lines = [':orphan:', '', 'README 首例检查', '===============', '', '.. testcode:: readme-first', '']
  lines.extend('   ' + line for line in code.content.splitlines())
  lines.extend(['', '.. testoutput:: readme-first', ''])
  lines.extend('   ' + line for line in expected.content.splitlines())
  (source / 'readme-example.rst').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def git_output(*args: str) -> str:
  return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True, encoding='utf-8').strip()


def build(output: Path, version_label: str) -> None:
  '''严格构建、执行示例并检查实际 HTML；只写构建产物，不部署站点。'''
  sha = git_output('rev-parse', 'HEAD')
  dirty = bool(git_output('status', '--porcelain'))
  if version_label != 'dev':
    if RELEASE_LABEL.fullmatch(version_label) is None:
      raise ValueError('Expected dev or a vMAJOR.MINOR.PATCH tag')
    if git_output('rev-parse', f'refs/tags/{version_label}^{{}}') != sha or dirty:
      raise ValueError('Versioned documentation requires a clean checkout of the matching tag')
  if output.is_relative_to(ROOT / 'docs'):
    raise ValueError('Documentation output must be outside its source directory')
  if output.exists() and (not output.is_dir() or any(output.iterdir())):
    raise ValueError('Documentation output directory must be empty')
  output.parent.mkdir(parents=True, exist_ok=True)
  environment = os.environ | {
    'PYTHONHASHSEED': '0', 'PYTHONDONTWRITEBYTECODE': '1',
    'BAZI_DOC_ROOT': str(ROOT), 'BAZI_DOC_REF': sha,
    'BAZI_DOC_VERSION': '开发版' if version_label == 'dev' else version_label,
  }
  with (
    tempfile.TemporaryDirectory(prefix='bazi-docs-') as temporary,
    tempfile.TemporaryDirectory(prefix='.bazi-docs-', dir=output.parent) as staging,
  ):
    candidate = Path(staging) / 'candidate'
    source = Path(temporary) / 'source'
    shutil.copytree(ROOT / 'docs', source)
    generate_api(source)
    generate_readme_example(source)
    contributing = (ROOT / 'CONTRIBUTING.md').read_text(encoding='utf-8')
    contributing = contributing.replace('](bazi/', f'](https://github.com/0xf3cd/bazi/blob/{sha}/bazi/')
    (source / 'contributing.md').write_text(contributing, encoding='utf-8')
    version_text = f'''# 文档版本

当前页面：{'开发版' if version_label == 'dev' else version_label}。

对应源码提交：[{sha[:12]}](https://github.com/0xf3cd/bazi/tree/{sha})。
{'本地包含未提交修改，不能作为版本归档。' if dirty else '构建时工作树干净。'}

开发版单列在 `dev/`，可整目录更新；发布版文档按对应 tag 的名称归档，已有发布版目录不覆盖。
构建成功不代表已上线；版本入口以部署站点保留的版本清单为准。

站点启用后，可从[全部版本](https://0xf3cd.github.io/bazi/versions/)切换。
构建、归档与核对步骤见 {{doc}}`versioning`。
'''
    (source / 'versions.md').write_text(version_text, encoding='utf-8')
    for builder in ('html', 'doctest'):
      command = [
        sys.executable, '-B', '-m', 'sphinx', '-E', '-b', builder, '-n', '-W', '--keep-going',
        '-d', str(Path(temporary) / ('doctrees-' + builder)), str(source), str(candidate / builder),
      ]
      subprocess.run(command, env=environment, check=True)
    subprocess.run([
      sys.executable, '-B', str(ROOT / 'run_doc_checks.py'), str(candidate / 'html'), str(candidate / 'doctest'),
    ], env=environment, check=True)
    metadata = {
      'version': version_label, 'commit': sha, 'dirty': dirty,
      'python': sys.version.split()[0],
    }
    (candidate / 'html' / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    if output.exists():
      output.rmdir()
    candidate.rename(output)


def main() -> None:
  parser = argparse.ArgumentParser(description='构建并检查文档，不执行部署。')
  parser.add_argument('--output-dir', type=Path, default=ROOT / 'output_data' / 'docs', help='空输出目录；检查成功后才写入成品。')
  parser.add_argument('--version', default='dev', help='dev 或当前干净检出的 vMAJOR.MINOR.PATCH tag。')
  args = parser.parse_args()
  build(args.output_dir.resolve(), args.version)


if __name__ == '__main__':
  main()
