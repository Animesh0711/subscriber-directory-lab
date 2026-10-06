"""controller: shared application service. Author: OpenAI Codex."""
from data_io import generate, make_record, read_text
from skip_list import SkipList
from hash_table import HashTable
from sorted_array import SortedArray
from metrics import Counter, measured


def valid_key(value):
    if isinstance(value, bool) or not str(value).isdigit():
        raise ValueError('Subscriber ID must be a non-negative integer.')
    value = int(value)
    if value > 2147483647:
        raise ValueError('Subscriber ID must not exceed 2147483647.')
    return value


class Directory:
    def __init__(self):
        self.records, self.engines, self.build_metrics = [], [], []

    def build(self, records, capacity=None, probability=0.5, seed=8):
        capacity = capacity or max(1, int(len(records) / 0.8) + 1)
        skip, hashed = SkipList(probability, seed=seed), HashTable(capacity)
        def fill(engine, c):
            for record in records:
                engine.insert(record.subscriber_id, record, c)
            return engine
        _, sm = measured(lambda c: fill(skip, c))
        _, hm = measured(lambda c: fill(hashed, c))
        array, am = measured(lambda c: SortedArray(records, c))
        # Commit only after all three builds succeed.
        self.records = list(records)
        self.engines = [('Skip list', skip), ('Hash table', hashed),
                        ('Binary array', array)]
        self.build_metrics = [dict(method=n, **m) for n, m in
                              zip(['Skip list', 'Hash table',
                                   'Binary array'], [sm, hm, am])]
        return self.status()

    def load(self, n=50000, capacity=62501, probability=0.5, text=None):
        if not 1 <= capacity <= 2000000:
            raise ValueError('Buckets must be between 1 and 2000000.')
        records, errors = (read_text(text) if text is not None else
                           (generate(n), []))
        status = self.build(records, capacity, probability)
        return dict(status, rejected=errors)

    def status(self):
        if not self.engines:
            return {'count': 0, 'built': False, 'build': []}
        skip, hashed, array = [e for _, e in self.engines]
        return {'count': len(self.records), 'built': True,
                'build': self.build_metrics, 'skip': skip.inspect(),
                'hash': hashed.inspect(),
                'array': [r.subscriber_id for r in array.records[:24]]}

    def query(self, kind, low, high=None):
        low = valid_key(low)
        high = valid_key(high) if high is not None else low
        if kind not in ('exact', 'range', 'recursive'):
            raise ValueError('Unknown query type.')
        if low > high:
            raise ValueError('Range start must not exceed range end.')
        if not self.engines:
            raise ValueError('Build the indexes first.')
        output = []
        for name, engine in self.engines:
            def run(c):
                if kind == 'range':
                    return engine.range_search(low, high, c)
                record = (engine.search(low, c, recursive=True)
                          if kind == 'recursive' and name == 'Binary array'
                          else engine.search(low, c))
                return [] if record is None else [record]
            records, metric = measured(run)
            output.append({'method': name, 'matches': len(records),
                           'records': [r.data() for r in records[:100]],
                           **metric})
        return output

    def mutate(self, action, key):
        key = valid_key(key)
        if not self.engines:
            raise ValueError('Build the indexes first.')
        if action not in ('insert', 'delete'):
            raise ValueError('Unknown modification.')
        found = self.engines[0][1].search(key, Counter())
        if action == 'insert' and found is not None:
            raise ValueError('Duplicate subscriber ID.')
        if action == 'delete' and found is None:
            raise ValueError('Subscriber ID was not found.')
        record, output = make_record(key), []
        for name, engine in self.engines:
            def run(c):
                return (engine.insert(key, record, c) if action == 'insert'
                        else engine.delete(key, c))
            _, metric = measured(run)
            output.append(dict(method=name, **metric))
        if action == 'insert':
            self.records.append(record)
        else:
            self.records = [r for r in self.records if r.subscriber_id != key]
        return {'action': action, 'key': key, 'metrics': output,
                'count': len(self.records)}
