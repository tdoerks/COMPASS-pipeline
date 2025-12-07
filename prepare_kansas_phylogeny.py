#!/usr/bin/env python3
"""
Prepare Kansas Prophages for Phylogenetic Analysis

Extracts high-quality complete prophages from Kansas 2021-2025 COMPASS results
for phylogenetic tree construction.

Usage:
    python3 prepare_kansas_phylogeny.py --results-dir /bulk/tylerdoe/archives/compass_kansas_results

Output:
    - kansas_complete_prophages.fasta
    - kansas_prophage_metadata.tsv
    - phylogeny_stats.txt
"""

import argparse
import csv
from pathlib import Path
from Bio import SeqIO
from collections import defaultdict


def find_vibrant_results(results_dir):
    """Find all VIBRANT genome quality files"""
    print("Searching for VIBRANT results...")

    results_path = Path(results_dir)
    vibrant_files = list(results_path.rglob('VIBRANT_genome_quality_*.tsv'))

    print(f"  Found {len(vibrant_files)} VIBRANT quality files")
    return vibrant_files


def parse_vibrant_quality(quality_file, debug=False):
    """Parse VIBRANT genome quality file to find complete prophages"""
    complete_prophages = []

    try:
        with open(quality_file) as f:
            reader = csv.DictReader(f, delimiter='\t')

            # Debug: print first row to see column names
            if debug:
                first_row = next(reader, None)
                if first_row:
                    print(f"  Debug - Columns in {quality_file.name}:")
                    print(f"    {list(first_row.keys())}")
                    print(f"  Debug - First row values:")
                    for k, v in first_row.items():
                        print(f"    {k}: {v}")
                    # Process first row
                    quality = first_row.get('Quality', first_row.get('quality', '')).lower()
                    scaffold_name = first_row.get('scaffold', first_row.get('fragment', ''))
                    try:
                        if 'length_' in scaffold_name:
                            # Extract from scaffold name
                            length = int(scaffold_name.split('length_')[1].split('_')[0])
                        else:
                            length = int(first_row.get('length', first_row.get('fragment length', 0)))
                    except (ValueError, TypeError, IndexError):
                        length = 0

                    if quality in ['complete', 'complete circular', 'high quality', 'high quality draft'] and length >= 15000:
                        complete_prophages.append({
                            'scaffold': scaffold_name,
                            'length': length,
                            'quality': quality,
                            'file': quality_file
                        })

            # Process remaining rows
            for row in reader:
                # Try different possible column names (case-insensitive)
                quality = row.get('Quality', row.get('quality', '')).lower()

                # Extract length from scaffold name if not in separate column
                # Format: NODE_3_length_75406_cov_3.848415_fragment_1
                scaffold_name = row.get('scaffold', row.get('fragment', ''))
                try:
                    if 'length_' in scaffold_name:
                        # Extract from scaffold name
                        length = int(scaffold_name.split('length_')[1].split('_')[0])
                    else:
                        length = int(row.get('length', row.get('fragment length', 0)))
                except (ValueError, TypeError, IndexError):
                    length = 0

                # Keep complete and high quality prophages >= 15kb
                # VIBRANT quality types: "complete circular", "high quality draft", "medium quality draft", "low quality draft"
                if quality in ['complete', 'complete circular', 'high quality', 'high quality draft'] and length >= 15000:
                    complete_prophages.append({
                        'scaffold': scaffold_name,
                        'length': length,
                        'quality': quality,
                        'file': quality_file
                    })
    except Exception as e:
        print(f"  Warning: Could not parse {quality_file}: {e}")

    return complete_prophages


def extract_sample_id(vibrant_path):
    """Extract sample ID from VIBRANT file path"""
    # Path format: .../vibrant/SRR12345_vibrant/VIBRANT_SRR12345/...
    # or: .../vibrant/SRR12345/VIBRANT_SRR12345/...
    parts = vibrant_path.parts

    # Find 'vibrant' in path, sample ID should be next directory
    for i, part in enumerate(parts):
        if part == 'vibrant' and i + 1 < len(parts):
            sample_id = parts[i + 1]
            # Remove _vibrant suffix if present
            if sample_id.endswith('_vibrant'):
                sample_id = sample_id[:-8]  # Remove last 8 characters (_vibrant)
            return sample_id

    return 'Unknown'


def load_sample_metadata(results_dir, debug=False):
    """Load sample metadata from filtered_samples.csv files"""
    print("\nLoading sample metadata...")

    metadata = {}
    results_path = Path(results_dir)

    # Look for all filtered_samples.csv files
    for filtered_file in results_path.rglob('filtered_samples/filtered_samples.csv'):
        try:
            with open(filtered_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    srr_id = row.get('Run', '')
                    if srr_id:  # Only add if we have a valid Run ID
                        metadata[srr_id] = {
                            'organism': row.get('organism', 'Unknown'),
                            'sample_name': row.get('SampleName', ''),
                            'year': row.get('Year', 'Unknown')  # Changed from Collection_Date to Year
                        }
                        if debug and len(metadata) <= 3:  # Show first 3 samples
                            print(f"  Debug - Sample {srr_id}: organism={row.get('organism')}, year={row.get('Year')}")
        except Exception as e:
            print(f"  Warning: Could not read {filtered_file}: {e}")

    print(f"  Loaded metadata for {len(metadata)} samples")
    if debug and metadata:
        print(f"  Debug - First metadata key: {list(metadata.keys())[0]}")
    return metadata


def extract_year_from_sample(sample_name, collection_date):
    """Extract year from sample name or collection date"""
    # Try collection date first
    if collection_date and collection_date != 'Unknown':
        try:
            # Collection date might be YYYY-MM-DD or just YYYY
            year = collection_date.split('-')[0]
            if year.isdigit() and len(year) == 4:
                return int(year)
        except:
            pass

    # Try to extract year from sample name (e.g., "KS-2024-12345")
    if sample_name:
        parts = sample_name.split('-')
        for part in parts:
            if part.isdigit() and len(part) == 4 and part.startswith('20'):
                return int(part)

    return None


def extract_prophage_sequences(complete_prophages, sample_metadata, output_fasta, output_metadata, debug=False):
    """Extract prophage sequences from VIBRANT phages_combined files"""
    print(f"\nExtracting prophage sequences...")

    extracted_count = 0
    sequences = []
    metadata_rows = []

    # Group prophages by sample
    by_sample = defaultdict(list)
    for prophage in complete_prophages:
        sample_id = extract_sample_id(prophage['file'])
        by_sample[sample_id].append(prophage)

    print(f"  Processing {len(by_sample)} samples...")

    if debug:
        first_sample = list(by_sample.keys())[0] if by_sample else None
        if first_sample:
            print(f"  Debug - First extracted sample ID: '{first_sample}'")
            print(f"  Debug - Is it in metadata? {first_sample in sample_metadata}")
            if first_sample in sample_metadata:
                print(f"  Debug - Metadata: {sample_metadata[first_sample]}")

    for sample_id, prophages in by_sample.items():
        # Find phages_combined.fna file for this sample
        sample_vibrant_dir = prophages[0]['file'].parent.parent
        phage_files = list(sample_vibrant_dir.rglob('*.phages_combined.fna'))

        if not phage_files:
            print(f"  Warning: No phages_combined.fna found for {sample_id}")
            continue

        # Get metadata for this sample
        sample_meta = sample_metadata.get(sample_id, {})
        organism = sample_meta.get('organism', 'Unknown')
        sample_name = sample_meta.get('sample_name', '')
        year = sample_meta.get('year', 'Unknown')

        # Convert year to int if possible, or extract from sample name
        if year != 'Unknown' and year:
            try:
                # Handle float values like 2024.0
                year = int(float(year))
            except (ValueError, TypeError):
                year = 'Unknown'

        # If year is still Unknown, try to extract from sample name
        # Format: 24KS04GT05-EC or 23KS12CL01-EC
        if year == 'Unknown' and sample_name:
            # Extract first 2 digits if sample name starts with digits
            if len(sample_name) >= 2 and sample_name[:2].isdigit():
                year_prefix = sample_name[:2]
                # Convert to full year (24 -> 2024, 23 -> 2023)
                year = 2000 + int(year_prefix)

        # Parse the phages_combined.fna file
        for phage_file in phage_files:
            for record in SeqIO.parse(phage_file, 'fasta'):
                # Check if this prophage is in our complete list
                for prophage in prophages:
                    if prophage['scaffold'] in record.id:
                        # Create unique ID
                        prophage_id = f"{sample_id}_{record.id}"

                        # Update record
                        record.id = prophage_id
                        record.description = f"sample={sample_id} organism={organism} year={year} length={prophage['length']} quality={prophage['quality']}"

                        sequences.append(record)

                        metadata_rows.append({
                            'prophage_id': prophage_id,
                            'sample_id': sample_id,
                            'organism': organism,
                            'year': year if year else 'Unknown',
                            'length_bp': prophage['length'],
                            'quality': prophage['quality'],
                            'sample_name': sample_name
                        })

                        extracted_count += 1
                        break

    # Write sequences
    SeqIO.write(sequences, output_fasta, 'fasta')
    print(f"  ✅ Extracted {extracted_count} prophage sequences")
    print(f"  ✅ Saved to: {output_fasta}")

    # Write metadata
    with open(output_metadata, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['prophage_id', 'sample_id', 'organism', 'year', 'length_bp', 'quality', 'sample_name'], delimiter='\t')
        writer.writeheader()
        writer.writerows(metadata_rows)

    print(f"  ✅ Saved metadata: {output_metadata}")

    return metadata_rows


def print_statistics(prophage_metadata, output_file):
    """Generate and print statistics"""
    print("\n" + "=" * 70)
    print("Kansas Prophage Statistics")
    print("=" * 70)

    total = len(prophage_metadata)
    print(f"\nTotal complete prophages: {total}")

    # By year
    by_year = defaultdict(int)
    for p in prophage_metadata:
        by_year[p['year']] += 1

    print("\nProphages by year:")
    for year in sorted(by_year.keys(), key=lambda x: (isinstance(x, str), x)):
        print(f"  {year}: {by_year[year]}")

    # By organism
    by_organism = defaultdict(int)
    for p in prophage_metadata:
        by_organism[p['organism']] += 1

    print("\nProphages by organism:")
    for organism in sorted(by_organism.keys()):
        print(f"  {organism}: {by_organism[organism]}")

    # Length statistics
    lengths = [p['length_bp'] for p in prophage_metadata]
    if lengths:
        print(f"\nLength statistics:")
        print(f"  Mean: {sum(lengths)/len(lengths):.0f} bp")
        print(f"  Min: {min(lengths)} bp")
        print(f"  Max: {max(lengths)} bp")

    print("=" * 70)

    # Write to file
    with open(output_file, 'w') as f:
        f.write("Kansas Prophage Statistics\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total complete prophages: {total}\n\n")

        f.write("Prophages by year:\n")
        for year in sorted(by_year.keys(), key=lambda x: (isinstance(x, str), x)):
            f.write(f"  {year}: {by_year[year]}\n")

        f.write("\nProphages by organism:\n")
        for organism in sorted(by_organism.keys()):
            f.write(f"  {organism}: {by_organism[organism]}\n")

        if lengths:
            f.write(f"\nLength statistics:\n")
            f.write(f"  Mean: {sum(lengths)/len(lengths):.0f} bp\n")
            f.write(f"  Min: {min(lengths)} bp\n")
            f.write(f"  Max: {max(lengths)} bp\n")


def main():
    parser = argparse.ArgumentParser(description='Prepare Kansas prophages for phylogenetic analysis')
    parser.add_argument('--results-dir',
                       default='/bulk/tylerdoe/archives/compass_kansas_results',
                       help='Base directory with Kansas COMPASS results')
    parser.add_argument('--output-dir',
                       default='.',
                       help='Output directory for phylogeny files')
    parser.add_argument('--min-length',
                       type=int,
                       default=15000,
                       help='Minimum prophage length in bp (default: 15000)')

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_fasta = output_dir / 'kansas_complete_prophages.fasta'
    output_metadata = output_dir / 'kansas_prophage_metadata.tsv'
    output_stats = output_dir / 'phylogeny_stats.txt'

    print("=" * 70)
    print("Kansas Prophage Phylogeny Preparation")
    print("=" * 70)
    print(f"Results directory: {results_dir}")
    print(f"Minimum length: {args.min_length} bp")
    print(f"Output directory: {output_dir}")
    print("")

    # Find VIBRANT results
    vibrant_files = find_vibrant_results(results_dir)

    if not vibrant_files:
        print("\n❌ No VIBRANT results found!")
        print(f"   Check that {results_dir} contains VIBRANT output directories")
        return 1

    # Parse quality files
    print("\nParsing VIBRANT quality assessments...")
    all_complete_prophages = []
    debug_first = True  # Enable debug for first file only
    for vf in vibrant_files:
        prophages = parse_vibrant_quality(vf, debug=debug_first)
        all_complete_prophages.extend(prophages)
        debug_first = False  # Disable after first file

    print(f"  Found {len(all_complete_prophages)} complete prophages (>={args.min_length} bp)")

    if not all_complete_prophages:
        print("\n❌ No complete prophages found!")
        return 1

    # Load sample metadata
    sample_metadata = load_sample_metadata(results_dir, debug=True)

    # Extract sequences
    prophage_metadata = extract_prophage_sequences(
        all_complete_prophages,
        sample_metadata,
        output_fasta,
        output_metadata,
        debug=True
    )

    if not prophage_metadata:
        print("\n❌ No sequences extracted!")
        return 1

    # Print statistics
    print_statistics(prophage_metadata, output_stats)

    print("\n" + "=" * 70)
    print("✅ Phylogeny preparation complete!")
    print("=" * 70)
    print(f"\n📁 Output files:")
    print(f"   {output_fasta}")
    print(f"   {output_metadata}")
    print(f"   {output_stats}")

    print(f"\n📖 Next steps:")

    total = len(prophage_metadata)
    if total > 500:
        print(f"\n⚠️  You have {total} prophages - this is a lot for phylogenetic analysis!")
        print(f"   Consider subsampling:")
        print(f"   python3 bin/subsample_prophages_for_phylogeny.py \\")
        print(f"       --strategy representative \\")
        print(f"       --n 200 \\")
        print(f"       --input-fasta {output_fasta} \\")
        print(f"       --input-metadata {output_metadata} \\")
        print(f"       --output-fasta kansas_subsample.fasta \\")
        print(f"       --output-metadata kansas_subsample_metadata.tsv")
        print(f"\n   Then align the subsampled set:")
        print(f"   mafft --auto --thread 16 kansas_subsample.fasta > kansas_subsample_aligned.fasta")
    else:
        print(f"\n   1. Align sequences:")
        print(f"      mafft --auto --thread 16 {output_fasta} > kansas_aligned.fasta")

    print(f"\n   2. Build phylogenetic tree:")
    print(f"      sbatch build_phylogeny_kansas.slurm")

    print(f"\n   3. Visualize with iTOL (https://itol.embl.de/)")
    print(f"      - Upload the .treefile")
    print(f"      - Upload {output_metadata} for annotations")

    print("\n" + "=" * 70)

    return 0


if __name__ == '__main__':
    exit(main())
