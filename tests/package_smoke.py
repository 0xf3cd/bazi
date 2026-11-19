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
EOT_READS: list[str] = []


def check(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def record_eot_reads(event: str, args: tuple[Any, ...]) -> None:
  if event == 'open':
    path, _, _ = args
    if isinstance(path, str) and path.replace('\\', '/').endswith('/equation_of_time.bin'):
      EOT_READS.append(event)


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
  check([(entry.group, entry.name, entry.value) for entry in dist.entry_points] == [
    ('console_scripts', 'bazi', 'bazi.cli:main'),
  ], 'Installed entrypoints mismatch')
  check(not dist.metadata.get_all('License-Expression', []) and not dist.metadata.get_all('License', []), 'Blanket license claim')
  check(not any('License ::' in value for value in dist.metadata.get_all('Classifier', [])), 'Blanket license classifier')
  check(set(dist.metadata.get_all('License-File', [])) == {'LICENSE', 'THIRD_PARTY_NOTICES.md'}, 'License file metadata mismatch')
  check({d.metadata['Name'].lower() for d in importlib.metadata.distributions()} == {'bazi', 'pip'}, 'Functional consumer contains development dependencies')
  spec = importlib.util.find_spec('bazi')
  if spec is None or spec.origin is None:
    raise RuntimeError('Package not found')
  package_root = Path(spec.origin).resolve().parent
  check(package_root.is_relative_to(prefix), 'Package origin outside consumer')
  check(not Path.cwd().is_relative_to(package_root), 'Consumer cwd is inside package')
  check(importlib.util.find_spec('bazi.__main__') is None, 'Unexpected parallel module CLI')
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

  sys.addaudithook(record_eot_reads)

  import bazi
  check(Path(bazi.__file__).resolve().parent == package_root, 'Root import source leakage')
  check('bazi.bazi_chart' not in sys.modules and 'bazi.calendar.utils' not in sys.modules, 'Root import eagerly loaded chart/data')
  check('bazi.knowledge' not in sys.modules, 'Root import eagerly loaded interpretation data')
  check('bazi.context_matching' not in sys.modules, 'Root import eagerly loaded context matcher')

  from bazi.bazi import Bazi, 八字
  from bazi.bazi_chart import BaziChart, 命盘
  from bazi.defines import 天干, 十神
  from bazi.school import BaziConfig
  from bazi.calendar.utils import to_lunar, to_date
  from bazi.calendar.solar_time import apparent_solar_datetime
  from bazi.transit_chart import TransitChart, 流年大运
  from bazi.transits import TransitKind
  from bazi.analyzer.relationship import RelationshipAnalyzer
  from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase, 知识库
  from bazi.context_matching import NatalObservation, evaluate_context

  check(not EOT_READS, 'Imports eagerly read the EOT table')
  for longitude, error_type in ((True, TypeError), (float('nan'), ValueError), (180.01, ValueError)):
    try:
      Bazi.create(datetime(2000, 1, 1, tzinfo=UTC), 'male',
                  BaziConfig.from_values(precision='minute'), longitude=longitude)
    except error_type:
      pass
    else:
      raise RuntimeError('Longitude validation failed')
  check(not EOT_READS, 'Longitude validation read the EOT table')
  instant = datetime(2000, 11, 3, 0, 50, tzinfo=UTC)
  apparent = apparent_solar_datetime(instant, 0.0)
  check(len(EOT_READS) == 1, 'First apparent-solar conversion did not read exactly one EOT table')
  location_chart = BaziChart(Bazi.create(
    instant, 'male', BaziConfig.from_values(precision='minute'), longitude=0.0,
  ))
  facts = location_chart.bazi.location_time
  check(facts is not None and facts.apparent_time == apparent, 'Installed chart did not use apparent-solar conversion')
  check(len(EOT_READS) == 1, 'Repeated apparent-solar conversion reread the EOT table')
  print('PASS installed lazy EOT resource and location chart')

  chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
  check(len(chart.bazi.pillars) == 4, 'Installed chart input mismatch')
  transits = TransitChart(chart).at_year(2024)
  if transits is None:
    raise RuntimeError('Missing transits')
  analysis = RelationshipAnalyzer(chart)
  check(bool(analysis.at_birth.shensha), 'Missing natal analysis')
  check(bool(analysis.transits.shensha(transits.select(TransitKind.LIUNIAN))), 'Missing transit analysis')
  check(to_date(to_lunar(date(2023, 3, 22))) == date(2023, 3, 22), 'Installed lunar conversion failed')
  print('PASS installed calendar/chart/transits/analysis')

  check(八字 is Bazi and 命盘 is BaziChart and 流年大运 is TransitChart and 知识库 is KnowledgeBase,
    'Installed Chinese names do not refer to the original types')
  盘 = 命盘(八字.create('1990-05-17 10:30', '女'))
  check(盘.八字 is 盘.bazi and 盘.十神 is 盘.shishen, 'Chinese chart properties copied state')
  check(tuple(map(str, 盘.八字.四柱)) == ('庚午', '辛巳', '壬午', '乙巳'), 'Chinese pillar reading failed')
  check(盘.八字.日主 is 天干.壬 and 盘.十神.年.天干 is 十神.偏印, 'Chinese chart reading failed')
  try:
    盘.八字 = chart.bazi # type: ignore[misc]
  except AttributeError:
    pass
  else:
    raise RuntimeError('Installed Chinese chart property is writable')
  岁运 = 流年大运(盘).at_year(2024)
  if 岁运 is None:
    raise RuntimeError('Chinese transit query returned no result')
  check(str(岁运.大运) == '丁丑' and str(岁运.流年) == '甲辰', 'Chinese transit reading failed')
  定义, = 知识库.load().query(天干.丁, topic='定义')
  check(定义.text == '丁为阴火。', 'Chinese knowledge query failed')
  print('PASS installed Chinese chart/transits/knowledge reading')

  check(DEFAULT_SOURCE_PATH == package_root / 'knowledge_data.json', 'Installed default source path mismatch')
  knowledge = KnowledgeBase.load()
  entries = knowledge.query('丁')
  check(bool(entries) and entries[0].text in knowledge.render_subject('丁'), 'Installed knowledge query/display failed')
  try:
    knowledge.query('typo')
  except ValueError:
    pass
  else:
    raise RuntimeError('Installed knowledge input rejection failed')
  chart = BaziChart(Bazi.create(datetime(2000, 1, 3, 12), 'female'))
  matched = evaluate_context(chart, criterion_id='editorial.guansha_coexistence.v1', observation=NatalObservation())
  check(matched.criterion.status == 'SATISFIED' and bool(matched.reference_ids), 'Installed context evaluation failed')
  check(matched.bazi == chart.bazi and '参考条目：' in matched.render(), 'Installed context input/display failed')
  print('PASS installed knowledge resource and context evaluation')

  from bazi.cli import main as cli_main
  check(next(iter(dist.entry_points)).load() is cli_main, 'Installed entrypoint resolves to another function')
  try:
    cli_main([1]) # type: ignore[list-item] # Deliberately invalid public CLI input.
  except TypeError as error:
    check(str(error).startswith('Expected '), 'CLI type rejection failed for another reason')
  else:
    raise RuntimeError('Installed CLI argv validation failed')
  for name, module in tuple(sys.modules.items()):
    if name == 'bazi' or name.startswith('bazi.'):
      origin = getattr(module, '__file__', None)
      check(origin is not None and Path(origin).resolve().is_relative_to(package_root), f'Submodule source leakage: {name}')
  check(not {'celestial_calendar', 'requests'} & sys.modules.keys(), 'Optional offline dependency imported')
  check(WRITE_ATTEMPTS == ['open'], 'Runtime attempted a write after the positive control')
  print(f'PASS installed smoke: {len(roster)} files, optimized={not __debug__}, origin={package_root}')


if __name__ == '__main__':
  main()
