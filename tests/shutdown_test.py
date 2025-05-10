import asyncio
import pytest
import time

from functools import partial
from threading import Thread

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

    def shutdown_wrapper(wait, cancel_futures):
        exe.shutdown(wait, cancel_futures=cancel_futures)

    shutdown_thread = None
    if wait:
        # blocking sync shutdown in a separate thread
        shutdown_thread = Thread(target=shutdown_wrapper,
                                 args=(wait, cancel_futures))
        shutdown_thread.start()

        # test whether it's blocking
        time.sleep(0.1)
        assert shutdown_thread.is_alive()
    else:
        exe.shutdown(wait, cancel_futures=cancel_futures)

    results = await asyncio.gather(*futures, return_exceptions=True)

    if cancel_futures:
        for i in range(5):
            assert isinstance(results[i], asyncio.CancelledError)
    else:
        for i in range(5):
            assert results[i] == fib32

    if wait:
        assert shutdown_thread
        shutdown_thread.join()

    assert exe.is_shutdown()
