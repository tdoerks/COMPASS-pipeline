#!/bin/bash
#
# Build Fusobacterium host genome tree using BUSCO single-copy genes
#
# Strategy:
# 1. Extract a subset of highly conserved BUSCO genes present in all samples
# 2. Align each gene with MAFFT
# 3. Concatenate alignments
# 4. Build tree with FastTree
#

set -e

RESULTS_DIR="/fastscratch/tylerdoe/fusobacterium_results"
BUSCO_DIR="${RESULTS_DIR}/busco"
TREE_DIR="${RESULTS_DIR}/analysis/host_phylogenomics"

echo "========================================================================"
echo "Fusobacterium Host Genome Phylogenetic Tree"
echo "========================================================================"
echo ""
echo "Strategy: BUSCO single-copy core genes"
echo ""

# Create output directory
mkdir -p "${TREE_DIR}"
cd "${TREE_DIR}"

echo "Working directory: $(pwd)"
echo ""

# Load modules
module load MAFFT/7.505-GCC-11.3.0-with-extensions
module load FastTree/2.1.11-GCCcore-11.3.0

echo "========================================================================"
echo "Step 1: Identify Core BUSCO Genes"
echo "========================================================================"
echo ""

# Find all BUSCO result directories
busco_samples=$(ls -d ${BUSCO_DIR}/*_busco 2>/dev/null | wc -l)
echo "Found ${busco_samples} samples with BUSCO results"
echo ""

# Create list of all BUSCO genes present in each sample
echo "Identifying genes present in all samples..."
mkdir -p gene_lists

for sample_dir in ${BUSCO_DIR}/*_busco; do
    sample=$(basename "$sample_dir" | sed 's/_busco$//')

    # Find single-copy BUSCO sequences
    seq_dir="${sample_dir}/auto_lineage/run_bacteria_odb10/busco_sequences/single_copy_busco_sequences"

    if [ -d "$seq_dir" ]; then
        # List gene IDs (file names without extension)
        ls -1 "${seq_dir}"/*.faa 2>/dev/null | xargs -n1 basename | sed 's/\.faa$//' > "gene_lists/${sample}.txt"
    fi
done

echo "Counting gene presence across samples..."

# Find genes present in at least 90% of samples
min_samples=$((busco_samples * 90 / 100))
echo "Requiring genes in at least ${min_samples}/${busco_samples} samples"

# Count occurrences of each gene
cat gene_lists/*.txt | sort | uniq -c | sort -rn > gene_counts.txt

# Select top genes (present in most samples)
awk -v min="$min_samples" '$1 >= min {print $2}' gene_counts.txt | head -20 > core_genes.txt

n_core=$(wc -l < core_genes.txt)
echo "Selected ${n_core} core genes for tree building"
echo ""

if [ $n_core -lt 5 ]; then
    echo "WARNING: Too few core genes (${n_core}). Tree may not be reliable."
    echo "This might happen if BUSCO used different databases across samples."
    echo ""
fi

echo "Core genes selected:"
head -10 core_genes.txt
echo ""

echo "========================================================================"
echo "Step 2: Extract and Align Core Genes"
echo "========================================================================"
echo ""

mkdir -p gene_sequences
mkdir -p gene_alignments

gene_num=0
total_genes=$(wc -l < core_genes.txt)

while read gene_id; do
    gene_num=$((gene_num + 1))
    echo "Processing gene ${gene_num}/${total_genes}: ${gene_id}"

    # Extract this gene from all samples
    > "gene_sequences/${gene_id}.faa"

    for sample_dir in ${BUSCO_DIR}/*_busco; do
        sample=$(basename "$sample_dir" | sed 's/_busco$//')
        seq_dir="${sample_dir}/auto_lineage/run_bacteria_odb10/busco_sequences/single_copy_busco_sequences"
        gene_file="${seq_dir}/${gene_id}.faa"

        if [ -f "$gene_file" ]; then
            # Add sample ID to sequence header
            sed "s/^>/>SRR${sample}_/" "$gene_file" >> "gene_sequences/${gene_id}.faa"
        fi
    done

    # Count sequences
    n_seqs=$(grep -c "^>" "gene_sequences/${gene_id}.faa" || true)

    if [ $n_seqs -ge $min_samples ]; then
        # Align with MAFFT
        echo "  Aligning ${n_seqs} sequences..."
        mafft --quiet --auto "gene_sequences/${gene_id}.faa" > "gene_alignments/${gene_id}.aln" 2>/dev/null
    else
        echo "  Skipping (only ${n_seqs} sequences)"
    fi

done < core_genes.txt

echo ""
echo "Alignment complete!"
echo ""

echo "========================================================================"
echo "Step 3: Concatenate Alignments"
echo "========================================================================"
echo ""

echo "Concatenating aligned genes into super-matrix..."

# Use Python to concatenate alignments
python3 << 'PYTHON_SCRIPT'
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import glob
import sys

# Find all alignment files
aln_files = sorted(glob.glob('gene_alignments/*.aln'))

if not aln_files:
    print("ERROR: No alignment files found!")
    sys.exit(1)

print(f"Concatenating {len(aln_files)} gene alignments...")

# Dictionary to store concatenated sequences
sequences = {}

# Process each alignment
for aln_file in aln_files:
    gene_id = aln_file.split('/')[-1].replace('.aln', '')

    for record in SeqIO.parse(aln_file, 'fasta'):
        # Extract sample ID (everything before first underscore in header)
        sample_id = record.id.split('_')[0]

        if sample_id not in sequences:
            sequences[sample_id] = []

        sequences[sample_id].append(str(record.seq))

# Create concatenated sequences
concat_records = []
for sample_id, seqs in sequences.items():
    if len(seqs) == len(aln_files):  # Only include if all genes present
        concat_seq = ''.join(seqs)
        record = SeqRecord(
            Seq(concat_seq),
            id=sample_id,
            description=f"concatenated {len(seqs)} genes"
        )
        concat_records.append(record)

print(f"Concatenated sequences for {len(concat_records)} samples")
print(f"Total alignment length: {len(concat_records[0].seq)} bp")

# Write concatenated alignment
SeqIO.write(concat_records, 'concatenated_alignment.faa', 'fasta')

print("✓ Concatenated alignment saved")
PYTHON_SCRIPT

echo ""

echo "========================================================================"
echo "Step 4: Build Phylogenetic Tree"
echo "========================================================================"
echo ""

echo "Running FastTree on concatenated alignment..."
echo "This may take 10-30 minutes..."
echo ""

FastTree -log host_tree_fasttree.log concatenated_alignment.faa > host_tree.nwk

echo "✓ Tree building complete!"
echo ""

echo "========================================================================"
echo "Results"
echo "========================================================================"
echo ""

echo "Files created:"
echo "  - host_tree.nwk              : Newick tree file"
echo "  - concatenated_alignment.faa : Concatenated gene alignment"
echo "  - host_tree_fasttree.log     : FastTree log"
echo "  - gene_alignments/           : Individual gene alignments"
echo ""

# Count samples in tree
n_samples=$(grep -c "^>" concatenated_alignment.faa || echo "0")
echo "Samples in host tree: ${n_samples}"
echo ""

echo "========================================================================"
echo "Next Steps"
echo "========================================================================"
echo ""
echo "1. Visualize tree in iTOL:"
echo "   - Upload host_tree.nwk to https://itol.embl.de/"
echo "   - Compare to prophage tree topology"
echo ""
echo "2. Compare trees:"
echo "   - Prophage tree: ${RESULTS_DIR}/analysis/phylogenomics/prophage_tree.nwk"
echo "   - Host tree:     ${TREE_DIR}/host_tree.nwk"
echo ""
echo "3. Interpretation:"
echo "   - CONGRUENT trees → Vertical inheritance (co-evolution)"
echo "   - INCONGRUENT trees → Horizontal transfer"
echo ""
echo "========================================================================"
echo "COMPLETE!"
echo "========================================================================"
