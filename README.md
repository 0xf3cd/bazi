# Bazi Projects
> 排盘、五行、十神、纳音、刑冲破害、合会

## Instructions
* Install requirements by `python -m pip install -r Requirements.txt`
* Run linter: `ruff check .`
* Run tests: `./run_tests.py`
  * By default, hkodata tests and slow tests won't be running.
  * Add `-hko` argument to also run hkodata tests, like: `./run_tests.py -hko`.
  * Add `-s` argument to also run slow tests, like: `./run_tests.py -s`.
* Get test coverage: `./run_tests.py -c`
