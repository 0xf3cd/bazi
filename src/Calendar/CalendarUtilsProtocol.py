# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date
from typing import Union, Protocol
from .CalendarDefines import CalendarType, CalendarDate

class CalendarUtilsProtocol(Protocol):
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
  def to_solar(d: Union[date, CalendarDate]) -> CalendarDate: ...
  @staticmethod
  def to_lunar(d: Union[date, CalendarDate]) -> CalendarDate: ...
  @staticmethod
  def to_ganzhi(d: Union[date, CalendarDate]) -> CalendarDate: ...
  @staticmethod
  def to_date(d: Union[date, CalendarDate]) -> date: ...
