#!/usr/bin/env python3
"""
Create FASTA-mode samplesheet from assembly accession samplesheet.

Converts validation_samplesheet.csv (with assembly_accession column)
to a FASTA-mode samplesheet (with fasta column pointing to local files).
"""

import csv
import sys
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    input_file = script_dir / "validation_samplesheet.csv"
    output_file = script_dir / "validation_samplesheet_fasta.csv"
    assemblies_dir = script_dir / "assemblies"

    # Check input exists
    if not input_file.exists():
        print(f"ERROR: Input samplesheet not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    # Check assemblies directory exists
    if not assemblies_dir.exists():
        print(f"ERROR: Assemblies directory not found: {assemblies_dir}", file=sys.stderr)
        sys.exit(1)

    # Read input and write output
    samples_written = 0
    missing_files = []

    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=['sample', 'organism', 'fasta'])
        writer.writeheader()

        for row in reader:
            sample = row['sample']
            organism = row['organism']

            # Construct path to FASTA file
            fasta_file = assemblies_dir / f"{sample}.fasta"

            # Check if file exists
            if not fasta_file.exists():
                missing_files.append(sample)
                continue

            # Write row with relative path from project root
            writer.writerow({
                'sample': sample,
                'organism': organism,
                'fasta': f"data/validation/assemblies/{sample}.fasta"
            })
            samples_written += 1

    # Report results
    print(f"✓ Created FASTA-mode samplesheet: {output_file}")
    print(f"  Samples written: {samples_written}")

    if missing_files:
        print(f"\n⚠ Warning: {len(missing_files)} samples missing FASTA files:")
        for sample in missing_files[:10]:  # Show first 10
            print(f"    - {sample}.fasta")
        if len(missing_files) > 10:
            print(f"    ... and {len(missing_files) - 10} more")
        print()
    else:
        print(f"  All FASTA files found!")

    print(f"\nNext steps:")
    print(f"  1. Review: {output_file}")
    print(f"  2. Update run_compass_validation.sh to use:")
    print(f"     --input data/validation/validation_samplesheet_fasta.csv")

if __name__ == "__main__":
    main()
