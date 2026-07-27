# Bazi Projects
> 排盘、五行、十神、纳音、刑冲破害、合会

## Instructions
* Python version should be >= 3.11
* Install requirements by `python -m pip install -r Requirements.txt`
* The encoded HKO data under `src/Calendar/HkoData/data/` is committed to the repo; the library only reads it at runtime. To regenerate the data, `pip install requests` manually (deliberately not in Requirements.txt) and run `python -m src.Calendar.HkoData.Encoder` from the repo root.
* Run linter: `ruff check .`
* Run static type checker: `mypy .`
* Run tests: `./run_tests.py`
  * By default:
    * hkodata tests and slow tests won't run;
    * `ruff` and `mypy` won't run;
    * demo and interpreter won't run.
  * Arguments:
    * Add `-a`/`--all` to run everything: all tests (including hkodata and slow tests), coverage, linter, static type check, demo and interpreter. This takes precedence over `-nt` and `-k`.
    * Add `-nt`/`--no-test` to skip tests and coverage.
    * Add `-hko` to also run hkodata tests, like: `./run_tests.py -hko`.
    * Add `-s` to also run slow tests, like: `./run_tests.py -s`.
    * Add `-v` to show verbose info during testing.
    * Add `-k <expression>` to specify the test(s) to run, this argument will be passed to `pytest`. Mutually exclusive with `-s` and `-hko`: when `-k` is set, `-s`/`-hko` are ignored.
    * Add `-c` to collect coverage data during testing. This also produces a coverage report in `./covhtml`.
    * Add `-cr <rate>`/`--coverage-rate <rate>` to set the minimum coverage rate (default: 80.0); only takes effect when coverage runs (`-c` or `-a`).
    * Add `-r`/`--ruff` to run the linter after tests.
    * Add `-mypy` to run mypy static type checker after tests.
    * Add `-d` to run `./run_demo.py` after tests.
    * Add `-i` to run `./run_interpreter.py` after tests. 
