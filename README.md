# aio_process_pool

[![PyPI - Version](https://img.shields.io/pypi/v/aio_process_pool.svg)](https://pypi.org/project/aio_process_pool)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aio_process_pool.svg)](https://pypi.org/project/aio_process_pool)

-----

A simple async, android compatible (,not thread safe)  process pool implementation including a (mostly) `concurrent.futures.Executor` / `concurrent.futures.ProcessPoolExecutor` compliant `Executor`.

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

pool = ProcessPool()
executor = Executor()

def foo(x):
    return x

async def pool_example():
    return await pool.run(foo, 72)

async def executor_example():
    from functools import partial

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(foo, 74))

pool.shutdown()
executor.shutdown()
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
    exe = Executor()
    await exe.map_async(fib_wrapper, range(45))
    exe.shutdown()

asyncio.run(watch_htop_and_output_while_execution())
```

## License

`aio_process_pool` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
