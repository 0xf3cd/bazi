# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''原局与所选流运的关系、神煞及结构证据。

RelationshipAnalyzer 组合原局与流运查询；结果描述结构事实，不预测现实事件。'''

import functools

from dataclasses import dataclass
from enum import Enum, IntFlag, auto, unique
from itertools import combinations, product
from typing import Final, Literal, TypedDict, assert_never, cast
from collections.abc import Callable, Iterable, Sequence

from ..common import frozendict
from ..data_types import GanzhiData
from ..defines import Tiangan, Dizhi, Ganzhi, Shishen, DizhiRelation, TianganRelation
from ..rules import DizhiRules
from ..school import Anchor, BaziSchool
from ..bazi import Bazi
from ..bazi_chart import BaziChart, _check_chart
from ..transits import TransitKind, TransitSet
from ..utils import bazi_utils, shensha_utils, tiangan_utils, dizhi_utils
from ..utils.bazi_utils import hidden_tiangans


'''从命盘流派解析神煞判断函数的可选 definition 参数。'''
_DefinitionResolver = Callable[[BaziSchool], object]


@unique
class _AnchorKind(Enum):
  '''神煞查法取锚柱的天干、地支或完整干支。'''
  TIANGAN = auto()
  DIZHI   = auto()
  GANZHI  = auto()


'''各 Anchor 选择的柱位序号，按年、月、日、时排序。'''
_ANCHOR_PILLARS: Final[frozendict[Anchor, tuple[int, ...]]] = frozendict({
  Anchor.YEAR:         (0,),
  Anchor.DAY:          (2,),
  Anchor.YEAR_AND_DAY: (0, 2),
})

'''在流派有分歧处，从命盘流派解析神煞锚柱。'''
_AnchorResolver = Callable[[BaziSchool], Anchor]


@dataclass(frozen=True)
class _ShenshaSpec:
  '''
  神煞的规格：判断函数、查法锚、展示标签，以及可选的流派定义参数。

  kind 指定取锚柱天干、地支或完整干支；anchor 指定锚柱，无分歧时为固定 Anchor，
  有分歧时为读取命盘选项的解析函数。两者均须依该神煞自身出处，不能沿用既有神煞作默认，见 #167。

  Note:
  - predicate 的首参数类型须与 kind 一致；给定 definition 时，须通过同名仅关键字参数接收解析结果。
    各判断函数在运行时校验，注册表类型不能表达此契约。
  - label 是展示名，经 SHENSHA_LABELS 供渲染方使用，不参与查法。
  '''
  predicate:  Callable[..., bool]
  kind:       _AnchorKind
  anchor:     Anchor | _AnchorResolver
  label:      str
  definition: _DefinitionResolver | None = None


'''亲密关系分析支持的地支结果神煞注册表。'''
_REGISTRY: Final[frozendict[str, _ShenshaSpec]] = frozendict({
  # 桃花不设旋钮：《命理探源》的日支桃花另有纳音条件且只查月、时，只切锚会造出出处未言的规则。
  'taohua'     : _ShenshaSpec(shensha_utils.taohua,      _AnchorKind.DIZHI,   Anchor.YEAR_AND_DAY, '桃花'),
  'hongluan'   : _ShenshaSpec(shensha_utils.hongluan,    _AnchorKind.DIZHI,   Anchor.YEAR, '红鸾'),
  'hongyan'    : _ShenshaSpec(shensha_utils.hongyan,     _AnchorKind.TIANGAN, lambda school: school.hongyan_anchor, '红艳'),
  'tianxi'     : _ShenshaSpec(shensha_utils.tianxi,      _AnchorKind.DIZHI,   Anchor.YEAR, '天喜'),
  'yima'       : _ShenshaSpec(shensha_utils.yima,        _AnchorKind.DIZHI,   lambda school: school.yima_anchor, '驿马'),
  'huagai'     : _ShenshaSpec(shensha_utils.huagai,      _AnchorKind.DIZHI,   lambda school: school.huagai_anchor, '华盖'),
  'yangren'    : _ShenshaSpec(
    shensha_utils.yangren,
    _AnchorKind.TIANGAN,
    Anchor.DAY,
    '羊刃',
    lambda school: school.yangren_def,
  ),
  'feiren'     : _ShenshaSpec(
    shensha_utils.feiren,
    _AnchorKind.TIANGAN,
    Anchor.DAY,
    '飞刃',
    lambda school: school.feiren_def,
  ),
  'tianyi'     : _ShenshaSpec(
    shensha_utils.tianyi,
    _AnchorKind.TIANGAN,
    lambda school: school.tianyi_anchor,
    '天乙贵人',
    lambda school: school.tianyi_def,
  ),
  'jiangxing'  : _ShenshaSpec(shensha_utils.jiangxing,   _AnchorKind.DIZHI,   lambda school: school.jiangxing_anchor, '将星'),
  'zaisha'     : _ShenshaSpec(shensha_utils.zaisha,      _AnchorKind.DIZHI,   lambda school: school.zaisha_anchor, '灾煞'),
  'jiesha'     : _ShenshaSpec(shensha_utils.jiesha,      _AnchorKind.DIZHI,   lambda school: school.jiesha_anchor, '劫煞'),
  'wangshen'   : _ShenshaSpec(shensha_utils.wangshen,    _AnchorKind.DIZHI,   lambda school: school.wangshen_anchor, '亡神'),
  'guchen'     : _ShenshaSpec(shensha_utils.guchen,      _AnchorKind.DIZHI,   Anchor.YEAR, '孤辰'),
  'guasu'      : _ShenshaSpec(shensha_utils.guasu,       _AnchorKind.DIZHI,   Anchor.YEAR, '寡宿'),
  'lushen'     : _ShenshaSpec(shensha_utils.lushen,      _AnchorKind.TIANGAN, Anchor.DAY, '禄神'),
  'jinyu'      : _ShenshaSpec(shensha_utils.jinyu,       _AnchorKind.TIANGAN, lambda school: school.jinyu_anchor, '金舆'),
  # 文昌与文昌贵是两颗星，不是一颗星的两种读法；两表的重合面写在 `ShenshaRules.WENCHANGGUI`。
  'wenchang'   : _ShenshaSpec(
    shensha_utils.wenchang,
    _AnchorKind.TIANGAN,
    lambda school: school.wenchang_anchor,
    '文昌',
    lambda school: school.wenchang_def,
  ),
  'wenchanggui': _ShenshaSpec(shensha_utils.wenchanggui, _AnchorKind.TIANGAN, Anchor.YEAR, '文昌贵'),
  # 太极贵人一干所对地支数不一（戊己占四库）。多支是 predicate 内部的事，
  # 注册表与分析结果的形状不变。
  'taiji'      : _ShenshaSpec(
    shensha_utils.taiji,
    _AnchorKind.TIANGAN,
    lambda school: school.taiji_anchor,
    '太极贵人',
    lambda school: school.taiji_def,
  ),
  # 国印贵人两读共用一个旋钮，无一格重合，详见 `ShenshaRules.GuoyinDef`。
  'guoyin'     : _ShenshaSpec(
    shensha_utils.guoyin,
    _AnchorKind.TIANGAN,
    lambda school: school.guoyin_anchor,
    '国印贵人',
    lambda school: school.guoyin_def,
  ),
  'kongwang'   : _ShenshaSpec(shensha_utils.kongwang, _AnchorKind.GANZHI, lambda school: school.kongwang_anchor, '空亡'),
})


'''按注册序提供神煞展示标签，供渲染方使用；
从注册表推导，新增条目无需维护第二份列表。'''
SHENSHA_LABELS: Final[frozendict[str, str]] = frozendict({
  name: spec.label for name, spec in _REGISTRY.items()
})


def _anchor_keys(spec: _ShenshaSpec, bazi: Bazi) -> tuple[tuple[int, Tiangan | Dizhi | Ganzhi], ...]:
  '''该神煞在本盘上的柱位序号与查询值，按年、月、日、时排序。'''
  anchor = spec.anchor if isinstance(spec.anchor, Anchor) else spec.anchor(bazi.config.school)
  pillars = bazi.pillars
  if spec.kind is _AnchorKind.TIANGAN:
    return tuple((index, pillars[index].tiangan) for index in _ANCHOR_PILLARS[anchor])
  elif spec.kind is _AnchorKind.DIZHI:
    return tuple((index, pillars[index].dizhi) for index in _ANCHOR_PILLARS[anchor])
  elif spec.kind is _AnchorKind.GANZHI:
    return tuple((index, pillars[index]) for index in _ANCHOR_PILLARS[anchor])
  else:
    assert_never(spec.kind) # pragma: no cover # _AnchorKind 的全部成员已在上方分派。


def _shensha_predicate(spec: _ShenshaSpec, school: BaziSchool) -> Callable[..., bool]:
  '''存在流派定义参数时，按盘绑定该参数。'''
  if spec.definition is None:
    return spec.predicate
  definition = spec.definition(school)
  return functools.partial(spec.predicate, definition=definition)


def _eval_at_birth(spec: _ShenshaSpec, bazi: Bazi) -> frozenset[Dizhi]:
  '''在原局上判断某神煞。
  干锚查四支，支锚／整柱锚查其余三支（排除自身柱），双锚按柱各查一次。
  '''
  dizhis = bazi.four_dizhis
  keys = _anchor_keys(spec, bazi)

  predicate = _shensha_predicate(spec, bazi.config.school)
  return frozenset(
    dz
    for index, key in keys
    for candidate_index, dz in enumerate(dizhis)
    if spec.kind is _AnchorKind.TIANGAN or candidate_index != index
    if predicate(key, dz)
  )


def _eval_transits(spec: _ShenshaSpec, bazi: Bazi, transit_dizhis: Iterable[Dizhi]) -> frozenset[Dizhi]:
  '''在流运地支上判断某神煞。
  流运地支不可能是锚柱自身，故每个锚值均查全部流运支。
  '''
  predicate = _shensha_predicate(spec, bazi.config.school)
  return frozenset(
    dz
    for (_, key), dz in product(_anchor_keys(spec, bazi), transit_dizhis)
    if predicate(key, dz)
  )


_DAY_PILLAR_INDEX: Final[int] = 2


def _day_pillar_participates(combo: dizhi_utils.GanzhiRelationCombo) -> bool:
  '''检查组合中是否有日柱这一具体出现，不以相同地支值代替柱位。'''
  return any(occurrence.index == _DAY_PILLAR_INDEX for occurrence in combo)


def _project_gong(
  discovery: dizhi_utils.GanzhiRelationDiscovery,
  predicate: Callable[[dizhi_utils.GanzhiRelationCombo], bool],
) -> dizhi_utils.DizhiRelationDiscovery:
  '''先按具体参与柱过滤拱局，再投影地支。'''
  return dizhi_utils.GanzhiRelationDiscovery({
    relation : filtered
    for relation in DizhiRules.GONG_RELATIONS
    if len(filtered := tuple(combo for combo in discovery.get(relation, ()) if predicate(combo))) > 0
  }).to_dizhi_discovery()


def _with_gong(
  existing: dizhi_utils.DizhiRelationDiscovery,
  gong: dizhi_utils.DizhiRelationDiscovery,
) -> dizhi_utils.DizhiRelationDiscovery:
  '''加入不重叠的拱局键，不重排既有组合。'''
  assert set(existing).isdisjoint(gong)
  return dizhi_utils.DizhiRelationDiscovery({**existing, **gong})


class ShenshaAnalysis(TypedDict):
  # 桃花星所在地支。
  taohua:      frozenset[Dizhi]
  # 红艳星所在地支。
  hongyan:     frozenset[Dizhi]
  # 红鸾星所在地支。
  hongluan:    frozenset[Dizhi]
  # 天喜星所在地支。
  tianxi:      frozenset[Dizhi]
  # 驿马星所在地支。
  yima:        frozenset[Dizhi]
  # 华盖星所在地支。
  huagai:      frozenset[Dizhi]
  # 羊刃所在地支。
  yangren:     frozenset[Dizhi]
  # 飞刃所在地支。
  feiren:      frozenset[Dizhi]
  # 天乙贵人所在地支。
  tianyi:      frozenset[Dizhi]
  # 将星所在地支。
  jiangxing:   frozenset[Dizhi]
  # 灾煞所在地支。
  zaisha:      frozenset[Dizhi]
  # 劫煞所在地支。
  jiesha:      frozenset[Dizhi]
  # 亡神所在地支。
  wangshen:    frozenset[Dizhi]
  # 孤辰所在地支。
  guchen:      frozenset[Dizhi]
  # 寡宿所在地支。
  guasu:       frozenset[Dizhi]
  # 禄神所在地支。
  lushen:      frozenset[Dizhi]
  # 金舆所在地支。
  jinyu:       frozenset[Dizhi]
  # 文昌所在地支。
  wenchang:    frozenset[Dizhi]
  # 文昌贵所在地支。
  wenchanggui: frozenset[Dizhi]
  # 太极贵人所在地支。
  taiji:       frozenset[Dizhi]
  # 国印贵人所在地支。
  guoyin:      frozenset[Dizhi]
  # 六甲旬空命中的地支；逐锚二支与具体位置见 kongwang 详情。
  kongwang:    frozenset[Dizhi]


class AtBirthShenshaAnalysis(ShenshaAnalysis):
  # 魁罡日柱。
  kuigang: Ganzhi | None
  # 天赦日柱。
  tianshe: Ganzhi | None


@dataclass(frozen=True)
class KongwangHit:
  '''旬空命中的一处目标。原局保留柱位，流运保留种类；同支或同干支的不同位置不合并。

  origin 为 natal 时 pillar 是年／月／日／时且 kind 为 None；transit 时相反。
  ganzhi 保留完整目标，但查法只使用其地支，不加目标天干或纳音条件。
  '''
  origin: Literal['natal', 'transit']
  pillar: Literal['year', 'month', 'day', 'hour'] | None
  kind:   TransitKind | None
  ganzhi: Ganzhi

  def __post_init__(self) -> None:
    if not isinstance(self.ganzhi, Ganzhi):
      raise TypeError(f'Expected Ganzhi, got {type(self.ganzhi)}')
    for value, expected in ((self.ganzhi.tiangan, Tiangan), (self.ganzhi.dizhi, Dizhi)):
      if not isinstance(value, expected):
        raise TypeError(f'Expected {expected.__name__}, got {type(value)}')
    if not isinstance(self.origin, str):
      raise TypeError(f'Expected str, got {type(self.origin)}')
    if self.pillar is not None and not isinstance(self.pillar, str):
      raise TypeError(f'Expected str | None, got {type(self.pillar)}')
    if self.kind is not None and not isinstance(self.kind, TransitKind):
      raise TypeError(f'Expected TransitKind | None, got {type(self.kind)}')
    if self.origin == 'natal':
      if self.pillar not in ('year', 'month', 'day', 'hour') or self.kind is not None:
        raise ValueError('Invalid natal kongwang coordinate')
    elif self.origin == 'transit':
      if self.pillar is not None or self.kind is None:
        raise ValueError('Invalid transit kongwang coordinate')
    else:
      raise ValueError(f'Unsupported origin: {self.origin}')


@dataclass(frozen=True)
class KongwangResult:
  '''一个本命锚的旬空二支与原始命中。anchor 记录年／日来源，ganzhi 记录完整锚。

  无命中仍返回该锚及空 hits；xunkong 由已校验的完整锚计算，不另存一份可矛盾的二支。
  不判断填实、冲合解空或吉凶，也不修改目标地支及其他关系结果。
  '''
  anchor: Literal['year', 'day']
  ganzhi: Ganzhi
  hits:   tuple[KongwangHit, ...]

  def __post_init__(self) -> None:
    absent = shensha_utils.xunkong(self.ganzhi)
    if not isinstance(self.anchor, str):
      raise TypeError(f'Expected str, got {type(self.anchor)}')
    if self.anchor not in ('year', 'day'):
      raise ValueError(f'Unsupported anchor: {self.anchor}')
    if not isinstance(self.hits, tuple) or not all(isinstance(hit, KongwangHit) for hit in self.hits):
      raise TypeError(f'Expected tuple of KongwangHit, got {type(self.hits)}')
    for hit in self.hits:
      if hit.ganzhi.dizhi not in absent:
        raise ValueError('Kongwang hit is outside the anchor xunkong')
      if hit.origin == 'natal' and hit.pillar == self.anchor:
        raise ValueError('Kongwang anchor cannot inspect its own natal pillar')

  @property
  def xunkong(self) -> frozenset[Dizhi]:
    '''该完整锚所在旬的空亡二支。'''
    return shensha_utils.xunkong(self.ganzhi)


def _kongwang_results(bazi: Bazi, targets: tuple[KongwangHit, ...]) -> tuple[KongwangResult, ...]:
  '''与支集汇总共用注册表取锚和谓词；位置在投影前保留，原局按具体柱位排除自身。'''
  spec = _REGISTRY['kongwang']
  predicate = _shensha_predicate(spec, bazi.config.school)
  results = []
  for index, key in _anchor_keys(spec, bazi):
    assert isinstance(key, Ganzhi)
    anchor = cast(Literal['year', 'day'], _PILLAR_NAMES[index])
    results.append(KongwangResult(anchor, key, tuple(
      target for target in targets
      if target.origin != 'natal' or target.pillar != anchor
      if predicate(key, target.ganzhi.dizhi)
    )))
  return tuple(results)


class AtBirthAnalysis:
  '''原局亲密关系分析。'''
  def __init__(self, chart: BaziChart) -> None:
    _check_chart(chart)
    self._chart: Final[BaziChart] = chart

  def __repr__(self) -> str:
    '''交互探索用的简短摘要，内容为所持命盘的摘要；格式不是承诺。'''
    return f'AtBirthAnalysis({self._chart!r})'

  @property
  def shensha(self) -> AtBirthShenshaAnalysis:
    bazi = self._chart.bazi
    # 注册条目各存于自身键下，再加入两个整柱神煞，它们返回干支而非地支集合。
    # 推导式无法按 TypedDict 检查，由 test_analyses_are_built_from_the_registry 核对键集。
    return cast(AtBirthShenshaAnalysis, {
      **{name: _eval_at_birth(spec, bazi) for name, spec in _REGISTRY.items()},
      'kuigang'  : bazi.day_pillar if shensha_utils.kuigang(bazi.day_pillar) else None,
      'tianshe'  : bazi.day_pillar if shensha_utils.tianshe(bazi.month_commander, bazi.day_pillar) else None,
    })

  @property
  def kongwang(self) -> tuple[KongwangResult, ...]:
    '''按配置的年／日锚次序返回原局旬空详情；命中按年、月、日、时排序，排除锚自身柱。'''
    bazi = self._chart.bazi
    return _kongwang_results(bazi, tuple(
      KongwangHit('natal', pillar, None, ganzhi)
      for pillar, ganzhi in zip(_PILLAR_NAMES, bazi.pillars)
    ))

  @property
  def day_master_relations(self) -> tiangan_utils.TianganRelationDiscovery:
    '''日主与年、月、时明干的关系，按天干值汇总。

    Return: (TianganRelationDiscovery) 关系到冻结天干组合元组的不可变映射。

    Note:
    - 每个组合是无序的 frozenset，不携带柱位；同一对干在不同柱位出现时合并。
      生／克的组合也不表达方向，不能按集合迭代顺序判断谁生谁、谁克谁。
    - 有向判断使用 `tiangan_utils.sheng`／`ke`；按柱位比较时由 `chart.bazi.four_tiangans`
      取干，各柱十神见 `chart.shishen`。配偶星证据不是通用的日主关系入口。
    '''
    y_tg, m_tg, d_tg, h_tg = self._chart.bazi.four_tiangans
    return tiangan_utils.discover_mutual([d_tg], [y_tg, m_tg, h_tg])
  
  @property
  def house_relations(self) -> dizhi_utils.DizhiRelationDiscovery:
    '''婚姻宫的关系；拱局按本盘流派判断，只保留日柱这一具体出现参与的组合。'''
    # 非拱保留完整发现路径，以支持三支组合；原局上等价于日支与其余三支的跨组发现。
    # 重复日支值时，按值过滤会误收其他柱形成的拱局，因此先过滤具体参与柱，再投影。
    bazi: Final[Bazi] = self._chart.bazi
    definitions = bazi.config.school.relation_definitions

    existing = dizhi_utils.discover(bazi.four_dizhis, definitions=definitions).filter(
      lambda _, combo : self._chart.house_of_relationship in combo
    )
    gong = _project_gong(
      dizhi_utils.discover_ganzhis(
        bazi.pillars,
        definitions=definitions,
        relations=DizhiRules.GONG_RELATIONS,
      ),
      _day_pillar_participates,
    )
    return _with_gong(existing, gong)
  
  @property
  def star_relations(self) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''配偶星的天干、地支关系；拱局按本盘流派判断，只保留实支参与者含配偶星地支的组合。'''
    stars = self._chart.relationship_stars
    bazi: Final[Bazi] = self._chart.bazi
    definitions = bazi.config.school.relation_definitions

    tg = tiangan_utils.discover(bazi.four_tiangans).filter(lambda _, combo : stars.tiangan in combo)
    existing = dizhi_utils.discover(bazi.four_dizhis, definitions=definitions).filter(
      lambda _, combo : any(dz in combo for dz in stars.dizhi)
    )
    gong = _project_gong(
      dizhi_utils.discover_ganzhis(
        bazi.pillars,
        definitions=definitions,
        relations=DizhiRules.GONG_RELATIONS,
      ),
      lambda combo : any(occurrence.ganzhi.dizhi in stars.dizhi for occurrence in combo),
    )
    return GanzhiData(tg, _with_gong(existing, gong))



class TransitAnalysis:
  '''流运亲密关系分析。'''
  def __init__(self, chart: BaziChart) -> None:
    _check_chart(chart)
    self._chart: Final[BaziChart] = chart

  def __repr__(self) -> str:
    '''交互探索用的简短摘要，内容为所持命盘的摘要；格式不是承诺。'''
    return f'TransitAnalysis({self._chart!r})'

  @staticmethod
  def _check_transits(transits: object) -> None:
    if not isinstance(transits, TransitSet):
      raise TypeError(f'Expected TransitSet, got {type(transits)}')

  def shensha(self, transits: TransitSet) -> ShenshaAnalysis:
    '''
    返回给定流运的亲密关系神煞分析。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (ShenshaAnalysis) 给定流运的神煞结果。
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = tuple(gz.dizhi for gz in transit_ganzhis)

    bazi = self._chart.bazi
    # 与原局同一份名册，只是查在流运地支上；说明见原局那处。
    return cast(ShenshaAnalysis, {
      name: _eval_transits(spec, bazi, transit_dizhis) for name, spec in _REGISTRY.items()
    })

  def kongwang(self, transits: TransitSet) -> tuple[KongwangResult, ...]:
    '''本命年／日锚查所选流运支；命中依 TransitSet.items 排序，不反向以流运为锚查原局。

    Args:
    - transits: (TransitSet) 所选具名流运；错型抛 TypeError。

    Return: (tuple[KongwangResult, ...]) 逐锚详情；同干支不同流运种类分别保留，无命中也保留二支。
    '''
    self._check_transits(transits)
    return _kongwang_results(self._chart.bazi, tuple(
      KongwangHit('transit', None, kind, ganzhi) for kind, ganzhi in transits.items
    ))
  
  def day_master_relations(self, transits: TransitSet) -> tiangan_utils.TianganRelationDiscovery:
    '''
    返回日主与流运天干之间的关系。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (tiangan_utils.TianganRelationDiscovery) 日主与流运天干的关系。
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_tiangans = tuple(gz.tiangan for gz in transit_ganzhis)

    return tiangan_utils.discover_mutual([self._chart.bazi.day_master], transit_tiangans)

  def house_relations(self, transits: TransitSet) -> dizhi_utils.DizhiRelationDiscovery:
    '''
    返回配偶宫/婚姻宫与流运地支之间的关系。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (dizhi_utils.DizhiRelationDiscovery) 配偶宫与流运地支的关系。

    Note:
    - 拱局按本盘流派判断，只保留日柱这一具体出现参与的组合。
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = [gz.dizhi for gz in transit_ganzhis]

    house = self._chart.house_of_relationship
    bazi = self._chart.bazi
    definitions = bazi.config.school.relation_definitions

    # 三支组合可横跨婚姻宫、另一原局支与流运支；先查完整原局侧，再保留有流运参与的宫组合。
    # discover_mutual 按值查，只有重复的宫支值不能证明多支组合有流运参与；单支自刑则可以。
    def __is_house_transit_relation(_: DizhiRelation, combo: frozenset[Dizhi]) -> bool:
      if house not in combo:
        return False
      if len(combo) == 1:
        return house in transit_dizhis
      return not (combo - {house}).isdisjoint(transit_dizhis)

    existing = dizhi_utils.discover_mutual(
      bazi.four_dizhis,
      transit_dizhis,
      definitions=definitions,
    ).filter(__is_house_transit_relation)
    gong = _project_gong(
      dizhi_utils.discover_mutual_ganzhis(
        bazi.pillars,
        transit_ganzhis,
        definitions=definitions,
        relations=DizhiRules.GONG_RELATIONS,
      ),
      _day_pillar_participates,
    )
    return _with_gong(existing, gong)
  
  @unique
  class Level(IntFlag):
    # 只分析流运。
    TRANSITS_ONLY        = 1 << 0

    # 分析流运与原局的跨组关系。
    MUTUAL               = 1 << 1

    # 合并上述两种范围。
    ALL                  = TRANSITS_ONLY | MUTUAL

  '''level 参数支持的全部常量级别。'''
  _ALL_LEVELS: Final[tuple[Level, ...]] = (Level.TRANSITS_ONLY, Level.MUTUAL, Level.ALL)

  def star_relations(
    self,
    transits: TransitSet,
    *, level: Level = Level.ALL,
  ) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''
    返回配偶星/婚姻星与流运干支之间的关系。

    Args:
    - transits: (TransitSet) 参与分析的流运。
    - level: (Level) 分析范围。

    Return: (GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery])
    配偶星与流运干支的天干、地支关系。

    Note:
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
    definitions = self._chart.bazi.config.school.relation_definitions
    stars = self._chart.relationship_stars

    tg = tiangan_utils.TianganRelationDiscovery({})
    dz = dizhi_utils.DizhiRelationDiscovery({})
    gong_dz = dizhi_utils.DizhiRelationDiscovery({})

    if level & TransitAnalysis.Level.TRANSITS_ONLY:
      tg = tg.merge(
        tiangan_utils.discover(transit_tg),
      )
      dz = dz.merge(
        dizhi_utils.discover(transit_dz, definitions=definitions),
      )
      gong_dz = gong_dz.merge(
        dizhi_utils.discover_ganzhis(
          transit_ganzhis,
          definitions=definitions,
          relations=DizhiRules.GONG_RELATIONS,
        ).to_dizhi_discovery(),
      )

    if level & TransitAnalysis.Level.MUTUAL:
      tg = tg.merge(
        tiangan_utils.discover_mutual(at_birth_tg, transit_tg),
      )
      dz = dz.merge(
        dizhi_utils.discover_mutual(at_birth_dz, transit_dz, definitions=definitions),
      )
      gong_dz = gong_dz.merge(
        dizhi_utils.discover_mutual_ganzhis(
          at_birth_ganzhis,
          transit_ganzhis,
          definitions=definitions,
          relations=DizhiRules.GONG_RELATIONS,
        ).to_dizhi_discovery(),
      )

    dz = _with_gong(dz, gong_dz)

    return GanzhiData(
      tg.filter(lambda _, combo : stars.tiangan in combo),
      dz.filter(lambda _, combo : any(dz in combo for dz in stars.dizhi)),
    )
  
  def zhengyin(self, transits: TransitSet) -> GanzhiData[bool, bool]:
    '''
    检查流运的天干地支是否包含正印，即是否在走正印运。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (GanzhiData[bool, bool]) 天干、地支是否分别含正印。
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
    检查流运的天干地支是否包含夫妻星/婚姻星。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (GanzhiData[bool, bool]) 天干、地支是否分别含夫妻星。
    '''

    self._check_transits(transits)

    stars = self._chart.relationship_stars
    transit_ganzhis = transits.ganzhis

    return GanzhiData(
      any(gz.tiangan is stars.tiangan for gz in transit_ganzhis),
      any(gz.dizhi   in stars.dizhi   for gz in transit_ganzhis),
    )



'''非拱地支关系全集；拱局由 `DizhiRules.GONG_RELATIONS` 单独分三段求值。'''
_NON_GONG_RELATIONS: Final[tuple[DizhiRelation, ...]] = tuple(
  relation for relation in DizhiRelation if relation not in DizhiRules.GONG_RELATIONS
)

'''天干关系到明干具体出现组合的冻结映射。组合成员是 `GanzhiOccurrence`（序号属于 RelationshipEvidence 的序列契约）；
同一天干值的多处出现各成组合；组合不含方向。'''
StemRelationDiscovery = frozendict[TianganRelation, tuple[frozenset[dizhi_utils.GanzhiOccurrence], ...]]


def _discover_stem_occurrences(ganzhis: Sequence[Ganzhi]) -> StemRelationDiscovery:
  '''把值级天干发现展开为明干具体出现组合。

  对明干序列调值级 `tiangan_utils.search`，再把每个值组合展开为全部「天干值集合等于该组合」
  的出现对；同值多处出现各成组合，值级结果与此不一致（值级按值去重）。天干四关系全二元，
  不需要地支自刑的单支特例；藏干不进天干关系组合。
  '''
  occurrences = tuple(dizhi_utils.GanzhiOccurrence(index, gz) for index, gz in enumerate(ganzhis))
  stems = tuple(gz.tiangan for gz in ganzhis)

  result: dict[TianganRelation, tuple[frozenset[dizhi_utils.GanzhiOccurrence], ...]] = {}
  for relation in TianganRelation:
    pairs: list[frozenset[dizhi_utils.GanzhiOccurrence]] = []
    for combo in tiangan_utils.search(stems, relation):
      pairs.extend(
        frozenset(candidate)
        for candidate in combinations(occurrences, 2)
        if frozenset(occurrence.ganzhi.tiangan for occurrence in candidate) == combo
      )
    if pairs:
      result[relation] = tuple(pairs)
  return StemRelationDiscovery(result)


@dataclass(frozen=True)
class StarAppearance:
  '''配偶星目标干的一处实际出现；明干／藏干、原局柱位／岁运种类分开记录，重复位置不合并。'''

  origin: Literal['natal', 'transit']
  pillar: Literal['year', 'month', 'day', 'hour'] | None   # natal 才有
  kind:   TransitKind | None                               # transit 才有
  ganzhi: Ganzhi
  layer:  Literal['visible', 'hidden']
  stem:   Tiangan                                          # 恒为目标干

  def __post_init__(self) -> None:
    for value, expected in ((self.ganzhi, Ganzhi), (self.stem, Tiangan)):
      if not isinstance(value, expected):
        raise TypeError(f'Expected {expected.__name__}, got {type(value)}')
    if self.kind is not None and not isinstance(self.kind, TransitKind):
      raise TypeError(f'Expected TransitKind | None, got {type(self.kind)}')
    if not isinstance(self.origin, str):
      raise TypeError(f'Expected str, got {type(self.origin)}')
    if self.pillar is not None and not isinstance(self.pillar, str):
      raise TypeError(f'Expected str | None, got {type(self.pillar)}')
    if not isinstance(self.layer, str):
      raise TypeError(f'Expected str, got {type(self.layer)}')
    if self.origin == 'natal':
      if self.pillar not in ('year', 'month', 'day', 'hour') or self.kind is not None:
        raise ValueError('Invalid natal appearance coordinate')
    elif self.origin == 'transit':
      if self.pillar is not None or self.kind is None:
        raise ValueError('Invalid transit appearance coordinate')
    else:
      raise ValueError(f'Unsupported origin: {self.origin}')
    if self.layer not in ('visible', 'hidden'):
      raise ValueError(f'Unsupported layer: {self.layer}')
    # 目标干恒不是日主，日柱明干位不会出现目标干，无需官杀路径的「日主明干排除」特例。
    if self.layer == 'visible' and self.stem is not self.ganzhi.tiangan:
      raise ValueError('Visible stem differs from its Ganzhi')
    if self.layer == 'hidden' and self.stem not in hidden_tiangans(self.ganzhi.dizhi):
      raise ValueError('Hidden stem is absent from its Ganzhi')


@dataclass(frozen=True)
class RelationshipEvidence:
  '''一次婚恋结构查询的可核证据。

  序号契约：`house_relations`／`star_relations`／`stem_relations` 的组合成员共享一个序列——
  原局四柱为 0–3，所选岁运按 `TransitSet.items` 的固定顺序自 4 起；组合的范围由序号直接分出
  （全部 `< 4` 为原局内部，全部 `≥ 4` 为岁运内部，其余为原局×岁运）。本类没有 scope 字段，
  不声称它能单独检查范围；跨字段约束归拥有 profile 与 evidence 的 `ContextResult`。

  `transits` 是实际取得的所选岁运；原局、无坐标或全部缺失时为 `None`。
  '''

  star_target:     GanzhiData[Tiangan, tuple[Dizhi, ...]]
  appearances:     tuple[StarAppearance, ...]
  house_relations: dizhi_utils.GanzhiRelationDiscovery   # 含日柱的组合，未投影
  star_relations:  dizhi_utils.GanzhiRelationDiscovery   # 含配偶星地支参与者的组合，未投影
  stem_relations:  StemRelationDiscovery                 # 含目标干的明干组合
  transits:        TransitSet | None

  def __post_init__(self) -> None:
    if not isinstance(self.star_target, GanzhiData):
      raise TypeError(f'Expected GanzhiData, got {type(self.star_target)}')
    if not isinstance(self.appearances, tuple) or not all(
      isinstance(member, StarAppearance) for member in self.appearances
    ):
      raise TypeError(f'Expected tuple of StarAppearance, got {type(self.appearances)}')
    for value in (self.house_relations, self.star_relations):
      if not isinstance(value, dizhi_utils.GanzhiRelationDiscovery):
        raise TypeError(f'Expected GanzhiRelationDiscovery, got {type(value)}')
    if not isinstance(self.stem_relations, frozendict):
      raise TypeError(f'Expected StemRelationDiscovery, got {type(self.stem_relations)}')
    if self.transits is not None and not isinstance(self.transits, TransitSet):
      raise TypeError(f'Expected TransitSet | None, got {type(self.transits)}')


def _merge_discoveries(*discoveries: dizhi_utils.GanzhiRelationDiscovery) -> dizhi_utils.GanzhiRelationDiscovery:
  '''按键拼接多段发现结果；首个出现的关系键位保留，段内组合序保持发现顺序。

  `GanzhiRelationDiscovery` 没有 `merge`；本函数只拼键，不复制规则定义。
  三段拱局（原局内部、跨组、岁运内部）的组合序号互斥，不会产生重复组合。
  '''
  merged: dict[DizhiRelation, list[dizhi_utils.GanzhiRelationCombo]] = {}
  for discovery in discoveries:
    for relation, combos in discovery.items():
      merged.setdefault(relation, []).extend(combos)
  return dizhi_utils.GanzhiRelationDiscovery({
    relation: tuple(combos) for relation, combos in merged.items()
  })


def _shifted(discovery: dizhi_utils.GanzhiRelationDiscovery, offset: int) -> dizhi_utils.GanzhiRelationDiscovery:
  '''把单侧局部的组合序号平移到全局序列契约下。'''
  return dizhi_utils.GanzhiRelationDiscovery({
    relation: tuple(
      frozenset(dizhi_utils.GanzhiOccurrence(occurrence.index + offset, occurrence.ganzhi) for occurrence in combo)
      for combo in combos
    )
    for relation, combos in discovery.items()
  })


def _canonical_combos(
  combos: tuple[dizhi_utils.GanzhiRelationCombo, ...],
  predicate: Callable[[dizhi_utils.GanzhiRelationCombo], bool],
) -> tuple[dizhi_utils.GanzhiRelationCombo, ...]:
  '''保留满足谓词的组合并按序号元组升序排列；与导出契约同一顺序，记录往返后相等。'''
  return tuple(sorted(
    (combo for combo in combos if predicate(combo)),
    key=lambda combo: tuple(sorted(occurrence.index for occurrence in combo)),
  ))


_PILLAR_NAMES: Final[tuple[Literal['year', 'month', 'day', 'hour'], ...]] = ('year', 'month', 'day', 'hour')


def _star_appearances(
  pillars: tuple[Ganzhi, ...],
  transits: TransitSet | None,
  target: Tiangan,
) -> tuple[StarAppearance, ...]:
  '''逐柱逐所取岁运记录目标干的实际出现；同一位置明藏两层并存各一条。'''
  appearances: list[StarAppearance] = []
  for pillar, ganzhi in zip(_PILLAR_NAMES, pillars):
    if ganzhi.tiangan is target:
      appearances.append(StarAppearance('natal', pillar, None, ganzhi, 'visible', target))
    if target in hidden_tiangans(ganzhi.dizhi):
      appearances.append(StarAppearance('natal', pillar, None, ganzhi, 'hidden', target))
  if transits is not None:
    for kind, ganzhi in transits.items:
      if ganzhi.tiangan is target:
        appearances.append(StarAppearance('transit', None, kind, ganzhi, 'visible', target))
      if target in hidden_tiangans(ganzhi.dizhi):
        appearances.append(StarAppearance('transit', None, kind, ganzhi, 'hidden', target))
  return tuple(appearances)


def spouse_evidence(chart: BaziChart, transits: TransitSet | None) -> RelationshipEvidence:
  '''计算一次婚恋结构查询的可核证据；只读结构与位置，不判婚恋吉凶。

  求值分四段：非拱关系对 `原局＋岁运` 完整序列一次求值（序号天然全局）；拱局分原局内部
  （相邻、所拱之支不在原局）、原局×岁运（跨组柱位对）、岁运内部（相邻、局部序号 +4）三段。
  拼接后序列里的所拱之支会填实全部拱局，使本成立的单侧拱局消失，因此不能一次拼接。
  三段都不被另一侧填实抑制。

  过滤：宫证据为组合含序号 2（日柱这一具体出现，不以同值地支代替柱位）；星证据为组合中任一
  参与者的地支属配偶星地支；天干侧为明干组合含目标干。证据不投影，保留完整干支与序号。

  Args:
  - chart: (BaziChart) 待查命盘；取法与关系定义读自其流派配置。
  - transits: (TransitSet | None) 实际取得的所选岁运；`None` 表示只查原局。

  Return: (RelationshipEvidence) 目标、出现与三类关系证据。
  '''
  _check_chart(chart)
  if transits is not None and not isinstance(transits, TransitSet):
    raise TypeError(f'Expected TransitSet | None, got {type(transits)}')

  bazi = chart.bazi
  pillars = bazi.pillars
  transit_ganzhis = () if transits is None else transits.ganzhis
  seq = pillars + transit_ganzhis
  definitions = bazi.config.school.relation_definitions

  merged = _merge_discoveries(
    dizhi_utils.discover_ganzhis(seq, definitions=definitions, relations=_NON_GONG_RELATIONS),
    dizhi_utils.discover_ganzhis(pillars, definitions=definitions, relations=DizhiRules.GONG_RELATIONS),
    dizhi_utils.discover_mutual_ganzhis(
      pillars, transit_ganzhis, definitions=definitions, relations=DizhiRules.GONG_RELATIONS,
    ),
    _shifted(
      dizhi_utils.discover_ganzhis(
        transit_ganzhis, definitions=definitions, relations=DizhiRules.GONG_RELATIONS,
      ),
      len(pillars),
    ),
  )

  star_target = chart.relationship_stars
  # 过滤保持具体组合与序号，不投影；GanzhiRelationDiscovery 没有值级 filter，
  # 用与 RelationDiscovery.filter 同语义的键内过滤（无组合的关系整键丢弃）。

  def __star_combo(combo: dizhi_utils.GanzhiRelationCombo) -> bool:
    return any(occurrence.ganzhi.dizhi in star_target.dizhi for occurrence in combo)

  def __stem_combo(combo: frozenset[dizhi_utils.GanzhiOccurrence]) -> bool:
    return any(occurrence.ganzhi.tiangan is star_target.tiangan for occurrence in combo)

  house_relations = dizhi_utils.GanzhiRelationDiscovery({
    relation : filtered
    for relation, combos in merged.items()
    if len(filtered := _canonical_combos(combos, _day_pillar_participates)) > 0
  })
  star_relations = dizhi_utils.GanzhiRelationDiscovery({
    relation : filtered
    for relation, combos in merged.items()
    if len(filtered := _canonical_combos(combos, __star_combo)) > 0
  })
  stem_relations = StemRelationDiscovery({
    relation : filtered
    for relation, combos in _discover_stem_occurrences(seq).items()
    if len(filtered := _canonical_combos(combos, __stem_combo)) > 0
  })

  return RelationshipEvidence(
    star_target,
    _star_appearances(pillars, transits, star_target.tiangan),
    house_relations,
    star_relations,
    stem_relations,
    transits,
  )


class RelationshipAnalyzer:
  '''组合 AtBirthAnalysis 与 TransitAnalysis 的亲密关系分析入口。'''
  def __init__(self, chart: BaziChart) -> None:
    _check_chart(chart)
    self._chart: Final[BaziChart] = chart

  def __repr__(self) -> str:
    '''交互探索用的简短摘要，内容为所持命盘的摘要；格式不是承诺。'''
    return f'RelationshipAnalyzer({self._chart!r})'

  @functools.cached_property
  def at_birth(self) -> AtBirthAnalysis:
    return AtBirthAnalysis(self._chart)

  @functools.cached_property
  def transits(self) -> TransitAnalysis:
    return TransitAnalysis(self._chart)
