"""sorted_array: merge sort and binary search. Author: OpenAI Codex."""


def merge_sort(records, c):
    result = list(records)
    width, n = 1, len(result)
    buffer = [None] * n
    while width < n:
        for start in range(0, n, 2 * width):
            mid, end = min(start + width, n), min(start + 2 * width, n)
            i, j = start, mid
            for k in range(start, end):
                if i < mid and (j >= end or c.compare(
                        result[i].subscriber_id,
                        result[j].subscriber_id) <= 0):
                    buffer[k], i = result[i], i + 1
                else:
                    buffer[k], j = result[j], j + 1
                c.writes += 1
        result, buffer = buffer, result
        width *= 2
    return result


class SortedArray:
    def __init__(self, records, c):
        self.records = merge_sort(records, c)
        for i in range(1, len(self.records)):
            if c.compare(self.records[i - 1].subscriber_id,
                         self.records[i].subscriber_id) == 0:
                raise ValueError('Duplicate subscriber ID.')

    def search(self, key, c, recursive=False):
        if recursive:
            return self._recursive(key, 0, len(self.records) - 1, c)
        low, high = 0, len(self.records) - 1
        while low <= high:
            mid = low + (high - low) // 2
            c.visits += 1
            order = c.compare(self.records[mid].subscriber_id, key)
            if order == 0:
                return self.records[mid]
            if order < 0:
                low = mid + 1
            else:
                high = mid - 1
        return None

    def _recursive(self, key, low, high, c):
        if low > high:
            return None
        mid = low + (high - low) // 2
        c.visits += 1
        order = c.compare(self.records[mid].subscriber_id, key)
        if order == 0:
            return self.records[mid]
        if order < 0:
            return self._recursive(key, mid + 1, high, c)
        return self._recursive(key, low, mid - 1, c)

    def _lower_bound(self, key, c):
        low, high = 0, len(self.records)
        while low < high:
            mid = low + (high - low) // 2
            c.visits += 1
            if c.compare(self.records[mid].subscriber_id, key) < 0:
                low = mid + 1
            else:
                high = mid
        return low

    def range_search(self, low, high, c):
        if low > high:
            raise ValueError('Range start must not exceed range end.')
        i, result = self._lower_bound(low, c), []
        while i < len(self.records):
            c.visits += 1
            if c.compare(self.records[i].subscriber_id, high) > 0:
                break
            result.append(self.records[i])
            i += 1
        return result

    def insert(self, key, value, c):
        i = self._lower_bound(key, c)
        if i < len(self.records) and c.compare(
                self.records[i].subscriber_id, key) == 0:
            raise ValueError('Duplicate subscriber ID.')
        self.records.append(value)
        for j in range(len(self.records) - 1, i, -1):
            self.records[j] = self.records[j - 1]
            c.writes += 1
        self.records[i] = value
        c.writes += 1

    def delete(self, key, c):
        i = self._lower_bound(key, c)
        if i == len(self.records) or c.compare(
                self.records[i].subscriber_id, key) != 0:
            return False
        for j in range(i, len(self.records) - 1):
            self.records[j] = self.records[j + 1]
            c.writes += 1
        self.records.pop()
        c.writes += 1
        return True
