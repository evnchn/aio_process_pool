# aio_process_pool

[![PyPI - Version](https://img.shields.io/pypi/v/aio_process_pool.svg)](https://pypi.org/project/aio_process_pool)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aio_process_pool.svg)](https://pypi.org/project/aio_process_pool)

-----

A simple async, android compatible process pool and a (mostly) `concurrent.futures.Executor` / `ProcessPoolExecutor` compliant `Executor`.

Not thread safe.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Demo](#demo)
- [Executor](#executor)
- [License](#license)

## Installation

```console
pip install aio_process_pool
```

## Usage

```python
import asyncio

from aio_process_pool import ProcessPool, Executor

def foo(x=7):
    return x

# sync
executor = Executor()
assert executor.map(foo, [1, 2, 3]) == [1, 2, 3]
executor.shutdown()

# async
async def example():
    pool = ProcessPool()
    executor = Executor()

    # run a function in the pool
    assert await pool.run(foo, 2) == 2
    # map using a process pool
    assert await pool.map(foo, [1, 2, 3]) == [1, 2, 3]

    # use the executor with run_in_executor from asyncio
    loop = asyncio.get_event_loop()
    assert await loop.run_in_executor(executor, foo) == 7

    # map again
    assert await executor.map_async(foo, [1, 2, 3]) == [1, 2, 3]

    pool.shutdown()
    await executor.shutdown_async()

asyncio.run(example())
```

## Executor

The `Executor` is mostly `concurrent.futures.Executor` compliant and can therefor be used as a replacement for `concurrent.futures.ProcessPoolExecutor`.

It is possible to monkey patch this executor into an environment:

```python
import concurrent.futures, aio_process_pool
concurrent.futures.ProcessPoolExecutor = aio_process_pool.Executor
```

This is very helpful if you have code using a `ProcessPoolExecutor` and want to run it on android (with buildozer).

### shutdown behaviour / deadlock under certain conditions

Since this package is based on asyncio I was not able to implement the specified shutdown behaviour under certain conditions.

If there are tasks pending and the `wait` parameter is `True` `shutdown` is supposed to block until all pending tasks are done. Since the execution of those task depends on the event loop this produces a deadlock.

The handle this situation this implementation raises a `RuntimeError` in that case instead of deadlocking.

If possible use `shutdown_async` instead. `shutdown_async` should behave `concurrent.futures.Executor` compliant.


### map from within the loop

Since `map` is -- according to `concurrent.futures.Executor` -- supposed to be a sync function it uses `asyncio.new_event_loop` to get a new event loop and runs `map_async` in that loop. This is only possible if we're not inside a loop already. This is somehow not `concurrent.futures.Executor` compliant.

If possible use `map_async` instead.

If anyone knows how to improve this.....

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
