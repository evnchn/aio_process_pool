# asyncprocesspool

[![PyPI - Version](https://img.shields.io/pypi/v/asyncprocesspool.svg)](https://pypi.org/project/asyncprocesspool)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/asyncprocesspool.svg)](https://pypi.org/project/asyncprocesspool)

-----

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install asyncprocesspool
```

## Usage

```python
from asyncprocesspool import AsyncProcessPool


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

`asyncprocesspool` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
