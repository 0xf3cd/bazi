# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import pytest

from bazi.bazi import Bazi, 八字
from bazi.bazi_chart import BaziChart, 命盘
from bazi.defines import 天干, 十神, 五行
from bazi.knowledge import KnowledgeBase, 知识库
from bazi.transit_chart import TransitChart, 流年大运
from bazi.transits import TransitKind


def test_chart_reading() -> None:
  assert 八字 is Bazi and 命盘 is BaziChart
  盘 = 命盘(八字.create('1990-05-17 10:30', '女'))
  assert 盘.八字 is 盘.bazi
  assert tuple(map(str, 盘.八字.四柱)) == ('庚午', '辛巳', '壬午', '乙巳')
  assert 盘.八字.四柱 == 盘.bazi.pillars
  assert 盘.八字.日主 is 天干.壬
  assert 盘.十神 is 盘.shishen
  assert (盘.十神.年.天干, 盘.十神.月.天干, 盘.十神.日.天干, 盘.十神.时.天干) == (
    十神.偏印, 十神.正印, None, 十神.伤官,
  )
  assert (盘.十神.年.地支, 盘.十神.月.地支, 盘.十神.日.地支, 盘.十神.时.地支) == (
    十神.正财, 十神.偏财, 十神.正财, 十神.偏财,
  )
  assert '十神' not in vars(盘)
  for value, names in (
    (盘, ('八字', '十神')), (盘.八字, ('四柱', '日主')),
    (盘.十神, ('年', '月', '日', '时')), (盘.十神.年, ('天干', '地支')),
  ):
    for name in names:
      with pytest.raises(AttributeError):
        setattr(value, name, None)


def test_year_reading_and_absence() -> None:
  assert 流年大运 is TransitChart
  盘 = 命盘(八字.create('1990-05-17 10:30', '女'))
  查询 = 流年大运(盘)
  assert 查询.at_year(1989) is None
  岁运 = 查询.at_year(2024)
  assert 岁运 is not None
  assert str(岁运.大运) == '丁丑' and str(岁运.流年) == '甲辰'
  assert 岁运.大运 is 岁运.dayun and 岁运.流年 is 岁运.liunian
  assert 岁运.select(TransitKind.LIUNIAN).大运 is None
  assert 岁运.select(TransitKind.DAYUN).流年 is None
  for name in ('大运', '流年'):
    with pytest.raises(AttributeError):
      setattr(岁运, name, None)


def test_domain_knowledge_reading() -> None:
  assert 知识库 is KnowledgeBase
  知识 = 知识库.load()
  for 对象 in (天干.丁, 十神.正官, 五行.木):
    条目 = 知识.query(对象)
    assert 条目 and 条目 == 知识.query(str(对象))
    assert all(知识.entry(一条.claim_id) is 一条 for 一条 in 条目)
  定义, = 知识.query(天干.丁, topic='定义')
  assert 定义.text == '丁为阴火。'
  assert 知识.sources[定义.sources[0]].work == '《刻京台增补渊海子平大全》'
