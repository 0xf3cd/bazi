# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''仓内原作参考文字的显式范围前提判别；不判断现实事件、力量或有效制化。'''

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime
from enum import Enum
from typing import Any, Final, Literal, NamedTuple, TypeVar, get_args

from .bazi import BaziGender, LocationTimeJson, _parse_location
from .bazi_chart import BaziChart, _check_chart
from .common import frozendict
from .data_types import GanzhiData
from .defines import Dizhi, Ganzhi, Tiangan, Shishen, DizhiRelation, TianganRelation
from .analyzer.relationship import RelationshipEvidence, StarAppearance, StemRelationDiscovery, spouse_evidence
from .knowledge import KnowledgeBase, KnowledgeEntry
from ._validation import _text, _choice, _mapping, _pairs, _tuple
from .school import BaziConfig, BaziSchool, _config_json
from .transit_chart import TransitChart
from .transits import TransitKind, TransitSet
from .utils.bazi_utils import hidden_tiangans, shishen
from .utils.dizhi_utils import GanzhiOccurrence, GanzhiRelationDiscovery


'''完整前提判别，独立于知识整理状态。'''
MatchStatus = Literal['SATISFIED', 'NOT_SATISFIED', 'UNKNOWN']

'''判据或条目判别的理由。'''
MatchReason = Literal[
  'premise_satisfied', 'required_classification_absent', 'day_master_differs', 'female_gate_false',
  'missing_transit_coordinate', 'transit_unavailable', 'binding_unrecognized',
]

'''观察范围，无隐式默认值。'''
ObservationScope = Literal['natal', 'natal_and_liunian']

'''婚恋判据的观察范围。'''
RelationshipScope = Literal['natal', 'natal_and_transits']

'''显式岁运查询的入口。'''
TransitEntry = Literal['at_year', 'at_month', 'at_date', 'at_moment']

'''有序观察查询中的位置。'''
Pillar = Literal['year', 'month', 'day', 'hour', 'liunian']

_T = TypeVar('_T')
_PILLARS: Final[tuple[Pillar, ...]] = ('year', 'month', 'day', 'hour')
_RECORD_VERSION: Final = 4

'''各入口结构上能取得的流运种类；取得与否还取决于命盘与后端，这张表只是上限。'''
_ENTRY_KINDS: Final[frozendict[TransitEntry, frozenset[TransitKind]]] = frozendict({
  'at_year':   frozenset((TransitKind.XIAOYUN, TransitKind.DAYUN, TransitKind.LIUNIAN)),
  'at_month':  frozenset((TransitKind.XIAOYUN, TransitKind.DAYUN, TransitKind.LIUNIAN, TransitKind.LIUYUE)),
  'at_date':   frozenset((TransitKind.XIAOYUN, TransitKind.DAYUN, TransitKind.LIUNIAN, TransitKind.LIUYUE, TransitKind.LIURI)),
  'at_moment': frozenset((TransitKind.XIAOYUN, TransitKind.DAYUN, TransitKind.LIUNIAN, TransitKind.LIUYUE, TransitKind.LIURI)),
})

'''各入口必填的坐标字段；其余坐标字段在该入口出现即是请求形错误。'''
_ENTRY_FIELDS: Final[frozendict[TransitEntry, tuple[str, ...]]] = frozendict({
  'at_year':   ('gz_year',),
  'at_month':  ('gz_year', 'gz_month'),
  'at_date':   ('solar_date',),
  'at_moment': ('solar_moment',),
})


class _Criterion(NamedTuple):
  definition:      str
  claims:          tuple[str, ...]
  profile_kind:    Literal['context', 'relationship']
  # premise：条目前提即本判据，条目以 `EntryMatch` 判别；condition：判据只判可计算事实，
  # 条目文字另含程序不判的条件，条目以 `RelatedEntry` 作条件参考返回。
  entry_role:      Literal['premise', 'condition']
  female_required: bool


_GUANSHA: Final = 'editorial.guansha_coexistence.v1'
_FEMALE: Final = 'editorial.guansha_coexistence_female.v1'
_PALACE: Final = 'editorial.spouse_palace_xingchong.v1'
_TOUGAN: Final = 'editorial.spouse_star_tougan.v1'
_DING: Final = 'tiangan.ding_weak_and_overcontrolled'
_GENG: Final = 'tiangan.geng_regulated_transit'
_PIANYIN: Final = 'shishen.pianyin_favorable_or_balanced'
_XIAOYIN: Final = 'shishen.xiaoyin_duoshi'

_CRITERIA: Final[frozendict[str, _Criterion]] = frozendict({
  _GUANSHA: _Criterion('选定范围内正官与七杀各至少出现一次。', (
    'editorial.shishen.zhengguan.legal_trouble', 'editorial.shishen.qisha.legal_trouble',
  ), 'context', 'premise', False),
  _FEMALE: _Criterion('选定范围内正官与七杀各至少出现一次，且输入为女命。', (
    'editorial.shishen.zhengguan.infidelity', 'editorial.shishen.qisha.infidelity',
  ), 'context', 'premise', True),
  _DING: _Criterion('日主为丁火；身弱、克太多留在条目文字中，程序不判别。', (
    'legacy.tiangan.ding.weak_state',
  ), 'context', 'condition', False),
  _GENG: _Criterion('日主为庚金；行运有制有化、后天有教养留在条目文字中，程序不判别；即使选了流年，也不视为条文中的行运。', (
    'legacy.tiangan.geng.regulated_transit',
  ), 'context', 'condition', False),
  _PIANYIN: _Criterion('选定范围内偏印至少出现一次；喜用、不过旺、不受刑克冲害留在条目文字中，程序不判别。', (
    'legacy.shishen.SH-199',
  ), 'context', 'condition', False),
  _XIAOYIN: _Criterion('选定范围内偏印与食神各至少出现一次；共现不等于枭印夺食，夺食是否成立留在条目文字中。', (
    'legacy.shishen.SH-066',
  ), 'context', 'condition', False),
  _PALACE: _Criterion('选定范围内，日柱地支作为具体参与者卷入刑或冲；刑按命盘流派的刑定义解释。', (
    'editorial.tanyuan.wife_palace_xingchong.v1',
  ), 'relationship', 'condition', False),
  _TOUGAN: _Criterion('选定范围内，按命盘流派配置的配偶星目标干至少有一处明干实际出现。', (
    'editorial.tanyuan.wife_star_gantou.v1',
  ), 'relationship', 'condition', False),
})

'''日主判据：观察键与所需日主。'''
_DAY_MASTER_CRITERIA: Final[frozendict[str, tuple[str, Tiangan]]] = frozendict({
  _DING: ('day_master_ding', Tiangan.丁),
  _GENG: ('day_master_geng', Tiangan.庚),
})

'''十神出现判据：观察键与所需十神，各至少出现一次；出现取自本次观察的明藏干（口径见 `evaluate_context`），不计力量。'''
_CLASS_CRITERIA: Final[frozendict[str, frozendict[str, Shishen]]] = frozendict({
  _PIANYIN: frozendict({'pianyin_observed': Shishen.偏印}),
  _XIAOYIN: frozendict({'pianyin_observed': Shishen.偏印, 'shishen_observed': Shishen.食神}),
})

'''求值与目录共用的观察键；日主与十神分类的观察键仍由各自定义表所有。'''
_OBS_COEXISTENCE: Final = 'observed_coexistence'
_OBS_FEMALE: Final = 'female'
_OBS_PALACE_CHONG: Final = 'day_pillar_in_chong'
_OBS_PALACE_XING: Final = 'day_pillar_in_xing'
_OBS_STAR_VISIBLE: Final = 'target_stem_visible'
_OBS_STAR_HIDDEN: Final = 'target_stem_hidden'


def _observation_keys(criterion_id: str) -> tuple[str, ...]:
  if criterion_id in _DAY_MASTER_CRITERIA:
    return (_DAY_MASTER_CRITERIA[criterion_id][0],)
  if criterion_id in _CLASS_CRITERIA:
    return tuple(_CLASS_CRITERIA[criterion_id])
  if criterion_id in (_GUANSHA, _FEMALE):
    return (_OBS_COEXISTENCE, _OBS_FEMALE)
  if criterion_id == _PALACE:
    return (_OBS_PALACE_CHONG, _OBS_PALACE_XING)
  if criterion_id == _TOUGAN:
    return (_OBS_STAR_VISIBLE, _OBS_STAR_HIDDEN)
  raise ValueError(f'Unsupported criterion metadata: {criterion_id}')

# 内容摘要包含完整条目及其绑定的对象、情境与来源记录，用于识别默认记录约定，不能只凭 ID 或展示词确认绑定。
_BINDINGS: Final[frozendict[str, str]] = frozendict({
  'editorial.shishen.zhengguan.legal_trouble': 'd5cc38a85c86d67b130125b7832f1c68ba9499523dc5f3069ffa4c9fe83b79c8',
  'editorial.shishen.qisha.legal_trouble': 'dfec24146c99cb472d08f13a81fa94aef179e45c1ae55ddbdd9031b11d6dd8b0',
  'editorial.shishen.zhengguan.infidelity': '521a35869f53778daf677a2666a381696eb77f8749a68057999f55a83a8b68f2',
  'editorial.shishen.qisha.infidelity': '478c85056c653e1aade39f7bbd3baa04bbf0a0ac981aa7605b5c8241455fc8ee',
  'editorial.tanyuan.wife_palace_xingchong.v1': '39f4cfac78016b9ab61e302d5286c3560b3affe5a9ebfced07ed63cd29c5b69c',
  'editorial.tanyuan.wife_star_gantou.v1': '19c0828c98c02e2d63f4d666b63e21e4fd2c38c220d28f3565851b1fd4cbecb1',
  'legacy.tiangan.ding.weak_state': 'ed2b7f071196ad84e88b8353cbad6feefb865f7dd73e4877d39a9c905673c658',
  'legacy.tiangan.geng.regulated_transit': 'd81819f4276641522e2ae51190b473e2da70ac6bf0a939d1c634081d45d2c31c',
  'legacy.shishen.SH-199': '3bedc4dc359b82d45e1e4ae155719b36efae39e104c2492dcbf8a1824cb16de0',
  'legacy.shishen.SH-066': '3b8543516b20f854f9105aad3cc9c237b7da13e5d5753a59fc424140de8c4537',
})

# 关联条目的男命门槛：女命查询不关联本条，静态查阅不受限；不在表内的条目无门槛。
# 门槛先于绑定识别，同 ID 自定义顶替不能绕过；语料侧的对照标记见各条目 limits。
_RELATED_GENDERS: Final[frozendict[str, BaziGender]] = frozendict({
  'editorial.tanyuan.wife_palace_xingchong.v1': BaziGender.MALE,
  'editorial.tanyuan.wife_star_gantou.v1':      BaziGender.MALE,
})

_STATUS_BY_REASON: Final[frozendict[MatchReason, MatchStatus]] = frozendict({
  'premise_satisfied':              'SATISFIED',
  'required_classification_absent': 'NOT_SATISFIED',
  'day_master_differs':             'NOT_SATISFIED',
  'female_gate_false':              'NOT_SATISFIED',
  'missing_transit_coordinate':     'UNKNOWN',
  'transit_unavailable':            'UNKNOWN',
  'binding_unrecognized':           'UNKNOWN',
})


def _typed(value: object, expected: type[_T]) -> _T:
  if not isinstance(value, expected):
    raise TypeError(f'Expected {expected.__name__}, got {type(value)}')
  return value


def _year(value: object) -> None:
  if value is not None and type(value) is not int:
    raise TypeError(f'Expected int | None, got {type(value)}')


def _verdict(status: MatchStatus, reason: MatchReason) -> None:
  _choice(status, get_args(MatchStatus))
  _choice(reason, get_args(MatchReason))
  if status != _STATUS_BY_REASON[reason]:
    raise ValueError('Status and reason disagree')


@dataclass(frozen=True)
class ContextProfile:
  '''显式选择原局或原局加单流年；固定包含全部实际藏干，不以藏干百分比计力量。

  Note:
  - 年份是干支年标签，不是公历时刻；缺失年份返回 UNKNOWN。
  - natal 不接年份；natal_and_liunian 只加入单个 LIUNIAN。年份须为确切 int，拒绝 bool 与子类。
  '''

  observation_scope: ObservationScope
  ganzhi_year:        int | None = None

  def __post_init__(self) -> None:
    _choice(self.observation_scope, get_args(ObservationScope))
    _year(self.ganzhi_year)
    if self.observation_scope == 'natal' and self.ganzhi_year is not None:
      raise ValueError('Natal scope cannot include a transit coordinate')


@dataclass(frozen=True)
class TransitCoordinate:
  '''一次岁运查询的入口与真实坐标；各入口字段互斥，缺字段与多余字段都是请求形错误。

  at_year／at_month 的年份是干支年标签；at_month 另需干支月；at_date 是东八区无时区公历日；
  at_moment 是东八区无时区时刻，保存请求原样（含微秒），求值按 `TransitChart` 既有规则截到秒。

  Note:
  - `gz_year` 须为确切 `int`（拒 `bool` 与子类）；`solar_date` 须 `type is date`（`datetime`
    是 `date` 子类，须拒）；`solar_moment` 须 `type is datetime` 且不带时区。
    `TransitChart` 自身的年份入口只用 `isinstance`，坐标类型必须在这一层先拦。
  - 缺本入口必填字段或带其他入口字段抛 `ValueError`。
  '''

  entry:        TransitEntry
  gz_year:      int | None = None
  gz_month:     Dizhi | None = None
  solar_date:   date | None = None
  solar_moment: datetime | None = None

  def __post_init__(self) -> None:
    _choice(self.entry, get_args(TransitEntry))
    if self.gz_year is not None and type(self.gz_year) is not int:
      raise TypeError(f'Expected int | None, got {type(self.gz_year)}')
    if self.gz_month is not None and not isinstance(self.gz_month, Dizhi):
      raise TypeError(f'Expected Dizhi | None, got {type(self.gz_month)}')
    if self.solar_date is not None and type(self.solar_date) is not date:
      raise TypeError(f'Expected date | None, got {type(self.solar_date)}')
    if self.solar_moment is not None:
      if type(self.solar_moment) is not datetime:
        raise TypeError(f'Expected datetime | None, got {type(self.solar_moment)}')
      if self.solar_moment.tzinfo is not None:
        raise ValueError('Timezone should be well-processed outside of this record')
    for name in _ENTRY_FIELDS[self.entry]:
      if getattr(self, name) is None:
        raise ValueError(f'Missing coordinate field for {self.entry}: {name}')
    for name in ('gz_year', 'gz_month', 'solar_date', 'solar_moment'):
      if name not in _ENTRY_FIELDS[self.entry] and getattr(self, name) is not None:
        raise ValueError(f'Unexpected coordinate field for {self.entry}: {name}')


@dataclass(frozen=True)
class RelationshipProfile:
  '''显式选择原局，或原局加一组按坐标查询、显式选定种类的岁运；无隐式默认。

  Note:
  - `kinds` 须为 `tuple[TransitKind, ...]`，重复与不支持抛错；`natal` 不带坐标与种类，
    `natal_and_transits` 须显式给非空 `kinds`，缺查询坐标在求值期得到 UNKNOWN。
  - 有 `coordinate` 时 `kinds` 须落在该入口结构上支持的种类内。
  - 合法但乱序的 `kinds` 在类型与重复检查后按 `TransitSet.items` 的固定种类序规范化，
    不因调用方顺序产生两份等价记录；JSON 恢复则要求记录已是规范序。
  '''

  scope:      RelationshipScope
  coordinate: TransitCoordinate | None = None
  kinds:      tuple[TransitKind, ...] = ()

  def __post_init__(self) -> None:
    _choice(self.scope, get_args(RelationshipScope))
    if self.coordinate is not None and not isinstance(self.coordinate, TransitCoordinate):
      raise TypeError(f'Expected TransitCoordinate | None, got {type(self.coordinate)}')
    if not isinstance(self.kinds, tuple):
      raise TypeError(f'Expected tuple, got {type(self.kinds)}')
    for kind in self.kinds:
      if not isinstance(kind, TransitKind):
        raise TypeError(f'Expected TransitKind, got {type(kind)}')
    if len(set(self.kinds)) != len(self.kinds):
      raise ValueError(f'Duplicate transit kinds: {self.kinds}')
    if self.scope == 'natal':
      if self.coordinate is not None or self.kinds != ():
        raise ValueError('Natal scope cannot include transit inputs')
    elif self.kinds == ():
      raise ValueError('natal_and_transits requires explicit transit kinds')
    if self.coordinate is not None and not frozenset(self.kinds) <= _ENTRY_KINDS[self.coordinate.entry]:
      raise ValueError(f'Unsupported transit kinds for {self.coordinate.entry}: {self.kinds}')
    # 规范化到 TransitSet.items 的固定种类序（即 TransitKind 声明序）。
    object.__setattr__(self, 'kinds', tuple(
      kind for kind in TransitKind if kind in frozenset(self.kinds)
    ))


@dataclass(frozen=True)
class CriterionInfo:
  '''判据的不可变查阅目录，不是一次命盘判别，也不认证条目适用于现实事件。

  Note:
  - premise 判关联条目的完整前提，condition 只判局部事实，不能据此认定条目全文前提成立。
  - claim_ids 是默认语料的约定，不保证自定义知识库有这些条目。绑定识别核对条目及其引用的
    对象、情境、来源记录的内容摘要，不以相同 ID 认证内容，也不认证条文真伪或现实适用性。
  - required_gender 是判据门槛：仅 editorial.guansha_coexistence_female.v1 要求女命，范围完整时
    男命得到 NOT_SATISFIED/female_gate_false。claim_genders 只限制关联条目；两条男命婚恋条目
    不向女命返回，不改变事实判别。普通官杀并见判据没有性别门槛。
  - observation_keys 在两个官杀判据中都保留 female，是否有性别门槛另由 required_gender 表示。
  - 直接构造只检查目录值的形状，不认证自填说明；已注册目录请从 criterion／criteria 取得。
  '''

  criterion_id:     str
  definition:       str
  profile_type:     type[ContextProfile] | type[RelationshipProfile]
  entry_role:       Literal['premise', 'condition']
  observation_keys: tuple[str, ...]
  required_gender:  BaziGender | None
  claim_ids:        tuple[str, ...]
  claim_genders:    frozendict[str, BaziGender]

  def __post_init__(self) -> None:
    for value in (self.criterion_id, self.definition):
      _text(value)
    _typed(self.profile_type, type)
    if self.profile_type not in (ContextProfile, RelationshipProfile):
      raise ValueError(f'Unsupported profile type: {self.profile_type}')
    _choice(self.entry_role, ('premise', 'condition'))
    for values in (self.observation_keys, self.claim_ids):
      _tuple(values, str)
      if not values or len(set(values)) != len(values):
        raise ValueError('Expected non-empty distinct metadata values')
    if self.required_gender is not None:
      _typed(self.required_gender, BaziGender)
    _typed(self.claim_genders, frozendict)
    for claim_id, gender in self.claim_genders.items():
      _choice(claim_id, self.claim_ids)
      _typed(gender, BaziGender)

  @property
  def profile_kind(self) -> Literal['context', 'relationship']:
    '''profile_type 对应的查阅类别。'''
    return 'context' if self.profile_type is ContextProfile else 'relationship'

  @property
  def scopes(self) -> tuple[ObservationScope | RelationshipScope, ...]:
    '''profile_type 接受的观察范围。'''
    return get_args(ObservationScope if self.profile_type is ContextProfile else RelationshipScope)

  @property
  def required_inputs(self) -> tuple[str, ...]:
    '''evaluate_context 的必填参数；profile 的构造要求另见 profile_type 与 scope_inputs。'''
    return ('chart', 'criterion_id', 'profile')

  @property
  def optional_inputs(self) -> tuple[str, ...]:
    '''evaluate_context 的可选参数；省略时沿用求值入口的默认值。'''
    return ('knowledge', 'include_reference_only')

  @property
  def scope_inputs(self) -> frozendict[str, tuple[str, ...]]:
    '''各 scope 取得完整范围的额外 profile 字段。

    关系流运范围的 kinds 在构造期必须非空；年份／坐标缺失则在求值时返回 UNKNOWN，
    不把这两种输入要求混为同一种失败。
    '''
    return frozendict({
      scope: () if scope == 'natal' else (
        ('ganzhi_year',) if self.profile_type is ContextProfile else ('coordinate', 'kinds')
      ) for scope in self.scopes
    })

  @property
  def transit_entries(self) -> frozendict[TransitEntry, tuple[str, ...]]:
    '''关系 profile 的坐标入口及必填坐标字段；ContextProfile 不接 TransitCoordinate。'''
    return _ENTRY_FIELDS if self.profile_type is RelationshipProfile else frozendict({})

  @property
  def transit_kinds(self) -> frozendict[TransitEntry, frozenset[TransitKind]]:
    '''关系坐标入口结构上支持的流运种类上限，不保证某个命盘实际可取得。'''
    return _ENTRY_KINDS if self.profile_type is RelationshipProfile else frozendict({})

  @property
  def unknown_conditions(self) -> frozendict[MatchReason, str]:
    '''CriterionResult 的 UNKNOWN 条件；绑定失败另作用于条目层，不列为事实判别原因。'''
    return frozendict({
      'missing_transit_coordinate': '选择含流运范围后未给所需年份或坐标；范围缺失先于性别门槛与事实判别。',
      'transit_unavailable': '流运查询不可用；关系范围也包括任一所求种类未取得，已取得证据仍保留。',
    })

  @property
  def binding_effect(self) -> Literal['entry_unknown', 'related_unrecognized']:
    '''绑定未识别时，premise 的 EntryMatch 为 UNKNOWN/binding_unrecognized，
    condition 的 RelatedEntry.recognized 为 False；两者均不改变 CriterionResult。
    '''
    return 'entry_unknown' if self.entry_role == 'premise' else 'related_unrecognized'


def criterion(id: str) -> CriterionInfo:
  '''按稳定 ID 查阅判据，不加载知识库、不创建命盘；未知 ID 抛 ValueError，错型抛 TypeError。'''
  _choice(id, tuple(_CRITERIA))
  registered = _CRITERIA[id]
  return CriterionInfo(
    criterion_id=id,
    definition=registered.definition,
    profile_type=ContextProfile if registered.profile_kind == 'context' else RelationshipProfile,
    entry_role=registered.entry_role,
    observation_keys=_observation_keys(id),
    required_gender=BaziGender.FEMALE if registered.female_required else None,
    claim_ids=registered.claims,
    claim_genders=frozendict({key: _RELATED_GENDERS[key] for key in registered.claims if key in _RELATED_GENDERS}),
  )


def criteria() -> frozendict[str, CriterionInfo]:
  '''返回全部已注册判据的不可变目录；每项由现有定义与 profile 契约派生。'''
  return frozendict({criterion_id: criterion(criterion_id) for criterion_id in _CRITERIA})


@dataclass(frozen=True)
class RelatedEntry:
  '''该判据的条件参考条目。关联只表示「这条文字是这个判据所选条件的参考」，不是事实已成立，
  也不是完整前提已满足；不升级来源状态或输出资格。判别状态只在 `CriterionResult` 展示。'''

  claim_id:   str
  recognized: bool   # 条目绑定摘要与 `_BINDINGS` 一致；同 ID 被自定义条目顶替时为 False

  def __post_init__(self) -> None:
    _typed(self.claim_id, str)
    if not self.claim_id.strip():
      raise ValueError('Expected non-empty claim ID')
    _typed(self.recognized, bool)


@dataclass(frozen=True)
class ChartOccurrence:
  '''一处已分类天干，保留柱位、明藏层及时间身份；重复位置不合并。'''

  origin:      Literal['natal', 'transit']
  pillar:      Pillar
  ganzhi:      Ganzhi
  layer:       Literal['visible', 'hidden']
  stem:        Tiangan
  shishen:     Shishen
  kind:        TransitKind | None = None
  ganzhi_year: int | None = None

  def __post_init__(self) -> None:
    _choice(self.origin, ('natal', 'transit'))
    _choice(self.pillar, get_args(Pillar))
    _choice(self.layer, ('visible', 'hidden'))
    for value, expected in ((self.ganzhi, Ganzhi), (self.stem, Tiangan), (self.shishen, Shishen)):
      _typed(value, expected)
    _year(self.ganzhi_year)
    if self.kind is not None:
      _typed(self.kind, TransitKind)
    if self.origin == 'natal':
      if self.pillar not in _PILLARS or self.kind is not None or self.ganzhi_year is not None:
        raise ValueError('Invalid natal occurrence coordinate')
      if self.pillar == 'day' and self.layer == 'visible':
        raise ValueError('Day-master visible stem is excluded by convention')
    elif self.pillar != 'liunian' or self.kind is not TransitKind.LIUNIAN or self.ganzhi_year is None:
      raise ValueError('Invalid LIUNIAN occurrence coordinate')
    if self.layer == 'visible' and self.stem != self.ganzhi.tiangan:
      raise ValueError('Visible stem differs from its Ganzhi')
    if self.layer == 'hidden' and self.stem not in hidden_tiangans(self.ganzhi.dizhi):
      raise ValueError('Hidden stem is absent from its Ganzhi')

  @property
  def index(self) -> int:
    '''返回有序观察查询的位置：原局四柱为0–3，流年为4。'''
    return get_args(Pillar).index(self.pillar)


@dataclass(frozen=True)
class CriterionResult:
  '''完整判别与已知局部观察分开记录，局部观察不替代缺失的范围。'''

  criterion_id:   str
  definition:     str
  status:         MatchStatus
  reason:         MatchReason
  scope_complete: bool
  observations:   frozendict[str, bool]

  def __post_init__(self) -> None:
    _choice(self.criterion_id, tuple(_CRITERIA))
    _typed(self.definition, str)
    if self.definition != _CRITERIA[self.criterion_id].definition:
      raise ValueError('Unsupported criterion definition')
    _verdict(self.status, self.reason)
    _typed(self.scope_complete, bool)
    if not self.scope_complete and self.status != 'UNKNOWN':
      raise ValueError('Incomplete scope cannot have a complete verdict')
    _typed(self.observations, frozendict)
    for name, value in self.observations.items():
      _typed(name, str)
      _typed(value, bool)


@dataclass(frozen=True)
class EntryMatch:
  '''语义绑定后的条目前提判别，独立于结构判据。'''

  claim_id: str
  status:   MatchStatus
  reason:   MatchReason

  def __post_init__(self) -> None:
    _typed(self.claim_id, str)
    if not self.claim_id.strip():
      raise ValueError('Expected non-empty claim ID')
    _verdict(self.status, self.reason)


def _validate_input(text: str) -> None:
  data = _typed(json.loads(text, object_pairs_hook=_pairs), dict)
  common_keys = {'gender', 'config', 'pillars'}
  default_keys = common_keys | {'birth_time'}
  location_keys = common_keys | LocationTimeJson.__required_keys__
  if data.keys() == location_keys:
    _parse_location(data)
  elif data.keys() == default_keys:
    _typed(data['birth_time'], str)
    birth = datetime.fromisoformat(data['birth_time'])
    if birth.tzinfo is not None or birth.second or birth.microsecond or birth.isoformat() != data['birth_time']:
      raise ValueError('Expected canonical naive minute birth time')
  else:
    raise ValueError('Expected complete default or location-aware input roster')

  _choice(data['gender'], ('male', 'female'))
  config = _mapping(data['config'], tuple(field.name for field in fields(BaziConfig)))
  BaziConfig.from_values(**{**config, 'school': BaziSchool.from_json(config['school'])})

  pillars = _typed(data['pillars'], list)
  if len(pillars) != 4:
    raise ValueError('Expected four ordered natal pillars')
  for value in pillars:
    _typed(value, str)
    Ganzhi.from_str(value)


'''见 `RelationshipEvidence` 的序列契约：原局四柱为 0–3，所选岁运自 4 起。'''
_NATAL_SEQUENCE_LENGTH: Final[int] = 4

_COORDINATE_KEYS: Final[tuple[str, ...]] = ('entry', 'gz_year', 'gz_month', 'solar_date', 'solar_moment')
_APPEARANCE_KEYS: Final[tuple[str, ...]] = ('origin', 'pillar', 'kind', 'ganzhi', 'layer', 'stem')
_RELATIONSHIP_KEYS: Final[tuple[str, ...]] = (
  'star_target', 'appearances', 'house_relations', 'star_relations', 'stem_relations', 'transits',
)

_EnumT = TypeVar('_EnumT', bound=Enum)
_RelationEnumT = TypeVar('_RelationEnumT', DizhiRelation, TianganRelation)

def _canonical_date(value: object) -> date:
  '''要求规范 ISO 日期拼写；`datetime` 串与紧凑写法回读不等，均拒。'''
  text = _typed(value, str)
  parsed = date.fromisoformat(text)
  if parsed.isoformat() != text:
    raise ValueError(f'Expected canonical ISO date: {text}')
  return parsed


def _canonical_moment(value: object) -> datetime:
  '''要求无时区、保留请求原样（含微秒）的规范时刻；空格分隔、`…15.25`、带偏移均拒。'''
  text = _typed(value, str)
  parsed = datetime.fromisoformat(text)
  if parsed.tzinfo is not None or parsed.isoformat() != text:
    raise ValueError(f'Expected canonical naive moment: {text}')
  return parsed


def _restore_kinds(value: object) -> tuple[TransitKind, ...]:
  '''恢复种类列表：逐个成员复核、查重，且须已是固定种类序，非规范序拒绝。'''
  kinds: list[TransitKind] = []
  for item in _typed(value, list):
    text = _typed(item, str)
    try:
      kinds.append(TransitKind(text))
    except ValueError:
      raise ValueError(f'Unsupported TransitKind: {text}') from None
  if len(set(kinds)) != len(kinds):
    raise ValueError(f'Duplicate transit kinds: {kinds}')
  canonical = tuple(kind for kind in TransitKind if kind in set(kinds))
  if tuple(kinds) != canonical:
    raise ValueError(f'Expected transit kinds in the canonical order, got {kinds}')
  return canonical


def _restore_coordinate(value: object) -> TransitCoordinate:
  data = _typed(value, dict)
  _mapping(data, _COORDINATE_KEYS)
  gz_year = data['gz_year']
  if gz_year is not None and type(gz_year) is not int:
    raise TypeError(f'Expected int | None, got {type(gz_year)}')
  return TransitCoordinate(
    data['entry'],
    gz_year,
    None if data['gz_month'] is None else Dizhi.from_str(_typed(data['gz_month'], str)),
    None if data['solar_date'] is None else _canonical_date(data['solar_date']),
    None if data['solar_moment'] is None else _canonical_moment(data['solar_moment']),
  )


def _restore_relationship_profile(data: dict[str, Any]) -> RelationshipProfile:
  coordinate = None if data['coordinate'] is None else _restore_coordinate(data['coordinate'])
  return RelationshipProfile(data['scope'], coordinate, _restore_kinds(data['kinds']))


def _export_relation_combos(
  discovery: Mapping[_EnumT, tuple[frozenset[GanzhiOccurrence], ...]],
  declarations: tuple[_EnumT, ...],
) -> dict[str, list[list[dict[str, object]]]]:
  '''关系键按枚举声明序、组合按序号元组升序导出，同一结果字节稳定。'''
  exported: dict[str, list[list[dict[str, object]]]] = {}
  for relation in declarations:
    combos = discovery.get(relation)
    if combos is None:
      continue
    exported[relation.value] = [
      [
        {'index': occurrence.index, 'ganzhi': str(occurrence.ganzhi)}
        for occurrence in sorted(combo, key=lambda occurrence: occurrence.index)
      ]
      for combo in sorted(combos, key=lambda combo: tuple(sorted(occurrence.index for occurrence in combo)))
    ]
  return exported


def _restore_relation_combos(
  value: object,
  relation_type: type[_RelationEnumT],
) -> dict[_RelationEnumT, tuple[frozenset[GanzhiOccurrence], ...]]:
  data = _typed(value, dict)
  result: dict[_RelationEnumT, tuple[frozenset[GanzhiOccurrence], ...]] = {}
  for key, combos in data.items():
    relation = relation_type.from_str(_typed(key, str))
    restored: list[frozenset[GanzhiOccurrence]] = []
    for combo in _typed(combos, list):
      members: list[GanzhiOccurrence] = []
      for member in _typed(combo, list):
        item = _mapping(member, ('index', 'ganzhi'))
        index = item['index']
        if type(index) is not int:
          raise TypeError(f'Expected int, got {type(index)}')
        if index < 0:
          raise ValueError(f'Expected a non-negative index, got {index}')
        members.append(GanzhiOccurrence(index, Ganzhi.from_str(_typed(item['ganzhi'], str))))
      restored.append(frozenset(members))
    # 组合外层序按导出的同一排序键（序号元组升序）核对，非规范序拒绝；
    # 关系键序与组合内成员序由映射与不可变集合吸收，不在此收紧。
    order = [tuple(sorted(occurrence.index for occurrence in combo)) for combo in restored]
    if order != sorted(order):
      raise ValueError(f'Expected combos in the canonical order, got {order}')
    result[relation] = tuple(restored)
  return result


def _restore_transits(value: object) -> TransitSet | None:
  if value is None:
    return None
  data = _typed(value, dict)
  kinds = _restore_kinds(list(data))
  return TransitSet(**{
    kind.value: Ganzhi.from_str(_typed(data[kind.value], str))
    for kind in kinds
  })


def _restore_relationship(value: object) -> RelationshipEvidence:
  data = _typed(value, dict)
  _mapping(data, _RELATIONSHIP_KEYS)
  target = _mapping(data['star_target'], ('tiangan', 'dizhi'))
  appearances = []
  for item in _typed(data['appearances'], list):
    record = _mapping(item, _APPEARANCE_KEYS)
    kind = None if record['kind'] is None else _transit_kind(record['kind'])
    appearances.append(StarAppearance(
      record['origin'],
      record['pillar'],
      kind,
      Ganzhi.from_str(_typed(record['ganzhi'], str)),
      record['layer'],
      Tiangan.from_str(_typed(record['stem'], str)),
    ))
  return RelationshipEvidence(
    GanzhiData(
      Tiangan.from_str(_typed(target['tiangan'], str)),
      tuple(Dizhi.from_str(_typed(dz, str)) for dz in _typed(target['dizhi'], list)),
    ),
    tuple(appearances),
    GanzhiRelationDiscovery(_restore_relation_combos(data['house_relations'], DizhiRelation)),
    GanzhiRelationDiscovery(_restore_relation_combos(data['star_relations'], DizhiRelation)),
    StemRelationDiscovery(_restore_relation_combos(data['stem_relations'], TianganRelation)),
    _restore_transits(data['transits']),
  )


def _transit_kind(value: object) -> TransitKind:
  '''恢复岁运种类；这是 `StarAppearance` 的五值白名单，与原局／流年观察的 `('liunian',)` 是两份白名单。'''
  _choice(value, tuple(kind.value for kind in TransitKind))
  return TransitKind(value)


@dataclass(frozen=True)
class ContextResult:
  '''保存判别、证据及条目的不可变结果；婚恋结果另存结构证据，条件判据另存条件参考条目。

  复用传入的已验证 KnowledgeBase，渲染不重建知识对象。JSON 保留判据、profile、
  完整出生／性别／配置身份、年份／坐标／种类、全部观察、证据、输入与知识快照。
  地点输入使用与命盘 JSON 相同的五个字段，保留固定民用基准及未截断真太阳钟。

  Note:
  - 婚恋 profile 的结果 `occurrences` 恒为空，原局／流年 profile 不带 `relationship`；
    前提判据（官杀两条）不带 `related`，条件判据的 `entries` 恒为空。构造期校验字段间
    结构自洽，但不重算或认证命盘、判别、证据真伪，也不认证输入与证据干支的一致性。
  '''

  profile:        ContextProfile | RelationshipProfile
  criterion:      CriterionResult
  occurrences:    tuple[ChartOccurrence, ...]
  relationship:   RelationshipEvidence | None
  related:        tuple[RelatedEntry, ...]
  entries:        tuple[EntryMatch, ...]
  input_json:     str
  knowledge:      KnowledgeBase

  def __post_init__(self) -> None:
    if not isinstance(self.profile, (ContextProfile, RelationshipProfile)):
      raise TypeError(f'Expected ContextProfile | RelationshipProfile, got {type(self.profile)}')
    _typed(self.criterion, CriterionResult)
    _tuple(self.occurrences, ChartOccurrence)
    if self.relationship is not None and not isinstance(self.relationship, RelationshipEvidence):
      raise TypeError(f'Expected RelationshipEvidence | None, got {type(self.relationship)}')
    _tuple(self.related, RelatedEntry)
    _tuple(self.entries, EntryMatch)
    _typed(self.input_json, str)
    _validate_input(self.input_json)
    _typed(self.knowledge, KnowledgeBase)
    for match in self.entries:
      self.knowledge.entry(match.claim_id)
    for related in self.related:
      self.knowledge.entry(related.claim_id)

    criterion = _CRITERIA[self.criterion.criterion_id]
    profile_kind = 'relationship' if isinstance(self.profile, RelationshipProfile) else 'context'
    if criterion.profile_kind != profile_kind:
      raise ValueError('Criterion profile kind disagrees with the profile type')
    if criterion.entry_role == 'premise' and self.related != ():
      raise ValueError('Premise criterion cannot carry condition references')
    if criterion.entry_role == 'condition' and self.entries != ():
      raise ValueError('Condition criterion cannot carry premise matches')

    if isinstance(self.profile, RelationshipProfile):
      relationship = self.relationship
      if relationship is None or self.occurrences != ():
        raise ValueError('Relationship profile requires evidence without occurrences')
      if self.profile.scope == 'natal' and relationship.transits is not None:
        raise ValueError('Natal scope cannot carry obtained transits')
      # 取得集合在 None 时为空；完整范围要求坐标与实际取得的岁运，取得集合恰等于非空所求。
      obtained = frozenset() if relationship.transits is None else frozenset(relationship.transits)
      if not obtained <= frozenset(self.profile.kinds):
        raise ValueError('Obtained transit kinds exceed the requested kinds')
      if self.profile.scope == 'natal_and_transits' and self.criterion.scope_complete:
        if self.profile.coordinate is None or relationship.transits is None:
          raise ValueError('Complete scope requires a queried coordinate and obtained transits')
        if obtained != frozenset(self.profile.kinds):
          raise ValueError('Complete scope must obtain every requested kind')
      limit = _NATAL_SEQUENCE_LENGTH if relationship.transits is None else _NATAL_SEQUENCE_LENGTH + len(relationship.transits.items)
      for discovery in (relationship.house_relations, relationship.star_relations, relationship.stem_relations):
        for combos in discovery.values():
          for combo in combos:
            if any(occurrence.index >= limit for occurrence in combo):
              raise ValueError('Evidence index exceeds the queried sequence')
    elif self.relationship is not None:
      raise ValueError('Context profile cannot carry relationship evidence')

  def export_json(self) -> str:
    '''导出版本4记录、全部证据及知识注册表，不改变参考输出资格。

    原局／流年记录显式带 `relationship: null`，空的 `entries`／`related` 写空列表，不省键。
    婚恋证据的关系键按枚举声明序、组合按序号元组升序导出，同一结果字节稳定。
    '''
    profile: object
    if isinstance(self.profile, RelationshipProfile):
      coordinate = self.profile.coordinate
      coordinate_json: object = None
      if coordinate is not None:
        coordinate_json = {
          'entry':        coordinate.entry,
          'gz_year':      coordinate.gz_year,
          'gz_month':     None if coordinate.gz_month is None else coordinate.gz_month.value,
          'solar_date':   None if coordinate.solar_date is None else coordinate.solar_date.isoformat(),
          'solar_moment': None if coordinate.solar_moment is None else coordinate.solar_moment.isoformat(),
        }
      profile = {
        'scope':      self.profile.scope,
        'coordinate': coordinate_json,
        'kinds':      [kind.value for kind in self.profile.kinds],
      }
    else:
      profile = asdict(self.profile)

    relationship: object = None
    if self.relationship is not None:
      evidence = self.relationship
      relationship = {
        'star_target': {
          'tiangan': str(evidence.star_target.tiangan),
          'dizhi':   [str(dz) for dz in evidence.star_target.dizhi],
        },
        'appearances': [
          {
            'origin':  value.origin,
            'pillar':  value.pillar,
            'kind':    None if value.kind is None else value.kind.value,
            'ganzhi':  str(value.ganzhi),
            'layer':   value.layer,
            'stem':    str(value.stem),
          }
          for value in evidence.appearances
        ],
        'house_relations': _export_relation_combos(evidence.house_relations, tuple(DizhiRelation)),
        'star_relations':  _export_relation_combos(evidence.star_relations, tuple(DizhiRelation)),
        'stem_relations':  _export_relation_combos(evidence.stem_relations, tuple(TianganRelation)),
        'transits':        None if evidence.transits is None else evidence.transits.json,
      }

    data = {
      'record_version': _RECORD_VERSION,
      'profile': profile,
      'criterion': {**asdict(self.criterion), 'observations': dict(self.criterion.observations)},
      'occurrences': [
        {**asdict(value), 'ganzhi': str(value.ganzhi), 'stem': str(value.stem), 'shishen': str(value.shishen),
         'kind': None if value.kind is None else value.kind.value}
        for value in self.occurrences
      ],
      'relationship': relationship,
      'related': [asdict(value) for value in self.related],
      'entries': [asdict(value) for value in self.entries],
      'input': json.loads(self.input_json),
      'knowledge': self.knowledge._export_data(),
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'

  @classmethod
  def from_json(cls, text: str) -> 'ContextResult':
    '''恢复版本4记录并校验结构及各值类型，不重算或认证判别、证据、输入与条目绑定间的一致性。
    旧版本记录明确拒绝；版本检查先于键集合检查，使真实 v2 记录得到版本拒绝而非键集差异。
    需要新格式时应由原输入与配置重新求值。

    Note:
    - 地点输入校验字段集合、规范拼写及民用／UTC 瞬间相等，不重算命盘或观察。
    - profile 按键集分派：`{observation_scope, ganzhi_year}` 为 `ContextProfile`，`{scope, coordinate, kinds}`
      为 `RelationshipProfile`，两者不混写；婚恋记录的坐标、种类与证据按各自规范拼写逐项复核。
    '''
    _typed(text, str)
    data = json.loads(text, object_pairs_hook=_pairs)
    if not isinstance(data, dict):
      raise TypeError(f'Expected JSON object, got {type(data)}')
    version = data.get('record_version')
    if type(version) is not int or version != _RECORD_VERSION:
      raise ValueError('Unsupported record version')
    _mapping(
      data,
      ('record_version', 'profile', 'criterion', 'occurrences', 'relationship', 'related', 'entries', 'input', 'knowledge'),
    )

    profile_data = _typed(data['profile'], dict)
    profile: ContextProfile | RelationshipProfile
    if set(profile_data) == {'observation_scope', 'ganzhi_year'}:
      profile = ContextProfile(**_mapping(data['profile'], ('observation_scope', 'ganzhi_year')))
    elif set(profile_data) == {'scope', 'coordinate', 'kinds'}:
      profile = _restore_relationship_profile(_mapping(data['profile'], ('scope', 'coordinate', 'kinds')))
    else:
      raise ValueError(f'JSON fields differ: {set(profile_data)}')

    criterion = _mapping(data['criterion'], tuple(field.name for field in fields(CriterionResult)))
    _typed(criterion['observations'], dict)
    criterion['observations'] = frozendict(criterion['observations'])
    occurrences = []
    for item in _typed(data['occurrences'], list):
      value = _mapping(item, tuple(field.name for field in fields(ChartOccurrence)))
      for name, domain in (('ganzhi', Ganzhi), ('stem', Tiangan), ('shishen', Shishen)):
        _typed(value[name], str)
        value[name] = domain.from_str(value[name])
      if value['kind'] is not None:
        _choice(value['kind'], ('liunian',))
        value['kind'] = TransitKind.LIUNIAN
      occurrences.append(ChartOccurrence(**value))
    relationship = None if data['relationship'] is None else _restore_relationship(data['relationship'])
    related = tuple(
      RelatedEntry(**_mapping(item, ('claim_id', 'recognized'))) for item in _typed(data['related'], list)
    )
    entries = tuple(EntryMatch(**_mapping(item, ('claim_id', 'status', 'reason'))) for item in _typed(data['entries'], list))

    return cls(
      profile,
      CriterionResult(**criterion),
      tuple(occurrences),
      relationship,
      related,
      entries,
      json.dumps(data['input'], ensure_ascii=False),
      KnowledgeBase._from_data(data['knowledge']),
    )

  def render(self) -> str:
    '''展示判别、证据及完整参考原文和来源限度；前提满足不表示事件成立。'''
    criterion = self.criterion
    if isinstance(self.profile, RelationshipProfile):
      return self._render_relationship()

    premise = _CRITERIA[criterion.criterion_id].entry_role == 'premise'
    verdict_label = '结构前提' if premise else '事实判别'
    lines = [
      f'判据：{criterion.criterion_id}；{criterion.definition}',
      f'范围：全部明藏干；{self.profile.observation_scope}；干支年={self.profile.ganzhi_year}',
      f'{verdict_label}：{criterion.status}；{criterion.reason}；scope_complete={criterion.scope_complete}',
      f'输入：{self.input_json}',
      '已知观察：' + json.dumps(dict(criterion.observations), ensure_ascii=False),
    ]
    if premise:
      lines.append('前提满足只表示本范围内的原作使用条件满足，不表示现实事件成立。')
    for value in self.occurrences:
      lines.append(
        f'证据：{value.origin}.{value.pillar}；{value.ganzhi}；'
        f'{value.layer}；{value.stem}={value.shishen}；'
        f'kind={None if value.kind is None else value.kind.value}；干支年={value.ganzhi_year}'
      )
    for match in self.entries:
      lines.append(f'原作参考前提：{match.claim_id}；{match.status}；{match.reason}')
      lines.append(self.knowledge.render(self.knowledge.entry(match.claim_id), premise_verdict=match.status))
    if not premise:
      lines.extend(self._render_related())
    return '\n'.join(lines)

  def _render_relationship(self) -> str:
    '''婚恋结果的三栏证据与条件参考渲染；不输出任何「某组合在全局仍有效」的结论。'''
    profile = self.profile
    assert isinstance(profile, RelationshipProfile) # 调用方已按 profile 分支。
    evidence = self.relationship
    assert evidence is not None # 构造期已核与 profile 配对。

    coordinate_text = '无'
    if profile.coordinate is not None:
      coordinate = profile.coordinate
      parts: list[str] = [coordinate.entry]
      if coordinate.gz_year is not None:
        parts.append(f'干支年={coordinate.gz_year}')
      if coordinate.gz_month is not None:
        parts.append(f'干支月={coordinate.gz_month}')
      if coordinate.solar_date is not None:
        parts.append(f'公历日={coordinate.solar_date.isoformat()}')
      if coordinate.solar_moment is not None:
        parts.append(f'时刻={coordinate.solar_moment.isoformat()}')
      coordinate_text = '；'.join(parts)
    obtained = () if evidence.transits is None else tuple(kind for kind in evidence.transits)
    requested_text = ','.join(kind.value for kind in profile.kinds)
    obtained_text = ','.join(kind.value for kind in obtained)
    missing_text = ','.join(kind.value for kind in profile.kinds if kind not in obtained)

    lines = [
      f'判据：{self.criterion.criterion_id}；{self.criterion.definition}',
      (
        f'范围：{profile.scope}；坐标={coordinate_text}；请求种类=[{requested_text}]；'
        f'取得种类=[{obtained_text}]；未取得种类=[{missing_text}]'
      ),
      f'事实判别：{self.criterion.status}；{self.criterion.reason}；scope_complete={self.criterion.scope_complete}',
      f'输入：{self.input_json}',
      '已知观察：' + json.dumps(dict(self.criterion.observations), ensure_ascii=False),
      f'配偶星：目标干={evidence.star_target.tiangan}；地支={"、".join(str(dz) for dz in evidence.star_target.dizhi)}',
    ]
    for value in evidence.appearances:
      where = value.pillar if value.kind is None else value.kind.value
      lines.append(f'证据出现：{value.origin}.{where}；{value.ganzhi}；{value.layer}；{value.stem}')

    for scope_name, in_scope in (
      ('原局内部', lambda indexes: all(index < _NATAL_SEQUENCE_LENGTH for index in indexes)),
      ('原局×岁运', lambda indexes: any(index >= _NATAL_SEQUENCE_LENGTH for index in indexes)
       and any(index < _NATAL_SEQUENCE_LENGTH for index in indexes)),
      ('岁运内部', lambda indexes: all(index >= _NATAL_SEQUENCE_LENGTH for index in indexes)),
    ):
      chunks: list[str] = []
      # 每项标宫／星／明干类别；同一组合属多类时分别列出，不合并、不改变关系与序号。
      for category, discovery in (
        ('宫', evidence.house_relations),
        ('星', evidence.star_relations),
        ('明干', evidence.stem_relations),
      ):
        for relation, combos in discovery.items():
          for combo in combos:
            indexes = tuple(occurrence.index for occurrence in combo)
            if not in_scope(indexes):
              continue
            chunks.append(f'{category}·{relation}：' + '、'.join(
              f'{occurrence.index}:{occurrence.ganzhi}'
              for occurrence in sorted(combo, key=lambda occurrence: occurrence.index)
            ))
      lines.append(f'证据：{scope_name}；' + ('；'.join(chunks) if chunks else '无'))

    lines.extend(self._render_related())
    return '\n'.join(lines)

  def _render_related(self) -> list[str]:
    '''条件判据的判别说明与条件参考；条目文字中的条件一律标为未由程序判别。'''
    lines = ['事实判别不表示原文完整条件已满足，也不表示现实事件成立。']
    header = '关联参考（该判据的条件参考，不表示事实已成立或完整前提已满足）'
    for related in self.related:
      if related.recognized:
        lines.append(f'{header}：{related.claim_id}')
        lines.append(self.knowledge.render(
          self.knowledge.entry(related.claim_id),
          premise_verdict='完整前提未由程序判别',
        ))
      else:
        # 只列 ID 与「绑定未识别」，不渲染被顶替的自定义文字。
        lines.append(f'{header}：{related.claim_id}；绑定未识别')
    return lines


def _binding_digest(knowledge: KnowledgeBase, entry: KnowledgeEntry) -> str:
  binding = {
    'entry': asdict(entry),
    'objects': [asdict(knowledge.objects[role.object_id]) for role in entry.roles],
    'contexts': [asdict(knowledge.contexts[key]) for key in entry.contexts],
    'sources': [asdict(knowledge.sources[key]) for key in entry.sources],
  }
  return hashlib.sha256(json.dumps(binding, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def _query_transits(chart: BaziChart, coordinate: TransitCoordinate) -> TransitSet | None:
  '''按入口分派查询；各入口的字段在位由 `TransitCoordinate` 构造期保证。'''
  transit_chart = TransitChart(chart)
  if coordinate.entry == 'at_year':
    assert coordinate.gz_year is not None # TransitCoordinate 构造期已核。
    return transit_chart.at_year(coordinate.gz_year)
  if coordinate.entry == 'at_month':
    assert coordinate.gz_year is not None and coordinate.gz_month is not None # 同上。
    return transit_chart.at_month(coordinate.gz_year, coordinate.gz_month)
  if coordinate.entry == 'at_date':
    assert coordinate.solar_date is not None # 同上。
    return transit_chart.at_date(coordinate.solar_date)
  assert coordinate.solar_moment is not None # 同上。
  return transit_chart.at_moment(coordinate.solar_moment)


def _eligible_claims(
  criterion_id: str,
  knowledge: KnowledgeBase,
  include_reference_only: bool,
  gender: BaziGender,
) -> tuple[tuple[str, bool], ...]:
  '''判据关联条目中通过输出资格与性别门槛的条目，及其绑定是否与 `_BINDINGS` 一致；两种条目角色共用。'''
  eligible: list[tuple[str, bool]] = []
  for claim_id in _CRITERIA[criterion_id].claims:
    entry = knowledge.entries.get(claim_id)
    if entry is None or (not include_reference_only and entry.output != 'default'):
      continue
    required_gender = _RELATED_GENDERS.get(claim_id)
    if required_gender is not None and gender is not required_gender:
      continue
    eligible.append((claim_id, _binding_digest(knowledge, entry) == _BINDINGS[claim_id]))
  return tuple(eligible)


def _select_transits(queried: TransitSet, requested: tuple[TransitKind, ...]) -> TransitSet | None:
  '''取「所求 ∩ 现有」；交集空返回 `None`，不上抛 `select` 的缺项异常。'''
  present = frozenset(queried)
  obtainable = frozenset(requested) & present
  if not obtainable:
    return None
  return queried.select(*(kind for kind in requested if kind in obtainable))


def evaluate_context(
  chart: BaziChart,
  *,
  criterion_id: str,
  profile: ContextProfile | RelationshipProfile,
  knowledge: KnowledgeBase | None = None,
  include_reference_only: bool = False,
) -> ContextResult:
  '''检查选定范围是否满足已注册判据，返回判别、观察、证据及条目的匹配结果。

  Note:
  - 婚恋判据走 `RelationshipProfile`，按 `spouse_evidence` 计算结构证据；其余判据走
    `ContextProfile`。判据与 profile 种类不符抛 `ValueError`。
  - 官杀两条判据判别关联条目的完整前提。其余判据只判可计算事实：婚恋两条判结构，丁火、
    庚金两条判日主，偏印、枭印两条判十神是否出现。身弱、有制有化、喜用、夺食、「有用／
    喜忌／成格」等完整理论条件留在知识文本，不为它们新增 UNKNOWN，也不认证其已满足；
    所需流年缺失或不可查询时返回 UNKNOWN。
  - 参考条目须显式设置 include_reference_only=True。条件判据的关联条目只是条件参考，
    与事实判别的状态无关；只向男命返回的关联条目对女命一律不关联（门槛先于绑定状态），静态查阅不受限。
  - 未传 knowledge 时，每次独立加载默认来源，已保存的修改在后续加载时可见；
    传入知识库则直接复用。已有知识库和结果保留原内容，共享调用须显式重载才能取得更新。
  - 观察原局年、月、时明干与四支全部实际藏干；请求流年时加入该流年明干与藏干。
    不观察日主明干，但等于日主的藏干仍分类为比肩；藏干百分比不作权重，重复位置保留。
    不另加力量／次数阈值、相邻、去留或有效制化条件。
  - 范围完整性优先于女命条件与事实判别：男命缺必需年份仍为 UNKNOWN / missing_transit_coordinate。
    婚恋范围缺查询坐标为 UNKNOWN / missing_transit_coordinate；入口不可查询或所求种类
    部分缺失为 UNKNOWN / transit_unavailable，已取得种类的证据照常保留。
    SATISFIED / NOT_SATISFIED 只描述完整的显式前提，不证明现实事件成立。
  - 官杀判据关联的四条原作知识均仅供参考；自定义库若改变同 ID 的条目、对象、
    前提、情境、来源或输出政策，该条返回 binding_unrecognized。条件参考同样核对绑定，
    不一致时记 `recognized=False`，不改变事实判别。等值的导出重载条目仍可匹配。
  - 未选择参考条目或知识库中缺少相应条目时，不生成其 EntryMatch 或 RelatedEntry。
    前提满足不授予默认输出资格。

  Return: (ContextResult) 判据结果、逐柱观察或结构证据、条目匹配，以及输入与知识快照。
  '''
  _check_chart(chart)
  if not isinstance(profile, (ContextProfile, RelationshipProfile)):
    raise TypeError(f'Expected ContextProfile | RelationshipProfile, got {type(profile)}')
  _choice(criterion_id, tuple(_CRITERIA))
  _typed(include_reference_only, bool)
  expected_kind = _CRITERIA[criterion_id].profile_kind
  actual_kind = 'relationship' if isinstance(profile, RelationshipProfile) else 'context'
  if expected_kind != actual_kind:
    raise ValueError(f'Criterion {criterion_id} expects a {expected_kind} profile, got a {actual_kind} profile')
  if knowledge is not None:
    _typed(knowledge, KnowledgeBase)
  knowledge = KnowledgeBase.load() if knowledge is None else knowledge
  bazi = chart.bazi

  location_time = bazi.location_time
  identity = {
    **({'birth_time': bazi.solar_datetime.isoformat()} if location_time is None else location_time.json),
    'gender': str(bazi.gender),
    'config': _config_json(bazi.config),
    'pillars': [str(value) for value in bazi.pillars],
  }
  input_json = json.dumps(identity, ensure_ascii=False)

  if isinstance(profile, RelationshipProfile):
    unavailable: MatchReason | None = None
    if profile.scope == 'natal':
      evidence = spouse_evidence(chart, None)
    elif profile.coordinate is None:
      unavailable = 'missing_transit_coordinate'
      evidence = spouse_evidence(chart, None)
    else:
      queried = _query_transits(chart, profile.coordinate)
      if queried is None:
        unavailable = 'transit_unavailable'
        evidence = spouse_evidence(chart, None)
      else:
        transits = _select_transits(queried, profile.kinds)
        evidence = spouse_evidence(chart, transits)
        if transits is None or frozenset(transits) != frozenset(profile.kinds):
          unavailable = 'transit_unavailable'

    day_pillar_in_chong = DizhiRelation.冲 in evidence.house_relations
    day_pillar_in_xing = DizhiRelation.刑 in evidence.house_relations
    target_stem_visible = any(value.layer == 'visible' for value in evidence.appearances)
    target_stem_hidden = any(value.layer == 'hidden' for value in evidence.appearances)
    observations = frozendict(
      {_OBS_PALACE_CHONG: day_pillar_in_chong, _OBS_PALACE_XING: day_pillar_in_xing}
      if criterion_id == _PALACE
      else {_OBS_STAR_VISIBLE: target_stem_visible, _OBS_STAR_HIDDEN: target_stem_hidden}
    )

    reason: MatchReason
    if unavailable is not None:
      reason = unavailable
    elif criterion_id == _PALACE:
      reason = 'premise_satisfied' if (day_pillar_in_chong or day_pillar_in_xing) else 'required_classification_absent'
    else:
      reason = 'premise_satisfied' if target_stem_visible else 'required_classification_absent'

    eligible = _eligible_claims(criterion_id, knowledge, include_reference_only, bazi.gender)
    return ContextResult(
      profile,
      CriterionResult(
        criterion_id,
        _CRITERIA[criterion_id].definition,
        _STATUS_BY_REASON[reason],
        reason,
        unavailable is None,
        observations,
      ),
      (),
      evidence,
      tuple(RelatedEntry(*claim) for claim in eligible),
      (),
      input_json,
      knowledge,
    )

  def __occurrences(ganzhi: Ganzhi, pillar: Pillar, kind: TransitKind | None = None) -> tuple[ChartOccurrence, ...]:
    origin: Literal['natal', 'transit'] = 'natal' if kind is None else 'transit'
    year = None if kind is None else profile.ganzhi_year
    stems: tuple[tuple[Literal['visible', 'hidden'], Tiangan], ...] = (
      (() if pillar == 'day' else (('visible', ganzhi.tiangan),)) +
      tuple(('hidden', stem) for stem in hidden_tiangans(ganzhi.dizhi))
    )

    return tuple(
      ChartOccurrence(
        origin,
        pillar,
        ganzhi,
        layer,
        stem,
        shishen(bazi.day_master, stem),
        kind,
        year,
      )
      for layer, stem in stems
    )

  occurrences = [
    occurrence
    for pillar, ganzhi in zip(_PILLARS, bazi.pillars, strict=True)
    for occurrence in __occurrences(ganzhi, pillar)
  ]
  unavailable = None
  if profile.observation_scope == 'natal_and_liunian':
    if profile.ganzhi_year is None:
      unavailable = 'missing_transit_coordinate'
    else:
      transits = TransitChart(chart).at_year(profile.ganzhi_year)
      if transits is None or transits.liunian is None:
        unavailable = 'transit_unavailable'
      else:
        occurrences.extend(__occurrences(transits.liunian, 'liunian', TransitKind.LIUNIAN))

  classes = {value.shishen for value in occurrences}
  fact: MatchReason
  if criterion_id in _DAY_MASTER_CRITERIA:
    key, day_master = _DAY_MASTER_CRITERIA[criterion_id]
    observations = frozendict({key: bazi.day_master is day_master})
    fact = 'premise_satisfied' if observations[key] else 'day_master_differs'
  elif criterion_id in _CLASS_CRITERIA:
    observations = frozendict({key: required in classes for key, required in _CLASS_CRITERIA[criterion_id].items()})
    fact = 'premise_satisfied' if all(observations.values()) else 'required_classification_absent'
  else:
    coexistence = Shishen.正官 in classes and Shishen.七杀 in classes
    female = bazi.gender is BaziGender.FEMALE
    observations = frozendict({
      _OBS_COEXISTENCE: coexistence, _OBS_FEMALE: female,
    })
    if _CRITERIA[criterion_id].female_required and not female:
      fact = 'female_gate_false'
    else:
      fact = 'premise_satisfied' if coexistence else 'required_classification_absent'
  reason = fact if unavailable is None else unavailable

  matches: list[EntryMatch] = []
  related: tuple[RelatedEntry, ...] = ()
  eligible = _eligible_claims(criterion_id, knowledge, include_reference_only, bazi.gender)
  if _CRITERIA[criterion_id].entry_role == 'premise':
    for claim_id, recognized in eligible:
      entry_reason = reason if recognized else 'binding_unrecognized'
      matches.append(EntryMatch(claim_id, _STATUS_BY_REASON[entry_reason], entry_reason))
  else:
    related = tuple(RelatedEntry(*claim) for claim in eligible)

  return ContextResult(
    profile,
    CriterionResult(
      criterion_id,
      _CRITERIA[criterion_id].definition,
      _STATUS_BY_REASON[reason],
      reason,
      unavailable is None,
      observations,
    ),
    tuple(occurrences),
    None,
    related,
    tuple(matches),
    input_json,
    knowledge,
  )
