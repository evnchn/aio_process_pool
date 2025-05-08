# aio_process_pool

[![PyPI - Version](https://img.shields.io/pypi/v/aio_process_pool.svg)](https://pypi.org/project/aio_process_pool)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aio_process_pool.svg)](https://pypi.org/project/aio_process_pool)

-----

Tihs pacakage provides an async, (hopefully soon fully) `concurrent.futures.Executor` compliant, android compatible process pool.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Demo](#demo)
- [License](#license)

## Installation

```console
pip install aio_process_pool
```

## Usage

```python
from aio_process_pool import ProcessPool, Executor

def foo(x):
    return x

# Note:
# - the process pool must be initialize AFTER all functions that are supposed
#   to be called are defined
# - it's not save to initialize a process pool from a multithreaded process
#   because it's based on `os.fork` / `multiprocessing.Process`

pool = ProcessPool()
executor = Executor()

async def pool_example():
    return await pool.run(foo, 72)

async def executor_example():
    from functools import partial

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(foo, 74))
```

## Demo

```python
import asyncio
from aio_process_pool import Executor

def fib(n):
    if n <= 2: return 1
    return fib(n-1) + fib(n-2)

def fib_wrapper(n):
    print(f"fib({n}) = .....")
    result = fib(n)
    print(f"fib({n}) = {result}")

async def watch_htop_and_output_while_execution():
    pool = Executor()
    await pool.map_async(fib_wrapper, range(45))

asyncio.run(watch_htop_and_output_while_execution())
```

## License

`aio_process_pool` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
