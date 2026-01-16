#!/usr/bin/env python3
"""
Fix prophage metadata by extracting it from FASTA headers
"""

import csv
import sys
from pathlib import Path

def extract_metadata_from_fasta(fasta_file, output_tsv):
    """Extract metadata from FASTA headers"""
    print(f"Reading FASTA file: {fasta_file}")

    metadata = []

    with open(fasta_file, 'r') as f:
        for line in f:
            if line.startswith('>'):
                # Parse header
                # Format: >SRR30276930_vibrant_NODE_48_length_28980_cov_4.050844 sample=SRR30276930_vibrant length=28980 completeness=Likely Complete
                parts = line.strip().split()

                if len(parts) < 2:
                    continue

                prophage_id = parts[0][1:]  # Remove '>'

                # Parse key=value pairs
                info = {}
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        info[key] = value

                sample_id = info.get('sample', '')
                length = info.get('length', '0')
                completeness = info.get('completeness', 'Unknown')

                # Extract year from sample ID (e.g., SRR30276930_vibrant)
                # We'll need to look this up from the sample metadata
                # For now, set to Unknown
                year = 'Unknown'
                organism = 'Unknown'

                metadata.append({
                    'prophage_id': prophage_id,
                    'sample_id': sample_id,
                    'year': year,
                    'organism': organism,
                    'length_bp': length,
                    'completeness': completeness
                })

    print(f"  Found {len(metadata)} prophages")

    # Write TSV
    print(f"Writing metadata to: {output_tsv}")
    with open(output_tsv, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['prophage_id', 'sample_id', 'year', 'organism', 'length_bp', 'completeness'])

        for entry in metadata:
            writer.writerow([
                entry['prophage_id'],
                entry['sample_id'],
                entry['year'],
                entry['organism'],
                entry['length_bp'],
                entry['completeness']
            ])

    print(f"✅ Wrote {len(metadata)} entries to metadata file")
    return len(metadata)

def main():
    fasta_file = '/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny/complete_prophages.fasta'
    output_tsv = '/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny/prophage_metadata.tsv'

    print("=" * 70)
    print("Fixing Prophage Metadata")
    print("=" * 70)
    print()

    if not Path(fasta_file).exists():
        print(f"❌ ERROR: FASTA file not found: {fasta_file}")
        sys.exit(1)

    n_entries = extract_metadata_from_fasta(fasta_file, output_tsv)

    print()
    print("=" * 70)
    print("✅ Metadata file regenerated!")
    print("=" * 70)
    print()
    print(f"Created metadata for {n_entries} prophages")
    print()
    print("Note: Year and organism are set to 'Unknown' for now.")
    print("This is fine for basic phylogenetic analysis.")
    print()
    print("Next step:")
    print("  bash run_subsample_phylogeny.sh")
    print()

if __name__ == '__main__':
    main()
