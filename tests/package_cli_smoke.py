# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Exercise the installed launcher from a foreign cwd, with no development dependencies.'''

import hashlib
import importlib.metadata
import os
import re
import subprocess
import sys
import sysconfig

from pathlib import Path


def check(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def main() -> None:
  check(sys.flags.isolated == 1 and sys.dont_write_bytecode, 'CLI smoke requires -I -B')
  check(sys.prefix != sys.base_prefix, 'CLI consumer must be a virtual environment')
  prefix = Path(sys.prefix)
  launcher = prefix / ('Scripts/bazi.exe' if os.name == 'nt' else 'bin/bazi')
  check(launcher.is_file(), 'Installed launcher missing')
  dist = importlib.metadata.distribution('bazi')
  package = Path(str(dist.locate_file('bazi'))).resolve()
  before = {path.relative_to(package): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in package.rglob('*') if path.is_file()}
  cwd = Path.cwd() / f'{prefix.name}-cli-{int(not __debug__)}'
  cwd.mkdir()
  check(not cwd.is_relative_to(prefix), 'CLI cwd must be outside installation')

  # A startup witness runs in the real launcher process, not in a replacement python -c entry.
  witness = Path(sysconfig.get_paths()['purelib']) / 'sitecustomize.py'
  check(not witness.exists(), 'Unexpected consumer startup customization')
  with witness.open('x', encoding='utf-8') as stream:
    stream.write('import os\nif "BAZI_SMOKE_OPTIMIZED" in os.environ:\n'
      '  print("__bazi_optimized__=" + str(int(not __debug__)), flush=True)\n')
  env = {key: value for key, value in os.environ.items()
    if key not in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONOPTIMIZE')}
  env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', BAZI_SMOKE_OPTIMIZED=str(int(not __debug__)))
  if not __debug__:
    env['PYTHONOPTIMIZE'] = '1'

  def run(*args: str, error: str | None = None) -> str:
    result = subprocess.run([str(launcher), *args], cwd=cwd, env=env,
      capture_output=True, text=True, encoding='utf-8', timeout=45, check=False)
    marker, separator, output = result.stdout.partition('\n')
    check(bool(separator) and marker == '__bazi_optimized__=' + str(int(not __debug__)),
      'Real launcher did not confirm requested optimization')
    check(result.returncode == (0 if error is None else 2), f'CLI exit mismatch: {args}: {result.stderr}')
    if error is None:
      check(not result.stderr, f'CLI unexpected stderr: {args}: {result.stderr}')
    else:
      check(output == '' and error in result.stderr and 'usage: bazi ' in result.stderr,
        f'CLI rejected for wrong reason: {args}: {result.stderr}')
    return output

  try:
    help_text = run('--help')
    check(run() == help_text, 'Bare CLI differs from help')
    for task in ('chart', 'knowledge', 'match'):
      check(f'bazi {task}' in help_text and f'bazi {task}' in run(task, '--help'), 'CLI help lost a task')
    check('--output' in run('chart', '--help'), 'Chart help lost output option')
    check('--ganzhi-month' in run('match', '--help'), 'Match help lost month coordinate')
    for flags in ((), ('--transits',), ('--relationship',)):
      output = run('chart', '--seed', '236', *flags)
      check(output == run('chart', '--seed', '236', *flags) and output.startswith('random seed: 236\n'), 'Seed replay differs')
      check('日主' in output or '日元' in output, 'Seeded chart display missing')
      if flags == ('--transits',):
        check('大运' in output and '流年' in output and '\x1b[' in output, 'Demo lost full transit/color display')
      elif flags == ('--relationship',):
        check('夫妻宫：' in output and '六甲旬空依据：' in output and '起十年' in output, 'Relationship report incomplete')
    check(not tuple(cwd.iterdir()), 'Read-only CLI tasks wrote files')
    fixed = ('--birth-time', '2000-01-03 12:00', '--gender', '女', '--precision', '分')
    chart = run('chart', *fixed, '--knowledge', '--transits', '--relationship', '--output', 'chart.txt')
    chart_file = cwd / 'chart.txt'
    chart_bytes = chart_file.read_bytes()
    check(chart_file.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', chart) and b'\x1b[' not in chart_bytes,
      'Chart export differs from display')
    check('丁为阴火。' in run('knowledge', '丁'), 'Installed knowledge query missing')
    check('topic' in run('knowledge') or '知识' in run('knowledge'), 'Knowledge overview missing')
    run('knowledge', '--validate-knowledge')
    check(chart_file.read_bytes() == chart_bytes, 'Knowledge query overwrote chart')
    criterion = 'editorial.guansha_coexistence.v1'
    check(criterion in run('match'), 'Criterion listing missing')
    check('SATISFIED' in run('match', criterion, *fixed, '--observation-scope', 'natal'), 'Installed matching failed')
    check('也许' in run('match', criterion, *fixed, '--observation-scope', 'natal', '--knowledge'), 'Installed explicit reading missing')
    month = run('match', 'editorial.spouse_palace_xingchong.v1', *fixed,
      '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_month',
      '--ganzhi-year', '2024', '--ganzhi-month', '午', '--transit-kinds', 'liunian,liuyue')
    check('UNKNOWN' not in month and '2024' in month and '午' in month, 'Installed Chinese month query failed')
    local = run('chart', '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'female',
      '--precision', 'minute', '--longitude', '-157.4')
    check('2024-01-01T12:00:00+14:00' in local, 'Installed location input lost civil time')
    source = cwd / 'source.json'
    source.write_bytes((package / 'knowledge_data.json').read_bytes())
    run('knowledge', '--knowledge-source', str(source), '--validate-knowledge')
    run('chart', '--knowledge', '--knowledge-source', str(source), '--output', str(source), error='overwrite')
    check(source.read_bytes() == (package / 'knowledge_data.json').read_bytes(), 'Source overwrite guard truncated source')
    files = {path.relative_to(cwd): path.read_bytes() for path in cwd.rglob('*') if path.is_file()}
    for tokens, reason in (
      (('unknown-task',), 'invalid choice'),
      (('chart', '--unknown'), 'unrecognized arguments'),
      (('chart', '--birth-time', '2000-01-01 12:00'), '--gender'),
      (('knowledge', '--object', 'typo'), 'Unknown object'),
    ):
      run(*tokens, error=reason)
    check(files == {path.relative_to(cwd): path.read_bytes() for path in cwd.rglob('*') if path.is_file()},
      'Invalid installed command changed files')
  finally:
    witness.unlink()
  check(before == {path.relative_to(package): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in package.rglob('*') if path.is_file()}, 'CLI wrote into installed package')
  print(f'PASS real installed launcher: three tasks, seed/output/guard/negative controls, optimized={not __debug__}')


if __name__ == '__main__':
  main()
