# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import dataclass
from enum import Enum
from typing import Final, TypeAlias, TypedDict

from .common import frozendict
from .defines import Shishen, Tiangan


class ShishenDescription(TypedDict):
  # The general descriptions of the Shishen.
  # 这个十神的基本描述。
  general:        list[str]

  # The descriptions when the Shishen is in good status.
  # 当十神处于力量不过强，状态良好的时候（如不被冲、克，也不过旺/为命主喜用时），这个十神代表的特征。
  in_good_status: list[str]

  # The descriptions when the Shishen is in bad status.
  # 当十神过旺（如在天干和地支藏干中出现3次）或被其他元素冲克（如处于“绝”一柱/受刑、穿、克...）的时候，这个十神代表的特征。
  in_bad_status:  list[str]

  # The views of relationship and friendship represented by the Shishen.
  # 这个十神代表的恋爱观和交友观。
  relationship:   list[str]


# The description of the Tiangan, including the meanings, interpretations, images, traits, personalities that it has.
class TianganDescription(TypedDict):
  # The general description(s) of a given Tiangan.
  general:     list[str]

  # The personalities that the given Tiangan reveals.
  personality: list[str]


class _DescriptionSource(Enum):
  '''A stable source-witness identifier. / 稳定的来源见证标识。'''

  EDITORIAL                                = 'editorial'
  YUANHAI_ZIPING_RELATIONS                 = 'yuanhai_ziping_relations'
  YUANHAI_ZIPING_STEM_TABLE                = 'yuanhai_ziping_stem_table'
  YUANHAI_ZIPING_STEM_SYMBOLS_P69          = 'yuanhai_ziping_stem_symbols_p69'
  YUANHAI_ZIPING_STEM_SYMBOLS_P70          = 'yuanhai_ziping_stem_symbols_p70'
  MINGLI_TANYUAN_STEM_BASICS               = 'mingli_tanyuan_stem_basics'
  MINGLI_TANYUAN_SHISHEN_DEFINITIONS       = 'mingli_tanyuan_shishen_definitions'


class _DescriptionLineage(Enum):
  '''An independent textual lineage. / 独立的文本谱系。'''

  EDITORIAL        = 'editorial'
  YUANHAI_ZIPING   = 'yuanhai_ziping'
  MINGLI_TANYUAN   = 'mingli_tanyuan'


class _DescriptionTextLayer(Enum):
  '''The textual layer represented by a source witness. / 来源见证对应的文本层。'''

  EDITORIAL  = 'editorial'
  BAIWEN     = 'baiwen'


class _DescriptionOutput(Enum):
  '''The output policy of a description claim. / 语料断言的输出策略。'''

  DEFAULT        = 'default'
  REFERENCE_ONLY = 'reference_only'


class _DescriptionCondition(Enum):
  '''A prerequisite that enum lookup cannot evaluate. / 枚举查表无法判断的适用条件。'''

  CHART_CONTEXT_REQUIRED = 'chart_context_required'


@dataclass(frozen=True)
class _DescriptionSourceRecord:
  '''A fixed witness and its evidentiary boundary. / 固定底本见证及其证据边界。'''

  work:         str
  attribution:  str
  edition:      str
  locator:      str
  url:          str
  text_layer:   _DescriptionTextLayer
  lineage:      _DescriptionLineage
  excerpt:      str
  supports:     str
  limitations:  str


_DESCRIPTION_SOURCES: Final[
  frozendict[_DescriptionSource, _DescriptionSourceRecord]
] = frozendict({
  _DescriptionSource.EDITORIAL: _DescriptionSourceRecord(
    work='Bazi description corpus',
    attribution='Ningqi Wang',
    edition='Repository editorial confirmed for issue #24',
    locator='PR #222',
    url='https://github.com/0xf3cd/bazi/pull/222',
    text_layer=_DescriptionTextLayer.EDITORIAL,
    lineage=_DescriptionLineage.EDITORIAL,
    excerpt='Repository-original editorial prose.',
    supports='Authorship and the reference-only product classification.',
    limitations='Does not establish a classical rule or real-world prediction.',
  ),
  _DescriptionSource.YUANHAI_ZIPING_RELATIONS: _DescriptionSourceRecord(
    work='《刻京台增补渊海子平大全》',
    attribution='李钦增补',
    edition='明万历二十八年闽书林刘龙田乔山堂刊本',
    locator='PDF p. 6, right leaf, paragraph beginning “生我者為正印偏印”',
    url='https://archive.org/details/20260506_20260506_1149/page/n5/mode/2up',
    text_layer=_DescriptionTextLayer.BAIWEN,
    lineage=_DescriptionLineage.YUANHAI_ZIPING,
    excerpt='生我者為正印偏印我生者為傷官食神尅我者為正官七殺我尅者為偏財正財比肩者為劫財敗財其法陽見陰為正陰見陽為正陽見陽為偏陰見陰為偏如甲丙戊庚壬屬陽乙丁己辛癸屬陰是也',
    supports='The five relations, paired Shishen names, and the 正/偏 polarity rule.',
    limitations='Uses both 劫財 and 敗財; it does not support collapsing both into one name or support personality, kinship, fortune, or unconditional chart judgments.',
  ),
  _DescriptionSource.YUANHAI_ZIPING_STEM_TABLE: _DescriptionSourceRecord(
    work='《刻京台增补渊海子平大全》',
    attribution='李钦增补',
    edition='明万历二十八年闽书林刘龙田乔山堂刊本',
    locator='PDF p. 8, “天干五阳通变” and “天干五阴通变” tables',
    url='https://archive.org/details/20260506_20260506_1149/page/n7/mode/2up',
    text_layer=_DescriptionTextLayer.BAIWEN,
    lineage=_DescriptionLineage.YUANHAI_ZIPING,
    excerpt='天干五陽通變天干五陰通變',
    supports='The Yang/Yin stem groups.',
    limitations='Uses separate 劫財 and 敗財 labels; it does not make their nomenclature or the attached kinship glosses unconditional across schools.',
  ),
  _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69: _DescriptionSourceRecord(
    work='《刻京台增补渊海子平大全》',
    attribution='李钦增补',
    edition='明万历二十八年闽书林刘龙田乔山堂刊本',
    locator='PDF p. 69, left leaf, “十干体象”',
    url='https://archive.org/details/20260506_20260506_1149/page/n68/mode/2up',
    text_layer=_DescriptionTextLayer.BAIWEN,
    lineage=_DescriptionLineage.YUANHAI_ZIPING,
    excerpt='甲木天干作首排乙木根荄種得深丙火明明一太陽',
    supports='The element names for 甲、乙、丙 and a named historical image for 丙.',
    limitations='Does not make the image a cross-school definition or a personality premise.',
  ),
  _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70: _DescriptionSourceRecord(
    work='《刻京台增补渊海子平大全》',
    attribution='李钦增补',
    edition='明万历二十八年闽书林刘龙田乔山堂刊本',
    locator='PDF p. 70, both leaves, “十干体象”',
    url='https://archive.org/details/20260506_20260506_1149/page/n69/mode/2up',
    text_layer=_DescriptionTextLayer.BAIWEN,
    lineage=_DescriptionLineage.YUANHAI_ZIPING,
    excerpt='丁火其形一燭燈戊土城墻堤岸同己土田園屬四維庚金頑鈍性偏剛辛金珠玉性虛靈壬水汪洋併百川癸水應非雨露麼',
    supports='The element names for 丁 through 癸 and named historical images for 丁、戊、辛、壬.',
    limitations='Does not make the images cross-school definitions or personality premises.',
  ),
  _DescriptionSource.MINGLI_TANYUAN_STEM_BASICS: _DescriptionSourceRecord(
    work='《命理探源》',
    attribution='袁树珊著',
    edition='版心题《命理探原》',
    locator='PDF pp. 33 and 36, “干枝阴阳” and “干枝五行及四时方位”',
    url='https://commons.wikimedia.org/w/index.php?curid=132876481',
    text_layer=_DescriptionTextLayer.BAIWEN,
    lineage=_DescriptionLineage.MINGLI_TANYUAN,
    excerpt='甲丙戊庚壬爲陽乙丁己辛癸爲陰甲乙屬木爲東方丙丁屬火爲南方戊己屬土爲中央庚辛屬金爲西方壬癸屬水爲北方',
    supports='The ten stems grouped directly by polarity and element.',
    limitations='Does not support personality, fortune, fixed imagery, or health prose.',
  ),
  _DescriptionSource.MINGLI_TANYUAN_SHISHEN_DEFINITIONS: _DescriptionSourceRecord(
    work='《命理探源》',
    attribution='袁树珊著',
    edition='版心题《命理探原》',
    locator='PDF pp. 66-70, “十干生克定名”',
    url='https://commons.wikimedia.org/w/index.php?curid=132876481',
    text_layer=_DescriptionTextLayer.BAIWEN,
    lineage=_DescriptionLineage.MINGLI_TANYUAN,
    excerpt='陽見陰陰見陽則爲正陽見陽陰見陰則爲偏與我比者爲比肩爲劫財敗財我生者爲傷官食神我尅者爲正財偏財尅我者爲正官偏官生我者爲正印偏印',
    supports='The five relations, polarity distinctions, and this witness\'s Shishen nomenclature.',
    limitations='Does not support collapsing both into 劫財.',
  ),
})


@dataclass(frozen=True)
class _DescriptionClaim:
  '''A description claim with source state and output policy. / 带来源状态与输出策略的语料断言。'''

  claim_id:    str
  text:        str
  sources:     tuple[_DescriptionSource, ...]
  attribution: str
  conditions:  tuple[_DescriptionCondition, ...]
  output:      _DescriptionOutput


'''A bare default-output string with unclassified source, or an explicit claim.
来源未分类的默认输出裸字符串，或显式语料断言。'''
_DescriptionItem: TypeAlias = str | _DescriptionClaim


class _ShishenCorpusDescription(TypedDict):
  general:        list[_DescriptionItem]
  in_good_status: list[_DescriptionItem]
  in_bad_status:  list[_DescriptionItem]
  relationship:   list[_DescriptionItem]


class _TianganCorpusDescription(TypedDict):
  general:     list[_DescriptionItem]
  personality: list[_DescriptionItem]


def _claim(
  claim_id: str,
  text: str,
  sources: tuple[_DescriptionSource, ...],
  attribution: str,
  output: _DescriptionOutput,
  conditions: tuple[_DescriptionCondition, ...] = (),
) -> _DescriptionClaim:
  assert isinstance(claim_id, str)
  assert isinstance(text, str)
  assert all(isinstance(source, _DescriptionSource) for source in sources)
  assert isinstance(attribution, str)
  assert isinstance(output, _DescriptionOutput)
  assert all(isinstance(condition, _DescriptionCondition) for condition in conditions)
  return _DescriptionClaim(
    claim_id=claim_id,
    text=text,
    sources=sources,
    attribution=attribution,
    conditions=conditions,
    output=output,
  )


def _editorial_reference(claim_id: str, text: str) -> _DescriptionClaim:
  return _claim(
    claim_id=claim_id,
    text=text,
    sources=(_DescriptionSource.EDITORIAL,),
    attribution='Repository editorial',
    output=_DescriptionOutput.REFERENCE_ONLY,
  )


def _unverified_reference(
  claim_id: str,
  text: str,
  conditions: tuple[_DescriptionCondition, ...] = (),
) -> _DescriptionClaim:
  return _claim(
    claim_id=claim_id,
    text=text,
    sources=(),
    attribution='Legacy corpus; source unverified',
    conditions=conditions,
    output=_DescriptionOutput.REFERENCE_ONLY,
  )


def _shishen_definition(claim_id: str, text: str) -> _DescriptionClaim:
  return _claim(
    claim_id=claim_id,
    text=text,
    sources=(
      _DescriptionSource.YUANHAI_ZIPING_RELATIONS,
      _DescriptionSource.MINGLI_TANYUAN_SHISHEN_DEFINITIONS,
    ),
    attribution='《渊海子平》与《命理探源》十神定义',
    output=_DescriptionOutput.DEFAULT,
  )


def _tiangan_definition(
  claim_id: str,
  text: str,
  yuan_hai_source: _DescriptionSource,
) -> _DescriptionClaim:
  return _claim(
    claim_id=claim_id,
    text=text,
    sources=(
      yuan_hai_source,
      _DescriptionSource.MINGLI_TANYUAN_STEM_BASICS,
    ),
    attribution='《渊海子平》与《命理探源》天干定义',
    output=_DescriptionOutput.DEFAULT,
  )


def _historical_symbol(
  claim_id: str,
  text: str,
  source: _DescriptionSource,
) -> _DescriptionClaim:
  return _claim(
    claim_id=claim_id,
    text=text,
    sources=(source,),
    attribution='《渊海子平·十干体象》',
    output=_DescriptionOutput.REFERENCE_ONLY,
  )


# The private corpus is the single source of description text. / 私有语料表是描述文字的单一来源。
_SHISHEN_DESCRIPTION_CORPUS: Final[
  frozendict[Shishen, _ShishenCorpusDescription]
] = frozendict({
  Shishen.比肩 : {
    'general': [
      _shishen_definition(
        'shishen.bijian.definition',
        '比肩为与日主五行、阴阳皆相同者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-001',
        '代表同辈、竞争、合作。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-002',
        '代表自己、兄弟姐妹、朋友、同事、团体党派、合伙人、同行者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-003',
        '代表的亲戚：对男、女命主来说都代表自己。但实际运用时，不管男、女，也会把比肩当成兄弟姐妹来看。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-004',
        '代表的正面性格：乐观开朗、积极向上、善良、不记仇、心胸宽广、能容忍。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-005',
        '代表的负面性格：三心二意、做事三分钟热度、过于轻视自己、自卑、妄自菲薄、喜欢多管闲事。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-006',
        '对于日主而言。身强时比肩可以帮助日主，身弱时比肩可以排斥我，所以比肩星象征着协助（身弱时）和竞争（身强时）。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-007',
        '比肩是与日主同类同气的星，在地支也叫“禄”，其意为自尊，自信，自我意识，自主能力。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-008',
        '比肩代表了命主的主观性、独立性，也有命主需要亲力亲为的象。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-009',
        '比肩过重，喜见官杀来制，也可用食伤泄秀。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-010',
        '命带比肩的人（特别是透出天干者），在外人眼里印象通常不错，嘻嘻哈哈、大大咧咧的。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-011',
        '能结交到朋友，在朋友/兄弟姐妹需要帮助时倾囊相助。为人乐观开朗，善良，不记仇。实实在在地帮助别人，讲义气。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-012',
        '个性果断，有自己的想法。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-013',
        '命中比肩为用：可从事的职业有运动员，演员，生意人，司机，体力劳动者，中介等。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-014',
        '比肩的心性稳健刚毅，勇于冒险，上进进取。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-015',
        '比劫（比肩、劫财）过多，象征着命主易有同类相争的体验，如在学校中和同学争考试排名，在工作中和同事竞争等。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-016',
        '比劫（比肩、劫财）过多，也象征着克财。比肩克财是一点点克，今天花一点，明天花一点。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-017',
        '比肩过多者，不懂得拒绝他人，兄弟间缺乏相助，或好友相聚不会长久，有时善意的提醒却导致和朋友的相处中发生不愉快。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-018',
        '八字中比肩过重的人：平时须注意对待他人莫过于慷慨；谨言慎行，避免口舌是非；也需要了解持之以恒的重要性。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-019',
        '容易不把钱当一回事，花钱大手大脚。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-020',
        '背信弃义，愿意沾别人的小便宜。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-021',
        '容易流于孤僻，不合群，缺乏团队和合作精神，反为孤立寡合。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-022',
        '追求平等、自由。比较看重个人空间。喜欢和朋友/伴侣一起成长，探索新的可能。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-023',
        '不喜欢束缚。他们需要能够理解他们的朋友/伴侣。被约束和被控制是他们的雷区。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-024',
        '需要给他们选择和自由的空间。',
      ),
    ],
  },
  Shishen.劫财: {
    'general': [
      _unverified_reference(
        'legacy.shishen.SH-025',
        '代表冒险、挑战、财富、资源。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-026',
        '代表兄弟姐妹、同事、朋友等身边的人，也代表争斗、小人、同行、同事、竞争者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-027',
        '劫财，顾名思义，代表“掠夺”，是一种激进的象征。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-028',
        '命带劫财（特别是劫财透天或过重者），谦虚之中带有傲气。这类人重视细节，通常先着眼于细节而后全局，不善抽象性思维，但在做人做事上通常能坚持到底。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-029',
        '代表的亲戚：对男、女命主来说都代表兄弟姐妹和家族中的同辈。但实际运用时，不管男、女，也会把劫财当成兄弟姐妹来看。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-030',
        '代表的正面性格：口才好、反应快、应变力强、有个性、敢爱敢恨、拿得起放得下。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-031',
        '代表的负面性格：脾气大、不服输、嫉妒心强、爱计较、固执、行事粗鲁、有勇无谋、喜欢吹牛、华而不实。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-032',
        '若八字中带有官杀、食伤（尤喜七杀、食神），可帮助平衡过强的劫财。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-033',
        '劫财在地支叫羊刃，羊刃是五行之极地，为极刚之物。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-034',
        '劫财为日主异性的五行相同者，劫财可以给日主傍身，但帮助日主时需要“劫”日主的“财”，指日主需要付出报酬/代价等。',
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-035',
        '命中劫财为用：命主可以当运动员，军人，武职等。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-036',
        '心性坦率真诚，热情诚恳，坚强志旺，努力不懈。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-037',
        '比劫（比肩、劫财）过多，象征着命主易有同类相争的体验，如在学校中和同学争考试排名，在工作中和同事竞争等。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-038',
        '比劫（比肩、劫财）过多，也象征着克财。劫财克财是一下子花很多钱。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-039',
        '劫财过多，则对人对事容易产生怀疑态度。需要重视与人之协调性。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-040',
        '劫财过重，说明命主性格要强，是良好的管理人才。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-041',
        '心性狭隘，胆大妄为，强悍，有攻击性，不通融，投机，冒险，强好胜，急切，冲动，嫉妒，侵害。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-042',
        '容易盲目行事，冲动行事，蛮横而不够谨慎。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-043',
        '劫财型的人在关系中寻求刺激和新鲜感。他们喜欢冒险和挑战，也有对财富和资源的渴望。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-044',
        '他们的情感世界多姿多彩。是冒险型的人，喜欢新鲜事物。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-045',
        '在恋爱关系中，他们喜欢充当引领者的角色 - 即他们更倾向于引领和主导一段恋爱关系。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-046',
        '与他们交友/恋爱时，需要寻找新的活动和话题，从而保持这段关系中的活力和趣味性。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-047',
        '与他们交友/恋爱时，也需要一定的心理准备，接受他们的多变。',
      ),
    ],
  },
  Shishen.食神: {
    'general': [
      _shishen_definition(
        'shishen.shishen.definition',
        '食神为日主所生且阴阳相同者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-048',
        '代表享受、满足、乐趣、美食、艺术。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-049',
        '食神是命主所生，与命主阴阳相同，代表了口欲和口福，爱好美食，喜欢享乐。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-050',
        '由于食神和命主阴阳相同，其力不尽泄（留有内涵，有所保留），是有节制之泄。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-051',
        '食伤泄出元神（即命主、日主、日元），如同内在潜能被刺激引发，而表现出各种思想、言行、智慧及才艺，故常称为食为吐秀或食伤泄秀。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-052',
        '食神可生财，而财为养命之源；食神又能克制七杀，铲除凶暴之攻击，保护元神寿命，使元神避免横祸，得以安享官爵禄位，故又称食神为爵星或寿星。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-053',
        '食神还代表了第二文昌星，主学习、智慧。与正印不同，食神代表的学习更倾向于艺术方面（舞蹈、唱歌...）、思想表达、口才等。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-054',
        '代表福气、口福、饮食、口才、娱乐、艺术，也代表旅行、健康、寿命。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-055',
        '代表子女、晚辈、学生、员工、宠物（因为食神是日主所生，所以可以取象为子女晚辈、宠物、员工等受到自己帮扶和滋养的人事物）。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-056',
        '代表财源，因为从五行的角度上说，食神可以生财。食神生财，富贵自天来。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-057',
        '代表的亲戚：对男命来说代表女婿、孙子；对女命来说代表女儿。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-058',
        '代表的正面性格：温和儒雅、通情达理、爱好文艺、聪明精细、与世无争、不喜与人辩驳。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-059',
        '代表的负面性格：空想幻想、自命不凡、不切实际、过于清高、为人挑剔。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-060',
        '食伤（食神、伤官）都能生财星。但食神生财更倾向于传统行业，比较保守。伤官生财更倾向于新兴行业，讲究创新。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-061',
        '食神主为人敦厚和蔼，重感情，朋友有难能伸手帮助。也代表命主不喜约束，向往自由。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-062',
        '食伤代表能说会道，食神平和而伤官偏激，食神比伤官更稳重而踏实。',
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-063',
        '心性温和随性，待人宽厚，善解人意，体贴别人。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-064',
        '食神过旺，好幻想，易钻牛角尖；也容易流于虚伪，缺乏是非，显得迂腐懦弱。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _editorial_reference(
        'editorial.shishen.shishen.anxiety_insomnia',
        '食神之人头脑活动非常旺盛，想东想西，因此食神过旺的人，易焦虑失眠。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-066',
        '逢枭印夺食，求谋不顺利，处处阻逆，连谋温饱都很费力。可用比劫来化。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-067',
        '这种人喜欢和朋友/伴侣共享美好的时光。他们喜欢共同的生活体验来发展和深化关系，如一起烹饪、看电影、旅行、探险等。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-068',
        '在关系中，他们更看重对方的审美和品味，希望在生活中找到共鸣的精神体验。他们在关系中注重情绪的感受的表达。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-069',
        '和他们恋爱时，需要花心思在共同体验上，找到共鸣（如一起做饭、出去旅行等）。',
      ),
    ],
  },
  Shishen.伤官: {
    'general': [
      _shishen_definition(
        'shishen.shangguan.definition',
        '伤官为日主所生且阴阳相异者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-070',
        '代表批判、变革。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-071',
        '伤官和食神代表的个性不同，伤官不如食神那样和和气气，反而有点“又狂又傲娇”和恃才傲物的感觉。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-072',
        '伤官也由命主所生，但与命主阴阳相反，所以伤官为异性之泄，其力必尽泄，是无节制之泄。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-073',
        '代表下属、晚辈、才艺、著作、技术、创新事物、艺术文化。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-074',
        '代表的亲戚：对男命来说代表祖母、孙女；对女命来说代表儿子。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-075',
        '代表的正面性格：多才多艺、领悟力高、干劲十足、聪明伶俐。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-076',
        '代表的负面性格：博而不精、恃才傲物、刚愎自用、气量小、为达目的不择手段、贪心重而不知足。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-077',
        '食伤（食神、伤官）都能生财星。但食神生财更倾向于传统行业，比较保守。伤官生财更倾向于新兴行业，讲究创新。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-078',
        '食伤代表能说会道，食神平和而伤官偏激，伤官比食神灵活，有灵气和创造力。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-079',
        '伤官型人喜奉献，愿帮助人，但相比食神型人，他们可能会计较得失，帮助他人后期待他人感激，常想超越他人。',
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-080',
        '伤官状态好（如处于十二长生旺点，或得其他元素生扶而不受克、刑、冲等），容貌易出众，有自己独特的审美和品味。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-081',
        '有才学和能力；有独立性，不依赖他人。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-082',
        '心性聪明灵活，活跃好胜，才华横溢。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-083',
        '伤官过多，容易自视甚高、任性盲目，喜见正偏财以泄伤官之盛气，也喜见印枭以制伤官之傲气。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-084',
        '气量狭小，有怨必报，叛逆，难以管束。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-085',
        '容易流于任性，缺乏约束，反为桀骜不驯。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-086',
        '这种人追求思想的火花和智慧的碰撞。他们在关系中追求智慧上的共鸣，也欣赏精神独立。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-087',
        '和食神一样，他们也注重沟通和表达。他们注重意见交换和思想交流。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-088',
        '他们渴望和另一半有思想层面的交流。他们喜欢探讨哲学、文化、社会问题等一些比较深刻的话题。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-089',
        '他们在寻找可以探寻人生奥秘、共同成长的人。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-090',
        '他们对于浮于表面的恋爱游戏并没有什么兴趣。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-091',
        '在和他们相处时，需要准备好进行深入对话的准备（思想交流），也需要学会尊重和欣赏他们的批判精神和独立思考。',
      ),
    ],
  },
  Shishen.正财: {
    'general': [
      _shishen_definition(
        'shishen.zhengcai.definition',
        '正财为日主所克且阴阳相异者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-092',
        '代表稳定的经济来源/金库。象征稳定和资源/财富的积累。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-093',
        '代表工资、薪水、工作、资产、不动产。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-094',
        '代表的亲戚：对男命来说代表父亲、老婆；对女命来说代表父亲。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-095',
        '代表的正面性格：老实肯干、任劳任怨、勤俭节约、明辨是非、待人诚实。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-096',
        '代表的负面性格：小气、吝啬、不知变通、缺乏趣味、刻板枯燥、计较得失。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-097',
        '正财型人为人讲信用，简朴端正。为人务实、实在。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-098',
        '为人正义，明辨是非，爱打抱不平，待人诚实，有责任感，为人处事豪爽大方，礼貌热情，是个值得信赖的人。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-099',
        '代表自己能够控制的财物，可以动用的关系，代表实质的物质，像是命主的金钱、薪水、产业稳定的收入，占有欲望。',
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-100',
        '其人性格温和、深谋远虑，为人处事审慎。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-101',
        '做事脚踏实地，不虚伪，不狡诈，善于顾家守财，一生勤劳节俭。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-102',
        '勤勉节俭，稳重踏实，保守勤恳，任劳任怨。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-103',
        '为人处事过于胆小怕事。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-104',
        '容易流于苟且，缺乏进取心，得过且过，懦弱无能。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-105',
        '他们在恋爱中寻找稳定和保障。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-106',
        '他们更倾向于建立一个可靠、舒适的环境。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-107',
        '对他们来说，恋爱更像是一种投资。他们选择结婚对象时，会考虑长远在一起的可能性。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-108',
        '他们重视另一半的经济基础和生活能力，并认为这是恋爱/婚姻关系中的重要基石。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-109',
        '通常在感情里会表现出责任感，也会做出承诺。他们希望和伴侣一起打造充满安全感的环境。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-110',
        '和他们恋爱，需要表现出对未来的规划，以及对这段关系的认真态度。',
      ),
    ],
  },
  Shishen.偏财: {
    'general': [
      _shishen_definition(
        'shishen.piancai.definition',
        '偏财为日主所克且阴阳相同者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-111',
        '代表意外之财，非传统的收入来源。也代表惊喜（如彩票）和非凡的体验。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-112',
        '代表不稳定的财、不固定的收入，如副业收入、意外收入、浮动资金、投资、彩票，也代表众人之财（可取象为基金、投资等，所以偏财状态好的人可以从事金融相关工作，如交易员）。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-113',
        '偏财也有从流通中取财之象，如通过交易、转让、投机、借贷、中介、提供咨询服务等方式获得财富。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-114',
        '代表的亲戚：对男命来说代表父亲、女朋友、情人；对女命来说代表父亲。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-115',
        '代表的正面性格：为人豪爽、慷慨、不计较得失、不亏待人。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-116',
        '代表的负面性格：挥霍无度、奢靡、急躁、偏激、焦虑。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-117',
        '男性风流多情，女性爱打扮。主人好交际、会社交。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-118',
        '命带偏财的人生活比较自由开放，心直口快，乐于助人，不拘小节，易有异性缘。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-119',
        '偏财型人弹性强，能屈能伸，适合从事商业，即使破产，也有东山再起的机会。',
      ),
    ], 
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-120',
        '偏财型人做事注重全局，迅速敏捷。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-121',
        '善于发现机会，把握局势而生财。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-122',
        '心性慷慨重义，聪明灵活，乐观开朗。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-123',
        '偏财过多的人行事敏捷却缺乏持久性。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-124',
        '偏财过重，容易过于乐观，在别人眼中不够稳重，做事草率，生活容易晨昏颠倒。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-125',
        '容易不把钱当一回事，花钱大手大脚。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-126',
        '容易流于虚浮，缺乏节制，浮华风流。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-127',
        '偏财型的人在恋爱中追求刺激、新奇。他们向往能带来心跳加速感的恋爱。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-128',
        '他们在感情中常常不按常理出牌。他们对于传统的生活方式和传统的恋爱模式不感兴趣，而是向往有激情和兴奋的体验，并享受生活中的不确定性。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-129',
        '和他们恋爱，需要尝试新鲜事物（如玩剧本杀、冒险）。要在关系中充满惊喜和各种可能。',
      ),
    ],
  },
  Shishen.正官: {
    'general': [
      _shishen_definition(
        'shishen.zhengguan.definition',
        '正官为克制日主且阴阳相异者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-130',
        '代表规则、传统、权威，也代表纪律和责任感。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-131',
        '代表克制自己、自我约束，从而成才。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-132',
        '正官的管制温文尔雅。七杀的管制大刀阔斧，更加无情。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-133',
        '正官也代表管理能力。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-134',
        '代表政治、公职、大公司、能力、上司、法律、制度、威信、压力、声望。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-135',
        '代表的亲戚：对男命来说代表女儿；对女命来说代表老公、男友。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-136',
        '代表的正面性格：稳重、正直、讲信用、有责任感、讲规矩。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-137',
        '代表的负面性格：过于保守、迂腐、优柔寡断、积极性差。',
      ),
      _editorial_reference(
        'editorial.shishen.zhengguan.legal_trouble',
        '如在命盘中也见七杀，则称为官杀混杂，也许代表在公司里受排挤、职场不顺，或有官司是非。',
      ),
      _editorial_reference(
        'editorial.shishen.zhengguan.infidelity',
        '对女命而言，由于官杀代表男朋友/丈夫，所以官杀混杂也代表在感情上纠结，或是在感情上可能会出轨。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-140',
        '正官是护身卫财之本，表示保护人身及财产的安全，正官象征官方权力，多受法理的约束。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-141',
        '代表约束和管教的力量，如法律，纪律，长辈，上司，政府，学制，职业，目标，计划等合理的规则规范和管理，或者是国家公共机关的制度。',
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-142',
        '为人厚道，做事稳重，办事认真，只求平安，不喜反抗，为人清廉洁公正，自尊心强，重视名利，品性端庄，心地善良，光明磊落，讲德礼节。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-143',
        '心性正直有责任感，端庄严肃，为人诚实守信。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-144',
        '胆小怕事，墨守成规，唯唯诺诺，容易有自卑感。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-145',
        '容易循规蹈矩、流于形式；刻板保守，墨守成规。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-146',
        '在恋爱中需要尊重和认可，在乎另一半的尊重和认可，并注重另一半的道德品质和社会地位。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-147',
        '他们更倾向于传统、正式的恋爱关系，对待感情认真严肃，喜欢有序的生活方式。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-148',
        '在他们眼中，一个理想的另一半有责任心、遵守承诺、并得到他人尊敬。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-149',
        '他们喜欢稳定持久的关系，喜欢建立在共同价值观和相互尊重基础上的关系。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-150',
        '和他们恋爱需要展示自己的诚信、稳重，诚实地交流和表达自己的想法。',
      ),
    ],
  },
  Shishen.七杀: {
    'general': [
      _shishen_definition(
        'shishen.qisha.definition',
        '七杀为克制日主且阴阳相同者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-151',
        '代表激情和冒险，象征挑战现状、突破极限的勇气。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-152',
        '夸张一点说，代表通过被外界“毒打”从而历经磨练成才。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-153',
        '七杀的管制大刀阔斧、雷厉风行，所以也是一种霸道的象征。',
      ),
      _editorial_reference(
        'editorial.shishen.qisha.crime_disaster',
        '官司、法院、牢狱、军队、公检法、忌恨、小人、恶人、凶祸、外伤、疾病。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-155',
        '代表的亲戚：在男命中代表儿子；在女命中代表男朋友、情人、丈夫。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-156',
        '代表的正面性格：有进取心、有冲劲、做事果断、见义勇为、勇于创新。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-157',
        '代表的负面性格：偏激、凶暴、好胜心强、猜忌心重、阴沉。',
      ),
      _editorial_reference(
        'editorial.shishen.qisha.legal_trouble',
        '如在命盘中也见正官，则称为官杀混杂，也许代表在公司里受排挤、职场不顺，或有官司是非。',
      ),
      _editorial_reference(
        'editorial.shishen.qisha.infidelity',
        '对女命而言，由于官杀代表男朋友/丈夫，所以官杀混杂也代表在感情上纠结，或是在感情上可能会出轨。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-160',
        '与日柱同性之克，无情之克，其含义为打击，压制，暴力，权其性刚雄，具有叛逆，称霸之性，需制化方可驾驭。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-161',
        '代表非正当的管理和约束，或强制性的压迫和管制。这种管理和压迫容易让其他人产生反感和排斥。',
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-162',
        '有野心和志气，能够通过努力达到自己的目的。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-163',
        '心性豪爽侠义，上进积极，威严机智。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-164',
        '专制，暴力、独断、霸气，匪气，好胜，冲动，凶残。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-165',
        '容易偏激，叛逆和过于霸道，容易走极端。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _editorial_reference(
        'editorial.shishen.qisha.external_disaster',
        '七杀代表突如其来的打击、攻击、意外灾害等外在环境的变故。',
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-167',
        '他们在恋爱中追求强烈的情感体验和各种成长机会。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-168',
        '他们希望和另一半经历人生风雨，书写一段传奇性的故事。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-169',
        '七杀型人倾向于动态和不稳定的恋爱关系。他们情感深刻而热烈，感情中常有“共患难”的情节。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-170',
        '他们看中另一半的独立性，欣赏能从逆境中站起来的。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-171',
        '成为TA的战友，和他一起历经困难，成为TA的战友，这样就能和TA感情长久。',
      ),
    ],
  },
  Shishen.正印: {
    'general': [
      _shishen_definition(
        'shishen.zhengyin.definition',
        '正印为生助日主且阴阳相异者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-172',
        '代表智慧、教化，也代表关怀和指导。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-173',
        '正印也代表学习、智慧。和食神不同，正印代表的是论文、学术研究、学校考试相关的学习。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-174',
        '代表印章（这也是正印的本意）、授权、权力、学业、学历、才识、智慧、庇护、祖产，也代表生扶、帮助你的事物。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-175',
        '代表的亲戚：代表男命和女命的母亲。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-176',
        '代表的正面性格：宽容、仁慈、不记仇、注重内涵、有气质。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-177',
        '代表的负面性格：过于依赖他人、思想不切实际、不懂人情世故、死爱面子活受罪。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-178',
        '主秀气、文采。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-179',
        '慈悲心肠，富于浓厚的人情味儿，待人重情重义，思考力丰富，聪明多智慧，内涵不露，有随机应变的能力，常能谋大事，吸取知识，有精气神，正识正见，是生扶本身（日主）的吉星。',
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-180',
        '主为人儒雅，做事聪明而有计谋，善于观察、隐藏自我。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-181',
        '正印型人如果遇到不利处境，也能审时度势，顺应外界情况进行调整。他们也是善解人意的智慧型人士。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-182',
        '心性聪明仁慈，淡泊名利。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-183',
        '正印过多，且八字中不见官杀，不能化杀为权，则表示为人本分、保守，不轻易改变初衷，比较厚道，遇事只求自保。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-184',
        '正印受克或过旺，利己心强，不顾他人，厚己薄他，喜欢空想而缺乏付之行动，对过去的东西耿耿于怀，记忆力强，依赖心强，死要面子活受罪。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-185',
        '容易流于庸碌，缺乏进取心，迟钝消极。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-186',
        '正印型人喜欢和朋友/伴侣精神上的连接。他们在关系中常是良师益友的角色，喜欢充当保护者，引导、照顾、体贴、关怀对方。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-187',
        '他们喜欢给另一半提供情感上的鼓励。理想伴侣是能够欣赏他们的智慧和慷慨，同时也愿意向他们学习。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-188',
        '和他们恋爱，要体现出对知识和成长的渴望，并对他们的指导和帮助有感激。在关系中，你们需要寻找到共同成长的路径。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-189',
        '他们欣赏生活中和他们共同寻找生活中的“深意”中的另一半，精神共鸣让关系更持久和稳固。',
      ),
    ],
  },
  Shishen.偏印: {
    'general': [
      _shishen_definition(
        'shishen.pianyin.definition',
        '偏印为生助日主且阴阳相同者。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-190',
        '代表非传统的智慧和创造力，象征艺术、想象。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-191',
        '相比正印，偏印生助日主更加“拧巴”，不像正印那样尽心尽力。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-192',
        '代表宗教、艺术、文化、玄学、医学、技艺、创作、副业，也代表生扶、帮助你的事物。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-193',
        '代表的亲戚：代表男命和女命的继母、后母、养母。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-194',
        '代表的正面性格：悟性高、直觉敏锐、观察力强、富有创造力、心思细腻。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-195',
        '代表的负面性格：多学少成、做事容易半途而废、思想怪异、孤僻、疑心病重、冷淡。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-196',
        '偏印型人有艺术家性格；适合发展专长类技能，从而成为专业人才。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-197',
        '少言，少动，文静。',
      ),
    ],
    'in_good_status': [
      _unverified_reference(
        'legacy.shishen.SH-198',
        '有艺术、文学、哲理、玄学之天赋，对非现实领域悟性甚高。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-199',
        '偏印为喜用或状态良好（不过旺、不受刑克冲害）：善于观察，心思细致，喜欢传统文化和周易，具有神秘，先知先觉的能力，常有独特的内心世界，能看透人情世故，超凡脱俗，不重视名利。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-200',
        '爱恨分明，领悟能力强，机智而精明，知道自己想要什么，做事有目的性。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-201',
        '心性精明干练，反应迅速，多才多艺。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'in_bad_status': [
      _unverified_reference(
        'legacy.shishen.SH-202',
        '偏印过重，通常喜欢独来独往，表达过于含蓄，凡事不喜欢直言，不擅长争名夺利。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-203',
        '需读理解与人交往的人情世故，并保持幽默诙谐的生活态度，否则容易曲高和寡。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-204',
        '过于沉浸在自己的世界里；有心计，精于算计；妄想，疑心重，冷漠，自私思想行为怪异，自我封闭；学而不精，不通人情，胆怯心虚，心狠手辣。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.shishen.SH-205',
        '容易流于孤独，缺乏人情，反为自私冷漠。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
    'relationship': [
      _unverified_reference(
        'legacy.shishen.SH-206',
        '在恋爱中追求灵魂共鸣，能够激发创意和灵感的关系让他们向往。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-207',
        '偏印型人在生活中有艺术气息，有独特世界观的浪漫主义者。他们往往对神秘事物、玄学、心理学等有兴趣。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-208',
        '他们在关系中喜欢探索新的表达方式，享受和另一半的非传统的交流互动。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-209',
        '他们的理想伴侣能够理解他们的内心世界，并和他们一起踏上探索未知世界的旅程。',
      ),
      _unverified_reference(
        'legacy.shishen.SH-210',
        '和他们恋爱，需要敞开心扉，探索生活的多种可能性，也需要欣赏、支持他在生活中的探索和创造。',
      ),
    ],
  },
})


# The private Tiangan corpus has the same form as above. / 私有天干语料表采用与上文相同的形式。
_TIANGAN_DESCRIPTION_CORPUS: Final[
  frozendict[Tiangan, _TianganCorpusDescription]
] = frozendict({
  Tiangan.甲: {
    'general': [
      _tiangan_definition(
        'tiangan.jia.definition',
        '甲为阳木。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69,
      ),
      _unverified_reference(
        'legacy.tiangan.jia.tree_image',
        '甲比作参天大树，有栋梁之才。',
      ),
      _editorial_reference(
        'editorial.tiangan.jia.fatigue',
        '容易疲劳，须注意肝胆。',
      ),
      _editorial_reference(
        'editorial.tiangan.jia.annual_checkup',
        '请注意可能会有（胆、头）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.jia.personality',
        '仁慈富同情心，个性积极，精力旺盛，外文雅内好强，刚直正气，重感情，具开拓精神，固执独断，善于表现自己，待人大方，精明能干。',
      ),
      _unverified_reference(
        'legacy.tiangan.jia.ambition',
        '甲木之人，有上进心，有志气，有骨气，心地善良，占有欲强。',
      ),
      _unverified_reference(
        'legacy.tiangan.jia.weak_state',
        '如果甲木偏弱（如局中无印、比来生助，日主反而被官、杀克制的），说明这个人胆小怕事、独善其身、性格也较忧郁，常常是哑巴吃黄连，敢怒不敢言。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.tiangan.jia.strong_state',
        '如果甲木偏旺，说明这人长得高大，骨骼也粗大，但瘦而不胖，平常不苟言笑，做事一板一眼、心直口快、不善变通、容易吃亏。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.tiangan.jia.balanced_state',
        '如果日干甲木中和，生泄适度，说明此人性格较中庸，刚柔并济，容易成功。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
  },
  Tiangan.乙: {
    'general': [
      _tiangan_definition(
        'tiangan.yi.definition',
        '乙为阴木。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69,
      ),
      _unverified_reference(
        'legacy.tiangan.yi.vine_grass_image',
        '乙如蔓藤花草。',
      ),
      _editorial_reference(
        'editorial.tiangan.yi.annual_checkup',
        '请注意可能会有（肝、颈）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.yi.personality',
        '仁慈富同情心，干劲十足，外文雅内好强，温柔含蓄，坚忍礼让，消极善妒，优柔寡断，感情脆弱，做事心思细腻。',
      ),
      _unverified_reference(
        'legacy.tiangan.yi.adaptability',
        '对环境的适应能力很强，像草一样春风吹又生。乙木不像甲木硬碰硬的来，甲木容易被摧折，乙木更具柔韧性/适应性。',
      ),
      _unverified_reference(
        'legacy.tiangan.yi.opportunity',
        '乙木之人秀丽柔弱，（可能）不禁风雨，但善于利用环境、适应环境、把握机遇、因势利导等。',
      ),
    ],
  },
  Tiangan.丙: {
    'general': [
      _tiangan_definition(
        'tiangan.bing.definition',
        '丙为阳火。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69,
      ),
      _historical_symbol(
        'tiangan.bing.sun_symbol',
        '丙火像太阳。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69,
      ),
      _unverified_reference(
        'legacy.tiangan.bing.frost_snow_image',
        '丙火既不怕寒霜也不忌冷雪。',
      ),
      _editorial_reference(
        'editorial.tiangan.bing.heart_attention',
        '须注意心、血压、小肠、眼睛及肩的问题。',
      ),
      _editorial_reference(
        'editorial.tiangan.bing.annual_checkup',
        '请注意可能会有（小肠、肩膀、血压）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.bing.temper',
        '性格不拘小节大而化之，为朋友的忠实听众，但听后常不当一回事，且易这耳进那耳出，易发脾气，却也收得快。',
      ),
      _unverified_reference(
        'legacy.tiangan.bing.sociability',
        '热情有礼，豪爽，乐观进取，好胜心强，急躁易冲动，缺乏耐性，待人耿直，善交朋友，光明磊落不喜掩饰。',
      ),
      _unverified_reference(
        'legacy.tiangan.bing.impatience',
        '丙火之人性格急躁，喜欢争上风，对人热情大方，有礼貌，好打抱不平。',
      ),
    ],
  },
  Tiangan.丁: {
    'general': [
      _tiangan_definition(
        'tiangan.ding.definition',
        '丁为阴火。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _historical_symbol(
        'tiangan.ding.lamp_symbol',
        '丁火有烛灯之象。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _unverified_reference(
        'legacy.tiangan.ding.firefly_image',
        '丁火如萤火，虽没丙火强烈，但却易让人接受。',
      ),
      _editorial_reference(
        'editorial.tiangan.ding.heart_attention',
        '须注意心、血压、小肠、眼睛等问题。',
      ),
      _editorial_reference(
        'editorial.tiangan.ding.annual_checkup',
        '请注意可能会有（心脏、血压）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.ding.personality',
        '温文尔雅，敦厚纯朴，重信守义，沉静友善，保守勤奋，易任性逞强，热情谦恭，有时又流于虚伪叛逆。',
      ),
      _unverified_reference(
        'legacy.tiangan.ding.weak_state',
        '丁火日主若是身弱，就发挥不出丁火的优点，如果又见克太多，则会变成胆小，多愁多虑。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.tiangan.ding.emotional_expression',
        '内心感情丰富且不善表达于言词，善忌妒，人称闷骚型。',
      ),
    ],
  },
  Tiangan.戊: {
    'general': [
      _tiangan_definition(
        'tiangan.wu.definition',
        '戊为阳土。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _historical_symbol(
        'tiangan.wu.wall_symbol',
        '戊土有城墙之象。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _unverified_reference(
        'legacy.tiangan.wu.earth_image',
        '戊土为大地，取坚固厚实的意思。',
      ),
      _unverified_reference(
        'legacy.tiangan.wu.mountain_dryness',
        '戊土为阳土，其特性为高山之土，因近太阳故为燥土。',
      ),
      _editorial_reference(
        'editorial.tiangan.wu.annual_checkup',
        '请注意可能会有（脾胃、腹部、胸背部、身体上半身两侧）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.wu.personality',
        '敦厚朴实，重信讲义，忠实至诚，宽大包容，乐于助人，反应迟钝，不懂变通，做事细心，胆小怕事。',
      ),
      _unverified_reference(
        'legacy.tiangan.wu.steadfastness',
        '喜欢旧事物，也不喜欢搬迁。承诺别人则会守信到底，决不拖拉。',
      ),
    ],
  },
  Tiangan.己: {
    'general': [
      _tiangan_definition(
        'tiangan.ji.definition',
        '己为阴土。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _unverified_reference(
        'legacy.tiangan.ji.yin_softness',
        '己性阴柔。',
      ),
      _editorial_reference(
        'editorial.tiangan.ji.digestive_attention',
        '须注意脾胃、腹部。',
      ),
      _editorial_reference(
        'editorial.tiangan.ji.annual_checkup',
        '请注意可能会（脾、腹）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.ji.personality',
        '个性谨慎，温和重义，外随和内坚忍。',
      ),
      _unverified_reference(
        'legacy.tiangan.ji.adverse_state',
        '己土状态不好时，容易猜疑妒忌，懒怠固执，欠果断。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.tiangan.ji.reserve',
        '举止较淡定，寡言，不重修饰，慢慢相处方能发现TA的优点。',
      ),
    ],
  },
  Tiangan.庚: {
    'general': [
      _tiangan_definition(
        'tiangan.geng.definition',
        '庚为阳金。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _unverified_reference(
        'legacy.tiangan.geng.iron_image',
        '庚金如刚铁，无坚不摧，个性刚烈，豪侠仗义。',
      ),
      _editorial_reference(
        'editorial.tiangan.geng.annual_checkup',
        '请注意可能会有（大肠、脐轮）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.geng.personality',
        '表情严肃，坚持原则，积极进取，自尊心强，好胜，不讲情面，刚毅重义气，易怒，果断，善权谋，好结交朋友，宁折不弯。',
      ),
      _unverified_reference(
        'legacy.tiangan.geng.regulated_transit',
        '如果庚金日主盘中的庚金行运有制有化，后天有教养，性虽刚但不逼人，有义气但不鲁莽惹祸。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
  },
  Tiangan.辛: {
    'general': [
      _tiangan_definition(
        'tiangan.xin.definition',
        '辛为阴金。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _historical_symbol(
        'tiangan.xin.jewel_symbol',
        '辛金有珠玉之象。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _unverified_reference(
        'legacy.tiangan.xin.noble_beauty',
        '辛金高贵且艳丽。',
      ),
      _editorial_reference(
        'editorial.tiangan.xin.annual_checkup',
        '请注意可能会有（肺、屁股）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.xin.appearance',
        '为人好面子，注重衣着，易有异性缘，处事刚柔并济，粗中有细。',
      ),
      _unverified_reference(
        'legacy.tiangan.xin.personality',
        '坦直无私，脚踏实地，恒心毅力，稳重，刻薄寡情，易生不平。做事细腻认真，精明能干。',
      ),
    ],
  },
  Tiangan.壬: {
    'general': [
      _tiangan_definition(
        'tiangan.ren.definition',
        '壬为阳水。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _historical_symbol(
        'tiangan.ren.river_symbol',
        '壬水有汪洋百川之象。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _editorial_reference(
        'editorial.tiangan.ren.urinary_attention',
        '应注意膀胱和肾（泌尿系统）。',
      ),
      _editorial_reference(
        'editorial.tiangan.ren.annual_checkup',
        '请注意可能会有(膀胱、胫)方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.ren.personality',
        '富心机，深藏不露，外表冷淡，机智灵敏，多才多艺，冲动易怒。',
      ),
      _unverified_reference(
        'legacy.tiangan.ren.achievement',
        '才智高，理性佳，重责任，交际广，人缘佳，能见风转舵，反应灵敏，善算计，外表平静，胆大心细，事业容易有成就，好求变，易激动，定性差，个性不服输，做事大而化之。',
      ),
      _unverified_reference(
        'legacy.tiangan.ren.resourcefulness',
        '为人热情澎湃，足智多谋，多才多艺，善钻营。',
      ),
      _unverified_reference(
        'legacy.tiangan.ren.weak_state',
        '若壬水日主身弱又克太过，乖巧聪明，胆小怕事，魄力不足成大事。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
      _unverified_reference(
        'legacy.tiangan.ren.strong_state',
        '若壬水日主身旺，水太过，就如脱缰之马，又喜走捷径，易失足。水性太过的，聪明狡诈，任性风流。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
  },
  Tiangan.癸: {
    'general': [
      _tiangan_definition(
        'tiangan.gui.definition',
        '癸为阴水。',
        _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,
      ),
      _unverified_reference(
        'legacy.tiangan.gui.stream_rain_image',
        '癸水如涓涓细流，如雨水。',
      ),
      _editorial_reference(
        'editorial.tiangan.gui.annual_checkup',
        '请注意可能会有（肾脏、足）方面的疾病，假如真的有，建议您每年要定期做健康检查。',
      ),
    ],
    'personality': [
      _unverified_reference(
        'legacy.tiangan.gui.personality',
        '聪明，看似平静，其实内心澎湃汹涌，巧于临机应变，有远见，细水长流，个性内向保守，节俭，有洁癖，正直而踏实，相对而言，也显得感情脆弱，有点神经质，喜欢幻想，拥有浪漫情怀。',
      ),
      _unverified_reference(
        'legacy.tiangan.gui.resourcefulness',
        '聪颖智巧，隐忍含蓄，内向斯文，巧于心机，深思多虑，沉静节约，贪小便宜，好胜逞强，有耐力恒心，做事认真，学识多广。',
      ),
      _unverified_reference(
        'legacy.tiangan.gui.restraint',
        '阴柔，宁静，不冲动，有耐心，处事手法好，以柔至刚，深思熟虑，以进为退，喜后发制人。',
      ),
      _unverified_reference(
        'legacy.tiangan.gui.strong_unfavorable_state',
        '若癸水日主身旺癸为忌神，为人表面心如止水，内心想入非非，好幻想，不切实际，喜钻牛角尖。',
        conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
      ),
    ],
  },
})


def _project_texts(
  items: list[_DescriptionItem],
  include_reference_only: bool,
) -> list[str]:
  assert isinstance(include_reference_only, bool)
  return [
    item.text if isinstance(item, _DescriptionClaim) else item
    for item in items
    if (
      include_reference_only
      or not isinstance(item, _DescriptionClaim)
      or (
        item.output is _DescriptionOutput.DEFAULT
        and not item.conditions
      )
    )
  ]


def _project_shishen_description(
  description: _ShishenCorpusDescription,
  include_reference_only: bool,
) -> ShishenDescription:
  return {
    'general':        _project_texts(description['general'], include_reference_only),
    'in_good_status': _project_texts(description['in_good_status'], include_reference_only),
    'in_bad_status':  _project_texts(description['in_bad_status'], include_reference_only),
    'relationship':   _project_texts(description['relationship'], include_reference_only),
  }


def _project_tiangan_description(
  description: _TianganCorpusDescription,
  include_reference_only: bool,
) -> TianganDescription:
  return {
    'general':     _project_texts(description['general'], include_reference_only),
    'personality': _project_texts(description['personality'], include_reference_only),
  }


def _complete_shishen_description(shishen: Shishen) -> ShishenDescription:
  assert isinstance(shishen, Shishen)
  return _project_shishen_description(_SHISHEN_DESCRIPTION_CORPUS[shishen], include_reference_only=True)


def _complete_tiangan_description(tg: Tiangan) -> TianganDescription:
  assert isinstance(tg, Tiangan)
  return _project_tiangan_description(_TIANGAN_DESCRIPTION_CORPUS[tg], include_reference_only=True)


# Public tables contain only descriptions eligible for default output. The mappings are
# frozen, but their entry dictionaries and lists are mutable; direct readers must not
# mutate either. `Interpreter.interpret_*` returns deep copies that callers can modify.
# 公开表只含可默认输出的语料。映射冻结，但条目字典和列表仍可变；直接读取者不得修改。
# `Interpreter.interpret_*` 返回深拷贝，调用方可放心修改。
SHISHEN_DESCRIPTIONS: Final[frozendict[Shishen, ShishenDescription]] = frozendict({
  shishen: _project_shishen_description(description, include_reference_only=False)
  for shishen, description in _SHISHEN_DESCRIPTION_CORPUS.items()
})

TIANGAN_DESCRIPTIONS: Final[frozendict[Tiangan, TianganDescription]] = frozendict({
  tg: _project_tiangan_description(description, include_reference_only=False)
  for tg, description in _TIANGAN_DESCRIPTION_CORPUS.items()
})
