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

def create_itol_colorstrip(metadata_file, output_prefix):
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

    # Load metadata
    print(f"Loading metadata from: {metadata_file}")
    samples = []
    with open(metadata_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            samples.append(row)
    print(f"Loaded {len(samples)} samples")
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

    # Extract subspecies from organism field
    if samples and 'Organism' in samples[0]:
        subspecies_data = []
        for row in samples:
            sample = row.get('Run', row.get('sample', ''))
            org = str(row.get('Organism', ''))

            # Try to match known subspecies
            matched = False
            for species, color in subspecies_colors.items():
                if species.lower() in org.lower():
                    subspecies_data.append((sample, color, species))
                    matched = True
                    break

            if not matched:
                subspecies_data.append((sample, subspecies_colors['Other'], 'Other'))

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
            for sample, color, label in subspecies_data:
                f.write(f"{sample}\t{color}\t{label}\n")

        print(f"✓ Created: {output_prefix}_subspecies.txt")
        print(f"  Unique subspecies: {len(set([x[2] for x in subspecies_data]))}")

    print()

    # 2. HOST ANNOTATION
    print("Creating host annotation...")

    host_colors = {
        'Homo sapiens': '#1B9E77',  # Teal
        'Bos taurus': '#D95F02',  # Orange
        'Sus scrofa': '#7570B3',  # Purple
        'Other': '#E7298A'  # Pink
    }

    if samples and 'host' in samples[0]:
        host_data = []
        for row in samples:
            sample = row.get('Run', row.get('sample', ''))
            host = str(row.get('host', ''))

            if host in host_colors:
                host_data.append((sample, host_colors[host], host))
            else:
                host_data.append((sample, host_colors['Other'], 'Other'))

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
            for sample, color, label in host_data:
                f.write(f"{sample}\t{color}\t{label}\n")

        print(f"✓ Created: {output_prefix}_host.txt")
        print(f"  Unique hosts: {len(set([x[2] for x in host_data]))}")

    print()

    # 3. ISOLATION SOURCE ANNOTATION
    print("Creating isolation source annotation...")

    source_colors = {
        'Oral': '#8DD3C7',  # Light teal
        'GI': '#FFFFB3',  # Light yellow
        'Blood': '#FB8072',  # Light red
        'Other': '#BEBADA'  # Light purple
    }

    if samples and 'isolation_source' in samples[0]:
        source_data = []
        for row in samples:
            sample = row.get('Run', row.get('sample', ''))
            source = str(row.get('isolation_source', '')).lower()

            # Classify source
            if any(kw in source for kw in ['oral', 'saliva', 'dental', 'plaque', 'mouth', 'tonsil']):
                category = 'Oral'
            elif any(kw in source for kw in ['stool', 'feces', 'colon', 'gut', 'intestin', 'ileum', 'caecum']):
                category = 'GI'
            elif any(kw in source for kw in ['blood', 'serum', 'plasma']):
                category = 'Blood'
            else:
                category = 'Other'

            source_data.append((sample, source_colors[category], category))

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
            for sample, color, label in source_data:
                f.write(f"{sample}\t{color}\t{label}\n")

        print(f"✓ Created: {output_prefix}_source.txt")
        print(f"  Unique sources: {len(set([x[2] for x in source_data]))}")

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
    metadata_file = "fusobacterium_necrophorum_study/data/fusobacterium_metadata.tsv"
    output_prefix = "fusobacterium_necrophorum_study/data/itol"

    if len(sys.argv) > 1:
        metadata_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_prefix = sys.argv[2]

    create_itol_colorstrip(metadata_file, output_prefix)

if __name__ == "__main__":
    main()
