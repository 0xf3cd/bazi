# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import random
import re
from typing import cast

import pytest

from bazi import cli
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Zhu, Dizhi, Ganzhi
from bazi.analyzer.relationship import ShenshaAnalysis, AtBirthShenshaAnalysis, KongwangResult, KongwangHit
from bazi.analyzer.relationship import RelationshipAnalyzer, SHENSHA_LABELS
from bazi.analyzer.relationship import AtBirthAnalysis, TransitAnalysis
from bazi.transit_chart import TransitChart
from bazi.transits import TransitSet
from bazi.transits import TransitKind


def test_shensha_labels() -> None:
  shensha: ShenshaAnalysis = {
    'taohua'     : frozenset((Dizhi.子,)),
    'hongyan'    : frozenset((Dizhi.丑,)),
    'hongluan'   : frozenset((Dizhi.寅,)),
    'tianxi'     : frozenset((Dizhi.卯,)),
    'yima'       : frozenset((Dizhi.辰,)),
    'huagai'     : frozenset((Dizhi.巳,)),
    'yangren'    : frozenset((Dizhi.午,)),
    'feiren'     : frozenset((Dizhi.未,)),
    'tianyi'     : frozenset((Dizhi.未,)),
    'jiangxing'  : frozenset((Dizhi.申,)),
    'zaisha'     : frozenset((Dizhi.午,)),
    'jiesha'     : frozenset((Dizhi.亥,)),
    'wangshen'   : frozenset((Dizhi.酉,)),
    'guchen'     : frozenset((Dizhi.戌,)),
    'guasu'      : frozenset((Dizhi.亥,)),
    'lushen'     : frozenset((Dizhi.子,)),
    'jinyu'      : frozenset((Dizhi.丑,)),
    'wenchang'   : frozenset((Dizhi.寅,)),
    'wenchanggui': frozenset((Dizhi.卯,)),
    'taiji'      : frozenset((Dizhi.辰,)),
    'guoyin'     : frozenset((Dizhi.巳,)),
    'kongwang'   : frozenset((Dizhi.戌,)),
  }
  expected = (
    ('桃花', frozenset((Dizhi.子,))),
    ('红鸾', frozenset((Dizhi.寅,))),
    ('红艳', frozenset((Dizhi.丑,))),
    ('天喜', frozenset((Dizhi.卯,))),
    ('驿马', frozenset((Dizhi.辰,))),
    ('华盖', frozenset((Dizhi.巳,))),
    ('羊刃', frozenset((Dizhi.午,))),
    ('飞刃', frozenset((Dizhi.未,))),
    ('天乙贵人', frozenset((Dizhi.未,))),
    ('将星', frozenset((Dizhi.申,))),
    ('灾煞', frozenset((Dizhi.午,))),
    ('劫煞', frozenset((Dizhi.亥,))),
    ('亡神', frozenset((Dizhi.酉,))),
    ('孤辰', frozenset((Dizhi.戌,))),
    ('寡宿', frozenset((Dizhi.亥,))),
    ('禄神', frozenset((Dizhi.子,))),
    ('金舆', frozenset((Dizhi.丑,))),
    ('文昌', frozenset((Dizhi.寅,))),
    ('文昌贵', frozenset((Dizhi.卯,))),
    ('太极贵人', frozenset((Dizhi.辰,))),
    ('国印贵人', frozenset((Dizhi.巳,))),
    ('空亡', frozenset((Dizhi.戌,))),
  )

  # Keep display labels exhaustive as ShenshaAnalysis grows.
  assert len(expected) == len(ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__)
  assert cli._named_shensha(shensha) == expected
  assert cli._shensha_strs(shensha) == [
    f'{label}：{cli._colored_str(next(iter(dizhis)))}'
    for label, dizhis in expected
  ]

  common_keys = ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__
  at_birth_keys = AtBirthShenshaAnalysis.__required_keys__ | AtBirthShenshaAnalysis.__optional_keys__
  assert tuple(cli._WHOLE_PILLAR_SHENSHA_LABELS) == ('kuigang', 'tianshe')
  assert set(cli._WHOLE_PILLAR_SHENSHA_LABELS) == at_birth_keys - common_keys
  assert tuple(cli._WHOLE_PILLAR_SHENSHA_LABELS.values()) == ('魁罡', '天赦')

  kuigang = Ganzhi.from_str('庚辰')
  tianshe = Ganzhi.from_str('戊寅')
  at_birth_shensha: AtBirthShenshaAnalysis = {
    **shensha,
    'kuigang': kuigang,
    'tianshe': tianshe,
  }
  assert cli._at_birth_shensha_strs(at_birth_shensha) == [
    *cli._shensha_strs(shensha),
    f'魁罡：{cli._colored_str(kuigang)}',
    f'天赦：{cli._colored_str(tianshe)}',
  ]
  assert cli._at_birth_shensha_strs({
    **shensha,
    'kuigang': kuigang,
    'tianshe': None,
  }) == [
    *cli._shensha_strs(shensha),
    f'魁罡：{cli._colored_str(kuigang)}',
  ]
  assert cli._at_birth_shensha_strs({
    **shensha,
    'kuigang': None,
    'tianshe': tianshe,
  }) == [
    *cli._shensha_strs(shensha),
    f'天赦：{cli._colored_str(tianshe)}',
  ]

  empty_shensha: ShenshaAnalysis = {
    'taohua'     : frozenset(),
    'hongyan'    : frozenset(),
    'hongluan'   : frozenset(),
    'tianxi'     : frozenset(),
    'yima'       : frozenset(),
    'huagai'     : frozenset(),
    'yangren'    : frozenset(),
    'feiren'     : frozenset(),
    'tianyi'     : frozenset(),
    'jiangxing'  : frozenset(),
    'zaisha'     : frozenset(),
    'jiesha'     : frozenset(),
    'wangshen'   : frozenset(),
    'guchen'     : frozenset(),
    'guasu'      : frozenset(),
    'lushen'     : frozenset(),
    'jinyu'      : frozenset(),
    'wenchang'   : frozenset(),
    'wenchanggui': frozenset(),
    'taiji'      : frozenset(),
    'guoyin'     : frozenset(),
    'kongwang'   : frozenset(),
  }
  empty_at_birth_shensha: AtBirthShenshaAnalysis = {
    **empty_shensha,
    'kuigang': None,
    'tianshe': None,
  }
  assert cli._shensha_strs(empty_shensha) == []
  assert cli._at_birth_shensha_strs(empty_at_birth_shensha) == []
  assert cli._at_birth_shensha_strs({
    **empty_shensha,
    'kuigang': None,
    'tianshe': tianshe,
  }) == [f'天赦：{cli._colored_str(tianshe)}']
  assert cli._no_shensha_str(empty_at_birth_shensha) == '原局无桃花、红鸾、红艳、天喜、驿马、华盖、羊刃、飞刃、天乙贵人、将星、灾煞、劫煞、亡神、孤辰、寡宿、禄神、金舆、文昌、文昌贵、太极贵人、国印贵人、空亡、魁罡、天赦'

  for selected, ordered in (
    ((), ()),
    ((Dizhi.酉, Dizhi.子, Dizhi.午), (Dizhi.子, Dizhi.午, Dizhi.酉)),
    ((Dizhi.亥, Dizhi.戌, Dizhi.酉, Dizhi.申, Dizhi.未, Dizhi.午,
      Dizhi.巳, Dizhi.辰, Dizhi.卯, Dizhi.寅, Dizhi.丑, Dizhi.子),
     (Dizhi.子, Dizhi.丑, Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.巳,
      Dizhi.午, Dizhi.未, Dizhi.申, Dizhi.酉, Dizhi.戌, Dizhi.亥)),
  ):
    text = ', '.join(map(cli._colored_str, ordered))
    for name, label in SHENSHA_LABELS.items():
      current = cast(ShenshaAnalysis, {**empty_shensha, name: frozenset(selected)})
      assert cli._shensha_strs(current) == ([f'{label}：{text}'] if selected else [])


def test_kongwang_display_keeps_anchor_and_target() -> None:
  anchor = Ganzhi.from_str('甲子')
  target = Ganzhi.from_str('甲戌')
  assert cli._kongwang_strs((
    KongwangResult(Zhu.日, anchor, (KongwangHit(Zhu.时, target),)),
    KongwangResult(Zhu.年, anchor, ()),
  )) == ['日柱 甲子 → 旬空戌亥；命中：时柱 甲戌', '年柱 甲子 → 旬空戌亥；命中：无']
  assert cli._kongwang_strs((KongwangResult(Zhu.日, anchor, (
    KongwangHit(TransitKind.DAYUN, target),
    KongwangHit(TransitKind.LIUNIAN, target),
  )),)) == ['日柱 甲子 → 旬空戌亥；命中：dayun 甲戌、liunian 甲戌']


def _plain_shensha(shensha: ShenshaAnalysis) -> list[str]:
  values = cast(dict[str, frozenset[Dizhi]], shensha)
  return [
    f'{label}：' + ', '.join(branch for branch in '子丑寅卯辰巳午未申酉戌亥' if branch in set(map(str, values[name])))
    for name, label in SHENSHA_LABELS.items() if values[name]
  ]


def _plain_kongwang(results: tuple[KongwangResult, ...]) -> list[str]:
  lines = []
  for result in results:
    absent = ''.join(branch for branch in '子丑寅卯辰巳午未申酉戌亥' if branch in set(map(str, result.xunkong)))
    hits = '、'.join(
      f'{str(hit.position) + "柱" if isinstance(hit.position, Zhu) else hit.position.value} {hit.ganzhi}'
      for hit in result.hits
    ) or '无'
    lines.append(f'{result.anchor}柱 {result.ganzhi} → 旬空{absent}；命中：{hits}')
  return lines


@pytest.mark.parametrize('empty', [False, True])
def test_main_relationship_keeps_ten_years(
  monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], empty: bool,
) -> None:
  if empty:
    at_birth = cast(AtBirthShenshaAnalysis, {
      **{name: frozenset() for name in SHENSHA_LABELS}, 'kuigang': None, 'tianshe': None,
    })
    transits = cast(ShenshaAnalysis, {name: frozenset() for name in SHENSHA_LABELS})
    monkeypatch.setattr(AtBirthAnalysis, 'shensha', property(lambda self: at_birth))

    def no_shensha(self: TransitAnalysis, selected: TransitSet) -> ShenshaAnalysis:
      return transits

    monkeypatch.setattr(TransitAnalysis, 'shensha', no_shensha)

  chart = BaziChart(Bazi.random(rng=random.Random(236)))
  analyzer = RelationshipAnalyzer(chart)
  stars = chart.relationship_stars
  at_birth_shensha = analyzer.at_birth.shensha
  natal_lines = _plain_shensha(at_birth_shensha)
  for label, pillar in (('魁罡', at_birth_shensha['kuigang']), ('天赦', at_birth_shensha['tianshe'])):
    if pillar is not None:
      natal_lines.append(f'{label}：{pillar}')
  lines = [
    'random seed: 236', re.sub(r'\x1b\[[0-9;]*m', '', cli._get_basic_info(chart)), '\n' + '-' * 60 + '\n',
    f'夫妻宫：{chart.house_of_relationship}', f'配偶星：{", ".join(map(str, (stars.tiangan, *stars.dizhi)))}',
    '\n' + '-' * 60 + '\n',
    *(['原局神煞：', *natal_lines] if natal_lines else [
      '原局无桃花、红鸾、红艳、天喜、驿马、华盖、羊刃、飞刃、天乙贵人、将星、灾煞、劫煞、亡神、孤辰、寡宿、禄神、金舆、文昌、文昌贵、太极贵人、国印贵人、空亡、魁罡、天赦',
    ]),
    '六甲旬空依据：', *_plain_kongwang(analyzer.at_birth.kongwang), '\n' + '-' * 60 + '\n',
    f'流年神煞（{chart.bazi.ganzhi_year + 20} 起十年）：',
  ]
  transit_chart = TransitChart(chart)
  years = list(range(chart.bazi.ganzhi_year + 20, chart.bazi.ganzhi_year + 30))
  for year in years:
    selected = transit_chart.at_year(year)
    assert selected is not None
    liunian = selected.select(TransitKind.LIUNIAN)
    shensha = _plain_shensha(analyzer.transits.shensha(liunian))
    lines.append(f'{year}：' + ('' if shensha else '无'))
    lines.extend(f'  {line}' for line in shensha)
    lines.extend(f'  {line}' for line in _plain_kongwang(analyzer.transits.kongwang(liunian)))
  state = random.getstate()
  assert cli.main(['relationship', '--seed', '236']) == 0
  output = capsys.readouterr()
  assert output.err == ''
  assert re.sub(r'\x1b\[[0-9;]*m', '', output.out) == '\n'.join(lines) + '\n'
  assert [int(year) for year in re.findall(r'^(\d+)：', output.out, flags=re.MULTILINE)] == years
  assert ('原局无桃花' in output.out) is empty
  assert random.getstate() == state
