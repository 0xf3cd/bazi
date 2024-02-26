# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import datetime

class Bazi:
  '''
  Bazi (八字) is not aware of the timezone. We don't care abot the timezone when creating a Bazi object.
  Timezone should be well-processed outside of this class.

  Attention: this class does not know anything about timezone. 
  '''
  def __init__(self, year: int, month: int, day: int, hour: int, minute: int) -> None:
    '''
    Input the birth time. We don't care about the timezone.
    The input time should be solar time.
    '''
    self._datetime = datetime(year, month, day, hour, minute)

  @property
  def datetime(self) -> datetime:
    return self._datetime

  @property
  def year(self) -> int:
    return self._datetime.year

  @property
  def month(self) -> int:
    return self.datetime.month

  @property
  def day(self) -> int:
    return self.datetime.day
  
  @property
  def hour(self) -> int:
    return self.datetime.hour
  
  @property
  def minute(self) -> int:
    return self.datetime.minute
  
  @property
  def 年柱(self) -> str:
    # return self._datetime.strftime('%Y年 %m月 %d日 %H时 %M分'
    return ''
  
八字 = Bazi
