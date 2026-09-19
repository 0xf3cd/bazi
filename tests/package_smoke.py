# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Copied into a foreign cwd and run with an installed wheel, under -I -B and -O.'''

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import sys

from datetime import date, datetime, UTC
from pathlib import Path
from typing import Any


WRITE_ATTEMPTS: list[str] = []


def check(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def deny_writes(event: str, args: tuple[Any, ...]) -> None:
  if event == 'open':
    _, mode, flags = args
    if (mode and any(char in mode for char in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
      WRITE_ATTEMPTS.append(event)
      raise PermissionError('Runtime write blocked')
  if event in ('os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.chmod', 'os.link', 'os.symlink', 'os.truncate', 'os.utime'):
    WRITE_ATTEMPTS.append(event)
    raise PermissionError('Runtime write blocked')


def main() -> None:
  expected = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
  check(sys.flags.isolated == 1 and sys.dont_write_bytecode, 'Smoke requires -I -B')
  check(not os.environ.get('PYTHONPATH'), 'PYTHONPATH must be empty')
  check(sys.prefix != sys.base_prefix, 'Consumer must be a virtual environment')
  prefix = Path(sys.prefix).resolve()
  dist = importlib.metadata.distribution('bazi')
  check(dist.version == expected['version'], 'Installed version mismatch')
  check(dist.metadata['Name'] == 'bazi', 'Installed name mismatch')
  check(dist.metadata['Requires-Python'] == '>=3.11', 'Python requirement mismatch')
  check(not dist.requires, 'Unexpected runtime dependencies')
  check(not dist.entry_points, 'Unexpected installed entrypoints')
  check(not dist.metadata.get('License-Expression') and not dist.metadata.get('License'), 'Blanket license claim')
  check(not any('License ::' in value for value in dist.metadata.get_all('Classifier', [])), 'Blanket license classifier')
  check(set(dist.metadata.get_all('License-File', [])) == {'LICENSE', 'THIRD_PARTY_NOTICES.md'}, 'License file metadata mismatch')
  check({d.metadata['Name'].lower() for d in importlib.metadata.distributions()} == {'bazi', 'pip'}, 'Functional consumer contains development dependencies')
  spec = importlib.util.find_spec('bazi')
  check(spec is not None and spec.origin is not None, 'Package not found')
  if spec is None or spec.origin is None:
    raise RuntimeError('Package not found')
  package_root = Path(spec.origin).resolve().parent
  check(package_root.is_relative_to(prefix), 'Package origin outside consumer')
  check(not Path.cwd().is_relative_to(package_root), 'Consumer cwd is inside package')
  check(importlib.util.find_spec('src') is None, 'Unexpected src compatibility package')
  roster = {path.relative_to(package_root.parent).as_posix() for path in package_root.rglob('*') if path.is_file()}
  check(roster == set(expected['package']), 'Installed package file roster mismatch')
  for name, digest in expected['package'].items():
    check(hashlib.sha256((package_root.parent / name).read_bytes()).hexdigest() == digest, f'Installed bytes differ: {name}')
  for name, digest in expected['licenses'].items():
    matches = [file for file in dist.files or () if str(file).endswith('/licenses/' + name)]
    check(len(matches) == 1, 'Installed license missing')
    check(hashlib.sha256(matches[0].read_binary()).hexdigest() == digest, 'Installed license bytes differ')

  # Audit hooks enforce read-only use even under root and on Windows.
  sys.addaudithook(deny_writes)
  try:
    (package_root / 'write-control').write_bytes(b'must not be written')
  except PermissionError as error:
    check(str(error) == 'Runtime write blocked', 'Write control failed for the wrong reason')
  else:
    raise RuntimeError('Write guard failed its positive control')
  print('PASS executable runtime write-attempt control')

  import bazi
  check('bazi.bazi_chart' not in sys.modules and 'bazi.calendar.hko_data_utils' not in sys.modules, 'Root import eagerly loaded chart/data')
  from bazi.bazi import Bazi
  from bazi.bazi_chart import BaziChart
  from bazi.school import BaziConfig
  from bazi.calendar import CalendarBackend, calendar_utils_of
  from bazi.defines import Jieqi, Tiangan, Shishen
  from bazi.transit_chart import TransitChart
  from bazi.transits import TransitKind
  from bazi.analyzer.relationship import RelationshipAnalyzer
  from bazi.interpreter import Interpreter

  check(Path(bazi.__file__).resolve().is_relative_to(prefix), 'Root import source leakage')
  for backend in CalendarBackend:
    utils = calendar_utils_of(backend)
    check(utils.to_date(utils.to_lunar(date(2024, 2, 10))) == date(2024, 2, 10), 'Calendar roundtrip mismatch')
    check(utils.jieqi_date(2024, Jieqi.LICHUN) == date(2024, 2, 4), 'Calendar absolute date mismatch')
    chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male', BaziConfig.from_values(backend=backend, precision='day')))
    check(BaziChart.from_json(json.loads(json.dumps(chart.json))).json == chart.json, 'JSON restoration mismatch')
    transits = TransitChart(chart).at_year(2024)
    check(transits is not None, 'Missing transits')
    if transits is None:
      raise RuntimeError('Missing transits')
    analysis = RelationshipAnalyzer(chart)
    check('taohua' in analysis.at_birth.shensha, 'Missing natal analysis')
    check('taohua' in analysis.transits.shensha(transits.select(TransitKind.LIUNIAN)), 'Missing transit analysis')
    try:
      Bazi.create(datetime(2000, 1, 1, tzinfo=UTC), 'male')
    except ValueError:
      pass
    else:
      raise RuntimeError('Timezone rejection failed')
    try:
      BaziChart.from_json({**chart.json, 'extra': 'invalid'})
    except ValueError:
      pass
    else:
      raise RuntimeError('JSON input rejection failed')
    print(f'PASS backend={backend.value} JSON/transits/analysis/input rejection')
  for value in Tiangan:
    check(bool(Interpreter.interpret_tiangan(value)['general']), 'Missing Tiangan description')
  for shishen in Shishen:
    check(bool(Interpreter.interpret_shishen(shishen)['general']), 'Missing Shishen description')
  try:
    calendar_utils_of(42)  # type: ignore[arg-type] # Deliberately invalid public input.
  except TypeError:
    pass
  else:
    raise RuntimeError('Type rejection failed')
  for name, module in tuple(sys.modules.items()):
    if name == 'bazi' or name.startswith('bazi.'):
      origin = getattr(module, '__file__', None)
      check(origin is not None and Path(origin).resolve().is_relative_to(package_root), f'Submodule source leakage: {name}')
  check(not {'celestial_calendar', 'requests', 'bazi.calendar.celestial_data.generator', 'bazi.calendar.hko_data.encoder'} & sys.modules.keys(), 'Optional offline module imported')
  check(WRITE_ATTEMPTS == ['open'], 'Runtime attempted a write after the positive control')
  print(f'PASS installed smoke: {len(roster)} files, optimized={not __debug__}, origin={package_root}')


if __name__ == '__main__':
  main()
