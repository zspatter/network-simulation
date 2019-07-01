import csv
import random


def write_tsv(path='edge_list.tsv'):
    with open(file=path, mode='w', newline='') as out:
        tsv = csv.writer(out, delimiter='\t')
        for x in range(1, 26):
            for y in range(1, 26):
                if random.choice(list(range(5))) == 0 and x != y:
                    tsv.writerow([x, y])


if __name__ == '__main__':
    write_tsv()
