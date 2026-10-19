:orphan:

README 首例检查
===============

.. testcode:: readme-first

   from datetime import datetime
   
   from bazi.bazi import Bazi
   from bazi.bazi_chart import BaziChart
   
   bazi = Bazi.create(datetime(1990, 5, 17, 10, 30), 'female')
   chart = BaziChart(bazi)
   
   print('四柱', ' '.join(str(pillar) for pillar in bazi.pillars))
   print('日主', bazi.day_master)
   print('性别', chart.json['gender'])
   print('精度与后端', chart.json['precision'], chart.json['backend'])

.. testoutput:: readme-first

   四柱 庚午 辛巳 壬午 乙巳
   日主 壬
   性别 female
   精度与后端 day celestial
