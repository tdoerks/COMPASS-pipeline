#!/usr/bin/env python3
"""
Generate COMPASS samplesheet for Bacteroides fragilis study
"""

def main():
    # Check for input file
    input_file = "data/sra_accessions_bacteroides.txt"
    output_file = "data/samplesheet_bacteroides.txt"

    print("="*70)
    print("Generating COMPASS Samplesheet - Bacteroides fragilis")
    print("="*70)

    # Read SRR accessions
    with open(input_file, 'r') as f:
        accessions = [line.strip() for line in f if line.strip()]

    print(f"Read {len(accessions)} accessions from {input_file}")

    # Generate samplesheet
    with open(output_file, 'w') as f:
        for acc in accessions:
            f.write(f"{acc}\n")

    print(f"✓ Saved samplesheet to {output_file}")
    print(f"✓ Total samples: {len(accessions)}")
    print()
    print("="*70)
    print("Next step:")
    print("  Submit COMPASS job: sbatch run_bacteroides.sh")
    print("="*70)

if __name__ == "__main__":
    main()
