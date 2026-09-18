#!/usr/bin/env python3
"""
fetch_stec_samples.py

Parse NCBI Pathogen Isolates TSV exports and build COMPASS samplesheets.
Works for STEC (E. coli with stx genes), Shigella, or any organism.

MANUAL DOWNLOAD:
  1. Go to: https://www.ncbi.nlm.nih.gov/pathogens/isolates/
  2. Search your organism (e.g. "Escherichia coli" or "Shigella")
  3. Apply filters as needed (Virulence genes → stx, Has AMR data, etc.)
  4. Download → TSV
  5. Run this script on the downloaded file

USAGE:
  # STEC (stx filter on by default):
  python3 bin/fetch_stec_samples.py isolates.tsv --out samplesheet_stec.csv

  # Shigella (no stx filter, sort newest first, latest 1000):
  python3 bin/fetch_stec_samples.py shigella.tsv --no-stx-filter --sort-date --max 1000 --out samplesheet_shigella.csv

  # Any organism, no filters:
  python3 bin/fetch_stec_samples.py isolates.tsv --no-stx-filter --all-ast --max 500
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter

STX_PAT = re.compile(r'\bstx|\bestX', re.IGNORECASE)

DATE_COLS = ('Create date', 'collection_date', 'Collection date', 'create_date')


def _parse_date(s):
    """Return a sortable date string from various NCBI date formats, or '' if unparseable."""
    if not s:
        return ''
    s = s.strip()
    # Formats seen: 2023-04-15, 2023/04/15, Apr 2023, 2023
    for pat, fmt in [
        (r'^\d{4}-\d{2}-\d{2}$', '%Y-%m-%d'),
        (r'^\d{4}/\d{2}/\d{2}$', '%Y/%m/%d'),
        (r'^\d{4}-\d{2}$', '%Y-%m'),
        (r'^\d{4}$', '%Y'),
    ]:
        if re.match(pat, s):
            return s  # already sortable as string
    return s  # return as-is; worst case sort will still group roughly


def parse_isolates(path, max_samples=None, require_ast=True,
                   require_stx=True, sort_by_date=False, organism_name='isolate'):
    rows = []
    skipped_no_gca = 0
    skipped_no_ast = 0
    skipped_no_stx = 0
    all_rows = []

    with open(path, encoding='utf-8-sig') as f:
        first = f.readline()
        f.seek(0)
        delimiter = '\t' if '\t' in first else ','
        reader = csv.DictReader(f, delimiter=delimiter)
        reader.fieldnames = [h.lstrip('#').strip() for h in (reader.fieldnames or [])]

        for row in reader:
            vf = (row.get('Virulence genotypes', '') or
                  row.get('virulence_genotypes', '') or
                  row.get('AMR genotypes', '') or
                  row.get('AMR_genotypes', '') or
                  row.get('Computed types', '') or '')

            if require_stx and not STX_PAT.search(vf):
                skipped_no_stx += 1
                continue

            acc = (row.get('Assembly', '') or
                   row.get('assembly_accession', '') or
                   row.get('Isolate', '') or '').strip()
            # Only accept GCA/GCF accessions
            if acc and not re.match(r'^GC[AF]_', acc):
                acc = ''
            if not acc or acc in ('-', 'NA', 'N/A'):
                skipped_no_gca += 1
                continue

            if require_ast:
                ast_cols = [v for k, v in row.items()
                            if 'AST' in k or 'MIC' in k or 'SIR' in k.upper()]
                has_ast = any(v.strip() in ('R', 'I', 'S') for v in ast_cols)
                amr = row.get('AMR genotypes', '') or row.get('AMR_genotypes', '') or ''
                if not has_ast and not amr.strip():
                    skipped_no_ast += 1
                    continue

            stx1 = bool(re.search(r'\bstx1|\bestX-1', vf, re.IGNORECASE))
            stx2 = bool(re.search(r'\bstx2|\bestX-[23456789]', vf, re.IGNORECASE))
            stx_type = ('stx1+stx2' if stx1 and stx2 else
                        'stx1' if stx1 else 'stx2' if stx2 else
                        'stx_positive' if STX_PAT.search(vf) else 'negative')

            date_val = ''
            for dc in DATE_COLS:
                date_val = row.get(dc, '').strip()
                if date_val:
                    break

            all_rows.append({
                'sample': acc.replace('.', '_', 1).replace('.', '_'),
                'organism': organism_name,
                'assembly_accession': acc,
                'stx_type': stx_type,
                'source': row.get('isolation_source', row.get('Isolation source',
                                  row.get('Source', ''))),
                'collection_date': date_val,
                'biosample': row.get('BioSample', row.get('biosample_acc', '')),
                'mlst_st': row.get('MLST', row.get('Serovar', row.get('serovar', ''))),
                'vf_genes': vf,
            })

    if sort_by_date:
        all_rows.sort(key=lambda r: _parse_date(r['collection_date']), reverse=True)

    rows = all_rows[:max_samples] if max_samples else all_rows

    print(f"Parsed {len(rows)} {organism_name} isolates with assemblies")
    if require_stx:
        print(f"  Skipped — no stx gene: {skipped_no_stx}")
    print(f"  Skipped — no GCA:      {skipped_no_gca}")
    if require_ast:
        print(f"  Skipped — no AST:      {skipped_no_ast}")
    if sort_by_date and rows:
        print(f"  Date range: {rows[-1]['collection_date']} → {rows[0]['collection_date']}")
    return rows


def write_samplesheet(rows, out_path):
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample', 'organism', 'assembly_accession'])
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in ['sample', 'organism', 'assembly_accession']})
    print(f"Wrote {len(rows)} samples → {out_path}")

    # Write companion metadata CSV with NCBI-derived stx classification.
    # COMPASS VFDB only covers O157:H7 reference stx; AMRFinder needs --plus for
    # VIRULENCE genes. This file lets build_compass_viewer.py use the authoritative
    # NCBI classification instead.
    meta_path = out_path.replace('.csv', '_stx_metadata.csv')
    with open(meta_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample', 'stx_type', 'stx_genes_ncbi',
                                               'collection_date', 'source', 'mlst_st'])
        writer.writeheader()
        for r in rows:
            writer.writerow({
                'sample': r['sample'],
                'stx_type': r['stx_type'],
                'stx_genes_ncbi': re.sub(r'estX', 'stx', r.get('vf_genes', ''), flags=re.IGNORECASE),
                'collection_date': r.get('collection_date', ''),
                'source': r.get('source', ''),
                'mlst_st': r.get('mlst_st', ''),
            })
    print(f"Wrote stx metadata → {meta_path}")


def write_stats(rows, out_path, organism_name):
    stx_types = Counter(r['stx_type'] for r in rows)
    sources = Counter(r['source'] for r in rows if r['source'])
    with open(out_path, 'w') as f:
        f.write(f"{organism_name} sample summary\n{'='*40}\n")
        f.write(f"Total: {len(rows)}\n\n")
        if any(v != 'negative' for v in stx_types):
            f.write("stx subtype:\n")
            for k, v in sorted(stx_types.items(), key=lambda x: -x[1]):
                f.write(f"  {k}: {v}\n")
            f.write("\n")
        f.write("Top isolation sources:\n")
        for src, cnt in sources.most_common(15):
            f.write(f"  {src}: {cnt}\n")
    print(f"Wrote stats → {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('isolates_tsv', help='NCBI Pathogen Isolates export TSV/CSV')
    ap.add_argument('--out', default='samplesheet.csv', help='Output samplesheet path')
    ap.add_argument('--max', type=int, default=None, help='Max samples to include')
    ap.add_argument('--organism', default='isolate',
                    help='Organism label for samplesheet (e.g. Escherichia, Shigella)')
    ap.add_argument('--no-stx-filter', action='store_true', default=False,
                    help='Include all isolates regardless of stx gene presence')
    ap.add_argument('--sort-date', action='store_true', default=False,
                    help='Sort by collection date newest-first before applying --max')
    ap.add_argument('--all-ast', action='store_true', default=False,
                    help='Include isolates without AST/AMR data')
    args = ap.parse_args()

    if not os.path.exists(args.isolates_tsv):
        print(f"ERROR: file not found: {args.isolates_tsv}", file=sys.stderr)
        sys.exit(1)

    rows = parse_isolates(
        args.isolates_tsv,
        max_samples=args.max,
        require_ast=not args.all_ast,
        require_stx=not args.no_stx_filter,
        sort_by_date=args.sort_date,
        organism_name=args.organism,
    )

    if not rows:
        print("No isolates found — check column names in the TSV header.")
        sys.exit(1)

    write_samplesheet(rows, args.out)
    stats_path = args.out.replace('.csv', '_stats.txt')
    write_stats(rows, stats_path, args.organism)

    print(f"\nNext steps:")
    print(f"  1. Download assemblies: datasets download genome accession --inputfile <(awk -F, 'NR>1{{print $3}}' {args.out}) --include genome")
    print(f"  2. Run COMPASS: nextflow run main.nf --input_mode assembly --input {args.out}")


if __name__ == '__main__':
    main()
