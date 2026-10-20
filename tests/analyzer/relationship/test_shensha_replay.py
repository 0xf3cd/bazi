# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shensha_replay.py

import pytest

import random
import itertools

from bazi.defines import Tiangan, Dizhi
from bazi.utils import shensha_utils, tiangan_utils, dizhi_utils
from bazi.bazi_chart import BaziChart
from bazi.school import Anchor
from bazi.transit_chart import TransitChart
from bazi.analyzer.relationship import RelationshipAnalyzer

from relationship_samples import random_year_transits


@pytest.mark.slow
def test_at_birth_shensha(rng: random.Random) -> None:
  for _ in range(100):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    analyzer = RelationshipAnalyzer(chart)

    dm: Tiangan = chart.bazi.day_master
    y, m, d, h = chart.bazi.four_dizhis
    school = chart.bazi.config.school
    # The five Dizhi-anchored Shenshas each carry their own knob -- read each one, never a shared flag.
    year_anchored = {
      'yima':      school.yima_anchor is Anchor.YEAR_AND_DAY,
      'huagai':    school.huagai_anchor is Anchor.YEAR_AND_DAY,
      'jiangxing': school.jiangxing_anchor is Anchor.YEAR_AND_DAY,
      'jiesha':    school.jiesha_anchor is Anchor.YEAR_AND_DAY,
      'wangshen':  school.wangshen_anchor is Anchor.YEAR_AND_DAY,
    }
    use_day_zaisha_anchor = school.zaisha_anchor is Anchor.YEAR_AND_DAY

    # The 红艳 anchor stem follows the chart's school (查法锚, issue #69) -- don't assume the day master.
    anchor: Tiangan = dm if school.hongyan_anchor is Anchor.DAY else chart.bazi.year_pillar.tiangan

    at_birth = analyzer.at_birth

    # Taohua / 桃花
    expected_taohua: list[Dizhi] = []
    for dz1, dz2 in itertools.product([y], [m, d, h]):
      if shensha_utils.taohua(dz1, dz2):
        expected_taohua.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.taohua(dz1, dz2):
        expected_taohua.append(dz2)
    assert at_birth.shensha['taohua'] == set(expected_taohua)
    assert at_birth.shensha['taohua'] == at_birth.shensha['taohua'] # Repeated lookup must answer the same.

    # Hongyan / 红艳
    expected_hongyan: list[Dizhi] = []
    for tg, dz in itertools.product([anchor], [y, m, d, h]):
      if shensha_utils.hongyan(tg, dz):
        expected_hongyan.append(dz)
    assert at_birth.shensha['hongyan'] == set(expected_hongyan)
    assert at_birth.shensha['hongyan'] == at_birth.shensha['hongyan'] # Repeated lookup must answer the same.

    # Hongluan / 红鸾
    expected_hongluan: list[Dizhi] = []
    for dz1, dz2 in itertools.product([y], [m, d, h]):
      if shensha_utils.hongluan(dz1, dz2):
        expected_hongluan.append(dz2)
    assert at_birth.shensha['hongluan'] == set(expected_hongluan)
    assert at_birth.shensha['hongluan'] == at_birth.shensha['hongluan'] # Repeated lookup must answer the same.

    # Tianxi / 天喜
    expected_tianxi: list[Dizhi] = []
    for dz1, dz2 in itertools.product([y], [m, d, h]):
      if shensha_utils.tianxi(dz1, dz2):
        expected_tianxi.append(dz2)
    assert at_birth.shensha['tianxi'] == set(expected_tianxi)
    assert at_birth.shensha['tianxi'] == at_birth.shensha['tianxi'] # Repeated lookup must answer the same.

    # Yima / 驿马
    expected_yima: list[Dizhi] = []
    if year_anchored['yima']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.yima(dz1, dz2):
          expected_yima.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.yima(dz1, dz2):
        expected_yima.append(dz2)
    assert at_birth.shensha['yima'] == set(expected_yima)
    assert at_birth.shensha['yima'] == at_birth.shensha['yima'] # Repeated lookup must answer the same.

    # Huagai / 华盖
    expected_huagai: list[Dizhi] = []
    if year_anchored['huagai']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.huagai(dz1, dz2):
          expected_huagai.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.huagai(dz1, dz2):
        expected_huagai.append(dz2)
    assert at_birth.shensha['huagai'] == set(expected_huagai)
    assert at_birth.shensha['huagai'] == at_birth.shensha['huagai'] # Repeated lookup must answer the same.

    # Yangren / 羊刃
    expected_yangren: list[Dizhi] = []
    for dz in [y, m, d, h]:
      if shensha_utils.yangren(
        dm,
        dz,
        definition=chart.bazi.config.school.yangren_def,
      ):
        expected_yangren.append(dz)
    assert at_birth.shensha['yangren'] == set(expected_yangren)
    assert at_birth.shensha['yangren'] == at_birth.shensha['yangren'] # Repeated lookup must answer the same.

    # Feiren / 飞刃
    expected_feiren: list[Dizhi] = []
    for dz in [y, m, d, h]:
      if shensha_utils.feiren(
        dm,
        dz,
        definition=chart.bazi.config.school.feiren_def,
      ):
        expected_feiren.append(dz)
    assert at_birth.shensha['feiren'] == set(expected_feiren)
    assert at_birth.shensha['feiren'] == at_birth.shensha['feiren'] # Repeated lookup must answer the same.

    # Tianyi Guiren / 天乙贵人
    expected_tianyi: list[Dizhi] = []
    for tg, dz in itertools.product([chart.bazi.year_pillar.tiangan, dm], [y, m, d, h]):
      if shensha_utils.tianyi(
        tg,
        dz,
        definition=chart.bazi.config.school.tianyi_def,
      ):
        expected_tianyi.append(dz)
    assert at_birth.shensha['tianyi'] == set(expected_tianyi)
    assert at_birth.shensha['tianyi'] == at_birth.shensha['tianyi'] # Repeated lookup must answer the same.

    # Jiangxing / 将星
    expected_jiangxing: list[Dizhi] = []
    if year_anchored['jiangxing']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.jiangxing(dz1, dz2):
          expected_jiangxing.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.jiangxing(dz1, dz2):
        expected_jiangxing.append(dz2)
    assert at_birth.shensha['jiangxing'] == set(expected_jiangxing)
    assert at_birth.shensha['jiangxing'] == at_birth.shensha['jiangxing'] # Repeated lookup must answer the same.

    # Zaisha / 灾煞
    expected_zaisha = [dz for dz in (m, d, h) if shensha_utils.zaisha(y, dz)]
    if use_day_zaisha_anchor:
      expected_zaisha.extend(dz for dz in (y, m, h) if shensha_utils.zaisha(d, dz))
    assert at_birth.shensha['zaisha'] == set(expected_zaisha)
    assert at_birth.shensha['zaisha'] == at_birth.shensha['zaisha'] # Repeated lookup must answer the same.

    # Jiesha / 劫煞
    expected_jiesha: list[Dizhi] = []
    if year_anchored['jiesha']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.jiesha(dz1, dz2):
          expected_jiesha.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.jiesha(dz1, dz2):
        expected_jiesha.append(dz2)
    assert at_birth.shensha['jiesha'] == set(expected_jiesha)
    assert at_birth.shensha['jiesha'] == at_birth.shensha['jiesha'] # Repeated lookup must answer the same.

    # Wangshen / 亡神
    expected_wangshen: list[Dizhi] = []
    if year_anchored['wangshen']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.wangshen(dz1, dz2):
          expected_wangshen.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.wangshen(dz1, dz2):
        expected_wangshen.append(dz2)
    assert at_birth.shensha['wangshen'] == set(expected_wangshen)
    assert at_birth.shensha['wangshen'] == at_birth.shensha['wangshen'] # Repeated lookup must answer the same.

    # Guchen / 孤辰
    expected_guchen = {dz for dz in (m, d, h) if shensha_utils.guchen(y, dz)}
    assert at_birth.shensha['guchen'] == expected_guchen
    assert at_birth.shensha['guchen'] == at_birth.shensha['guchen'] # Repeated lookup must answer the same.

    # Guasu / 寡宿
    expected_guasu = {dz for dz in (m, d, h) if shensha_utils.guasu(y, dz)}
    assert at_birth.shensha['guasu'] == expected_guasu
    assert at_birth.shensha['guasu'] == at_birth.shensha['guasu'] # Repeated lookup must answer the same.

    # Lushen / 禄神
    expected_lushen = {dz for dz in (y, m, d, h) if shensha_utils.lushen(dm, dz)}
    assert at_birth.shensha['lushen'] == expected_lushen
    assert at_birth.shensha['lushen'] == at_birth.shensha['lushen'] # Repeated lookup must answer the same.

    # Jinyu / 金舆
    expected_jinyu = {dz for dz in (y, m, d, h) if shensha_utils.jinyu(dm, dz)}
    assert at_birth.shensha['jinyu'] == expected_jinyu
    assert at_birth.shensha['jinyu'] == at_birth.shensha['jinyu'] # Repeated lookup must answer the same.

    # Kuigang / 魁罡
    expected_kuigang = chart.bazi.day_pillar if shensha_utils.kuigang(chart.bazi.day_pillar) else None
    assert at_birth.shensha['kuigang'] == expected_kuigang
    assert at_birth.shensha['kuigang'] == at_birth.shensha['kuigang'] # Repeated lookup must answer the same.

    # Tianshe / 天赦
    expected_tianshe = (
      chart.bazi.day_pillar
      if shensha_utils.tianshe(chart.bazi.month_commander, chart.bazi.day_pillar)
      else None
    )
    assert at_birth.shensha['tianshe'] == expected_tianshe
    assert at_birth.shensha['tianshe'] == at_birth.shensha['tianshe'] # Repeated lookup must answer the same.


@pytest.mark.slow
def test_filtered(rng: random.Random) -> None:
  '''Test "star_relations" only contain filtered combos.'''
  for _ in range(16):
    chart: BaziChart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)

    stars = chart.relationship_stars
    at_birth = analyzer.at_birth

    for tg_rel, tg_combos in tiangan_utils.discover(chart.bazi.four_tiangans).items():
      if tg_rel not in at_birth.star_relations.tiangan:
        assert all(stars.tiangan not in tg_combo for tg_combo in tg_combos)
      else:
        for tg_combo in tg_combos:
          assert (stars.tiangan in tg_combo) == (tg_combo in at_birth.star_relations.tiangan[tg_rel])

    for dz_rel, dz_combos in dizhi_utils.discover(
      chart.bazi.four_dizhis,
      definitions=chart.bazi.config.school.relation_definitions, # The oracle mirrors the chart's school (issue #69).
    ).items():
      if dz_rel not in at_birth.star_relations.dizhi:
        assert all(dz not in dz_combo for dz_combo in dz_combos for dz in stars.dizhi)
      else:
        for dz_combo in dz_combos:
          assert any(dz in dz_combo for dz in stars.dizhi) == (dz_combo in at_birth.star_relations.dizhi[dz_rel])


@pytest.mark.slow
def test_transit_shensha(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    transit_chart = TransitChart(chart)

    y_dz = chart.bazi.year_pillar.dizhi
    d_dz = chart.bazi.day_pillar.dizhi
    school = chart.bazi.config.school
    # The five Dizhi-anchored Shenshas each carry their own knob -- read each one, never a shared flag.
    year_anchored = {
      'yima':      school.yima_anchor is Anchor.YEAR_AND_DAY,
      'huagai':    school.huagai_anchor is Anchor.YEAR_AND_DAY,
      'jiangxing': school.jiangxing_anchor is Anchor.YEAR_AND_DAY,
      'jiesha':    school.jiesha_anchor is Anchor.YEAR_AND_DAY,
      'wangshen':  school.wangshen_anchor is Anchor.YEAR_AND_DAY,
    }
    use_day_zaisha_anchor = school.zaisha_anchor is Anchor.YEAR_AND_DAY

    # The 红艳 anchor stem follows the chart's school (查法锚, issue #69) -- don't assume the day master.
    anchor: Tiangan = (chart.bazi.day_master if school.hongyan_anchor is Anchor.DAY
                       else chart.bazi.year_pillar.tiangan)

    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = random_year_transits(transit_chart, random_year, rng)

      transit_dz = tuple(gz.dizhi for gz in transits.ganzhis)
      actual = transits_analysis.shensha(transits)

      # Taohua / 桃花
      expected = []
      for dz in transit_dz:
        if shensha_utils.taohua(y_dz, dz):
          expected.append(dz)
        if shensha_utils.taohua(d_dz, dz):
          expected.append(dz)
      assert actual['taohua'] == set(expected)

      # Hongyan / 红艳
      expected = []
      for dz in transit_dz:
        if shensha_utils.hongyan(anchor, dz):
          expected.append(dz)
      assert actual['hongyan'] == set(expected)

      # Hongluan / 红鸾
      expected = []
      for dz in transit_dz:
        if shensha_utils.hongluan(y_dz, dz):
          expected.append(dz)
      assert actual['hongluan'] == set(expected)

      # Tianxi / 天喜
      expected = []
      for dz in transit_dz:
        if shensha_utils.tianxi(y_dz, dz):
          expected.append(dz)
      assert actual['tianxi'] == set(expected)

      # Yima / 驿马
      expected = []
      for dz in transit_dz:
        if year_anchored['yima'] and shensha_utils.yima(y_dz, dz):
          expected.append(dz)
        if shensha_utils.yima(d_dz, dz):
          expected.append(dz)
      assert actual['yima'] == set(expected)

      # Huagai / 华盖
      expected = []
      for dz in transit_dz:
        if year_anchored['huagai'] and shensha_utils.huagai(y_dz, dz):
          expected.append(dz)
        if shensha_utils.huagai(d_dz, dz):
          expected.append(dz)
      assert actual['huagai'] == set(expected)

      # Yangren / 羊刃
      expected = []
      for dz in transit_dz:
        if shensha_utils.yangren(
          chart.bazi.day_master,
          dz,
          definition=chart.bazi.config.school.yangren_def,
        ):
          expected.append(dz)
      assert actual['yangren'] == set(expected)

      # Feiren / 飞刃
      expected = []
      for dz in transit_dz:
        if shensha_utils.feiren(
          chart.bazi.day_master,
          dz,
          definition=chart.bazi.config.school.feiren_def,
        ):
          expected.append(dz)
      assert actual['feiren'] == set(expected)

      # Tianyi Guiren / 天乙贵人
      expected = []
      for tg, dz in itertools.product(
        [chart.bazi.year_pillar.tiangan, chart.bazi.day_master],
        transit_dz,
      ):
        if shensha_utils.tianyi(
          tg,
          dz,
          definition=chart.bazi.config.school.tianyi_def,
        ):
          expected.append(dz)
      assert actual['tianyi'] == set(expected)

      # Jiangxing / 将星
      expected = []
      for dz in transit_dz:
        if year_anchored['jiangxing'] and shensha_utils.jiangxing(y_dz, dz):
          expected.append(dz)
        if shensha_utils.jiangxing(d_dz, dz):
          expected.append(dz)
      assert actual['jiangxing'] == set(expected)

      # Zaisha / 灾煞
      expected = []
      for dz in transit_dz:
        if shensha_utils.zaisha(y_dz, dz):
          expected.append(dz)
        if use_day_zaisha_anchor and shensha_utils.zaisha(d_dz, dz):
          expected.append(dz)
      assert actual['zaisha'] == set(expected)

      # Jiesha / 劫煞
      expected = []
      for dz in transit_dz:
        if year_anchored['jiesha'] and shensha_utils.jiesha(y_dz, dz):
          expected.append(dz)
        if shensha_utils.jiesha(d_dz, dz):
          expected.append(dz)
      assert actual['jiesha'] == set(expected)

      # Wangshen / 亡神
      expected = []
      for dz in transit_dz:
        if year_anchored['wangshen'] and shensha_utils.wangshen(y_dz, dz):
          expected.append(dz)
        if shensha_utils.wangshen(d_dz, dz):
          expected.append(dz)
      assert actual['wangshen'] == set(expected)

      # Guchen / 孤辰
      expected = [dz for dz in transit_dz if shensha_utils.guchen(y_dz, dz)]
      assert actual['guchen'] == set(expected)

      # Guasu / 寡宿
      expected = [dz for dz in transit_dz if shensha_utils.guasu(y_dz, dz)]
      assert actual['guasu'] == set(expected)

      # Lushen / 禄神
      expected = [dz for dz in transit_dz if shensha_utils.lushen(chart.bazi.day_master, dz)]
      assert actual['lushen'] == set(expected)

      # Jinyu / 金舆
      expected = [dz for dz in transit_dz if shensha_utils.jinyu(chart.bazi.day_master, dz)]
      assert actual['jinyu'] == set(expected)
