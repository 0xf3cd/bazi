# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from run_demo import colored_str
from run_relationship_analyzer import _named_shensha, shensha_strs
from src.defines import Dizhi
from src.analyzer.relationship import ShenshaAnalysis


def test_shensha_labels() -> None:
  shensha: ShenshaAnalysis = {
    'taohua'  : frozenset((Dizhi.子,)),
    'hongyan' : frozenset((Dizhi.丑,)),
    'hongluan': frozenset((Dizhi.寅,)),
    'tianxi'  : frozenset((Dizhi.卯,)),
    'yima'    : frozenset((Dizhi.辰,)),
    'huagai'  : frozenset((Dizhi.巳,)),
    'yangren' : frozenset((Dizhi.午,)),
    'tianyi'  : frozenset((Dizhi.未,)),
  }
  expected = (
    ('桃花', frozenset((Dizhi.子,))),
    ('红鸾', frozenset((Dizhi.寅,))),
    ('红艳', frozenset((Dizhi.丑,))),
    ('天喜', frozenset((Dizhi.卯,))),
    ('驿马', frozenset((Dizhi.辰,))),
    ('华盖', frozenset((Dizhi.巳,))),
    ('羊刃', frozenset((Dizhi.午,))),
    ('天乙贵人', frozenset((Dizhi.未,))),
  )

  assert _named_shensha(shensha) == expected
  assert shensha_strs(shensha) == [
    f'{label}：{colored_str(next(iter(dizhis)))}'
    for label, dizhis in expected
  ]
