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

   from bazi.bazi import 八字
   from bazi.bazi_chart import 命盘
   
   盘 = 命盘(八字.create('1990-05-17 10:30', '女'))
   print('四柱', ' '.join(map(str, 盘.八字.四柱)))
   print('日主', 盘.八字.日主)
   print('年干十神', 盘.十神.年.天干)

.. testoutput:: readme-first

   四柱 庚午 辛巳 壬午 乙巳
   日主 壬
   年干十神 偏印

.. testcleanup:: readme-first

   os.chdir(_readme_cwd)
   _readme_directory.cleanup()
