# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_interpreter.py

from collections.abc import Sequence
from hashlib import sha256
from typing import Final, cast

import pytest

from bazi.descriptions import (
  ShishenDescription,
  TianganDescription,
  _DescriptionClaim,
  _DescriptionOutput,
  _DescriptionSource,
  _SHISHEN_DESCRIPTION_CORPUS,
  _TIANGAN_DESCRIPTION_CORPUS,
  SHISHEN_DESCRIPTIONS,
  TIANGAN_DESCRIPTIONS,
)
from bazi.defines import Tiangan, Shishen
from bazi.interpreter import Interpreter


_REFERENCE_ONLY_CASES: Final[tuple[tuple[Shishen | Tiangan, str, str], ...]] = (
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


def _as_mapping(description: ShishenDescription | TianganDescription) -> dict[str, list[str]]:
  return cast(dict[str, list[str]], description)


def _description_count(descriptions: Sequence[ShishenDescription | TianganDescription]) -> int:
  return sum(len(texts) for description in descriptions for texts in _as_mapping(description).values())


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

  assert _description_count(default_shishen) == 203
  assert _description_count(complete_shishen) == 210
  assert _description_count(default_tiangan) == 43
  assert _description_count(complete_tiangan) == 58


def test_reference_only_claims() -> None:
  claims: list[tuple[Shishen | Tiangan, str, _DescriptionClaim]] = []
  for shishen, description in _SHISHEN_DESCRIPTION_CORPUS.items():
    for field in ('general', 'in_good_status', 'in_bad_status', 'relationship'):
      claims.extend(
        (shishen, field, item)
        for item in description[field]
        if isinstance(item, _DescriptionClaim)
      )
  for tg, tg_description in _TIANGAN_DESCRIPTION_CORPUS.items():
    for tg_field in ('general', 'personality'):
      claims.extend(
        (tg, tg_field, item)
        for item in tg_description[tg_field]
        if isinstance(item, _DescriptionClaim)
      )

  assert [
    (subject, field, claim.text)
    for subject, field, claim in claims
  ] == list(_REFERENCE_ONLY_CASES)
  assert all(claim.source is _DescriptionSource.EDITORIAL for _, _, claim in claims)
  assert all(claim.output is _DescriptionOutput.REFERENCE_ONLY for _, _, claim in claims)


def test_complete_corpus_is_conserved() -> None:
  # Pin the complete corpus text and order; update deliberately when the text changes.
  # 钉住完整语料的文字与顺序；有意修改文字时同步更新。
  assert _complete_corpus_fingerprint() == '4c9e9bf192951aeb23fa23a6ea14bbe5e8fc63e7ce82653d0c584ed97f94f947'


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


def test_corpus_is_frozen() -> None:
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
