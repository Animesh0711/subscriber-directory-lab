"""benchmark: repeatable experiments and exports. Author: OpenAI Codex."""
import csv
import json
import os
import platform
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path
from controller import Directory, release_indexes
from data_io import generate, write_csv
from metrics import Counter, measured
from sorted_array import merge_sort

ROOT = Path(__file__).resolve().parents[1]


def linear(records, low, high, c, exact=False):
    result = []
    for record in records:
        c.visits += 1
        order = c.compare(record.subscriber_id, low)
        if exact:
            if order == 0:
                return [record]
        elif order >= 0 and c.compare(record.subscriber_id, high) <= 0:
            result.append(record)
    return result if exact else merge_sort(result, c)


def workload(n, seed=80):
    rng = random.Random(seed)
    exact = [100000 + 2 * rng.randrange(n) for _ in range(80)]
    exact += [100001 + 2 * rng.randrange(n) for _ in range(20)]
    rng.shuffle(exact)
    ranges = []
    for _ in range(12):
        start = rng.randrange(max(1, n - 100))
        ranges.append((100000 + start * 2, 100000 + (start + 99) * 2))
    return exact, ranges


def run_benchmark(sizes=(1000, 10000, 50000), repeats=5, progress=None):
    if repeats < 2:
        raise ValueError('Use at least two repetitions.')
    output, raw, builds, inspections = [], [], [], []
    folder = ROOT / 'results'
    folder.mkdir(exist_ok=True)
    for n in sizes:
        if progress:
            progress('%s records: building indexes' % n)
        records = generate(n)
        if progress:
            progress('%s records: constructing search structures' % n)
        app = Directory()
        app.build(records)
        if progress:
            progress('%s records: preparing benchmark data' % n)
        write_csv(ROOT / 'data' / ('subscribers_%d.csv' % n), records)
        exact, ranges = workload(n)
        (ROOT / 'data' / ('queries_%d.json' % n)).write_text(
            json.dumps({'exact': exact, 'range': ranges}, indent=2))
        status = app.status()
        if progress:
            progress('%s records: starting queries' % n)
        inspections.append(dict(n=n, skip=status['skip'],
                                hash=status['hash'], array=status['array']))
        for row in app.build_metrics:
            builds.append(dict(n=n, **row))
        methods = list(app.engines) + [('Binary recursive',
                                       app.engines[2][1]),
                                      ('Linear baseline', None)]
        for kind, queries in [('exact', exact), ('range', ranges)]:
            active = [x for x in methods if kind == 'exact' or
                      x[0] != 'Binary recursive']
            # Correctness oracle is outside all timed regions.
            oracle = {r.subscriber_id: r for r in records}
            for name, engine in active:
                if progress:
                    progress('%s records: %s / %s' % (n, kind, name))
                def batch(c):
                    answers = []
                    for q in queries:
                        lo, hi = (q, q) if kind == 'exact' else q
                        if engine is None:
                            found = linear(records, lo, hi, c,
                                           exact=kind == 'exact')
                        elif kind == 'range':
                            found = engine.range_search(lo, hi, c)
                        else:
                            record = (engine.search(lo, c, True)
                                      if name == 'Binary recursive'
                                      else engine.search(lo, c))
                            found = [] if record is None else [record]
                        answers.append(found)
                    return answers
                answers = batch(Counter())  # warm-up and validation
                for q, found in zip(queries, answers):
                    expected = ([oracle[q]] if q in oracle else []) \
                        if kind == 'exact' else sorted(
                            [r for r in records if
                             q[0] <= r.subscriber_id <= q[1]],
                            key=lambda r: r.subscriber_id)
                    assert found == expected, (name, kind, q)
                readings = []
                for repetition in range(repeats):
                    _, metric = measured(batch)
                    readings.append(metric['time_us'] / len(queries))
                    raw.append(dict(n=n, kind=kind, method=name,
                                    repetition=repetition + 1,
                                    queries=len(queries), **metric))
                output.append(dict(n=n, kind=kind, method=name,
                    mean_us=statistics.mean(readings),
                    stdev_us=statistics.stdev(readings),
                    comparisons=metric['comparisons'] / len(queries),
                    visits=metric['visits'] / len(queries),
                    writes=metric['writes'] / len(queries),
                    queries=len(queries), repeats=repeats))
        # Release linked nodes iteratively. Deep cascading destruction of
        # linked Python objects can exhaust the WebAssembly runtime stack.
        # This is outside every measured region; saved results are values.
        if progress:
            progress('%s records: releasing benchmark indexes' % n)
        release_indexes(app.engines)
    metadata = {'python': platform.python_version(),
                'os': platform.platform(),
                'processor': os.environ.get('PROCESSOR_IDENTIFIER', ''),
                'logical_cpus': os.cpu_count(),
                'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                'seed': 8, 'probability': 0.5, 'sizes': list(sizes),
                'repeats': repeats, 'timing': 'instrumented batch mean',
                'range_contract': 'ascending subscriber ID, inclusive',
                'correctness': 'all query outputs match independent oracle'}
    result = dict(metadata=metadata, summary=output, raw=raw,
                  builds=builds, inspections=inspections)
    (folder / 'benchmark.json').write_text(json.dumps(result, indent=2))
    for name, rows in [('summary', output), ('raw_timings', raw),
                       ('build_metrics', builds)]:
        with (folder / (name + '.csv')).open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return result


if __name__ == '__main__':
    result = run_benchmark()
    for row in result['summary']:
        print('{n:6} {kind:5} {method:17} {mean_us:10.3f} us'.format(**row))
    print('All measured query results matched the validation oracle.')
