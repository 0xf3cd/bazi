# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import unittest
import random
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo
from itertools import product
from typing import Optional, Union
from bazi import (
  Tiangan, Dizhi, Ganzhi, Wuxing, Yinyang, BaziUtils,
  BaziGender, BaziPrecision, BaziData, Bazi, 八字, Shishen, ShierZhangsheng,
  BaziChart, 命盘,
  TraitTuple, HiddenTianganDict
)


class TestBaziGender(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(BaziGender), 2)

    self.assertIs(BaziGender.YANG, BaziGender.MALE)
    self.assertIs(BaziGender.YANG, BaziGender.男)
    self.assertIs(BaziGender.YANG, BaziGender.阳)
    self.assertIs(BaziGender.YANG, BaziGender.乾)

    self.assertIs(BaziGender.YIN, BaziGender.FEMALE)
    self.assertIs(BaziGender.YIN, BaziGender.女)
    self.assertIs(BaziGender.YIN, BaziGender.阴)
    self.assertIs(BaziGender.YIN, BaziGender.坤)

  def test_str(self) -> None:
    self.assertEqual(str(BaziGender.YANG), '男')
    self.assertEqual(str(BaziGender.YIN), '女')
    self.assertIs(BaziGender.YANG, BaziGender('男'))
    self.assertIs(BaziGender.YIN, BaziGender('女'))


class TestBazi(unittest.TestCase):
  def test_init(self) -> None:
    for _ in range(128):
      random_dt: datetime = datetime(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      )

      bazi: Bazi = Bazi(
        birth_time=random_dt,
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )

      self.assertEqual(bazi.solar_birth_date, date(random_dt.year, random_dt.month, random_dt.day))
      self.assertEqual(bazi.hour, random_dt.hour)
      self.assertEqual(bazi.minute, random_dt.minute)
      self.assertEqual(bazi.gender, BaziGender.男)
      self.assertEqual(bazi.precision, BaziPrecision.DAY)

  def test_chinese(self) -> None:
    self.assertIs(Bazi, 八字)

    for _ in range(128):
      random_dt: datetime = datetime(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      )

      bazi: 八字 = 八字(
        birth_time=random_dt,
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )

      self.assertEqual(bazi.solar_birth_date, date(random_dt.year, random_dt.month, random_dt.day))
      self.assertEqual(bazi.hour, random_dt.hour)
      self.assertEqual(bazi.minute, random_dt.minute)
      self.assertEqual(bazi.gender, BaziGender.男)
      self.assertEqual(bazi.precision, BaziPrecision.DAY)

  def test_invalid_arguments(self) -> None:
    random_dt: datetime = datetime(
      year=random.randint(1950, 2000),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59)
    )

    with self.assertRaises(TypeError):
      Bazi(birth_time=random_dt, gender=BaziGender.男) # type: ignore # Missing `precision`
    with self.assertRaises(TypeError):
      Bazi(birth_time=random_dt, precision=BaziPrecision.DAY) # type: ignore # Missing `gender`
    with self.assertRaises(AssertionError):
      Bazi(birth_time='2024-03-03', gender=BaziGender.男, precision=BaziPrecision.DAY) # type: ignore # Currently doesn't take string as input
    with self.assertRaises(AssertionError):
      Bazi(birth_time=date(9999, 1, 1), gender=BaziGender.男, precision=BaziPrecision.DAY) # type: ignore
    with self.assertRaises(AssertionError):
      dt: datetime = datetime(
        year=9999, # Out of supported range.
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      )
      Bazi(birth_time=dt, gender=BaziGender.男, precision=BaziPrecision.DAY)
    with self.assertRaises(AssertionError):
      Bazi(
        birth_time=datetime(
          year=2000,
          month=1,
          day=1,
          hour=7,
          minute=0,
          second=0,
          tzinfo=ZoneInfo('Asia/Shanghai') # Doesn't support timezone.
        ),
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )

  @staticmethod
  def __create_bazi(dt: datetime) -> Bazi:
    return Bazi(
      birth_time=dt,
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )

  def test_four_dizhis_correctness(self) -> None:
    '''
    Test the correctness of `Bazi` on the given test cases.
    Precision is at `DAY` level.
    '''
    def __subtest(dt: datetime, dizhi_strs: list[str]) -> None:
      assert len(dizhi_strs) == 4

      bazi = self.__create_bazi(dt)
      self.assertEqual(bazi.four_dizhis, (
        Dizhi.from_str(dizhi_strs[0]),
        Dizhi.from_str(dizhi_strs[1]),
        Dizhi.from_str(dizhi_strs[2]),
        Dizhi.from_str(dizhi_strs[3]),
      ))

    with self.subTest('Basic cases'):
      # Data was collected from "测测" app on my iPhone 15 Pro Max.
      __subtest(datetime(2024, 2, 6, 11, 55), ['辰', '寅', '子', '午'])
      __subtest(datetime(1984, 4, 2, 4, 2), ['子', '卯', '寅', '寅'])

      __subtest(datetime(1998, 3, 17, 13, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 13, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 15, 0), ['寅', '卯', '亥', '申'])
      __subtest(datetime(1998, 3, 17, 23, 0), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 0, 59), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 1, 0), ['寅', '卯', '子', '丑'])

    with self.subTest('Edge cases'):
      __subtest(datetime(1998, 3, 17, 13, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 13, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 15, 0), ['寅', '卯', '亥', '申'])
      __subtest(datetime(1998, 3, 17, 23, 0), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 0, 59), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 1, 0), ['寅', '卯', '子', '丑'])

      __subtest(datetime(2000, 2, 3, 0, 0), ['卯', '丑', '卯', '子'])
      __subtest(datetime(2000, 2, 3, 22, 59), ['卯', '丑', '卯', '亥'])
      __subtest(datetime(2000, 2, 3, 23, 0), ['卯', '丑', '辰', '子'])
      __subtest(datetime(2000, 2, 4, 0, 0), ['辰', '寅', '辰', '子'])
      __subtest(datetime(2000, 2, 4, 1, 0), ['辰', '寅', '辰', '丑'])

  def test_four_tiangans_correctness(self) -> None:
    def __subtest(dt: datetime, tiangan_strs: list[str]) -> None:
      assert len(tiangan_strs) == 4

      bazi = self.__create_bazi(dt)
      self.assertEqual(bazi.four_tiangans, (
        Tiangan.from_str(tiangan_strs[0]),
        Tiangan.from_str(tiangan_strs[1]),
        Tiangan.from_str(tiangan_strs[2]),
        Tiangan.from_str(tiangan_strs[3]),
      ))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲', '丁', '丙', '庚'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚', '戊', '壬', '辛'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛', '戊', '丙', '戊'])
  
  def test_chart(self) -> None:
    def __subtest(dt: datetime, ganzhi_strs: list[str]) -> None:
      assert len(ganzhi_strs) == 4

      bazi = self.__create_bazi(dt)
      pillars: BaziData[Ganzhi] = bazi.pillars
      self.assertEqual(pillars.year, Ganzhi.from_str(ganzhi_strs[0]))
      self.assertEqual(pillars.month, Ganzhi.from_str(ganzhi_strs[1]))
      self.assertEqual(pillars.day, Ganzhi.from_str(ganzhi_strs[2]))
      self.assertEqual(pillars.hour, Ganzhi.from_str(ganzhi_strs[3]))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])

  def test_consistency(self) -> None:
    def __subtest(dt: datetime, ganzhi_strs: list[str]) -> None:
      assert len(ganzhi_strs) == 4

      bazi = self.__create_bazi(dt)
      pillars: BaziData[Ganzhi] = bazi.pillars

      self.assertEqual(bazi.day_master, pillars.day.tiangan)
      self.assertEqual(bazi.month_commander, pillars.month.dizhi)

      self.assertEqual(bazi.year_pillar, pillars.year)
      self.assertEqual(bazi.month_pillar, pillars.month)
      self.assertEqual(bazi.day_pillar, pillars.day)
      self.assertEqual(bazi.hour_pillar, pillars.hour)

      self.assertEqual(bazi.four_tiangans, tuple([tg for tg, _ in pillars]))
      self.assertEqual(bazi.four_dizhis, tuple([dz for _, dz in pillars]))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])


class TestBaziChart(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(BaziChart, 命盘)

    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)

    self.assertTrue(chart.is_day_master(bazi.day_master))
    for tg in Tiangan:
      if tg is not bazi.day_master:
        self.assertFalse(chart.is_day_master(tg))

  def test_malicious(self) -> None:
    with self.subTest('Modification attemp'):
      bazi: Bazi = Bazi(
        birth_time=datetime(1984, 4, 2, 4, 2),
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )
      chart: BaziChart = BaziChart(bazi)

      bazi._day_pillar = Ganzhi.from_str('甲子')
      self.assertEqual(chart.bazi._day_pillar, Ganzhi.from_str('丙寅'))
      self.assertEqual(bazi._day_pillar, Ganzhi.from_str('甲子'))

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
      self.assertEqual(BaziUtils.get_tiangan_traits(pillar.tiangan), pillar_traits.tiangan)
      self.assertEqual(BaziUtils.get_dizhi_traits(pillar.dizhi), pillar_traits.dizhi)

  def test_hidden_tiangans(self) -> None:
    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    hidden_tiangans: BaziData[HiddenTianganDict] = chart.hidden_tiangans

    self.assertEqual(len(list(hidden_tiangans)), 4)

    self.assertDictEqual(hidden_tiangans.year, {  # 子
      Tiangan.癸 : 100,
    })
    self.assertDictEqual(hidden_tiangans.month, { # 卯
      Tiangan.乙 : 100,
    })
    self.assertDictEqual(hidden_tiangans.day, {   # 寅
      Tiangan.甲 : 60, Tiangan.丙 : 30, Tiangan.戊 : 10,
    })
    self.assertDictEqual(hidden_tiangans.hour, {  # 寅
      Tiangan.甲 : 60, Tiangan.丙 : 30, Tiangan.戊 : 10,
    })

  def test_shishens(self) -> None:
    chart: BaziChart = BaziChart.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    shishens: BaziData[BaziChart.PillarShishens] = chart.shishens

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

  def test_nayins(self) -> None:
    chart: BaziChart = BaziChart.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    nayins: BaziData[str] = chart.nayins

    self.assertEqual(len(list(nayins)), 4)

    #           Year    Month     Day     Hour
    # Tiangan    甲       丁       丙       庚
    #   Dizhi    子       卯       寅       寅

    self.assertEqual(nayins.year, '海中金')
    self.assertEqual(nayins.month, '炉中火')
    self.assertEqual(nayins.day, '炉中火')
    self.assertEqual(nayins.hour, '松柏木')

  def test_shier_zhangshengs(self) -> None:
    chart: BaziChart = BaziChart.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    zhangshengs: BaziData[ShierZhangsheng] = chart.shier_zhangshengs

    self.assertEqual(len(list(zhangshengs)), 4)

    #           Year    Month     Day     Hour
    # Tiangan    甲       丁       丙       庚
    #   Dizhi    子       卯       寅       寅

    self.assertEqual(zhangshengs.year, ShierZhangsheng.胎)
    self.assertEqual(zhangshengs.month, ShierZhangsheng.沐浴)
    self.assertEqual(zhangshengs.day, ShierZhangsheng.长生)
    self.assertEqual(zhangshengs.hour, ShierZhangsheng.长生)

  def test_consistency(self) -> None:
    '''
    Test that the results provided by `traits`, `hidden_tiangans`, and `shishens` are consistent.
    '''
    for _ in range(256):
      chart: BaziChart = BaziChart.create(
        birth_time=datetime(
          random.randint(1903, 2097),
          random.randint(1, 12),
          random.randint(1, 28),
          random.randint(0, 23),
          random.randint(0, 59),
        ),
        gender=random.choice(list(BaziGender)),
        precision=BaziPrecision.DAY, # Currently only supports DAY-level precision.
      )

      day_master: Tiangan = chart.bazi.day_master
      pillars: BaziData[Ganzhi] = chart.bazi.pillars
      traits: BaziData[BaziChart.PillarTraits] = chart.traits
      hidden_tiangans: BaziData[HiddenTianganDict] = chart.hidden_tiangans
      shishens: BaziData[BaziChart.PillarShishens] = chart.shishens

      # The major component in hidden Tiangans of a Dizhi is expected to be of the same Wuxing as the Dizhi.
      # 地支中的主气（即本气）应该和地支本身的五行一致。
      for pillar_traits, pillar_hidden_tiangans in zip(traits, hidden_tiangans):
        major_tiangan: Tiangan = max(pillar_hidden_tiangans.items(), key=lambda pair: pair[1])[0]
        self.assertEqual(pillar_traits.dizhi.wuxing, BaziUtils.get_tiangan_traits(major_tiangan).wuxing)

      # Double-check that the shishens are correct.
      # 确保各个天干地支的十神准确。
      for pillar_idx, (pillar, pillar_traits, pillar_shishens) in enumerate(zip(pillars, traits, shishens)):
        # Check Dizhi.
        dz_shishen: Shishen = pillar_shishens.dizhi
        dz_traits: TraitTuple = pillar_traits.dizhi
        self.assertEqual(dz_shishen, BaziUtils.get_shishen(day_master, pillar.dizhi))
        self.assertEqual(dz_traits, BaziUtils.get_dizhi_traits(pillar.dizhi))

        # Check Tiangan.
        tg_shishen: Optional[Shishen] = pillar_shishens.tiangan
        if pillar_idx == 2: # Day master.
          self.assertIsNone(tg_shishen)
          continue

        tg_traits: TraitTuple = pillar_traits.tiangan
        self.assertEqual(tg_shishen, BaziUtils.get_shishen(day_master, pillar.tiangan))
        self.assertEqual(tg_traits, BaziUtils.get_tiangan_traits(pillar.tiangan))

  def test_json(self) -> None:
    for _ in range(64):
      dt: datetime = datetime(
        random.randint(1903, 2097),
        random.randint(1, 12),
        random.randint(1, 28),
        random.randint(0, 23),
        random.randint(0, 59),
      )
      chart: BaziChart = BaziChart.create(
        birth_time=dt,
        gender=random.choice(list(BaziGender)),
        precision=BaziPrecision.DAY, # Currently only supports DAY-level precision.
      )

      j: dict = chart.json
      j_str: str = json.dumps(j)
      __j: dict = json.loads(j_str)

      self.assertEqual(j, __j)

      # Do something bad on the JSON object `__j`.
      # This shouldn't have any effect on `chart`.
      __j['datetime'] = datetime.now().isoformat()
      __j['gender'] = 'male'
      __j['tiangan_traits'], __j['dizhi_traits'] = __j['dizhi_traits'], __j['tiangan_traits']
      __j['tiangan_shishens'], __j['dizhi_shishens'] = __j['dizhi_shishens'], __j['tiangan_shishens']
      self.assertEqual(chart.json, j)
      self.assertNotEqual(chart.json, __j)

      self.assertEqual(datetime.fromisoformat(j['birth_time']), dt)
      self.assertEqual(j['precision'], 'day') # Currently only supports DAY-level precision.

      j_gender: BaziGender = BaziGender.MALE
      if j['gender'] == 'female':
        j_gender = BaziGender.FEMALE
      self.assertEqual(j_gender, chart.bazi.gender)

      __chart: BaziChart = BaziChart.create(datetime.fromisoformat(j['birth_time']), j_gender, BaziPrecision.DAY)

      self.assertEqual(j, __chart.json)

  def test_json_correctness(self) -> None:
    chart: BaziChart = BaziChart.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    
    #           Year    Month     Day     Hour
    # Tiangan    甲       丁       丙       庚
    #   Dizhi    子       卯       寅       寅

    j: dict = chart.json
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

    self.assertEqual(j['hidden_tiangans'], {
      'year': { '癸': 100 },
      'month': { '乙': 100 },
      'day': { '甲': 60, '丙': 30, '戊': 10 },
      'hour': { '甲': 60, '丙': 30, '戊': 10 },
    })

    self.assertEqual(j['tiangan_shishens'], {
      'year': '偏印',
      'month': '劫财',
      'day': None,
      'hour': '偏财',
    })

    self.assertEqual(j['dizhi_shishens'], {
      'year': '正官',
      'month': '正印',
      'day': '偏印',
      'hour': '偏印',
    })

    self.assertEqual(j['nayins'], {
      'year': '海中金',
      'month': '炉中火',
      'day': '炉中火',
      'hour': '松柏木',
    })

    self.assertEqual(j['12zhangshengs'], {
      'year': '胎',
      'month': '沐浴',
      'day': '长生',
      'hour': '长生',
    })

  def test_create(self) -> None:
    with self.assertRaises(ValueError):
      BaziChart.create('WrongDatetimeFormat', BaziGender.FEMALE, BaziPrecision.DAY)
    with self.assertRaises(ValueError):
      BaziChart.create(datetime.now(), 'femal', BaziPrecision.DAY)
    with self.assertRaises(ValueError):
      BaziChart.create(datetime.now(), BaziGender.FEMALE, 'dya')

    # Create a datetime and set its timezone to Asia/Shanghai.
    _dt: datetime = datetime.now()
    _dt = _dt.replace(tzinfo=ZoneInfo('Asia/Shanghai'))
    with self.assertRaises(AssertionError):
      BaziChart.create(_dt, BaziGender.FEMALE, BaziPrecision.DAY)
    with self.assertRaises(AssertionError):
      BaziChart.create(_dt.isoformat(), BaziGender.FEMALE, BaziPrecision.DAY)

    now: datetime = datetime.now()
    dt_options: list[Union[str, datetime]] = [now, now.isoformat()]
    male_options: list[Union[str, BaziGender]] = [BaziGender.男, BaziGender.YANG, BaziGender.阳, 'Male', '男', 'MALE']
    female_options: list[Union[str, BaziGender]] = [BaziGender.YIN, BaziGender.FEMALE, '女', 'FEMALE', 'female']
    day_precision_options: list[Union[str, BaziPrecision]] = [BaziPrecision.DAY, 'day', 'DAY', 'Day', '日', '天', 'd', 'D']

    expected_chart: BaziChart = BaziChart.create(now, BaziGender.FEMALE, BaziPrecision.DAY)
    for dt, g, p in product(dt_options, female_options, day_precision_options):
      chart: BaziChart = BaziChart.create(dt, g, p)
      self.assertEqual(chart.json, expected_chart.json)
    
    expected_chart: BaziChart = BaziChart.create(now, BaziGender.MALE, BaziPrecision.DAY)
    for dt, g, p in product(dt_options, male_options, day_precision_options):
      chart: BaziChart = BaziChart.create(dt, g, p)
      self.assertEqual(chart.json, expected_chart.json)

    unsupported_precision_options: list = [BaziPrecision.HOUR, BaziPrecision.MINUTE, 'hour', 'minute', 'H', 'm', '时', '小时', '分', '分钟']
    for dt, g, p in product(dt_options, male_options + female_options, unsupported_precision_options):
      with self.assertRaises(AssertionError):
        BaziChart.create(dt, g, p) # Other level precision is not supported at the moment
