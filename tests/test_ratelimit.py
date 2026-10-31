import pytest
from app.services.ratelimit import hit
from fakeredis import FakeAsyncRedis
class FakePipe:
    def __init__(self, store):
        self.store,self.ops = store, []

    async def __aenter__(self):
        return self
    async def __aexit__(self, *exc):
        return False
    
    async def incr(self, key):
        self.ops.append(("incr", key))
        return self
    def expire(self, key, seconds):
        self.ops.append(("expire", key))
        return self
    async def execute(self):
        out = []
        for op, key in self.ops:
            if op == "incr":
                self.store[key] = self.store.get(key, 0) + 1
                out.append(self.store[key])
            else:
                out.append(True)
        return out

# class FakeRedis:
#     def __init__(self):
#         self.store = []
        
#     def pipeline(self):
#         return FakePipe(self.store)



class BrokenRedis:
    def pipeline(self):
        raise ConnectionError("down")

@pytest.mark.asyncio
async def test_blocks_after_limitt():
    r = FakeAsyncRedis()
    results = [await hit(r, "k", 3, 60, now=1000.0) for _ in range(5)]
    assert [ok for ok, _ in results] == [True, True, True, False, False]

@pytest.mark.asyncio
async def test_new_window_reset():
    r = FakeAsyncRedis()
    for _ in range(4):
        await hit(r, "k", 3, 60, now=1000) 
    ok, _ = await hit(r, "k", 3, 60, now=1060.0)
    assert ok

@pytest.mark.asyncio
async def test_retry_after_is_within_window():
    r = FakeAsyncRedis()
    _, retry = await hit(r, "k", 3, 60, now=1030.0)
    assert 0 < retry <= 60

@pytest.mark.asyncio
async def test_fails_open_when_redis_is_down():
    ok, _ = await hit(BrokenRedis(), "k", 1, 60)
    assert ok



