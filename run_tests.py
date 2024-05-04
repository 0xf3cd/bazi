#!/usr/bin/env python3

import os
import sys
import shutil
import psutil
import platform
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import coverage
import colorama


# Get the argument from terminal. If `coverage`, then generate coverage report.
argparse = argparse.ArgumentParser()
argparse.add_argument('-c', '--coverage', action='store_true', help='Whether or not to generate coverage report.')
argparse.add_argument('-cr', '--coverage-rate', type=float, help='Must-met minimum coverage rate. Default: 80.0', default=80.0)

argparse.add_argument('-nl', '--no-linter', action='store_true', help='Whether or not to skip linting.')

argparse.add_argument('-s', '--slow-test', action='store_true', help='Whether or not to run slow tests.')
argparse.add_argument('-hko', '--hkodata-test', action='store_true', help='Whether or not to run hkodata tests.')
argparse.add_argument('-ep', '--errorprone-test', type=int, help='Whether or not to rerun errorprone tests.', default=0)
argparse.add_argument('-k', '--expression', type=str, help='Expression to filter tests.', default=None)

argparse.add_argument('-d', '--demo', action='store_true', help='Whether or not to run demo code.')
argparse.add_argument('-i', '--interpreter', action='store_true', help='Whether or not to run interpreter.')

args = argparse.parse_args()
do_cov: bool = args.coverage
minimum_cov_rate: float = args.coverage_rate
skip_linter: bool = args.no_linter
run_slow_test: bool = args.slow_test
run_hko_test: bool = args.hkodata_test
run_errorprone_test_rounds: int = args.errorprone_test
expression: Optional[str] = args.expression
do_demo: bool = args.demo
do_interpreter: bool = args.interpreter

term_width: int = shutil.get_terminal_size().columns

def print_sysinfo() -> None:
  # Print system time and other info.
  mem = psutil.virtual_memory()
  this_moment: datetime = datetime.now()
  print('#' * term_width)

  print(f'-- {sys.argv}')
  print(f'-- system time: {this_moment.astimezone()} ({this_moment.astimezone().tzinfo})')
  print(f'-- python executable: {sys.executable}')
  print(f'-- python version: {sys.version}')
  print(f'-- pid: {os.getpid()}')
  print(f'-- cwd: {os.getcwd()}')
  print(f'-- node: {platform.node()}')

  print(f'-- system: {platform.system()}')
  print(f'-- platform: {platform.platform()}')
  print(f'-- release: {platform.release()}')
  print(f'-- version: {platform.version()}')
  print(f'-- machine: {platform.machine()}')
  print(f'-- processor: {platform.processor()}')
  print(f'-- architecture: {platform.architecture()}')
  print(f'-- cpu cores: {os.cpu_count()}')

  print(f'-- memory size: {mem.total // 1024 // 1024} MB')
  print(f'-- usable memory size: {mem.available // 1024 // 1024} MB')
  print(f'-- disk usage: {psutil.disk_usage("/").percent}%')


# Run tests and generate html coverage report.
def run_tests() -> int:
  print('\n' + '#' * term_width)
  print('>> Running bazi tests...')

  # Make `bazi` importable from the current directory.
  sys.path.append(str(Path(__file__).parent / 'src'))
  from src.test import run_bazi_tests # noqa: E402
  ret_code: int = run_bazi_tests(expression=expression, slow_tests=run_slow_test)

  if run_hko_test:
    print('\n' + '#' * term_width)
    print('>> Running hkodata tests...')
    from src.HkoData.test import run_hkodata_tests # noqa: E402
    ret_code |= run_hkodata_tests(expression=expression)

  from src.test import run_errorprone_bazi_tests # noqa: E402
  for round in range(run_errorprone_test_rounds):
    print('\n' + '#' * term_width)
    print(f'>> Rerunning errorprone tests... Round {round + 1}/{run_errorprone_test_rounds}.')

    round_ret_code: int = run_errorprone_bazi_tests(expression=expression)
    ret_code |= round_ret_code

    if round_ret_code == 0:
      print(colorama.Fore.GREEN + f'>> Round {round + 1}/{run_errorprone_test_rounds} OK!' + colorama.Style.RESET_ALL)
    else:
      print(colorama.Fore.RED + f'>> Round {round + 1}/{run_errorprone_test_rounds} failed! Stopping...' + colorama.Style.RESET_ALL)
      break

  if ret_code != 0:
    # Print in red.
    print(colorama.Fore.RED + f'>> Tests failed with exit code {ret_code}' + colorama.Style.RESET_ALL)

  return ret_code


def run_coverage(test_f: Callable[[], int]) -> int:
  print('\n' + '#' * term_width)
  print(f'>> Running {test_f} with coverage...')

  cov = coverage.Coverage(
    omit=[
      '*/__init__.py',
      '*/run_tests.py',
      '*/test/*',
      'src/hkodata/encoder.py',
    ]
  )
  cov.start()
  ret_code: int = test_f()
  cov.stop()
  cov.html_report(directory=str(Path(__file__).parent / 'covhtml'))

  # Print the coverage report.
  print('\n' + '#' * term_width)
  print('>> Generating coverage report...')
  cov_rate: float = cov.report(show_missing=True)
  
  if cov_rate < minimum_cov_rate:
    print(colorama.Fore.RED + f'>> Coverage rate: {cov_rate}% (below {minimum_cov_rate}%)' + colorama.Style.RESET_ALL)
    ret_code |= 0x42
  else:
    print(colorama.Fore.GREEN + f'>> Coverage rate: {cov_rate}%' + colorama.Style.RESET_ALL)

  return ret_code


def run_ruff() -> int:
  # Use `ruff` to check for style violations.
  print('\n' + '#' * term_width)
  print('>> Checking for style violations...')

  proc: subprocess.CompletedProcess = subprocess.run([
    'ruff', 'check', str(Path(__file__).parent)
  ], capture_output=True)
  ruff_ret: int = proc.returncode
  print('>> Checking style violations completed...')

  if ruff_ret == 0:
    print(colorama.Fore.GREEN + '>> No style violations found!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + '>> Violations detected!' + colorama.Style.RESET_ALL)
    print(proc.stdout.decode('utf-8'))
    print(proc.stderr.decode('utf-8'))

  return ruff_ret


def run_proc_and_print(cmds: list[str]) -> int:
  '''This method is mainly for compatability with Windows.'''
  if platform.system() == 'Windows':
    ret: int = subprocess.run(cmds).returncode
  else:
    proc: subprocess.CompletedProcess = subprocess.run(cmds, capture_output=True)
    ret: int = proc.returncode
    print(proc.stdout.decode('utf-8'))
    print(proc.stderr.decode('utf-8'))
  return ret


def run_demo() -> int:
  print('\n' + '#' * term_width)
  print('>> Running demo...')
  ret: int = run_proc_and_print([
    'python3', str(Path(__file__).parent / 'run_demos.py')
  ])

  if ret == 0:
    print(colorama.Fore.GREEN + '>> Demo passed!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + '>> Demo failed!' + colorama.Style.RESET_ALL)
  return ret


def run_interpreter() -> int:
  print('\n' + '#' * term_width)
  print('>> Running interpreter...')
  ret: int = run_proc_and_print([
    'python3', str(Path(__file__).parent / 'run_interpreter.py')
  ])
  
  if ret == 0:
    print(colorama.Fore.GREEN + '>> Interpreter passed!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + '>> Interpreter failed!' + colorama.Style.RESET_ALL)
  return ret


def main() -> None:
  start_time: datetime = datetime.now()
  ret_code: int = 0

  print_sysinfo()

  if do_cov:
    ret_code |= run_coverage(run_tests)
  else:
    ret_code |= run_tests()

  if do_demo:
    ret_code |= run_demo()

  if do_interpreter:
    ret_code |= run_interpreter()

  if not skip_linter:
    ret_code |= run_ruff()

  print('\n' + '#' * term_width)
  end_time: datetime = datetime.now()
  print(f'-- Finished at {end_time.isoformat()}')
  print(f'-- Time elapsed: {end_time - start_time}')

  if ret_code == 0:
    print(colorama.Fore.GREEN + '>> All tasks passed!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + f'>> Some tasks failed! Exit with code {ret_code}' + colorama.Style.RESET_ALL)

  sys.exit(ret_code)


if __name__ == '__main__':
  main()
