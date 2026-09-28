#!/usr/bin/env python3
"""
Extract prophage sequences from VIBRANT results for phylogenetic analysis

Strategy:
1. Extract integrated prophage regions from VIBRANT
2. Combine into multi-FASTA for alignment
3. Prepare for tree building (MAFFT + FastTree)
"""

import os
import glob
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

def extract_prophage_sequences():
    """Extract all prophage sequences from VIBRANT results"""

    results_dir = '/fastscratch/tylerdoe/fusobacterium_results'
    vibrant_dir = f'{results_dir}/vibrant'

    print("="*70)
    print("Extracting Prophage Sequences for Phylogenetic Analysis")
    print("="*70)
    print()

    # Find all prophage FASTA files
    prophage_files = glob.glob(f'{vibrant_dir}/SRR*_vibrant/*_contigs.phages_combined.fna')

    print(f"Found {len(prophage_files)} samples with prophage sequences")
    print()

    all_prophages = []
    prophage_count = 0

    for fasta_file in prophage_files:
        # Get sample name
        sample = os.path.basename(os.path.dirname(fasta_file)).replace('_vibrant', '')

        # Read prophage sequences
        if os.path.getsize(fasta_file) > 0:
            for record in SeqIO.parse(fasta_file, 'fasta'):
                # Rename with sample prefix
                new_id = f"{sample}_{record.id}"
                new_record = SeqRecord(
                    record.seq,
                    id=new_id,
                    description=f"prophage from {sample}"
                )
                all_prophages.append(new_record)
                prophage_count += 1

    print(f"Total prophage sequences extracted: {prophage_count}")
    print()

    # Save combined prophage sequences
    output_file = f'{results_dir}/analysis/all_prophage_sequences.fna'
    SeqIO.write(all_prophages, output_file, 'fasta')

    print(f"✓ Saved all prophage sequences to {output_file}")
    print()

    # Stats
    lengths = [len(rec.seq) for rec in all_prophages]
    if lengths:
        print("Prophage size statistics:")
        print(f"  Total sequences: {len(lengths)}")
        print(f"  Min size: {min(lengths):,} bp")
        print(f"  Max size: {max(lengths):,} bp")
        print(f"  Mean size: {sum(lengths)//len(lengths):,} bp")

    return len(all_prophages)

def extract_terminase_genes():
    """Extract conserved terminase genes for more focused tree"""

    results_dir = '/fastscratch/tylerdoe/fusobacterium_results'
    phanotate_dir = f'{results_dir}/phanotate'

    print()
    print("="*70)
    print("Extracting Terminase Genes (Most Conserved Prophage Marker)")
    print("="*70)
    print()

    # This would require parsing PHANOTATE annotations
    # For now, we'll use full prophages
    print("Note: Using full prophage sequences for this analysis")
    print("Future: Can extract specific genes (terminase, integrase) from PHANOTATE")
    print()

def main():
    print("Fusobacterium Prophage Phylogenetic Analysis")
    print()

    # Extract sequences
    n_sequences = extract_prophage_sequences()

    # Future: extract specific genes
    extract_terminase_genes()

    print()
    print("="*70)
    print("Next Steps for Tree Building")
    print("="*70)
    print()
    print("1. Align prophage sequences:")
    print("   mafft --auto --thread 8 all_prophage_sequences.fna > prophages_aligned.fna")
    print()
    print("2. Build tree:")
    print("   FastTree -nt -gtr prophages_aligned.fna > prophage_tree.nwk")
    print()
    print("3. Visualize tree:")
    print("   - Upload prophage_tree.nwk to iTOL (https://itol.embl.de/)")
    print("   - Or use FigTree, ggtree in R")
    print()
    print("4. Compare to host tree:")
    print("   - Extract 16S or core genes from assemblies")
    print("   - Build host tree")
    print("   - Compare topologies")
    print()
    print("Analysis Questions:")
    print("  - Do prophages cluster by Fusobacterium subspecies?")
    print("  - Or do they cluster by prophage type (horizontal transfer)?")
    print("  - F. necrophorum prophages unique or shared?")
    print("="*70)

if __name__ == "__main__":
    main()
