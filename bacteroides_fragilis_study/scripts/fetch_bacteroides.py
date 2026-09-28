#!/usr/bin/env python3
"""
Fetch Bacteroides fragilis SRA Accessions - Oxygen Gradient Study

Focus: Obligate anaerobe (gut) prophage burden
Organism: Bacteroides fragilis (most abundant gut anaerobe)
Comparison: Same niche as E. coli but obligate anaerobe
Hypothesis: Lower prophage burden than E. coli (facultative)
"""
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime

def fetch_all_bacteroides():
    """Fetch ALL Bacteroides fragilis SRA accessions"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    # Search for Bacteroides fragilis WGS data
    params = {
        'db': 'sra',
        'term': 'Bacteroides fragilis[Organism] AND illumina[Platform] AND GENOMIC[Source] AND WGS[Strategy]',
        'retmax': 10000,
        'retmode': 'json'
    }

    print("="*70)
    print("OXYGEN GRADIENT STUDY - Bacteroides fragilis")
    print("="*70)
    print("Organism: Bacteroides fragilis (obligate anaerobe)")
    print("Niche: Human gut (same as E. coli but anaerobic)")
    print("Expected prophage burden: LOW (1-2/genome like Fusobacterium)")
    print("Comparison: E. coli has 8.2 prophages/genome (facultative)")
    print("="*70)
    print()

    print("Searching NCBI SRA for Bacteroides fragilis WGS...")

    try:
        response = requests.get(base_url, params=params, timeout=30)
        data = response.json()

        id_list = data.get('esearchresult', {}).get('idlist', [])
        count = int(data.get('esearchresult', {}).get('count', 0))
        print(f"Found {count} total Bacteroides fragilis WGS samples")
        print(f"(Will retrieve up to {len(id_list)} accessions)")
        print()

        if id_list:
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

            accessions = []
            for i in range(0, len(id_list), 100):
                batch_ids = id_list[i:i+100]

                print(f"Fetching accessions batch {i//100 + 1}/{(len(id_list)-1)//100 + 1}...", flush=True)

                fetch_params = {
                    'db': 'sra',
                    'id': ','.join(batch_ids),
                    'rettype': 'full',
                    'retmode': 'xml'
                }

                time.sleep(0.4)  # NCBI rate limit
                response = requests.get(fetch_url, params=fetch_params, timeout=60)

                try:
                    root = ET.fromstring(response.content)
                    for run in root.findall('.//RUN'):
                        acc = run.get('accession')
                        if acc and acc.startswith('SRR'):
                            accessions.append(acc)
                except ET.ParseError:
                    print(f"  Warning: Could not parse XML for batch {i//100 + 1}")
                    pass

            print(f"\n✓ Retrieved {len(accessions)} Bacteroides fragilis SRR accessions")
            return accessions

    except Exception as e:
        print(f"ERROR: {e}")

    return []

def main():
    accessions = fetch_all_bacteroides()

    if not accessions:
        print("\n❌ ERROR: No accessions retrieved")
        return

    output_file = "data/sra_accessions_bacteroides.txt"

    with open(output_file, 'w') as f:
        for acc in accessions:
            f.write(f"{acc}\n")

    print(f"\n✓ Saved {len(accessions)} accessions to {output_file}")
    print()
    print("="*70)
    print("Summary")
    print("="*70)
    print(f"Total Bacteroides fragilis samples: {len(accessions)}")
    print(f"Output file: {output_file}")
    print()
    print("Oxygen Gradient Study Context:")
    print("  - Bacteroides fragilis: Obligate anaerobe (THIS STUDY)")
    print("  - Fusobacterium: Obligate anaerobe (1.3 prophages/genome) ✓")
    print("  - E. coli: Facultative anaerobe (8.2 prophages/genome)")
    print("  - Salmonella: Facultative anaerobe (4.2 prophages/genome) ✓")
    print()
    print("Hypothesis:")
    print("  Bacteroides should have LOW prophage burden (1-2/genome)")
    print("  Similar to Fusobacterium due to obligate anaerobic lifestyle")
    print()
    print("Next steps:")
    print("  1. Generate samplesheet: python3 scripts/create_samplesheet.py")
    print("  2. Submit COMPASS job: sbatch run_bacteroides.sh")
    print("="*70)

if __name__ == "__main__":
    main()
