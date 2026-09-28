# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_interpreter.py

from collections.abc import Sequence
from hashlib import sha256
from typing import Final, cast

import pytest

from bazi.common import frozendict
from bazi.descriptions import (
  ShishenDescription,
  TianganDescription,
  _DescriptionClaim,
  _DescriptionCondition,
  _DescriptionOutput,
  _DescriptionSource,
  _DescriptionTextLayer,
  _DESCRIPTION_SOURCES,
  _SHISHEN_DESCRIPTION_CORPUS,
  _TIANGAN_DESCRIPTION_CORPUS,
  _project_texts,
  SHISHEN_DESCRIPTIONS,
  TIANGAN_DESCRIPTIONS,
)
from bazi.defines import Tiangan, Shishen
from bazi.interpreter import Interpreter


_EDITORIAL_REFERENCE_CASES: Final[tuple[tuple[Shishen | Tiangan, str, str], ...]] = (
  (Shishen.食神, 'in_bad_status', '食神之人头脑活动非常旺盛，想东想西，因此食神过旺的人，易焦虑失眠。'),
  (Shishen.正官, 'general', '如在命盘中也见七杀，则称为官杀混杂，也许代表在公司里受排挤、职场不顺，或有官司是非。'),
  (Shishen.正官, 'general', '对女命而言，由于官杀代表男朋友/丈夫，所以官杀混杂也代表在感情上纠结，或是在感情上可能会出轨。'),
  (Shishen.七杀, 'general', '官司、法院、牢狱、军队、公检法、忌恨、小人、恶人、凶祸、外伤、疾病。'),
  (Shishen.七杀, 'general', '如在命盘中也见正官，则称为官杀混杂，也许代表在公司里受排挤、职场不顺，或有官司是非。'),
  (Shishen.七杀, 'general', '对女命而言，由于官杀代表男朋友/丈夫，所以官杀混杂也代表在感情上纠结，或是在感情上可能会出轨。'),
  (Shishen.七杀, 'in_bad_status', '七杀代表突如其来的打击、攻击、意外灾害等外在环境的变故。'),
  (Tiangan.甲, 'general', '容易疲劳，须注意肝胆。'),
  (Tiangan.甲, 'general', '请注意可能会有（胆、头）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.乙, 'general', '请注意可能会有（肝、颈）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.丙, 'general', '须注意心、血压、小肠、眼睛及肩的问题。'),
  (Tiangan.丙, 'general', '请注意可能会有（小肠、肩膀、血压）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.丁, 'general', '须注意心、血压、小肠、眼睛等问题。'),
  (Tiangan.丁, 'general', '请注意可能会有（心脏、血压）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.戊, 'general', '请注意可能会有（脾胃、腹部、胸背部、身体上半身两侧）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.己, 'general', '须注意脾胃、腹部。'),
  (Tiangan.己, 'general', '请注意可能会（脾、腹）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.庚, 'general', '请注意可能会有（大肠、脐轮）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.辛, 'general', '请注意可能会有（肺、屁股）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.壬, 'general', '应注意膀胱和肾（泌尿系统）。'),
  (Tiangan.壬, 'general', '请注意可能会有(膀胱、胫)方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
  (Tiangan.癸, 'general', '请注意可能会有（肾脏、足）方面的疾病，假如真的有，建议您每年要定期做健康检查。'),
)

_SHISHEN_DEFINITIONS: Final[tuple[tuple[Shishen, str, str], ...]] = (
  (Shishen.比肩, 'shishen.bijian.definition', '比肩为与日主五行、阴阳皆相同者。'),
  (Shishen.食神, 'shishen.shishen.definition', '食神为日主所生且阴阳相同者。'),
  (Shishen.伤官, 'shishen.shangguan.definition', '伤官为日主所生且阴阳相异者。'),
  (Shishen.正财, 'shishen.zhengcai.definition', '正财为日主所克且阴阳相异者。'),
  (Shishen.偏财, 'shishen.piancai.definition', '偏财为日主所克且阴阳相同者。'),
  (Shishen.正官, 'shishen.zhengguan.definition', '正官为克制日主且阴阳相异者。'),
  (Shishen.七杀, 'shishen.qisha.definition', '七杀为克制日主且阴阳相同者。'),
  (Shishen.正印, 'shishen.zhengyin.definition', '正印为生助日主且阴阳相异者。'),
  (Shishen.偏印, 'shishen.pianyin.definition', '偏印为生助日主且阴阳相同者。'),
)

_TIANGAN_DEFINITIONS: Final[
  tuple[tuple[Tiangan, str, str, _DescriptionSource], ...]
] = (
  (Tiangan.甲, 'tiangan.jia.definition', '甲为阳木。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69),
  (Tiangan.乙, 'tiangan.yi.definition', '乙为阴木。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69),
  (Tiangan.丙, 'tiangan.bing.definition', '丙为阳火。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69),
  (Tiangan.丁, 'tiangan.ding.definition', '丁为阴火。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.戊, 'tiangan.wu.definition', '戊为阳土。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.己, 'tiangan.ji.definition', '己为阴土。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.庚, 'tiangan.geng.definition', '庚为阳金。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.辛, 'tiangan.xin.definition', '辛为阴金。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.壬, 'tiangan.ren.definition', '壬为阳水。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.癸, 'tiangan.gui.definition', '癸为阴水。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
)

_HISTORICAL_SYMBOL_CASES: Final[
  tuple[tuple[Tiangan, str, str, _DescriptionSource], ...]
] = (
  (Tiangan.丙, 'tiangan.bing.sun_symbol', '丙火像太阳。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69),
  (Tiangan.丁, 'tiangan.ding.lamp_symbol', '丁火有烛灯之象。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.戊, 'tiangan.wu.wall_symbol', '戊土有城墙之象。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.辛, 'tiangan.xin.jewel_symbol', '辛金有珠玉之象。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
  (Tiangan.壬, 'tiangan.ren.river_symbol', '壬水有汪洋百川之象。', _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70),
)

_SOURCE_EXCERPTS: Final[frozendict[_DescriptionSource, str]] = frozendict({
  _DescriptionSource.EDITORIAL: 'Repository-original editorial prose.',
  _DescriptionSource.YUANHAI_ZIPING_RELATIONS: '生我者為正印偏印我生者為傷官食神尅我者為正官七殺我尅者為偏財正財比肩者為劫財敗財其法陽見陰為正陰見陽為正陽見陽為偏陰見陰為偏如甲丙戊庚壬屬陽乙丁己辛癸屬陰是也',
  _DescriptionSource.YUANHAI_ZIPING_STEM_TABLE: '天干五陽通變天干五陰通變',
  _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69: '甲木天干作首排乙木根荄種得深丙火明明一太陽',
  _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70: '丁火其形一燭燈戊土城墻堤岸同己土田園屬四維庚金頑鈍性偏剛辛金珠玉性虛靈壬水汪洋併百川癸水應非雨露麼',
  _DescriptionSource.MINGLI_TANYUAN_STEM_BASICS: '甲丙戊庚壬爲陽乙丁己辛癸爲陰甲乙屬木爲東方丙丁屬火爲南方戊己屬土爲中央庚辛屬金爲西方壬癸屬水爲北方',
  _DescriptionSource.MINGLI_TANYUAN_SHISHEN_DEFINITIONS: '陽見陰陰見陽則爲正陽見陽陰見陰則爲偏與我比者爲比肩爲劫財敗財我生者爲傷官食神我尅者爲正財偏財尅我者爲正官偏官生我者爲正印偏印',
})

_REFERENCE_ONLY_CASES: Final[tuple[tuple[Shishen | Tiangan, str, str], ...]] = (
  _EDITORIAL_REFERENCE_CASES
  + tuple((tg, 'general', text) for tg, _, text, _ in _HISTORICAL_SYMBOL_CASES)
)


def _as_mapping(description: ShishenDescription | TianganDescription) -> dict[str, list[str]]:
  return cast(dict[str, list[str]], description)


def _description_count(descriptions: Sequence[ShishenDescription | TianganDescription]) -> int:
  return sum(len(texts) for description in descriptions for texts in _as_mapping(description).values())


def _all_claims() -> list[tuple[Shishen | Tiangan, str, _DescriptionClaim]]:
  claims: list[tuple[Shishen | Tiangan, str, _DescriptionClaim]] = []
  for shishen, shishen_description in _SHISHEN_DESCRIPTION_CORPUS.items():
    for shishen_field in ('general', 'in_good_status', 'in_bad_status', 'relationship'):
      claims.extend(
        (shishen, shishen_field, item)
        for item in shishen_description[shishen_field]
        if isinstance(item, _DescriptionClaim)
      )
  for tg, tg_description in _TIANGAN_DESCRIPTION_CORPUS.items():
    for tg_field in ('general', 'personality'):
      claims.extend(
        (tg, tg_field, item)
        for item in tg_description[tg_field]
        if isinstance(item, _DescriptionClaim)
      )
  return claims


def _complete_corpus_fingerprint() -> str:
  rows: list[str] = []
  for shishen in Shishen:
    description = Interpreter.interpret_shishen(shishen, include_reference_only=True)
    for field, texts in _as_mapping(description).items():
      rows.extend(f'S:{shishen}:{field}:{text}' for text in texts)
  for tg in Tiangan:
    tg_description = Interpreter.interpret_tiangan(tg, include_reference_only=True)
    for field, texts in _as_mapping(tg_description).items():
      rows.extend(f'T:{tg}:{field}:{text}' for text in texts)
  return sha256('\n'.join(rows).encode()).hexdigest()


def test_interpret_shishen() -> None:
  for shishen in Shishen:
    result: ShishenDescription = Interpreter.interpret_shishen(shishen)

    keys: list[str] = ['general', 'in_good_status', 'in_bad_status', 'relationship']
    for k in keys:
      assert k in result
      assert isinstance(result[k], list) # type: ignore # mypy complains.
      assert len(result[k]) >= 1 # type: ignore # mypy complains.
      for d in result[k]: # type: ignore # mypy complains.
        assert isinstance(d, str)
        assert len(d) >= 1

        assert d == d.strip(), f'"{d}" not stripped' # No space at the beginning or end.
        assert d[-1] == '。', f'"{d}" not ending with "。"' # End with '。'.

    assert result == Interpreter.interpret_shishen(shishen)


def test_interpret_tiangan() -> None:
  for tg in Tiangan:
    result: TianganDescription = Interpreter.interpret_tiangan(tg)

    keys: list[str] = ['general', 'personality']
    for k in keys:
      assert k in result
      assert isinstance(result[k], list) # type: ignore # mypy complains.
      assert len(result[k]) >= 1 # type: ignore # mypy complains.
      for d in result[k]: # type: ignore # mypy complains.
        assert isinstance(d, str)
        assert len(d) >= 1

        assert d == d.strip(), f'"{d}" not stripped' # No space at the beginning or end.
        assert d[-1] == '。', f'"{d}" not ending with "。"' # End with '。'.

    assert result == Interpreter.interpret_tiangan(tg)


def test_interpret_shishen_negative() -> None:
  with pytest.raises(TypeError):
    Interpreter.interpret_shishen('比肩') # type: ignore


def test_interpret_tiangan_negative() -> None:
  with pytest.raises(TypeError):
    Interpreter.interpret_tiangan('甲') # type: ignore


def test_reference_only_descriptions_are_opt_in() -> None:
  reference_only: dict[tuple[Shishen | Tiangan, str], list[str]] = {}
  for subject, field, text in _REFERENCE_ONLY_CASES:
    reference_only.setdefault((subject, field), []).append(text)

  default_shishen: list[ShishenDescription] = []
  complete_shishen: list[ShishenDescription] = []
  for shishen in Shishen:
    default = Interpreter.interpret_shishen(shishen)
    complete = Interpreter.interpret_shishen(shishen, include_reference_only=True)
    assert default == SHISHEN_DESCRIPTIONS[shishen]
    for field in ('general', 'in_good_status', 'in_bad_status', 'relationship'):
      excluded = reference_only.get((shishen, field), [])
      assert _as_mapping(default)[field] == [
        text for text in _as_mapping(complete)[field] if text not in excluded
      ]
    default_shishen.append(default)
    complete_shishen.append(complete)

  default_tiangan: list[TianganDescription] = []
  complete_tiangan: list[TianganDescription] = []
  for tg in Tiangan:
    tg_default = Interpreter.interpret_tiangan(tg)
    tg_complete = Interpreter.interpret_tiangan(tg, include_reference_only=True)
    assert tg_default == TIANGAN_DESCRIPTIONS[tg]
    for tg_field in ('general', 'personality'):
      excluded = reference_only.get((tg, tg_field), [])
      assert _as_mapping(tg_default)[tg_field] == [
        text for text in _as_mapping(tg_complete)[tg_field] if text not in excluded
      ]
    default_tiangan.append(tg_default)
    complete_tiangan.append(tg_complete)

  assert _description_count(default_shishen) == 212
  assert _description_count(complete_shishen) == 219
  assert _description_count(default_tiangan) == 52
  assert _description_count(complete_tiangan) == 72


def test_reference_only_is_keyword_only() -> None:
  with pytest.raises(TypeError):
    Interpreter.interpret_shishen(Shishen.食神, True) # type: ignore
  with pytest.raises(TypeError):
    Interpreter.interpret_tiangan(Tiangan.甲, True) # type: ignore


def test_reference_only_claims() -> None:
  claims = [
    (subject, field, claim)
    for subject, field, claim in _all_claims()
    if claim.output is _DescriptionOutput.REFERENCE_ONLY
  ]

  assert {
    (subject, field, claim.text)
    for subject, field, claim in claims
  } == set(_REFERENCE_ONLY_CASES)
  assert [
    (subject, field, claim.text)
    for subject, field, claim in claims
    if claim.sources == (_DescriptionSource.EDITORIAL,)
  ] == list(_EDITORIAL_REFERENCE_CASES)


def test_provenance_pilot_claims() -> None:
  shishen_definition_sources = (
    _DescriptionSource.YUANHAI_ZIPING_RELATIONS,
    _DescriptionSource.MINGLI_TANYUAN_SHISHEN_DEFINITIONS,
  )
  for shishen, claim_id, text in _SHISHEN_DEFINITIONS:
    claim = _SHISHEN_DESCRIPTION_CORPUS[shishen]['general'][0]
    assert isinstance(claim, _DescriptionClaim)
    assert claim.claim_id == claim_id
    assert claim.text == text
    assert claim.sources == shishen_definition_sources
    assert claim.attribution == '《渊海子平》与《命理探源》十神定义'
    assert claim.output is _DescriptionOutput.DEFAULT
    assert Interpreter.interpret_shishen(shishen)['general'][0] == text
    assert Interpreter.interpret_shishen(
      shishen,
      include_reference_only=True,
    )['general'][0] == text

  assert 'shishen.jiecai.definition' not in {
    claim.claim_id for _, _, claim in _all_claims()
  }

  for tg, claim_id, text, yuan_hai_source in _TIANGAN_DEFINITIONS:
    claim = _TIANGAN_DESCRIPTION_CORPUS[tg]['general'][0]
    assert isinstance(claim, _DescriptionClaim)
    assert claim.claim_id == claim_id
    assert claim.text == text
    assert claim.sources == (
      yuan_hai_source,
      _DescriptionSource.MINGLI_TANYUAN_STEM_BASICS,
    )
    assert claim.attribution == '《渊海子平》与《命理探源》天干定义'
    assert claim.output is _DescriptionOutput.DEFAULT
    assert Interpreter.interpret_tiangan(tg)['general'][0] == text
    assert Interpreter.interpret_tiangan(
      tg,
      include_reference_only=True,
    )['general'][0] == text

  claims_by_id = {claim.claim_id: claim for _, _, claim in _all_claims()}
  for tg, claim_id, text, source in _HISTORICAL_SYMBOL_CASES:
    claim = claims_by_id[claim_id]
    assert claim.text == text
    assert claim.sources == (source,)
    assert claim.attribution == '《渊海子平·十干体象》'
    assert claim.output is _DescriptionOutput.REFERENCE_ONLY
    assert text not in Interpreter.interpret_tiangan(tg)['general']
    assert text in Interpreter.interpret_tiangan(
      tg,
      include_reference_only=True,
    )['general']


def test_provenance_integrity() -> None:
  assert set(_DESCRIPTION_SOURCES) == set(_DescriptionSource)
  assert {
    source: record.excerpt
    for source, record in _DESCRIPTION_SOURCES.items()
  } == dict(_SOURCE_EXCERPTS)
  assert _DESCRIPTION_SOURCES[_DescriptionSource.YUANHAI_ZIPING_RELATIONS].locator == (
    'PDF p. 6, right leaf, paragraph beginning “生我者為正印偏印”'
  )
  assert _DESCRIPTION_SOURCES[_DescriptionSource.YUANHAI_ZIPING_STEM_TABLE].locator == (
    'PDF p. 8, “天干五阳通变” and “天干五阴通变” tables'
  )
  assert _DESCRIPTION_SOURCES[
    _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69
  ].locator == 'PDF p. 69, left leaf, “十干体象”'
  assert _DESCRIPTION_SOURCES[
    _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70
  ].locator == 'PDF p. 70, both leaves, “十干体象”'
  assert _DESCRIPTION_SOURCES[_DescriptionSource.MINGLI_TANYUAN_STEM_BASICS].locator == (
    'PDF pp. 33 and 36, “干枝阴阳” and “干枝五行及四时方位”'
  )
  assert _DESCRIPTION_SOURCES[
    _DescriptionSource.MINGLI_TANYUAN_SHISHEN_DEFINITIONS
  ].locator == (
    'PDF pp. 66-70, “十干生克定名”'
  )
  for source in (
    _DescriptionSource.MINGLI_TANYUAN_STEM_BASICS,
    _DescriptionSource.MINGLI_TANYUAN_SHISHEN_DEFINITIONS,
  ):
    assert _DESCRIPTION_SOURCES[source].work == '《命理探源》'
    assert _DESCRIPTION_SOURCES[source].edition == '版心题《命理探原》'

  for source, record in _DESCRIPTION_SOURCES.items():
    assert all((
      record.work,
      record.attribution,
      record.edition,
      record.locator,
      record.url,
      record.excerpt,
      record.supports,
      record.limitations,
    ))
    assert record.text_layer is (
      _DescriptionTextLayer.EDITORIAL
      if source is _DescriptionSource.EDITORIAL
      else _DescriptionTextLayer.BAIWEN
    )

  claims = [claim for _, _, claim in _all_claims()]
  claim_ids = [claim.claim_id for claim in claims]
  assert len(claim_ids) == len(set(claim_ids))
  for claim in claims:
    assert claim.claim_id
    assert claim.text
    assert claim.attribution
    assert claim.sources
    assert all(source in _DESCRIPTION_SOURCES for source in claim.sources)
    if claim.output is _DescriptionOutput.DEFAULT:
      assert not claim.conditions
      assert len({
        _DESCRIPTION_SOURCES[source].lineage
        for source in claim.sources
      }) >= 2


def test_projection_rejects_unmet_conditions_and_reference_only_claims() -> None:
  default = _DescriptionClaim(
    claim_id='test.default',
    text='Default claim.',
    sources=(_DescriptionSource.EDITORIAL,),
    attribution='Test',
    conditions=(),
    output=_DescriptionOutput.DEFAULT,
  )
  conditional = _DescriptionClaim(
    claim_id='test.conditional',
    text='Conditional claim.',
    sources=(_DescriptionSource.EDITORIAL,),
    attribution='Test',
    conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
    output=_DescriptionOutput.DEFAULT,
  )
  reference = _DescriptionClaim(
    claim_id='test.reference',
    text='Reference-only claim.',
    sources=(_DescriptionSource.EDITORIAL,),
    attribution='Test',
    conditions=(),
    output=_DescriptionOutput.REFERENCE_ONLY,
  )

  items: list[str | _DescriptionClaim] = ['Legacy claim.', default, conditional, reference]
  assert _project_texts(items, include_reference_only=False) == [
    'Legacy claim.',
    'Default claim.',
  ]
  assert _project_texts(items, include_reference_only=True) == [
    'Legacy claim.',
    'Default claim.',
    'Conditional claim.',
    'Reference-only claim.',
  ]


def test_complete_corpus_is_conserved() -> None:
  # Pin the complete corpus text and order; update the hash only for intentional edits.
  assert _complete_corpus_fingerprint() == '78603ba30dcd8f4240897ae0b45e9d5d9fcc535641cb1463b68feff6ae06d89d'


def test_reference_only_deepcopy() -> None:
  shishen = Interpreter.interpret_shishen(Shishen.食神, include_reference_only=True)
  shishen['in_bad_status'].append('污染内容')
  assert '污染内容' not in Interpreter.interpret_shishen(
    Shishen.食神,
    include_reference_only=True,
  )['in_bad_status']

  tg = Interpreter.interpret_tiangan(Tiangan.甲, include_reference_only=True)
  tg['general'].append('污染内容')
  assert '污染内容' not in Interpreter.interpret_tiangan(
    Tiangan.甲,
    include_reference_only=True,
  )['general']


def test_reference_only_negative() -> None:
  with pytest.raises(TypeError):
    Interpreter.interpret_shishen(Shishen.食神, include_reference_only=1) # type: ignore
  with pytest.raises(TypeError):
    Interpreter.interpret_tiangan(Tiangan.甲, include_reference_only=1) # type: ignore


def test_public_tables_are_frozen() -> None:
  # The public description tables are frozen: reassigning an entry must fail, and
  # mutating a returned description must not corrupt them.
  # 公开描述表是冻结的：覆盖条目必须报错；修改返回的描述不能污染它们。
  with pytest.raises(TypeError):
    SHISHEN_DESCRIPTIONS[Shishen.比肩] = SHISHEN_DESCRIPTIONS[Shishen.比肩] # type: ignore # mypy complains.
  with pytest.raises(TypeError):
    TIANGAN_DESCRIPTIONS[Tiangan.甲] = TIANGAN_DESCRIPTIONS[Tiangan.甲] # type: ignore # mypy complains.

  mutated_shishen: ShishenDescription = Interpreter.interpret_shishen(Shishen.比肩)
  mutated_shishen['general'].append('污染内容')
  assert '污染内容' not in Interpreter.interpret_shishen(Shishen.比肩)['general']

  mutated_tg: TianganDescription = Interpreter.interpret_tiangan(Tiangan.甲)
  mutated_tg['general'].append('污染内容')
  assert '污染内容' not in Interpreter.interpret_tiangan(Tiangan.甲)['general']
