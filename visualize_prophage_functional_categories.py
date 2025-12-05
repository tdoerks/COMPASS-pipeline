#!/usr/bin/env python3
"""
Prophage Functional Categories Visualization

Creates a pie chart showing the distribution of prophage protein functional categories:
- DNA Packaging (terminase, portal, scaffolding)
- Structural (capsid, tail, head, baseplate)
- Lysis (holin, lysin, endolysin)
- Regulation (repressor, regulator, antitermination)
- DNA Modification (integrase, recombinase, helicase, polymerase)
- Tail Fiber (tail fiber, receptor binding)
- Hypothetical/Unknown
- Other (characterized but uncategorized)

Parses VIBRANT annotation files to extract protein functional descriptions.
"""

import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter

def parse_vibrant_annotations(base_dir):
    """
    Parse VIBRANT annotation files to extract prophage functional categories.

    VIBRANT creates annotation files in:
    vibrant/{sample}_vibrant/VIBRANT_{sample}_contigs/VIBRANT_annotations_{sample}_contigs.tsv

    Returns: Counter of functional categories
    """
    print("\n🧬 Parsing VIBRANT annotation files...")

    vibrant_dir = base_dir / "vibrant"
    if not vibrant_dir.exists():
        print(f"❌ Error: VIBRANT directory not found: {vibrant_dir}")
        sys.exit(1)

    # Define functional category keywords
    function_keywords = {
        'DNA Packaging': [
            'terminase', 'portal', 'scaffolding', 'DNA-packaging',
            'packaging protein', 'head-tail connector', 'DNA packaging',
            'prohead protease', 'protease and scaffold'
        ],
        'Structural': [
            'capsid', 'coat protein', 'tail', 'baseplate', 'head protein',
            'neck', 'collar', 'major capsid', 'minor capsid', 'tail protein',
            'tail tube', 'tail sheath', 'virion', 'head-tail', 'phage head',
            'tail length', 'tail assembly', 'morphogenesis'
        ],
        'Lysis': [
            'holin', 'lysin', 'endolysin', 'spanin', 'lysis protein',
            'murein hydrolase', 'cell lysis', 'lysis cassette', 'peptidase'
        ],
        'Regulation': [
            'antitermination', 'repressor', 'regulator', 'cro protein',
            'cI protein', 'transcriptional', 'anti-repressor', 'activator',
            'DNA-binding', 'helix-turn-helix'
        ],
        'DNA Modification': [
            'recombinase', 'integrase', 'helicase', 'primase', 'polymerase',
            'ligase', 'exonuclease', 'endonuclease', 'DNA replication',
            'topoisomerase', 'nuclease', 'DNA repair', 'DNA metabolism'
        ],
        'Tail Fiber': [
            'tail fiber', 'tail spike', 'tail tip', 'receptor binding',
            'host specificity', 'adhesin', 'host recognition'
        ],
    }

    functional_data = Counter()
    hypothetical_count = 0
    total_proteins = 0
    samples_processed = 0
    files_found = 0

    # Collect sample annotations for debugging
    debug_annotations = []

    print(f"  Searching for VIBRANT directories in: {vibrant_dir}")

    # Process each VIBRANT directory
    for sample_dir in sorted(vibrant_dir.glob("*_vibrant")):
        sample_id = sample_dir.name.replace('_vibrant', '')

        # Look for annotation file in expected location
        # Pattern: vibrant/{sample}_vibrant/VIBRANT_{sample}_contigs/VIBRANT_annotations_{sample}_contigs.tsv
        annotation_pattern = f"VIBRANT_annotations_{sample_id}_contigs.tsv"
        annot_files = list(sample_dir.rglob(annotation_pattern))

        if not annot_files:
            # Try alternate patterns
            annot_files = list(sample_dir.rglob("VIBRANT_annotations_*.tsv"))

        if not annot_files:
            continue

        files_found += 1
        samples_processed += 1

        try:
            df_annot = pd.read_csv(annot_files[0], sep='\t')

            # Debug: Show columns and sample data from first file
            if samples_processed == 1:
                print(f"\n  📋 Found annotation file: {annot_files[0].name}")
                print(f"  📋 Columns: {list(df_annot.columns)}")
                print(f"  📋 Shape: {df_annot.shape}")

            # Try to find the protein annotation column
            # VIBRANT uses different column names depending on version
            protein_col = None
            for col in ['protein', 'annotation', 'product', 'description',
                       'AMG KO name', 'KEGG', 'Pfam', 'VOG', 'annotation']:
                if col in df_annot.columns:
                    protein_col = col
                    if samples_processed == 1:
                        print(f"  ✅ Using column: '{protein_col}'")
                    break

            if not protein_col:
                # Try to use the last column or any column with text
                for col in df_annot.columns:
                    if df_annot[col].dtype == 'object':
                        protein_col = col
                        if samples_processed == 1:
                            print(f"  ⚠️  No standard column found, trying: '{protein_col}'")
                        break

            if not protein_col:
                if samples_processed == 1:
                    print(f"  ❌ Could not find suitable annotation column")
                continue

            # Show sample annotations
            if samples_processed == 1:
                print(f"\n  📝 Sample annotations (first 10):")
                for idx, ann in enumerate(df_annot[protein_col].dropna().head(10), 1):
                    print(f"      {idx}. {ann}")
                print()

            # Categorize each annotation
            for annotation in df_annot[protein_col].dropna():
                total_proteins += 1
                annotation_lower = str(annotation).lower()

                # Collect debug samples
                if len(debug_annotations) < 20:
                    debug_annotations.append(annotation)

                # Skip hypothetical/unknown proteins
                hypothetical_keywords = [
                    'hypothetical', 'duf', 'unknown function',
                    'uncharacterized', 'putative', 'predicted protein',
                    'unnamed protein', 'protein of unknown function'
                ]

                if any(kw in annotation_lower for kw in hypothetical_keywords):
                    hypothetical_count += 1
                    continue

                # Categorize by keyword matching
                categorized = False
                for category, keywords in function_keywords.items():
                    if any(keyword.lower() in annotation_lower for keyword in keywords):
                        functional_data[category] += 1
                        categorized = True
                        break

                # If not categorized and not hypothetical, mark as "Other"
                if not categorized:
                    functional_data['Other'] += 1

        except Exception as e:
            print(f"    ⚠️  Warning: Could not parse {annot_files[0].name}: {e}")
            continue

        if samples_processed % 100 == 0:
            print(f"    Processed {samples_processed} samples...")

    print(f"\n  📁 VIBRANT directories found: {len(list(vibrant_dir.glob('*_vibrant')))}")
    print(f"  📄 Annotation files found: {files_found}")
    print(f"  ✅ Successfully processed: {samples_processed} samples")
    print(f"  🧬 Total proteins analyzed: {total_proteins:,}")

    if functional_data:
        print(f"\n  📊 Functional Categories:")
        for category, count in functional_data.most_common():
            pct = count / total_proteins * 100 if total_proteins > 0 else 0
            print(f"    • {category}: {count:,} ({pct:.1f}%)")
        hyp_pct = hypothetical_count / total_proteins * 100 if total_proteins > 0 else 0
        print(f"    • Hypothetical/Unknown: {hypothetical_count:,} ({hyp_pct:.1f}%)")

        return {
            'counts': dict(functional_data),
            'hypothetical_count': hypothetical_count,
            'total_proteins': total_proteins,
            'samples_processed': samples_processed
        }
    else:
        print("\n  ❌ No functional annotations found!")
        print(f"     Total proteins seen: {total_proteins}")
        print(f"     Hypothetical: {hypothetical_count}")

        if debug_annotations:
            print(f"\n  🔍 Sample of annotations found:")
            for idx, ann in enumerate(debug_annotations[:10], 1):
                print(f"      {idx}. {ann}")

        return None

def create_functional_categories_pie_chart(stats, output_dir):
    """Create a focused pie chart of prophage functional categories."""
    print("\n📊 Creating functional categories pie chart...")

    if not stats or not stats['counts']:
        print("  ❌ No functional data to visualize")
        return None

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')

    # Prepare data
    categories = list(stats['counts'].keys())
    counts = [stats['counts'][c] for c in categories]

    # Add hypothetical to the data
    categories.append('Hypothetical/Unknown')
    counts.append(stats['hypothetical_count'])

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))

    # Color palette
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
             '#9966FF', '#FF9F40', '#C9CBCF', '#E0E0E0']

    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        counts,
        labels=categories,
        autopct='%1.1f%%',
        colors=colors[:len(categories)],
        startangle=90,
        textprops={'fontsize': 11, 'weight': 'bold'}
    )

    # Make percentage text more visible
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    ax.set_title(
        f'Prophage Functional Categories\nKansas 2021-2025 NARMS Dataset\n'
        f'({stats["total_proteins"]:,} proteins from {stats["samples_processed"]} samples)',
        fontsize=14,
        fontweight='bold',
        pad=20
    )

    # Save figure
    output_file = output_dir / "prophage_functional_categories.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Pie chart saved to: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 visualize_prophage_functional_categories.py <base_directory>")
        print("  base_directory should contain vibrant/ subdirectory")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        sys.exit(1)

    print("=" * 80)
    print("🦠 PROPHAGE FUNCTIONAL CATEGORIES VISUALIZATION")
    print("=" * 80)
    print(f"Data directory: {base_dir}")
    print()

    # Parse VIBRANT annotations
    stats = parse_vibrant_annotations(base_dir)

    if not stats:
        print("\n❌ Could not extract functional categories from VIBRANT annotations")
        print("   Check that VIBRANT has been run and annotation files exist")
        sys.exit(1)

    # Create visualization
    output_file = create_functional_categories_pie_chart(stats, base_dir)

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated file:")
    print(f"  📊 {output_file}")
    print()

if __name__ == "__main__":
    main()
