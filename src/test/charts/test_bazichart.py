# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazichart.py

import unittest
import random
import json
import copy

from datetime import datetime
from typing import Optional

from src.Defines import Tiangan, Ganzhi, Wuxing, Yinyang, Shishen, ShierZhangsheng
from src.Bazi import BaziGender, BaziPrecision, Bazi
from src.Common import TraitTuple, HiddenTianganDict, BaziData
from src.Utils import BaziUtils

from src.Charts import BaziChart
from src.Charts.BaziChart import 原盘


class TestBaziChart(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(BaziChart, 原盘)

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
    chart: BaziChart = BaziChart(Bazi.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    ))
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
    chart: BaziChart = BaziChart(Bazi.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    ))
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
    chart: BaziChart = BaziChart(Bazi.create(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    ))
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
      chart: BaziChart = BaziChart(Bazi.random())

      day_master: Tiangan = chart.bazi.day_master
      pillars: list[Ganzhi] = list(chart.bazi.pillars)
      traits: BaziData[BaziChart.PillarTraits] = chart.traits
      hidden_tiangans: BaziData[HiddenTianganDict] = chart.hidden_tiangans
      shishens: BaziData[BaziChart.PillarShishens] = chart.shishens

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

  def test_json(self) -> None:
    for _ in range(64):
      dt: datetime = datetime(
        random.randint(1903, 2097),
        random.randint(1, 12),
        random.randint(1, 28),
        random.randint(0, 23),
        random.randint(0, 59),
      )
      chart: BaziChart = BaziChart(Bazi.create(
        birth_time=dt,
        gender=random.choice(list(BaziGender)),
        precision=BaziPrecision.DAY, # Currently only supports DAY-level precision.
      ))

      j: BaziChart.JsonDict = chart.json
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

    j: BaziChart.JsonDict = chart.json
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
      'year': '癸:100',
      'month': '乙:100',
      'day': '甲:60,丙:30,戊:10',
      'hour': '甲:60,丙:30,戊:10',
    })

    self.assertEqual(j['tiangan_shishens'], {
      'year': '偏印',
      'month': '劫财',
      'day': 'None',
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

    self.assertEqual(j['shier_zhangshengs'], {
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
