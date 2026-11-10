import time
from datetime import datetime

import motor.motor_asyncio
from pymongo.errors import DuplicateKeyError

from info import DATABASE_NAME, DATABASE_URI


class Database:

    def __init__(self, uri, database_name):
        # Fail fast (8s) instead of hanging 30s when Mongo is unreachable
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri, serverSelectionTimeoutMS=8000)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.stats = self.db.stats
        self.cool = self.db.cooldowns
        self.settings = self.db.settings
        self.bans = self.db.bans
        self._mem_cool: dict = {}      # fallback if MongoDB is down

    async def ping(self):
        await self._client.admin.command("ping")

    async def ensure_indexes(self):
        # cooldown rows delete themselves 10 minutes after the last use
        await self.cool.create_index("at", expireAfterSeconds=600)

    # ---- users ----
    async def add_user(self, id, name, username=None):
        await self.col.update_one(
            {"id": int(id)},
            {"$setOnInsert": {"id": int(id), "name": name, "username": username,
                              "joined": time.time(), "links": 0}},
            upsert=True,
        )

    async def touch_user(self, id, name, username=None):
        await self.col.update_one({"id": int(id)},
                                  {"$set": {"name": name, "username": username, "last_seen": time.time()}})

    async def get_user(self, id):
        return await self.col.find_one({"id": int(id)})

    async def inc_user_links(self, id):
        try:
            await self.col.update_one({"id": int(id)}, {"$inc": {"links": 1}})
        except Exception:
            pass

    async def recent_users(self, n=10):
        return await self.col.find({}).sort("joined", -1).limit(n).to_list(length=n)

    # ---- bans ----
    async def add_ban(self, id, reason="", by=0):
        await self.bans.update_one({"_id": int(id)},
                                   {"$set": {"reason": reason, "by": int(by), "at": time.time()}}, upsert=True)

    async def remove_ban(self, id) -> bool:
        r = await self.bans.delete_one({"_id": int(id)})
        return r.deleted_count > 0

    async def get_bans(self):
        return await self.bans.find({}).to_list(length=500)

    async def is_user_exist(self, id):
        return bool(await self.col.find_one({"id": int(id)}))

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"id": int(user_id)})

    # ---- 1 link per N seconds per user ----
    async def try_acquire(self, user_id: int, seconds: int):
        """Atomic. Returns (allowed, seconds_to_wait).
        Only one request per user can win, even if they send 10 files at the same instant."""
        now = time.time()
        uid = int(user_id)
        try:
            await self.cool.update_one(
                {"_id": uid, "ts": {"$lte": now - seconds}},
                {"$set": {"ts": now, "at": datetime.utcnow()}},
                upsert=True,
            )
            return True, 0
        except DuplicateKeyError:
            doc = await self.cool.find_one({"_id": uid})
            wait = int(seconds - (now - doc["ts"])) + 1 if doc else 1
            return False, max(1, wait)
        except Exception:
            # DB problem -> in-memory rule so the limit still works
            last = self._mem_cool.get(uid, 0)
            if now - last < seconds:
                return False, int(seconds - (now - last)) + 1
            self._mem_cool[uid] = now
            if len(self._mem_cool) > 5000:
                self._mem_cool.clear()
            return True, 0

    async def release(self, user_id: int):
        """Give the slot back (link creation failed, user should not be punished)."""
        uid = int(user_id)
        self._mem_cool.pop(uid, None)
        try:
            await self.cool.delete_one({"_id": uid})
        except Exception:
            pass

    # ---- counters ----
    async def inc_stat(self, name: str, amount: int = 1):
        try:
            await self.stats.update_one({"_id": name}, {"$inc": {"value": amount}}, upsert=True)
        except Exception:
            pass

    async def get_stat(self, name: str) -> int:
        try:
            doc = await self.stats.find_one({"_id": name})
            return int(doc["value"]) if doc else 0
        except Exception:
            return 0

    # ---- small key/value settings (e.g. start image set with /setstart) ----
    async def set_setting(self, key: str, value):
        await self.settings.update_one({"_id": key}, {"$set": {"value": value}}, upsert=True)

    async def get_setting(self, key: str, default=None):
        try:
            doc = await self.settings.find_one({"_id": key})
            return doc["value"] if doc else default
        except Exception:
            return default


db = Database(DATABASE_URI, DATABASE_NAME)
