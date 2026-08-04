# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi_utils.py

import random
import itertools
from datetime import date, datetime, timedelta

import pytest

from src.defines import Ganzhi, Tiangan, Dizhi, Wuxing, Yinyang, Shishen, ShierZhangsheng
from src.data_types import TraitTuple, HiddenTianganDict
from src.utils import bazi_utils


def test_ganzhi_of_day_basic() -> None:
  # Basic
  d: date = date(2024, 3, 1)
  assert bazi_utils.ganzhi_of_day(d) == bazi_utils.ganzhi_of_day(d)

  dt: datetime = datetime(2024, 3, 1, 15, 34, 6)
  assert bazi_utils.ganzhi_of_day(d) == bazi_utils.ganzhi_of_day(dt) # `bazi_utils.ganzhi_of_day` also takes `datetime` objects.

  # Correctness
  d = date(2024, 3, 1)
  assert bazi_utils.ganzhi_of_day(d) == Ganzhi.from_str('甲子')
  assert bazi_utils.ganzhi_of_day(d + timedelta(days=1)) == Ganzhi.from_str('乙丑')
  assert bazi_utils.ganzhi_of_day(d - timedelta(days=1)) == Ganzhi.from_str('癸亥')

  assert bazi_utils.ganzhi_of_day(date(1914, 2, 14)) == Ganzhi.from_str('辛未')
  assert bazi_utils.ganzhi_of_day(date(1933, 11, 1)) == Ganzhi.from_str('辛未')
  assert bazi_utils.ganzhi_of_day(date(1958, 6, 29)) == Ganzhi.from_str('丁丑')
  assert bazi_utils.ganzhi_of_day(date(1964, 1, 19)) == Ganzhi.from_str('丁卯')
  assert bazi_utils.ganzhi_of_day(date(1984, 5, 31)) == Ganzhi.from_str('乙丑')
  assert bazi_utils.ganzhi_of_day(date(1997, 1, 30)) == Ganzhi.from_str('壬申')
  assert bazi_utils.ganzhi_of_day(date(2003, 7, 12)) == Ganzhi.from_str('丙戌')

  for offset in range(-2000, 2000):
    d = date(2024, 3, 1) + timedelta(days=offset)
    assert bazi_utils.ganzhi_of_day(d) == Ganzhi.list_sexagenary_cycle()[offset % 60]


def test_ganzhi_of_day_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.ganzhi_of_day('2024-03-01') # type: ignore


def test_ganzhi_of_year() -> None:
  with pytest.raises(TypeError):
    bazi_utils.ganzhi_of_year('2024') # type: ignore
  with pytest.raises(TypeError):
    bazi_utils.ganzhi_of_year((2024,)) # type: ignore

  assert bazi_utils.ganzhi_of_year(1836) == Ganzhi.from_str('丙申')
  assert bazi_utils.ganzhi_of_year(1930) == Ganzhi.from_str('庚午')
  assert bazi_utils.ganzhi_of_year(1902) == Ganzhi.from_str('壬寅')
  assert bazi_utils.ganzhi_of_year(1984) == Ganzhi.from_str('甲子')
  assert bazi_utils.ganzhi_of_year(2024) == Ganzhi.from_str('甲辰')
  assert bazi_utils.ganzhi_of_year(2075) == Ganzhi.from_str('乙未')
  assert bazi_utils.ganzhi_of_year(2123) == Ganzhi.from_str('癸未')

  for _ in range(20):
    random_ganzhi_year: int = random.randint(1000, 9999)
    another_random_ganzhi_year: int = random.randint(-20, 20) * 60 + random_ganzhi_year
    assert (bazi_utils.ganzhi_of_year(another_random_ganzhi_year) ==
            bazi_utils.ganzhi_of_year(random_ganzhi_year))


def test_month_tiangan() -> None:
  # 五虎遁口诀(年上起月):甲己之年丙作首,乙庚之年戊为头,丙辛之年寻庚起,丁壬壬位顺行流,戊癸之年甲寅求。
  # 下表为口诀的手工转录（oracle 独立于此仓的任何表）：每个年干一行，12 个字依次是寅月到丑月的月干。
  wuhudun: dict[Tiangan, str] = {
    Tiangan.甲 : '丙丁戊己庚辛壬癸甲乙丙丁', # 甲己之年丙作首(丙寅起)
    Tiangan.己 : '丙丁戊己庚辛壬癸甲乙丙丁',
    Tiangan.乙 : '戊己庚辛壬癸甲乙丙丁戊己', # 乙庚之年戊为头(戊寅起)
    Tiangan.庚 : '戊己庚辛壬癸甲乙丙丁戊己',
    Tiangan.丙 : '庚辛壬癸甲乙丙丁戊己庚辛', # 丙辛之年寻庚起(庚寅起)
    Tiangan.辛 : '庚辛壬癸甲乙丙丁戊己庚辛',
    Tiangan.丁 : '壬癸甲乙丙丁戊己庚辛壬癸', # 丁壬壬位顺行流(壬寅起)
    Tiangan.壬 : '壬癸甲乙丙丁戊己庚辛壬癸',
    Tiangan.戊 : '甲乙丙丁戊己庚辛壬癸甲乙', # 戊癸之年甲寅求(甲寅起)
    Tiangan.癸 : '甲乙丙丁戊己庚辛壬癸甲乙',
  }

  for year_tg, month_row in wuhudun.items():
    assert len(month_row) == 12
    for idx, expected_tg in enumerate(month_row):
      month_dz: Dizhi = Dizhi.from_index((idx + 2) % 12) # First month is "寅".
      assert bazi_utils.month_tiangan(year_tg, month_dz) == Tiangan(expected_tg)


def test_month_tiangan_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.month_tiangan('甲', Dizhi.寅) # type: ignore
  with pytest.raises(TypeError):
    bazi_utils.month_tiangan(Tiangan.甲, '寅') # type: ignore


def test_hour_tiangan() -> None:
  # 五鼠遁口诀(日上起时):甲己还加甲,乙庚丙作初,丙辛从戊起,丁壬庚子居,戊癸壬子求。
  # 下表为口诀的手工转录（oracle 独立于此仓的任何表）：每个日干一行，12 个字依次是子时到亥时的时干。
  wushudun: dict[Tiangan, str] = {
    Tiangan.甲 : '甲乙丙丁戊己庚辛壬癸甲乙', # 甲己还加甲(甲子起)
    Tiangan.己 : '甲乙丙丁戊己庚辛壬癸甲乙',
    Tiangan.乙 : '丙丁戊己庚辛壬癸甲乙丙丁', # 乙庚丙作初(丙子起)
    Tiangan.庚 : '丙丁戊己庚辛壬癸甲乙丙丁',
    Tiangan.丙 : '戊己庚辛壬癸甲乙丙丁戊己', # 丙辛从戊起(戊子起)
    Tiangan.辛 : '戊己庚辛壬癸甲乙丙丁戊己',
    Tiangan.丁 : '庚辛壬癸甲乙丙丁戊己庚辛', # 丁壬庚子居(庚子起)
    Tiangan.壬 : '庚辛壬癸甲乙丙丁戊己庚辛',
    Tiangan.戊 : '壬癸甲乙丙丁戊己庚辛壬癸', # 戊癸壬子求(壬子起)
    Tiangan.癸 : '壬癸甲乙丙丁戊己庚辛壬癸',
  }

  for day_tg, hour_row in wushudun.items():
    assert len(hour_row) == 12
    for idx, expected_tg in enumerate(hour_row):
      hour_dz: Dizhi = Dizhi.from_index(idx) # First hour is "子".
      assert bazi_utils.hour_tiangan(day_tg, hour_dz) == Tiangan(expected_tg)


def test_hour_tiangan_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.hour_tiangan('甲', Dizhi.寅) # type: ignore
  with pytest.raises(TypeError):
    bazi_utils.hour_tiangan(Tiangan.甲, '寅') # type: ignore


def test_tiangan_traits() -> None:
  for idx, tg in enumerate(Tiangan):
    expected_wuxing: Wuxing = Wuxing.as_list()[idx // 2]
    expected_yinyang: Yinyang = Yinyang.as_list()[idx % 2]
    assert bazi_utils.tiangan_traits(tg) == TraitTuple(expected_wuxing, expected_yinyang)
    assert str(bazi_utils.tiangan_traits(tg)) == str(expected_yinyang) + str(expected_wuxing)


def test_tiangan_traits_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.tiangan_traits('甲') # type: ignore


def test_dizhi_traits() -> None:
  assert bazi_utils.dizhi_traits(Dizhi('子')) == TraitTuple(Wuxing('水'), Yinyang('阳'))
  assert bazi_utils.dizhi_traits(Dizhi('辰')) == TraitTuple(Wuxing('土'), Yinyang('阳'))
  assert bazi_utils.dizhi_traits(Dizhi('巳')) == TraitTuple(Wuxing('火'), Yinyang('阴'))
  assert bazi_utils.dizhi_traits(Dizhi('丑')) == TraitTuple(Wuxing('土'), Yinyang('阴'))

  for idx, dz in enumerate(Dizhi):
    expected_wuxing: Wuxing
    month_idx: int = (idx - 2) % 12
    if month_idx % 3 == 2:
      expected_wuxing = Wuxing.土
    elif month_idx < 3:
      expected_wuxing = Wuxing.木
    elif month_idx < 6:
      expected_wuxing = Wuxing.火
    elif month_idx < 9:
      expected_wuxing = Wuxing.金
    else:
      expected_wuxing = Wuxing.水

    expected_yinyang: Yinyang = Yinyang.as_list()[idx % 2]
    assert bazi_utils.dizhi_traits(dz) == TraitTuple(expected_wuxing, expected_yinyang)


def test_dizhi_traits_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.dizhi_traits('子') # type: ignore


def test_traits_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.traits('甲') # type: ignore


def test_hidden_tiangans() -> None:
  for dz in Dizhi:
    percentages: HiddenTianganDict = bazi_utils.hidden_tiangans(dz)
    assert len(percentages) >= 1
    assert len(percentages) <= 3
    assert sum(percentages.values()) == 100
    for tg in percentages:
      assert tg in Tiangan


def test_hidden_tiangans_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.hidden_tiangans('子') # type: ignore


def test_shishen() -> None:
  assert bazi_utils.shishen(Tiangan.甲, Tiangan.甲) == Shishen.比肩
  assert bazi_utils.shishen(Tiangan.甲, Tiangan.乙) == Shishen.劫财
  assert bazi_utils.shishen(Tiangan.甲, Dizhi.寅) == Shishen.比肩
  assert bazi_utils.shishen(Tiangan.甲, Dizhi.卯) == Shishen.劫财

  assert bazi_utils.shishen(Tiangan.甲, Tiangan.丙) == Shishen.食神
  assert bazi_utils.shishen(Tiangan.甲, Dizhi.午) == Shishen.伤官

  assert bazi_utils.shishen(Tiangan.甲, Tiangan.戊) == Shishen.偏财
  assert bazi_utils.shishen(Tiangan.甲, Dizhi.未) == Shishen.正财

  assert bazi_utils.shishen(Tiangan.甲, Tiangan.辛) == Shishen.正官
  assert bazi_utils.shishen(Tiangan.甲, Dizhi.申) == Shishen.七杀

  assert bazi_utils.shishen(Tiangan.甲, Tiangan.壬) == Shishen.偏印
  assert bazi_utils.shishen(Tiangan.甲, Dizhi.子) == Shishen.正印


def test_shishen_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.shishen('甲', Tiangan.甲) # type: ignore
  with pytest.raises(TypeError):
    bazi_utils.shishen(Tiangan.甲, '寅') # type: ignore


def test_nayin_str() -> None:
  assert bazi_utils.nayin_str(Ganzhi.from_str('甲子')) == '海中金'
  assert bazi_utils.nayin_str(Ganzhi.from_str('乙丑')) == '海中金'
  assert bazi_utils.nayin_str(Ganzhi.from_str('丙寅')) == '炉中火'

  assert bazi_utils.nayin_str(Ganzhi.from_str('癸卯')) == '金箔金'
  assert bazi_utils.nayin_str(Ganzhi.from_str('甲辰')) == '覆灯火'
  assert bazi_utils.nayin_str(Ganzhi.from_str('乙巳')) == '覆灯火'
  assert bazi_utils.nayin_str(Ganzhi.from_str('丙午')) == '天河水'

  assert bazi_utils.nayin_str(Ganzhi.from_str('辛酉')) == '石榴木'
  assert bazi_utils.nayin_str(Ganzhi.from_str('壬戌')) == '大海水'
  assert bazi_utils.nayin_str(Ganzhi.from_str('癸亥')) == '大海水'

  cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
  for tg in Tiangan:
    for dz in Dizhi:
      gz: Ganzhi = Ganzhi(tg, dz)
      if gz in cycle:
        assert len(bazi_utils.nayin_str(gz)) == 3
      else:
        with pytest.raises(AssertionError):
          bazi_utils.nayin_str(gz) # Ganzhis not in the sexagenary cycle don't have nayin.


def test_nayin_str_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.nayin_str('甲子') # type: ignore


def test_shier_zhangsheng() -> None:
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('甲子')) == ShierZhangsheng.沐浴
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('甲亥')) == ShierZhangsheng.长生
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('甲午')) == ShierZhangsheng.死

  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('乙亥')) == ShierZhangsheng.死
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('乙丑')) == ShierZhangsheng.衰

  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('丙午')) == ShierZhangsheng.帝旺
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('丙未')) == ShierZhangsheng.衰

  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('丁未')) == ShierZhangsheng.冠带
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('丁戌')) == ShierZhangsheng.养

  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('戊戌')) == ShierZhangsheng.墓
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('戊亥')) == ShierZhangsheng.绝

  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('己亥')) == ShierZhangsheng.胎
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('庚辰')) == ShierZhangsheng.养
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('辛酉')) == ShierZhangsheng.临官
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('壬申')) == ShierZhangsheng.长生
  assert bazi_utils.shier_zhangsheng(*Ganzhi.from_str('癸卯')) == ShierZhangsheng.长生

  for dz in Dizhi:
    assert (bazi_utils.shier_zhangsheng(*Ganzhi.from_strs('丙', str(dz))) ==
            bazi_utils.shier_zhangsheng(*Ganzhi.from_strs('戊', str(dz))))
    assert (bazi_utils.shier_zhangsheng(*Ganzhi.from_strs('丁', str(dz))) ==
            bazi_utils.shier_zhangsheng(*Ganzhi.from_strs('己', str(dz))))


def test_shier_zhangsheng_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.shier_zhangsheng('甲', Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    bazi_utils.shier_zhangsheng(Tiangan.甲, '子') # type: ignore


def test_from_shier_zhangsheng() -> None:
  assert bazi_utils.from_shier_zhangsheng(Tiangan('甲'), ShierZhangsheng.沐浴) == Dizhi('子')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('甲'), ShierZhangsheng.长生) == Dizhi('亥')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('甲'), ShierZhangsheng.死) == Dizhi('午')

  assert bazi_utils.from_shier_zhangsheng(Tiangan('乙'), ShierZhangsheng.死) == Dizhi('亥')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('乙'), ShierZhangsheng.衰) == Dizhi('丑')

  assert bazi_utils.from_shier_zhangsheng(Tiangan('丙'), ShierZhangsheng.帝旺) == Dizhi('午')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('丙'), ShierZhangsheng.衰) == Dizhi('未')

  assert bazi_utils.from_shier_zhangsheng(Tiangan('丁'), ShierZhangsheng.冠带) == Dizhi('未')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('丁'), ShierZhangsheng.养) == Dizhi('戌')

  assert bazi_utils.from_shier_zhangsheng(Tiangan('戊'), ShierZhangsheng.墓) == Dizhi('戌')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('戊'), ShierZhangsheng.绝) == Dizhi('亥')

  assert bazi_utils.from_shier_zhangsheng(Tiangan('己'), ShierZhangsheng.胎) == Dizhi('亥')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('庚'), ShierZhangsheng.养) == Dizhi('辰')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('辛'), ShierZhangsheng.临官) == Dizhi('酉')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('壬'), ShierZhangsheng.长生) == Dizhi('申')
  assert bazi_utils.from_shier_zhangsheng(Tiangan('癸'), ShierZhangsheng.长生) == Dizhi('卯')

  for place in ShierZhangsheng:
    assert (bazi_utils.from_shier_zhangsheng(Tiangan('丙'), place) ==
            bazi_utils.from_shier_zhangsheng(Tiangan('戊'), place))
    assert (bazi_utils.from_shier_zhangsheng(Tiangan('丁'), place) ==
            bazi_utils.from_shier_zhangsheng(Tiangan('己'), place))


def test_from_shier_zhangsheng_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.from_shier_zhangsheng('甲', ShierZhangsheng.沐浴) # type: ignore
  with pytest.raises(TypeError):
    bazi_utils.from_shier_zhangsheng(Tiangan.甲, '沐浴') # type: ignore


def test_shier_zhangsheng_consistency() -> None:
  for tg, dz in itertools.product(Tiangan, Dizhi):
    zs: ShierZhangsheng = bazi_utils.shier_zhangsheng(tg, dz)
    assert bazi_utils.from_shier_zhangsheng(tg, zs) == dz
  for tg, zs in itertools.product(Tiangan, ShierZhangsheng):
    dz: Dizhi = bazi_utils.from_shier_zhangsheng(tg, zs) # type: ignore
    assert bazi_utils.shier_zhangsheng(tg, dz) == zs


def test_lu() -> None:
  for tg in Tiangan:
    assert bazi_utils.lu(tg) == bazi_utils.from_shier_zhangsheng(tg, ShierZhangsheng('临官'))


def test_lu_negative() -> None:
  with pytest.raises(TypeError):
    bazi_utils.lu('甲') # type: ignore
