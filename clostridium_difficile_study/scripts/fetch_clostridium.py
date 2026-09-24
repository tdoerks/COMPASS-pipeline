#!/usr/bin/env python3
"""
Fetch Clostridium difficile SRA accessions for oxygen gradient study

Part of comparative prophage burden analysis across oxygen tolerance groups:
- Obligate anaerobes: Fusobacterium, Bacteroides, Clostridium
- Facultative anaerobes: E. coli, Salmonella
- Obligate aerobes: Mycobacterium, Pseudomonas

Hypothesis: Anaerobes have lower prophage burden due to reduced oxidative stress
"""

import time
import urllib.request
import urllib.parse
import json
from xml.etree import ElementTree as ET

def fetch_sra_accessions(organism, platform='illumina', max_results=10000):
    """
    Fetch SRA accessions for a given organism

    Args:
        organism: Scientific name (e.g., 'Clostridium difficile')
        platform: Sequencing platform (default: illumina)
        max_results: Maximum number of results to retrieve

    Returns:
        List of SRR accession numbers
    """

    print("="*70)
    print(f"Fetching {organism} SRA Accessions")
    print("="*70)
    print()

    # Search query
    search_term = f'{organism}[Organism] AND {platform}[Platform] AND GENOMIC[Source] AND WGS[Strategy]'

    print(f"Search query: {search_term}")
    print()

    # Step 1: esearch to get count and IDs
    print("Step 1: Searching NCBI SRA database...")
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        'db': 'sra',
        'term': search_term,
        'retmax': max_results,
        'retmode': 'json'
    }

    url = f"{esearch_url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())

    if 'esearchresult' not in data:
        print("ERROR: No results found")
        return []

    count = int(data['esearchresult']['count'])
    id_list = data['esearchresult']['idlist']

    print(f"Total matching records: {count}")
    print(f"Retrieved IDs: {len(id_list)}")
    print()

    # Step 2: efetch to get SRR accessions
    print("Step 2: Fetching SRR accessions...")
    print("(This may take a few minutes...)")
    print()

    accessions = []

    # Process in batches of 100
    batch_size = 100
    for i in range(0, len(id_list), batch_size):
        batch = id_list[i:i+batch_size]

        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            'db': 'sra',
            'id': ','.join(batch),
            'retmode': 'xml'
        }

        url = f"{efetch_url}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url) as response:
            # Parse XML
            root = ET.fromstring(response.read())

        # Extract SRR accessions
        for exp_pkg in root.findall('.//EXPERIMENT_PACKAGE'):
            for run in exp_pkg.findall('.//RUN'):
                accession = run.get('accession')
                if accession and accession.startswith('SRR'):
                    accessions.append(accession)

        print(f"Processed {i+len(batch)}/{len(id_list)} IDs... (found {len(accessions)} accessions)")

        # Rate limiting
        time.sleep(0.4)

    print()
    print(f"✓ Total SRR accessions retrieved: {len(accessions)}")
    print()

    return accessions

def save_accessions(accessions, output_file):
    """Save accessions to file"""
    with open(output_file, 'w') as f:
        for acc in accessions:
            f.write(f"{acc}\n")

    print(f"✓ Saved to {output_file}")
    print()

def main():
    """Main execution"""

    organism = "Clostridioides difficile"  # Updated nomenclature
    output_file = "data/sra_accessions_clostridium.txt"

    print("Clostridium difficile SRA Accession Retrieval")
    print()
    print("Study context:")
    print("  - Obligate anaerobe (no oxygen tolerance)")
    print("  - Gut pathogen (C. difficile infection)")
    print("  - Comparison to aerobic/facultative bacteria")
    print("  - Expected: LOW prophage burden (like Fusobacterium)")
    print()

    # Fetch accessions
    accessions = fetch_sra_accessions(organism)

    if not accessions:
        # Try alternative name
        print("No results with 'Clostridioides difficile', trying 'Clostridium difficile'...")
        accessions = fetch_sra_accessions("Clostridium difficile")

    if accessions:
        # Save to file
        save_accessions(accessions, output_file)

        print("="*70)
        print("Summary")
        print("="*70)
        print()
        print(f"Organism: {organism}")
        print(f"Total accessions: {len(accessions)}")
        print(f"Output file: {output_file}")
        print()
        print("Next steps:")
        print("  1. Create samplesheet: python3 scripts/create_samplesheet.py")
        print("  2. Launch pipeline: sbatch run_clostridium.sh")
        print("  3. Compare results to Fusobacterium and Bacteroides")
        print()
        print("Expected outcome:")
        print("  - Low prophage burden (1-2 prophages/genome)")
        print("  - Similar to other obligate anaerobes")
        print("  - Much lower than E. coli (~8) or Salmonella (~4)")
        print()
    else:
        print("ERROR: Failed to retrieve accessions")
        print("Check organism name or search parameters")

if __name__ == "__main__":
    main()
