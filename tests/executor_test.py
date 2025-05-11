import asyncio
import pytest

from functools import partial

from aio_process_pool import Executor
from .pool_test import fib

fib32 = 2178309 # fib(32)

def test_shutdown_trivial():
    exe = Executor()
    exe.shutdown()
    assert exe.is_shutdown()

@pytest.mark.asyncio
async def test_shutdown_trivial_async():
    exe = Executor()
    await exe.shutdown_async()
    assert exe.is_shutdown()

@pytest.mark.asyncio
@pytest.mark.parametrize("wait", (True, False))
@pytest.mark.parametrize("cancel_futures", (True, False))
async def test_shutdown_parameters_async(wait, cancel_futures):
    exe = Executor(max_workers=2)
    loop = asyncio.get_event_loop()

    # start "long" running jobs
    futures = [loop.run_in_executor(exe, partial(fib, 32)) for _ in range(5)]
    futures += [exe.shutdown_async(wait=wait, cancel_futures=cancel_futures)]

    results = await asyncio.gather(*futures, return_exceptions=True)

    if cancel_futures:
        assert results[0] == results[1] == fib32
        for i in [2, 3, 4]:
            assert isinstance(results[i], asyncio.CancelledError)
        assert results[5] is None
    else:
        assert results == [fib32] * 5 + [None]

    assert exe.is_shutdown()

@pytest.mark.asyncio
@pytest.mark.parametrize("wait", (True, False))
@pytest.mark.parametrize("cancel_futures", (True, False))
async def test_shutdown_parameters_sync(wait, cancel_futures):
    exe = Executor(max_workers=2)
    loop = asyncio.get_event_loop()

    # start "long" running jobs
    futures = [loop.run_in_executor(exe, partial(fib, 32)) for _ in range(5)]

    if not wait:
        exe.shutdown(wait, cancel_futures=cancel_futures)
    else:
        with pytest.raises(RuntimeError):
            exe.shutdown(wait, cancel_futures=cancel_futures)

    results = await asyncio.gather(*futures, return_exceptions=True)

    if cancel_futures:
        for i in range(5):
            assert isinstance(results[i], asyncio.CancelledError)
    else:
        for i in range(5):
            assert results[i] == fib32

    assert exe.is_shutdown()
