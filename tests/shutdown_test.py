import asyncio
import pytest

from functools import partial

from aio_process_pool import Executor
from .pool_test import fib

fib33 = 3524578 # fib(33)

def test_shutdown_trivial():
    exe = Executor()
    exe.shutdown()
    assert exe.is_shutdown()

@pytest.mark.asyncio
async def test_shutdown_trivial_async():
    exe = Executor()
    await exe.shutdown_async()
    assert exe.is_shutdown()

async def shutdown_test(wait, cancel_futures):
    exe = Executor(max_workers=2)
    loop = asyncio.get_event_loop()

    # start long running jobs
    futures = [loop.run_in_executor(exe, partial(fib, 33)) for _ in range(5)]
    futures += [exe.shutdown_async(wait=wait, cancel_futures=cancel_futures)]

    return exe, await asyncio.gather(*futures, return_exceptions=True)

def check_cancelled_shutdown_resutls(results):
    assert results[0] == fib33
    assert results[1] == fib33
    assert isinstance(results[2], asyncio.CancelledError)
    assert isinstance(results[3], asyncio.CancelledError)
    assert isinstance(results[4], asyncio.CancelledError)
    assert results[5] is None

@pytest.mark.asyncio
async def test_shutdown_cancel_true():
    exe, results = await shutdown_test(True, True)

    check_cancelled_shutdown_resutls(results)
    assert exe.is_shutdown()

@pytest.mark.asyncio
async def test_shutdown_cancel_true_wait_false():
    exe, results = await shutdown_test(False, True)

    check_cancelled_shutdown_resutls(results)
    assert exe.is_shutdown()

@pytest.mark.asyncio
async def test_shutdown_cancel_false():
    exe, results = await shutdown_test(True, False)

    assert results == [fib33] * 5 + [None]
    assert exe.is_shutdown()

@pytest.mark.asyncio
async def test_shutdown_cancel_false_wait_false():
    exe, results = await shutdown_test(False, False)

    assert results == [fib33] * 5 + [None]
    assert exe.is_shutdown()
