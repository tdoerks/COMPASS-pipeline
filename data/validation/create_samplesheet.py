#!/usr/bin/env python3
"""
Generate COMPASS samplesheet from validation genomes
Usage: python create_samplesheet.py
"""

import os
import glob
from pathlib import Path

# Configuration
ASSEMBLIES_DIR = "data/validation/assemblies"
OUTPUT_CSV = "data/validation/validation_samplesheet.csv"
ORGANISM = "Escherichia"  # For AMRFinder

def main():
    # Find all FASTA files
    fasta_files = sorted(glob.glob(f"{ASSEMBLIES_DIR}/*.fasta"))

    if not fasta_files:
        print(f"ERROR: No FASTA files found in {ASSEMBLIES_DIR}")
        print("Run download_genomes.sh first!")
        return

    # Generate samplesheet
    with open(OUTPUT_CSV, 'w') as f:
        # Header
        f.write("sample,organism,fasta\n")

        # Add each genome
        for fasta_path in fasta_files:
            # Get sample name from filename (remove .fasta extension)
            sample_name = Path(fasta_path).stem

            # Get absolute path
            abs_path = os.path.abspath(fasta_path)

            # Write row
            f.write(f"{sample_name},{ORGANISM},{abs_path}\n")

    # Summary
    print(f"Samplesheet created: {OUTPUT_CSV}")
    print(f"Total samples: {len(fasta_files)}")
    print("")
    print("Sample breakdown:")

    # Count by tier
    tiers = {
        "Tier 1 (EC958, JJ1886, ETEC)": 0,
        "Tier 2 (K12, ATCC, CFT073)": 0,
        "Tier 3 (FDA-ARGOS)": 0,
        "Tier 4 (DIVERSE)": 0,
        "Tier 5 (ENTEROBASE)": 0
    }

    for fasta_path in fasta_files:
        sample = Path(fasta_path).stem
        if any(x in sample for x in ["EC958", "JJ1886", "ETEC", "VREC"]):
            tiers["Tier 1 (EC958, JJ1886, ETEC)"] += 1
        elif any(x in sample for x in ["K12", "ATCC", "CFT073"]):
            tiers["Tier 2 (K12, ATCC, CFT073)"] += 1
        elif "FDA_ARGOS" in sample:
            tiers["Tier 3 (FDA-ARGOS)"] += 1
        elif "DIVERSE" in sample:
            tiers["Tier 4 (DIVERSE)"] += 1
        elif "ENTEROBASE" in sample:
            tiers["Tier 5 (ENTEROBASE)"] += 1

    for tier, count in tiers.items():
        if count > 0:
            print(f"  {tier}: {count}")

    print("")
    print("Next step: sbatch data/validation/run_compass_validation.sh")

if __name__ == "__main__":
    main()
