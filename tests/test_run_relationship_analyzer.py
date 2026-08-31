# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from run_demo import colored_str
from run_relationship_analyzer import _named_shensha, _no_shensha_str, shensha_strs
from src.defines import Dizhi
from src.analyzer.relationship import ShenshaAnalysis


def test_shensha_labels() -> None:
  shensha: ShenshaAnalysis = {
    'taohua'   : frozenset((Dizhi.子,)),
    'hongyan'  : frozenset((Dizhi.丑,)),
    'hongluan' : frozenset((Dizhi.寅,)),
    'tianxi'   : frozenset((Dizhi.卯,)),
    'yima'     : frozenset((Dizhi.辰,)),
    'huagai'   : frozenset((Dizhi.巳,)),
    'yangren'  : frozenset((Dizhi.午,)),
    'feiren'   : frozenset((Dizhi.未,)),
    'tianyi'   : frozenset((Dizhi.未,)),
    'jiangxing': frozenset((Dizhi.申,)),
    'zaisha'   : frozenset((Dizhi.午,)),
    'jiesha'   : frozenset((Dizhi.亥,)),
    'wangshen' : frozenset((Dizhi.酉,)),
    'guchen'   : frozenset((Dizhi.戌,)),
    'guasu'    : frozenset((Dizhi.亥,)),
    'lushen'   : frozenset((Dizhi.子,)),
    'jinyu'    : frozenset((Dizhi.丑,)),
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
  )

  # Keep display labels exhaustive as ShenshaAnalysis grows.
  assert len(expected) == len(ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__)
  assert _named_shensha(shensha) == expected
  assert shensha_strs(shensha) == [
    f'{label}：{colored_str(next(iter(dizhis)))}'
    for label, dizhis in expected
  ]

  empty_shensha: ShenshaAnalysis = {
    'taohua'   : frozenset(),
    'hongyan'  : frozenset(),
    'hongluan' : frozenset(),
    'tianxi'   : frozenset(),
    'yima'     : frozenset(),
    'huagai'   : frozenset(),
    'yangren'  : frozenset(),
    'feiren'   : frozenset(),
    'tianyi'   : frozenset(),
    'jiangxing': frozenset(),
    'zaisha'   : frozenset(),
    'jiesha'   : frozenset(),
    'wangshen' : frozenset(),
    'guchen'   : frozenset(),
    'guasu'    : frozenset(),
    'lushen'   : frozenset(),
    'jinyu'    : frozenset(),
  }
  assert shensha_strs(empty_shensha) == []
  assert _no_shensha_str(empty_shensha) == '原局无桃花、红鸾、红艳、天喜、驿马、华盖、羊刃、飞刃、天乙贵人、将星、灾煞、劫煞、亡神、孤辰、寡宿、禄神、金舆'
