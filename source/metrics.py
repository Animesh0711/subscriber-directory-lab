"""metrics: operation counters and timer. Author: OpenAI Codex for Animesh."""
from dataclasses import dataclass, asdict
from time import perf_counter


@dataclass
class Counter:
    comparisons: int = 0
    visits: int = 0
    writes: int = 0

    def compare(self, left, right):
        # One logical three-way key comparison, not Python opcode counting.
        self.comparisons += 1
        return (left > right) - (left < right)

    def data(self):
        return asdict(self)


def measured(function):
    counter = Counter()
    start = perf_counter()
    result = function(counter)
    elapsed = (perf_counter() - start) * 1000000
    return result, {**counter.data(), 'time_us': elapsed}
