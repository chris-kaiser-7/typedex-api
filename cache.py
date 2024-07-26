from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=60*60)

async def init_cache():
    pass

async def get_assistant(assistant):
    return cache.get(assistant)

async def set_assistant(assistant, data):
    cache[assistant] = data