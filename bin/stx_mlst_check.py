#!/usr/bin/env python3
"""
stx_mlst_check.py
Print MLST data for all stx-positive isolates in compass_summary.tsv.

Usage (from COMPASS-1.1.0/):
    python3 bin/stx_mlst_check.py
    python3 bin/stx_mlst_check.py path/to/compass_summary.tsv
"""

import csv
import re
import sys

tsv_path = sys.argv[1] if len(sys.argv) > 1 else 'compass_summary.tsv'

stx_pat = re.compile(r'\bstx1|\bstx2|\bstxA\b|\bstxB\b', re.IGNORECASE)

with open(tsv_path) as f:
    reader = csv.DictReader(f, delimiter='\t')
    print('\t'.join(['sample_id', 'mlst_scheme', 'mlst_st', 'stx_genes']))
    count = 0
    for row in reader:
        vf = row.get('top_virulence_genes', '')
        if stx_pat.search(vf):
            stx = ', '.join(
                g.strip() for g in vf.split(',')
                if g.strip().lower().startswith('stx')
            )
            print('\t'.join([
                row.get('sample_id', '-'),
                row.get('mlst_scheme', '-'),
                row.get('mlst_st', '-'),
                stx
            ]))
            count += 1
    print(f'\nTotal stx-positive: {count}', flush=True)
