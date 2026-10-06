"""tests: independent correctness checks. Author: OpenAI Codex."""
import json
import random
import unittest
from pathlib import Path
from controller import Directory, valid_key
from data_io import FIELDS, generate, make_record, read_text
from hash_table import HashTable
from skip_list import SkipList
from sorted_array import SortedArray
from metrics import Counter


class IndexTests(unittest.TestCase):
    def test_01_high_lane_search(self):
        s = SkipList(seed=8)
        for key in range(100):
            s.insert(key, make_record(key), Counter())
        self.assertGreater(s.level, 0)
        self.assertEqual(s.search(90, Counter()).subscriber_id, 90)

    def test_02_top_level_growth(self):
        s = SkipList(seed=1)
        s.insert(10, make_record(10), Counter())
        self.assertGreater(s.level, 0)

    def test_03_delete_all_levels(self):
        s = SkipList(seed=1)
        s.insert(10, make_record(10), Counter())
        self.assertTrue(s.delete(10, Counter()))
        self.assertTrue(all(x is None for x in s.head.forward))
        self.assertEqual(s.level, 0)

    def test_04_no_collision(self):
        h = HashTable(101)
        for key in (1, 2, 3):
            h.insert(key, make_record(key), Counter())
        self.assertEqual(h.inspect()['max_chain'], 1)

    def test_05_collision_tail_search(self):
        h = HashTable(1)
        for key in range(10):
            h.insert(key, make_record(key), Counter())
        c = Counter()
        self.assertEqual(h.search(0, c).subscriber_id, 0)
        self.assertEqual(c.visits, 10)
        self.assertEqual(h.inspect()['load_factor'], 10)

    def test_06_chain_middle_delete(self):
        h = HashTable(1)
        for key in (1, 2, 3):
            h.insert(key, make_record(key), Counter())
        self.assertTrue(h.delete(2, Counter()))
        self.assertIsNone(h.search(2, Counter()))
        self.assertIsNotNone(h.search(1, Counter()))
        self.assertIsNotNone(h.search(3, Counter()))

    def test_07_negative_hash_key(self):
        h = HashTable(7)
        h.insert(-42, make_record(42), Counter())
        self.assertTrue(0 <= h._bucket(-42) < 7)
        self.assertIsNotNone(h.search(-42, Counter()))

    def test_08_binary_middle_left_absent(self):
        a = SortedArray([make_record(x) for x in (30, 10, 20)], Counter())
        for recursive in (False, True):
            self.assertEqual(
                a.search(20, Counter(), recursive).subscriber_id, 20)
            self.assertEqual(
                a.search(10, Counter(), recursive).subscriber_id, 10)
            self.assertIsNone(a.search(0, Counter(), recursive))

    def test_09_degenerate_skip_list(self):
        s = SkipList(probability=0)
        for key in range(50):
            s.insert(key, make_record(key), Counter())
        self.assertEqual(s.level, 0)
        self.assertIsNotNone(s.search(49, Counter()))
        self.assertIsNone(s.search(500, Counter()))

    def test_10_empty_single_two(self):
        for size in (0, 1, 2):
            app = Directory()
            app.build(generate(size))
            found = app.query('range', 0, 2147483647)
            self.assertTrue(all(x['matches'] == size for x in found))
            self.assertTrue(all(x['matches'] == 0 for x in
                                app.query('exact', 999999)))

    def test_11_randomized_oracle(self):
        # dict and sorted are used only here as independent test oracles.
        app, expected = Directory(), {}
        app.build([])
        rng = random.Random(99)
        for _ in range(250):
            key = rng.randrange(100)
            if key in expected:
                app.mutate('delete', key)
                del expected[key]
            else:
                app.mutate('insert', key)
                expected[key] = make_record(key)
            for _, engine in app.engines:
                result = engine.range_search(20, 80, Counter())
                oracle = [expected[k] for k in sorted(expected)
                          if 20 <= k <= 80]
                self.assertEqual(result, oracle)

    def test_12_duplicate_atomicity(self):
        app = Directory()
        app.build(generate(5))
        with self.assertRaises(ValueError):
            app.mutate('insert', 100000)
        self.assertEqual(len(app.records), 5)
        for row in app.query('exact', 100000):
            self.assertEqual(row['matches'], 1)

    def test_13_bad_csv_rows(self):
        header = ','.join(FIELDS) + '\n'
        valid = '8,1,SYN,2026-01-01T00:00:00,60,5G,-70\n'
        text = header + valid + valid + 'bad,1,SYN,date,2,5G,-70\n'
        records, errors = read_text(text)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(errors), 2)

    def test_14_empty_header_only(self):
        with self.assertRaises(ValueError):
            read_text('')
        self.assertEqual(read_text(','.join(FIELDS) + '\n'), ([], []))

    def test_15_bad_query(self):
        for key in ('abc', '-1', '1.5', True, 2147483648):
            with self.assertRaises(ValueError):
                valid_key(key)
        app = Directory()
        app.build(generate(10))
        with self.assertRaises(ValueError):
            app.query('range', 10, 1)

    def test_16_full_scale(self):
        app = Directory()
        app.build(generate(50000))
        for row in app.query('range', 100000, 100198):
            self.assertEqual(row['matches'], 100)
        for row in app.query('exact', 199998):
            self.assertEqual(row['matches'], 1)

    def test_17_invalid_configuration(self):
        for constructor in (lambda: SkipList(1), lambda: HashTable(0)):
            with self.assertRaises(ValueError):
                constructor()

    def test_18_absent_deletion(self):
        for engine in (SkipList(), HashTable(3), SortedArray([], Counter())):
            self.assertFalse(engine.delete(10, Counter()))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(IndexTests)
    path = Path(__file__).resolve().parents[1] / 'results' / 'tests.txt'
    path.parent.mkdir(exist_ok=True)
    with path.open('w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    print(path.read_text())
    summary = {'run': result.testsRun, 'failures': len(result.failures),
               'errors': len(result.errors), 'passed': result.wasSuccessful()}
    path.with_suffix('.json').write_text(json.dumps(summary, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
