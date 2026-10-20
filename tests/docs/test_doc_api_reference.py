# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''API 页生成与继承期望的分工：生成器解析失败要响，checker 不共用生成器的推导。'''

import sys
from pathlib import Path

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'docs/_ext'))
sys.path.insert(0, str(ROOT))

import api_reference
from api_contract import DECLARED_MEMBERS
from run_doc_checks import runtime_members


@pytest.mark.parametrize('base', ['LunarYearInfo', 'NoSuchBase'])
def test_ambiguous_or_missing_bases_fail(monkeypatch, base):
  monkeypatch.setitem(api_reference.BASES, 'bazi.common.frozendict', (base,))
  with pytest.raises(ValueError, match='exactly one contract base class'):
    api_reference.inherited_members('bazi.common.frozendict')


def test_external_bases_need_the_allowlist(monkeypatch):
  monkeypatch.setattr(api_reference, 'EXTERNAL_BASES', frozenset())
  with pytest.raises(ValueError, match='exactly one contract base class'):
    api_reference.inherited_members('bazi.bazi.BaziGender')


def test_oracle_ignores_typeddict_bases(monkeypatch):
  expected = runtime_members('bazi.bazi_chart.BaziJson.DefaultBaziChartJsonDict')
  monkeypatch.setitem(api_reference.BASES, 'bazi.bazi_chart.BaziJson.DefaultBaziChartJsonDict', ('TypedDict',))
  assert api_reference.inherited_members('bazi.bazi_chart.BaziJson.DefaultBaziChartJsonDict') != expected
  assert runtime_members('bazi.bazi_chart.BaziJson.DefaultBaziChartJsonDict') == expected


def test_oracle_ignores_mro_base_table(monkeypatch):
  expected = runtime_members('bazi.defines.dizhi.Dizhi')
  monkeypatch.setitem(api_reference.BASES, 'bazi.defines.dizhi.Dizhi', ('Enum',))
  assert api_reference.inherited_members('bazi.defines.dizhi.Dizhi') != expected
  assert runtime_members('bazi.defines.dizhi.Dizhi') == expected


def test_contract_classes_agree_on_inheritance():
  for cls in DECLARED_MEMBERS:
    assert api_reference.inherited_members(cls) == runtime_members(cls), cls


def option_lines(text: str, qualified: str) -> list[str]:
  lines = text.splitlines()
  start = lines.index('.. autoclass:: ' + qualified)
  block = []
  for line in lines[start + 1:]:
    if not line.strip():
      break
    block.append(line)
  return block


def test_empty_member_lists_not_all_members(tmp_path):
  api_reference.generate_api(tmp_path)
  for filename, qualified in (
    ('bazi-common.rst', 'bazi.common.frozendict'),
    ('bazi-data_types.rst', 'bazi.data_types.HiddenTianganDict'),
    ('bazi-transits.rst', 'bazi.transits.DayunDatabase'),
  ):
    text = (tmp_path / 'api' / filename).read_text(encoding='utf-8')
    assert option_lines(text, qualified) == [], qualified
  assert option_lines((tmp_path / 'api/bazi-data_types.rst').read_text(encoding='utf-8'), 'bazi.data_types.BaziData')


def test_alias_reexport_pages_own_wording(tmp_path):
  api_reference.generate_api(tmp_path)
  defines = (tmp_path / 'api/bazi-defines-tiangan.rst').read_text(encoding='utf-8')
  calendar = (tmp_path / 'api/bazi-calendar.rst').read_text(encoding='utf-8')
  assert '   :py:obj:`bazi.defines.tiangan.Tiangan` 的别名。' in defines
  assert '   :py:obj:`bazi.calendar.dates.CalendarType` 的重导出。' in calendar
  assert '的别名或重导出。' not in defines + calendar
