# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''登记源码中的 API 示例，核对页面代码后在独立进程执行。'''

import ast
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from markdown_it import MarkdownIt

from house_docstrings import source_attribute_docs


'''每个具名对象恰有一个完整代码块；删除、增加或改变围栏语言均须更新并验证登记。'''
EXAMPLE_OWNERS: Final[frozenset[str]] = frozenset({
  'bazi.utils.dizhi_utils.DizhiRelationDiscovery',
  'bazi.bazi_chart.BaziChart.relationship_stars',
  'bazi.bazi_chart.BaziChart.traits',
  'bazi.bazi_chart.BaziChart.hidden_tiangan',
  'bazi.bazi_chart.BaziChart.shishen',
  'bazi.bazi_chart.BaziChart.nayin',
  'bazi.bazi_chart.BaziChart.shier_zhangsheng',
  'bazi.bazi_chart.BaziChart.dayun',
  'bazi.bazi_chart.BaziChart.xiaoyun',
  'bazi.bazi_chart.BaziChart.liunian',
  'bazi.calendar.hko_data_utils.prev_jie',
  'bazi.calendar.hko_data_utils.next_jie',
  'bazi.chart_text.TextStyle',
  'bazi.defines.wuxing.Wuxing.generates',
  'bazi.defines.wuxing.Wuxing.destructs',
  'bazi.rules',
  'bazi.utils.bazi_utils.shishen',
  'bazi.utils.bazi_utils.nayin_str',
  'bazi.utils.bazi_utils.shier_zhangsheng',
  'bazi.utils.bazi_utils.from_shier_zhangsheng',
  'bazi.utils.bazi_utils.lu',
  'bazi.utils.dizhi_utils.sanhui',
  'bazi.utils.dizhi_utils.liuhe',
  'bazi.utils.dizhi_utils.anhe',
  'bazi.utils.dizhi_utils.tonghe',
  'bazi.utils.dizhi_utils.tongluhe',
  'bazi.utils.dizhi_utils.sanhe',
  'bazi.utils.dizhi_utils.banhe',
  'bazi.utils.dizhi_utils.gonghe',
  'bazi.utils.dizhi_utils.gonghui',
  'bazi.utils.dizhi_utils.xing',
  'bazi.utils.dizhi_utils.chong',
  'bazi.utils.dizhi_utils.po',
  'bazi.utils.dizhi_utils.hai',
  'bazi.utils.dizhi_utils.sheng',
  'bazi.utils.dizhi_utils.ke',
  'bazi.utils.dizhi_utils.search',
  'bazi.utils.dizhi_utils.discover_mutual',
  'bazi.utils.shensha_utils.taohua',
  'bazi.utils.shensha_utils.hongyan',
  'bazi.utils.shensha_utils.hongluan',
  'bazi.utils.shensha_utils.tianxi',
  'bazi.utils.shensha_utils.yima',
  'bazi.utils.shensha_utils.huagai',
  'bazi.utils.shensha_utils.jiangxing',
  'bazi.utils.shensha_utils.zaisha',
  'bazi.utils.shensha_utils.jiesha',
  'bazi.utils.shensha_utils.wangshen',
  'bazi.utils.shensha_utils.guchen',
  'bazi.utils.shensha_utils.guasu',
  'bazi.utils.shensha_utils.lushen',
  'bazi.utils.shensha_utils.jinyu',
  'bazi.utils.shensha_utils.kuigang',
  'bazi.utils.shensha_utils.tianshe',
  'bazi.utils.shensha_utils.yangren',
  'bazi.utils.shensha_utils.feiren',
  'bazi.utils.shensha_utils.tianyi',
  'bazi.utils.shensha_utils.wenchang',
  'bazi.utils.shensha_utils.wenchanggui',
  'bazi.utils.shensha_utils.taiji',
  'bazi.utils.shensha_utils.guoyin',
  'bazi.utils.tiangan_utils.he',
  'bazi.utils.tiangan_utils.chong',
  'bazi.utils.tiangan_utils.sheng',
  'bazi.utils.tiangan_utils.ke',
  'bazi.utils.tiangan_utils.search',
  'bazi.utils.tiangan_utils.discover_mutual',
})

'''出生精度的 Examples 是三个粒度的文字对照，不是待执行程序。'''
PROSE_EXAMPLES: Final[frozenset[str]] = frozenset({'bazi.school.BaziPrecision'})

'''缩进原文块按引文核对，不能当作 Python 执行或从页面对账中滤掉。'''
QUOTED_BLOCKS: Final[dict[str, tuple[str, str]]] = {
  'bazi.rules.ShenshaRules.TaijiDef': ('bazi.rules', '壬巳癸申一作壬癸巳申偏喜美，封侯万户即三公\n'),
}


@dataclass(frozen=True)
class ApiExample:
  module: str
  owner: str
  code: str
  output: str | None


def collect_examples(package: Path) -> tuple[ApiExample, ...]:
  '''扫描全部源码说明；登记决定期望，不决定扫描范围。'''
  documents: dict[str, tuple[str, str]] = {}

  def walk(node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef, name: str, module: str) -> None:
    documents[name] = module, ast.get_docstring(node) or ''
    for child in node.body:
      if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        walk(child, name + '.' + child.name, module)

  modules = []
  for path in sorted(package.rglob('*.py')):
    module = '.'.join(path.relative_to(package.parent).with_suffix('').parts).removesuffix('.__init__')
    modules.append(module)
    walk(ast.parse(path.read_text(encoding='utf-8')), module, module)
  for name, lines in source_attribute_docs(package).items():
    module = max((module for module in modules if name.startswith(module + '.')), key=len)
    documents[name] = module, '\n'.join(lines)

  parser = MarkdownIt('commonmark')
  examples = []
  found: set[str] = set()
  prose: set[str] = set()
  quoted: set[str] = set()
  for name, (module, text) in documents.items():
    fences = [token for token in parser.parse(text) if token.type in ('fence', 'code_block')]
    has_heading = re.search(r'^(?:Examples|Usage)[:：]', text, re.MULTILINE) is not None
    if not fences and not has_heading:
      continue
    if name in QUOTED_BLOCKS:
      assert len(fences) == 1 and fences[0].type == 'code_block', ('Quoted block shape', name)
      assert (module, fences[0].content) == QUOTED_BLOCKS[name], ('Quoted block content', name)
      quoted.add(name)
      continue
    if name in PROSE_EXAMPLES:
      assert has_heading and not fences, ('Prose example gained code', name)
      prose.add(name)
      continue
    assert name in EXAMPLE_OWNERS, ('Unregistered API example', name)
    assert [token.info for token in fences] in (['python'], ['python', 'text']), ('API example fences', name)
    code = fences[0].content
    output = fences[1].content if len(fences) == 2 else None
    tree = ast.parse(code, filename=name)
    assert output is not None or any(isinstance(node, ast.Assert) for node in ast.walk(tree)), ('Missing expected result', name)
    found.add(name)
    examples.append(ApiExample(module, name, code, output))
  assert found == EXAMPLE_OWNERS, ('API example coverage', sorted(EXAMPLE_OWNERS - found))
  assert prose == PROSE_EXAMPLES, ('Prose example coverage', sorted(PROSE_EXAMPLES - prose))
  assert quoted == QUOTED_BLOCKS.keys(), ('Quoted block coverage', sorted(QUOTED_BLOCKS.keys() - quoted))
  return tuple(examples)


def check_example_blocks(examples: tuple[ApiExample, ...], pages: Mapping[str, Sequence[str]]) -> None:
  '''实际 HTML 必须显示受测代码与输出；多出的普通围栏也不能漏验。'''
  expected: dict[str, Counter[str]] = defaultdict(Counter)
  for example in examples:
    page = 'api/' + example.module.replace('.', '-') + '.html'
    expected[page][example.code] += 1
    if example.output is not None:
      expected[page][example.output] += 1
  for module, text in QUOTED_BLOCKS.values():
    expected['api/' + module.replace('.', '-') + '.html'][text] += 1
  assert expected.keys() <= pages.keys(), ('Missing API example pages', expected.keys() - pages.keys())
  for filename, blocks in pages.items():
    if filename.startswith('api/'):
      actual = Counter(blocks)
      wanted = expected.get(filename, Counter())
      assert actual == wanted, ('Rendered API examples', filename, 'extra', actual - wanted, 'missing', wanted - actual)


def run_example(example: ApiExample, root: Path, timeout: float = 30) -> None:
  '''每例独立工作目录与进程，不借用上一例的变量或导入。'''
  with tempfile.TemporaryDirectory(prefix='bazi-api-example-') as directory:
    try:
      result = subprocess.run(
        [sys.executable, '-B', '-c', example.code],
        cwd=directory, env=os.environ | {'PYTHONPATH': str(root), 'PYTHONIOENCODING': 'utf-8'},
        capture_output=True, text=True, encoding='utf-8', timeout=timeout, check=False,
      )
    except subprocess.TimeoutExpired as error:
      raise RuntimeError('API example timed out: ' + example.owner) from error
    assert result.returncode == 0, (example.owner, result.stdout, result.stderr)
    assert result.stdout == (example.output or ''), ('API example output', example.owner, result.stdout, example.output)
    assert not result.stderr, ('API example stderr', example.owner, result.stderr)
