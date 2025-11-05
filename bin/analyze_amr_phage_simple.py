#!/usr/bin/env python3
import os
from pathlib import Path

def count_amr_genes(amr_file):
    """Count only AMR genes (not virulence/stress)"""
    if not Path(amr_file).exists():
        return 0
    count = 0
    with open(amr_file) as f:
        for line in f:
            if line.startswith('NA') and '\tAMR\t' in line:
                count += 1
    return count

def count_phages(phage_file):
    """Count phage sequences in FASTA"""
    if not Path(phage_file).exists():
        return 0
    if Path(phage_file).stat().st_size == 0:
        return 0
    count = 0
    with open(phage_file) as f:
        for line in f:
            if line.startswith('>'):
                count += 1
    return count

# Analyze 2024 data
amr_dir = Path("results_kansas_2024/amrfinder")
vibrant_dir = Path("results_kansas_2024/vibrant")

samples_both = []
samples_amr_only = []
samples_phage_only = []

for amr_file in amr_dir.glob("*_amr.tsv"):
    sample_id = amr_file.stem.replace('_amr', '')

    amr_count = count_amr_genes(amr_file)
    phage_count = count_phages(vibrant_dir / f"{sample_id}_phages.fna")

    if amr_count > 0 and phage_count > 0:
        samples_both.append((sample_id, amr_count, phage_count))
    elif amr_count > 0:
        samples_amr_only.append((sample_id, amr_count))
    elif phage_count > 0:
        samples_phage_only.append((sample_id, phage_count))

print("\n" + "="*60)
print("Kansas 2024 AMR-Phage Correlation Analysis")
print("="*60)
print(f"\nTotal samples: {len(list(amr_dir.glob('*_amr.tsv')))}")
print(f"Samples with AMR: {len(samples_both) + len(samples_amr_only)}")
print(f"Samples with phages: {len(samples_both) + len(samples_phage_only)}")
print(f"\n🔬 Samples with BOTH AMR and phages: {len(samples_both)}")
print(f"   AMR only: {len(samples_amr_only)}")
print(f"   Phages only: {len(samples_phage_only)}")

print(f"\n📋 Top 20 samples with both AMR and phages:")
print(f"{'Sample ID':<20} {'AMR genes':<12} {'Phages'}")
print("-" * 60)
for sample_id, amr, phage in sorted(samples_both, key=lambda x: x[1], reverse=True)[:20]:
    print(f"{sample_id:<20} {amr:<12} {phage}")
