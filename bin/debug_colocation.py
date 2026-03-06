#!/usr/bin/env python3
"""
Debug script to understand why we're not finding AMR-prophage co-locations
"""

import sys
from pathlib import Path
import csv

def debug_sample(results_dir, sample_id):
    """Debug a single sample to see what's happening"""

    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"

    print(f"\n{'='*80}")
    print(f"DEBUGGING SAMPLE: {sample_id}")
    print(f"{'='*80}\n")

    # Check AMR file
    amr_file = amr_dir / f"{sample_id}_amr.tsv"
    print(f"1. AMR FILE: {amr_file}")
    print(f"   Exists: {amr_file.exists()}")

    if amr_file.exists():
        with open(amr_file) as f:
            lines = f.readlines()
            print(f"   Lines: {len(lines)}")
            if len(lines) > 1:
                print(f"\n   First AMR gene (showing first 2 data lines):")
                print(f"   Header: {lines[0].strip()}")
                for i in range(1, min(3, len(lines))):
                    parts = lines[i].strip().split('\t')
                    if len(parts) >= 11:
                        print(f"   Line {i}: Contig={parts[1]}, Start={parts[2]}, End={parts[3]}, Gene={parts[5]}, Type={parts[8]}")

    # Check VIBRANT directory
    sample_vibrant_dir = vibrant_dir / f"{sample_id}_vibrant"
    print(f"\n2. VIBRANT DIRECTORY: {sample_vibrant_dir}")
    print(f"   Exists: {sample_vibrant_dir.exists()}")

    if sample_vibrant_dir.exists():
        print(f"   Contents:")
        for item in sorted(sample_vibrant_dir.iterdir()):
            print(f"     - {item.name}")

        # Look for coordinate files
        coord_files = list(sample_vibrant_dir.glob("**/VIBRANT_integrated_prophage_coordinates_*.tsv"))
        print(f"\n   Coordinate files found: {len(coord_files)}")
        for cf in coord_files:
            print(f"     - {cf.name}")
            with open(cf) as f:
                lines = f.readlines()
                print(f"       Lines: {len(lines)}")
                if len(lines) > 1:
                    print(f"       Header: {lines[0].strip()}")
                    if len(lines) > 1:
                        print(f"       First prophage: {lines[1].strip()}")

        # Look for phages FASTA
        phages_fasta = vibrant_dir / f"{sample_id}_phages.fna"
        print(f"\n   Phages FASTA: {phages_fasta}")
        print(f"   Exists: {phages_fasta.exists()}")

        if phages_fasta.exists():
            with open(phages_fasta) as f:
                lines = f.readlines()
                print(f"   Lines: {len(lines)}")
                print(f"   First 5 headers:")
                count = 0
                for line in lines:
                    if line.startswith('>'):
                        print(f"     {line.strip()}")
                        count += 1
                        if count >= 5:
                            break

    # Now let's see if we can find contig name matches
    print(f"\n3. CHECKING CONTIG NAME MATCHING:")

    # Get AMR contigs
    amr_contigs = set()
    if amr_file.exists():
        with open(amr_file) as f:
            next(f)  # skip header
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 11 and parts[8] == 'AMR':
                    amr_contigs.add(parts[1])

    print(f"   AMR contigs (first 10): {sorted(list(amr_contigs))[:10]}")

    # Get prophage contigs from coordinate file
    prophage_contigs = set()
    if coord_files:
        for cf in coord_files:
            with open(cf) as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    contig = row.get('scaffold', row.get('contig', ''))
                    if contig:
                        prophage_contigs.add(contig)

    print(f"   Prophage contigs (first 10): {sorted(list(prophage_contigs))[:10]}")

    # Check for matches
    matches = amr_contigs & prophage_contigs
    print(f"\n   Contigs that appear in BOTH AMR and prophage: {len(matches)}")
    if matches:
        print(f"   Examples: {sorted(list(matches))[:5]}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 debug_colocation.py <results_dir> <sample_id>")
        print("\nExample:")
        print("  python3 debug_colocation.py /path/to/results SRR123456")
        sys.exit(1)

    debug_sample(sys.argv[1], sys.argv[2])
