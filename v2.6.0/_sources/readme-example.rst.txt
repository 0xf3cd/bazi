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

   from bazi.bazi import Bazi
   from bazi.bazi_chart import BaziChart
   
   chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
   print('四柱', ' '.join(map(str, chart.bazi.pillars)))
   print('日主', chart.bazi.day_master)
   print('年干十神', chart.shishen.year.tiangan)

.. testoutput:: readme-first

   四柱 庚午 辛巳 壬午 乙巳
   日主 壬
   年干十神 偏印

.. testcleanup:: readme-first

   os.chdir(_readme_cwd)
   _readme_directory.cleanup()
