"""hash_table: separate chaining index. Author: OpenAI Codex for Animesh."""


class ChainNode:
    def __init__(self, key, value, next_node=None):
        self.key, self.value, self.next = key, value, next_node


class HashTable:
    def __init__(self, capacity=62501):
        if capacity < 1:
            raise ValueError('Bucket count must be positive.')
        self.buckets = [None] * capacity
        self.size = 0

    def _bucket(self, key):
        # Explicit integer mixer. Modulo also normalizes negative keys.
        return ((key * 2654435761) & 0xffffffff) % len(self.buckets)

    def search(self, key, c):
        node = self.buckets[self._bucket(key)]
        while node is not None:
            c.visits += 1
            if c.compare(node.key, key) == 0:
                return node.value
            node = node.next
        return None

    def insert(self, key, value, c):
        if self.search(key, c) is not None:
            raise ValueError('Duplicate subscriber ID.')
        i = self._bucket(key)
        self.buckets[i] = ChainNode(key, value, self.buckets[i])
        self.size += 1
        c.writes += 1

    def delete(self, key, c):
        i = self._bucket(key)
        prev, node = None, self.buckets[i]
        while node is not None:
            c.visits += 1
            if c.compare(node.key, key) == 0:
                if prev is None:
                    self.buckets[i] = node.next
                else:
                    prev.next = node.next
                self.size -= 1
                c.writes += 1
                return True
            prev, node = node, node.next
        return False

    def range_search(self, low, high, c):
        if low > high:
            raise ValueError('Range start must not exceed range end.')
        result = []
        for head in self.buckets:
            node = head
            while node is not None:
                c.visits += 1
                lower = c.compare(node.key, low)
                upper = c.compare(node.key, high)
                if lower >= 0 and upper <= 0:
                    result.append(node.value)
                node = node.next
        # Ordered output is part of the contract for every structure.
        from sorted_array import merge_sort
        return merge_sort(result, c)

    def inspect(self, limit=12):
        chains, lengths = [], []
        for i, head in enumerate(self.buckets):
            node, keys, length = head, [], 0
            while node is not None:
                length += 1
                if len(keys) < limit:
                    keys.append(node.key)
                node = node.next
            lengths.append(length)
            if length and len(chains) < limit:
                chains.append({'bucket': i, 'length': length, 'keys': keys})
        return {'size': self.size, 'capacity': len(lengths),
                'load_factor': self.size / len(lengths),
                'max_chain': max(lengths, default=0),
                'occupied': sum(x > 0 for x in lengths),
                'lengths': lengths, 'chains': chains}
