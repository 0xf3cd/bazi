# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazichart.py

import json
import copy
import itertools

import pytest
import unittest

from datetime import datetime, date, timedelta
from typing import Optional

from src.Defines import Tiangan, Ganzhi, Wuxing, Yinyang, Shishen, ShierZhangsheng
from src.Bazi import BaziGender, BaziPrecision, Bazi
from src.Utils import BaziUtils

from src.Common import (
  TraitTuple, DayunTuple, XiaoyunTuple,
  HiddenTianganDict, BaziData, BaziJson
)

from src.BaziChart import BaziChart, 命盘


class TestBaziChart(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(BaziChart, 命盘)

    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)

    self.assertEqual(chart.bazi.day_master, bazi.day_master)
    for tg in Tiangan:
      if tg is not bazi.day_master:
        self.assertNotEqual(chart.bazi.day_master, tg)

    self.assertRaises(AssertionError, lambda: BaziChart(date(2024, 1, 1)))  # type: ignore

  def test_malicious(self) -> None:
    with self.subTest('Modification attemp'):
      bazi: Bazi = Bazi(
        birth_time=datetime(1984, 4, 2, 4, 2),
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )
      chart: BaziChart = BaziChart(bazi)

      bazi._day_pillar = Ganzhi.from_str('甲子') # type: ignore
      self.assertEqual(chart.bazi._day_pillar, Ganzhi.from_str('丙寅'))
      self.assertEqual(bazi._day_pillar, Ganzhi.from_str('甲子'))

    with self.assertRaises(AttributeError):
      BaziChart(Bazi.random()).bazi = Bazi.random()  # type: ignore

    with self.subTest('Invalid __init__ parameters'):
      with self.assertRaises(AssertionError):
        BaziChart('1984-04-02 04:02:00') # type: ignore
      with self.assertRaises(TypeError):
        BaziChart(datetime(1984, 4, 2, 4, 2), BaziGender.男, BaziPrecision.DAY) # type: ignore

  def test_traits(self) -> None:
    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    traits: BaziData[BaziChart.PillarTraits] = chart.traits

    self.assertEqual(len(list(traits)), 4)

    self.assertEqual(traits.year.tiangan, TraitTuple(Wuxing.木, Yinyang.阳))  # 甲
    self.assertEqual(traits.year.dizhi, TraitTuple(Wuxing.水, Yinyang.阳))    # 子

    self.assertEqual(traits.month.tiangan, TraitTuple(Wuxing.火, Yinyang.阴)) # 丁
    self.assertEqual(traits.month.dizhi, TraitTuple(Wuxing.木, Yinyang.阴))   # 卯

    self.assertEqual(traits.day.tiangan, TraitTuple(Wuxing.火, Yinyang.阳))   # 丙
    self.assertEqual(traits.day.dizhi, TraitTuple(Wuxing.木, Yinyang.阳))     # 寅

    self.assertEqual(traits.hour.tiangan, TraitTuple(Wuxing.金, Yinyang.阳))  # 庚
    self.assertEqual(traits.hour.dizhi, TraitTuple(Wuxing.木, Yinyang.阳))    # 寅

    for pillar, pillar_traits in zip(bazi.pillars, traits):
      self.assertEqual(BaziUtils.tiangan_traits(pillar.tiangan), pillar_traits.tiangan)
      self.assertEqual(BaziUtils.dizhi_traits(pillar.dizhi), pillar_traits.dizhi)

  def test_hidden_tiangans(self) -> None:
    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    hidden_tiangans: BaziData[HiddenTianganDict] = chart.hidden_tiangan

    self.assertEqual(len(list(hidden_tiangans)), 4)

    self.assertDictEqual(dict(hidden_tiangans.year), {  # 子
      Tiangan.癸 : 100,
    })
    self.assertDictEqual(dict(hidden_tiangans.month), { # 卯
      Tiangan.乙 : 100,
    })
    self.assertDictEqual(dict(hidden_tiangans.day), {   # 寅
      Tiangan.甲 : 60, Tiangan.丙 : 30, Tiangan.戊 : 10,
    })
    self.assertDictEqual(dict(hidden_tiangans.hour), {  # 寅
      Tiangan.甲 : 60, Tiangan.丙 : 30, Tiangan.戊 : 10,
    })

  def test_shishens(self) -> None:
    chart: BaziChart = BaziChart(Bazi.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    ))
    shishens: BaziData[BaziChart.PillarShishens] = chart.shishen

    self.assertEqual(len(list(shishens)), 4)

    #           Year    Month     Day     Hour
    # Tiangan    甲       丁       丙       庚
    #   Dizhi    子       卯       寅       寅

    self.assertEqual(shishens.year.tiangan, Shishen.偏印)
    self.assertEqual(shishens.year.dizhi, Shishen.正官)

    self.assertEqual(shishens.month.tiangan, Shishen.劫财)
    self.assertEqual(shishens.month.dizhi, Shishen.正印)

    self.assertEqual(shishens.day.tiangan, None) # Day master's shishen is None.
    self.assertEqual(shishens.day.dizhi, Shishen.偏印)

    self.assertEqual(shishens.hour.tiangan, Shishen.偏财)
    self.assertEqual(shishens.hour.dizhi, Shishen.偏印)

  def test_nayin(self) -> None:
    chart: BaziChart = BaziChart(Bazi.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    ))
    nayin: BaziData[str] = chart.nayin

    self.assertEqual(len(list(nayin)), 4)

    #           Year    Month     Day     Hour
    # Tiangan    甲       丁       丙       庚
    #   Dizhi    子       卯       寅       寅

    self.assertEqual(nayin.year, '海中金')
    self.assertEqual(nayin.month, '炉中火')
    self.assertEqual(nayin.day, '炉中火')
    self.assertEqual(nayin.hour, '松柏木')

  def test_shier_zhangsheng(self) -> None:
    chart: BaziChart = BaziChart(Bazi.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    ))
    zhangshengs: BaziData[ShierZhangsheng] = chart.shier_zhangsheng

    self.assertEqual(len(list(zhangshengs)), 4)

    #           Year    Month     Day     Hour
    # Tiangan    甲       丁       丙       庚
    #   Dizhi    子       卯       寅       寅

    self.assertEqual(zhangshengs.year, ShierZhangsheng.胎)
    self.assertEqual(zhangshengs.month, ShierZhangsheng.沐浴)
    self.assertEqual(zhangshengs.day, ShierZhangsheng.长生)
    self.assertEqual(zhangshengs.hour, ShierZhangsheng.长生)

  @pytest.mark.slow
  def test_basic_info_correctness(self) -> None:
    '''
    Test that the results provided by `traits`, `hidden_tiangans`, and `shishens` are correct.
    '''
    for _ in range(128):
      chart: BaziChart = BaziChart(Bazi.random())

      day_master: Tiangan = chart.bazi.day_master
      pillars: list[Ganzhi] = list(chart.bazi.pillars)
      traits: BaziData[BaziChart.PillarTraits] = chart.traits
      hidden_tiangans: BaziData[HiddenTianganDict] = chart.hidden_tiangan
      shishens: BaziData[BaziChart.PillarShishens] = chart.shishen

      # The major component in hidden Tiangans of a Dizhi is expected to be of the same Wuxing as the Dizhi.
      # 地支中的主气（即本气）应该和地支本身的五行一致。
      for pillar_traits, pillar_hidden_tiangans in zip(traits, hidden_tiangans):
        major_tiangan: Tiangan = max(pillar_hidden_tiangans.items(), key=lambda pair: pair[1])[0]
        self.assertEqual(pillar_traits.dizhi.wuxing, BaziUtils.tiangan_traits(major_tiangan).wuxing)

      # Double-check that the shishens are correct.
      # 确保各个天干地支的十神准确。
      for pillar_idx, (pillar, pillar_traits, pillar_shishens) in enumerate(zip(pillars, traits, shishens)):
        # Check Dizhi.
        dz_shishen: Shishen = pillar_shishens.dizhi
        dz_traits: TraitTuple = pillar_traits.dizhi
        self.assertEqual(dz_shishen, BaziUtils.shishen(day_master, pillar.dizhi))
        self.assertEqual(dz_traits, BaziUtils.dizhi_traits(pillar.dizhi))

        # Check Tiangan.
        tg_shishen: Optional[Shishen] = pillar_shishens.tiangan
        if pillar_idx == 2: # Day master.
          self.assertIsNone(tg_shishen)
          continue

        tg_traits: TraitTuple = pillar_traits.tiangan
        self.assertEqual(tg_shishen, BaziUtils.shishen(day_master, pillar.tiangan))
        self.assertEqual(tg_traits, BaziUtils.tiangan_traits(pillar.tiangan))

  def test_dayun_sexagenary_cycle(self) -> None:
    for _ in range(10):
      random_bazi: Bazi = Bazi.random()
      chart: BaziChart = BaziChart(random_bazi)

      dayun_gen = chart.dayun
      first_60_dayuns: list[Ganzhi] = [next(dayun_gen).ganzhi for _ in range(60)]
      next_60_dayuns: list[Ganzhi] = [next(dayun_gen).ganzhi for _ in range(60)]

      self.assertListEqual(first_60_dayuns, next_60_dayuns)
      self.assertSetEqual(set(first_60_dayuns), set(Ganzhi.list_sexagenary_cycle()))

  def test_dayun_order(self) -> None:
    for _ in range(10):
      random_bazi: Bazi = Bazi.random()
      
      month_gz: Ganzhi = random_bazi.month_pillar
      year_dz_yinyaang: Yinyang = BaziUtils.dizhi_traits(random_bazi.year_pillar.dizhi).yinyang

      cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
      expected_first_dayun_gz: Ganzhi = cycle[(cycle.index(month_gz) + 1) % 60]
      expected_order: bool = True
      if (random_bazi.gender is BaziGender.男) and (year_dz_yinyaang is Yinyang.阴):
        expected_first_dayun_gz = cycle[(cycle.index(month_gz) - 1) % 60]
        expected_order = False
      elif (random_bazi.gender is BaziGender.女) and (year_dz_yinyaang is Yinyang.阳):
        expected_first_dayun_gz = cycle[(cycle.index(month_gz) - 1) % 60]
        expected_order = False
      
      chart: BaziChart = BaziChart(random_bazi)
      first_dayun = next(chart.dayun)

      self.assertEqual(first_dayun.ganzhi, expected_first_dayun_gz)
      self.assertEqual(chart.dayun_order, expected_order)

  def test_dayun_start_moment(self) -> None:
    # TODO: currently `HkoDataCalendarUtils` only supports day-level precision,
    # which makes the `delta` a lot bigger.
    # After supporting finer precision, this test should be updated.
    delta: timedelta = timedelta(days=120)

    bazi1: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    self.assertAlmostEqual(
      BaziChart(bazi1).dayun_start_moment,
      datetime(2009, 12, 30),
      delta=delta,
    )

    bazi2: Bazi = Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY)
    self.assertAlmostEqual(
      BaziChart(bazi2).dayun_start_moment, 
      datetime(1985, 3, 5),
      delta=delta,
    )

    bazi3: Bazi = Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.FEMALE, BaziPrecision.DAY)
    self.assertAlmostEqual(
      BaziChart(bazi3).dayun_start_moment, 
      datetime(1993, 5, 25),
      delta=delta,
    )

  def test_dayun_ganzhi(self) -> None:
    bazi1: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    bazi1_dayun_gen = BaziChart(bazi1).dayun
    self.assertEqual(next(bazi1_dayun_gen).ganzhi, Ganzhi.from_str('己卯'))
    self.assertEqual(next(bazi1_dayun_gen).ganzhi, Ganzhi.from_str('庚辰'))
    self.assertEqual(next(bazi1_dayun_gen).ganzhi, Ganzhi.from_str('辛巳'))

    bazi2: Bazi = Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY)
    bazi2_dayun_gen = BaziChart(bazi2).dayun
    self.assertEqual(next(bazi2_dayun_gen).ganzhi, Ganzhi.from_str('戊辰'))
    self.assertEqual(next(bazi2_dayun_gen).ganzhi, Ganzhi.from_str('己巳'))
    self.assertEqual(next(bazi2_dayun_gen).ganzhi, Ganzhi.from_str('庚午'))

    bazi3: Bazi = Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.FEMALE, BaziPrecision.DAY)
    bazi3_dayun_gen = BaziChart(bazi3).dayun
    self.assertEqual(next(bazi3_dayun_gen).ganzhi, Ganzhi.from_str('丙寅'))
    self.assertEqual(next(bazi3_dayun_gen).ganzhi, Ganzhi.from_str('乙丑'))
    self.assertEqual(next(bazi3_dayun_gen).ganzhi, Ganzhi.from_str('甲子'))

  def test_dayun_ganzhi_year(self) -> None:
    bazi1: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    first_dayun1: DayunTuple = next(BaziChart(bazi1).dayun)
    self.assertEqual(first_dayun1.ganzhi_year, 2009)

    bazi2: Bazi = Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY)
    first_dayun2: DayunTuple = next(BaziChart(bazi2).dayun)
    self.assertEqual(first_dayun2.ganzhi_year, 1984) # TODO: 测测 Says Dayun starts in 1985. Revisit here later...

    bazi3: Bazi = Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.FEMALE, BaziPrecision.DAY)
    first_dayun3: DayunTuple = next(BaziChart(bazi3).dayun)
    self.assertEqual(first_dayun3.ganzhi_year, 1993)

    for _ in range(10):
      random_bazi: Bazi = Bazi.random()
      dayun_start_times: list[DayunTuple] = list(itertools.islice(BaziChart(random_bazi).dayun, 10))
      for dayun1, dayun2 in zip(dayun_start_times, dayun_start_times[1:]):
        self.assertEqual(dayun2.ganzhi_year - dayun1.ganzhi_year, 10)

  def test_dayun_db(self) -> None:
    bazi: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    chart: BaziChart = BaziChart(bazi)
    db = chart.dayun_db

    first_dayun: DayunTuple = next(chart.dayun)
    for year in range(first_dayun.ganzhi_year, first_dayun.ganzhi_year + 10):
      self.assertEqual(db[year], DayunTuple(first_dayun.ganzhi_year, Ganzhi.from_str('己卯')))
    for year in range(first_dayun.ganzhi_year + 10, first_dayun.ganzhi_year + 20):
      self.assertEqual(db[year], DayunTuple(first_dayun.ganzhi_year + 10, Ganzhi.from_str('庚辰')))
    for year in range(first_dayun.ganzhi_year + 20, first_dayun.ganzhi_year + 30):
      self.assertEqual(db[year], DayunTuple(first_dayun.ganzhi_year + 20, Ganzhi.from_str('辛巳')))

  def test_xiaoyun(self) -> None:
    def __subtest(bazi: Bazi, expected_xiaoyun_str: str) -> None:
      xiaoyuns: tuple[XiaoyunTuple, ...] = BaziChart(bazi).xiaoyun
      expected: list[Ganzhi] = [Ganzhi.from_str(s) for s in expected_xiaoyun_str.split()]
      self.assertEqual(len(xiaoyuns), len(expected))
      for age, gz in enumerate(expected, start=1):
        self.assertEqual(xiaoyuns[age-1].xusui, age)
        self.assertEqual(xiaoyuns[age-1].ganzhi, gz)
    
    # Data collected from https://p.china95.net/paipan/bazi/
    __subtest(Bazi.create(datetime(2017, 8, 17, 2, 23), BaziGender.MALE, BaziPrecision.DAY), 
              '戊子 丁亥 丙戌 乙酉')
    __subtest(Bazi.create(datetime(2017, 8, 17, 2, 23), BaziGender.FEMALE, BaziPrecision.DAY), 
              '庚寅 辛卯 壬辰 癸巳 甲午 乙未 丙申 丁酉')
    __subtest(Bazi.create(datetime(2017, 8, 16, 2, 23), BaziGender.MALE, BaziPrecision.DAY),
              '丙子 乙亥 甲戌 癸酉')
    __subtest(Bazi.create(datetime(2017, 4, 16, 2, 23), BaziGender.FEMALE, BaziPrecision.DAY),
              '甲寅 乙卯 丙辰 丁巳 戊午 己未 庚申')

  def test_liunian(self) -> None:
    cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
    for _ in range(16):
      random_bazi: Bazi = Bazi.random()
      chart: BaziChart = BaziChart(random_bazi)
      for year, ganzhi in itertools.islice(chart.liunian, 80):
        expected_ganzhi: Ganzhi = cycle[(year - 1924) % 60] # 1924 is a year of "甲子"
        self.assertEqual(ganzhi, expected_ganzhi)

      # The first liunian is also the birth ganzhi year.
      self.assertEqual(next(chart.liunian).ganzhi_year, random_bazi.ganzhi_date.year)

  @pytest.mark.slow
  def test_consistency(self) -> None:
    '''Ensure every run gives the consistent results...'''
    for _ in range(64):
      random_bazi: Bazi = Bazi.random()
      expected: BaziChart = BaziChart(random_bazi)

      for __ in range(5):
        chart: BaziChart = BaziChart(random_bazi)
        self.assertEqual(chart.bazi, expected.bazi)

        self.assertListEqual(list(chart.traits), list(expected.traits))
        self.assertListEqual(list(chart.hidden_tiangan), list(expected.hidden_tiangan))
        self.assertListEqual(list(chart.shishen), list(expected.shishen))
        self.assertListEqual(list(chart.nayin), list(expected.nayin))
        self.assertListEqual(list(chart.shier_zhangsheng), list(expected.shier_zhangsheng))

        self.assertEqual(chart.dayun_order, expected.dayun_order)
        self.assertEqual(chart.dayun_start_moment, expected.dayun_start_moment)
        self.assertEqual(chart.xiaoyun, expected.xiaoyun)

        self.assertEqual(list(itertools.islice(chart.liunian, 100)), 
                         list(itertools.islice(expected.liunian, 100)))
        self.assertEqual(list(itertools.islice(chart.dayun, 100)), 
                         list(itertools.islice(expected.dayun, 100)))

        self.assertDictEqual(chart.json, expected.json)

  @pytest.mark.slow
  def test_json(self) -> None:
    for _ in range(32):
      chart: BaziChart = BaziChart(Bazi.random())
      dt: datetime = chart.bazi.solar_datetime

      j: BaziJson.BaziChartJsonDict = chart.json
      j_str: str = json.dumps(j)
      __j: dict = json.loads(j_str)

      self.assertEqual(j, __j)

      # Do something bad on the JSON object `__j`.
      # This shouldn't have any effect on `chart`.
      __j['datetime'] = datetime.now().isoformat()
      __j['gender'] = 'male'
      __j['tiangan_traits'], __j['dizhi_traits'] = __j['dizhi_traits'], __j['tiangan_traits']
      __j['tiangan_shishen'], __j['dizhi_shishen'] = __j['dizhi_shishen'], __j['tiangan_shishen']
      self.assertEqual(chart.json, j)
      self.assertNotEqual(chart.json, __j)

      self.assertEqual(datetime.fromisoformat(j['birth_time']), dt)
      self.assertEqual(j['precision'], 'day') # Currently only supports DAY-level precision.

      j_gender: BaziGender = BaziGender.MALE
      if j['gender'] == 'female':
        j_gender = BaziGender.FEMALE
      self.assertEqual(j_gender, chart.bazi.gender)

      __chart: BaziChart = BaziChart(
        Bazi.create(datetime.fromisoformat(j['birth_time']), j_gender, BaziPrecision.DAY)
      )

      self.assertEqual(j, __chart.json)

  def test_json_correctness(self) -> None:
    chart: BaziChart = BaziChart(Bazi.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    ))
    
    #           Year    Month     Day     Hour
    # Tiangan    甲       丁       丙       庚
    #   Dizhi    子       卯       寅       寅

    j: BaziJson.BaziChartJsonDict = chart.json
    j_str: str = json.dumps(j)
    __j: dict = json.loads(j_str)

    self.assertEqual(j, __j)

    self.assertEqual(j['pillars'], {
      'year': '甲子',
      'month': '丁卯',
      'day': '丙寅',
      'hour': '庚寅',
    })

    self.assertEqual(j['tiangan_traits'], {
      'year': '阳木',
      'month': '阴火',
      'day': '阳火',
      'hour': '阳金',
    })

    self.assertEqual(j['dizhi_traits'], {
      'year': '阳水',
      'month': '阴木',
      'day': '阳木',
      'hour': '阳木',
    })

    self.assertEqual(j['hidden_tiangan'], {
      'year': '癸:100',
      'month': '乙:100',
      'day': '甲:60,丙:30,戊:10',
      'hour': '甲:60,丙:30,戊:10',
    })

    self.assertEqual(j['tiangan_shishen'], {
      'year': '偏印',
      'month': '劫财',
      'day': 'None',
      'hour': '偏财',
    })

    self.assertEqual(j['dizhi_shishen'], {
      'year': '正官',
      'month': '正印',
      'day': '偏印',
      'hour': '偏印',
    })

    self.assertEqual(j['nayin'], {
      'year': '海中金',
      'month': '炉中火',
      'day': '炉中火',
      'hour': '松柏木',
    })

    self.assertEqual(j['shier_zhangsheng'], {
      'year': '胎',
      'month': '沐浴',
      'day': '长生',
      'hour': '长生',
    })

  def test_deepcopy(self) -> None:
    chart: BaziChart = BaziChart(Bazi.random())

    chart2: BaziChart = copy.deepcopy(chart)

    self.assertIsNot(chart.bazi, chart2.bazi)
    self.assertIsNot(chart._bazi, chart2._bazi)

    old_bazi: Bazi = chart._bazi
    chart._bazi = BaziChart(Bazi.random())._bazi # type: ignore

    self.assertIsNot(chart.bazi, old_bazi)
    self.assertIsNot(chart._bazi, old_bazi)
