"""
MemoryKeyValueStore

Class for a KeyValueStore that is stored in local memory.

The value is stored with an expiration time, which is checked on 
retrieval to make sure it is not expired.

A heap of (exptime, key) tuples is maintained to track of keys
eligible for expiration; it is checked on each store() call.

"""
import asyncio
import time

from .key_value_store import KeyValueStore


ONE_WEEK_IN_SECONDS = 60 * 60 * 24 * 7



class MemoryKeyValueStore(KeyValueStore):
    """
    A KeyValueStore that is stored in local memory.
    """

    # does not accept null keys or values

    def __init__(self, default_exptime_seconds=ONE_WEEK_IN_SECONDS):
        """
        Constructor - takes default cache expiration time (in seconds) as optional argument.
        """

        # maps key to (string,expiration_time) tuple
        self.key_to_str_and_exptime = {}

        # expiration time to use if none was supplied
        self.default_exptime_seconds = default_exptime_seconds

        # used to clear expired keys
        self.expiration_heap = []

        # async lock
        self.lock = asyncio.Lock()


    @staticmethod
    def _isexpired(exptime):
        """
        Helper method - check if the given time has passed
        """
        return exptime < time.time()


    async def _delete_key(self, key):
        """
        Removes key from cache.
        Only call from a method inside an async lock.
        """
        # note this doesn't remove anything from self.expiration_heap;
        # that's OK, it will get removed later
        str_and_exptime = self.key_to_str_and_exptime.pop(key)
        if str_and_exptime:
            return True


    async def _check_one_expiration(self):
        """
        Removes a key eligible for expiration (if any are).
        Returns True if one was removed.
        """
        if self.expiration_heap:
            exptime, key = self.expiration_heap[0]
            if self._isexpired(exptime):
                heappop(self.expiration_heap)
                await self._delete_key(key)
                return True

        return False


    async def _check_expiration(self):
        """
        Removes some number of keys eligible for expiration (if any are).
        For now up to two are removed on each call.
        """
        key_deleted = await self._check_one_expiration()
        if key_deleted:
            await self._check_one_expiration()


    async def lookup(self, key):
        """
        Returns the URL associated with the given key, or None if not found.
        """

        # use an async lock to handle multiple updates properly
        async with self.lock:
            return await self._lookup(key)


    async def _lookup(self, key):
        """
        Returns the URL associated with the given key, or None if not found.
        """
        str_and_exptime = await self._lookup_with_exptime(key)
        if str_and_exptime:
            # only returns the value, not the expiration time
            return str_and_exptime[0]  # return the string value


    async def _lookup_with_exptime(self, key):
        """
        Looks up key and returns corresponding value and expiration time.
        """
        # return value and expiration time if found
        str_and_exptime = self.key_to_str_and_exptime.get(key)
        if str_and_exptime:
            stringval, exptime = str_and_exptime

            # make sure the key isn't expired
            if self._isexpired(exptime):
                # delete so future callers won't deal with this
                await self._delete_key(key)
            else:
                return stringval, exptime


    async def store(self, key, stringval, exptime_seconds=None):
        """
        Stores the key with the given string value and expiration.
        It expires in exptime seconds (default_exptime_seconds if not supplied).
        """

        # use an async lock to handle multiple updates properly
        async with self.lock:
            return await self._store(key, stringval, exptime_seconds)


    async def _store(self, key, stringval, exptime_seconds=None):
        """
        Stores the key with the given string value.
        It expires in exptime_seconds seconds (default_exptime_seconds if not supplied).
        Returns True on success, False if the key exists with a different value.
        Changes to expiration on an existing key are ignored.
        Raises an exception if called with an invalid key or value.
        """
        if not key:
            # don't allow None or "" for a key
            raise KeyError("null key for cache")

        if stringval is None:
            raise ValueError("null value for cache")

        if not exptime_seconds:
            exptime_seconds = self.default_exptime_seconds
        elif self._isexpired(time.time() + exptime_seconds):
            raise KeyError("cache expiration time has passed")

        # do some garbage collection of expired keys
        await self._check_expiration()

        # check if key exists
        str_and_exptime = await self._lookup_with_exptime(key)
        if str_and_exptime:
            # found the key
            existing_stringval, _existing_exptime = str_and_exptime
            if existing_stringval == stringval:
                # the key already exists with this value
                return True  # no need to do anything else

            else:
                # the key exists with a different value; don't update
                return False

        # doesn't exist, do the insert
        self.key_to_str_and_exptime[key] = (stringval, exptime_seconds + time.time())
        return True


async def test():
    """
    Tests
    """
    cache = MemoryKeyValueStore()
    val = await cache.lookup("test")
    print("Lookup non-existent key: val=%s (expect None)" % val)

    val = await cache.store("test1", "abc")
    print("store test1:  val=%s" % val)

    val = await cache.lookup("test1")
    print("lookup test1: val=%s" % val)

    val = await cache.store("test2", "efgh")
    print("store test2:  val=%s" % val)

    val = await cache.lookup("test2")
    print("lookup test2: val=%s" % val)

    val = await cache.store("test3", "efgh2")
    print("store test3:  val=%s" % val)

    # this should fail, key already exists
    val = await cache.store("test3", "efgh3")
    print("store different test3: val=%s (expect False)" % val)

    # test for expiration
    val = await cache.store("test4", "ijkl", 2)
    print("store test4:  val=%s" % val)

    val = await cache.lookup("test4")
    print("lookup test4: val=%s" % val)

    await asyncio.sleep(3)

    val = await cache.lookup("test4")
    print("lookup test4 after sleep: val=%s (expect None)" % val)

    try:
        print("Test to catch exception for None value...")
        val = await cache.store("test3", None)
    except KeyError as keyexc:
        print("Caught key error '%s'" % keyexc)
    except ValueError as valexc:
        print("Caught value error '%s'" % valexc)


if __name__ == "__main__":
    asyncio.run(test())
