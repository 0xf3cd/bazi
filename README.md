# Bazi Projects
> 排盘、五行、十神、纳音、刑冲破害、合会

## Instructions
* Python version should be >= 3.9
* Install requirements by `python -m pip install -r Requirements.txt`
* Run linter: `ruff check .`
* Run static type checker: `mypy .`
* Run tests: `./run_tests.py`
  * By default:
    * hkodata tests and slow tests won't run;
    * `ruff` and `mypy` won't run;
    * demo and interpreter won't run.
  * Arguments:
    * Add `-hko` to also run hkodata tests, like: `./run_tests.py -hko`.
    * Add `-s` to also run slow tests, like: `./run_tests.py -s`.
    * Add `-v` to show verbose info during testing.
    * Add `-k <expression>` to specify the test(s) to run, this argument will be passed to `pytest`.
    * Add `-c` to collect coverage data during testing. This also produces a coverage report in `./covhtml`.
    * Add `-l` to run the linter after tests.
    * Add `-mypy` to run mypy static type checker after tests.
    * Add `-d` to run `./run_demo.py` after tests.
    * Add `-i` to run `./run_interpreter.py` after tests. 
