# COMPASS Pipeline - FASTA Input Mode Guide

Complete guide for running COMPASS with pre-downloaded assembly FASTA files.

---

## Table of Contents

1. [When to Use FASTA Mode](#when-to-use-fasta-mode)
2. [Samplesheet Format](#samplesheet-format)
3. [Quick Start](#quick-start)
4. [Detailed Workflow](#detailed-workflow)
5. [Common Errors](#common-errors)
6. [Examples](#examples)

---

## When to Use FASTA Mode

Use FASTA mode when you:

✅ **Have pre-downloaded assemblies** (from NCBI, local sequencing, etc.)
✅ **Want to analyze reference genomes** for validation or comparison
✅ **Can't download from SRA** (network restrictions, missing SRA accessions)
✅ **Have custom/unpublished assemblies** not in public databases

**Don't use FASTA mode if:**
- You have SRA accessions → Use `--input_mode sra_list`
- You want to start from raw reads → Use SRA mode (includes QC)

---

## Samplesheet Format

### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `sample` | Unique sample identifier | `EC958` |
| `organism` | Organism name (for MLST scheme selection) | `Escherichia` |
| `fasta` | **ABSOLUTE path** to FASTA file | `/fastscratch/user/assemblies/EC958.fasta` |

### Critical Requirements

⚠️ **MUST use absolute paths** - Relative paths will fail!

✅ **Good** (absolute):
```csv
sample,organism,fasta
EC958,Escherichia,/fastscratch/tylerdoe/project/assemblies/EC958.fasta
```

❌ **Bad** (relative):
```csv
sample,organism,fasta
EC958,Escherichia,assemblies/EC958.fasta
EC958,Escherichia,./assemblies/EC958.fasta
EC958,Escherichia,../data/EC958.fasta
```

### Example Samplesheet

**File**: `my_samples_fasta.csv`

```csv
sample,organism,fasta
EC958,Escherichia,/fastscratch/tylerdoe/COMPASS-pipeline/assemblies/EC958.fasta
JJ1886,Escherichia,/fastscratch/tylerdoe/COMPASS-pipeline/assemblies/JJ1886.fasta
K12_MG1655,Escherichia,/fastscratch/tylerdoe/COMPASS-pipeline/assemblies/K12_MG1655.fasta
ATCC_25922,Escherichia,/fastscratch/tylerdoe/COMPASS-pipeline/assemblies/ATCC_25922.fasta
```

---

## Quick Start

### 1. Organize Your FASTA Files

```bash
# Create assemblies directory
mkdir -p /fastscratch/$USER/my_project/assemblies

# Place or download your FASTA files there
ls /fastscratch/$USER/my_project/assemblies/
# EC958.fasta
# JJ1886.fasta
# K12_MG1655.fasta
```

### 2. Create Samplesheet

**Method A**: Manual creation

```bash
cat > my_samples.csv <<'EOF'
sample,organism,fasta
EC958,Escherichia,/fastscratch/$USER/my_project/assemblies/EC958.fasta
JJ1886,Escherichia,/fastscratch/$USER/my_project/assemblies/JJ1886.fasta
K12_MG1655,Escherichia,/fastscratch/$USER/my_project/assemblies/K12_MG1655.fasta
EOF
```

**Method B**: Generate from directory

```bash
# Generate samplesheet from all FASTA files in directory
echo "sample,organism,fasta" > my_samples.csv
for fasta in /fastscratch/$USER/my_project/assemblies/*.fasta; do
    sample=$(basename "$fasta" .fasta)
    organism="Escherichia"  # Change as needed
    echo "$sample,$organism,$fasta" >> my_samples.csv
done
```

### 3. Run COMPASS

```bash
nextflow run main.nf \
    -profile beocat \
    --input my_samples.csv \
    --input_mode fasta \
    --outdir results_fasta \
    --max_cpus 16 \
    --max_memory 64.GB
```

---

## Detailed Workflow

### Step 1: Obtain FASTA Files

**Option A: Download from NCBI** (see [Manual Download Guide](../data/validation/MANUAL_DOWNLOAD_GUIDE.md))

**Option B: From local sequencing**
```bash
# Copy assemblies from sequencing run
cp /path/to/sequencing_run/assemblies/*.fasta ./assemblies/
```

**Option C: Assemble from reads** (external to COMPASS)
```bash
# Example with SPAdes
spades.py -1 reads_R1.fq -2 reads_R2.fq -o assembly_output
cp assembly_output/contigs.fasta assemblies/sample1.fasta
```

### Step 2: Verify FASTA Files

```bash
# Check files exist
ls -lh assemblies/*.fasta

# Verify FASTA format (should start with >)
head -1 assemblies/EC958.fasta
# >NZ_HG941718.1 Escherichia coli EC958 chromosome, complete genome

# Check file size (should be >1 MB for bacterial genome)
du -h assemblies/*.fasta
```

### Step 3: Create Samplesheet with Absolute Paths

**Helper Script**: `create_fasta_samplesheet.sh`

```bash
#!/bin/bash
# Create FASTA-mode samplesheet with absolute paths

ASSEMBLY_DIR="/fastscratch/$USER/my_project/assemblies"
ORGANISM="Escherichia"  # Change as needed
OUTPUT="my_samples.csv"

echo "sample,organism,fasta" > "$OUTPUT"

for fasta in "$ASSEMBLY_DIR"/*.fasta; do
    if [ -f "$fasta" ]; then
        sample=$(basename "$fasta" .fasta)
        # Get absolute path
        abs_path=$(realpath "$fasta")
        echo "$sample,$ORGANISM,$abs_path" >> "$OUTPUT"
    fi
done

echo "Created samplesheet: $OUTPUT"
wc -l "$OUTPUT"
```

**Usage**:
```bash
chmod +x create_fasta_samplesheet.sh
./create_fasta_samplesheet.sh
```

### Step 4: Validate Samplesheet

```bash
# Check format
head -5 my_samples.csv

# Verify all files exist
while IFS=, read -r sample organism fasta; do
    if [ "$sample" != "sample" ]; then
        if [ ! -f "$fasta" ]; then
            echo "ERROR: File not found for $sample: $fasta"
        else
            echo "OK: $sample"
        fi
    fi
done < my_samples.csv
```

### Step 5: Run Pipeline

**Interactive Mode** (small datasets):
```bash
nextflow run main.nf \
    -profile beocat \
    --input my_samples.csv \
    --input_mode fasta \
    --outdir results
```

**SLURM Batch Job** (large datasets):

Create `run_fasta.sh`:
```bash
#!/bin/bash
#SBATCH --job-name=compass_fasta
#SBATCH --output=compass_fasta_%j.out
#SBATCH --error=compass_fasta_%j.err
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G

module load Nextflow

cd $SLURM_SUBMIT_DIR

nextflow run main.nf \
    -profile beocat \
    --input my_samples.csv \
    --input_mode fasta \
    --outdir results_fasta \
    --max_cpus 16 \
    --max_memory 64.GB \
    -resume \
    -with-report results_fasta/nextflow_report.html \
    -with-timeline results_fasta/nextflow_timeline.html
```

Submit:
```bash
sbatch run_fasta.sh
```

---

## Common Errors

### Error 1: "Argument of file() function cannot be null"

**Symptom**:
```
ERROR ~ Argument of `file` function cannot be null
 -- Check script 'main.nf' at line: 62
```

**Cause**: Samplesheet has wrong column name

**Solution**: Make sure column is named `fasta` (not `file`, `path`, or `assembly_accession`)

```csv
# Wrong
sample,organism,file
sample,organism,assembly_accession

# Correct
sample,organism,fasta
```

---

### Error 2: "Unable to read from 'sample.fasta'"

**Symptom**:
```
[15:43:19] Unable to read from 'EC958.fasta'
```

**Cause**: Used relative paths instead of absolute paths

**Diagnosis**:
```bash
# Check work directory
ls -la work/00/abc123.../
# Shows broken symlink

ls -L work/00/abc123.../sample.fasta
# ls: cannot access: No such file or directory
```

**Solution**: Use absolute paths in samplesheet
```bash
# Convert relative to absolute
realpath assemblies/EC958.fasta
# /fastscratch/tylerdoe/project/assemblies/EC958.fasta
```

---

### Error 3: File not found

**Symptom**: Pipeline can't find FASTA files

**Causes**:
1. File doesn't exist at specified path
2. Typo in filename
3. Permissions issue

**Diagnosis**:
```bash
# Test each file in samplesheet
while IFS=, read -r sample organism fasta; do
    if [ "$sample" != "sample" ]; then
        if [ -f "$fasta" ]; then
            echo "✓ $sample: OK"
        else
            echo "✗ $sample: NOT FOUND at $fasta"
        fi
    fi
done < my_samples.csv
```

**Solution**: Fix paths or copy files to correct location

---

### Error 4: DAG file already exists

**Symptom**:
```
DAG file already exists: results/nextflow_dag.html
```

**Cause**: Previous run created output files

**Solution**: Clean up before restarting
```bash
rm -rf results/
rm -rf .nextflow/
```

---

## Examples

### Example 1: Validation Dataset

**Scenario**: Run COMPASS on 10 reference genomes for validation

```bash
# 1. Download genomes (see Manual Download Guide)
mkdir -p validation/assemblies

# 2. Create samplesheet
cat > validation_samples.csv <<'EOF'
sample,organism,fasta
K12_MG1655,Escherichia,/fastscratch/tylerdoe/validation/assemblies/K12_MG1655.fasta
EC958,Escherichia,/fastscratch/tylerdoe/validation/assemblies/EC958.fasta
JJ1886,Escherichia,/fastscratch/tylerdoe/validation/assemblies/JJ1886.fasta
ATCC_25922,Escherichia,/fastscratch/tylerdoe/validation/assemblies/ATCC_25922.fasta
CFT073,Escherichia,/fastscratch/tylerdoe/validation/assemblies/CFT073.fasta
EOF

# 3. Run pipeline
nextflow run main.nf \
    -profile beocat \
    --input validation_samples.csv \
    --input_mode fasta \
    --outdir validation_results
```

---

### Example 2: Custom Isolates

**Scenario**: Analyze locally sequenced outbreak isolates

```bash
# 1. Assemblies from sequencing facility
ls outbreak_assemblies/
# isolate_001.fasta
# isolate_002.fasta
# isolate_003.fasta

# 2. Generate samplesheet
echo "sample,organism,fasta" > outbreak_samples.csv
for fasta in outbreak_assemblies/*.fasta; do
    sample=$(basename "$fasta" .fasta)
    abs_path=$(realpath "$fasta")
    echo "$sample,Escherichia,$abs_path" >> outbreak_samples.csv
done

# 3. Run COMPASS
sbatch -J outbreak_compass <<'EOF'
#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G

module load Nextflow

nextflow run main.nf \
    -profile beocat \
    --input outbreak_samples.csv \
    --input_mode fasta \
    --outdir outbreak_results \
    -resume
EOF
```

---

### Example 3: Mixed Organisms

**Scenario**: Analyze different bacterial species

```bash
cat > mixed_samples.csv <<'EOF'
sample,organism,fasta
EC_01,Escherichia,/fastscratch/user/assemblies/EC_01.fasta
SA_02,Staphylococcus,/fastscratch/user/assemblies/SA_02.fasta
LM_03,Listeria,/fastscratch/user/assemblies/LM_03.fasta
SE_04,Salmonella,/fastscratch/user/assemblies/SE_04.fasta
EOF

nextflow run main.nf \
    -profile beocat \
    --input mixed_samples.csv \
    --input_mode fasta \
    --outdir mixed_results
```

---

## Best Practices

### File Organization
```
project/
├── assemblies/           # FASTA files
│   ├── sample1.fasta
│   ├── sample2.fasta
│   └── sample3.fasta
├── samplesheet.csv       # Metadata
├── run_compass.sh        # SLURM script
└── results/              # Output (created by pipeline)
```

### Naming Conventions
- Use consistent, descriptive sample names
- Avoid spaces and special characters in filenames
- Use `.fasta` or `.fa` extension (not `.fna`, `.txt`, etc.)

### Quality Control
Before running COMPASS, check:
- ✅ Assembly quality (N50, L50, completeness)
- ✅ File integrity (not corrupted/truncated)
- ✅ Correct organism (matches expected species)

### Resource Allocation
- Small datasets (<10 samples): 8 CPUs, 32GB RAM
- Medium datasets (10-100 samples): 16 CPUs, 64GB RAM
- Large datasets (>100 samples): 32 CPUs, 128GB RAM

---

## See Also

- [VALIDATION_QUICKSTART.md](../VALIDATION_QUICKSTART.md) - Validation-specific workflow
- [Manual Download Guide](../data/validation/MANUAL_DOWNLOAD_GUIDE.md) - Downloading genomes from NCBI
- [QUICK_START.md](../QUICK_START.md) - General COMPASS usage
- [Main README](../README.md) - Full documentation

---

## Contact

For questions or issues with FASTA input mode:
- Tyler Doerksen - tdoerks@vet.k-state.edu
- GitHub Issues: https://github.com/tdoerks/COMPASS-pipeline/issues

---

**Last Updated**: February 2026
**Pipeline Version**: COMPASS v1.3-dev
