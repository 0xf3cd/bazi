'''构建并检查安装工件，消费者不从源码检出导入。'''

import argparse
import hashlib
import importlib.metadata
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import venv
import zipfile

from pathlib import Path
from email.parser import BytesParser
from typing import Any, Final, Literal, TypedDict
from collections import Counter
from collections.abc import Collection, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cache


ROOT: Final[Path] = Path(__file__).resolve().parent
# 独立资源清单，用于核对 pyproject.toml 与 MANIFEST.in 的声明。
RUNTIME_DATA: Final[tuple[str, ...]] = (
  'bazi/calendar/hko_data/data/jieqi_encoded.bin',
  'bazi/calendar/hko_data/data/lunardate_encoded.bin',
  'bazi/calendar/celestial_data/data/jieqi_moments.txt',
  'bazi/calendar/celestial_data/data/lunar_years_algo1.txt',
  'bazi/calendar/celestial_data/data/lunar_years_algo2.txt',
  'bazi/calendar/celestial_data/data/equation_of_time.bin',
  'bazi/knowledge_data.json',
)
SOURCE_FILES: Final[tuple[str, ...]] = (
  'pyproject.toml', 'MANIFEST.in', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
  'README.md', 'API_CONTRACT.md', 'RELEASE_NOTES.md', 'RELEASING.md', 'Requirements.txt', 'ruff.toml',
  'run_tests.py', 'run_package_checks.py', 'run_release.py', 'run_demo.py', 'run_interpreter.py',
  'run_relationship_analyzer.py', 'run_docs.py', 'run_doc_checks.py', 'run_docs_site.py',
  'CONTRIBUTING.md',
  '.github/workflows/release.yml', '.github/workflows/on_pull_request.yml',
  '.github/workflows/on_push.yml', '.github/workflows/pypy_compatibility.yml', '.github/workflows/docs-publish.yml',
  '.github/ISSUE_TEMPLATE/knowledge-correction.yml', '.github/ISSUE_TEMPLATE/school-reading.yml',
  'docs/requirements.txt', 'docs/conf.py', 'docs/index.md', 'docs/versioning.md',
  'docs/_ext/api_reference.py', 'docs/_ext/house_docstrings.py', 'docs/_ext/typeddict_fields.py',
  'docs/_ext/knowledge_catalog.py', 'docs/_ext/source_links.py',
  'docs/_static/documentation.css',
  'docs/guides/quickstart.md', 'docs/guides/configuration.md',
  'docs/guides/relations-transits.md', 'docs/guides/integration.md', 'docs/guides/knowledge.md',
  'docs/guides/rule-coverage.md',
  'docs/catalog/index.rst', 'docs/catalog/objects.rst', 'docs/catalog/contexts.rst',
  'docs/catalog/sources.rst', 'docs/catalog/entries.rst', 'docs/catalog/criteria.rst',
  'docs/catalog/topics.rst', 'docs/catalog/viewpoints.rst', 'docs/catalog/filters.rst',
  'bazi/py.typed', 'bazi/calendar/celestial_data/SCHEMA.md',
)

ENVIRONMENT_ROLES: Final[tuple[str, ...]] = (
  'outer', 'build-wheel-direct', 'build-sdist', 'build-wheel-rebuilt',
  'consumer-wheel-direct', 'consumer-wheel-rebuilt', 'consumer-typing',
)


class Installer(TypedDict):
  '''实际调用前观察到的安装工具；scope 相对于所记录的目标环境。'''
  name: str
  version: str
  scope: Literal['runner', 'target']


class Environment(TypedDict):
  '''环境销毁前采集的白名单字段，不包含路径或安装来源。'''
  role: str
  python: dict[str, str]
  platform: dict[str, str]
  distributions: dict[str, str]
  installers: list[Installer]


_INSTALLATION: Final[ContextVar[tuple[str, list[Installer]] | None]] = ContextVar('installation', default=None)


def clean_environment() -> dict[str, str]:
  return {key: value for key, value in os.environ.items() if key not in ('PYTHONPATH', 'PYTHONHOME', 'MYPYPATH')}


def pip_version(line: str) -> str:
  from packaging.version import Version

  match = re.fullmatch(r'pip (\S+) from .+ \(python [0-9]+\.[0-9]+\)', line)
  if match is None:
    raise ValueError('Unsupported pip version output')
  Version(match[1])
  return match[1]


def observe_pip(prefix: list[str], scope: Literal['runner', 'target'], installers: list[Installer]) -> None:
  line = subprocess.check_output([*prefix, '--version'], env=clean_environment(), text=True, encoding='utf-8')
  record: Installer = {'name': 'pip', 'version': pip_version(line.strip()), 'scope': scope}
  if record not in installers:
    installers.append(record)


def outer_installers(receipt: Path) -> list[Installer]:
  lines = receipt.read_text(encoding='utf-8').splitlines()
  if len(lines) != 3:
    raise ValueError('Expected three outer installer observations')
  records: list[Installer] = []
  for line in lines:
    record: Installer = {'name': 'pip', 'version': pip_version(line), 'scope': 'runner'}
    if record not in records:
      records.append(record)
  return records


def observe_build_installer(event: str, args: tuple[Any, ...]) -> None:
  active = _INSTALLATION.get()
  if event != 'subprocess.Popen' or active is None:
    return
  python, installers = active
  argv = args[1]
  if isinstance(argv, str):
    for prefix in ([sys.executable, '-m', 'pip', '--python', python], [python, '-Im', 'pip']):
      if argv.startswith(subprocess.list2cmdline([*prefix, 'install']) + ' '):
        argv = [*prefix, 'install']
        break
  if not isinstance(argv, (list, tuple)):
    raise TypeError('Unsupported build installer invocation')
  scope: Literal['runner', 'target']
  if list(argv[:5]) == [sys.executable, '-m', 'pip', '--python', python] and 'install' in argv[5:]:
    prefix, scope = [sys.executable, '-m', 'pip'], 'runner'
  elif list(argv[:3]) == [python, '-Im', 'pip'] and 'install' in argv[3:]:
    prefix, scope = [python, '-Im', 'pip'], 'target'
  else:
    raise ValueError('Unsupported build installer invocation')
  token = _INSTALLATION.set(None)
  try:
    observe_pip(prefix, scope, installers)
  finally:
    _INSTALLATION.reset(token)


@cache
def register_installer_observer() -> None:
  # 审计钩子无法移除；只注册一次，非安装窗口不观察，也不保存命令参数。
  sys.addaudithook(observe_build_installer)


@contextmanager
def build_context() -> Iterator[None]:
  '''为串行构建临时过滤导入路径并显示 build 的安装失败输出，退出时恢复。'''
  original = {key: os.environ[key] for key in ('PYTHONPATH', 'PYTHONHOME', 'MYPYPATH') if key in os.environ}
  logger = logging.getLogger('build')
  level = logger.level
  handler = logging.StreamHandler()
  for key in original:
    del os.environ[key]
  logger.addHandler(handler)
  logger.setLevel(logging.INFO)
  try:
    yield
  finally:
    logger.removeHandler(handler)
    logger.setLevel(level)
    for key in ('PYTHONPATH', 'PYTHONHOME', 'MYPYPATH'):
      os.environ.pop(key, None)
    os.environ.update(original)


def collect_environment(python: str, role: str, installers: list[Installer]) -> Environment:
  from packaging.version import Version

  script = '''import importlib.metadata as metadata, json, platform, re
distributions = {}
for distribution in metadata.distributions():
  name = distribution.metadata['Name']
  if not name or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?', name):
    raise ValueError('Invalid distribution name')
  name = re.sub(r'[-_.]+', '-', name).lower()
  if name in distributions:
    raise ValueError('Duplicate normalized distribution')
  distributions[name] = distribution.version
print(json.dumps({'python': {'implementation': platform.python_implementation(), 'version': platform.python_version()},
  'platform': {'system': platform.system(), 'machine': platform.machine()}, 'distributions': dict(sorted(distributions.items()))}))
'''
  data = json.loads(subprocess.check_output([python, '-I', '-c', script], env=clean_environment(), text=True, encoding='utf-8'))
  if not installers:
    raise ValueError('Missing installer observations')
  for version in data['distributions'].values():
    Version(version)
  for value in (*data['python'].values(), *data['platform'].values()):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', value):
      raise ValueError('Unsupported environment identity')
  return {'role': role, 'python': data['python'], 'platform': data['platform'],
    'distributions': data['distributions'], 'installers': list(installers)}


def build_artifact(source: Path, output: Path, kind: Literal['wheel', 'sdist'], role: str, work: Path,
                   environments: list[Environment] | None) -> None:
  if environments is None:
    run([sys.executable, '-m', 'build', '--' + kind, '--outdir', str(output), str(source)], work)
    return
  # 导出时用 build 公开 API 持有隔离环境上下文，在清理前采集；普通门禁仍用 CLI。
  from build import ProjectBuilder
  from build.env import DefaultIsolatedEnv

  register_installer_observer()
  installers: list[Installer] = []
  with build_context(), DefaultIsolatedEnv() as environment:
    builder = ProjectBuilder.from_isolated_env(environment, str(source))
    def install(requirements: Collection[str]) -> None:
      token = _INSTALLATION.set((environment.python_executable, installers))
      try:
        environment.install(requirements)
      finally:
        _INSTALLATION.reset(token)
    install(builder.build_system_requires)
    install(builder.get_requires_for_build(kind))
    builder.build(kind, str(output))
    environments.append(collect_environment(environment.python_executable, role, installers))


def source_identity(root: Path, files: tuple[str, ...]) -> str:
  def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=root, env=clean_environment(), text=True, encoding='utf-8').strip()
  if Path(git('rev-parse', '--show-toplevel')).resolve() != root.resolve():
    raise ValueError('Environment export requires a source checkout')
  sha = git('rev-parse', 'HEAD')
  if not re.fullmatch(r'[0-9a-f]{40}', sha) or git('status', '--porcelain', '--untracked-files=all'):
    raise ValueError('Environment export requires a clean source checkout')
  if not set(files) <= set(git('ls-files', '-z').split('\0')):
    raise ValueError('Environment export requires tracked source inputs')
  return sha


def sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(root: Path) -> tuple[str, ...]:
  files = set(SOURCE_FILES) | set(RUNTIME_DATA)
  files.update(path.relative_to(root).as_posix() for path in (root / 'bazi').rglob('*.py'))
  files.update(f'bazi/calendar/hko_data/data/{year}.txt' for year in range(1901, 2101))
  for path in (root / 'tests').rglob('*'):
    if path.suffix in ('.py', '.ini', '.txt', '.json') and '__pycache__' not in path.parts:
      files.add(path.relative_to(root).as_posix())
  for name in files:
    path = root / name
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
      raise ValueError(f'Invalid source input: {name}')
  return tuple(sorted(files))


def check_description(content: bytes, readme: bytes, label: str) -> None:
  content = content.replace(b'\r\n', b'\n')
  readme = readme.replace(b'\r\n', b'\n')
  if not readme.endswith(b'\n'):
    readme += b'\n'
  header, separator, body = content.partition(b'\n\n')
  if not separator or BytesParser().parsebytes(header).get_all('Description-Content-Type') != ['text/markdown']:
    raise ValueError(f'Description content type mismatch: {label}')
  if body != readme:
    raise ValueError(f'Description bytes differ from README: {label}')


def check_wheel(wheel: Path, expected: dict[str, str], licenses: dict[str, str], readme: bytes) -> None:
  with zipfile.ZipFile(wheel) as archive:
    names = archive.namelist()
    metadata_dir = wheel.name.split('-')[0] + '-' + wheel.name.split('-')[1] + '.dist-info/'
    metadata_files = {metadata_dir + name for name in ('METADATA', 'WHEEL', 'top_level.txt', 'RECORD')}
    license_files = {metadata_dir + 'licenses/' + name for name in licenses}
    if duplicates := sorted(name for name, count in Counter(names).items() if count > 1):
      raise ValueError(f'Duplicate wheel members: {wheel.name}: {duplicates}')
    if set(names) != set(expected) | metadata_files | license_files:
      raise ValueError(f'Wheel file roster mismatch: {wheel.name}: {set(names) ^ (set(expected) | metadata_files | license_files)}')
    for name, digest in expected.items():
      if hashlib.sha256(archive.read(name)).hexdigest() != digest:
        raise ValueError(f'Wheel bytes differ: {name}')
    for name, digest in licenses.items():
      if hashlib.sha256(archive.read(metadata_dir + 'licenses/' + name)).hexdigest() != digest:
        raise ValueError(f'License bytes differ: {name}')
    check_description(archive.read(metadata_dir + 'METADATA'), readme, wheel.name)


def run(command: list[str], cwd: Path) -> None:
  print(f'RUN cwd={cwd} argv={command!r}', flush=True)
  subprocess.run(command, cwd=cwd, env=clean_environment(), check=True)


def consumer(directory: Path, wheel: Path, installers: list[Installer] | None = None) -> Path:
  venv.EnvBuilder(with_pip=True).create(directory)
  python = directory / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
  if installers is not None:
    observe_pip([str(python), '-I', '-m', 'pip'], 'target', installers)
  run([str(python), '-I', '-m', 'pip', 'install', '--no-index', '--no-deps', '--no-compile', str(wheel)], directory.parent)
  # Python 3.11 的 ensurepip 还会安装 setuptools；消费者只需要 pip 与 bazi。
  if installers is not None:
    observe_pip([str(python), '-I', '-m', 'pip'], 'target', installers)
  run([str(python), '-I', '-m', 'pip', 'uninstall', '-y', 'setuptools'], directory.parent)
  return python


def check_packages(root: Path, work: Path, output_dir: Path | None,
                   environment_report: Path | None = None, outer_installer_report: Path | None = None) -> None:
  if output_dir is not None and output_dir.exists() and any(output_dir.iterdir()):
    raise ValueError('Output directory must be empty')
  if environment_report is not None and environment_report.exists():
    raise ValueError('Environment report must not exist')
  files = source_files(root)
  source_sha = source_identity(root, files) if environment_report is not None else None
  environments: list[Environment] | None = [] if environment_report is not None else None
  outer = outer_installers(outer_installer_report) if outer_installer_report is not None else []
  before = {name: sha256(root / name) for name in files}
  readme = (root / 'README.md').read_bytes()
  project = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))['project']
  package = {name: digest for name, digest in before.items() if name.startswith('bazi/') and (name.endswith('.py') or name == 'bazi/py.typed' or name in RUNTIME_DATA)}
  licenses = {name: before[name] for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md')}
  stage = work / 'source'
  for name in files:
    target = stage / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / name, target)

  direct_dir, sdist_dir, rebuilt_dir = (work / name for name in ('direct', 'sdist', 'rebuilt'))
  build_artifact(stage, direct_dir, 'wheel', 'build-wheel-direct', work, environments)
  build_artifact(stage, sdist_dir, 'sdist', 'build-sdist', work, environments)
  direct, = direct_dir.glob('*.whl')
  sdist, = sdist_dir.glob('*.tar.gz')
  extracted = work / 'extracted'
  with tarfile.open(sdist) as archive:
    members = [member for member in archive.getmembers() if not member.isdir()]
    prefix = f'bazi-{project["version"]}/'
    payload: dict[str, bytes] = {}
    for member in members:
      if not member.isfile() or not member.name.startswith(prefix) or '..' in Path(member.name).parts:
        raise ValueError(f'Unsafe sdist member: {member.name}')
      name = member.name.removeprefix(prefix)
      if name in payload:
        raise ValueError(f'Duplicate sdist member: {name}')
      stream = archive.extractfile(member)
      if stream is None:
        raise ValueError(f'Unreadable sdist member: {name}')
      payload[name] = stream.read()
    generated = {'PKG-INFO', 'setup.cfg'} | {f'bazi.egg-info/{name}' for name in ('PKG-INFO', 'SOURCES.txt', 'dependency_links.txt', 'top_level.txt')}
    if set(payload) != set(files) | generated:
      raise ValueError(f'Sdist file roster mismatch: {set(payload) ^ (set(files) | generated)}')
    for name, digest in before.items():
      if hashlib.sha256(payload[name]).hexdigest() != digest:
        raise ValueError(f'Sdist bytes differ: {name}')
    check_description(payload['PKG-INFO'], readme, sdist.name)
    # 只提取已核验的普通文件，不提取归档链接或任意路径。
    for name, content in payload.items():
      target = extracted / name
      target.parent.mkdir(parents=True, exist_ok=True)
      target.write_bytes(content)
  build_artifact(extracted, rebuilt_dir, 'wheel', 'build-wheel-rebuilt', work, environments)
  rebuilt, = rebuilt_dir.glob('*.whl')
  pair = {path: sha256(path) for path in (sdist, rebuilt)}
  run([sys.executable, '-m', 'twine', 'check', '--strict', str(direct), str(sdist), str(rebuilt)], work)

  foreign = work / 'consumer'
  foreign.mkdir()
  shutil.copyfile(root / 'tests/package_smoke.py', foreign / 'package_smoke.py')
  expected = {'package': package, 'licenses': licenses, 'version': project['version']}
  (foreign / 'expected.json').write_text(json.dumps(expected), encoding='utf-8')
  for label, wheel in (('direct', direct), ('rebuilt', rebuilt)):
    check_wheel(wheel, package, licenses, readme)
    installers: list[Installer] | None = [] if environments is not None else None
    python = consumer(work / (label + '-venv'), wheel, installers)
    for optimization in ([], ['-O']):
      run([str(python), '-I', '-B', *optimization, 'package_smoke.py', 'expected.json'], foreign)
    if environments is not None and installers is not None:
      environments.append(collect_environment(str(python), 'consumer-wheel-' + label, installers))

  installers = [] if environments is not None else None
  python = consumer(work / 'typing-venv', rebuilt, installers)
  if installers is not None:
    observe_pip([str(python), '-I', '-m', 'pip'], 'target', installers)
  run([str(python), '-I', '-m', 'pip', 'install', 'mypy==' + importlib.metadata.version('mypy')], foreign)
  good = ('from datetime import UTC, datetime, timedelta, timezone\nfrom pathlib import Path\nfrom dataclasses import replace\nfrom bazi.bazi import Bazi, LocationTime\nfrom bazi.bazi_chart import BaziChart\n'
          'from bazi.calendar.dates import GanzhiYearMonth, JieqiTime, LunarYearInfo\n'
          'from bazi.calendar.hko_data import LunarYearInfo as HkoInfo\n'
          'from bazi.calendar.hko_data.decoder import LunarYearInfo as DecoderInfo\n'
          'from bazi.calendar.celestial_data.loader import LunarYearInfo as CelestialInfo\n'
          'from bazi.defines import Zhu, TianganLayer, Dizhi, Jieqi, Tiangan, Ganzhi\n'
          'from bazi.transits import TransitKind\n'
          'from bazi.analyzer.relationship import KongwangHit, KongwangResult, StarAppearance\n'
          'from bazi.school import BaziConfig\n'
          'from bazi.common import frozendict\n'
          'from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase, KnowledgeObject, KnowledgeEntry, KnowledgeSource, object_id\n'
          'from bazi.context_matching import NatalObservation, LiunianObservation, TransitObservation, Observation, YearCoordinate, MonthCoordinate, DateCoordinate, MomentCoordinate, LiunianPosition, ChartOccurrence, CriterionResult, CriterionReason, ContextResult, CriterionInfo, criterion, criteria, evaluate_context\n'
          'chart: BaziChart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), "male"))\n'
          'knowledge = KnowledgeBase.load()\n'
          'entries: tuple[KnowledgeEntry, ...] = knowledge.query(object_id="tiangan.ding")\n'
          'entry = entries[0]\ndisplay_flag: bool = entry.show_by_default\n'
          'objects: tuple[KnowledgeObject, ...] = knowledge.find_objects("丁")\n'
          'found: tuple[KnowledgeEntry, ...] = knowledge.search("丁", include_reference_only=True)\n'
          'topics: tuple[str, ...] = knowledge.filter_values("topic")\n'
          'catalog: frozendict[str, CriterionInfo] = criteria()\n'
          'info: CriterionInfo = criterion("editorial.guansha_coexistence.v1")\n'
          'observation_types: tuple[type[NatalObservation] | type[LiunianObservation] | type[TransitObservation], ...] = info.observation_types\n'
          'source_path: Path = DEFAULT_SOURCE_PATH\n'
          'identifier: str = object_id(Tiangan.丁)\n'
          'witness: KnowledgeSource = knowledge.sources["repository_guoyin_variants"]\n'
          'display: str = knowledge.render(entries[0], show_sources=True, manual_context=True, premise_verdict="UNKNOWN")\n'
          'subject_text: str = knowledge.render_subject(identifier, include_reference_only=True, show_sources=True)\n'
          'matched: ContextResult = evaluate_context(chart, criterion_id="editorial.guansha_coexistence.v1", observation=NatalObservation())\n'
          'result_input: Bazi = matched.bazi\n'
          'copied: ContextResult = replace(matched, _bazi=result_input)\n'
          'ids: tuple[str, ...] = matched.reference_ids\n'
          'constructed: ContextResult = ContextResult(observation=matched.observation, criterion=matched.criterion, evidence=matched.evidence, reference_ids=ids, _bazi=result_input, knowledge=knowledge)\n'
          'year_request = YearCoordinate(ganzhi_year=2024)\n'
          'month_request = MonthCoordinate(ganzhi_year=2024, ganzhi_month=Dizhi.辰)\n'
          'date_request = DateCoordinate(datetime(2024, 4, 10).date())\n'
          'moment_request = MomentCoordinate(datetime(2024, 4, 10, 12))\n'
          'observation: Observation = TransitObservation((TransitKind.LIUNIAN,), year_request)\n'
          'liunian_observation = LiunianObservation(2024)\n'
          'position = LiunianPosition(2024)\n'
          'reason: CriterionReason = "premise_satisfied"\n'
          'verdict = CriterionResult(info.criterion_id, reason, frozendict({}))\n'
          'target = Ganzhi.from_str("甲子")\n'
          'hit = KongwangHit(Zhu.月, target)\n'
          'anchor = KongwangResult(Zhu.日, target, ())\n'
          'appearance = StarAppearance(Zhu.月, target, TianganLayer.明干, Tiangan.甲)\n'
          'lunar: LunarYearInfo = {"first_solar_day": datetime(2000, 2, 5).date(), "leap": False, "leap_month": None, "days_counts": [30] * 12, "ganzhi": target}\n'
          'hko: HkoInfo = lunar\ndecoder: DecoderInfo = hko\ncelestial: CelestialInfo = decoder\n')
  good += ('local: Bazi = Bazi.create(datetime(2023, 12, 31, 22, tzinfo=UTC), "female", '
           'BaziConfig.from_values(precision="minute"), longitude=-157.4, civil_timezone=timezone(timedelta(hours=14)))\n'
           'local_chart: BaziChart = BaziChart(local)\n'
           'local_record: ContextResult = evaluate_context(local_chart, criterion_id="editorial.guansha_coexistence.v1", observation=NatalObservation())\n'
           'coordinate: GanzhiYearMonth = local.ganzhi_year_month\n'
           'from_branch: GanzhiYearMonth = GanzhiYearMonth.from_dizhi(2000, Dizhi.寅)\n'
           'from_jie: GanzhiYearMonth = GanzhiYearMonth.from_jie(JieqiTime(Jieqi.立春, datetime(2000, 2, 4)))\n'
           'reference: datetime = local.reference_datetime\n'
           'month_jies: tuple[JieqiTime, JieqiTime] = local.month_jies\n'
           'facts: LocationTime | None = local.location_time\n'
           'if facts is not None:\n'
           '  instant: datetime = facts.canonical_instant\n'
           '  civil: datetime = facts.civil_time\n'
           '  apparent: datetime = facts.apparent_time\n')
  (foreign / 'good.py').write_text(good, encoding='utf-8')
  bad = good + ('wrong: int = chart\nBazi.create(42, "male")\n'
                'Bazi.create(datetime.now(), "male", longitude="0", civil_timezone="UTC")\n'
                'knowledge.query(object_id=42)\nLiunianObservation("2024")\n'
                'knowledge.find_objects(42)\nknowledge.search(42)\nknowledge.filter_values(42)\n'
                'criterion(42)\ninfo.definition = "changed"\ncatalog["changed"] = info\n'
                'object_id(Dizhi.子)\n'
                'knowledge.render(entries[0], premise_verdict=1)\n'
                'knowledge.render_subject(Tiangan.丁, include_reference_only=1)\n'
                'knowledge.sources["editorial"] = witness\n'
                'witness.work = "changed"\n'
                'evaluate_context(chart, criterion_id=42, observation="natal")\n'
                'ContextResult(matched.observation, matched.criterion, matched.evidence, (1,), 42, knowledge)\n'
                'KnowledgeEntry(entry.claim_id, entry.text, entry.roles, entry.relations, entry.topics, entry.applicability, entry.premise, entry.contexts, entry.sources, entry.source_state, entry.attribution, entry.viewpoint, entry.exceptions, entry.limits, "true", entry.legacy)\n'
                'YearCoordinate("2024")\nMonthCoordinate(2024, "辰")\nDateCoordinate("2024-04-10")\nMomentCoordinate("2024-04-10T12:00:00")\n'
                'TransitObservation(("liunian",))\nLiunianPosition("2024")\n'
                'KongwangHit("年", target)\nKongwangResult(Zhu.YUE, target, ())\n'
                'StarAppearance(Zhu.月, target, "明干", Tiangan.甲)\n'
                'ChartOccurrence("年", target, TianganLayer.明干, Tiangan.甲, "比肩")\n'
                'CriterionResult(info.criterion_id, "invalid", frozendict({}))\n'
                'matched.bazi = chart.bazi\n'
                'chart.json\nBaziChart.from_json({})\nmatched.input_json\nmatched.export_json()\nContextResult.from_json("")\nknowledge.export_json()\nKnowledgeBase.from_json("")\n'
                'GanzhiYearMonth(2000, "1")\nGanzhiYearMonth.from_dizhi(2000, 1)\n'
                'GanzhiYearMonth.from_jie(datetime.now())\n'
                'local.reference_datetime = datetime.now()\n'
                'local.month_jies = ()\n'
                'coordinate.month = 0\n'
                'def unsafe_time(value: Bazi) -> datetime:\n  return value.location_time.canonical_instant\n')
  (foreign / 'bad.py').write_text(bad, encoding='utf-8')
  command = [str(python), '-I', '-X', 'utf8', '-m', 'mypy', '--strict', '--no-incremental', '--follow-imports=silent', '--show-traceback']
  run([*command, 'good.py'], foreign)
  result = subprocess.run(
    [*command, 'bad.py'],
    cwd=foreign,
    env={**os.environ, 'MYPYPATH': '', 'PYTHONPATH': ''},
    capture_output=True, text=True, encoding='utf-8', check=False,
  )
  print(result.stdout, end='')
  print(result.stderr, end='')
  print('Installed typing negative EXIT=' + str(result.returncode), flush=True)
  if result.returncode != 1 or '[assignment]' not in result.stdout or '[arg-type]' not in result.stdout or 'import-untyped' in result.stdout or 'import-not-found' in result.stdout:
    raise ValueError('Installed typing negative control did not reach both type checks')
  for interface in ('create', 'query', 'find_objects', 'search', 'filter_values', 'criterion', 'LiunianObservation', 'TransitObservation', 'YearCoordinate', 'MonthCoordinate', 'DateCoordinate', 'MomentCoordinate', 'LiunianPosition', 'ChartOccurrence', 'KongwangHit', 'KongwangResult', 'StarAppearance', 'CriterionResult', 'KnowledgeEntry', 'evaluate_context', 'ContextResult', 'GanzhiYearMonth', 'from_dizhi', 'from_jie', 'object_id', 'render', 'render_subject'):
    if f'to "{interface}"' not in result.stdout:
      raise ValueError(f'Installed typing negative control missed {interface}')
  for message in ('"None"',):
    if message not in result.stdout:
      raise ValueError(f'Installed time typing negative control missed {message}')
  for owner_name, attribute_name, trigger in (
    ('Bazi', 'reference_datetime', 'local.reference_datetime = datetime.now()'),
    ('Bazi', 'month_jies', 'local.month_jies = ()'),
    ('GanzhiYearMonth', 'month', 'coordinate.month = 0'),
    ('KnowledgeSource', 'work', 'witness.work = "changed"'),
    ('CriterionInfo', 'definition', 'info.definition = "changed"'),
    ('ContextResult', 'bazi', 'matched.bazi = chart.bazi'),
  ):
    line_number = bad.splitlines().index(trigger) + 1
    message = f'bad.py:{line_number}: error: Property "{attribute_name}" defined in "{owner_name}" is read-only  [misc]'
    if message not in result.stdout.splitlines():
      raise ValueError(f'Installed typing negative control missed {owner_name}.{attribute_name}')
  for value_type, trigger in (
    ('CriterionInfo', 'catalog["changed"] = info'),
    ('KnowledgeSource', 'knowledge.sources["editorial"] = witness'),
  ):
    line_number = bad.splitlines().index(trigger) + 1
    message = f'bad.py:{line_number}: error: Unsupported target for indexed assignment ("frozendict[str, {value_type}]")  [index]'
    if message not in result.stdout.splitlines():
      raise ValueError(f'Installed typing negative control missed immutable {value_type} mapping')
  for owner, removed_member in (('BaziChart', 'json'), ('ContextResult', 'input_json'), ('ContextResult', 'export_json'), ('KnowledgeBase', 'export_json')):
    if f'"{owner}" has no attribute "{removed_member}"' not in result.stdout:
      raise ValueError(f'Installed typing negative control missed removed {owner}.{removed_member}')

  if environments is not None and installers is not None:
    environments.append(collect_environment(str(python), 'consumer-typing', installers))
    environments.insert(0, collect_environment(sys.executable, 'outer', outer))

  for path, digest in pair.items():
    if sha256(path) != digest:
      raise ValueError(f'Tested artifact changed: {path.name}')
    print(f'TESTED {path.name} sha256={digest}', flush=True)
  if before != {name: sha256(root / name) for name in files}:
    raise ValueError('Source changed during artifact verification')
  if source_sha is not None and source_identity(root, source_files(root)) != source_sha:
    raise ValueError('Source identity changed during artifact verification')
  if output_dir is not None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
      raise ValueError('Output directory must be empty')
    for path, digest in pair.items():
      destination = output_dir / path.name
      shutil.copyfile(path, destination)
      if sha256(destination) != digest:
        raise ValueError(f'Retained artifact changed: {path.name}')
  if environment_report is not None and environments is not None:
    if tuple(environment['role'] for environment in environments) != ENVIRONMENT_ROLES:
      raise ValueError('Environment role roster mismatch')
    report = {'schema_version': 1, 'source_sha': source_sha,
      'pair': {kind: {'filename': path.name, 'sha256': pair[path]} for kind, path in (('sdist', sdist), ('wheel', rebuilt))},
      'environments': environments}
    environment_report.parent.mkdir(parents=True, exist_ok=True)
    with environment_report.open('x', encoding='utf-8') as report_stream:
      json.dump(report, report_stream, sort_keys=True, ensure_ascii=False, indent=2)
      report_stream.write('\n')


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--output-dir', type=Path, help='在空的仓外目录中只保留已验证 sdist 及其重建 wheel。')
  parser.add_argument('--environment-report', type=Path, help='在仓外新文件中记录七类实际环境；须同时保留工件并提供外层安装器记录。')
  parser.add_argument('--outer-installer-report', type=Path, help='release 安装步骤三次 pip --version 的原始行，仅解析版本，不复制原文。')
  args = parser.parse_args()
  output_dir = args.output_dir.resolve() if args.output_dir is not None else None
  environment_report = args.environment_report.resolve() if args.environment_report is not None else None
  outer_installer_report = args.outer_installer_report.resolve() if args.outer_installer_report is not None else None
  if (environment_report is None) != (outer_installer_report is None) or (environment_report is not None and output_dir is None):
    parser.error('Environment export requires --output-dir, --environment-report and --outer-installer-report together')
  if output_dir is not None and output_dir.is_relative_to(ROOT):
    raise ValueError('Artifacts must stay outside the source checkout')
  for path in (environment_report, outer_installer_report):
    if path is not None and (path.is_relative_to(ROOT) or (output_dir is not None and path.is_relative_to(output_dir))):
      raise ValueError('Environment reports must stay outside the source checkout and artifact directory')
  if environment_report is not None and environment_report == outer_installer_report:
    raise ValueError('Environment report and installer receipt must be different files')
  with tempfile.TemporaryDirectory(prefix='bazi-package-') as temporary:
    work = Path(temporary).resolve()
    if work.is_relative_to(ROOT):
      raise ValueError('TMPDIR must be outside the source checkout')
    check_packages(ROOT, work, output_dir, environment_report, outer_installer_report)


if __name__ == '__main__':
  main()
