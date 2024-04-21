import time
from dataclasses import dataclass
from datetime import timedelta


class Cache:
    @dataclass
    class __CacheItem:
        item: object
        time: float

    def __init__(self, expiry_seconds=5):
        self.__items = {}
        self.__expiry_delta = timedelta(seconds=expiry_seconds)  # Use timedelta

    def put(self, key, value):
        current_time = time.time()
        self.__items[key] = self.__CacheItem(value, current_time)

    def get(self, key):
        current_time = time.time()
        cache_item = self.__items.get(key)
        if cache_item is not None and cache_item.time + self.__expiry_delta.total_seconds() < current_time:
            return cache_item.item
        else:
            self.pop(key)
            return None

    def get_all_items(self):
        items = []
        current_time = time.time()
        cache_keys = list(self.__items.keys())

        for key in cache_keys:
            cache_item = self.__items.get(key)
            if cache_item.time + self.__expiry_delta.total_seconds() < current_time:
                items.append(cache_item.item)
            else:
                self.pop(key)

        return items

    def pop(self, key):
        self.__items.pop(key, None)
