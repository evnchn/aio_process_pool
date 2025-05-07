import asyncio
import pytest

from functools import partial

from aio_process_pool import AsyncProcessPool

def fib(n):
    assert n >= 0
    if n == 0: return 0
    if n <= 2: return 1
    return fib(n-1) + fib(n-2)

@pytest.mark.asyncio
async def test_run():
    pool = AsyncProcessPool()
    assert await pool.run(fib, 6) == 8

@pytest.mark.asyncio
async def test_executor():
    pool = AsyncProcessPool()

    loop = asyncio.get_event_loop()

    futures = [loop.run_in_executor(pool, partial(fib, 35-i)) for i in range(7)]
    results = await asyncio.gather(*futures)

    assert results == [9227465, 5702887, 3524578, 2178309, 1346269, 832040, 514229]
