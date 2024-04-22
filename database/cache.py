from dataclasses import dataclass
from datetime import timedelta, datetime


class Cache:
    @dataclass
    class __CacheItem:
        item: object
        time: datetime

    def __init__(self, expiry_seconds=5):
        self.__items = {}
        self.__expiry_delta = timedelta(seconds=expiry_seconds)

    def put(self, key, value):
        current_time = datetime.now()
        self.__items[key] = self.__CacheItem(value, current_time)

    def get(self, key):
        current_time = datetime.now()
        cache_item = self.__items.get(key)
        if cache_item is not None and cache_item.time + self.__expiry_delta.total_seconds() < current_time:
            return cache_item.item
        else:
            self.pop(key)
            return None

    def get_all_items(self):
        items = []
        current_time = datetime.now()
        cache_keys = list(self.__items.keys())

        for key in cache_keys:
            cache_item = self.__items.get(key)
            elapsed_time = current_time - cache_item.time
            if elapsed_time >= self.__expiry_delta:
                items.append(cache_item.item)
            else:
                self.pop(key)

        return items

    def pop(self, key):
        self.__items.pop(key, None)
