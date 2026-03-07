#!/usr/bin/env python3
"""
Download Diverse Bacterial Pathogen SRA Accessions

Queries NCBI SRA for 20 different bacterial pathogens and downloads
N random samples per organism to create a diverse 1,000-sample dataset.

Usage:
    python download_diverse_bacteria.py --output data/
"""

import argparse
import subprocess
import sys
import time
import random
from pathlib import Path
from collections import defaultdict

def run_esearch(organism, max_samples=50):
    """
    Query NCBI SRA for bacterial samples using esearch/efetch

    Args:
        organism: Scientific name of organism
        max_samples: Maximum number of samples to retrieve

    Returns:
        List of SRR accessions
    """
    print(f"\n{'='*60}")
    print(f"Searching for: {organism}")
    print(f"Target samples: {max_samples}")
    print(f"{'='*60}")

    # Build query with filters
    query = f'"{organism}"[Organism] AND "GENOMIC"[Source] AND "ILLUMINA"[Platform] AND "WGS"[Strategy]'

    print(f"Query: {query}")

    try:
        # Count total results
        count_cmd = [
            'esearch',
            '-db', 'sra',
            '-query', query
        ]

        print("Counting available samples...")
        result = subprocess.run(count_cmd, capture_output=True, text=True, check=True)

        # Extract count from XML
        count_line = [line for line in result.stdout.split('\n') if '<Count>' in line]
        if count_line:
            count = int(count_line[0].replace('<Count>', '').replace('</Count>', '').strip())
            print(f"  Found {count} total samples")
        else:
            print("  Warning: Could not determine count")
            count = max_samples * 2  # Assume enough samples

        # Fetch SRR accessions
        # Get more than needed to allow for random sampling
        fetch_count = min(count, max_samples * 3)

        fetch_cmd = count_cmd + [
            '|', 'efetch', '-format', 'runinfo'
        ]

        print(f"Fetching up to {fetch_count} sample records...")

        # Run as shell command to allow piping
        full_cmd = ' '.join(count_cmd) + ' | efetch -format runinfo'
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, check=True)

        # Parse runinfo CSV
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            print(f"  Warning: No results found for {organism}")
            return []

        header = lines[0].split(',')
        run_col = header.index('Run') if 'Run' in header else 0
        bytes_col = header.index('bytes') if 'bytes' in header else None

        # Extract SRR accessions and filter by size
        srr_accessions = []
        for line in lines[1:]:
            if not line.strip():
                continue
            fields = line.split(',')
            if len(fields) > run_col:
                srr = fields[run_col]

                # Filter by size (1GB to 10GB is reasonable for bacteria)
                if bytes_col and len(fields) > bytes_col:
                    try:
                        size_bytes = int(fields[bytes_col])
                        size_gb = size_bytes / (1024**3)
                        if size_gb < 1 or size_gb > 10:
                            continue  # Skip too small or too large
                    except:
                        pass  # Keep if we can't parse size

                if srr.startswith('SRR') or srr.startswith('ERR') or srr.startswith('DRR'):
                    srr_accessions.append(srr)

        print(f"  Retrieved {len(srr_accessions)} valid accessions")

        # Randomly sample if we have more than needed
        if len(srr_accessions) > max_samples:
            srr_accessions = random.sample(srr_accessions, max_samples)
            print(f"  Randomly sampled {max_samples} accessions")

        return srr_accessions

    except subprocess.CalledProcessError as e:
        print(f"  Error querying NCBI: {e}")
        print(f"  stdout: {e.stdout}")
        print(f"  stderr: {e.stderr}")
        return []
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return []

def save_srr_list(organism, srr_list, output_dir):
    """Save SRR accessions to file"""
    if not srr_list:
        return None

    # Clean organism name for filename
    safe_name = organism.replace(' ', '_').replace('/', '_')
    filename = output_dir / f"{safe_name}_srr_list.txt"

    with open(filename, 'w') as f:
        for srr in srr_list:
            f.write(f"{srr}\n")

    print(f"  Saved {len(srr_list)} accessions to: {filename}")
    return filename

def main():
    parser = argparse.ArgumentParser(
        description='Download diverse bacterial pathogen SRA accessions'
    )
    parser.add_argument(
        '--targets',
        default='scripts/organism_targets.txt',
        help='File with target organisms (default: scripts/organism_targets.txt)'
    )
    parser.add_argument(
        '--output',
        default='data/srr_accessions_by_organism',
        help='Output directory for SRR lists (default: data/srr_accessions_by_organism)'
    )
    parser.add_argument(
        '--combined',
        default='data/combined_srr_list.txt',
        help='Combined output file (default: data/combined_srr_list.txt)'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=3,
        help='Delay between queries in seconds (default: 3)'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read organism targets
    organisms = []
    target_counts = {}

    print("Reading organism targets...")
    with open(args.targets, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|')
            if len(parts) >= 2:
                organism = parts[0].strip()
                count = int(parts[1].strip())
                organisms.append(organism)
                target_counts[organism] = count

    print(f"\nFound {len(organisms)} target organisms")
    print(f"Total target samples: {sum(target_counts.values())}")

    # Download accessions for each organism
    all_srr_files = []
    total_accessions = 0
    results_summary = []

    for i, organism in enumerate(organisms, 1):
        print(f"\n[{i}/{len(organisms)}] Processing: {organism}")

        # Query NCBI
        srr_list = run_esearch(organism, max_samples=target_counts[organism])

        # Save to file
        if srr_list:
            filename = save_srr_list(organism, srr_list, output_dir)
            all_srr_files.append(filename)
            total_accessions += len(srr_list)
            results_summary.append(f"{organism}: {len(srr_list)} samples")
        else:
            print(f"  Warning: No accessions retrieved for {organism}")
            results_summary.append(f"{organism}: 0 samples (FAILED)")

        # Rate limiting
        if i < len(organisms):
            print(f"  Waiting {args.delay} seconds before next query...")
            time.sleep(args.delay)

    # Combine all SRR lists
    print(f"\n{'='*60}")
    print("Creating combined SRR list...")
    print(f"{'='*60}")

    combined_path = Path(args.combined)
    combined_path.parent.mkdir(parents=True, exist_ok=True)

    all_srrs = []
    for srr_file in all_srr_files:
        if srr_file and srr_file.exists():
            with open(srr_file, 'r') as f:
                srrs = [line.strip() for line in f if line.strip()]
                all_srrs.extend(srrs)

    # Remove duplicates
    all_srrs = list(set(all_srrs))

    with open(combined_path, 'w') as f:
        for srr in sorted(all_srrs):
            f.write(f"{srr}\n")

    # Print summary
    print(f"\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"\nResults by organism:")
    for result in results_summary:
        print(f"  {result}")
    print(f"\nTotal accessions retrieved: {len(all_srrs)}")
    print(f"Combined list saved to: {combined_path}")
    print(f"\nIndividual organism files saved to: {output_dir}/")
    print(f"\n{'='*60}")
    print("Next steps:")
    print(f"  1. Review the combined list: cat {combined_path} | wc -l")
    print(f"  2. Generate samplesheet: python scripts/create_samplesheet.py")
    print(f"  3. Run COMPASS pipeline: sbatch run_diverse_bacteria_1000.sh")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
