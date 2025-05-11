import asyncio
import pytest

from aio_process_pool.worker import Worker

def foo(x):
    from time import sleep
    sleep(x)
    return x

@pytest.mark.asyncio
async def test_worker_basics():
    worker = Worker()
    assert await worker.run(foo, 0.1) == (0.1, None)
    assert await worker.run(foo, 0.2) == (0.2, None)
    worker.shutdown()

@pytest.mark.asyncio
async def test_worker_parallel():
    worker = Worker()
    futures = [worker.run(foo, 0.1), worker.run(foo, 0.2), worker.run(foo, 0.3)]

    results = await asyncio.gather(*futures, return_exceptions=True)
    assert results == [(0.1, None), (0.2, None), (0.3, None)]
    worker.shutdown()

async def delayed_shutdown(worker, delay, kill):
    await asyncio.sleep(delay)
    worker.shutdown(kill=kill)

@pytest.mark.asyncio
async def test_worker_shutdown():
    worker = Worker()
    futures = [worker.run(foo, 1), worker.run(foo, 2), worker.run(foo, 3)]
    loop = asyncio.get_event_loop()
    loop.call_soon(worker.shutdown)
    results = await asyncio.gather(*futures, return_exceptions=True)

    for r in results:
        assert isinstance(r, asyncio.CancelledError)

@pytest.mark.asyncio
async def test_worker_shutdown2():
    worker = Worker()
    futures = [worker.run(foo, 1), worker.run(foo, 2), worker.run(foo, 3)]
    futures += [delayed_shutdown(worker, 0.2, True)]
    results = await asyncio.gather(*futures, return_exceptions=True)
    for r in results[:-1]:
        assert isinstance(r, asyncio.CancelledError)
    assert results[-1] == None

@pytest.mark.asyncio
async def test_worker_shutdown3():
    worker = Worker()
    futures = [worker.run(foo, 1), worker.run(foo, 2), worker.run(foo, 3)]
    futures += [delayed_shutdown(worker, 0.2, False)]
    results = await asyncio.gather(*futures, return_exceptions=True)
    assert results[0] == (1, None)
    for r in results[1:-1]:
        assert isinstance(r, asyncio.CancelledError)
    assert results[-1] == None

