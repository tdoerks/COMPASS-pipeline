#!/usr/bin/env python3
"""
Simple iTOL annotation generator for Fusobacterium host tree
Handles the SRRSRR prefix issue and creates color strips for:
- Organism/species
- Host
- Isolation source
"""
import csv
import re
from collections import defaultdict

def main():
    # Parse tree to get sample IDs
    print("Reading tree...")
    with open('host_tree.nwk', 'r') as f:
        tree = f.read()

    # Extract SRR IDs from tree (they appear as SRRSRR123456)
    tree_samples = re.findall(r'SRR(SRR\d+)', tree)
    print(f"Found {len(tree_samples)} samples in tree")

    # Load metadata
    print("Loading metadata...")
    metadata = {}
    with open('fusobacterium_metadata.tsv', 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            acc = row.get('accession', '')
            if acc.startswith('SRR'):
                metadata[acc] = row

    print(f"Loaded {len(metadata)} samples from metadata")

    # Match tree samples to metadata
    matched = 0
    for tree_id in tree_samples:
        if tree_id in metadata:
            matched += 1

    print(f"Matched {matched}/{len(tree_samples)} samples")

    # Create organism/species colorstrip
    print("\nCreating organism colorstrip...")
    organisms = defaultdict(list)
    for tree_id in tree_samples:
        if tree_id in metadata:
            org = metadata[tree_id].get('organism', 'Unknown')
            # Clean up organism name
            if org and 'Fusobacterium' in org:
                parts = org.split()
                if len(parts) >= 2:
                    org = f"{parts[0]} {parts[1]}"
            organisms[org].append(f"SRR{tree_id}")

    # Assign colors
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    org_colors = {}
    for i, org in enumerate(sorted(organisms.keys())):
        org_colors[org] = colors[i % len(colors)]

    # Write organism colorstrip
    with open('itol_organism.txt', 'w') as f:
        f.write("DATASET_COLORSTRIP\n")
        f.write("SEPARATOR TAB\n")
        f.write("DATASET_LABEL\tOrganism\n")
        f.write("COLOR\t#ff0000\n")
        f.write("LEGEND_TITLE\tOrganism\n")

        shapes = '\t'.join(['1'] * len(org_colors))
        f.write(f"LEGEND_SHAPES\t{shapes}\n")

        legend_colors = '\t'.join([org_colors[o] for o in sorted(org_colors.keys())])
        f.write(f"LEGEND_COLORS\t{legend_colors}\n")

        legend_labels = '\t'.join([o.replace(' ', '_') for o in sorted(org_colors.keys())])
        f.write(f"LEGEND_LABELS\t{legend_labels}\n")

        f.write("DATA\n")
        for org, samples in organisms.items():
            color = org_colors[org]
            label = org.replace(' ', '_')
            for sample in samples:
                f.write(f"{sample}\t{color}\t{label}\n")

    print(f"  ✓ itol_organism.txt ({len(organisms)} species)")

    # Create host colorstrip
    print("Creating host colorstrip...")
    hosts = defaultdict(list)
    for tree_id in tree_samples:
        if tree_id in metadata:
            host = metadata[tree_id].get('host', 'Unknown')
            if not host or host == 'missing':
                host = 'Unknown'
            hosts[host].append(f"SRR{tree_id}")

    host_colors = {}
    for i, host in enumerate(sorted(hosts.keys())):
        host_colors[host] = colors[i % len(colors)]

    with open('itol_host.txt', 'w') as f:
        f.write("DATASET_COLORSTRIP\n")
        f.write("SEPARATOR TAB\n")
        f.write("DATASET_LABEL\tHost\n")
        f.write("COLOR\t#ff0000\n")
        f.write("LEGEND_TITLE\tHost\n")

        shapes = '\t'.join(['1'] * len(host_colors))
        f.write(f"LEGEND_SHAPES\t{shapes}\n")

        legend_colors = '\t'.join([host_colors[h] for h in sorted(host_colors.keys())])
        f.write(f"LEGEND_COLORS\t{legend_colors}\n")

        legend_labels = '\t'.join([h.replace(' ', '_') for h in sorted(host_colors.keys())])
        f.write(f"LEGEND_LABELS\t{legend_labels}\n")

        f.write("DATA\n")
        for host, samples in hosts.items():
            color = host_colors[host]
            label = host.replace(' ', '_')
            for sample in samples:
                f.write(f"{sample}\t{color}\t{label}\n")

    print(f"  ✓ itol_host.txt ({len(hosts)} hosts)")

    # Create isolation source colorstrip
    print("Creating isolation source colorstrip...")
    sources = defaultdict(list)
    for tree_id in tree_samples:
        if tree_id in metadata:
            source = metadata[tree_id].get('isolation_source',
                                          metadata[tree_id].get('isolation-source', 'Unknown'))
            if not source or source == 'missing':
                source = 'Unknown'
            # Truncate very long sources
            if len(source) > 50:
                source = source[:47] + '...'
            sources[source].append(f"SRR{tree_id}")

    source_colors = {}
    for i, source in enumerate(sorted(sources.keys())):
        source_colors[source] = colors[i % len(colors)]

    with open('itol_isolation_source.txt', 'w') as f:
        f.write("DATASET_COLORSTRIP\n")
        f.write("SEPARATOR TAB\n")
        f.write("DATASET_LABEL\tIsolation_Source\n")
        f.write("COLOR\t#ff0000\n")
        f.write("LEGEND_TITLE\tIsolation Source\n")

        # Limit legend to top 15 sources
        top_sources = sorted(sources.keys(), key=lambda x: len(sources[x]), reverse=True)[:15]

        shapes = '\t'.join(['1'] * len(top_sources))
        f.write(f"LEGEND_SHAPES\t{shapes}\n")

        legend_colors = '\t'.join([source_colors[s] for s in top_sources])
        f.write(f"LEGEND_COLORS\t{legend_colors}\n")

        legend_labels = '\t'.join([s.replace(' ', '_')[:30] for s in top_sources])
        f.write(f"LEGEND_LABELS\t{legend_labels}\n")

        f.write("DATA\n")
        for source, samples in sources.items():
            color = source_colors[source]
            label = source.replace(' ', '_')[:30]
            for sample in samples:
                f.write(f"{sample}\t{color}\t{label}\n")

    print(f"  ✓ itol_isolation_source.txt ({len(sources)} sources)")

    print("\n" + "="*60)
    print("SUCCESS! iTOL annotation files created")
    print("="*60)
    print("\nFiles created:")
    print("  - itol_organism.txt")
    print("  - itol_host.txt")
    print("  - itol_isolation_source.txt")
    print("\nUpload to iTOL:")
    print("  1. Go to https://itol.embl.de")
    print("  2. Upload host_tree.nwk")
    print("  3. Drag and drop the itol_*.txt files")

if __name__ == "__main__":
    main()
