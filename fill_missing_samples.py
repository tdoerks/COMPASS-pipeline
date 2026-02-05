#!/usr/bin/env python3
"""
Fill missing samples in the E. coli monthly dataset.
Fetches exactly the number of samples needed for each incomplete month.
"""
import requests
import random
import time
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

def fetch_sra_accessions(year, month, max_results=500):
    """Fetch SRA accessions for E. coli from a specific month"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    # Format: 2020/01
    date_str = f"{year}/{month:02d}"

    params = {
        'db': 'sra',
        'term': f'Escherichia coli[Organism] AND {date_str}[Release Date] AND illumina[Platform] AND GENOMIC[Source]',
        'retmax': max_results,
        'retmode': 'json'
    }

    print(f"Querying {year}-{month:02d}...", end=" ", flush=True)

    try:
        response = requests.get(base_url, params=params, timeout=30)
        data = response.json()

        id_list = data.get('esearchresult', {}).get('idlist', [])
        count = int(data.get('esearchresult', {}).get('count', 0))
        print(f"Found {count} total", end=" ", flush=True)

        # Fetch SRR accessions from UIDs using XML format
        if id_list:
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

            accessions = []
            # Process in batches of 100
            for i in range(0, min(len(id_list), max_results), 100):
                batch_ids = id_list[i:i+100]

                fetch_params = {
                    'db': 'sra',
                    'id': ','.join(batch_ids),
                    'rettype': 'full',
                    'retmode': 'xml'
                }

                time.sleep(0.4)  # Be nice to NCBI
                response = requests.get(fetch_url, params=fetch_params, timeout=60)

                # Parse XML to get Run accessions
                try:
                    root = ET.fromstring(response.content)
                    for run in root.findall('.//RUN'):
                        acc = run.get('accession')
                        if acc and acc.startswith('SRR'):
                            accessions.append(acc)
                except ET.ParseError:
                    pass

            print(f"→ Got {len(accessions)} accessions")
            return accessions

    except Exception as e:
        print(f"ERROR: {e}")

    return []

def parse_gap_report(report_file):
    """Parse the sample distribution report to find gaps"""
    gaps = []

    with open(report_file, 'r') as f:
        in_summary = False
        for line in f:
            # Look for lines like "  2020-01: 15 samples needed"
            if "Months needing samples:" in line:
                in_summary = True
                continue

            if in_summary:
                if line.strip().startswith("202"):  # Year starts with 202
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        month = parts[0].strip()
                        needed = int(parts[1].split()[0])
                        year, month_num = month.split('-')
                        gaps.append((int(year), int(month_num), needed))

    return gaps

def fill_missing_samples(input_file, report_file, output_file):
    """Fill in missing samples for incomplete months"""

    print("="*70)
    print("Filling Missing E. coli Samples")
    print("="*70)
    print()

    # Read existing samples to avoid duplicates
    with open(input_file, 'r') as f:
        existing_samples = set(line.strip() for line in f if line.strip())

    print(f"Existing samples: {len(existing_samples)}")
    print()

    # Parse gap report
    gaps = parse_gap_report(report_file)

    if not gaps:
        print("No gaps found in report. Dataset appears complete!")
        return

    print(f"Found {len(gaps)} incomplete months")
    print()

    # Fetch missing samples for each gap
    new_samples = []
    total_needed = sum(needed for _, _, needed in gaps)

    for year, month, needed in gaps:
        print(f"\nFetching {needed} samples for {year}-{month:02d}...")

        accessions = fetch_sra_accessions(year, month, max_results=500)

        # Filter out existing samples
        available = [acc for acc in accessions if acc not in existing_samples]

        if len(available) < needed:
            print(f"  WARNING: Only {len(available)} new samples available (needed {needed})")
            sampled = available
        else:
            # Randomly sample the needed amount
            sampled = random.sample(available, needed)

        new_samples.extend(sampled)
        print(f"  ✓ Selected {len(sampled)} new samples")

        time.sleep(1)  # Rate limiting

    # Append new samples to file
    print()
    print("="*70)
    print(f"Adding {len(new_samples)} new samples to {output_file}")

    with open(output_file, 'a') as f:
        for sample in new_samples:
            f.write(f"{sample}\n")

    # Report final count
    final_count = len(existing_samples) + len(new_samples)

    print()
    print("="*70)
    print("Complete!")
    print("="*70)
    print(f"Original samples: {len(existing_samples)}")
    print(f"New samples added: {len(new_samples)}")
    print(f"Final total: {final_count}")
    print(f"Target: ~7,142 (73 months × 100 samples)")
    print(f"Completion: {100*final_count/7142:.1f}%")
    print()

if __name__ == "__main__":
    input_file = "sra_accessions_ecoli_monthly_100_2020-2026.txt"
    report_file = "sample_distribution_report.txt"
    output_file = input_file  # Append to same file

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = input_file
    if len(sys.argv) > 2:
        report_file = sys.argv[2]

    try:
        fill_missing_samples(input_file, report_file, output_file)
    except FileNotFoundError as e:
        print(f"ERROR: File not found: {e}")
        print(f"Usage: {sys.argv[0]} [input_file] [report_file]")
        print()
        print("Make sure to run analyze_sample_distribution.py first!")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
