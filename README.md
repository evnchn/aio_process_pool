# aio_process_pool

[![PyPI - Version](https://img.shields.io/pypi/v/aio_process_pool.svg)](https://pypi.org/project/aio_process_pool)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aio_process_pool.svg)](https://pypi.org/project/aio_process_pool)

-----

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install aio_process_pool
```

## Usage

```python
from aio_process_pool import AsyncProcessPool


def foo(x):
    return x


# Note:
# - the process pool must be initialize AFTER all functions that are supposed
#   to be called are defined
# - it's not save to initialize a process pool from a multithreaded process
#   because it's based on `os.fork` / `multiprocessing.Process`
pool = AsyncProcessPool()


async def using_run():
    return await pool.run(foo, 72)


async def using_submit():
    future = pool.submit(foo, 73)
    return await future


async def using_executor():
    from functools import partial

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(pool, partial(foo, 74))
```

## License

`aio_process_pool` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
