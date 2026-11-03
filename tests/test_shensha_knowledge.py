# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import FrozenInstanceError, asdict, replace
from hashlib import sha256

import pytest

from bazi.analyzer.relationship import SHENSHA_LABELS
from bazi.defines import Dizhi, Tiangan
from bazi.knowledge import KnowledgeBase, guoyin_entry, guoyin_def
from bazi.rules import BaziRules, ShenshaRules

from knowledge_additions import SHENSHA_OBJECT_IDS, SHENSHA_SOURCE_IDS, SHENSHA_ENTRY_IDS


KNOWLEDGE = KnowledgeBase.load()


@pytest.mark.parametrize('definition,claim_id,offset', [
  (ShenshaRules.GuoyinDef.MODERN, 'shensha.guoyin.modern', 8),
  (ShenshaRules.GuoyinDef.WUXING_JINGJI, 'shensha.guoyin.wuxing_jingji', 7),
])
def test_guoyin_round_trip_keeps_sources(
  definition: ShenshaRules.GuoyinDef, claim_id: str, offset: int,
) -> None:
  entry = guoyin_entry(KNOWLEDGE, definition)
  assert entry is KNOWLEDGE.entry(claim_id)
  assert guoyin_def(KNOWLEDGE, claim_id) is definition
  assert entry.sources == ('repository_guoyin_variants',)
  assert entry.source_state == 'repository_attributed' and entry.show_by_default is False
  assert all((target.index - BaziRules.TIANGAN_LU[tg].index) % 12 == offset
             for tg, target in ShenshaRules.GUOYIN[definition].items())
  with pytest.raises(FrozenInstanceError):
    entry.text = 'changed' # type: ignore[misc]


def test_guoyin_links_exhaust_definitions() -> None:
  assert set(ShenshaRules.GuoyinDef) == {
    ShenshaRules.GuoyinDef.MODERN, ShenshaRules.GuoyinDef.WUXING_JINGJI,
  }
  linked = {guoyin_entry(KNOWLEDGE, definition).claim_id for definition in ShenshaRules.GuoyinDef}
  for claim_id in KNOWLEDGE.entries:
    assert (guoyin_def(KNOWLEDGE, claim_id) is not None) is (claim_id in linked)


def test_guoyin_uses_callers_edited_entries() -> None:
  entry = replace(KNOWLEDGE.entry('shensha.guoyin.modern'), text='自定义说明。', viewpoint='自定义展示')
  source = replace(KNOWLEDGE.sources[entry.sources[0]], work='自定义来源记录')
  custom = KnowledgeBase(
    tuple(KNOWLEDGE.objects.values()), tuple(KNOWLEDGE.contexts.values()), (source,), (entry,),
  )
  assert guoyin_entry(custom, ShenshaRules.GuoyinDef.MODERN) is entry
  assert guoyin_def(custom, entry.claim_id) is ShenshaRules.GuoyinDef.MODERN
  assert custom.sources[guoyin_entry(custom, ShenshaRules.GuoyinDef.MODERN).sources[0]] is source
  assert KNOWLEDGE.entry(entry.claim_id).text != entry.text
  assert custom.query() == ()


@pytest.mark.parametrize('definition', tuple(ShenshaRules.GuoyinDef))
def test_guoyin_missing_entry_fails(
  definition: ShenshaRules.GuoyinDef,
) -> None:
  claim_id = guoyin_entry(KNOWLEDGE, definition).claim_id
  partial = KnowledgeBase(
    tuple(KNOWLEDGE.objects.values()), tuple(KNOWLEDGE.contexts.values()), tuple(KNOWLEDGE.sources.values()),
    tuple(entry for identifier, entry in KNOWLEDGE.entries.items() if identifier != claim_id),
  )
  for knowledge in (KnowledgeBase((), (), (), ()), partial):
    with pytest.raises(ValueError, match=f'^Unknown claim ID: {claim_id}$'):
      guoyin_entry(knowledge, definition)
    with pytest.raises(ValueError, match=f'^Unknown claim ID: {claim_id}$'):
      guoyin_def(knowledge, claim_id)


@pytest.mark.parametrize('bad', [None, True, 1, 'MODERN', (), [], {}, Dizhi.子, Tiangan.甲])
def test_guoyin_rejects_wrong_types(bad: object) -> None:
  with pytest.raises(TypeError, match='Expected KnowledgeBase'):
    guoyin_entry(bad, ShenshaRules.GuoyinDef.MODERN) # type: ignore[arg-type]
  with pytest.raises(TypeError, match='Expected GuoyinDef'):
    guoyin_entry(KNOWLEDGE, bad) # type: ignore[arg-type]
  with pytest.raises(TypeError, match='Expected KnowledgeBase'):
    guoyin_def(bad, 'shensha.guoyin.modern') # type: ignore[arg-type]
  if not isinstance(bad, str):
    with pytest.raises(TypeError, match='Expected str'):
      guoyin_def(KNOWLEDGE, bad) # type: ignore[arg-type]


@pytest.mark.parametrize('claim_id', ['', ' ', 'unknown', 'MODERN', 'shensha.guoyin'])
def test_guoyin_unknown_id_fails(claim_id: str) -> None:
  with pytest.raises(ValueError):
    guoyin_def(KNOWLEDGE, claim_id)


def test_additions_remain_reference_only() -> None:
  k = KNOWLEDGE
  for registry, cohort in (
    (k.objects, SHENSHA_OBJECT_IDS), (k.sources, SHENSHA_SOURCE_IDS), (k.entries, SHENSHA_ENTRY_IDS),
  ):
    selected = tuple(identifier for identifier in registry if identifier in cohort)
    assert selected == cohort
    positions = tuple(tuple(registry).index(identifier) for identifier in selected)
    assert positions == tuple(range(positions[0], positions[0] + len(cohort)))
  for identifier in SHENSHA_OBJECT_IDS:
    obj = k.objects[identifier]
    assert obj.kind == 'shensha' and obj.name == SHENSHA_LABELS[identifier.removeprefix('shensha.')]
    entries = k.query(object_id=identifier, include_reference_only=True)
    assert len(entries) >= 2 and k.query(object_id=identifier) == ()
    assert all(entry.text in k.render_subject(identifier, include_reference_only=True) for entry in entries)
  for claim_id, source_id in zip(SHENSHA_ENTRY_IDS, SHENSHA_SOURCE_IDS, strict=True):
    entry = k.entry(claim_id)
    assert entry.sources == (source_id,) and entry.source_state == 'witnessed'
    assert entry.show_by_default is False and entry.legacy is None
    assert entry.applicability == 'unconditional' and entry.premise == ''
    assert entry.contexts == entry.relations == entry.exceptions == entry.limits == ()
    assert entry.topics == ('查法口径',)
    assert len(entry.roles) == 1 and entry.roles[0].object_id in SHENSHA_OBJECT_IDS
    assert k.sources[source_id].state == 'witnessed'
    assert k.sources[source_id].limitations
    promoted = replace(entry, show_by_default=True)
    with pytest.raises(ValueError, match='Default entry needs independent lineages'):
      KnowledgeBase(tuple(k.objects.values()), (), tuple(k.sources.values()), (promoted,))


def test_excerpts_keep_layers_and_original_chars() -> None:
  expected = {
    'sanming_tonghui.tianyi.yinyang': ('baiwen', '其曰陽貴陰貴乃冬至用陽夏至用陰非晝夜之說'),
    'sanming_tonghui.taohua.table': ('baiwen', '寅午戍卯巳酉丑午申子辰酉亥卯未子即長生第二位沐浴之宫是也一名敗神一名桃花煞'),
    'sanming_tonghui.yima.table': ('baiwen', '寅午戌生人馬在申而五陽干乘之'),
    'sanming_tonghui.huagai.table': ('baiwen', '故以三合底處得庫謂之華葢洞𤣥經云将星處乎中軍華葢張乎庫土是也'),
    'sanming_tonghui.yangren.luming': ('baiwen', '故羊刃常居祿前一辰'),
    'sanming_tonghui.yangren.ziping': ('baiwen', '子平以甲丙戊庚壬五陽干有刃乙丁巳辛癸五陰干無刃'),
    'xingxue_dacheng.wenchang_xin_xu': ('zhushi', '獨辛不以生而以戌為文昌戌在辛之方位'),
    'wenzhen_shensha.tianyi': ('editorial', '古诀：\n“甲戊庚牛羊, 乙己鼠猴乡, 丙丁猪鸡位, 壬癸兔蛇藏, 六辛逢虎马, 此是贵人方.”——《渊海子平》\n查法：以日/年干查四地支'),
    'wenzhen_shensha.taohua': ('editorial', '古诀：\n申子辰在酉, 寅午戌在卯, 巳酉丑在午, 亥卯未在子.\n查法：以年、日支查余三支'),
    'wenzhen_shensha.yima': ('editorial', '古诀：\n申子辰马在寅, 寅午戌马在申,巳酉丑马在亥, 亥卯未马在巳\n查法：以年、日支查余三支'),
    'wenzhen_shensha.wenchang': ('editorial', '古诀：\n甲乙巳午报君知, 丙戊申宫丁己鸡.庚猪辛鼠壬逢虎, 癸人见卯入云梯.\n甲日巳。乙日午。丙日申。丁日酉。戊日申。己日酉。庚日亥。辛日子。壬日寅。癸日卯。\n查法：以日/年干查四地支'),
    'wenzhen_shensha.huagai': ('editorial', '古诀：\n寅午戌见戌, 亥卯未见未,申子辰见辰, 巳酉丑见丑.\n查法：以年、日支查余支'),
    'wenzhen_shensha.yangren': ('editorial', '古诀：\n甲日卯。乙日寅。丙日午。丁日巳。戊日午。\n己日巳。庚日酉。辛日申。壬日子。癸日亥。\n查法：以日干查四地支'),
    'click2macao.tianyi_geng_with_xin': ('editorial', '庚辛逢馬虎，此是貴人方。'),
  }
  assert set(expected) == set(SHENSHA_SOURCE_IDS)
  for source_id, (layer, excerpt) in expected.items():
    source = KNOWLEDGE.sources[source_id]
    assert (source.text_layer, source.excerpt) == (layer, excerpt)
    if source_id.startswith('sanming_tonghui.'):
      assert source.lineage == 'sanming_tonghui' and '四库全书本电子转录' in source.edition
    if source_id.startswith('wenzhen_shensha.'):
      assert source.lineage == 'wenzhen_shensha' and '2026-11-01' in source.edition
  assert '果老星命' in KNOWLEDGE.sources['xingxue_dacheng.wenchang_xin_xu'].limitations
  assert '起源' in KNOWLEDGE.sources['click2macao.tianyi_geng_with_xin'].limitations


def test_reference_entry_meanings_are_pinned() -> None:
  expected = {
    'shensha.tianyi.yinyang': ('shensha.tianyi', '三命通会', '《三命通会》所引通玄经推法以冬至用阳贵、夏至用阴贵，与昼夜说分列。'),
    'shensha.taohua.table': ('shensha.taohua', '三命通会', '《三命通会》称咸池又名桃花煞，以三合组的沐浴位取支。'),
    'shensha.yima.table': ('shensha.yima', '三命通会', '《三命通会》的驿马条载寅午戌生人马在申。'),
    'shensha.huagai.table': ('shensha.huagai', '三命通会', '《三命通会》以三合库位称华盖。'),
    'shensha.yangren.luming': ('shensha.yangren', '三命通会', '《三命通会》所载羊刃读法取禄前一辰。'),
    'shensha.yangren.ziping': ('shensha.yangren', '三命通会', '《三命通会》另记子平五阳干有刃、五阴干无刃。'),
    'shensha.wenchang.xin_xu': ('shensha.wenchang', 'XIN_XU', '《星学大成》〈论文昌〉的夹注明定辛取戌，以戌在辛之方位解释该格。'),
    'shensha.tianyi.lookup': ('shensha.tianyi', '现代问真', '问真《神煞大全》的天乙贵人条以日干或年干查四地支，庚与甲、戊同取丑、未。'),
    'shensha.taohua.lookup': ('shensha.taohua', '现代问真', '问真《神煞大全》的桃花/咸池条以年支、日支查余三支，按申子辰见酉、寅午戌见卯、巳酉丑见午、亥卯未见子取值。'),
    'shensha.yima.lookup': ('shensha.yima', '现代问真', '问真《神煞大全》的驿马条以年支、日支查余三支，按申子辰见寅、寅午戌见申、巳酉丑见亥、亥卯未见巳取值。'),
    'shensha.wenchang.lookup': ('shensha.wenchang', '现代问真', '问真《神煞大全》以“文昌贵人”为题列出辛取子的十干表，以日干或年干查四地支；对应本库文昌的辛子读法。'),
    'shensha.huagai.lookup': ('shensha.huagai', '现代问真', '问真《神煞大全》的华盖条以年支、日支查余支，按寅午戌见戌、亥卯未见未、申子辰见辰、巳酉丑见丑取值。'),
    'shensha.yangren.lookup': ('shensha.yangren', '现代问真', '问真《神煞大全》的羊刃条以日干查四地支；阴干列乙见寅、丁己见巳、辛见申、癸见亥，对应本库十干帝旺位读法。'),
    'shensha.tianyi.geng_with_xin': ('shensha.tianyi', 'GENG_WITH_XIN', '林颂濰《天乙贵人口诀的真伪》列出庚辛同组、见寅午的另一首天乙口诀。'),
  }
  assert tuple(expected) == SHENSHA_ENTRY_IDS
  for claim_id, (object_id, viewpoint, text) in expected.items():
    entry = KNOWLEDGE.entry(claim_id)
    assert (entry.roles[0].object_id, entry.viewpoint, entry.text) == (object_id, viewpoint, text)
    assert entry.roles[0].name == '讨论对象' and entry.attribution == '本仓整理'


def test_source_metadata_is_pinned() -> None:
  records = [asdict(KNOWLEDGE.sources[identifier]) for identifier in SHENSHA_SOURCE_IDS]
  payload = json.dumps(records, ensure_ascii=False, sort_keys=True).encode('utf-8')
  assert sha256(payload).hexdigest() == 'd005a680a013cbd68cd34e58e9e5dc34e28a6d0a05f58bcc2d85bcf8b92add88'
