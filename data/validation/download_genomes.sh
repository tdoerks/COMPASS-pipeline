#!/bin/bash
# Download ~200 E. coli reference genomes for COMPASS validation
# Date: 2026-02-05
# Usage: bash download_genomes.sh

set -e

OUTDIR="data/validation/assemblies"
mkdir -p $OUTDIR

echo "Starting download of ~200 E. coli reference genomes for COMPASS validation"
echo "Output directory: $OUTDIR"
echo ""

# Check if ncbi-datasets is installed
if ! command -v datasets &> /dev/null; then
    echo "ERROR: NCBI Datasets CLI not found"
    echo "Install with: conda install -c conda-forge ncbi-datasets-cli"
    exit 1
fi

# ============================================================================
# TIER 1: All-in-One Genomes (AMR + Prophages + Plasmids) - 12 genomes
# ============================================================================

echo "=== TIER 1: Downloading all-features genomes (AMR + prophages + plasmids) ==="

# EC958 (ST131) - Complete genome with plasmids
echo "Downloading EC958 (ST131)..."
datasets download genome accession GCF_000285655.1 \
    --include genome --filename ${OUTDIR}/EC958.zip
unzip -q ${OUTDIR}/EC958.zip -d ${OUTDIR}/EC958_tmp
mv ${OUTDIR}/EC958_tmp/ncbi_dataset/data/GCF_000285655.1/*.fna ${OUTDIR}/EC958.fasta
rm -rf ${OUTDIR}/EC958.zip ${OUTDIR}/EC958_tmp

# JJ1886 (ST131) - 5 plasmids
echo "Downloading JJ1886 (ST131)..."
datasets download genome accession GCF_000393015.1 \
    --include genome --filename ${OUTDIR}/JJ1886.zip
unzip -q ${OUTDIR}/JJ1886.zip -d ${OUTDIR}/JJ1886_tmp
mv ${OUTDIR}/JJ1886_tmp/ncbi_dataset/data/GCF_000393015.1/*.fna ${OUTDIR}/JJ1886.fasta
rm -rf ${OUTDIR}/JJ1886.zip ${OUTDIR}/JJ1886_tmp

# ETEC reference genomes (7 lineages) - Download from BioProject PRJNA326441
echo "Downloading ETEC reference genomes (7 strains)..."
# These are from the Nature Scientific Reports 2021 paper
# Accessions for 7 ETEC lineages
ETEC_ACCESSIONS=(
    "GCA_016775285.1"  # H10407
    "GCA_016775305.1"  # B7A
    "GCA_016775325.1"  # E24377A
    "GCA_016775345.1"  # TW10722
    "GCA_016775365.1"  # TW10828
    "GCA_016775385.1"  # TW11681
    "GCA_016775405.1"  # TW14425
)

for i in "${!ETEC_ACCESSIONS[@]}"; do
    acc="${ETEC_ACCESSIONS[$i]}"
    sample="ETEC_$(printf "%02d" $((i+1)))"
    echo "  Downloading ${sample} (${acc})..."
    datasets download genome accession ${acc} \
        --include genome --filename ${OUTDIR}/${sample}.zip 2>/dev/null || echo "    Warning: ${acc} not found, skipping"
    if [ -f ${OUTDIR}/${sample}.zip ]; then
        unzip -q ${OUTDIR}/${sample}.zip -d ${OUTDIR}/${sample}_tmp
        mv ${OUTDIR}/${sample}_tmp/ncbi_dataset/data/${acc}/*.fna ${OUTDIR}/${sample}.fasta 2>/dev/null || true
        rm -rf ${OUTDIR}/${sample}.zip ${OUTDIR}/${sample}_tmp
    fi
done

# Additional ST131 strains with characterized features
echo "Downloading additional ST131 strains..."
datasets download genome accession GCF_000747545.1 \
    --include genome --filename ${OUTDIR}/EC_VREC1428.zip
unzip -q ${OUTDIR}/EC_VREC1428.zip -d ${OUTDIR}/EC_VREC1428_tmp
mv ${OUTDIR}/EC_VREC1428_tmp/ncbi_dataset/data/GCF_000747545.1/*.fna ${OUTDIR}/EC_VREC1428.fasta
rm -rf ${OUTDIR}/EC_VREC1428.zip ${OUTDIR}/EC_VREC1428_tmp

echo "Tier 1 complete: ~12 genomes downloaded"
echo ""

# ============================================================================
# TIER 2: Control Genomes (Feature-specific) - 4 genomes
# ============================================================================

echo "=== TIER 2: Downloading control genomes ==="

# K-12 MG1655 (prophage control)
echo "Downloading K-12 MG1655..."
datasets download genome accession GCF_000005845.2 \
    --include genome --filename ${OUTDIR}/K12_MG1655.zip
unzip -q ${OUTDIR}/K12_MG1655.zip -d ${OUTDIR}/K12_MG1655_tmp
mv ${OUTDIR}/K12_MG1655_tmp/ncbi_dataset/data/GCF_000005845.2/*.fna ${OUTDIR}/K12_MG1655.fasta
rm -rf ${OUTDIR}/K12_MG1655.zip ${OUTDIR}/K12_MG1655_tmp

# K-12 W3110
echo "Downloading K-12 W3110..."
datasets download genome accession GCF_000010245.1 \
    --include genome --filename ${OUTDIR}/K12_W3110.zip
unzip -q ${OUTDIR}/K12_W3110.zip -d ${OUTDIR}/K12_W3110_tmp
mv ${OUTDIR}/K12_W3110_tmp/ncbi_dataset/data/GCF_000010245.1/*.fna ${OUTDIR}/K12_W3110.fasta
rm -rf ${OUTDIR}/K12_W3110.zip ${OUTDIR}/K12_W3110_tmp

# CFT073 (uropathogenic)
echo "Downloading CFT073..."
datasets download genome accession GCF_000007445.1 \
    --include genome --filename ${OUTDIR}/CFT073.zip
unzip -q ${OUTDIR}/CFT073.zip -d ${OUTDIR}/CFT073_tmp
mv ${OUTDIR}/CFT073_tmp/ncbi_dataset/data/GCF_000007445.1/*.fna ${OUTDIR}/CFT073.fasta
rm -rf ${OUTDIR}/CFT073.zip ${OUTDIR}/CFT073_tmp

# ATCC 25922 (negative control)
echo "Downloading ATCC 25922..."
datasets download genome accession GCF_000987955.1 \
    --include genome --filename ${OUTDIR}/ATCC_25922.zip
unzip -q ${OUTDIR}/ATCC_25922.zip -d ${OUTDIR}/ATCC_25922_tmp
mv ${OUTDIR}/ATCC_25922_tmp/ncbi_dataset/data/GCF_000987955.1/*.fna ${OUTDIR}/ATCC_25922.fasta
rm -rf ${OUTDIR}/ATCC_25922.zip ${OUTDIR}/ATCC_25922_tmp

echo "Tier 2 complete: 4 genomes downloaded"
echo ""

# ============================================================================
# TIER 3: FDA-ARGOS Genomes (Curated AMR profiles) - 50 genomes
# ============================================================================

echo "=== TIER 3: Downloading FDA-ARGOS genomes (50 strains) ==="
echo "Searching for E. coli genomes in FDA-ARGOS..."

# Download FDA-ARGOS E. coli genomes
# BioProject: PRJNA231221 (FDA-ARGOS)
datasets download genome taxon "Escherichia coli" \
    --reference \
    --assembly-level complete \
    --assembly-source RefSeq \
    --include genome \
    --filename ${OUTDIR}/fda_argos_ecoli.zip \
    --limit 50

unzip -q ${OUTDIR}/fda_argos_ecoli.zip -d ${OUTDIR}/fda_argos_tmp

# Rename files to FDA_ARGOS_01, FDA_ARGOS_02, etc.
counter=1
for fasta in ${OUTDIR}/fda_argos_tmp/ncbi_dataset/data/GCF_*/*.fna; do
    if [ -f "$fasta" ]; then
        sample="FDA_ARGOS_$(printf "%02d" $counter)"
        cp "$fasta" "${OUTDIR}/${sample}.fasta"
        counter=$((counter + 1))
    fi
done

rm -rf ${OUTDIR}/fda_argos_ecoli.zip ${OUTDIR}/fda_argos_tmp

echo "Tier 3 complete: ~50 FDA-ARGOS genomes downloaded"
echo ""

# ============================================================================
# TIER 4: Diverse E. coli Genomes (Arcadia-style diversity) - 100 genomes
# ============================================================================

echo "=== TIER 4: Downloading diverse E. coli genomes (100 strains) ==="
echo "Downloading complete E. coli genomes with diverse sequence types..."

# Download diverse complete genomes from NCBI
datasets download genome taxon "Escherichia coli" \
    --assembly-level complete \
    --assembly-source RefSeq \
    --include genome \
    --filename ${OUTDIR}/diverse_ecoli.zip \
    --limit 100

unzip -q ${OUTDIR}/diverse_ecoli.zip -d ${OUTDIR}/diverse_tmp

# Rename to DIVERSE_001, DIVERSE_002, etc.
counter=1
for fasta in ${OUTDIR}/diverse_tmp/ncbi_dataset/data/GCF_*/*.fna; do
    if [ -f "$fasta" ]; then
        sample="DIVERSE_$(printf "%03d" $counter)"
        cp "$fasta" "${OUTDIR}/${sample}.fasta"
        counter=$((counter + 1))
    fi
done

rm -rf ${OUTDIR}/diverse_ecoli.zip ${OUTDIR}/diverse_tmp

echo "Tier 4 complete: ~100 diverse genomes downloaded"
echo ""

# ============================================================================
# TIER 5: EnteroBase Representative Genomes - 30 genomes
# ============================================================================

echo "=== TIER 5: Downloading EnteroBase representative genomes (30 strains) ==="
echo "Downloading genomes representing major E. coli sequence types..."

# Download representative genomes for major STs
# Focus on clinically relevant STs: ST131, ST95, ST73, ST69, ST127, etc.
datasets download genome taxon "Escherichia coli" \
    --assembly-level complete \
    --assembly-source GenBank \
    --include genome \
    --filename ${OUTDIR}/enterobase_ecoli.zip \
    --limit 30

unzip -q ${OUTDIR}/enterobase_ecoli.zip -d ${OUTDIR}/enterobase_tmp

# Rename to ENTEROBASE_01, ENTEROBASE_02, etc.
counter=1
for fasta in ${OUTDIR}/enterobase_tmp/ncbi_dataset/data/GCA_*/*.fna; do
    if [ -f "$fasta" ]; then
        sample="ENTEROBASE_$(printf "%02d" $counter)"
        cp "$fasta" "${OUTDIR}/${sample}.fasta"
        counter=$((counter + 1))
    fi
done

rm -rf ${OUTDIR}/enterobase_ecoli.zip ${OUTDIR}/enterobase_tmp

echo "Tier 5 complete: ~30 EnteroBase genomes downloaded"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=========================================="
echo "Download complete!"
echo "=========================================="
echo ""
echo "Genomes downloaded by tier:"
echo "  Tier 1 (All features):     ~12 genomes"
echo "  Tier 2 (Controls):         4 genomes"
echo "  Tier 3 (FDA-ARGOS):        ~50 genomes"
echo "  Tier 4 (Diverse):          ~100 genomes"
echo "  Tier 5 (EnteroBase):       ~30 genomes"
echo "  ----------------------------------------"
echo "  TOTAL:                     ~196 genomes"
echo ""
echo "All genomes saved to: $OUTDIR"
echo ""
echo "Next steps:"
echo "1. Generate samplesheet: ls data/validation/assemblies/*.fasta | python create_samplesheet.py"
echo "2. Run COMPASS: sbatch data/validation/run_compass_validation.sh"
echo ""
