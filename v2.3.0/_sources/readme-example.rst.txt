:orphan:

README 首例检查
===============

.. testsetup:: readme-first

   import os
   import tempfile
   _readme_cwd = os.getcwd()
   _readme_directory = tempfile.TemporaryDirectory()
   os.chdir(_readme_directory.name)

.. testcode:: readme-first

   import json
   from datetime import datetime
   from pathlib import Path
   
   from bazi.bazi import Bazi
   from bazi.bazi_chart import BaziChart
   from bazi.chart_text import basic_text
   
   bazi = Bazi.create(datetime(1990, 5, 17, 10, 30), 'female')
   chart = BaziChart(bazi)
   
   print('四柱', ' '.join(str(pillar) for pillar in bazi.pillars))
   print('日主', bazi.day_master)
   print('性别', chart.json['gender'])
   print('精度与后端', chart.json['precision'], chart.json['backend'])
   
   Path('chart.txt').write_text(basic_text(chart), encoding='utf-8')
   Path('chart.json').write_text(
     json.dumps(chart.json, ensure_ascii=False, indent=2) + '\n',
     encoding='utf-8',
   )
   print('已保存 chart.txt 和 chart.json')

.. testoutput:: readme-first

   四柱 庚午 辛巳 壬午 乙巳
   日主 壬
   性别 female
   精度与后端 day celestial
   已保存 chart.txt 和 chart.json

.. testcleanup:: readme-first

   os.chdir(_readme_cwd)
   _readme_directory.cleanup()
