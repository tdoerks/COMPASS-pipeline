#!/usr/bin/env python3
"""
Create quick reference guide for tree tip labels

Simple lookup table:
Tree Label → Subspecies, Host, Source

Easy to use while viewing the tree in iTOL
"""

import csv
import sys
import re

def extract_all_labels_from_tree(tree_file):
    """Extract all tip labels from tree file"""
    with open(tree_file, 'r') as f:
        tree_string = f.read()

    # Extract labels (between comma/paren and colon)
    labels = re.findall(r'([A-Za-z0-9_\.]+):', tree_string)
    return labels

def extract_sample_from_label(label):
    """Extract SRR from label like SRR10901569_NODE_9_..."""
    if label.startswith('_R_'):
        label = label[3:]
    parts = label.split('_NODE')
    if parts:
        return parts[0]
    return None

def load_metadata(metadata_file):
    """Load metadata"""
    metadata = {}
    with open(metadata_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            # Try multiple possible column names for SRR accession
            # Note: Some metadata files have SRR in 'Genus' column (mislabeled)
            srr = (row.get('Run', '') or
                   row.get('PublicAccession', '') or
                   row.get('sample', '') or
                   row.get('Genus', ''))  # Sometimes mislabeled!
            if srr and srr.startswith('SRR'):
                metadata[srr] = row
    return metadata

def create_quick_reference(tree_file, metadata_file, output_file):
    """Create quick reference lookup table"""

    print("="*70)
    print("Creating Tree Quick Reference Guide")
    print("="*70)
    print()

    # Get all labels from tree
    print(f"Parsing tree: {tree_file}")
    labels = extract_all_labels_from_tree(tree_file)
    print(f"Found {len(labels)} tip labels")
    print()

    # Load metadata
    print(f"Loading metadata: {metadata_file}")
    metadata = load_metadata(metadata_file)
    print(f"Loaded metadata for {len(metadata)} samples")
    print()

    # Create lookup table
    print(f"Creating reference: {output_file}")
    print()

    with open(output_file, 'w') as f:
        f.write("# Fusobacterium Prophage Tree - Quick Reference Guide\n")
        f.write("# Use this to identify samples when viewing the tree\n")
        f.write("#\n")
        f.write("# Format: Tree_Label | Subspecies | Host | Source | Prophages\n")
        f.write("#\n")
        f.write("="*100 + "\n\n")

        # Group by sample
        samples_seen = set()

        for label in sorted(labels):
            srr = extract_sample_from_label(label)
            if not srr or srr in samples_seen:
                continue

            samples_seen.add(srr)

            meta = metadata.get(srr, {})

            # Extract key info - try multiple column names
            organism = (meta.get('Organism', '') or
                       meta.get('organism', '') or
                       meta.get('sub_species', '') or
                       'Unknown')

            # Shorten subspecies name
            if 'Fusobacterium' in organism or 'fusobacterium' in organism.lower():
                # Extract just species name
                parts = organism.split()
                if len(parts) >= 2:
                    subspecies = f"F. {parts[1]}"
                else:
                    subspecies = organism
            else:
                subspecies = organism

            host = meta.get('host', '') or meta.get('Host', '') or 'Unknown'
            # Shorten host
            if 'Homo sapiens' in host:
                host = 'Human'
            elif 'Bos taurus' in host:
                host = 'Bovine'
            elif 'Sus scrofa' in host:
                host = 'Pig'

            source = (meta.get('isolation_source', '') or
                     meta.get('isolation source', '') or
                     meta.get('isolation-source', '') or
                     'Unknown').lower()
            # Categorize
            if any(kw in source for kw in ['oral', 'saliva', 'dental', 'plaque', 'mouth']):
                source_cat = 'Oral'
            elif any(kw in source for kw in ['stool', 'feces', 'gut', 'intestin']):
                source_cat = 'GI'
            elif 'blood' in source:
                source_cat = 'Blood'
            else:
                source_cat = 'Other'

            # Write entry
            f.write(f"{srr:<15} | {subspecies:<25} | {host:<15} | {source_cat:<10}\n")

        f.write("\n" + "="*100 + "\n\n")

        # Add summary
        f.write("SUMMARY\n")
        f.write("-" * 100 + "\n\n")

        # Count subspecies
        subsp_counts = {}
        for srr in samples_seen:
            meta = metadata.get(srr, {})
            org = meta.get('Organism', 'Unknown')
            if 'Fusobacterium' in org:
                parts = org.split()
                if len(parts) >= 2:
                    name = f"F. {parts[1]}"
                else:
                    name = org
            else:
                name = org
            subsp_counts[name] = subsp_counts.get(name, 0) + 1

        f.write("Subspecies Distribution:\n")
        for subsp, count in sorted(subsp_counts.items(), key=lambda x: -x[1]):
            f.write(f"  {subsp}: {count} samples\n")

        f.write("\n")
        f.write(f"Total samples in tree: {len(samples_seen)}\n")
        f.write(f"Total prophage sequences: {len(labels)}\n")
        f.write(f"Average prophages per sample: {len(labels) / len(samples_seen):.1f}\n")

    print(f"✓ Created: {output_file}")
    print()
    print("This file shows:")
    print("  - All samples in the tree")
    print("  - Subspecies for each sample")
    print("  - Host and isolation source")
    print("  - Easy lookup by SRR accession")
    print()
    print("Use while viewing tree in iTOL to identify samples!")
    print()

def main():
    tree_file = "fusobacterium_results/analysis/phylogenomics/prophage_tree.nwk"
    metadata_file = "fusobacterium_necrophorum_study/data/fusobacterium_metadata.tsv"
    output_file = "fusobacterium_necrophorum_study/data/tree_quick_reference.txt"

    if len(sys.argv) > 1:
        tree_file = sys.argv[1]
    if len(sys.argv) > 2:
        metadata_file = sys.argv[2]
    if len(sys.argv) > 3:
        output_file = sys.argv[3]

    create_quick_reference(tree_file, metadata_file, output_file)

if __name__ == "__main__":
    main()
