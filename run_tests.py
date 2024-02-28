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

import coverage
import colorama


# Print system time and other info.
term_width: int = shutil.get_terminal_size().columns
start_time: datetime = datetime.now()
mem = psutil.virtual_memory()

print('#' * term_width)

print(f'-- {sys.argv}')
print(f'-- system time: {start_time.astimezone()} ({start_time.astimezone().tzinfo})')
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

# Get the argument from terminal. If `coverage`, then generate coverage report.
argparse = argparse.ArgumentParser()
argparse.add_argument('-c', '--coverage', action='store_true', help='Whether or not to generate coverage report.')
do_cov: bool = argparse.parse_args().coverage

# Make `bazi` importable from the current directory.
sys.path.append(str(Path(__file__).parent.parent))

# Run tests and generate html coverage report.
cov = coverage.Coverage()
if do_cov:
  cov.start()

print('\n' + '#' * term_width)
print('>> Running tests...')
from bazi import test # noqa: E402
test_ret: int = test.run_tests()

if do_cov:
  cov.stop()
  cov.html_report(directory=str(Path(__file__).parent / 'covhtml'))

  # Print the coverage report.
  print('\n' + '#' * term_width)
  print('>> Generating coverage report...')
  cov.report(show_missing=True)

# Use `ruff` to check for style violations.
print('\n' + '#' * term_width)
print('>> Checking for style violations...')
ruff_ret: int = subprocess.run(['ruff', str(Path(__file__).parent)]).returncode
print('>> Checking style violations completed...')

# Exit with the exit codes.
print('\n' + '#' * term_width)
end_time: datetime = datetime.now()
print(f'-- Finished at {end_time.isoformat()}')
print(f'-- Time elapsed: {end_time - start_time}')

color = colorama.Fore.GREEN if test_ret == 0 else colorama.Fore.RED
print(f'-- Tests exited with code {color}{test_ret}{colorama.Style.RESET_ALL}')

color = colorama.Fore.GREEN if ruff_ret == 0 else colorama.Fore.RED
print(f'-- Ruff exited with code {color}{ruff_ret}{colorama.Style.RESET_ALL}')

sys.exit(test_ret | ruff_ret) # Mix the two return codes just to convey the failure if any.
