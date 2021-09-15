"""
URLMapStore

Class that associates a shortname with a URL.
"""
import asyncio
import random
import string
import time


from .memory_key_value_store import MemoryKeyValueStore


class URLMapStore:
    """
    Associates a shortname with a URL.
    Association expires after a specified amount of time.
    """
    # default length of URL shortnames
    SHORTNAME_LEN = 8

    # upper and lowercase letters
    letters = string.ascii_lowercase + string.ascii_uppercase
    num_letters = len(letters)


    def __init__(self, string_cache):
        """
        Constructor - initial with cache implementation
        """
        self.cache = string_cache


    @classmethod
    def _generate_shortname(cls):
        """
        Generates a random shortname
        """
        return ''.join([cls.letters[random.randrange(0, cls.num_letters)] for idx in range(0, cls.SHORTNAME_LEN)])


    async def store(self, url, expiration_time=None, user_shortname=None):
        """
        Given a URL, returns a shortname. The user can supply their own shortname.
        """
        # returns shortname used

        shortname = user_shortname or self._generate_shortname()

        tries = 0
        MAX_TRIES = 10

        # keep trying different shortnames in case one is used
        while True:
            tries += 1
            result = await self.cache.store(shortname, url, expiration_time)
            if result:
                # successfully stored
                break
            else:
                # store failed because key exists with different value
                if shortname == user_shortname:
                    raise KeyError("User shortname exists with different URL")

                elif tries <= MAX_TRIES:
                    shortname = self._generate_shortname()
                else:
                    raise KeyError("Unable to generate shortname")

        return shortname


    async def lookup(self, shortname):
        """
        Looks up the URL associated with the given shortname
        """
        return await self.cache.lookup(shortname)


async def test():
    """
    Some tests
    """
    str_cache = MemoryKeyValueStore()
    cache = URLMapStore(str_cache)

    shortname1 = await cache.store("http://google.com")
    print("stored URL with value %s" % shortname1)

    val = await cache.lookup("abc123")
    print("val=%s" % val)

    val = await cache.lookup(shortname1)
    print("val=%s" % val)

    shortname2 = await cache.store("http://yahoo.com")
    print("stored URL with value %s" % shortname2)


    val = await cache.lookup(shortname2)
    print("val=%s" % val)

    val = await cache.lookup(shortname1)
    print("val=%s" % val)


if __name__ == "__main__":
    asyncio.run(test())

