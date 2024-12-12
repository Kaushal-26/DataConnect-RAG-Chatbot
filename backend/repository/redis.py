from typing import Optional, Union

import redis.asyncio as redis
from kombu.utils.url import safequote


class RedisRepository:
    """
    A repository class for interacting with Redis using async methods.

    Provides methods for adding, retrieving, and deleting key-value pairs in Redis.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize the Redis client."""

        self._host = safequote(host)
        self._port = port
        self._db = db
        self.redis_client = redis.Redis(host=self._host, port=self._port, db=self._db)

    async def add(self, key: str, value: Union[str, bytes], expire: Optional[int] = None):
        """Add a key-value pair to Redis."""

        await self.redis_client.set(key, value)
        if expire:
            await self.redis_client.expire(key, expire)

    async def get(self, key: str) -> Optional[str]:
        """Retrieve a value from Redis by key."""

        return await self.redis_client.get(key)

    async def delete(self, key: str):
        """Delete a key from Redis."""

        await self.redis_client.delete(key)

    async def close(self):
        """Close the Redis connection."""

        await self.redis_client.close()
