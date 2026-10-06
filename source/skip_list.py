"""skip_list: probabilistic ordered index. Author: OpenAI Codex for Animesh."""
import random


class Node:
    def __init__(self, key, value, height):
        self.key, self.value = key, value
        self.forward = [None] * (height + 1)


class SkipList:
    def __init__(self, probability=0.5, max_level=24, seed=8):
        if not 0 <= probability < 1 or not 0 <= max_level <= 32:
            raise ValueError('Probability must be 0..0.99; level 0..32.')
        self.p, self.limit = probability, max_level
        self.rng = random.Random(seed)
        self.head = Node(None, None, max_level)
        self.level, self.size = 0, 0

    def _path(self, key, c):
        update = [self.head] * (self.limit + 1)
        node = self.head
        for level in range(self.level, -1, -1):
            while node.forward[level] is not None:
                nxt = node.forward[level]
                c.visits += 1
                if c.compare(nxt.key, key) >= 0:
                    break
                node = nxt
            update[level] = node
        return update

    def search(self, key, c):
        node = self._path(key, c)[0].forward[0]
        if node is not None and c.compare(node.key, key) == 0:
            return node.value
        return None

    def insert(self, key, value, c):
        update = self._path(key, c)
        nxt = update[0].forward[0]
        if nxt is not None and c.compare(nxt.key, key) == 0:
            raise ValueError('Duplicate subscriber ID.')
        height = 0
        while height < self.limit and self.rng.random() < self.p:
            height += 1
        # _path initializes new levels to the sentinel.
        self.level = max(self.level, height)
        node = Node(key, value, height)
        for level in range(height + 1):
            node.forward[level] = update[level].forward[level]
            update[level].forward[level] = node
            c.writes += 2
        self.size += 1

    def delete(self, key, c):
        update = self._path(key, c)
        node = update[0].forward[0]
        if node is None or c.compare(node.key, key) != 0:
            return False
        for level in range(len(node.forward)):
            update[level].forward[level] = node.forward[level]
            c.writes += 1
        while self.level > 0 and self.head.forward[self.level] is None:
            self.level -= 1
        self.size -= 1
        return True

    def range_search(self, low, high, c):
        if low > high:
            raise ValueError('Range start must not exceed range end.')
        node = self._path(low, c)[0].forward[0]
        result = []
        while node is not None:
            c.visits += 1
            if c.compare(node.key, high) > 0:
                break
            result.append(node.value)
            node = node.forward[0]
        return result

    def inspect(self, limit=12):
        levels = []
        for level in range(self.level, -1, -1):
            keys, count = [], 0
            node = self.head.forward[level]
            while node is not None:
                count += 1
                if len(keys) < limit:
                    keys.append(node.key)
                node = node.forward[level]
            levels.append({'level': level, 'count': count, 'keys': keys})
        return {'size': self.size, 'levels': levels}
