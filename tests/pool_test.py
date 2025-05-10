import asyncio
import pytest

from functools import partial

from aio_process_pool import ProcessPool, Executor

def fib(n):
    assert n >= 0
    if n == 0: return 0
    if n <= 2: return 1
    return fib(n-1) + fib(n-2)

first_30_fib_numbers = [fib(x) for x in range(30)]

@pytest.mark.asyncio
async def test_run():
    pool = ProcessPool()
    assert await pool.run(fib, 6) == 8
    pool.shutdown()

@pytest.mark.asyncio
async def test_executor():
    exe = Executor()
    loop = asyncio.get_event_loop()

    futures = [loop.run_in_executor(exe, partial(fib, i)) for i in range(30)]
    assert await asyncio.gather(*futures) == first_30_fib_numbers

    await exe.shutdown_async()

@pytest.mark.asyncio
async def test_async_map():
    exe = Executor()
    assert await exe.map_async(fib, range(30)) == first_30_fib_numbers
    await exe.shutdown_async()

def test_map():
    exe = Executor()
    assert exe.map(fib, range(30)) == first_30_fib_numbers
    exe.shutdown()

def test_context_manager():
    with Executor() as exe:
        assert exe.map(fib, range(30)) == first_30_fib_numbers

@pytest.mark.asyncio
async def test_async_context_manager():
    async with Executor() as exe:
        assert await exe.map_async(fib, range(30)) == first_30_fib_numbers

