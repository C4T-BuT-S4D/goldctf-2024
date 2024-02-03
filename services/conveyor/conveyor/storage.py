from typing import Optional, cast
from uuid import UUID

import redis


class Repository:
    def __init__(self, redis_url: str, ttl_seconds: int):
        self.ttl = ttl_seconds
        self.redis = cast(
            redis.Redis,
            redis.Redis.from_url(redis_url, protocol=3, decode_responses=True),
        )
        self.redis.ping()

    def save_account_creds(self, account_id: UUID, access_key: bytes) -> bool:
        """
        Returns true if access_key wasn't previously bound to any account_id.
        """

        result = self.redis.set(
            Repository.__credentials_key(access_key),
            str(account_id),
            ex=self.ttl,
            nx=True,
        )

        return result == True

    def authenticate_by_creds(self, access_key: bytes) -> Optional[UUID]:
        """
        Returns the parsed account ID associated with this access_key, or None.
        """

        account_id = cast(
            Optional[str], self.redis.get(Repository.__credentials_key(access_key))
        )
        if account_id is None:
            return None

        return UUID(hex=account_id)

    @staticmethod
    def __credentials_key(key: bytes) -> str:
        return f"credentials:{key.hex()}"
