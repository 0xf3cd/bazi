# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_defines.py

import unittest
from itertools import product
from bazi import (
  Tiangan, 天干, Dizhi, 地支, Ganzhi, 干支, Jieqi, 节气,
  Wuxing, 五行, Yinyang, 阴阳, Shishen, 十神
)


class TestTiangan(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Tiangan), 10)
    self.assertEqual(Tiangan.JIA.value, '甲')
    self.assertEqual(Tiangan('甲').value, '甲')
    self.assertNotEqual(Tiangan.WU, Tiangan.REN)
    self.assertNotEqual(Tiangan.WU.value, Tiangan.REN.value)

  def test_alias(self) -> None:
    self.assertEqual(天干, Tiangan)
    self.assertIs(天干, Tiangan)
    self.assertEqual(len(天干), 10)

    self.assertIs(Tiangan.甲, Tiangan.JIA)
    self.assertIs(Tiangan.甲, Tiangan.甲)
    self.assertIs(天干.甲, Tiangan.甲)
    self.assertIs(天干.甲, 天干.JIA)
    self.assertIs(天干.BING, 天干.丙)

    self.assertIsNot(Tiangan.甲, Tiangan.乙)

    self.assertEqual(天干.甲.value, '甲')
    self.assertEqual(天干.JIA.value, '甲')
    self.assertEqual(天干.丁.value, Tiangan.丁.value)
    self.assertEqual(天干.甲.value, Tiangan.JIA.value)
    self.assertEqual(天干.甲.value, 天干.JIA.value)

    self.assertNotEqual(天干.癸, 天干.庚)
    self.assertNotEqual(天干.甲.value, Tiangan.丁.value)
    self.assertNotEqual(天干.WU.value, '甲')

    for e in Tiangan:
      self.assertIsNotNone(e.value)
      self.assertIn(e, 天干)

    for e in 天干:
      self.assertIsNotNone(e.value)
      self.assertIn(e, Tiangan)

  def test_as_list(self) -> None:
    self.assertListEqual(Tiangan.as_list(), list(Tiangan))
    self.assertListEqual(Tiangan.as_list(), \
      [Tiangan.甲, Tiangan.乙, Tiangan.丙, Tiangan.丁, Tiangan.戊, Tiangan.己, Tiangan.庚, Tiangan.辛, Tiangan.壬, Tiangan.癸])
  
  def test_from_str(self) -> None:
    with self.assertRaises(ValueError):
      Tiangan.from_str('甲甲')
    with self.assertRaises(ValueError):
      Tiangan.from_str('JIA')
    with self.assertRaises(ValueError):
      Tiangan.from_str('Jia')
    with self.assertRaises(ValueError):
      Tiangan.from_str('子')
    with self.assertRaises(AssertionError):
      Tiangan.from_str(Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      Tiangan.from_str(0) # type: ignore

    self.assertEqual(Tiangan.from_str('甲'), Tiangan.甲)
    self.assertEqual(Tiangan.甲, Tiangan.from_str('甲'))
    self.assertEqual(Tiangan.from_str('丁'), Tiangan.from_str('丁'))
    self.assertNotEqual(Tiangan.甲, Tiangan.from_str('丁'))
    self.assertNotEqual(Tiangan.from_str('丁'), Tiangan.from_str('甲'))
                        
  def test_str(self) -> None:
    for e in Tiangan:
      self.assertEqual(str(e), e.value)
      self.assertIs(Tiangan(str(e)), e)
    for e in Tiangan.as_list():
      self.assertEqual(str(e), e.value)
      self.assertIs(Tiangan(str(e)), e)

    self.assertEqual('甲乙丙丁戊己庚辛壬癸', ''.join([str(e) for e in Tiangan.as_list()]))

  def test_index(self) -> None:
    self.assertEqual(Tiangan.甲.index, 0)
    self.assertEqual(Tiangan.乙.index, 1)
    self.assertEqual(Tiangan.丙.index, 2)
    self.assertEqual(Tiangan.丁.index, 3)
    self.assertEqual(Tiangan.戊.index, 4)
    self.assertEqual(Tiangan.己.index, 5)
    self.assertEqual(Tiangan.庚.index, 6)
    self.assertEqual(Tiangan.辛.index, 7)
    self.assertEqual(Tiangan.壬.index, 8)
    self.assertEqual(Tiangan.癸.index, 9)

  def test_from_index(self) -> None:
    self.assertEqual(Tiangan.from_index(0), Tiangan.甲)
    self.assertEqual(Tiangan.from_index(1), Tiangan.乙)
    self.assertEqual(Tiangan.from_index(2), Tiangan.丙)
    self.assertEqual(Tiangan.from_index(3), Tiangan.丁)
    self.assertEqual(Tiangan.from_index(4), Tiangan.戊)
    self.assertEqual(Tiangan.from_index(5), Tiangan.己)
    self.assertEqual(Tiangan.from_index(6), Tiangan.庚)
    self.assertEqual(Tiangan.from_index(7), Tiangan.辛)
    self.assertEqual(Tiangan.from_index(8), Tiangan.壬)
    self.assertEqual(Tiangan.from_index(9), Tiangan.癸)
    with self.assertRaises(IndexError):
      Tiangan.from_index(10)
    with self.assertRaises(IndexError):
      Tiangan.from_index(-11)

class TestDizhi(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(12, len(Dizhi))
    self.assertEqual('子', Dizhi.ZI.value)
    self.assertEqual(Dizhi('子'), Dizhi.子)
    self.assertNotEqual(Dizhi.WEI, Dizhi.SHEN)
    self.assertNotEqual(Dizhi.WEI.value, Dizhi.SHEN.value)

  def test_alias(self) -> None:
    self.assertEqual(地支, Dizhi)
    self.assertIs(地支, Dizhi)
    self.assertEqual(12, len(地支))

    self.assertIs(Dizhi.子, Dizhi.ZI)
    self.assertIs(Dizhi.子, 地支.ZI)
    self.assertIs(Dizhi.子, 地支.子)
    
    self.assertIsNot(Dizhi.丑, Dizhi.午)

    self.assertEqual('午', 地支.午.value)
    self.assertEqual('午', Dizhi.午.value)
    self.assertEqual('未', 地支.WEI.value)
    self.assertEqual(Dizhi.午.value, Dizhi.WU.value)
    self.assertEqual(Dizhi.午.value, 地支.WU.value)
    
    self.assertNotEqual('未', 地支.SHEN.value)
    self.assertNotEqual(地支.申, 地支.未)

    for e in 地支:
      self.assertIsNotNone(e.value)
      self.assertIn(e, Dizhi)

    for e in Dizhi:
      self.assertIsNotNone(e.value)
      self.assertIn(e, 地支)

  def test_as_list(self) -> None:
    self.assertListEqual(Dizhi.as_list(), list(Dizhi))
    self.assertListEqual(Dizhi.as_list(), \
      [Dizhi.子, Dizhi.丑, Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.巳, Dizhi.午, Dizhi.未, Dizhi.申, Dizhi.酉, Dizhi.戌, Dizhi.亥])
  
  def test_from_str(self) -> None:
    with self.assertRaises(ValueError):
      Dizhi.from_str('子子')
    with self.assertRaises(ValueError):
      Dizhi.from_str('ZI')
    with self.assertRaises(ValueError):
      Dizhi.from_str('Zi')
    with self.assertRaises(ValueError):
      Dizhi.from_str('甲')
    with self.assertRaises(AssertionError):
      Dizhi.from_str(Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      Dizhi.from_str(0) # type: ignore
    with self.assertRaises(AssertionError):
      Dizhi.from_str(Tiangan.丁) # type: ignore

    self.assertEqual(Dizhi.from_str('寅'), Dizhi.寅)
    self.assertEqual(Dizhi.寅, Dizhi.from_str('寅'))
    self.assertEqual(Dizhi.from_str('卯'), Dizhi.from_str('卯'))
    self.assertNotEqual(Dizhi.寅, Dizhi.from_str('卯'))
    self.assertNotEqual(Dizhi.from_str('卯'), Dizhi.from_str('寅'))

  def test_str(self) -> None:
    for e in Dizhi:
      self.assertEqual(str(e), e.value)
      self.assertIs(Dizhi(str(e)), e)
    for e in Dizhi.as_list():
      self.assertEqual(str(e), e.value)
      self.assertIs(Dizhi(str(e)), e)

    self.assertEqual('子丑寅卯辰巳午未申酉戌亥', ''.join([str(e) for e in Dizhi.as_list()]))

  def test_index(self) -> None:
    self.assertEqual(Dizhi.子.index, 0)
    self.assertEqual(Dizhi.丑.index, 1)
    self.assertEqual(Dizhi.寅.index, 2)
    self.assertEqual(Dizhi.卯.index, 3)
    self.assertEqual(Dizhi.辰.index, 4)
    self.assertEqual(Dizhi.巳.index, 5)
    self.assertEqual(Dizhi.午.index, 6)
    self.assertEqual(Dizhi.未.index, 7)
    self.assertEqual(Dizhi.申.index, 8)
    self.assertEqual(Dizhi.酉.index, 9)
    self.assertEqual(Dizhi.戌.index, 10)
    self.assertEqual(Dizhi.亥.index, 11)

  def test_from_index(self) -> None:
    self.assertEqual(Dizhi.from_index(0), Dizhi.子)
    self.assertEqual(Dizhi.from_index(1), Dizhi.丑)
    self.assertEqual(Dizhi.from_index(2), Dizhi.寅)
    self.assertEqual(Dizhi.from_index(3), Dizhi.卯)
    self.assertEqual(Dizhi.from_index(4), Dizhi.辰)
    self.assertEqual(Dizhi.from_index(5), Dizhi.巳)
    self.assertEqual(Dizhi.from_index(6), Dizhi.午)
    self.assertEqual(Dizhi.from_index(7), Dizhi.未)
    self.assertEqual(Dizhi.from_index(8), Dizhi.申)
    self.assertEqual(Dizhi.from_index(9), Dizhi.酉)
    self.assertEqual(Dizhi.from_index(10), Dizhi.戌)
    self.assertEqual(Dizhi.from_index(11), Dizhi.亥)
    with self.assertRaises(IndexError):
      Dizhi.from_index(12)
    with self.assertRaises(IndexError):
      Dizhi.from_index(-13)

class TestGanzhi(unittest.TestCase):
  def test_basic(self) -> None:
    gz_jiazi: Ganzhi = Ganzhi(Tiangan.JIA, Dizhi.ZI)
    gz_jiazi2: Ganzhi = Ganzhi(Tiangan.甲, Dizhi.子)
    gz_bingwu: Ganzhi = Ganzhi(Tiangan.丙, Dizhi.午)

    self.assertEqual(gz_jiazi.tiangan, Tiangan.甲)
    self.assertEqual(gz_jiazi.dizhi, Dizhi.子)
    self.assertEqual(gz_jiazi2.tiangan, Tiangan.甲)
    self.assertEqual(gz_jiazi2.dizhi, Dizhi.子)
    self.assertEqual(gz_bingwu.tiangan, Tiangan.丙)
    self.assertEqual(gz_bingwu.dizhi, Dizhi.午)
    self.assertEqual(gz_jiazi, gz_jiazi2)
    self.assertNotEqual(gz_jiazi, gz_bingwu)
    self.assertNotEqual(gz_jiazi2, gz_bingwu)

    gz_list: list[Ganzhi] = []
    for _ in range(3):
      for tg in Tiangan:
        for dz in Dizhi:
          gz_list.append(Ganzhi(tg, dz))
          
    # In theory, 10 tiangans and 12 dizhis can produce 120 different Ganzhis.
    self.assertEqual(len(set(gz_list)), 120)

  def test_alias(self) -> None:
    self.assertIs(Ganzhi, 干支)
    self.assertEqual(Ganzhi(Tiangan.WU, Dizhi.XU), 干支(天干.戊, 地支.戌))  
    self.assertNotEqual(Ganzhi(Tiangan.WU, Dizhi.XU), Ganzhi(Tiangan.WU, Dizhi.MAO))

  def test_from_strs(self) -> None:
    self.assertEqual(Ganzhi.from_strs('甲', '子'), Ganzhi(Tiangan.甲, Dizhi.子))
    self.assertEqual(Ganzhi.from_strs('戊', '午'), Ganzhi(Tiangan.戊, Dizhi.午))
    self.assertNotEqual(Ganzhi.from_strs('丙', '子'), Ganzhi(Tiangan.丙, Dizhi.寅))

    with self.assertRaises(ValueError):
      Ganzhi.from_strs('假', '子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('JIA', '子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('Jia', '子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('甲', '子子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('子', '甲')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('子', '子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('甲', '甲')
    with self.assertRaises(AssertionError):
      Ganzhi.from_strs('甲', Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      Ganzhi.from_strs(Tiangan.甲, '子') # type: ignore
    with self.assertRaises(AssertionError):
      Ganzhi.from_strs(0, 0) # type: ignore

  def test_from_str(self) -> None:
    self.assertEqual(Ganzhi.from_str('甲子'), Ganzhi(Tiangan.甲, Dizhi.子))
    self.assertEqual(Ganzhi.from_str('戊午'), Ganzhi(Tiangan.戊, Dizhi.午))
    self.assertNotEqual(Ganzhi.from_str('丙子'), Ganzhi(Tiangan.丙, Dizhi.寅))

    with self.assertRaises(ValueError):
      Ganzhi.from_str('假子')
    with self.assertRaises(AssertionError):
      Ganzhi.from_str('JIA子')
    with self.assertRaises(AssertionError):
      Ganzhi.from_str('Jia子')
    with self.assertRaises(AssertionError):
      Ganzhi.from_str('甲子子')
    with self.assertRaises(ValueError):
      Ganzhi.from_str('子甲')
    with self.assertRaises(ValueError):
      Ganzhi.from_str('子子')
    with self.assertRaises(ValueError):
      Ganzhi.from_str('甲甲')
    with self.assertRaises(TypeError):
      Ganzhi.from_str(0) # type: ignore

  def test_str(self) -> None:
    for tg in Tiangan.as_list():
      for dz in Dizhi.as_list():
        # `Ganzhi` should be able to hold all 120 possible Tiangan-Dizhi pairs
        self.assertEqual(str(Ganzhi(tg, dz)), f'{tg}{dz}')
        self.assertEqual(Ganzhi.from_str(str(Ganzhi(tg, dz))), Ganzhi(tg, dz))

  def test_list_sexagenary_cycle(self) -> None:
    sexagenary_cycle = Ganzhi.list_sexagenary_cycle()

    self.assertEqual(len(sexagenary_cycle), 60)
    self.assertEqual(sexagenary_cycle[0], Ganzhi(Tiangan.甲, Dizhi.子))
    self.assertEqual(sexagenary_cycle[-1], Ganzhi(Tiangan.癸, Dizhi.亥))

    tg_list = Tiangan.as_list()
    dz_list = Dizhi.as_list()
    for i, gz in enumerate(sexagenary_cycle):
      self.assertIs(gz.tiangan, tg_list[i % 10])
      self.assertIs(gz.dizhi, dz_list[i % 12])

  def test_list_sexagenary_cycle_strs(self) -> None:
    sexagenary_cycle_strs = Ganzhi.list_sexagenary_cycle_strs()

    self.assertEqual(len(sexagenary_cycle_strs), 60)
    self.assertEqual(sexagenary_cycle_strs[0], '甲子')
    self.assertEqual(sexagenary_cycle_strs[-1], '癸亥')

    tg_list = Tiangan.as_list()
    dz_list = Dizhi.as_list()
    for i, gz_str in enumerate(sexagenary_cycle_strs):
      self.assertEqual(gz_str, f'{tg_list[i % 10]}{dz_list[i % 12]}')


class TestJieqi(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Jieqi), 24)
    self.assertEqual(Jieqi.QINGMING.value, '清明')
    self.assertEqual(Jieqi('清明'), Jieqi.清明)
    self.assertNotEqual(Jieqi.QINGMING, Jieqi.LICHUN)
    self.assertNotEqual(Jieqi.QINGMING.value, Jieqi.LICHUN.value)

  def test_alias(self) -> None:
    self.assertIs(节气, Jieqi)
    self.assertEqual(len(节气), len(Jieqi))

    for jq in Jieqi:
      self.assertIsNotNone(jq.value)
      self.assertIn(jq, 节气)
      self.assertIn(jq.value, (jq.value for jq in 节气))

    for jq in 节气:
      self.assertIsNotNone(jq.value)
      self.assertIn(jq, Jieqi)
      self.assertIn(jq.value, (jq.value for jq in Jieqi))

    self.assertIs(节气.雨水, Jieqi.YUSHUI)
    self.assertIs(节气.雨水, 节气.YUSHUI)
    self.assertIs(节气.雨水, Jieqi.雨水)

    self.assertEqual(节气.惊蛰, Jieqi.JINGZHE)
    self.assertNotEqual(节气.春分, 节气.秋分)
    self.assertNotEqual(Jieqi.春分, Jieqi.秋分)

  def test_as_list(self) -> None:
    self.assertListEqual(Jieqi.as_list(), list(Jieqi))
    self.assertListEqual(Jieqi.as_list(), [
      Jieqi.立春, Jieqi.雨水, Jieqi.惊蛰, Jieqi.春分, Jieqi.清明, Jieqi.谷雨, Jieqi.立夏, Jieqi.小满, Jieqi.芒种, Jieqi.夏至, Jieqi.小暑, Jieqi.大暑, 
      Jieqi.立秋, Jieqi.处暑, Jieqi.白露, Jieqi.秋分, Jieqi.寒露, Jieqi.霜降, Jieqi.立冬, Jieqi.小雪, Jieqi.大雪, Jieqi.冬至, Jieqi.小寒, Jieqi.大寒
    ])

  def test_from_str(self) -> None:
    with self.assertRaises(ValueError):
      Jieqi.from_str('甲甲')
    with self.assertRaises(ValueError):
      Jieqi.from_str('處暑') # Not supporting traditional Chinese.
    with self.assertRaises(AssertionError):
      Jieqi.from_str('立秋 ')
    with self.assertRaises(AssertionError):
      Jieqi.from_str('SHUNFEN')
    with self.assertRaises(AssertionError):
      Jieqi.from_str('Xiazhi')
    with self.assertRaises(AssertionError):
      Jieqi.from_str('春')
    with self.assertRaises(AssertionError):
      Jieqi.from_str(Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      Jieqi.from_str(0) # type: ignore

    for jq in Jieqi:
      self.assertEqual(Jieqi.from_str(str(jq)), jq)
      self.assertEqual(Jieqi(str(jq)), jq)

    self.assertEqual(Jieqi.from_str('秋分'), Jieqi.秋分)
    self.assertEqual(Jieqi.from_str('秋分'), Jieqi.from_str('秋分'))
    self.assertNotEqual(Jieqi.from_str('秋分'), Jieqi.from_str('小寒'))

    self.assertIs(Jieqi.from_str('立春'), Jieqi.立春)
    self.assertIs(Jieqi.from_str('雨水'), Jieqi.雨水)
    self.assertIs(Jieqi.from_str('惊蛰'), Jieqi.惊蛰)
    self.assertIs(Jieqi.from_str('春分'), Jieqi.春分)
    self.assertIs(Jieqi.from_str('清明'), Jieqi.清明)
    self.assertIs(Jieqi.from_str('谷雨'), Jieqi.谷雨)
    self.assertIs(Jieqi.from_str('立夏'), Jieqi.立夏)
    self.assertIs(Jieqi.from_str('小满'), Jieqi.小满)
    self.assertIs(Jieqi.from_str('芒种'), Jieqi.芒种)
    self.assertIs(Jieqi.from_str('夏至'), Jieqi.夏至)
    self.assertIs(Jieqi.from_str('小暑'), Jieqi.小暑)
    self.assertIs(Jieqi.from_str('大暑'), Jieqi.大暑)
    self.assertIs(Jieqi.from_str('立秋'), Jieqi.立秋)
    self.assertIs(Jieqi.from_str('处暑'), Jieqi.处暑)
    self.assertIs(Jieqi.from_str('白露'), Jieqi.白露)
    self.assertIs(Jieqi.from_str('秋分'), Jieqi.秋分)
    self.assertIs(Jieqi.from_str('寒露'), Jieqi.寒露)
    self.assertIs(Jieqi.from_str('霜降'), Jieqi.霜降)
    self.assertIs(Jieqi.from_str('立冬'), Jieqi.立冬)
    self.assertIs(Jieqi.from_str('小雪'), Jieqi.小雪)
    self.assertIs(Jieqi.from_str('大雪'), Jieqi.大雪)
    self.assertIs(Jieqi.from_str('冬至'), Jieqi.冬至)
    self.assertIs(Jieqi.from_str('小寒'), Jieqi.小寒)
    self.assertIs(Jieqi.from_str('大寒'), Jieqi.大寒)

  def test_str(self) -> None:
    for jq in Jieqi:
      self.assertEqual(str(jq), jq.value)
      self.assertEqual(Jieqi.from_str(str(jq)), jq)
    for jq in Jieqi.as_list():
      self.assertEqual(str(jq), jq.value)
      self.assertEqual(Jieqi.from_str(str(jq)), jq)

    self.assertEqual(''.join([str(jq) for jq in Jieqi.as_list()]), 
                     '立春雨水惊蛰春分清明谷雨立夏小满芒种夏至小暑大暑立秋处暑白露秋分寒露霜降立冬小雪大雪冬至小寒大寒')


class TestWuxing(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Wuxing), 5)
    self.assertEqual(Wuxing.METAL.value, '金')
    self.assertEqual(Wuxing.金.value, '金')
    self.assertEqual(Wuxing('金'), Wuxing.金)
    self.assertNotEqual(Wuxing.金, Wuxing.木)
    self.assertNotEqual(Wuxing.金.value, Wuxing.木.value)

  def test_alias(self) -> None:
    self.assertIs(Wuxing.木, Wuxing.WOOD)
    self.assertIs(Wuxing.火, Wuxing.FIRE)
    self.assertIs(Wuxing.土, Wuxing.EARTH)
    self.assertIs(Wuxing.金, Wuxing.METAL)
    self.assertIs(Wuxing.水, Wuxing.WATER)
    self.assertIs(Wuxing, 五行)

  def test_as_list(self) -> None:
    self.assertEqual(len(Wuxing.as_list()), 5)
    self.assertEqual(Wuxing.as_list()[0], Wuxing.木)
    self.assertEqual(Wuxing.as_list()[1], Wuxing.火)
    self.assertEqual(Wuxing.as_list()[2], Wuxing.土)
    self.assertEqual(Wuxing.as_list()[3], Wuxing.金)
    self.assertEqual(Wuxing.as_list()[4], Wuxing.水)

  def test_from_str(self) -> None:
    self.assertIs(Wuxing.from_str('木'), Wuxing.木)
    self.assertIs(Wuxing.from_str('火'), Wuxing.火)
    self.assertIs(Wuxing.from_str('土'), Wuxing.土)
    self.assertIs(Wuxing.from_str('金'), Wuxing.金)
    self.assertIs(Wuxing.from_str('水'), Wuxing.水)

    with self.assertRaises(AssertionError):
      Wuxing.from_str('')
    with self.assertRaises(AssertionError):
      Wuxing.from_str('木木')
    with self.assertRaises(ValueError):
      Wuxing.from_str('甲')
    with self.assertRaises(ValueError):
      Wuxing.from_str('辰')

  def test_str(self) -> None:
    for wx in Wuxing:
      self.assertEqual(str(wx), wx.value)
      self.assertEqual(Wuxing.from_str(str(wx)), wx)

    self.assertEqual(''.join([str(wx) for wx in Wuxing]), '木火土金水')

  def test_generates_and_destructs(self) -> None:
    self.assertTrue(Wuxing.木.generates(Wuxing.火))
    self.assertTrue(Wuxing.火.destructs(Wuxing.金))

    wx_list: list[Wuxing] = Wuxing.as_list()
    for wx1, wx2 in product(wx_list, wx_list):
      wx1_index: int = wx_list.index(wx1)
      wx2_index: int = wx_list.index(wx2)
      
      if (wx1_index + 1) % 5 == wx2_index:
        self.assertTrue(wx1.generates(wx2))
        self.assertFalse(wx2.generates(wx1))
        self.assertFalse(wx1.destructs(wx2))
      else:
        self.assertFalse(wx1.generates(wx2))

      if (wx1_index + 2) % 5 == wx2_index:
        self.assertTrue(wx1.destructs(wx2))
        self.assertFalse(wx2.destructs(wx1))
        self.assertFalse(wx1.generates(wx2))
      else:
        self.assertFalse(wx1.destructs(wx2))


class TestYinyang(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Yinyang), 2)
    self.assertIs(Yinyang.阴, Yinyang.YIN)
    self.assertIs(Yinyang.阳, Yinyang.YANG)

    self.assertEqual(Yinyang.阴.value, '阴')
    self.assertNotEqual(Yinyang.阴, Yinyang.阳)
    self.assertNotEqual(Yinyang.阴.value, Yinyang.阳.value)

    self.assertEqual(len(Yinyang.as_list()), 2)
    self.assertEqual(Yinyang.as_list()[0], Yinyang.阳)
    self.assertEqual(Yinyang.as_list()[1], Yinyang.阴)

    self.assertIs(阴阳, Yinyang)

  def test_str(self) -> None:
    self.assertEqual(str(Yinyang.阴), '阴')
    self.assertEqual(str(Yinyang.阳), '阳')
    self.assertEqual(Yinyang.from_str('阴'), Yinyang.阴)
    self.assertEqual(Yinyang.from_str('阳'), Yinyang.阳)
    self.assertEqual(Yinyang('阴'), Yinyang.阴)
    self.assertEqual(Yinyang('阳'), Yinyang.阳)

    self.assertEqual(''.join([str(e) for e in Yinyang.as_list()]), '阳阴')

    self.assertEqual(Yinyang.from_str('阴'), Yinyang.阴)
    self.assertEqual(Yinyang.from_str('阳'), Yinyang.阳)

    with self.assertRaises(ValueError):
      Yinyang.from_str('甲')
    with self.assertRaises(ValueError):
      Yinyang.from_str('辰')

  def test_opposite(self) -> None:
    self.assertEqual(Yinyang.阴.opposite, Yinyang.阳)
    self.assertEqual(Yinyang.阳.opposite, Yinyang.阴)


class TestShishen(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Shishen), 10)
    self.assertEqual(len(Shishen.as_list()), 10)
    self.assertIs(十神, Shishen)
    self.assertEqual(Shishen('比肩').value, '比肩')
    self.assertEqual(Shishen('食神').value, '食神')
    self.assertNotEqual(Shishen('偏印').value, '食神')

  def test_str(self) -> None:
    with self.subTest('Two characters - fullname'):
      self.assertEqual(str(Shishen.比肩), '比肩')
      self.assertEqual(str(Shishen.劫财), '劫财')
      self.assertEqual(str(Shishen.食神), '食神')
      self.assertEqual(str(Shishen.伤官), '伤官')
      self.assertEqual(str(Shishen.正财), '正财')
      self.assertEqual(str(Shishen.偏财), '偏财')
      self.assertEqual(str(Shishen.正官), '正官')
      self.assertEqual(str(Shishen.七杀), '七杀')
      self.assertEqual(str(Shishen.正印), '正印')
      self.assertEqual(str(Shishen.偏印), '偏印')

      for s in Shishen:
        self.assertEqual(str(s), s.value)
        self.assertEqual(Shishen.from_str(str(s)), s)
        self.assertEqual(Shishen(str(s)), s)

      self.assertEqual(''.join([str(s) for s in Shishen.as_list()]), 
                      '比肩劫财食神伤官正财偏财正官七杀正印偏印')
      
    with self.subTest('One character - abbreviation'):
      self.assertEqual(len(Shishen.str_mapping_table()), 10)

      self.assertIs(Shishen.from_str('比'), Shishen.比肩)
      self.assertIs(Shishen.from_str('劫'), Shishen.劫财)
      self.assertIs(Shishen.from_str('食'), Shishen.食神)
      self.assertIs(Shishen.from_str('伤'), Shishen.伤官)
      self.assertIs(Shishen.from_str('财'), Shishen.正财)
      self.assertIs(Shishen.from_str('才'), Shishen.偏财)
      self.assertIs(Shishen.from_str('官'), Shishen.正官)
      self.assertIs(Shishen.from_str('杀'), Shishen.七杀)
      self.assertIs(Shishen.from_str('印'), Shishen.正印)
      self.assertIs(Shishen.from_str('枭'), Shishen.偏印)

      self.assertEqual(''.join([s.abbr for s in Shishen]), '比劫食伤财才官杀印枭')

      with self.assertRaises(AssertionError):
        Shishen.from_str('甲')
      with self.assertRaises(AssertionError):
        Shishen.from_str('辰')
      with self.assertRaises(AssertionError):
        Shishen.from_str('')
      with self.assertRaises(ValueError):
        Shishen.from_str('甲子')
      with self.assertRaises(ValueError):
        Shishen.from_str('比间')
      with self.assertRaises(ValueError):
        Shishen.from_str('枭神')
