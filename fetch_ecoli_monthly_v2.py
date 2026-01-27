#!/usr/bin/env python3
"""
Fetch E. coli SRA accessions from NCBI
100 random samples per month from January 2020 to January 2026
"""
import requests
import random
import time
import xml.etree.ElementTree as ET

def fetch_sra_accessions(year, month, max_results=1000):
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

    print(f"Fetching {year}-{month:02d}...", end=" ", flush=True)

    try:
        response = requests.get(base_url, params=params, timeout=30)
        data = response.json()

        id_list = data.get('esearchresult', {}).get('idlist', [])
        count = int(data.get('esearchresult', {}).get('count', 0))
        print(f"Found {count} total", end=" ", flush=True)

        # Fetch SRR accessions from UIDs using XML format (more reliable)
        if id_list:
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            
            accessions = []
            # Process in batches of 100
            for i in range(0, min(len(id_list), 500), 100):
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

def main():
    print("="*70)
    print("Fetching E. coli SRA Accessions from NCBI")
    print("Period: January 2020 - January 2026")
    print("Target: 100 random samples per month")
    print("="*70)
    print()

    all_accessions = []
    monthly_counts = []

    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 1:  # Stop at January 2026
                break

            accessions = fetch_sra_accessions(year, month)

            # Sample 100 random (or all if less than 100)
            sample_size = min(100, len(accessions))
            if sample_size > 0:
                sampled = random.sample(accessions, sample_size)
                all_accessions.extend(sampled)
                monthly_counts.append((year, month, sample_size))
                print(f"  ✓ Sampled {sample_size} accessions")
            else:
                print(f"  ✗ No accessions found")

            time.sleep(1)  # Rate limiting for NCBI API

    # Save to file
    output_file = "sra_accessions_ecoli_monthly_100_2020-2026.txt"
    with open(output_file, 'w') as f:
        for acc in all_accessions:
            f.write(f"{acc}\n")

    print()
    print("="*70)
    print(f"Total accessions: {len(all_accessions)}")
    print(f"Saved to: {output_file}")
    print()
    print("Monthly breakdown:")
    for year, month, count in monthly_counts:
        print(f"  {year}-{month:02d}: {count} samples")
    print("="*70)

if __name__ == "__main__":
    main()
