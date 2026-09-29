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

_UNVERIFIED_TIANGAN_CLAIM_IDS: Final[tuple[tuple[Tiangan, str, str], ...]] = (
  (Tiangan.甲, 'general', 'legacy.tiangan.jia.tree_image'),
  (Tiangan.甲, 'personality', 'legacy.tiangan.jia.personality'),
  (Tiangan.甲, 'personality', 'legacy.tiangan.jia.ambition'),
  (Tiangan.甲, 'personality', 'legacy.tiangan.jia.weak_state'),
  (Tiangan.甲, 'personality', 'legacy.tiangan.jia.strong_state'),
  (Tiangan.甲, 'personality', 'legacy.tiangan.jia.balanced_state'),
  (Tiangan.乙, 'general', 'legacy.tiangan.yi.vine_grass_image'),
  (Tiangan.乙, 'personality', 'legacy.tiangan.yi.personality'),
  (Tiangan.乙, 'personality', 'legacy.tiangan.yi.adaptability'),
  (Tiangan.乙, 'personality', 'legacy.tiangan.yi.opportunity'),
  (Tiangan.丙, 'general', 'legacy.tiangan.bing.frost_snow_image'),
  (Tiangan.丙, 'personality', 'legacy.tiangan.bing.temper'),
  (Tiangan.丙, 'personality', 'legacy.tiangan.bing.sociability'),
  (Tiangan.丙, 'personality', 'legacy.tiangan.bing.impatience'),
  (Tiangan.丁, 'general', 'legacy.tiangan.ding.firefly_image'),
  (Tiangan.丁, 'personality', 'legacy.tiangan.ding.personality'),
  (Tiangan.丁, 'personality', 'legacy.tiangan.ding.weak_state'),
  (Tiangan.丁, 'personality', 'legacy.tiangan.ding.emotional_expression'),
  (Tiangan.戊, 'general', 'legacy.tiangan.wu.earth_image'),
  (Tiangan.戊, 'general', 'legacy.tiangan.wu.mountain_dryness'),
  (Tiangan.戊, 'personality', 'legacy.tiangan.wu.personality'),
  (Tiangan.戊, 'personality', 'legacy.tiangan.wu.steadfastness'),
  (Tiangan.己, 'general', 'legacy.tiangan.ji.yin_softness'),
  (Tiangan.己, 'personality', 'legacy.tiangan.ji.personality'),
  (Tiangan.己, 'personality', 'legacy.tiangan.ji.adverse_state'),
  (Tiangan.己, 'personality', 'legacy.tiangan.ji.reserve'),
  (Tiangan.庚, 'general', 'legacy.tiangan.geng.iron_image'),
  (Tiangan.庚, 'personality', 'legacy.tiangan.geng.personality'),
  (Tiangan.庚, 'personality', 'legacy.tiangan.geng.regulated_transit'),
  (Tiangan.辛, 'general', 'legacy.tiangan.xin.noble_beauty'),
  (Tiangan.辛, 'personality', 'legacy.tiangan.xin.appearance'),
  (Tiangan.辛, 'personality', 'legacy.tiangan.xin.personality'),
  (Tiangan.壬, 'personality', 'legacy.tiangan.ren.personality'),
  (Tiangan.壬, 'personality', 'legacy.tiangan.ren.achievement'),
  (Tiangan.壬, 'personality', 'legacy.tiangan.ren.resourcefulness'),
  (Tiangan.壬, 'personality', 'legacy.tiangan.ren.weak_state'),
  (Tiangan.壬, 'personality', 'legacy.tiangan.ren.strong_state'),
  (Tiangan.癸, 'general', 'legacy.tiangan.gui.stream_rain_image'),
  (Tiangan.癸, 'personality', 'legacy.tiangan.gui.personality'),
  (Tiangan.癸, 'personality', 'legacy.tiangan.gui.resourcefulness'),
  (Tiangan.癸, 'personality', 'legacy.tiangan.gui.restraint'),
  (Tiangan.癸, 'personality', 'legacy.tiangan.gui.strong_unfavorable_state'),
)

_UNVERIFIED_SHISHEN_CLAIM_RANGES: Final[
  tuple[tuple[Shishen, str, tuple[range, ...]], ...]
] = (
  (Shishen.比肩, 'general',        (range(1, 10),)),
  (Shishen.比肩, 'in_good_status', (range(10, 15),)),
  (Shishen.比肩, 'in_bad_status',  (range(15, 22),)),
  (Shishen.比肩, 'relationship',   (range(22, 25),)),
  (Shishen.劫财, 'general',        (range(25, 35),)),
  (Shishen.劫财, 'in_good_status', (range(35, 37),)),
  (Shishen.劫财, 'in_bad_status',  (range(37, 43),)),
  (Shishen.劫财, 'relationship',   (range(43, 48),)),
  (Shishen.食神, 'general',        (range(48, 63),)),
  (Shishen.食神, 'in_good_status', (range(63, 64),)),
  (Shishen.食神, 'in_bad_status',  (range(64, 65), range(66, 67))),
  (Shishen.食神, 'relationship',   (range(67, 70),)),
  (Shishen.伤官, 'general',        (range(70, 80),)),
  (Shishen.伤官, 'in_good_status', (range(80, 83),)),
  (Shishen.伤官, 'in_bad_status',  (range(83, 86),)),
  (Shishen.伤官, 'relationship',   (range(86, 92),)),
  (Shishen.正财, 'general',        (range(92, 100),)),
  (Shishen.正财, 'in_good_status', (range(100, 103),)),
  (Shishen.正财, 'in_bad_status',  (range(103, 105),)),
  (Shishen.正财, 'relationship',   (range(105, 111),)),
  (Shishen.偏财, 'general',        (range(111, 120),)),
  (Shishen.偏财, 'in_good_status', (range(120, 123),)),
  (Shishen.偏财, 'in_bad_status',  (range(123, 127),)),
  (Shishen.偏财, 'relationship',   (range(127, 130),)),
  (Shishen.正官, 'general',        (range(130, 138), range(140, 142))),
  (Shishen.正官, 'in_good_status', (range(142, 144),)),
  (Shishen.正官, 'in_bad_status',  (range(144, 146),)),
  (Shishen.正官, 'relationship',   (range(146, 151),)),
  (Shishen.七杀, 'general',        (range(151, 154), range(155, 158), range(160, 162))),
  (Shishen.七杀, 'in_good_status', (range(162, 164),)),
  (Shishen.七杀, 'in_bad_status',  (range(164, 166),)),
  (Shishen.七杀, 'relationship',   (range(167, 172),)),
  (Shishen.正印, 'general',        (range(172, 180),)),
  (Shishen.正印, 'in_good_status', (range(180, 183),)),
  (Shishen.正印, 'in_bad_status',  (range(183, 186),)),
  (Shishen.正印, 'relationship',   (range(186, 190),)),
  (Shishen.偏印, 'general',        (range(190, 198),)),
  (Shishen.偏印, 'in_good_status', (range(198, 202),)),
  (Shishen.偏印, 'in_bad_status',  (range(202, 206),)),
  (Shishen.偏印, 'relationship',   (range(206, 211),)),
)

_UNVERIFIED_SHISHEN_CLAIM_IDS: Final[tuple[tuple[Shishen, str, str], ...]] = tuple(
  (shishen, field, f'legacy.shishen.SH-{ordinal:03d}')
  for shishen, field, ranges in _UNVERIFIED_SHISHEN_CLAIM_RANGES
  for ordinals in ranges
  for ordinal in ordinals
)

_CONDITIONAL_UNVERIFIED_SHISHEN_GENERAL_CLAIM_IDS: Final[frozenset[str]] = frozenset({
  'legacy.shishen.SH-006',
  'legacy.shishen.SH-007',
  'legacy.shishen.SH-009',
  'legacy.shishen.SH-028',
  'legacy.shishen.SH-032',
  'legacy.shishen.SH-033',
  'legacy.shishen.SH-057',
  'legacy.shishen.SH-074',
  'legacy.shishen.SH-094',
  'legacy.shishen.SH-112',
  'legacy.shishen.SH-114',
  'legacy.shishen.SH-117',
  'legacy.shishen.SH-118',
  'legacy.shishen.SH-135',
  'legacy.shishen.SH-155',
  'legacy.shishen.SH-160',
})

_CONDITIONAL_UNVERIFIED_TIANGAN_CLAIM_IDS: Final[frozenset[str]] = frozenset({
  'legacy.tiangan.jia.weak_state',
  'legacy.tiangan.jia.strong_state',
  'legacy.tiangan.jia.balanced_state',
  'legacy.tiangan.ding.weak_state',
  'legacy.tiangan.ji.adverse_state',
  'legacy.tiangan.geng.regulated_transit',
  'legacy.tiangan.ren.weak_state',
  'legacy.tiangan.ren.strong_state',
  'legacy.tiangan.gui.strong_unfavorable_state',
})


_SOURCE_EXCERPTS: Final[frozendict[_DescriptionSource, str]] = frozendict({
  _DescriptionSource.EDITORIAL: 'Repository-original editorial prose.',
  _DescriptionSource.YUANHAI_ZIPING_RELATIONS: '生我者為正印偏印我生者為傷官食神尅我者為正官七殺我尅者為偏財正財比肩者為劫財敗財其法陽見陰為正陰見陽為正陽見陽為偏陰見陰為偏如甲丙戊庚壬屬陽乙丁己辛癸屬陰是也',
  _DescriptionSource.YUANHAI_ZIPING_STEM_TABLE: '天干五陽通變天干五陰通變',
  _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P69: '甲木天干作首排乙木根荄種得深丙火明明一太陽',
  _DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70: '丁火其形一燭燈戊土城墻堤岸同己土田園屬四維庚金頑鈍性偏剛辛金珠玉性虛靈壬水汪洋併百川癸水應非雨露麼',
  _DescriptionSource.MINGLI_TANYUAN_STEM_BASICS: '甲丙戊庚壬爲陽乙丁己辛癸爲陰甲乙屬木爲東方丙丁屬火爲南方戊己屬土爲中央庚辛屬金爲西方壬癸屬水爲北方',
  _DescriptionSource.MINGLI_TANYUAN_SHISHEN_DEFINITIONS: '陽見陰陰見陽則爲正陽見陽陰見陰則爲偏與我比者爲比肩爲劫財敗財我生者爲傷官食神我尅者爲正財偏財尅我者爲正官偏官生我者爲正印偏印',
})

_ATTRIBUTED_REFERENCE_CASES: Final[tuple[tuple[Shishen | Tiangan, str, str], ...]] = (
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


def _complete_text_rows() -> tuple[list[str], list[str]]:
  shishen_rows: list[str] = []
  for shishen in Shishen:
    description = Interpreter.interpret_shishen(shishen, include_reference_only=True)
    for field, texts in _as_mapping(description).items():
      shishen_rows.extend(f'S:{shishen}:{field}:{text}' for text in texts)

  tiangan_rows: list[str] = []
  for tg in Tiangan:
    tg_description = Interpreter.interpret_tiangan(tg, include_reference_only=True)
    for field, texts in _as_mapping(tg_description).items():
      tiangan_rows.extend(f'T:{tg}:{field}:{text}' for text in texts)

  return shishen_rows, tiangan_rows


def _complete_corpus_fingerprint() -> str:
  shishen_rows, tiangan_rows = _complete_text_rows()
  rows = shishen_rows + tiangan_rows
  for subject, field, claim in _all_claims():
    rows.append('\0'.join((
      'C', str(subject), field, claim.claim_id, claim.text,
      ','.join(source.value for source in claim.sources),
      claim.attribution,
      ','.join(condition.value for condition in claim.conditions),
      claim.output.value,
    )))
  return sha256('\n'.join(rows).encode()).hexdigest()


def _source_registry_fingerprint() -> str:
  rows: list[str] = []
  for source in _DescriptionSource:
    record = _DESCRIPTION_SOURCES[source]
    values = (
      source.value,
      record.work,
      record.attribution,
      record.edition,
      record.locator,
      record.url,
      record.text_layer.value,
      record.lineage.value,
      record.excerpt,
      record.supports,
      record.limitations,
    )
    rows.append('\0'.join(values))
  return sha256('\n'.join(rows).encode()).hexdigest()


def test_interpret_shishen() -> None:
  for shishen in Shishen:
    default: ShishenDescription = Interpreter.interpret_shishen(shishen)
    complete = Interpreter.interpret_shishen(shishen, include_reference_only=True)

    keys: list[str] = ['general', 'in_good_status', 'in_bad_status', 'relationship']
    for result in (default, complete):
      for k in keys:
        assert k in result
        assert isinstance(result[k], list) # type: ignore # mypy complains.
        for d in result[k]: # type: ignore # mypy complains.
          assert isinstance(d, str)
          assert len(d) >= 1

          assert d == d.strip(), f'"{d}" not stripped' # No space at the beginning or end.
          assert d[-1] == '。', f'"{d}" not ending with "。"' # End with '。'.

    assert default == Interpreter.interpret_shishen(shishen)


def test_interpret_tiangan() -> None:
  for tg in Tiangan:
    default: TianganDescription = Interpreter.interpret_tiangan(tg)
    complete = Interpreter.interpret_tiangan(tg, include_reference_only=True)

    keys: list[str] = ['general', 'personality']
    for result in (default, complete):
      for k in keys:
        assert k in result
        assert isinstance(result[k], list) # type: ignore # mypy complains.
        for d in result[k]: # type: ignore # mypy complains.
          assert isinstance(d, str)
          assert len(d) >= 1

          assert d == d.strip(), f'"{d}" not stripped' # No space at the beginning or end.
          assert d[-1] == '。', f'"{d}" not ending with "。"' # End with '。'.

    assert len(default['general']) == 1
    assert default['personality'] == []
    assert default == Interpreter.interpret_tiangan(tg)


def test_interpret_shishen_negative() -> None:
  with pytest.raises(TypeError):
    Interpreter.interpret_shishen('比肩') # type: ignore


def test_interpret_tiangan_negative() -> None:
  with pytest.raises(TypeError):
    Interpreter.interpret_tiangan('甲') # type: ignore


def test_reference_only_descriptions_are_opt_in() -> None:
  default_shishen: list[ShishenDescription] = []
  complete_shishen: list[ShishenDescription] = []
  shishen_definitions = {
    shishen: text for shishen, _, text in _SHISHEN_DEFINITIONS
  }
  for shishen in Shishen:
    default = Interpreter.interpret_shishen(shishen)
    complete = Interpreter.interpret_shishen(shishen, include_reference_only=True)
    assert default == SHISHEN_DESCRIPTIONS[shishen]
    assert default == {
      'general': [shishen_definitions[shishen]] if shishen in shishen_definitions else [],
      'in_good_status': [],
      'in_bad_status': [],
      'relationship': [],
    }
    default_shishen.append(default)
    complete_shishen.append(complete)

  assert tuple(_description_count([description]) for description in default_shishen) == (
    1, 0, 1, 1, 1, 1, 1, 1, 1, 1,
  )
  assert tuple(_description_count([description]) for description in complete_shishen) == (
    25, 23, 23, 23, 20, 20, 22, 22, 19, 22,
  )

  default_tiangan: list[TianganDescription] = []
  complete_tiangan: list[TianganDescription] = []
  definitions = {
    tg: text for tg, _, text, _ in _TIANGAN_DEFINITIONS
  }
  for tg in Tiangan:
    tg_default = Interpreter.interpret_tiangan(tg)
    tg_complete = Interpreter.interpret_tiangan(tg, include_reference_only=True)
    assert tg_default == TIANGAN_DESCRIPTIONS[tg]
    assert tg_default == {
      'general': [definitions[tg]],
      'personality': [],
    }
    default_tiangan.append(tg_default)
    complete_tiangan.append(tg_complete)

  assert _description_count(default_shishen) == 9
  assert _description_count(complete_shishen) == 219
  assert _description_count(default_tiangan) == 10
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

  attributed_claims = [
    (subject, field, claim)
    for subject, field, claim in claims
    if claim.sources
  ]
  assert {
    (subject, field, claim.text)
    for subject, field, claim in attributed_claims
  } == set(_ATTRIBUTED_REFERENCE_CASES)
  editorial_claims = [
    (subject, field, claim)
    for subject, field, claim in claims
    if claim.sources == (_DescriptionSource.EDITORIAL,)
  ]
  assert [
    (subject, field, claim.text)
    for subject, field, claim in editorial_claims
  ] == list(_EDITORIAL_REFERENCE_CASES)
  assert all(
    claim.attribution == 'Repository editorial'
    for _, _, claim in editorial_claims
  )

  unverified_shishen_claims = [
    (subject, field, claim)
    for subject, field, claim in claims
    if isinstance(subject, Shishen) and not claim.sources
  ]
  assert [
    (subject, field, claim.claim_id)
    for subject, field, claim in unverified_shishen_claims
  ] == list(_UNVERIFIED_SHISHEN_CLAIM_IDS)
  assert all(
    claim.attribution == 'Legacy corpus; source unverified'
    for _, _, claim in unverified_shishen_claims
  )
  conditional_shishen_claim_ids = {
    claim.claim_id
    for _, _, claim in unverified_shishen_claims
    if claim.conditions
  }
  assert len(conditional_shishen_claim_ids) == 79
  for shishen, field, claim in unverified_shishen_claims:
    expected_conditions = (
      (_DescriptionCondition.CHART_CONTEXT_REQUIRED,)
      if field in ('in_good_status', 'in_bad_status')
      or claim.claim_id in _CONDITIONAL_UNVERIFIED_SHISHEN_GENERAL_CLAIM_IDS
      else ()
    )
    assert claim.conditions == expected_conditions
    assert claim.text not in _as_mapping(Interpreter.interpret_shishen(shishen))[field]
    assert claim.text in _as_mapping(Interpreter.interpret_shishen(
      shishen,
      include_reference_only=True,
    ))[field]

  unverified_tiangan_claims = [
    (subject, field, claim)
    for subject, field, claim in claims
    if isinstance(subject, Tiangan) and not claim.sources
  ]
  assert [
    (subject, field, claim.claim_id)
    for subject, field, claim in unverified_tiangan_claims
  ] == list(_UNVERIFIED_TIANGAN_CLAIM_IDS)
  assert all(
    claim.attribution == 'Legacy corpus; source unverified'
    for _, _, claim in unverified_tiangan_claims
  )
  assert {
    claim.claim_id
    for _, _, claim in unverified_tiangan_claims
    if claim.conditions
  } == set(_CONDITIONAL_UNVERIFIED_TIANGAN_CLAIM_IDS)
  for tg, field, claim in unverified_tiangan_claims:
    expected_conditions = (
      (_DescriptionCondition.CHART_CONTEXT_REQUIRED,)
      if claim.claim_id in _CONDITIONAL_UNVERIFIED_TIANGAN_CLAIM_IDS
      else ()
    )
    assert claim.conditions == expected_conditions
    assert claim.text not in _as_mapping(Interpreter.interpret_tiangan(tg))[field]
    assert claim.text in _as_mapping(Interpreter.interpret_tiangan(
      tg,
      include_reference_only=True,
    ))[field]


def test_description_corpora_are_fully_classified() -> None:
  assert all(
    isinstance(item, _DescriptionClaim)
    for description in _SHISHEN_DESCRIPTION_CORPUS.values()
    for field in ('general', 'in_good_status', 'in_bad_status', 'relationship')
    for item in description[field]
  )
  assert all(
    isinstance(item, _DescriptionClaim)
    for description in _TIANGAN_DESCRIPTION_CORPUS.values()
    for field in ('general', 'personality')
    for item in description[field]
  )


def test_sourced_claims() -> None:
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
  assert _source_registry_fingerprint() == '7ccb163266026302dfe340108e28c9018cccfec48001f696c2f5056893c06a3e'

  claims = [claim for _, _, claim in _all_claims()]
  claim_ids = [claim.claim_id for claim in claims]
  assert len(claim_ids) == len(set(claim_ids))
  for claim in claims:
    assert claim.claim_id
    assert claim.text
    assert claim.attribution
    assert all(source in _DESCRIPTION_SOURCES for source in claim.sources)
    if claim.output is _DescriptionOutput.DEFAULT:
      assert claim.sources
      assert not claim.conditions
      assert len({
        _DESCRIPTION_SOURCES[source].lineage
        for source in claim.sources
      }) >= 2
    elif not claim.sources:
      assert claim.attribution == 'Legacy corpus; source unverified'


def test_default_projection_drops_conditional_and_reference_only_claims() -> None:
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
  conditional_reference = _DescriptionClaim(
    claim_id='test.conditional_reference',
    text='Conditional reference-only claim.',
    sources=(_DescriptionSource.EDITORIAL,),
    attribution='Test',
    conditions=(_DescriptionCondition.CHART_CONTEXT_REQUIRED,),
    output=_DescriptionOutput.REFERENCE_ONLY,
  )

  items: list[str | _DescriptionClaim] = [
    'Legacy claim.', default, conditional, reference, conditional_reference,
  ]
  assert _project_texts(items, include_reference_only=False) == [
    'Legacy claim.',
    'Default claim.',
  ]
  assert _project_texts(items, include_reference_only=True) == [
    'Legacy claim.',
    'Default claim.',
    'Conditional claim.',
    'Reference-only claim.',
    'Conditional reference-only claim.',
  ]


def test_complete_corpus_is_conserved() -> None:
  # Text/order fingerprints stay fixed when claim metadata changes intentionally.
  shishen_rows, tiangan_rows = _complete_text_rows()
  assert sha256('\n'.join(shishen_rows).encode()).hexdigest() == (
    '269edce269377eea3b53e4bc560097ad414058008894c45906931da0fbae500d'
  )
  assert sha256('\n'.join(tiangan_rows).encode()).hexdigest() == (
    'cbd11b02806a73ff5f062823d913b4d2343504e38a94ddb344a1d6caccf6133c'
  )
  assert sha256('\n'.join(shishen_rows + tiangan_rows).encode()).hexdigest() == (
    'c606a5e21efaea3b7cc0e49d8647debbba450d3eb40dcaa02fa0ed436e7547e8'
  )
  assert _complete_corpus_fingerprint() == 'db85e28b955eb0160e7d41f925f127482b81ba3c3aaa0845c084117e41a298f2'


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


@pytest.mark.parametrize('bad_flag', [1, 0, None])
def test_reference_only_negative(bad_flag: object) -> None:
  with pytest.raises(TypeError):
    Interpreter.interpret_shishen(Shishen.食神, include_reference_only=bad_flag) # type: ignore
  with pytest.raises(TypeError):
    Interpreter.interpret_tiangan(Tiangan.甲, include_reference_only=bad_flag) # type: ignore


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
