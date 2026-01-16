#!/usr/bin/env python3
"""
Prepare Prophages for Phylogenetic Analysis

Based on completeness assessment, extracts high-quality prophages
suitable for phylogenetic tree construction.

Steps:
1. Load completeness assessment results
2. Filter to complete prophages (>15kb, quality: High)
3. Extract prophage sequences
4. Create multi-FASTA for alignment
5. Generate metadata file for tree annotation

Outputs:
- complete_prophages.fasta (for alignment/tree)
- prophage_metadata.tsv (sample, year, organism, length)
- phylogeny_guide.txt (instructions for tree building)
"""

import os
import csv
from pathlib import Path
from Bio import SeqIO
from collections import defaultdict


def load_completeness_data(completeness_csv):
    """Load prophage completeness assessment results"""
    print(f"Loading completeness data from {completeness_csv}...")

    complete_prophages = []

    with open(completeness_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter to high-quality, complete prophages
            if row['quality'] == 'High' and int(row['length']) >= 15000:
                complete_prophages.append({
                    'sample_id': row['sample_id'],
                    'prophage_id': row['prophage_id'],
                    'length': int(row['length']),
                    'completeness': row['completeness'],
                    'quality': row['quality']
                })

    print(f"  Found {len(complete_prophages)} complete prophages (>15kb, High quality)")

    return complete_prophages


def load_metadata(base_dir):
    """Load sample metadata"""
    print("Loading sample metadata...")

    metadata = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        metadata_file = base_path / f"results_kansas_{year}" / "filtered_samples" / "filtered_samples.csv"

        if not metadata_file.exists():
            continue

        with open(metadata_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                srr_id = row['Run']
                metadata[srr_id] = {
                    'year': year,
                    'organism': row.get('organism', 'Unknown'),
                    'sample_name': row.get('SampleName', '')
                }

    print(f"  Loaded {len(metadata)} samples")
    return metadata


def extract_prophage_sequences(complete_prophages, base_dir, output_fasta):
    """Extract complete prophage sequences from VIBRANT output"""
    print(f"\nExtracting prophage sequences...")

    extracted = 0
    sequences = []

    base_path = Path(base_dir)

    # Group by sample
    prophages_by_sample = defaultdict(list)
    for prophage in complete_prophages:
        prophages_by_sample[prophage['sample_id']].append(prophage)

    # Extract sequences from VIBRANT output
    for year_dir in base_path.glob('results_kansas_*'):
        vibrant_dir = year_dir / 'vibrant'
        if not vibrant_dir.exists():
            continue

        for sample_dir in vibrant_dir.iterdir():
            if not sample_dir.is_dir():
                continue

            sample_id = sample_dir.name

            if sample_id not in prophages_by_sample:
                continue

            # Find phages_combined.fna
            phage_files = list(sample_dir.rglob("*.phages_combined.fna"))

            for phage_file in phage_files:
                for record in SeqIO.parse(phage_file, "fasta"):
                    # Check if this prophage is in our complete list
                    for prophage in prophages_by_sample[sample_id]:
                        if prophage['prophage_id'] in record.id or record.id in prophage['prophage_id']:
                            # Rename for clarity
                            record.id = f"{sample_id}_{record.id}"
                            record.description = f"sample={sample_id} length={prophage['length']} completeness={prophage['completeness']}"
                            sequences.append(record)
                            extracted += 1
                            break

    # Write to FASTA
    SeqIO.write(sequences, output_fasta, "fasta")

    print(f"  ✅ Extracted {extracted} prophage sequences")
    print(f"  ✅ Saved to: {output_fasta}")

    return sequences


def generate_metadata_file(sequences, complete_prophages, sample_metadata, output_tsv):
    """Generate metadata file for phylogenetic tree annotation"""
    print(f"\nGenerating metadata file: {output_tsv}")

    with open(output_tsv, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['prophage_id', 'sample_id', 'year', 'organism', 'length_bp', 'completeness'])

        for seq in sequences:
            # Extract sample ID from sequence ID
            # Format: SRR30276930_vibrant_NODE_48_length_28980...
            # Need to get "SRR30276930_vibrant" part
            parts = seq.id.split('_')
            if len(parts) >= 2:
                sample_id = f"{parts[0]}_{parts[1]}"  # SRR30276930_vibrant
            else:
                sample_id = parts[0]

            # Find corresponding prophage data
            prophage_data = None
            for p in complete_prophages:
                if p['sample_id'] == sample_id and (p['prophage_id'] in seq.id or seq.id.endswith(p['prophage_id'])):
                    prophage_data = p
                    break

            if not prophage_data:
                continue

            # Get metadata - need to strip "_vibrant" suffix for lookup
            srr_id = sample_id.replace('_vibrant', '')
            year = sample_metadata.get(srr_id, {}).get('year', 'Unknown')
            organism = sample_metadata.get(srr_id, {}).get('organism', 'Unknown')

            writer.writerow([
                seq.id,
                sample_id,
                year,
                organism,
                prophage_data['length'],
                prophage_data['completeness']
            ])

    print(f"  ✅ Saved: {output_tsv}")


def generate_phylogeny_guide(output_file, num_sequences):
    """Generate step-by-step guide for building phylogenetic tree"""
    print(f"\nGenerating phylogeny guide: {output_file}")

    guide = f"""
# Prophage Phylogenetic Analysis Guide

## Summary
- **{num_sequences} complete prophage sequences** extracted for phylogenetic analysis
- All prophages are >15kb and high quality
- Ready for alignment and tree construction

## Step 1: Multiple Sequence Alignment

### Option A: MAFFT (Fast, good for large datasets)
```bash
mafft --auto complete_prophages.fasta > prophages_aligned.fasta
```

### Option B: MUSCLE (More accurate)
```bash
muscle -in complete_prophages.fasta -out prophages_aligned.fasta
```

### Option C: Clustal Omega (For reference)
```bash
clustalo -i complete_prophages.fasta -o prophages_aligned.fasta --outfmt=fasta
```

## Step 2: Phylogenetic Tree Construction

### Option A: IQ-TREE (Recommended - fast + accurate)
```bash
iqtree2 -s prophages_aligned.fasta -m MFP -bb 1000 -nt AUTO
# -m MFP: ModelFinder Plus (auto-select best model)
# -bb 1000: 1000 bootstrap replicates
# -nt AUTO: auto-detect number of threads
```

### Option B: RAxML-NG (Very accurate)
```bash
raxml-ng --all --msa prophages_aligned.fasta --model GTR+G --bs-trees 100 --threads auto
```

### Option C: FastTree (Very fast, good for exploration)
```bash
FastTree -nt -gtr prophages_aligned.fasta > prophage_tree.nwk
```

## Step 3: Tree Visualization

### Option A: iTOL (Online, interactive)
1. Go to https://itol.embl.de/
2. Upload `prophage_tree.nwk`
3. Upload `prophage_metadata.tsv` as annotation dataset
4. Color by year or organism

### Option B: FigTree (Desktop app)
```bash
figtree prophage_tree.nwk
```

### Option C: R (ggtree)
```R
library(ggtree)
library(ggplot2)

tree <- read.tree("prophage_tree.nwk")
metadata <- read.table("prophage_metadata.tsv", header=TRUE, sep="\\t")

p <- ggtree(tree) %<+% metadata +
  geom_tippoint(aes(color=as.factor(year)), size=3) +
  theme_tree2() +
  labs(color="Year")

ggsave("prophage_tree.png", p, width=12, height=10, dpi=300)
```

## Expected Results

- **Temporal clustering?** Do prophages from same years cluster together?
- **Species specificity?** Do prophages cluster by host organism?
- **Movement patterns?** Do identical prophages appear across years/samples?

## Notes

- These are prophage **genes/regions**, not complete circular genomes
- Use caution when interpreting phylogeny of partial sequences
- Consider running viralFlye (v1.3-dev) for complete viral genome assembly
- Bootstrap support values <70% indicate weak support

## Troubleshooting

**Too many sequences?**
- Filter to top N most complete prophages
- Use FastTree for initial exploration
- Subsample by year/organism

**Alignment fails?**
- Check sequence quality
- Remove very short (<15kb) or very long (>100kb) outliers
- Try different aligner

**Tree looks weird?**
- Check for misalignments
- Try different substitution models
- Consider using protein sequences instead of nucleotides

## Publication-Quality Tree

For final publication tree:
1. Use IQ-TREE or RAxML-NG
2. 1000+ bootstrap replicates
3. Export as SVG from iTOL
4. Annotate with year, organism, AMR co-location
5. Show bootstrap support values

"""

    with open(output_file, 'w') as f:
        f.write(guide)

    print(f"  ✅ Saved: {output_file}")


def main():
    base_dir = os.path.expanduser('~/compass_kansas_results')
    completeness_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/prophage_completeness.csv')
    output_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/phylogeny')

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_fasta = f"{output_dir}/complete_prophages.fasta"
    output_metadata = f"{output_dir}/prophage_metadata.tsv"
    output_guide = f"{output_dir}/PHYLOGENY_GUIDE.txt"

    print("=" * 70)
    print("Prophage Phylogeny Preparation")
    print("=" * 70)

    # Check if completeness assessment has been run
    if not Path(completeness_csv).exists():
        print("\n⚠️  ERROR: Completeness assessment not found!")
        print(f"   Please run: python3 bin/assess_prophage_completeness.py")
        print(f"   Expected file: {completeness_csv}")
        return

    # Load data
    complete_prophages = load_completeness_data(completeness_csv)
    sample_metadata = load_metadata(base_dir)

    if not complete_prophages:
        print("\n⚠️  No complete prophages found!")
        print("   Check completeness assessment results")
        return

    # Extract sequences
    sequences = extract_prophage_sequences(complete_prophages, base_dir, output_fasta)

    if not sequences:
        print("\n⚠️  No sequences extracted!")
        print("   Check VIBRANT output directories")
        return

    # Generate metadata
    generate_metadata_file(sequences, complete_prophages, sample_metadata, output_metadata)

    # Generate guide
    generate_phylogeny_guide(output_guide, len(sequences))

    print("\n" + "=" * 70)
    print("✅ Phylogeny preparation complete!")
    print("=" * 70)
    print(f"\n📁 Output files:")
    print(f"   {output_fasta}")
    print(f"   {output_metadata}")
    print(f"   {output_guide}")
    print(f"\n📖 Next steps:")
    print(f"   1. Read the phylogeny guide: cat {output_guide}")
    print(f"   2. Align sequences with MAFFT/MUSCLE")
    print(f"   3. Build tree with IQ-TREE or RAxML")
    print(f"   4. Visualize with iTOL or FigTree")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
