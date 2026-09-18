#!/usr/bin/env python3
"""
Create iTOL annotation files for Fusobacterium prophage tree

Generates color-coded annotations for:
- Subspecies (F. nucleatum, F. necrophorum, etc.)
- Host species (Human, Bovine, etc.)
- Isolation source (Oral, GI, Clinical, etc.)
"""

import csv
import sys
import re

def extract_srr_from_label(label):
    """Extract SRR accession from tree label like _R_SRR848065_NODE_6_..."""
    # Remove _R_ prefix if present
    if label.startswith('_R_'):
        label = label[3:]
    # Extract SRR accession
    match = re.match(r'(SRR\d+)', label)
    if match:
        return match.group(1)
    return None

def parse_tree_labels(tree_file):
    """Extract all tip labels from tree file"""
    with open(tree_file, 'r') as f:
        tree_string = f.read()

    # Extract all labels (pattern: label followed by colon and branch length)
    labels = re.findall(r'([A-Za-z0-9_\.]+):', tree_string)
    return labels

def create_itol_colorstrip(tree_file, metadata_file, output_prefix):
    """
    Create iTOL color strip annotation files

    iTOL format:
    DATASET_COLORSTRIP
    SEPARATOR TAB
    DATASET_LABEL<tab>label
    COLOR<tab>#color
    DATA
    sample<tab>color<tab>label
    """

    print("="*70)
    print("Creating iTOL Annotation Files")
    print("="*70)
    print()

    # Parse tree to get all tip labels
    print(f"Parsing tree: {tree_file}")
    tree_labels = parse_tree_labels(tree_file)
    print(f"Found {len(tree_labels)} tip labels in tree")
    print()

    # Load metadata
    print(f"Loading metadata from: {metadata_file}")
    metadata = {}
    with open(metadata_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            srr = (row.get('sample', '') or
                   row.get('Run', '') or
                   row.get('Genus', ''))
            if srr and srr.startswith('SRR'):
                metadata[srr] = row
    print(f"Loaded metadata for {len(metadata)} samples")
    print()

    # 1. SUBSPECIES ANNOTATION
    print("Creating subspecies annotation...")

    # Define subspecies color scheme
    subspecies_colors = {
        'Fusobacterium nucleatum': '#E41A1C',  # Red
        'Fusobacterium necrophorum': '#377EB8',  # Blue
        'Fusobacterium funduliforme': '#4DAF4A',  # Green
        'Fusobacterium animalis': '#984EA3',  # Purple
        'Fusobacterium periodonticum': '#FF7F00',  # Orange
        'Fusobacterium hwasookii': '#FFFF33',  # Yellow
        'Fusobacterium varium': '#A65628',  # Brown
        'Fusobacterium mortiferum': '#F781BF',  # Pink
        'Fusobacterium ulcerans': '#999999',  # Gray
        'Other': '#CCCCCC'  # Light gray
    }

    # Create annotations for each tree label
    subspecies_data = []
    for label in tree_labels:
        srr = extract_srr_from_label(label)
        if not srr or srr not in metadata:
            continue

        meta = metadata[srr]
        org = str(meta.get('organism', '') or meta.get('Organism', '') or meta.get('sub_species', ''))

        # Try to match known subspecies
        matched = False
        for species, color in subspecies_colors.items():
            if species.lower() in org.lower():
                subspecies_data.append((label, color, species))
                matched = True
                break

        if not matched:
            subspecies_data.append((label, subspecies_colors['Other'], 'Other'))

    if subspecies_data:
        # Write subspecies annotation file
        with open(f"{output_prefix}_subspecies.txt", 'w') as f:
            f.write("DATASET_COLORSTRIP\n")
            f.write("SEPARATOR TAB\n")
            f.write("DATASET_LABEL\tFusobacterium Subspecies\n")
            f.write("COLOR\t#000000\n")
            f.write("STRIP_WIDTH\t50\n")
            f.write("MARGIN\t10\n")
            f.write("SHOW_INTERNAL\t0\n")
            f.write("\n")
            f.write("LEGEND_TITLE\tSubspecies\n")
            f.write("LEGEND_SHAPES\t" + "\t".join(["1"] * len(subspecies_colors)) + "\n")
            f.write("LEGEND_COLORS\t" + "\t".join(subspecies_colors.values()) + "\n")
            f.write("LEGEND_LABELS\t" + "\t".join(subspecies_colors.keys()) + "\n")
            f.write("\n")
            f.write("DATA\n")
            for full_label, color, species_name in subspecies_data:
                f.write(f"{full_label}\t{color}\t{species_name}\n")

        print(f"✓ Created: {output_prefix}_subspecies.txt")
        print(f"  Unique subspecies: {len(set([x[2] for x in subspecies_data]))}")
        print(f"  Annotated {len(subspecies_data)} tree tips")
    else:
        print("WARNING: No subspecies data found")

    print()

    # 2. HOST ANNOTATION
    print("Creating host annotation...")

    host_colors = {
        'Homo sapiens': '#1B9E77',  # Teal
        'Bos taurus': '#D95F02',  # Orange
        'Sus scrofa': '#7570B3',  # Purple
        'Other': '#E7298A'  # Pink
    }

    host_data = []
    for label in tree_labels:
        srr = extract_srr_from_label(label)
        if not srr or srr not in metadata:
            continue

        meta = metadata[srr]
        host = str(meta.get('host', '') or meta.get('Host', ''))

        if host in host_colors:
            host_data.append((label, host_colors[host], host))
        else:
            host_data.append((label, host_colors['Other'], 'Other'))

    if host_data:
        # Write host annotation file
        with open(f"{output_prefix}_host.txt", 'w') as f:
            f.write("DATASET_COLORSTRIP\n")
            f.write("SEPARATOR TAB\n")
            f.write("DATASET_LABEL\tHost Species\n")
            f.write("COLOR\t#000000\n")
            f.write("STRIP_WIDTH\t50\n")
            f.write("MARGIN\t10\n")
            f.write("SHOW_INTERNAL\t0\n")
            f.write("\n")
            f.write("LEGEND_TITLE\tHost\n")
            f.write("LEGEND_SHAPES\t" + "\t".join(["1"] * len(host_colors)) + "\n")
            f.write("LEGEND_COLORS\t" + "\t".join(host_colors.values()) + "\n")
            f.write("LEGEND_LABELS\t" + "\t".join(host_colors.keys()) + "\n")
            f.write("\n")
            f.write("DATA\n")
            for full_label, color, host_name in host_data:
                f.write(f"{full_label}\t{color}\t{host_name}\n")

        print(f"✓ Created: {output_prefix}_host.txt")
        print(f"  Unique hosts: {len(set([x[2] for x in host_data]))}")
        print(f"  Annotated {len(host_data)} tree tips")

    print()

    # 3. ISOLATION SOURCE ANNOTATION
    print("Creating isolation source annotation...")

    source_colors = {
        'Oral': '#8DD3C7',  # Light teal
        'GI': '#FFFFB3',  # Light yellow
        'Blood': '#FB8072',  # Light red
        'Other': '#BEBADA'  # Light purple
    }

    source_data = []
    for label in tree_labels:
        srr = extract_srr_from_label(label)
        if not srr or srr not in metadata:
            continue

        meta = metadata[srr]
        source = str(meta.get('isolation_source', '') or
                    meta.get('isolation source', '') or
                    meta.get('isolation-source', '')).lower()

        # Classify source
        if any(kw in source for kw in ['oral', 'saliva', 'dental', 'plaque', 'mouth', 'tonsil']):
            category = 'Oral'
        elif any(kw in source for kw in ['stool', 'feces', 'colon', 'gut', 'intestin', 'ileum', 'caecum']):
            category = 'GI'
        elif any(kw in source for kw in ['blood', 'serum', 'plasma']):
            category = 'Blood'
        else:
            category = 'Other'

        source_data.append((label, source_colors[category], category))

    if source_data:
        # Write source annotation file
        with open(f"{output_prefix}_source.txt", 'w') as f:
            f.write("DATASET_COLORSTRIP\n")
            f.write("SEPARATOR TAB\n")
            f.write("DATASET_LABEL\tIsolation Source\n")
            f.write("COLOR\t#000000\n")
            f.write("STRIP_WIDTH\t50\n")
            f.write("MARGIN\t10\n")
            f.write("SHOW_INTERNAL\t0\n")
            f.write("\n")
            f.write("LEGEND_TITLE\tSource\n")
            f.write("LEGEND_SHAPES\t" + "\t".join(["1"] * len(source_colors)) + "\n")
            f.write("LEGEND_COLORS\t" + "\t".join(source_colors.values()) + "\n")
            f.write("LEGEND_LABELS\t" + "\t".join(source_colors.keys()) + "\n")
            f.write("\n")
            f.write("DATA\n")
            for full_label, color, source_name in source_data:
                f.write(f"{full_label}\t{color}\t{source_name}\n")

        print(f"✓ Created: {output_prefix}_source.txt")
        print(f"  Unique sources: {len(set([x[2] for x in source_data]))}")
        print(f"  Annotated {len(source_data)} tree tips")

    print()
    print("="*70)
    print("Complete!")
    print("="*70)
    print()
    print("Upload to iTOL:")
    print("  1. Go to https://itol.embl.de/")
    print("  2. Upload prophage_tree.nwk")
    print("  3. Drag and drop annotation files:")
    print(f"     - {output_prefix}_subspecies.txt")
    print(f"     - {output_prefix}_host.txt")
    print(f"     - {output_prefix}_source.txt")
    print()

def main():
    tree_file = "fusobacterium_results/analysis/phylogenomics/prophage_tree.nwk"
    metadata_file = "fusobacterium_necrophorum_study/data/fusobacterium_metadata_prophage_merged.tsv"
    output_prefix = "fusobacterium_necrophorum_study/data/itol"

    if len(sys.argv) > 1:
        tree_file = sys.argv[1]
    if len(sys.argv) > 2:
        metadata_file = sys.argv[2]
    if len(sys.argv) > 3:
        output_prefix = sys.argv[3]

    create_itol_colorstrip(tree_file, metadata_file, output_prefix)

if __name__ == "__main__":
    main()
