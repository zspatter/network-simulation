import csv
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import make_tsv  # noqa: E402


def test_write_tsv_writes_only_well_formed_non_self_loop_rows(tmp_path):
    path = tmp_path / 'edges.tsv'

    make_tsv.write_tsv(path=str(path))

    with open(path, newline='') as f:
        rows = list(csv.reader(f, delimiter='\t'))

    assert rows  # random.choice(range(5)) == 0 fires often enough across 25*25 pairs
    for row in rows:
        assert len(row) == 2
        x, y = int(row[0]), int(row[1])
        assert 1 <= x <= 25
        assert 1 <= y <= 25
        assert x != y  # no self-loops
