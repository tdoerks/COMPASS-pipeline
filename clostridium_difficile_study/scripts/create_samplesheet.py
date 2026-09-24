#!/usr/bin/env python3
"""
Create COMPASS pipeline samplesheet for Clostridium difficile study

Input: SRA accessions (one per line)
Output: Samplesheet for COMPASS pipeline
"""

def create_samplesheet(input_file, output_file):
    """
    Create samplesheet from SRA accessions

    COMPASS pipeline expects simple format:
    SRR#######
    SRR#######
    ...
    """

    print("="*70)
    print("Creating COMPASS Samplesheet")
    print("="*70)
    print()

    # Read accessions
    with open(input_file, 'r') as f:
        accessions = [line.strip() for line in f if line.strip()]

    print(f"Input file: {input_file}")
    print(f"Total accessions: {len(accessions)}")
    print()

    # Write samplesheet
    with open(output_file, 'w') as f:
        for acc in accessions:
            f.write(f"{acc}\n")

    print(f"✓ Created samplesheet: {output_file}")
    print()
    print("Sample entries:")
    for acc in accessions[:5]:
        print(f"  {acc}")
    if len(accessions) > 5:
        print(f"  ... ({len(accessions)-5} more)")
    print()

    print("Next step:")
    print("  sbatch run_clostridium.sh")
    print()

def main():
    input_file = "data/sra_accessions_clostridium.txt"
    output_file = "data/samplesheet_clostridium.txt"

    create_samplesheet(input_file, output_file)

if __name__ == "__main__":
    main()
