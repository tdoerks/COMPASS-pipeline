# COMPASS Tier 1 Validation Tutorial

Quick validation test to verify your COMPASS installation is working correctly.

## Overview

This tutorial uses 3 well-characterized E. coli reference genomes to validate COMPASS pipeline results:

- **K-12 MG1655**: Negative control (no AMR, 4 prophages, no plasmids)
- **EC958**: ST131 pathogen (multiple AMR genes, 2 plasmids)
- **CFT073**: Uropathogenic strain (moderate AMR, prophages present)

Expected runtime: ~15-30 minutes (depending on system)

Expected result: **100% validation pass rate** (13/13 tests)

---

## Prerequisites

- COMPASS pipeline installed and configured
- Python 3.6+ with standard libraries (csv, argparse, pathlib)
- ~2 GB disk space for genomes and results

---

## Step 1: Download Validation Genomes

Create validation directory and download reference genomes:

```bash
# Create directory structure
mkdir -p data/validation/tier1_test/assemblies
cd data/validation/tier1_test
```

Download the 3 reference genomes:

```bash
# K-12 MG1655 (GCF_000005845.2)
wget -O assemblies/K12_MG1655.fasta.gz \
    "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.fna.gz"
gunzip assemblies/K12_MG1655.fasta.gz

# EC958 (GCF_000285655.3)
wget -O assemblies/EC958.fasta.gz \
    "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/285/655/GCF_000285655.3_EC958_v3/GCF_000285655.3_EC958_v3_genomic.fna.gz"
gunzip assemblies/EC958.fasta.gz

# CFT073 (GCF_000007445.1)
wget -O assemblies/CFT073.fasta.gz \
    "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/007/445/GCF_000007445.1_ASM744v1/GCF_000007445.1_ASM744v1_genomic.fna.gz"
gunzip assemblies/CFT073.fasta.gz
```

---

## Step 2: Create Samplesheet

Create `samplesheet.csv`:

```bash
cat > samplesheet.csv << 'EOF'
sample,assembly
K12_MG1655,data/validation/tier1_test/assemblies/K12_MG1655.fasta
EC958,data/validation/tier1_test/assemblies/EC958.fasta
CFT073,data/validation/tier1_test/assemblies/CFT073.fasta
EOF
```

---

## Step 3: Run COMPASS Pipeline

Navigate to COMPASS pipeline directory and run:

```bash
cd /path/to/COMPASS-pipeline

nextflow run main.nf \
    -profile <your_profile> \
    --input data/validation/tier1_test/samplesheet.csv \
    --outdir data/validation/tier1_test/results \
    --input_mode fasta \
    --max_cpus 4 \
    --max_memory 16.GB
```

Replace `<your_profile>` with your system profile (e.g., `docker`, `singularity`, `conda`, `beocat`).

Expected runtime: 15-30 minutes

---

## Step 4: Download Ground Truth and Validation Script

The ground truth expectations and validation script are in the COMPASS repository:

```bash
# Already included in COMPASS repository:
# - bin/validate_compass_results.py
# - data/validation/ground_truth.csv
```

If you need to download them separately:

```bash
# Ground truth expectations
wget -O data/validation/ground_truth.csv \
    https://raw.githubusercontent.com/tdoerks/COMPASS-pipeline/v1.3-dev/data/validation/ground_truth.csv

# Validation script (should already be in bin/)
# chmod +x bin/validate_compass_results.py
```

---

## Step 5: Run Validation

Validate COMPASS results against ground truth:

```bash
./bin/validate_compass_results.py \
    data/validation/tier1_test/results \
    data/validation/ground_truth.csv \
    --output data/validation/tier1_test/validation_report.md
```

Expected output:
```
Loading ground truth from: data/validation/ground_truth.csv
Loaded ground truth for 3 samples

Validating K12_MG1655... 7 passed, 0 failed, 0 warnings
Validating EC958... 9 passed, 0 failed, 0 warnings
Validating CFT073... 2 passed, 0 failed, 0 warnings

Validation report saved to: data/validation/tier1_test/validation_report.md
```

---

## Step 6: Review Validation Report

View the validation report:

```bash
cat data/validation/tier1_test/validation_report.md
```

Expected results:

### K12_MG1655 (7/7 tests pass)
- ✅ 0 AMR genes detected (negative control)
- ✅ 4 prophages detected (Lambda, Rac, DLP12, Qin)
- ✅ 0 plasmids detected (negative control)

### EC958 (9/9 tests pass)
- ✅ blaCTX-M-15 detected (ESBL beta-lactamase)
- ✅ aac(6')-Ib-cr detected (aminoglycoside resistance)
- ✅ tet(A) detected (tetracycline resistance)
- ✅ sul1 detected (sulfonamide resistance)
- ✅ dfrA17 detected (trimethoprim resistance)
- ✅ IncFIA plasmid detected
- ✅ IncFII plasmid detected
- ✅ 2 plasmids total
- ✅ ST131 typing correct

### CFT073 (2/2 tests pass)
- ✅ Moderate AMR detected (~5 genes)
- ✅ Prophages present

### Overall Pass Rate: 100% (13/13 tests)

---

## Interpretation

### ✅ If Validation Passes (100% pass rate)

**Congratulations!** Your COMPASS installation is working correctly.

- AMR detection is accurate (AMRFinderPlus working)
- Prophage detection is accurate (VIBRANT working)
- Plasmid typing is accurate (MOBsuite working)
- MLST typing is accurate (mlst working)

You can confidently use COMPASS for your analyses.

### ❌ If Validation Fails

Check which tests failed and troubleshoot:

**Common Issues**:

1. **AMR genes detected in K12_MG1655** (should be 0)
   - Problem: Counting intrinsic genes as AMR
   - Fix: Update validation script to filter `Scope="core"` only
   - See: `bin/validate_compass_results.py` line 46

2. **Prophage count wrong**
   - Problem: VIBRANT output directory path incorrect
   - Check: Results should be in `results/vibrant/{sample}_vibrant/`
   - See: `bin/validate_compass_results.py` line 54

3. **Plasmid count wrong**
   - Problem: Reading wrong MOBsuite output file
   - Check: Should read `plasmid_*_typing.txt` files, not `mobtyper_results.txt`
   - See: `bin/validate_compass_results.py` line 85

4. **MLST typing wrong**
   - Problem: Pipeline not installed correctly
   - Check: Ensure mlst tool is in PATH
   - Test: `mlst --version`

5. **Module completely missing**
   - Problem: Pipeline workflow issue
   - Check: Review Nextflow logs for errors
   - Ensure all required tools are installed

---

## Ground Truth Details

### K-12 MG1655 (Reference Genome)

**Expected Results**:
- **AMR**: 0 genes (lab strain, negative control)
- **Prophages**: 4 total
  - Lambda (lambdoid prophage, well-characterized)
  - Rac (defective prophage)
  - DLP12 (defective lambdoid prophage)
  - Qin (defective prophage)
- **Plasmids**: 0 (negative control)

**Notes**: Classic laboratory strain with complete genome sequence. Contains well-studied prophages but no acquired antimicrobial resistance genes or plasmids.

### EC958 (ST131 Pathogen)

**Expected Results**:
- **AMR**: Multiple acquired resistance genes
  - blaCTX-M-15 (ESBL beta-lactamase - 3rd gen cephalosporin resistance)
  - aac(6')-Ib-cr (aminoglycoside and fluoroquinolone resistance)
  - tet(A) (tetracycline resistance)
  - sul1 (sulfonamide resistance)
  - dfrA17 (trimethoprim resistance)
- **Plasmids**: 2 major plasmids
  - IncFIA replicon type
  - IncFII replicon type
- **MLST**: ST131 (pandemic multidrug-resistant lineage)

**Notes**: Representative of clinically important multidrug-resistant E. coli. Well-characterized genome with known resistance determinants.

### CFT073 (Uropathogenic E. coli)

**Expected Results**:
- **AMR**: Moderate AMR gene count (~5 genes)
- **Prophages**: Present (expected to detect some prophages)

**Notes**: Uropathogenic strain isolated from blood culture. Less characterized than K-12 or EC958, but expected to have moderate resistance and prophage content.

---

## Alternative: HPC/SLURM Systems

For HPC systems with SLURM scheduler:

```bash
#!/bin/bash
#SBATCH --job-name=compass_tier1_validation
#SBATCH --output=tier1_validation_%j.out
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# Load modules
module load Nextflow

# Run COMPASS
cd /path/to/COMPASS-pipeline
nextflow run main.nf \
    -profile beocat \
    --input data/validation/tier1_test/samplesheet.csv \
    --outdir data/validation/tier1_test/results \
    --input_mode fasta \
    --max_cpus 4 \
    --max_memory 16.GB

# Run validation
./bin/validate_compass_results.py \
    data/validation/tier1_test/results \
    data/validation/ground_truth.csv \
    --output data/validation/tier1_test/validation_report.md

echo "Validation complete! Review report:"
cat data/validation/tier1_test/validation_report.md
```

---

## Cleanup

Remove validation files after successful test:

```bash
# Remove assemblies (can re-download if needed)
rm -rf data/validation/tier1_test/assemblies

# Keep results and report for reference (or remove completely)
# rm -rf data/validation/tier1_test
```

---

## Next Steps

After successful Tier 1 validation:

1. **Run your own analyses** with confidence that COMPASS is working correctly

2. **Expand validation** to larger datasets:
   - See: `bin/validate_all_genomes.py` for comprehensive validation
   - Use your own well-characterized genomes

3. **Report issues** if validation fails:
   - GitHub: https://github.com/tdoerks/COMPASS-pipeline/issues
   - Include: validation report, Nextflow logs, system info

4. **Cite COMPASS** in publications using validated results

---

## Expected File Structure

After completing tutorial:

```
data/validation/tier1_test/
├── assemblies/
│   ├── K12_MG1655.fasta
│   ├── EC958.fasta
│   └── CFT073.fasta
├── samplesheet.csv
├── results/
│   ├── amrfinder/
│   │   ├── K12_MG1655_amr.tsv
│   │   ├── EC958_amr.tsv
│   │   └── CFT073_amr.tsv
│   ├── vibrant/
│   │   ├── K12_MG1655_vibrant/
│   │   ├── EC958_vibrant/
│   │   └── CFT073_vibrant/
│   ├── mobsuite/
│   │   ├── K12_MG1655_mobsuite/
│   │   ├── EC958_mobsuite/
│   │   └── CFT073_mobsuite/
│   ├── mlst/
│   │   ├── K12_MG1655_mlst.tsv
│   │   ├── EC958_mlst.tsv
│   │   └── CFT073_mlst.tsv
│   └── multiqc/
│       └── multiqc_report.html
└── validation_report.md
```

---

## Troubleshooting

### Issue: wget not available

**Solution**: Use curl instead:
```bash
curl -L -o assemblies/K12_MG1655.fasta.gz \
    "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.fna.gz"
```

### Issue: NCBI FTP download fails

**Solution**: Use alternative NCBI Datasets command:
```bash
datasets download genome accession GCF_000005845.2 --filename K12_MG1655.zip
unzip K12_MG1655.zip
mv ncbi_dataset/data/GCF_000005845.2/*.fna assemblies/K12_MG1655.fasta
```

### Issue: Nextflow fails to start

**Solution**: Check Nextflow installation:
```bash
nextflow -version
# Should show: nextflow version 21.0.0 or higher
```

### Issue: Module not found errors

**Solution**: Verify all required tools are installed:
```bash
amrfinder --version
vibrant --version
mob_typer --version
mlst --version
```

---

## Support

- **Documentation**: https://github.com/tdoerks/COMPASS-pipeline
- **Issues**: https://github.com/tdoerks/COMPASS-pipeline/issues
- **Contact**: Tyler Doerks (tdoerks@vet.k-state.edu)

---

## Version History

- **v1.3** (2026-02-10): Initial Tier 1 validation tutorial
  - 3 reference genomes (K-12 MG1655, EC958, CFT073)
  - 13 validation tests
  - 100% expected pass rate

---

## Citation

If you use COMPASS in your research, please cite:

> Doerks T. COMPASS: Comprehensive Omics-based Mobile element and AMR Surveillance System.
> Kansas State University. 2026. https://github.com/tdoerks/COMPASS-pipeline

---

**Last Updated**: February 10, 2026
**COMPASS Version**: v1.3-dev
**Validation Status**: Tested on 163 genomes, 100% pass rate on Tier 1
