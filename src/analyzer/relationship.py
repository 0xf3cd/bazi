# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import functools

from dataclasses import dataclass
from enum import Enum, IntFlag, auto, unique
from itertools import product
from typing import Final, TypedDict
from collections.abc import Callable, Iterable, Sequence

from ..common import frozendict
from ..data_types import GanzhiData
from ..defines import Tiangan, Dizhi, Ganzhi, Shishen, DizhiRelation
from ..rules import DizhiRules
from ..school import KeyStem, TianyiAnchor, JinyuAnchor, ZaishaAnchor, ShenshaAnchorProfile, BaziSchool
from ..bazi import Bazi
from ..bazi_chart import BaziChart
from ..transits import TransitSet
from ..utils import bazi_utils, shensha_utils, tiangan_utils, dizhi_utils


'''The type of the first argument passed to Shensha-finding functions: an iterable of Tiangan or Dizhi.'''
_FirstArgType = Iterable[Tiangan | Dizhi]

'''The type of the second argument passed to Shensha-finding functions: an iterable of Dizhi.'''
_SecondArgType = Iterable[Dizhi]

'''The type of the argument tuple that `find_shensha` accepts.'''
_ArgsType = tuple[_FirstArgType, _SecondArgType]

'''A resolver for a Shensha predicate's optional `definition` from the chart's school.'''
_DefinitionResolver = Callable[[BaziSchool], object]

def find_shensha(
  f: Callable[..., bool],
  *args: _ArgsType,
) -> Iterable[Dizhi]:
  '''A private/internal helper for finding Shensha (神煞): yield the Dizhi of every
  (key, dizhi) pair that the predicate `f` accepts.'''
  return (dz for keys, dizhis in args for key, dz in product(keys, dizhis) if f(key, dz))


@unique
class _KeySource(Enum):
  '''The key(s) that a Shensha is looked up by (查询神煞时所用的 key).

  Each registry entry must derive its key source and inspected pillars from that Shensha's
  own provenance; existing entries are not defaults for future Shenshas.
  每个注册项的查询 key 与被查柱都须来自该神煞自身出处；既有条目不构成后续神煞的默认口径。
  '''
  YEAR_DIZHI        = auto() # By the year pillar's Dizhi only (只看年支).
  YEAR_OR_DAY_DIZHI = auto() # By the year or day pillar's Dizhi (看年支或日支).
  DAY_MASTER        = auto() # Always by the Day Master (固定以日干为锚).
  KEY_TIANGAN       = auto() # By a key Tiangan (查法锚干): day master by default, year tiangan per school. Sole consumer today: 红艳 (see `_hongyan_anchor`).
  ANCHOR_TIANGANS   = auto() # By one or both year/day Tiangans selected per school (see `_tianyi_anchors`).
  JINYU_ANCHOR_TIANGANS = auto() # By the Day Master alone, or both year/day Tiangans, as selected for 金舆 (see `_jinyu_anchors`).
  ZAISHA_ANCHOR_DIZHIS = auto() # By the year Dizhi alone, or both year/day Dizhis, as selected for 灾煞 (see `_zaisha_anchors`).
  PROFILED_DIZHI    = auto() # By the day Dizhi alone, or both year and day Dizhis, as selected by the source profile for 驿马、华盖、将星、劫煞、亡神 (see `_profiled_shensha_anchors`).


@dataclass(frozen=True)
class _ShenshaSpec:
  '''
  The spec of a Shensha: the predicate, key source, and optional school-derived definition.
  神煞的规格：判断函数、查询 key，以及可选的流派定义参数。

  Note: the predicate's first-parameter type must match `key`. When `definition` is present, the
  predicate must accept its result through a keyword-only `definition` argument. Each predicate
  checks this contract at runtime; the registry's type does not express it.
  '''
  predicate:  Callable[..., bool]
  key:        _KeySource
  definition: _DefinitionResolver | None = None


'''The registry of the Dizhi-valued Shenshas supported by relationship analysis
(亲密关系分析支持的地支结果神煞注册表).'''
_REGISTRY: Final[frozendict[str, _ShenshaSpec]] = frozendict({
  'taohua'   : _ShenshaSpec(shensha_utils.taohua,    _KeySource.YEAR_OR_DAY_DIZHI),
  'hongyan'  : _ShenshaSpec(shensha_utils.hongyan,   _KeySource.KEY_TIANGAN),
  'hongluan' : _ShenshaSpec(shensha_utils.hongluan,  _KeySource.YEAR_DIZHI),
  'tianxi'   : _ShenshaSpec(shensha_utils.tianxi,    _KeySource.YEAR_DIZHI),
  'yima'     : _ShenshaSpec(shensha_utils.yima,      _KeySource.PROFILED_DIZHI),
  'huagai'   : _ShenshaSpec(shensha_utils.huagai,    _KeySource.PROFILED_DIZHI),
  'yangren'  : _ShenshaSpec(
    shensha_utils.yangren,
    _KeySource.DAY_MASTER,
    lambda school: school.yangren_def,
  ),
  'feiren'   : _ShenshaSpec(
    shensha_utils.feiren,
    _KeySource.DAY_MASTER,
    lambda school: school.feiren_def,
  ),
  'tianyi'   : _ShenshaSpec(
    shensha_utils.tianyi,
    _KeySource.ANCHOR_TIANGANS,
    lambda school: school.tianyi_def,
  ),
  'jiangxing': _ShenshaSpec(shensha_utils.jiangxing, _KeySource.PROFILED_DIZHI),
  'zaisha'   : _ShenshaSpec(shensha_utils.zaisha,    _KeySource.ZAISHA_ANCHOR_DIZHIS),
  'jiesha'   : _ShenshaSpec(shensha_utils.jiesha,    _KeySource.PROFILED_DIZHI),
  'wangshen' : _ShenshaSpec(shensha_utils.wangshen,  _KeySource.PROFILED_DIZHI),
  'guchen'   : _ShenshaSpec(shensha_utils.guchen,    _KeySource.YEAR_DIZHI),
  'guasu'    : _ShenshaSpec(shensha_utils.guasu,     _KeySource.YEAR_DIZHI),
  'lushen'   : _ShenshaSpec(shensha_utils.lushen,    _KeySource.DAY_MASTER),
  'jinyu'    : _ShenshaSpec(shensha_utils.jinyu,     _KeySource.JINYU_ANCHOR_TIANGANS),
})


def _hongyan_anchor(bazi: Bazi) -> Tiangan:
  '''The anchor Tiangan a HONGYAN (红艳) lookup keys on (查法锚干, issue #69): the registry
  records the static default (`_KeySource.KEY_TIANGAN`, the 《三命通会》 reading), and the
  chart's school profile overrides it at evaluation time -- `KeyStem.YEAR_MASTER` keys on
  the year tiangan instead. 红艳查法的锚干：注册表记静态默认（查日干），评估期由盘的
  `BaziSchool.hongyan_key` 覆盖（可查年干）。'''
  key_stem: Final[KeyStem] = bazi.config.school.hongyan_key
  if key_stem is KeyStem.DAY_MASTER:
    return bazi.day_master
  elif key_stem is KeyStem.YEAR_MASTER:
    return bazi.year_pillar.tiangan
  else:
    # Invariant: every `KeyStem` member must be wired up above. Reaching here means we
    # added a member but forgot to wire it -- not something users can trigger.
    # `raise` instead of `assert` so the guard survives `python -O`.
    raise AssertionError(f'`KeyStem` not wired up in `_hongyan_anchor`: {key_stem}') # pragma: no cover # Unreachable invariant guard.


def _tianyi_anchors(bazi: Bazi) -> tuple[Tiangan, ...]:
  '''Resolve the TIANYI GUIREN (天乙贵人) anchors selected by
  `BaziSchool.tianyi_anchor`; `YEAR_AND_DAY` returns both stems.
  按 `BaziSchool.tianyi_anchor` 解析天乙贵人锚干；年日兼查时同时返回两干。'''
  anchor: Final[TianyiAnchor] = bazi.config.school.tianyi_anchor
  if anchor is TianyiAnchor.DAY_MASTER:
    return (bazi.day_master,)
  elif anchor is TianyiAnchor.YEAR_MASTER:
    return (bazi.year_pillar.tiangan,)
  elif anchor is TianyiAnchor.YEAR_AND_DAY:
    return (bazi.year_pillar.tiangan, bazi.day_master)
  else:
    raise AssertionError(f'`TianyiAnchor` not wired up in `_tianyi_anchors`: {anchor}') # pragma: no cover # Unreachable invariant guard.


def _jinyu_anchors(bazi: Bazi) -> tuple[Tiangan, ...]:
  '''Resolve the JINYU (金舆) anchors selected by `BaziSchool.jinyu_anchor`.
  按 `BaziSchool.jinyu_anchor` 解析金舆锚干。'''
  anchor: Final[JinyuAnchor] = bazi.config.school.jinyu_anchor
  if anchor is JinyuAnchor.DAY_MASTER:
    return (bazi.day_master,)
  elif anchor is JinyuAnchor.YEAR_AND_DAY:
    return (bazi.year_pillar.tiangan, bazi.day_master)
  else:
    raise AssertionError(f'`JinyuAnchor` not wired up in `_jinyu_anchors`: {anchor}') # pragma: no cover # Unreachable invariant guard.


def _zaisha_anchors(bazi: Bazi) -> tuple[Dizhi, ...]:
  '''Resolve the ZAISHA (灾煞) anchors selected by `BaziSchool.zaisha_anchor`.
  按 `BaziSchool.zaisha_anchor` 解析灾煞锚支。'''
  anchor: Final[ZaishaAnchor] = bazi.config.school.zaisha_anchor
  if anchor is ZaishaAnchor.YEAR:
    return (bazi.year_pillar.dizhi,)
  elif anchor is ZaishaAnchor.YEAR_AND_DAY:
    return (bazi.year_pillar.dizhi, bazi.day_pillar.dizhi)
  else:
    raise AssertionError(f'`ZaishaAnchor` not wired up in `_zaisha_anchors`: {anchor}') # pragma: no cover # Unreachable invariant guard.


def _profiled_shensha_anchors(bazi: Bazi) -> tuple[Dizhi, ...]:
  '''Resolve the YIMA, HUAGAI, JIANGXING, JIESHA, and WANGSHEN anchors selected by
  `BaziSchool.shensha_anchor_profile`.
  按 `BaziSchool.shensha_anchor_profile` 解析驿马、华盖、将星、劫煞、亡神锚支。'''
  profile: Final[ShenshaAnchorProfile] = bazi.config.school.shensha_anchor_profile
  if profile is ShenshaAnchorProfile.WENZHEN:
    return (bazi.year_pillar.dizhi, bazi.day_pillar.dizhi)
  elif profile is ShenshaAnchorProfile.MINGLI_TANYUAN:
    return (bazi.day_pillar.dizhi,)
  else:
    raise AssertionError(f'`ShenshaAnchorProfile` not wired up in `_profiled_shensha_anchors`: {profile}') # pragma: no cover # Unreachable invariant guard.


def _shensha_keys(key_source: _KeySource, bazi: Bazi) -> tuple[Tiangan | Dizhi, ...]:
  '''Resolve a Shensha's lookup keys / 解析神煞查询 key。'''
  if key_source is _KeySource.YEAR_DIZHI:
    return (bazi.year_pillar.dizhi,)
  elif key_source is _KeySource.YEAR_OR_DAY_DIZHI:
    return (bazi.year_pillar.dizhi, bazi.day_pillar.dizhi)
  elif key_source is _KeySource.DAY_MASTER:
    return (bazi.day_master,)
  elif key_source is _KeySource.KEY_TIANGAN:
    return (_hongyan_anchor(bazi),)
  elif key_source is _KeySource.ANCHOR_TIANGANS:
    return _tianyi_anchors(bazi)
  elif key_source is _KeySource.JINYU_ANCHOR_TIANGANS:
    return _jinyu_anchors(bazi)
  elif key_source is _KeySource.ZAISHA_ANCHOR_DIZHIS:
    return _zaisha_anchors(bazi)
  elif key_source is _KeySource.PROFILED_DIZHI:
    return _profiled_shensha_anchors(bazi)
  else:
    # Invariant: every `_KeySource` member must be wired up above. Reaching here means we
    # added a member but forgot to wire it -- not something users can trigger.
    # `raise` instead of `assert` so the guard survives `python -O`.
    raise AssertionError(f'`_KeySource` not wired up in `_shensha_keys`: {key_source}') # pragma: no cover # Unreachable invariant guard.


def _shensha_predicate(spec: _ShenshaSpec, school: BaziSchool) -> Callable[..., bool]:
  '''Bind a Shensha predicate's school definition when it has one / 按盘绑定神煞定义参数。'''
  if spec.definition is None:
    return spec.predicate
  definition = spec.definition(school)
  return functools.partial(spec.predicate, definition=definition)


def _eval_at_birth(spec: _ShenshaSpec, bazi: Bazi) -> frozenset[Dizhi]:
  '''Evaluate a Shensha against the at-birth Bazi / 在原局上评估某个神煞。'''
  y_dz, m_dz, d_dz, h_dz = bazi.four_dizhis
  keys = _shensha_keys(spec.key, bazi)

  args: tuple[_ArgsType, ...]
  if spec.key is _KeySource.YEAR_DIZHI:
    args = ((keys, (m_dz, d_dz, h_dz)),)
  elif spec.key is _KeySource.ZAISHA_ANCHOR_DIZHIS:
    if bazi.config.school.zaisha_anchor is ZaishaAnchor.YEAR:
      year_key, = keys
      args = (((year_key,), (m_dz, d_dz, h_dz)),)
    else:
      assert bazi.config.school.zaisha_anchor is ZaishaAnchor.YEAR_AND_DAY
      year_key, day_key = keys
      args = (((year_key,), (m_dz, d_dz, h_dz)), ((day_key,), (y_dz, m_dz, h_dz)))
  elif spec.key is _KeySource.YEAR_OR_DAY_DIZHI or (
    spec.key is _KeySource.PROFILED_DIZHI
    and bazi.config.school.shensha_anchor_profile is ShenshaAnchorProfile.WENZHEN
  ):
    year_key, day_key = keys
    args = (((year_key,), (m_dz, d_dz, h_dz)), ((day_key,), (y_dz, m_dz, h_dz)))
  elif spec.key is _KeySource.PROFILED_DIZHI:
    assert bazi.config.school.shensha_anchor_profile is ShenshaAnchorProfile.MINGLI_TANYUAN
    day_key, = keys
    args = (((day_key,), (y_dz, m_dz, h_dz)),)
  else:
    args = ((keys, (y_dz, m_dz, d_dz, h_dz)),)

  return frozenset(find_shensha(_shensha_predicate(spec, bazi.config.school), *args))


def _eval_transits(spec: _ShenshaSpec, bazi: Bazi, transit_dizhis: Iterable[Dizhi]) -> frozenset[Dizhi]:
  '''Evaluate a Shensha against the transit Dizhis / 在流运地支上评估某个神煞。'''
  return frozenset(find_shensha(
    _shensha_predicate(spec, bazi.config.school),
    (_shensha_keys(spec.key, bazi), transit_dizhis),
  ))


# The ONLY place this file reads the school profile for Dizhi relation discovery:
# every `dizhi_utils` batch query below goes through one of these wrappers,
# so "no bare calls in this file" is a grep-checkable invariant --
# a forgotten relation-definition argument at some call site would silently fall back to the
# hardcoded defaults (issue #69).
# 本文件唯一为地支关系查法读流派档案的地方：下文所有 `dizhi_utils` 批量查法一律走这些
# 薄包装——「本文件无裸调」是一条 grep 可验的不变量，
# 某个调用点忘传参会静默回落到硬编码默认（issue #69）。
def _dz_discover(school: BaziSchool, dizhis: Sequence[Dizhi]) -> dizhi_utils.DizhiRelationDiscovery:
  '''`dizhi_utils.discover` under the chart's school profile / 按盘的流派档案发现地支关系。'''
  return dizhi_utils.discover(dizhis, anhe_def=school.anhe_def, xing_def=school.xing_def)


def _dz_discover_mutual(school: BaziSchool, dizhis1: Sequence[Dizhi], dizhis2: Sequence[Dizhi]) -> dizhi_utils.DizhiRelationDiscovery:
  '''`dizhi_utils.discover_mutual` under the chart's school profile / 按盘的流派档案发现两组地支间的关系。'''
  return dizhi_utils.discover_mutual(dizhis1, dizhis2, anhe_def=school.anhe_def, xing_def=school.xing_def)


def _dz_discover_ganzhis(school: BaziSchool, ganzhis: Sequence[Ganzhi]) -> dizhi_utils.GanzhiRelationDiscovery:
  '''Position-preserving discovery under the chart's school / 按盘的流派档案保留柱位发现关系。'''
  return dizhi_utils.discover_ganzhis(
    ganzhis,
    anhe_def=school.anhe_def,
    xing_def=school.xing_def,
    gong_def=school.gong_def,
  )


def _dz_discover_mutual_ganzhis(
  school: BaziSchool,
  ganzhis1: Sequence[Ganzhi],
  ganzhis2: Sequence[Ganzhi],
) -> dizhi_utils.GanzhiRelationDiscovery:
  '''Position-preserving mutual discovery under the chart's school / 按盘的流派档案保留柱位发现两组关系。'''
  return dizhi_utils.discover_mutual_ganzhis(
    ganzhis1,
    ganzhis2,
    anhe_def=school.anhe_def,
    xing_def=school.xing_def,
    gong_def=school.gong_def,
  )


_DAY_PILLAR_INDEX: Final[int] = 2


def _project_gong(
  discovery: dizhi_utils.GanzhiRelationDiscovery,
  predicate: Callable[[dizhi_utils.GanzhiRelationCombo], bool],
) -> dizhi_utils.DizhiRelationDiscovery:
  '''Filter concrete Gong participants before discarding their positions / 先按具体参与柱过滤拱局，再投影地支。'''
  return dizhi_utils.GanzhiRelationDiscovery({
    relation : filtered
    for relation in DizhiRules.GONG_RELATIONS
    if len(filtered := tuple(combo for combo in discovery.get(relation, ()) if predicate(combo))) > 0
  }).to_dizhi_discovery()


def _with_gong(
  existing: dizhi_utils.DizhiRelationDiscovery,
  gong: dizhi_utils.DizhiRelationDiscovery,
) -> dizhi_utils.DizhiRelationDiscovery:
  '''Add disjoint Gong keys without reordering existing relation combos / 加入拱局键且不重排既有组合。'''
  assert set(existing).isdisjoint(gong)
  return dizhi_utils.DizhiRelationDiscovery({**existing, **gong})


class ShenshaAnalysis(TypedDict):
  # The Taohua Dizhis    (桃花星所在地支)
  taohua:    frozenset[Dizhi]
  # The Hongyan Dizhis   (红艳星所在地支)
  hongyan:   frozenset[Dizhi]
  # The Hongluan Dizhis  (红鸾星所在地支)
  hongluan:  frozenset[Dizhi]
  # The Tianxi Dizhis    (天喜星所在地支)
  tianxi:    frozenset[Dizhi]
  # The Yima Dizhis      (驿马星所在地支)
  yima:      frozenset[Dizhi]
  # The Huagai Dizhis    (华盖星所在地支)
  huagai:    frozenset[Dizhi]
  # The Yangren Dizhis   (羊刃所在地支)
  yangren:   frozenset[Dizhi]
  # The Feiren Dizhis    (飞刃所在地支)
  feiren:    frozenset[Dizhi]
  # The Tianyi Dizhis    (天乙贵人所在地支)
  tianyi:    frozenset[Dizhi]
  # The Jiangxing Dizhis (将星所在地支)
  jiangxing: frozenset[Dizhi]
  # The Zaisha Dizhis    (灾煞所在地支)
  zaisha:    frozenset[Dizhi]
  # The Jiesha Dizhis    (劫煞所在地支)
  jiesha:    frozenset[Dizhi]
  # The Wangshen Dizhis  (亡神所在地支)
  wangshen:  frozenset[Dizhi]
  # The Guchen Dizhis    (孤辰所在地支)
  guchen:    frozenset[Dizhi]
  # The Guasu Dizhis     (寡宿所在地支)
  guasu:     frozenset[Dizhi]
  # The Lushen Dizhis    (禄神所在地支)
  lushen:    frozenset[Dizhi]
  # The Jinyu Dizhis     (金舆所在地支)
  jinyu:     frozenset[Dizhi]


class AtBirthShenshaAnalysis(ShenshaAnalysis):
  # The Kuigang day pillar (魁罡日柱)
  kuigang: Ganzhi | None
  # The Tianshe day pillar (天赦日柱)
  tianshe: Ganzhi | None


class AtBirthAnalysis:
  '''Analysis of Relationship at Birth / 出生时的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @property
  def shensha(self) -> AtBirthShenshaAnalysis:
    bazi = self._chart.bazi
    return {
      'taohua'   : _eval_at_birth(_REGISTRY['taohua'],    bazi),
      'hongyan'  : _eval_at_birth(_REGISTRY['hongyan'],   bazi),
      'hongluan' : _eval_at_birth(_REGISTRY['hongluan'],  bazi),
      'tianxi'   : _eval_at_birth(_REGISTRY['tianxi'],    bazi),
      'yima'     : _eval_at_birth(_REGISTRY['yima'],      bazi),
      'huagai'   : _eval_at_birth(_REGISTRY['huagai'],    bazi),
      'yangren'  : _eval_at_birth(_REGISTRY['yangren'],   bazi),
      'feiren'   : _eval_at_birth(_REGISTRY['feiren'],    bazi),
      'tianyi'   : _eval_at_birth(_REGISTRY['tianyi'],    bazi),
      'jiangxing': _eval_at_birth(_REGISTRY['jiangxing'], bazi),
      'zaisha'   : _eval_at_birth(_REGISTRY['zaisha'],    bazi),
      'jiesha'   : _eval_at_birth(_REGISTRY['jiesha'],    bazi),
      'wangshen' : _eval_at_birth(_REGISTRY['wangshen'],  bazi),
      'guchen'   : _eval_at_birth(_REGISTRY['guchen'],    bazi),
      'guasu'    : _eval_at_birth(_REGISTRY['guasu'],     bazi),
      'lushen'   : _eval_at_birth(_REGISTRY['lushen'],    bazi),
      'jinyu'    : _eval_at_birth(_REGISTRY['jinyu'],     bazi),
      'kuigang'  : bazi.day_pillar if shensha_utils.kuigang(bazi.day_pillar) else None,
      'tianshe'  : bazi.day_pillar if shensha_utils.tianshe(bazi.month_commander, bazi.day_pillar) else None,
    }

  @property
  def day_master_relations(self) -> tiangan_utils.TianganRelationDiscovery:
    y_tg, m_tg, d_tg, h_tg = self._chart.bazi.four_tiangans
    return tiangan_utils.discover_mutual([d_tg], [y_tg, m_tg, h_tg])
  
  @property
  def house_relations(self) -> dizhi_utils.DizhiRelationDiscovery:
    '''Relations that the House of Relationship / 婚姻宫 has. Gong is evaluated under the
    chart's school and retained only when the concrete day-pillar occurrence participates.
    拱局按本盘流派判断，并只保留日柱这一具体出现真正参与的组合。'''
    # For non-Gong relations, keep the complete-discovery path used for three-Dizhi combos;
    # at birth it is equivalent to mutual discovery between the day branch and the other three.
    # A value-only filter would retain a Gong pair formed by another occurrence when that
    # pillar repeats the day branch, so filter concrete participants before projection.
    bazi: Final[Bazi] = self._chart.bazi
    school: Final[BaziSchool] = bazi.config.school
    existing = _dz_discover(school, bazi.four_dizhis).filter(
      lambda _, combo : self._chart.house_of_relationship in combo
    )
    gong = _project_gong(
      _dz_discover_ganzhis(school, bazi.pillars),
      lambda combo : any(occurrence.index == _DAY_PILLAR_INDEX for occurrence in combo),
    )
    return _with_gong(existing, gong)
  
  @property
  def star_relations(self) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''Relations that the Star(s) of Relationship / 配偶星 / 婚姻星 has. Gong is evaluated
    under the chart's school and retained only when a real participant is a relationship-star
    branch. 拱局按本盘流派判断，并只保留实支参与者含配偶星地支的组合。'''
    stars = self._chart.relationship_stars
    bazi: Final[Bazi] = self._chart.bazi
    school: Final[BaziSchool] = bazi.config.school

    tg = tiangan_utils.discover(bazi.four_tiangans).filter(lambda _, combo : stars.tiangan in combo)
    existing = _dz_discover(school, bazi.four_dizhis).filter(lambda _, combo : any(dz in combo for dz in stars.dizhi))
    gong = _project_gong(
      _dz_discover_ganzhis(school, bazi.pillars),
      lambda combo : any(occurrence.ganzhi.dizhi in stars.dizhi for occurrence in combo),
    )
    return GanzhiData(tg, _with_gong(existing, gong))



class TransitAnalysis:
  '''Analysis of Relationship at Transits / 流运的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @staticmethod
  def _check_transits(transits: object) -> None:
    if not isinstance(transits, TransitSet):
      raise TypeError(f'Expected TransitSet, got {type(transits)}')

  def shensha(self, transits: TransitSet) -> ShenshaAnalysis:
    '''
    Return the Shenshas exposed by relationship analysis for the given transits.

    返回给定流运的亲密关系神煞分析。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns:
    - (ShenshaAnalysis) The Shensha analysis of the given transits.
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = tuple(gz.dizhi for gz in transit_ganzhis)

    bazi = self._chart.bazi
    return {
      'taohua'   : _eval_transits(_REGISTRY['taohua'],    bazi, transit_dizhis),
      'hongyan'  : _eval_transits(_REGISTRY['hongyan'],   bazi, transit_dizhis),
      'hongluan' : _eval_transits(_REGISTRY['hongluan'],  bazi, transit_dizhis),
      'tianxi'   : _eval_transits(_REGISTRY['tianxi'],    bazi, transit_dizhis),
      'yima'     : _eval_transits(_REGISTRY['yima'],      bazi, transit_dizhis),
      'huagai'   : _eval_transits(_REGISTRY['huagai'],    bazi, transit_dizhis),
      'yangren'  : _eval_transits(_REGISTRY['yangren'],   bazi, transit_dizhis),
      'feiren'   : _eval_transits(_REGISTRY['feiren'],    bazi, transit_dizhis),
      'tianyi'   : _eval_transits(_REGISTRY['tianyi'],    bazi, transit_dizhis),
      'jiangxing': _eval_transits(_REGISTRY['jiangxing'], bazi, transit_dizhis),
      'zaisha'   : _eval_transits(_REGISTRY['zaisha'],    bazi, transit_dizhis),
      'jiesha'   : _eval_transits(_REGISTRY['jiesha'],    bazi, transit_dizhis),
      'wangshen' : _eval_transits(_REGISTRY['wangshen'],  bazi, transit_dizhis),
      'guchen'   : _eval_transits(_REGISTRY['guchen'],    bazi, transit_dizhis),
      'guasu'    : _eval_transits(_REGISTRY['guasu'],     bazi, transit_dizhis),
      'lushen'   : _eval_transits(_REGISTRY['lushen'],    bazi, transit_dizhis),
      'jinyu'    : _eval_transits(_REGISTRY['jinyu'],     bazi, transit_dizhis),
    }
  
  def day_master_relations(self, transits: TransitSet) -> tiangan_utils.TianganRelationDiscovery:
    '''
    Return the Tiangan relations that the day master and other transit Tiangans form.
    
    返回日主和其他流运的天干之间的关系。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns: (tiangan_utils.TianganRelationDiscovery) The Tiangan relations that the day master and other transit Tiangans form.
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_tiangans = tuple(gz.tiangan for gz in transit_ganzhis)

    return tiangan_utils.discover_mutual([self._chart.bazi.day_master], transit_tiangans)

  def house_relations(self, transits: TransitSet) -> dizhi_utils.DizhiRelationDiscovery:
    '''
    Return the Dizhi relations that the House of Relationship and other transit Dizhis form.

    返回配偶宫/婚姻宫和其他流运的地支之间的关系。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns: (dizhi_utils.DizhiRelationDiscovery) The Dizhi relations that the House of Relationship and other transit Dizhis form.

    Note:
    - Gong is evaluated under the chart's school and retained only when the concrete day-pillar
      occurrence participates. 拱局按本盘流派判断，并只保留日柱这一具体出现参与的组合。
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = [gz.dizhi for gz in transit_ganzhis]

    house = self._chart.house_of_relationship
    bazi = self._chart.bazi
    school: Final[BaziSchool] = bazi.config.school

    # A three-Dizhi combo can span the house, another natal Dizhi, and a transit Dizhi.
    # Discover across the complete natal side first, then retain house combos with a transit
    # witness. `discover_mutual` is value-based, so a repeated house value alone does not
    # witness a multi-Dizhi combo; a singleton self-刑 does.
    def __is_house_transit_relation(_: DizhiRelation, combo: frozenset[Dizhi]) -> bool:
      if house not in combo:
        return False
      if len(combo) == 1:
        return house in transit_dizhis
      return not (combo - {house}).isdisjoint(transit_dizhis)

    existing = _dz_discover_mutual(school, bazi.four_dizhis, transit_dizhis).filter(__is_house_transit_relation)
    gong = _project_gong(
      _dz_discover_mutual_ganzhis(school, bazi.pillars, transit_ganzhis),
      lambda combo : any(occurrence.index == _DAY_PILLAR_INDEX for occurrence in combo),
    )
    return _with_gong(existing, gong)
  
  @unique
  class Level(IntFlag):
    # Analyze only transits. 只分析流运。
    TRANSITS_ONLY        = 1 << 0

    # Analyze the effects that transits and at-birth have on each other. 分析流运和原局互相的影响。
    MUTUAL               = 1 << 1

    # Analyze all effects, basically all of above. 分析所有影响。
    ALL                  = TRANSITS_ONLY | MUTUAL

  '''The constant level space for the `level` gate. `level` 闸的常量级别空间。'''
  _ALL_LEVELS: Final[tuple[Level, ...]] = (Level.TRANSITS_ONLY, Level.MUTUAL, Level.ALL)

  def star_relations(
    self,
    transits: TransitSet,
    *, level: Level = Level.ALL,
  ) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''
    Return the Tiangan and Dizhi relations that the Star(s) of Relationship and other transit Ganzhis form.

    返回配偶星/婚姻星和其他流运的干支之间的关系。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。
    - level: (Level) The level of the analysis. 返回分析的级别。

    Returns: (GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]) The Tiangan and Dizhi relations that the Star(s) of Relationship and other transit Ganzhis form.

    Note:
    - Gong is evaluated under the chart's school and retained only when a real participant is a
      relationship-star branch. With `TRANSITS_ONLY`, adjacency follows the present entries in
      `transits.ganzhis`; narrowing a `TransitSet` can therefore change Gong adjacency.
    - 拱局按本盘流派判断，并只保留实支参与者含配偶星地支的组合。`TRANSITS_ONLY` 的相邻关系
      按 `transits.ganzhis` 中实际存在的流运计算；缩小 `TransitSet` 可能因此改变拱局相邻关系。
    '''

    if not isinstance(level, TransitAnalysis.Level):
      raise TypeError(f'Expected Level, got {type(level)}')
    if level not in TransitAnalysis._ALL_LEVELS:
      raise ValueError(f'Unsupported level: {level}')
    self._check_transits(transits)

    transit_ganzhis = transits.ganzhis
    transit_tg = tuple(gz.tiangan for gz in transit_ganzhis)
    transit_dz = tuple(gz.dizhi for gz in transit_ganzhis)

    at_birth_tg = self._chart.bazi.four_tiangans
    at_birth_dz = self._chart.bazi.four_dizhis
    at_birth_ganzhis = self._chart.bazi.pillars
    school: Final[BaziSchool] = self._chart.bazi.config.school
    stars = self._chart.relationship_stars

    tg = tiangan_utils.TianganRelationDiscovery({})
    dz = dizhi_utils.DizhiRelationDiscovery({})
    gong_dz = dizhi_utils.DizhiRelationDiscovery({})
    if level & TransitAnalysis.Level.TRANSITS_ONLY:
      tg = tg.merge(tiangan_utils.discover(transit_tg))
      dz = dz.merge(_dz_discover(school, transit_dz))
      gong_dz = gong_dz.merge(_project_gong(
        _dz_discover_ganzhis(school, transit_ganzhis),
        lambda _: True,
      ))
    if level & TransitAnalysis.Level.MUTUAL:
      tg = tg.merge(tiangan_utils.discover_mutual(at_birth_tg, transit_tg))
      dz = dz.merge(_dz_discover_mutual(school, at_birth_dz, transit_dz))
      gong_dz = gong_dz.merge(_project_gong(
        _dz_discover_mutual_ganzhis(school, at_birth_ganzhis, transit_ganzhis),
        lambda _: True,
      ))
    dz = _with_gong(dz, gong_dz)

    return GanzhiData(
      tg.filter(lambda _, combo : stars.tiangan in combo),
      dz.filter(lambda _, combo : any(dz in combo for dz in stars.dizhi)),
    )
  
  def zhengyin(self, transits: TransitSet) -> GanzhiData[bool, bool]:
    '''
    Check if the transits' Tiangans and Dizhis contain Zhengyin (正印).

    检查流运的天干地支是否包含正印，即是否在走正印运。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns: (GanzhiData[bool, bool]) Whether the transits' Tiangans and Dizhis contain Zhengyin (正印).
    '''

    self._check_transits(transits)

    f = functools.partial(bazi_utils.shishen, self._chart.bazi.day_master)
    transit_ganzhis = transits.ganzhis

    return GanzhiData(
      any(f(gz.tiangan) is Shishen.正印 for gz in transit_ganzhis),
      any(f(gz.dizhi)   is Shishen.正印 for gz in transit_ganzhis),
    )
  
  def star(self, transits: TransitSet) -> GanzhiData[bool, bool]:
    '''
    Check if the transits' Tiangans and Dizhis contain the Star(s) of Relationship.

    检查流运的天干地支是否包含夫妻星/婚姻星。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns: (GanzhiData[bool, bool]) Whether the transits' Tiangans and Dizhis contain the Star(s) of Relationship.
    '''

    self._check_transits(transits)

    stars = self._chart.relationship_stars
    transit_ganzhis = transits.ganzhis

    return GanzhiData(
      any(gz.tiangan is stars.tiangan for gz in transit_ganzhis),
      any(gz.dizhi   in stars.dizhi   for gz in transit_ganzhis),
    )



class RelationshipAnalyzer:
  '''A thin wrapper of `AtBirthAnalysis` and `TransitAnalysis`.'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @functools.cached_property
  def at_birth(self) -> AtBirthAnalysis:
    return AtBirthAnalysis(self._chart)

  @functools.cached_property
  def transits(self) -> TransitAnalysis:
    return TransitAnalysis(self._chart)
