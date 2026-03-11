import redis
import os


class RedisConnection:
    def __init__(self, url=os.getenv("REDIS_URL")):
        try:
            self.connection = redis.Redis.from_url(url, decode_responses=True)
        except Exception as e:
            print(f"Redis init conn error {e}")

    def get_connection(self):
        return self.connection

    def close_connection(self):
        self.connection.close()

    def set(self, key, value, expire=int(os.getenv("REDIS_EXPIRE_TIME"))):
        return self.connection.set(key, value, ex=expire)

    def get(self, key):
        return self.connection.get(key)

    def delete(self, key):
        return self.connection.delete(key)

    def incr(self, key, amount=1):
        return self.connection.incr(key, amount)

    # clear partial cache
    def clear_partial_cache(self, key):
        for k in self.connection.scan_iter(f"{key}*"):
            self.connection.delete(k)

    def pipeline(self):
        return self.connection.pipeline()


redis_conn = RedisConnection()
