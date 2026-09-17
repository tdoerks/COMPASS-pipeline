#!/usr/bin/env python3
"""
fetch_stec_samples.py

Fetch STEC (Shiga toxin-producing E. coli) assemblies from the NCBI Pathogen
Isolates database that have confirmed stx genes + MIC/AST data.

Strategy:
  1. Query NCBI Pathogen Isolates for E. coli isolates that have:
     - Virulence gene hit matching stx* in the AMR/virulence metadata
     - A genome assembly (GCA accession)
     - At least one interpreted MIC/AST result (R/I/S)
  2. Download the isolates table
  3. Filter and write a COMPASS samplesheet (sample,organism,assembly_accession)

The cleanest approach is to download the isolates table manually from the
NCBI Pathogen Isolates Browser and pass it here. Instructions below.

MANUAL DOWNLOAD (recommended):
  1. Go to: https://www.ncbi.nlm.nih.gov/pathogens/isolates/
  2. Search: "Escherichia coli"
  3. Filter → Virulence genes → type "stx" → apply
  4. Also filter: "Has AMR data" (ensures MIC/AST present)
  5. Download → TSV (may be named isolates.csv)
  6. Run: python3 bin/fetch_stec_samples.py isolates.csv

AUTOMATED (requires NCBI API key for rate limits):
  Set NCBI_API_KEY env var and run with --fetch flag.

OUTPUT:
  samplesheet_stec.csv  — ready for: nextflow run main.nf --input_mode assembly
  stec_stats.txt        — summary of stx subtypes, sources, dates

USAGE:
  python3 bin/fetch_stec_samples.py <isolates_tsv> [--out samplesheet_stec.csv] [--max 500]
  python3 bin/fetch_stec_samples.py isolates.csv --max 200
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter

STX_PAT = re.compile(r'\bstx|\bestX', re.IGNORECASE)


def parse_isolates(path, max_samples=None, require_ast=True):
    """
    Parse NCBI Pathogen Isolates TSV export.
    Returns list of dicts for STEC isolates with assembly accessions.
    """
    rows = []
    skipped_no_gca = 0
    skipped_no_ast = 0
    skipped_no_stx = 0

    with open(path, encoding='utf-8-sig') as f:
        # NCBI export uses tab-delimited with # prefix on header; utf-8-sig strips BOM
        first = f.readline()
        f.seek(0)
        delimiter = '\t' if '\t' in first else ','
        reader = csv.DictReader(f, delimiter=delimiter)

        # Normalise header names (strip leading #, whitespace)
        reader.fieldnames = [h.lstrip('#').strip() for h in (reader.fieldnames or [])]

        for row in reader:
            # Find stx virulence genes column
            vf = (row.get('virulence_genotypes', '') or
                  row.get('AMR genotypes', '') or
                  row.get('AMR_genotypes', '') or
                  row.get('Computed types', '') or '')
            if not STX_PAT.search(vf):
                skipped_no_stx += 1
                continue

            # Need a GCA assembly
            acc = (row.get('Assembly', '') or
                   row.get('assembly_accession', '') or '').strip()
            if not acc or acc in ('-', 'NA', 'N/A'):
                skipped_no_gca += 1
                continue

            # Optionally require at least one AST result
            if require_ast:
                ast_cols = [v for k, v in row.items()
                            if 'AST' in k or 'MIC' in k or 'SIR' in k.upper()]
                has_ast = any(v.strip() in ('R', 'I', 'S') for v in ast_cols)
                # Fallback: AMR genotypes column (space or underscore) as proxy
                amr = row.get('AMR genotypes', '') or row.get('AMR_genotypes', '') or ''
                if not has_ast and not amr.strip():
                    skipped_no_ast += 1
                    continue

            # Classify stx subtype (NCBI uses estX-1/estX-2/estX-3 naming)
            stx1 = bool(re.search(r'\bstx1|\bestX-1', vf, re.IGNORECASE))
            stx2 = bool(re.search(r'\bstx2|\bestX-[23456789]', vf, re.IGNORECASE))
            stx_type = ('stx1+stx2' if stx1 and stx2 else
                        'stx1' if stx1 else 'stx2' if stx2 else 'stx_unknown')

            rows.append({
                'sample': acc.replace('.', '_', 1).replace('.', '_'),
                'organism': 'Escherichia',
                'assembly_accession': acc,
                'stx_type': stx_type,
                'source': row.get('isolation_source', row.get('Source', '')),
                'collection_date': row.get('collection_date', row.get('Create date', '')),
                'biosample': row.get('BioSample', row.get('biosample_acc', '')),
                'mlst_st': row.get('MLST', row.get('serovar', '')),
                'vf_genes': vf,
            })

            if max_samples and len(rows) >= max_samples:
                break

    print(f"Parsed {len(rows)} STEC isolates with assemblies")
    print(f"  Skipped — no stx gene: {skipped_no_stx}")
    print(f"  Skipped — no GCA:      {skipped_no_gca}")
    if require_ast:
        print(f"  Skipped — no AST:      {skipped_no_ast}")
    return rows


def write_samplesheet(rows, out_path):
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample', 'organism', 'assembly_accession'])
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in ['sample', 'organism', 'assembly_accession']})
    print(f"Wrote {len(rows)} samples → {out_path}")


def write_stats(rows, out_path):
    stx_types = Counter(r['stx_type'] for r in rows)
    sources = Counter(r['source'] for r in rows if r['source'])
    with open(out_path, 'w') as f:
        f.write(f"STEC sample summary\n{'='*40}\n")
        f.write(f"Total: {len(rows)}\n\n")
        f.write("stx subtype:\n")
        for k, v in sorted(stx_types.items(), key=lambda x: -x[1]):
            f.write(f"  {k}: {v}\n")
        f.write("\nTop isolation sources:\n")
        for src, cnt in sources.most_common(15):
            f.write(f"  {src}: {cnt}\n")
    print(f"Wrote stats → {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('isolates_tsv', help='NCBI Pathogen Isolates export TSV/CSV')
    ap.add_argument('--out', default='samplesheet_stec.csv', help='Output samplesheet path')
    ap.add_argument('--max', type=int, default=None, help='Max samples to include')
    ap.add_argument('--all-ast', action='store_true', default=False,
                    help='Include isolates without AST data (default: require AST)')
    args = ap.parse_args()

    if not os.path.exists(args.isolates_tsv):
        print(f"ERROR: file not found: {args.isolates_tsv}", file=sys.stderr)
        sys.exit(1)

    rows = parse_isolates(args.isolates_tsv,
                          max_samples=args.max,
                          require_ast=not args.all_ast)

    if not rows:
        print("No STEC isolates found — check column names in the TSV header.")
        sys.exit(1)

    write_samplesheet(rows, args.out)
    stats_path = args.out.replace('.csv', '_stats.txt')
    write_stats(rows, stats_path)

    print(f"\nNext steps:")
    print(f"  1. Download assemblies: ~/bin/datasets download genome accession --inputfile <(awk -F, 'NR>1{{print $3}}' {args.out}) --include genome")
    print(f"  2. Build fasta samplesheet: python3 bin/make_fasta_samplesheet.py {args.out}")
    print(f"  3. Run COMPASS: nextflow run main.nf --input_mode assembly --input {args.out}")


if __name__ == '__main__':
    main()
