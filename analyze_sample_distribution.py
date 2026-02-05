#!/usr/bin/env python3
"""
Analyze the distribution of recovered E. coli samples by month/year.
Identifies gaps in the monthly sampling strategy.
"""
import requests
import time
import sys
from collections import defaultdict
from datetime import datetime

def get_srr_release_date(srr_id):
    """Query NCBI for the release date of an SRR accession"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    params = {
        'db': 'sra',
        'term': f'{srr_id}[Accession]',
        'retmode': 'json',
        'retmax': 1
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()

        id_list = data.get('esearchresult', {}).get('idlist', [])
        if not id_list:
            return None

        # Get detailed info using esummary
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {
            'db': 'sra',
            'id': id_list[0],
            'retmode': 'json'
        }

        time.sleep(0.35)  # Rate limiting
        summary_response = requests.get(summary_url, params=summary_params, timeout=10)
        summary_data = summary_response.json()

        # Extract date from the result
        result = summary_data.get('result', {})
        uid = id_list[0]
        if uid in result:
            runs = result[uid].get('runs', '')
            # Parse the XML-like runs string for date
            # Format: <Run acc="SRR..." ... published="2020-01-15"...
            import re
            date_match = re.search(r'published="(\d{4}-\d{2})-\d{2}"', runs)
            if date_match:
                return date_match.group(1)  # Returns YYYY-MM

        return None

    except Exception as e:
        print(f"Error fetching {srr_id}: {e}", file=sys.stderr)
        return None

def analyze_distribution(input_file, output_file):
    """Analyze the distribution of samples by month/year"""

    print("="*70)
    print("Analyzing E. coli Sample Distribution by Month")
    print("="*70)
    print()

    # Read all SRR accessions
    with open(input_file, 'r') as f:
        srr_list = [line.strip() for line in f if line.strip()]

    print(f"Total samples to analyze: {len(srr_list)}")
    print()

    # Query NCBI for each sample's release date
    monthly_counts = defaultdict(int)
    failed_queries = []

    for i, srr in enumerate(srr_list, 1):
        if i % 100 == 0:
            print(f"Progress: {i}/{len(srr_list)} ({100*i/len(srr_list):.1f}%)")

        release_date = get_srr_release_date(srr)
        if release_date:
            monthly_counts[release_date] += 1
        else:
            failed_queries.append(srr)

    print()
    print("="*70)
    print("Analysis Complete")
    print("="*70)
    print()

    # Generate all expected months from 2020-01 to 2026-01
    expected_months = []
    for year in range(2020, 2027):
        for month in range(1, 13):
            month_str = f"{year}-{month:02d}"
            expected_months.append(month_str)
            if month_str == "2026-01":
                break
        if year == 2026:
            break

    # Generate report
    with open(output_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("E. coli Sample Distribution Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")

        f.write(f"Total samples analyzed: {len(srr_list)}\n")
        f.write(f"Failed queries: {len(failed_queries)}\n")
        f.write(f"Successfully dated: {sum(monthly_counts.values())}\n\n")

        f.write("="*70 + "\n")
        f.write("Monthly Distribution\n")
        f.write("="*70 + "\n\n")

        total_missing = 0
        incomplete_months = []

        for month in expected_months:
            count = monthly_counts.get(month, 0)
            missing = max(0, 100 - count)
            total_missing += missing

            status = "✓" if count >= 100 else "✗"
            f.write(f"{status} {month}: {count:3d} samples", )

            if missing > 0:
                f.write(f" (missing {missing})\n")
                incomplete_months.append((month, missing))
            else:
                f.write("\n")

        f.write("\n")
        f.write("="*70 + "\n")
        f.write("Summary\n")
        f.write("="*70 + "\n\n")

        complete_months = len([m for m in expected_months if monthly_counts.get(m, 0) >= 100])
        f.write(f"Complete months (≥100 samples): {complete_months}/{len(expected_months)}\n")
        f.write(f"Incomplete months: {len(incomplete_months)}/{len(expected_months)}\n")
        f.write(f"Total missing samples: {total_missing}\n\n")

        if incomplete_months:
            f.write("Months needing samples:\n")
            for month, missing in incomplete_months:
                f.write(f"  {month}: {missing} samples needed\n")

        if failed_queries:
            f.write(f"\n\nFailed queries ({len(failed_queries)}):\n")
            for srr in failed_queries[:20]:  # Show first 20
                f.write(f"  {srr}\n")
            if len(failed_queries) > 20:
                f.write(f"  ... and {len(failed_queries)-20} more\n")

    # Print summary to console
    print(f"Report saved to: {output_file}")
    print()
    print("Summary:")
    print(f"  Complete months: {complete_months}/{len(expected_months)}")
    print(f"  Incomplete months: {len(incomplete_months)}")
    print(f"  Total missing: {total_missing} samples")
    print()

    if incomplete_months:
        print("Top 10 months needing samples:")
        for month, missing in sorted(incomplete_months, key=lambda x: -x[1])[:10]:
            print(f"  {month}: {missing} samples")

if __name__ == "__main__":
    input_file = "sra_accessions_ecoli_monthly_100_2020-2026.txt"
    output_file = "sample_distribution_report.txt"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        analyze_distribution(input_file, output_file)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_file}")
        print(f"Usage: {sys.argv[0]} [input_file] [output_file]")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
