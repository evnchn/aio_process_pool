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

@pytest.mark.asyncio
async def test_shutdown_cancel_true():
    exe = Executor(max_workers=2)
    loop = asyncio.get_event_loop()

    # start long running jobs
    futures = [loop.run_in_executor(exe, partial(fib, 33)) for _ in range(5)]
    futures += [exe.shutdown_async(wait=True, cancel_futures=True)]

    results = await asyncio.gather(*futures, return_exceptions=True)

    fib33 = 3524578 # fib(33)
    assert results[0] == fib33
    assert results[1] == fib33
    assert isinstance(results[2], asyncio.CancelledError)
    assert isinstance(results[3], asyncio.CancelledError)
    assert isinstance(results[4], asyncio.CancelledError)
    assert results[5] is None

@pytest.mark.asyncio
async def test_shutdown_cancel_true_wait_false():
    exe = Executor(max_workers=2)
    loop = asyncio.get_event_loop()

    # start long running jobs
    futures = [loop.run_in_executor(exe, partial(fib, 33)) for _ in range(5)]
    futures += [exe.shutdown_async(wait=False, cancel_futures=True)]

    results = await asyncio.gather(*futures, return_exceptions=True)

    fib33 = 3524578 # fib(33)
    assert results[0] == fib33
    assert results[1] == fib33
    assert isinstance(results[2], asyncio.CancelledError)
    assert isinstance(results[3], asyncio.CancelledError)
    assert isinstance(results[4], asyncio.CancelledError)
    assert results[5] is None

@pytest.mark.asyncio
async def test_shutdown_cancel_false():
    exe = Executor(max_workers=2)
    loop = asyncio.get_event_loop()

    # start long running jobs
    futures = [loop.run_in_executor(exe, partial(fib, 33)) for _ in range(5)]
    futures += [exe.shutdown_async(wait=True, cancel_futures=False)]

    results = await asyncio.gather(*futures, return_exceptions=True)

    fib33 = 3524578 # fib(33)
    assert results[0] == fib33
    assert results[1] == fib33
    assert results[2] == fib33
    assert results[3] == fib33
    assert results[4] == fib33
    assert results[5] is None

@pytest.mark.asyncio
async def test_shutdown_cancel_false_wait_false():
    exe = Executor(max_workers=2)
    loop = asyncio.get_event_loop()

    # start long running jobs
    futures = [loop.run_in_executor(exe, partial(fib, 33)) for _ in range(5)]
    futures += [exe.shutdown_async(wait=False, cancel_futures=False)]

    results = await asyncio.gather(*futures, return_exceptions=True)

    fib33 = 3524578 # fib(33)
    assert results[0] == fib33
    assert results[1] == fib33
    assert results[2] == fib33
    assert results[3] == fib33
    assert results[4] == fib33
    assert results[5] is None
