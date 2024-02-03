from typing import cast

import redis


class Repository:
    def __init__(self, redis_url: str):
        self.redis = cast(redis.Redis, redis.Redis.from_url(redis_url))
        self.redis.ping()
