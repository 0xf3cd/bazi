# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date, datetime
from typing import Protocol, runtime_checkable

from ..defines import Jieqi
from ..common import JieqiTime
from .calendar_defines import CalendarType, CalendarDate


@runtime_checkable
class CalendarUtilsProtocol(Protocol):
  '''
  The protocol that all CalendarUtils classes conform to.

  Implementations may differ only in the *precision* of `jieqi_moment`: a data source that
  publishes jieqi dates but not their moments can answer no better than midnight of that
  date (`hko_data_calendar_utils`), while one carrying the real moments answers to the second
  (`CelestialCalendarUtils`).  Everything else here is date-level and must agree, which is
  what makes conforming implementations substitutable for one another.

  Two methods ride on that precision and escape the "must agree" rule: `prev_jie`/`next_jie`
  name the jie bracketing a moment, so between midnight and the true moment of a jieqi day the
  two backends legitimately name different jie.  The divergence is moment-shaped, not noise
  (~1.6% of random moments, all landing on jieqi days), and it propagates: `BaziChart`'s da-yun
  start counts jie from birth, so a jieqi-day birth can shift it by a full da-yun step (~10
  years).  Date-level queries stay within the frozen parity whitelist instead (see
  `tests/calendar/celestial_parity_data.py`).
  '''
  @staticmethod
  def get_min_supported_date(date_type: CalendarType) -> CalendarDate: ...
  @staticmethod
  def get_max_supported_date(date_type: CalendarType) -> CalendarDate: ...
  @staticmethod
  def is_valid_solar_date(d: CalendarDate) -> bool: ...
  @staticmethod
  def is_valid_lunar_date(d: CalendarDate) -> bool: ...
  @staticmethod
  def is_valid_ganzhi_date(d: CalendarDate) -> bool: ...
  @staticmethod
  def is_valid(d: CalendarDate) -> bool: ...
  @staticmethod
  def days_counts_in_ganzhi_year(ganzhi_year: int) -> list[int]: ...
  @staticmethod
  def lunar_to_solar(lunar_date: CalendarDate) -> CalendarDate: ...
  @staticmethod
  def solar_to_lunar(solar_date: CalendarDate) -> CalendarDate: ...
  @staticmethod
  def ganzhi_to_solar(ganzhi_date: CalendarDate) -> CalendarDate: ...
  @staticmethod
  def solar_to_ganzhi(solar_date: CalendarDate) -> CalendarDate: ...
  @staticmethod
  def lunar_to_ganzhi(lunar_date: CalendarDate) -> CalendarDate: ...
  @staticmethod
  def ganzhi_to_lunar(ganzhi_date: CalendarDate) -> CalendarDate: ...
  @staticmethod
  def to_solar(d: date | CalendarDate) -> CalendarDate: ...
  @staticmethod
  def to_lunar(d: date | CalendarDate) -> CalendarDate: ...
  @staticmethod
  def to_ganzhi(d: date | CalendarDate) -> CalendarDate: ...
  @staticmethod
  def to_date(d: date | CalendarDate) -> date: ...
  @staticmethod
  def jieqi_date(solar_year: int, jieqi: Jieqi) -> date: ...
  @staticmethod
  def jieqi_moment(solar_year: int, jieqi: Jieqi) -> datetime: ...
  @staticmethod
  def prev_jie(dt: datetime) -> JieqiTime: ...
  @staticmethod
  def next_jie(dt: datetime) -> JieqiTime: ...
