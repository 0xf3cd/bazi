# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import datetime
from functools import cache
from typing import Any

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context, RelationshipProfile
from bazi.school import BaziConfig


GUANSHA = 'editorial.guansha_coexistence.v1'
FEMALE = 'editorial.guansha_coexistence_female.v1'
LEGAL = ('editorial.shishen.zhengguan.legal_trouble', 'editorial.shishen.qisha.legal_trouble')
RELATIONSHIP = ('editorial.shishen.zhengguan.infidelity', 'editorial.shishen.qisha.infidelity')
DING, GENG = 'tiangan.ding_weak_and_overcontrolled', 'tiangan.geng_regulated_transit'
PIANYIN, XIAOYIN = 'shishen.pianyin_favorable_or_balanced', 'shishen.xiaoyin_duoshi'
CONDITION_CLAIMS = {
  DING: 'legacy.tiangan.ding.weak_state', GENG: 'legacy.tiangan.geng.regulated_transit',
  PIANYIN: 'legacy.shishen.SH-199', XIAOYIN: 'legacy.shishen.SH-066',
}


def chart(day: int = 3, gender: str = 'female', hour: int = 12) -> BaziChart:
  return BaziChart(Bazi.create(datetime(2000, 1, day, hour), gender, BaziConfig.from_values(backend='celestial', precision='day')))


def match(day: int = 3, gender: str = 'female', **kwargs: Any) -> ContextResult:
  options = {'criterion_id': GUANSHA, 'profile': ContextProfile('natal'), 'include_reference_only': True, **kwargs}
  return evaluate_context(chart(day, gender), **options)


@cache
def record(criterion_id: str, profile: ContextProfile, day: int, gender: str) -> ContextResult:
  return match(day, gender, criterion_id=criterion_id, profile=profile)


class Year(int):
  pass


# #233 婚恋判据: explicit transit profiles, missing data, three-state reference matrix, and record v3.
# All cases use reproducible real birth inputs and configs; 岁运 come from real TransitChart queries by coordinate.

PALACE = 'editorial.spouse_palace_xingchong.v1'
TOUGAN = 'editorial.spouse_star_tougan.v1'
RELATED_PALACE = 'editorial.tanyuan.wife_palace_xingchong.v1'
RELATED_TOUGAN = 'editorial.tanyuan.wife_star_gantou.v1'


def rel_match(
  criterion_id: str = PALACE,
  birth: str = '2000-01-01 12:00',
  gender: str = 'male',
  **kwargs: Any,
) -> ContextResult:
  options: dict[str, Any] = {'profile': RelationshipProfile('natal'), **kwargs}
  return evaluate_context(chart_from(birth, gender), criterion_id=criterion_id, **options)


def chart_from(birth: str, gender: str) -> BaziChart:
  return BaziChart(Bazi.create(birth, gender))
