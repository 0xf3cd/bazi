# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import pytest

from bazi.analyzer.relationship import SHENSHA_LABELS
from bazi.knowledge import KnowledgeBase
from bazi.rules import BaziRules, ShenshaRules


@pytest.mark.parametrize('definition,claim_id,offset', [
  (ShenshaRules.GuoyinDef.MODERN, 'shensha.guoyin.modern', 8),
  (ShenshaRules.GuoyinDef.WUXING_JINGJI, 'shensha.guoyin.wuxing_jingji', 7),
])
def test_guoyin_text_matches_rule(
  definition: ShenshaRules.GuoyinDef, claim_id: str, offset: int,
) -> None:
  entry = KnowledgeBase.load().entry(claim_id)
  assert f'偏移 +{offset}' in entry.text
  assert all((target.index - BaziRules.TIANGAN_LU[tg].index) % 12 == offset
             for tg, target in ShenshaRules.GUOYIN[definition].items())


def test_shensha_objects_match_known_catalog() -> None:
  for obj in KnowledgeBase.load().objects.values():
    if obj.kind == 'shensha' and obj.object_id != 'shensha.kongwang':
      assert obj.name == SHENSHA_LABELS[obj.object_id.removeprefix('shensha.')]
