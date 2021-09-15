"""
KeyValueStore

Abstract class for a simple key/value store with expiration.
"""
from abc import abstractmethod, ABCMeta
import time


class KeyValueStore:
    """
    Simple key/value store with expiration
    """

    # set this so we will be notified of missing overrides
    __metaclass__ = ABCMeta

    @abstractmethod
    def lookup(self, key):
        """
        Given a key, lookup a value. Returns None if the key is not found.
        """
        pass


    @abstractmethod
    def store(self, key, stringval, exptime_seconds=None):
        """
        Associates a key with a value for the given expiration time.
        Returns True on success, otherwise False.
        A value of None is not allowed.
        """
        return False
