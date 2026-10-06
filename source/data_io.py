"""data_io: synthetic records and validation. Author: OpenAI Codex."""
import csv
import io
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from hash_table import HashTable
from metrics import Counter

FIELDS = ['subscriber_id', 'cell_id', 'subscriber_ref', 'call_start',
          'duration_s', 'technology', 'signal_dbm']


@dataclass(frozen=True)
class Record:
    subscriber_id: int
    cell_id: int
    subscriber_ref: str
    call_start: str
    duration_s: int
    technology: str
    signal_dbm: int

    def data(self):
        return asdict(self)


def make_record(key, rng=None):
    rng = rng or random.Random(key)
    start = datetime(2026, 1, 1) + timedelta(seconds=rng.randrange(86400))
    return Record(key, rng.randint(1, 250), 'SYN-%08d' % key,
                  start.isoformat(), rng.randint(0, 3600),
                  rng.choice(['4G', '5G']), rng.randint(-120, -40))


def generate(n, seed=8):
    if not 0 <= n <= 1000000:
        raise ValueError('Record count must be between 0 and 1000000.')
    rng = random.Random(seed)
    records = [make_record(100000 + 2 * i, rng) for i in range(n)]
    rng.shuffle(records)
    return records


def parse_row(row):
    if len(row) != len(FIELDS):
        raise ValueError('Expected exactly seven fields.')
    key, cell = int(row[0]), int(row[1])
    duration, signal = int(row[4]), int(row[6])
    if key < 0 or key > 2147483647 or cell < 1:
        raise ValueError('ID must be 0..2147483647; cell ID positive.')
    if not row[2].strip() or not 0 <= duration <= 86400:
        raise ValueError('Reference required; duration must be 0..86400.')
    if row[5] not in ('4G', '5G') or not -150 <= signal <= 0:
        raise ValueError('Technology must be 4G/5G; signal -150..0 dBm.')
    datetime.fromisoformat(row[3])
    return Record(key, cell, row[2], row[3], duration, row[5], signal)


def read_text(text):
    rows = csv.reader(io.StringIO(text.lstrip('\ufeff')))
    if next(rows, None) != FIELDS:
        raise ValueError('CSV is empty or its header does not match.')
    records, errors = [], []
    seen = HashTable(62501)
    for line, row in enumerate(rows, 2):
        try:
            record = parse_row(row)
            seen.insert(record.subscriber_id, record, Counter())
            records.append(record)
        except (ValueError, TypeError) as error:
            errors.append({'line': line, 'error': str(error)})
    return records, errors


def read_csv(path):
    return read_text(path.read_text(encoding='utf-8-sig'))


def write_csv(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        for record in records:
            writer.writerow([getattr(record, field) for field in FIELDS])
