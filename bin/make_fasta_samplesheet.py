#!/usr/bin/env python3
"""
make_fasta_samplesheet.py

Build a COMPASS --input_mode fasta samplesheet from pre-downloaded genome FASTAs.

Genomes must be downloaded first with the NCBI datasets CLI:
    ~/bin/datasets download genome accession --inputfile accs.txt \
        --include genome --filename genomes.zip
    unzip -oq genomes.zip -d genomes_dl

Or in batches (recommended for >1000 accessions):
    split -l 500 accs.txt batch_
    for b in batch_*; do
        ~/bin/datasets download genome accession --inputfile "$b" \
            --include genome --filename "${b}.zip"
        unzip -oq "${b}.zip" -d "${b}_dl"
        rm "${b}.zip"
    done

USAGE:
    python3 bin/make_fasta_samplesheet.py                              # defaults
    python3 bin/make_fasta_samplesheet.py <original.csv> <genome_glob_pattern> <out.csv>

Defaults (Beocat, 6k E. coli MIC/AST run):
    original samplesheet : /fastscratch/tylerdoe/COMPASS-1.1.0/samplesheet.csv
    genome glob          : /fastscratch/tylerdoe/COMPASS-1.1.0/batch_*_dl/ncbi_dataset/data/*/*.fna
    output               : /fastscratch/tylerdoe/COMPASS-1.1.0/samplesheet_full_fasta.csv
"""

import os
import glob
import sys

DEFAULT_INPUT  = "/fastscratch/tylerdoe/COMPASS-1.1.0/samplesheet.csv"
DEFAULT_GLOB   = "/fastscratch/tylerdoe/COMPASS-1.1.0/batch_*_dl/ncbi_dataset/data/*/*.fna"
DEFAULT_OUTPUT = "/fastscratch/tylerdoe/COMPASS-1.1.0/samplesheet_full_fasta.csv"


def main():
    input_csv  = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    fna_glob   = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_GLOB
    output_csv = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUTPUT

    # load accession -> (sample, organism) from original samplesheet
    lookup = {}
    with open(input_csv) as f:
        next(f)  # skip header
        for line in f:
            line = line.strip().replace('\r', '')
            if not line:
                continue
            parts = line.split(',')
            s, org, acc = parts[0], parts[1], parts[2]
            lookup[acc] = (s, org)

    print(f"Loaded {len(lookup)} accessions from {input_csv}")

    # find all downloaded FASTAs and match to accessions
    rows = []
    missing = []
    for fna in sorted(glob.glob(fna_glob)):
        # path: .../ncbi_dataset/data/GCA_000692755.1/GCA_000692755.1_..._genomic.fna
        acc = os.path.basename(os.path.dirname(fna))
        if acc in lookup:
            s, org = lookup[acc]
            rows.append(f"{s},{os.path.abspath(fna)},{org}")
        else:
            missing.append(acc)

    with open(output_csv, "w") as f:
        f.write("sample,fasta,organism\n")
        f.write("\n".join(rows) + "\n")

    print(f"Wrote {len(rows)} samples to {output_csv}")
    if missing:
        print(f"WARNING: {len(missing)} FASTAs had no matching accession in the samplesheet")
    not_downloaded = len(lookup) - len(rows)
    if not_downloaded:
        print(f"NOTE: {not_downloaded} accessions from samplesheet have no downloaded FASTA (failed batches)")


if __name__ == "__main__":
    main()
