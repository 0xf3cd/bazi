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
    for task in ('demo', 'relationship', 'chart', 'knowledge', 'match'):
      check(f'bazi {task}' in help_text and f'bazi {task}' in run(task, '--help'), 'CLI help lost a task')
    for task in ('demo', 'relationship', 'chart'):
      output = run(task, '--seed', '236')
      check(output == run(task, '--seed', '236') and output.startswith('random seed: 236\n'), 'Seed replay differs')
      check('日主' in output or '日元' in output, 'Seeded chart display missing')
      if task == 'demo':
        check('大运' in output and '流年' in output and '\x1b[' in output, 'Demo lost full transit/color display')
      elif task == 'relationship':
        check('夫妻宫：' in output and '六甲旬空依据：' in output and '起十年' in output, 'Relationship report incomplete')
    check(not tuple(cwd.iterdir()), 'Read-only CLI tasks wrote files')
    fixed = ('--birth-time', '2000-01-03 12:00', '--gender', 'female')
    chart = run('chart', *fixed, '--output-dir', 'output_data')
    chart_file, = (cwd / 'output_data/interpretation_examples').glob('*.txt')
    chart_bytes = chart_file.read_bytes()
    check(chart_file.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', chart.removesuffix('\n')) and b'\x1b[' not in chart_bytes,
      'Chart export differs from display')
    check('丁为阴火。' in run('knowledge', '--object', 'tiangan.ding'), 'Installed knowledge query missing')
    check('topic' in run('knowledge') or '知识' in run('knowledge'), 'Knowledge overview missing')
    run('knowledge', '--validate-knowledge')
    run('knowledge', '--export-knowledge-base')
    check(len(tuple((cwd / 'output_data').rglob('*.txt'))) == 21, 'Chart and knowledge exports do not coexist')
    check(chart_file.read_bytes() == chart_bytes, 'Knowledge export overwrote chart')
    criterion = 'editorial.guansha_coexistence.v1'
    check(criterion in run('match'), 'Criterion listing missing')
    check('SATISFIED' in run('match', criterion, *fixed, '--observation-scope', 'natal'), 'Installed matching failed')
    local = run('chart', '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'female',
      '--precision', 'minute', '--longitude', '-157.4')
    check('2024-01-01T12:00:00+14:00' in local, 'Installed location input lost civil time')
    source = cwd / 'source.json'
    source.write_bytes((package / 'knowledge_data.json').read_bytes())
    run('knowledge', '--knowledge-source', str(source), '--validate-knowledge')
    protected = cwd / 'blocked/knowledge_base/tiangan'
    protected.mkdir(parents=True)
    protected_source = protected / '丁.txt'
    protected_source.write_bytes(source.read_bytes())
    run('knowledge', '--knowledge-source', str(protected_source), '--export-knowledge-base',
      '--output-dir', 'blocked', error='overwrite')
    check(protected_source.read_bytes() == source.read_bytes(), 'Source overwrite guard truncated source')
    files = {path.relative_to(cwd): path.read_bytes() for path in cwd.rglob('*') if path.is_file()}
    for tokens, reason in (
      (('unknown-task',), 'invalid choice'),
      (('chart', '--unknown'), 'unrecognized arguments'),
      (('chart', '--birth-time', '2000-01-01 12:00'), '--gender'),
      (('knowledge', '--object', 'typo'), 'Unknown object_id'),
      (('chart', '--export-chart-json', 'removed.json'), 'unrecognized arguments'),
      (('knowledge', '--export-knowledge-json', 'removed.json'), 'unrecognized arguments'),
      (('match', '--export-context-json', 'removed.json'), 'unrecognized arguments'),
    ):
      run(*tokens, error=reason)
    check(files == {path.relative_to(cwd): path.read_bytes() for path in cwd.rglob('*') if path.is_file()},
      'Invalid installed command changed files')
  finally:
    witness.unlink()
  check(before == {path.relative_to(package): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in package.rglob('*') if path.is_file()}, 'CLI wrote into installed package')
  print(f'PASS real installed launcher: five tasks, seed/export/guard/negative controls, optimized={not __debug__}')


if __name__ == '__main__':
  main()
