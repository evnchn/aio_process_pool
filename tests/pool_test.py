import asyncio
import pytest


from aio_process_pool import ProcessPool, SubprocessException

def fib(n):
    assert n >= 0
    if n == 0: return 0
    if n <= 2: return 1
    return fib(n-1) + fib(n-2)

def raise_exception(_=1):
    assert False

first_30_fib_numbers = [fib(x) for x in range(30)]

@pytest.mark.asyncio
async def test_run():
    pool = ProcessPool()
    assert await pool.run(fib, 6) == 8
    assert await pool.map(fib, [1, 2, 3]) == [1, 1, 2]
    pool.shutdown()

@pytest.mark.asyncio
async def test_exception():
    pool = ProcessPool()
    with pytest.raises(SubprocessException):
        await pool.run(raise_exception)
    pool.shutdown()

def test_0_worker():
    with pytest.raises(ValueError):
        _ = ProcessPool(0)
    assert True

tpi_pool = ProcessPool()
def blub(): return True

@pytest.mark.asyncio
async def test_pool_init_before_function_def():
    assert await tpi_pool.run(blub)

def foo(x):
    from time import sleep
    sleep(x)
    return x

async def delayed_shutdown(pool, delay, kill=False):
    await asyncio.sleep(delay)
    pool.shutdown(kill=kill)

@pytest.mark.asyncio
async def test_pool_early_shutdown():
    pool = ProcessPool()
    futures = [pool.run(foo, 1), pool.run(foo, 2), pool.run(foo, 3)]

    loop = asyncio.get_event_loop()
    loop.call_soon(pool.shutdown)

    results = await asyncio.gather(*futures, return_exceptions=True)

    for r in results:
        assert isinstance(r, asyncio.CancelledError)

@pytest.mark.asyncio
@pytest.mark.parametrize("kill", (True, False))
async def test_pool_delayed_shutdown(kill):
    pool = ProcessPool(1)

    futures = [pool.run(foo, 0.3), pool.run(foo, 2), pool.run(foo, 3)]
    futures += [delayed_shutdown(pool, 0.1, kill)]

    results = await asyncio.gather(*futures, return_exceptions=True)

    if not kill:
        assert results[0] == 0.3
        for r in results[1:-1]:
            assert isinstance(r, asyncio.CancelledError)
        assert results[-1] == None
    else:
        for r in results[:-1]:
            assert isinstance(r, asyncio.CancelledError)
        assert results[-1] == None
