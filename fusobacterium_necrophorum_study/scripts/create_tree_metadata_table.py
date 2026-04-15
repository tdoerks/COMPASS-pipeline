#!/usr/bin/env python3
"""
Create comprehensive metadata table for prophage tree samples

Maps tree tip labels (SRR_NODE_fragment) to:
- Sample accession (SRR)
- Subspecies
- Host species
- Isolation source
- Geography
- Study details
- Prophage information
"""

import csv
import sys

def extract_sample_from_tree_label(label):
    """Extract SRR accession from tree tip label"""
    # Labels like: SRR10901569_NODE_9_length_118569_cov_128.637039_fragment_3
    # or: _R_SRR10901569_NODE_9... (reverse complement)

    # Remove _R_ prefix if present
    if label.startswith('_R_'):
        label = label[3:]

    # Extract SRR accession (first part before _NODE)
    parts = label.split('_NODE')
    if parts:
        return parts[0]
    return None

def parse_tree_file(tree_file):
    """Extract all sample IDs from tree file"""
    with open(tree_file, 'r') as f:
        tree_string = f.read()

    # Extract all labels (sequences between parentheses/commas and colons)
    import re
    # Match pattern: word characters, underscores, dots up to a colon or comma/paren
    labels = re.findall(r'([A-Za-z0-9_\.]+):', tree_string)

    # Extract unique SRR accessions
    samples = set()
    for label in labels:
        srr = extract_sample_from_tree_label(label)
        if srr and srr.startswith('SRR'):
            samples.add(srr)

    return sorted(samples)

def load_metadata(metadata_file):
    """Load metadata into dictionary keyed by SRR accession"""
    metadata = {}
    with open(metadata_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            # Try multiple possible column names for SRR accession
            srr = row.get('Run', '') or row.get('PublicAccession', '') or row.get('sample', '')
            if srr and srr.startswith('SRR'):
                metadata[srr] = row
    return metadata

def load_prophage_counts(prophage_file):
    """Load prophage counts per sample"""
    counts = {}
    with open(prophage_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            sample = row.get('sample', '')
            count = row.get('prophage_count', '0')
            if sample:
                counts[sample] = int(count)
    return counts

def create_supplementary_table(tree_file, metadata_file, prophage_file, output_file):
    """Create comprehensive supplementary metadata table"""

    print("="*70)
    print("Creating Tree Sample Metadata Table")
    print("="*70)
    print()

    # Parse tree to get samples
    print(f"Parsing tree file: {tree_file}")
    tree_samples = parse_tree_file(tree_file)
    print(f"Found {len(tree_samples)} unique samples in tree")
    print()

    # Load metadata
    print(f"Loading metadata: {metadata_file}")
    metadata = load_metadata(metadata_file)
    print(f"Loaded metadata for {len(metadata)} samples")
    print()

    # Load prophage counts
    print(f"Loading prophage counts: {prophage_file}")
    prophage_counts = load_prophage_counts(prophage_file)
    print(f"Loaded prophage counts for {len(prophage_counts)} samples")
    print()

    # Create output table
    print(f"Creating output table: {output_file}")

    # Define columns for output
    output_columns = [
        'Sample_ID',
        'Subspecies',
        'Host',
        'Isolation_Source',
        'Isolation_Source_Category',
        'Geographic_Location',
        'Country',
        'Collection_Date',
        'BioProject',
        'BioSample',
        'Study_Title',
        'Prophage_Count',
        'Assembly_Size_Mb',
        'Library_Strategy',
        'Platform',
        'Center_Name'
    ]

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_columns, delimiter='\t')
        writer.writeheader()

        for srr in tree_samples:
            meta = metadata.get(srr, {})

            # Extract organism/subspecies - try multiple column names
            organism = (meta.get('Organism', '') or
                       meta.get('organism', '') or
                       meta.get('ScientificName', '') or
                       meta.get('sub_species', '') or
                       'Unknown')

            # Categorize isolation source - try multiple column names
            source = (meta.get('isolation_source', '') or
                     meta.get('isolation source', '') or
                     meta.get('isolation-source', '') or
                     meta.get('source', '')).lower()
            if any(kw in source for kw in ['oral', 'saliva', 'dental', 'plaque', 'mouth', 'tonsil', 'gingiv']):
                source_category = 'Oral'
            elif any(kw in source for kw in ['stool', 'feces', 'fecal', 'colon', 'gut', 'intestin', 'ileum', 'caecum', 'cecum']):
                source_category = 'Gastrointestinal'
            elif any(kw in source for kw in ['blood', 'serum', 'plasma']):
                source_category = 'Blood'
            elif any(kw in source for kw in ['abscess', 'wound', 'pus', 'infection']):
                source_category = 'Clinical'
            else:
                source_category = 'Other'

            # Extract country from geo_loc_name - try multiple column names
            geo = (meta.get('geo_loc_name', '') or
                  meta.get('geographic location (country and/or sea,region)', ''))
            country = geo.split(':')[0] if ':' in geo else geo

            # Get assembly size
            bases = meta.get('bases', '0')
            try:
                size_mb = f"{int(bases) / 1_000_000:.2f}" if bases else ''
            except:
                size_mb = ''

            row = {
                'Sample_ID': srr,
                'Subspecies': organism,
                'Host': meta.get('host', '') or meta.get('Host', ''),
                'Isolation_Source': (meta.get('isolation_source', '') or
                                    meta.get('isolation source', '') or
                                    meta.get('isolation-source', '') or
                                    meta.get('source', '')),
                'Isolation_Source_Category': source_category,
                'Geographic_Location': geo,
                'Country': country,
                'Collection_Date': (meta.get('collection_date', '') or
                                   meta.get('collection date', '') or
                                   meta.get('Collection_date', '')),
                'BioProject': meta.get('BioProject', '') or meta.get('ProjectAccession', ''),
                'BioSample': meta.get('BioSample', ''),
                'Study_Title': meta.get('study_title', '') or meta.get('project_name', ''),
                'Prophage_Count': prophage_counts.get(srr, 0),
                'Assembly_Size_Mb': size_mb,
                'Library_Strategy': meta.get('LibraryStrategy', ''),
                'Platform': meta.get('Platform', ''),
                'Center_Name': meta.get('Center Name', '') or meta.get('CenterName', '')
            }

            writer.writerow(row)

    print(f"✓ Created: {output_file}")
    print()

    # Print summary statistics
    print("="*70)
    print("Summary Statistics")
    print("="*70)
    print()

    # Count by subspecies
    subspecies_counts = {}
    source_counts = {}
    host_counts = {}

    with open(output_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            # Subspecies
            subsp = row['Subspecies']
            subspecies_counts[subsp] = subspecies_counts.get(subsp, 0) + 1

            # Source category
            src = row['Isolation_Source_Category']
            source_counts[src] = source_counts.get(src, 0) + 1

            # Host
            host = row['Host']
            host_counts[host] = host_counts.get(host, 0) + 1

    print("Samples by Subspecies:")
    for subsp, count in sorted(subspecies_counts.items(), key=lambda x: -x[1]):
        print(f"  {subsp}: {count}")
    print()

    print("Samples by Isolation Source Category:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count}")
    print()

    print("Samples by Host:")
    for host, count in sorted(host_counts.items(), key=lambda x: -x[1]):
        print(f"  {host}: {count}")
    print()

    print("="*70)
    print("COMPLETE!")
    print("="*70)
    print()
    print("This file can be used as:")
    print("  1. Supplementary Table for publication")
    print("  2. Reference when interpreting tree")
    print("  3. Input for statistical analyses")
    print()

def main():
    # Default file paths (run from repository root)
    tree_file = "fusobacterium_results/analysis/phylogenomics/prophage_tree.nwk"
    metadata_file = "fusobacterium_necrophorum_study/data/fusobacterium_metadata.tsv"
    prophage_file = "fusobacterium_necrophorum_study/data/fusobacterium_metadata_prophage_merged.tsv"
    output_file = "fusobacterium_necrophorum_study/data/tree_sample_metadata_supplementary.tsv"

    # Allow command line arguments
    if len(sys.argv) > 1:
        tree_file = sys.argv[1]
    if len(sys.argv) > 2:
        metadata_file = sys.argv[2]
    if len(sys.argv) > 3:
        prophage_file = sys.argv[3]
    if len(sys.argv) > 4:
        output_file = sys.argv[4]

    create_supplementary_table(tree_file, metadata_file, prophage_file, output_file)

if __name__ == "__main__":
    main()
