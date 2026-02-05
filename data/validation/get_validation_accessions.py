#!/usr/bin/env python3
"""
Get Validation Assembly Accessions
Programmatically collects E. coli assembly accessions from NCBI for COMPASS validation.

Queries NCBI Assembly database using Entrez E-utilities to collect:
- Tier 3: 50 FDA-ARGOS E. coli genomes (BioProject PRJNA231221)
- Tier 4: 100 Diverse complete E. coli genomes (RefSeq)
- Tier 5: 30 Major sequence type representatives

Appends results to existing validation_samplesheet.csv
"""

import csv
import sys
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

# NCBI Entrez E-utilities configuration
ENTREZ_EMAIL = "tdoerks@vet.k-state.edu"
ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def query_ncbi_assemblies(query, retmax=100):
    """Query NCBI Assembly database and return assembly accessions."""
    print(f"Querying NCBI: {query}")
    print(f"Requesting up to {retmax} results...")

    try:
        # Step 1: Search assembly database
        search_params = {
            'db': 'assembly',
            'term': query,
            'retmax': str(retmax),
            'email': ENTREZ_EMAIL
        }
        search_url = f"{ENTREZ_BASE}/esearch.fcgi?" + urllib.parse.urlencode(search_params)

        with urllib.request.urlopen(search_url) as response:
            search_xml = response.read().decode('utf-8')

        search_root = ET.fromstring(search_xml)
        id_list = [id_elem.text for id_elem in search_root.findall('.//Id')]

        print(f"Found {len(id_list)} assemblies")

        if len(id_list) == 0:
            return []

        # Step 2: Fetch assembly details in batches (avoid URI too long error)
        assemblies = []
        batch_size = 100  # Process 100 IDs at a time

        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i+batch_size]
            time.sleep(0.5)  # Rate limiting

            summary_params = {
                'db': 'assembly',
                'id': ','.join(batch_ids),
                'email': ENTREZ_EMAIL
            }
            summary_url = f"{ENTREZ_BASE}/esummary.fcgi?" + urllib.parse.urlencode(summary_params)

            with urllib.request.urlopen(summary_url) as response:
                summary_xml = response.read().decode('utf-8')

            summary_root = ET.fromstring(summary_xml)

            # Process this batch
            for doc in summary_root.findall('.//DocumentSummary'):
                # Extract assembly accession (RefSeq preferred)
                accession_elem = doc.find(".//AssemblyAccession")
                accession = accession_elem.text if accession_elem is not None else ''

                # Extract strain/isolate name
                species_elem = doc.find(".//SpeciesName")
                strain = species_elem.text.replace('Escherichia coli', '').strip() if species_elem is not None else ''

                # Get assembly level
                status_elem = doc.find(".//AssemblyStatus")
                assembly_level = status_elem.text if status_elem is not None else ''

                # Only include Complete Genome or Chromosome level assemblies
                if assembly_level not in ['Complete Genome', 'Chromosome']:
                    continue

                # Skip if no accession or not RefSeq
                if not accession or not accession.startswith('GCF_'):
                    continue

                assemblies.append({
                    'accession': accession,
                    'strain': strain,
                    'organism': 'Escherichia',
                    'assembly_level': assembly_level
                })

        print(f"Filtered to {len(assemblies)} complete/chromosome assemblies")
        return assemblies

    except Exception as e:
        print(f"ERROR querying NCBI: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return []

def load_existing_accessions(csv_path):
    """Load existing assembly accessions from samplesheet."""
    existing = set()
    if Path(csv_path).exists():
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'assembly_accession' in row:
                    existing.add(row['assembly_accession'])
    print(f"Loaded {len(existing)} existing accessions from {csv_path}")
    return existing

def get_tier3_fda_argos(existing_accessions, target=50):
    """Get Tier 3: FDA-ARGOS E. coli genomes."""
    print("\n" + "="*60)
    print("TIER 3: FDA-ARGOS E. coli Genomes")
    print("="*60)

    query = '"Escherichia coli"[Organism] AND PRJNA231221[BioProject] AND ("Complete Genome"[Assembly Level] OR "Chromosome"[Assembly Level])'

    assemblies = query_ncbi_assemblies(query, retmax=100)

    # Filter out existing accessions
    new_assemblies = [a for a in assemblies if a['accession'] not in existing_accessions]

    # Select up to target number
    selected = new_assemblies[:target]

    print(f"Selected {len(selected)} FDA-ARGOS genomes (target: {target})")
    return selected

def get_tier4_diverse(existing_accessions, target=100):
    """Get Tier 4: Diverse complete E. coli genomes."""
    print("\n" + "="*60)
    print("TIER 4: Diverse Complete E. coli Genomes")
    print("="*60)

    # Broader query - include both Complete Genome and Chromosome levels
    query = '"Escherichia coli"[Organism] AND ("Complete Genome"[Assembly Level] OR "Chromosome"[Assembly Level])'

    assemblies = query_ncbi_assemblies(query, retmax=500)

    # Filter out existing accessions
    new_assemblies = [a for a in assemblies if a['accession'] not in existing_accessions]

    # Select diverse subset (every nth genome for diversity)
    if len(new_assemblies) > target:
        step = len(new_assemblies) // target
        selected = [new_assemblies[i*step] for i in range(target)]
    else:
        selected = new_assemblies[:target]

    print(f"Selected {len(selected)} diverse genomes (target: {target})")
    return selected

def get_tier5_major_sts(existing_accessions, target=30):
    """Get Tier 5: Major sequence type representatives."""
    print("\n" + "="*60)
    print("TIER 5: Major Sequence Type Representatives")
    print("="*60)

    # Major ExPEC sequence types - use broader strain-based searches
    major_sts = [
        ('ST131', '"Escherichia coli"[Organism] AND (ST131[All Fields] OR "sequence type 131"[All Fields])'),
        ('ST95', '"Escherichia coli"[Organism] AND (ST95[All Fields] OR "sequence type 95"[All Fields])'),
        ('ST73', '"Escherichia coli"[Organism] AND (ST73[All Fields] OR "sequence type 73"[All Fields])'),
        ('ST69', '"Escherichia coli"[Organism] AND (ST69[All Fields] OR "sequence type 69"[All Fields])'),
        ('ST127', '"Escherichia coli"[Organism] AND (ST127[All Fields] OR "sequence type 127"[All Fields])'),
        ('ST10', '"Escherichia coli"[Organism] AND (ST10[All Fields] OR "sequence type 10"[All Fields])'),
        ('ST38', '"Escherichia coli"[Organism] AND (ST38[All Fields] OR "sequence type 38"[All Fields])'),
        ('ST405', '"Escherichia coli"[Organism] AND (ST405[All Fields] OR "sequence type 405"[All Fields])'),
        ('ST648', '"Escherichia coli"[Organism] AND (ST648[All Fields] OR "sequence type 648"[All Fields])'),
        ('ST167', '"Escherichia coli"[Organism] AND (ST167[All Fields] OR "sequence type 167"[All Fields])'),
    ]

    selected = []
    per_st = max(3, target // len(major_sts))  # At least 3 per ST

    for st_name, st_query in major_sts:
        if len(selected) >= target:
            break

        print(f"\nSearching for {st_name}...")
        # Remove RefSeq filter - too restrictive
        query = f'{st_query} AND ("Complete Genome"[Assembly Level] OR "Chromosome"[Assembly Level])'

        assemblies = query_ncbi_assemblies(query, retmax=20)

        # Filter out existing accessions
        new_assemblies = [a for a in assemblies if a['accession'] not in existing_accessions]

        # Select up to per_st genomes
        st_selected = new_assemblies[:per_st]

        # Tag with ST name
        for asm in st_selected:
            asm['st'] = st_name

        selected.extend(st_selected)
        print(f"  Added {len(st_selected)} {st_name} genomes")

        time.sleep(0.5)  # Rate limiting between queries

    # Trim to target if we have too many
    selected = selected[:target]

    print(f"\nSelected {len(selected)} ST representative genomes (target: {target})")
    return selected

def append_to_samplesheet(csv_path, tier_name, assemblies):
    """Append assemblies to validation samplesheet."""
    if not assemblies:
        print(f"No assemblies to add for {tier_name}")
        return 0

    added_count = 0
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)

        for i, asm in enumerate(assemblies, 1):
            # Generate sample name
            if 'st' in asm:
                sample_name = f"{asm['st']}_{i:03d}"
            else:
                sample_name = f"{tier_name}_{i:03d}"

            # Write row
            writer.writerow([sample_name, asm['organism'], asm['accession']])
            added_count += 1

    print(f"Appended {added_count} assemblies to {csv_path}")
    return added_count

def main():
    """Main execution."""
    print("="*60)
    print("COMPASS Validation Dataset - Assembly Accession Collection")
    print("="*60)

    # File paths
    script_dir = Path(__file__).parent
    csv_path = script_dir / "validation_samplesheet.csv"

    if not csv_path.exists():
        print(f"ERROR: Samplesheet not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    # Load existing accessions (Tier 1 & 2)
    existing = load_existing_accessions(csv_path)

    # Collect new accessions
    total_added = 0

    # Tier 3: FDA-ARGOS (50 genomes)
    tier3 = get_tier3_fda_argos(existing, target=50)
    existing.update(a['accession'] for a in tier3)
    count3 = append_to_samplesheet(csv_path, "FDA_ARGOS", tier3)
    total_added += count3

    # Tier 4: Diverse (100 genomes)
    tier4 = get_tier4_diverse(existing, target=100)
    existing.update(a['accession'] for a in tier4)
    count4 = append_to_samplesheet(csv_path, "DIVERSE", tier4)
    total_added += count4

    # Tier 5: Major STs (30 genomes)
    tier5 = get_tier5_major_sts(existing, target=30)
    count5 = append_to_samplesheet(csv_path, "ST", tier5)
    total_added += count5

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Tier 3 (FDA-ARGOS):  {count3} genomes added")
    print(f"Tier 4 (Diverse):    {count4} genomes added")
    print(f"Tier 5 (Major STs):  {count5} genomes added")
    print(f"TOTAL:               {total_added} genomes added")
    print(f"\nExpanded samplesheet: {csv_path}")

    # Count total rows
    with open(csv_path, 'r') as f:
        total_rows = sum(1 for line in f) - 1  # Subtract header

    print(f"Total samples in samplesheet: {total_rows}")
    print("\nReady for COMPASS validation run!")
    print("Next: sbatch data/validation/run_compass_validation.sh")

if __name__ == "__main__":
    main()
