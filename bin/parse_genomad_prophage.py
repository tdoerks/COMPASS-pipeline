#!/usr/bin/env python3
"""
parse_genomad_prophage.py

Aggregates per-sample geNomad virus_summary.tsv files into a single TSV
with ICTV taxonomy columns usable by generate_compass_summary.py and
build_phage_therapy_viewer.py.

Usage:
    python3 bin/parse_genomad_prophage.py --genomad-dir results/genomad_prophage \
                                          --out genomad_prophage_summary.tsv

Output columns:
    sample_id, prophage_count_genomad, prophage_families_ictv,
    prophage_genera_ictv, top_prophage_family, top_prophage_genus,
    genomad_virus_summary_json
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path


def parse_virus_summary(tsv_path):
    """Parse a geNomad virus_summary.tsv into list of dicts."""
    rows = []
    with open(tsv_path) as fh:
        reader = csv.DictReader(fh, delimiter='\t')
        for row in reader:
            rows.append(row)
    return rows


def extract_ictv(rows):
    """
    Pull ICTV family/genus from geNomad taxonomy string.
    geNomad taxonomy format: 'Realm;Subrealm;Kingdom;Phylum;Class;Order;Family;Subfamily;Genus'
    Not all levels are always present; missing levels are empty strings.
    """
    families = []
    genera = []
    for row in rows:
        tax = row.get('taxonomy', '') or ''
        parts = [p.strip() for p in tax.split(';')]
        # ICTV hierarchy: realm(0), subrealm(1), kingdom(2), phylum(3),
        #                  class(4), order(5), family(6), subfamily(7), genus(8)
        family = parts[6] if len(parts) > 6 and parts[6] else 'unclassified'
        genus  = parts[8] if len(parts) > 8 and parts[8] else 'unclassified'
        families.append(family)
        genera.append(genus)
    return families, genera


def summarise_sample(sample_id, virus_summary_path):
    rows = parse_virus_summary(virus_summary_path)
    if not rows:
        return {
            'sample_id': sample_id,
            'prophage_count_genomad': 0,
            'prophage_families_ictv': '',
            'prophage_genera_ictv': '',
            'top_prophage_family': '',
            'top_prophage_genus': '',
            'genomad_virus_summary_json': '[]',
        }

    families, genera = extract_ictv(rows)

    fam_counts = Counter(families)
    gen_counts = Counter(genera)
    top_family = fam_counts.most_common(1)[0][0] if fam_counts else ''
    top_genus  = gen_counts.most_common(1)[0][0] if gen_counts else ''

    # Deduplicated, sorted lists for the flat columns
    unique_families = sorted(set(f for f in families if f != 'unclassified'))
    unique_genera   = sorted(set(g for g in genera   if g != 'unclassified'))

    # Minimal JSON blob for the viewer (seq_name + taxonomy + score)
    summary_json = []
    for row in rows:
        summary_json.append({
            'seq': row.get('seq_name', ''),
            'length': row.get('length', ''),
            'topology': row.get('topology', ''),
            'taxonomy': row.get('taxonomy', ''),
            'virus_score': row.get('virus_score', ''),
            'fdr': row.get('fdr', ''),
            'n_genes': row.get('n_genes', ''),
            'taxonomy_class': row.get('taxonomy_classification', ''),
        })

    return {
        'sample_id': sample_id,
        'prophage_count_genomad': len(rows),
        'prophage_families_ictv': ';'.join(unique_families) if unique_families else 'unclassified',
        'prophage_genera_ictv': ';'.join(unique_genera) if unique_genera else 'unclassified',
        'top_prophage_family': top_family,
        'top_prophage_genus': top_genus,
        'genomad_virus_summary_json': json.dumps(summary_json),
    }


def main():
    parser = argparse.ArgumentParser(description='Aggregate geNomad prophage summaries')
    parser.add_argument('--genomad-dir', required=True,
                        help='Parent directory containing per-sample geNomad output dirs')
    parser.add_argument('--out', default='genomad_prophage_summary.tsv',
                        help='Output TSV path (default: genomad_prophage_summary.tsv)')
    args = parser.parse_args()

    genomad_root = Path(args.genomad_dir)
    if not genomad_root.is_dir():
        print(f'ERROR: --genomad-dir not found: {genomad_root}', file=sys.stderr)
        sys.exit(1)

    results = []
    for sample_dir in sorted(genomad_root.iterdir()):
        if not sample_dir.is_dir():
            continue
        sample_id = sample_dir.name

        # Expected path: <sample_dir>/<sample_id>_genomad/<sample_id>_summary/<sample_id>_virus_summary.tsv
        virus_tsv = sample_dir / f'{sample_id}_genomad' / f'{sample_id}_summary' / f'{sample_id}_virus_summary.tsv'
        if not virus_tsv.is_file():
            # Also try flat layout (if publishDir copied the inner dir)
            virus_tsv = sample_dir / f'{sample_id}_summary' / f'{sample_id}_virus_summary.tsv'

        if virus_tsv.is_file():
            results.append(summarise_sample(sample_id, virus_tsv))
        else:
            print(f'WARN: no virus_summary.tsv for {sample_id} (no prophages or geNomad skipped)', file=sys.stderr)
            results.append({
                'sample_id': sample_id,
                'prophage_count_genomad': 0,
                'prophage_families_ictv': '',
                'prophage_genera_ictv': '',
                'top_prophage_family': '',
                'top_prophage_genus': '',
                'genomad_virus_summary_json': '[]',
            })

    if not results:
        print('WARN: no samples found under', genomad_root, file=sys.stderr)
        sys.exit(0)

    fieldnames = [
        'sample_id', 'prophage_count_genomad', 'prophage_families_ictv',
        'prophage_genera_ictv', 'top_prophage_family', 'top_prophage_genus',
        'genomad_virus_summary_json',
    ]

    with open(args.out, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(results)

    print(f'Written {len(results)} samples to {args.out}')


if __name__ == '__main__':
    main()
