# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Explicitly scoped premises for repository-editorial reference text.
仓内原作参考文字的显式范围前提判别；不判断现实事件、力量或有效制化。'''

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from typing import Any, Final, Literal, TypeVar, get_args

from .bazi import BaziGender
from .bazi_chart import BaziChart
from .common import frozendict
from .defines import Ganzhi, Tiangan, Shishen
from .knowledge import KnowledgeBase, KnowledgeEntry
from .school import BaziConfig, BaziSchool, _config_json
from .transit_chart import TransitChart
from .transits import TransitKind
from .utils.bazi_utils import hidden_tiangans, shishen


'''Complete-premise verdict, independent of knowledge organization. / 完整前提判别，独立于知识整理状态。'''
MatchStatus = Literal['SATISFIED', 'NOT_SATISFIED', 'UNKNOWN']

'''Why the complete premise has this verdict. / 完整前提的判别理由。'''
MatchReason = Literal[
  'premise_satisfied', 'required_classification_absent', 'female_gate_false',
  'missing_transit_coordinate', 'transit_unavailable', 'predicate_undefined', 'binding_unrecognized',
]

'''The observation range; no implicit default. / 观察范围，无隐式默认值。'''
ObservationScope = Literal['natal', 'natal_and_liunian']

'''Position within the ordered observation query. / 有序观察查询中的位置。'''
Pillar = Literal['year', 'month', 'day', 'hour', 'liunian']

_T = TypeVar('_T')
_PILLARS: Final[tuple[Pillar, ...]] = ('year', 'month', 'day', 'hour')

_GUANSHA: Final = 'editorial.guansha_coexistence.v1'
_FEMALE: Final = 'editorial.guansha_coexistence_female.v1'
_CRITERIA: Final[frozendict[str, tuple[str, tuple[str, ...]]]] = frozendict({
  _GUANSHA: ('选定范围内正官与七杀各至少出现一次。', (
    'editorial.shishen.zhengguan.legal_trouble', 'editorial.shishen.qisha.legal_trouble',
  )),
  _FEMALE: ('选定范围内正官与七杀各至少出现一次，且输入为女命。', (
    'editorial.shishen.zhengguan.infidelity', 'editorial.shishen.qisha.infidelity',
  )),
  'tiangan.ding_weak_and_overcontrolled': ('丁火日主身弱及克太多；完整判据未定义。', ('legacy.tiangan.ding.weak_state',)),
  'tiangan.geng_regulated_transit': ('庚金日主有制有化及后天有教养；完整判据未定义。', ('legacy.tiangan.geng.regulated_transit',)),
  'shishen.pianyin_favorable_or_balanced': ('偏印喜用或状态良好；完整判据未定义。', ('legacy.shishen.SH-199',)),
  'shishen.xiaoyin_duoshi': ('枭印夺食；完整判据未定义，不等同于偏印与食神共现。', ('legacy.shishen.SH-066',)),
})

# Fingerprints include the entire entry and its bound object/context/source records.
# They identify the editorial meaning, not merely its ID or display words.
_BINDINGS: Final[frozendict[str, str]] = frozendict({
  'editorial.shishen.zhengguan.legal_trouble': '0cc47687bf24c6f5ffde1eda9d38ac5532838f765562aea57bf8e7f2cc6a582a',
  'editorial.shishen.qisha.legal_trouble': 'f5ec75f1814c3409f0bda3d65d380d45c781201a78a259316e8e17eb59096434',
  'editorial.shishen.zhengguan.infidelity': '02215c0a516e55e0d14b4da4f585685d954f692b9268857a3416aaff78487896',
  'editorial.shishen.qisha.infidelity': '6c687b90559b0b56cfc51a39e165025aad94811c9948bebe5c51bae9fd4f2801',
})

_STATUS_BY_REASON: Final[frozendict[MatchReason, MatchStatus]] = frozendict({
  'premise_satisfied':              'SATISFIED',
  'required_classification_absent': 'NOT_SATISFIED',
  'female_gate_false':              'NOT_SATISFIED',
  'missing_transit_coordinate':     'UNKNOWN',
  'transit_unavailable':            'UNKNOWN',
  'predicate_undefined':            'UNKNOWN',
  'binding_unrecognized':           'UNKNOWN',
})


def _typed(value: object, expected: type[_T]) -> _T:
  if not isinstance(value, expected):
    raise TypeError(f'Expected {expected.__name__}, got {type(value)}')
  return value


def _choice(value: object, choices: tuple[str, ...]) -> None:
  _typed(value, str)
  if value not in choices:
    raise ValueError(f'Unsupported value: {value}')


def _year(value: object) -> None:
  if value is not None and type(value) is not int:
    raise TypeError(f'Expected int | None, got {type(value)}')


def _tuple(values: object, expected: type[_T]) -> None:
  values = _typed(values, tuple)
  for value in values:
    _typed(value, expected)


def _verdict(status: MatchStatus, reason: MatchReason) -> None:
  _choice(status, get_args(MatchStatus))
  _choice(reason, get_args(MatchReason))
  if status != _STATUS_BY_REASON[reason]:
    raise ValueError('Status and reason disagree')


@dataclass(frozen=True)
class ContextProfile:
  '''Select natal or natal plus one LIUNIAN; all actual hidden stems are fixed.
  显式选择原局或原局加单流年；固定包含全部实际藏干，不以百分比计力量。

  Note:
  - A year is a Ganzhi-year label, not a Gregorian timestamp. Missing year is UNKNOWN.
  - 年份是干支年标签，不是公历时刻；缺失年份返回 UNKNOWN。
  '''

  observation_scope: ObservationScope
  ganzhi_year:        int | None = None

  def __post_init__(self) -> None:
    _choice(self.observation_scope, get_args(ObservationScope))
    _year(self.ganzhi_year)
    if self.observation_scope == 'natal' and self.ganzhi_year is not None:
      raise ValueError('Natal scope cannot include a transit coordinate')

  @property
  def stem_scope(self) -> Literal['visible_and_hidden']:
    return 'visible_and_hidden'


@dataclass(frozen=True)
class ChartOccurrence:
  '''One classified stem, preserving its position, layer and time identity.
  一处已分类天干，保留柱位、明藏层及时间身份；重复位置不合并。'''

  origin:      Literal['natal', 'transit']
  pillar:      Pillar
  index:       int
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
    if type(self.index) is not int:
      raise TypeError(f'Expected int, got {type(self.index)}')
    for value, expected in ((self.ganzhi, Ganzhi), (self.stem, Tiangan), (self.shishen, Shishen)):
      _typed(value, expected)
    _year(self.ganzhi_year)
    if self.kind is not None:
      _typed(self.kind, TransitKind)
    if self.origin == 'natal':
      if self.pillar not in _PILLARS or self.index != _PILLARS.index(self.pillar) or self.kind is not None or self.ganzhi_year is not None:
        raise ValueError('Invalid natal occurrence coordinate')
      if self.pillar == 'day' and self.layer == 'visible':
        raise ValueError('Day-master visible stem is excluded by convention')
    elif self.pillar != 'liunian' or self.index != 4 or self.kind is not TransitKind.LIUNIAN or self.ganzhi_year is None:
      raise ValueError('Invalid LIUNIAN occurrence coordinate')
    if self.layer == 'visible' and self.stem != self.ganzhi.tiangan:
      raise ValueError('Visible stem differs from its Ganzhi')
    if self.layer == 'hidden' and self.stem not in hidden_tiangans(self.ganzhi.dizhi):
      raise ValueError('Hidden stem is absent from its Ganzhi')


@dataclass(frozen=True)
class CriterionResult:
  '''Complete verdict with separately known observations, including partial scopes.
  完整判别与已知局部观察分开记录，局部观察不替代缺失的范围。

  Note:
  - `observed_coexistence` and `female` serve the editorial predicates. `day_master_is_ding`,
    `day_master_is_geng`, `observed_pianyin` and `observed_shishen` (食神, not 十神)
    are partial facts for undefined controls, not complete predicates.
  - `observed_coexistence` 与 `female` 用于原作前提；其余键记录丁／庚日主及偏印／食神
    的局部事实，不构成未定义情境的完整判据。`observed_shishen` 指食神，不是十神总类。
  '''

  criterion_id:   str
  revision:       int
  definition:     str
  status:         MatchStatus
  reason:         MatchReason
  scope_complete: bool
  observations:   frozendict[str, bool]

  def __post_init__(self) -> None:
    _choice(self.criterion_id, tuple(_CRITERIA))
    if type(self.revision) is not int:
      raise TypeError(f'Expected int, got {type(self.revision)}')
    _typed(self.definition, str)
    if self.revision != 1 or self.definition != _CRITERIA[self.criterion_id][0]:
      raise ValueError('Unsupported criterion definition or revision')
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
  '''Entry verdict after semantic binding, separate from the structural criterion.
  语义绑定后的条目前提判别，独立于结构 criterion。'''

  claim_id: str
  status:   MatchStatus
  reason:   MatchReason

  def __post_init__(self) -> None:
    _typed(self.claim_id, str)
    if not self.claim_id.strip():
      raise ValueError('Expected non-empty claim ID')
    _verdict(self.status, self.reason)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  result: dict[str, Any] = {}
  for key, value in pairs:
    if key in result:
      raise ValueError(f'Duplicate JSON key: {key}')
    result[key] = value
  return result


def _mapping(value: object, keys: tuple[str, ...]) -> dict[str, Any]:
  value = _typed(value, dict)
  if set(value) != set(keys):
    raise ValueError('Record fields differ')
  return dict(value)


def _array(value: object) -> list[Any]:
  return _typed(value, list)


def _validate_input(text: str) -> None:
  data = _mapping(
    json.loads(text, object_pairs_hook=_pairs),
    ('birth_time', 'gender', 'config', 'pillars'),
  )
  _typed(data['birth_time'], str)
  birth = datetime.fromisoformat(data['birth_time'])
  if birth.tzinfo is not None or birth.second or birth.microsecond or birth.isoformat() != data['birth_time']:
    raise ValueError('Expected canonical naive minute birth time')
  _choice(data['gender'], ('male', 'female'))
  config = _mapping(data['config'], tuple(field.name for field in fields(BaziConfig)))
  BaziConfig.from_values(
    backend=config['backend'],
    precision=config['precision'],
    dayun_year_rule=config['dayun_year_rule'],
    school=BaziSchool.from_json(config['school']),
  )
  pillars = _array(data['pillars'])
  if len(pillars) != 4:
    raise ValueError('Expected four ordered natal pillars')
  for value in pillars:
    _typed(value, str)
    Ganzhi.from_str(value)


@dataclass(frozen=True)
class ContextResult:
  '''Immutable observation record with full input and knowledge snapshots.
  不可变观察记录，附完整输入及知识快照；恢复只恢复记录，不重新计算。'''

  profile:        ContextProfile
  criterion:      CriterionResult
  occurrences:    tuple[ChartOccurrence, ...]
  entries:        tuple[EntryMatch, ...]
  input_json:     str
  knowledge_json: str

  def __post_init__(self) -> None:
    _typed(self.profile, ContextProfile)
    _typed(self.criterion, CriterionResult)
    _tuple(self.occurrences, ChartOccurrence)
    _tuple(self.entries, EntryMatch)
    _typed(self.input_json, str)
    _validate_input(self.input_json)
    knowledge = KnowledgeBase.from_json(self.knowledge_json)
    for match in self.entries:
      knowledge.entry(match.claim_id)

  def export_json(self) -> str:
    '''Export this record, including evidence and all knowledge registries.
    导出本记录、全部证据及知识注册表，不改变参考输出资格。'''
    data = {
      'record_version': 1,
      'profile': {**asdict(self.profile), 'stem_scope': self.profile.stem_scope},
      'criterion': {**asdict(self.criterion), 'observations': dict(self.criterion.observations)},
      'occurrences': [
        {**asdict(value), 'ganzhi': str(value.ganzhi), 'stem': str(value.stem), 'shishen': str(value.shishen),
         'kind': None if value.kind is None else value.kind.value}
        for value in self.occurrences
      ],
      'entries': [asdict(value) for value in self.entries],
      'input': json.loads(self.input_json),
      'knowledge': json.loads(self.knowledge_json),
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'

  @classmethod
  def from_json(cls, text: str) -> 'ContextResult':
    '''Restore an exported record without recalculation or cross-record authentication.
    恢复导出记录，不重算或认证判别、证据、输入与条目绑定间的一致性。'''
    _typed(text, str)
    data = _mapping(
      json.loads(text, object_pairs_hook=_pairs),
      ('record_version', 'profile', 'criterion', 'occurrences', 'entries', 'input', 'knowledge'),
    )
    if type(data['record_version']) is not int or data['record_version'] != 1:
      raise ValueError('Unsupported record version')
    profile = _mapping(data['profile'], ('observation_scope', 'ganzhi_year', 'stem_scope'))
    _choice(profile.pop('stem_scope'), ('visible_and_hidden',))
    criterion = _mapping(data['criterion'], tuple(field.name for field in fields(CriterionResult)))
    _typed(criterion['observations'], dict)
    criterion['observations'] = frozendict(criterion['observations'])
    occurrences = []
    for item in _array(data['occurrences']):
      value = _mapping(item, tuple(field.name for field in fields(ChartOccurrence)))
      for name, domain in (('ganzhi', Ganzhi), ('stem', Tiangan), ('shishen', Shishen)):
        _typed(value[name], str)
        value[name] = domain.from_str(value[name])
      if value['kind'] is not None:
        _choice(value['kind'], ('liunian',))
        value['kind'] = TransitKind.LIUNIAN
      occurrences.append(ChartOccurrence(**value))
    entries = tuple(EntryMatch(**_mapping(item, ('claim_id', 'status', 'reason'))) for item in _array(data['entries']))

    return cls(
      ContextProfile(**profile),
      CriterionResult(**criterion),
      tuple(occurrences),
      entries,
      json.dumps(data['input'], ensure_ascii=False),
      KnowledgeBase.from_json(json.dumps(data['knowledge'], ensure_ascii=False)).export_json(),
    )

  def render(self) -> str:
    '''Display verdict, evidence and complete reference text with source limits.
    展示判别、证据及完整参考原文和来源限度；前提满足不表示事件成立。'''
    criterion = self.criterion
    lines = [
      f'判据：{criterion.criterion_id}；revision={criterion.revision}；{criterion.definition}',
      f'范围：{self.profile.stem_scope}；{self.profile.observation_scope}；干支年={self.profile.ganzhi_year}',
      f'结构前提：{criterion.status}；{criterion.reason}；scope_complete={criterion.scope_complete}',
      f'输入：{self.input_json}',
      '已知观察：' + json.dumps(dict(criterion.observations), ensure_ascii=False),
      '前提满足只表示本范围内的原作使用条件满足，不表示现实事件成立。',
    ]
    for value in self.occurrences:
      lines.append(f'证据：{value.origin}.{value.pillar}[{value.index}]；{value.ganzhi}；{value.layer}；{value.stem}={value.shishen}；kind={None if value.kind is None else value.kind.value}；干支年={value.ganzhi_year}')
    knowledge = KnowledgeBase.from_json(self.knowledge_json)
    for match in self.entries:
      lines.append(f'原作参考前提：{match.claim_id}；{match.status}；{match.reason}')
      lines.append(knowledge._render(knowledge.entry(match.claim_id), premise_verdict=match.status))
    return '\n'.join(lines)


def _binding_digest(knowledge: KnowledgeBase, entry: KnowledgeEntry) -> str:
  binding = {
    'entry': asdict(entry),
    'objects': [asdict(knowledge.objects[role.object_id]) for role in entry.roles],
    'contexts': [asdict(knowledge.contexts[key]) for key in entry.contexts],
    'sources': [asdict(knowledge.sources[key]) for key in entry.sources],
  }
  return hashlib.sha256(json.dumps(binding, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def evaluate_context(
  chart: BaziChart,
  *,
  criterion_id: str,
  profile: ContextProfile,
  knowledge: KnowledgeBase | None = None,
  include_reference_only: bool = False,
) -> ContextResult:
  '''Evaluate a registered premise in an explicit scope, then bind reference entries.
  在显式范围内求值已注册前提，再联接参考条目；缺失上下文与未定义判据为 UNKNOWN。

  Note:
  - Only two editorial Guansha predicates are defined. Registered legacy controls remain UNKNOWN.
  - 仅定义两个原作官杀判据；已注册旧情境保留 UNKNOWN，不从文本推导新判据。
  '''
  _typed(chart, BaziChart)
  _typed(profile, ContextProfile)
  _choice(criterion_id, tuple(_CRITERIA))
  _typed(include_reference_only, bool)
  if knowledge is not None:
    _typed(knowledge, KnowledgeBase)
  knowledge = KnowledgeBase.load() if knowledge is None else knowledge
  bazi = chart.bazi

  def __occurrences(ganzhi: Ganzhi, pillar: Pillar, index: int, kind: TransitKind | None = None) -> tuple[ChartOccurrence, ...]:
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
        index,
        ganzhi,
        layer,
        stem,
        shishen(bazi.day_master, stem),
        kind,
        year,
      ) for layer, stem in stems
    )

  occurrences = [
    occurrence
    for index, (pillar, ganzhi) in enumerate(zip(_PILLARS, bazi.pillars, strict=True))
    for occurrence in __occurrences(ganzhi, pillar, index)
  ]
  unavailable: MatchReason | None = None
  if profile.observation_scope == 'natal_and_liunian':
    if profile.ganzhi_year is None:
      unavailable = 'missing_transit_coordinate'
    else:
      transits = TransitChart(chart).at_year(profile.ganzhi_year)
      if transits is None or transits.liunian is None:
        unavailable = 'transit_unavailable'
      else:
        occurrences.extend(__occurrences(transits.liunian, 'liunian', 4, TransitKind.LIUNIAN))

  classes = {value.shishen for value in occurrences}
  coexistence = Shishen.正官 in classes and Shishen.七杀 in classes
  female = bazi.gender is BaziGender.FEMALE
  observations = frozendict({
    'observed_coexistence': coexistence, 'female': female,
    'day_master_is_ding': bazi.day_master is Tiangan.丁,
    'day_master_is_geng': bazi.day_master is Tiangan.庚,
    'observed_pianyin': Shishen.偏印 in classes, 'observed_shishen': Shishen.食神 in classes,
  })

  reason: MatchReason
  if criterion_id not in (_GUANSHA, _FEMALE):
    reason = 'predicate_undefined'
  elif unavailable is not None:
    reason = unavailable
  elif criterion_id == _FEMALE and not female:
    reason = 'female_gate_false'
  elif not coexistence:
    reason = 'required_classification_absent'
  else:
    reason = 'premise_satisfied'
  status = _STATUS_BY_REASON[reason]

  matches = []
  for claim_id in _CRITERIA[criterion_id][1]:
    entry = knowledge.entries.get(claim_id)
    if entry is None or (not include_reference_only and entry.output != 'default'):
      continue
    recognized = criterion_id not in (_GUANSHA, _FEMALE) or _binding_digest(knowledge, entry) == _BINDINGS[claim_id]
    entry_reason = reason if recognized else 'binding_unrecognized'
    matches.append(EntryMatch(claim_id, _STATUS_BY_REASON[entry_reason], entry_reason))

  identity = {
    'birth_time': bazi.solar_datetime.isoformat(), 'gender': str(bazi.gender),
    'config': _config_json(bazi.config),
    'pillars': [str(value) for value in bazi.pillars],
  }
  return ContextResult(
    profile,
    CriterionResult(
      criterion_id,
      1,
      _CRITERIA[criterion_id][0],
      status,
      reason,
      unavailable is None,
      observations,
    ),
    tuple(occurrences),
    tuple(matches),
    json.dumps(identity, ensure_ascii=False),
    knowledge.export_json(),
  )
