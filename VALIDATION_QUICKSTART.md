# COMPASS Validation Run - Quick Start Guide

## Overview

Run COMPASS pipeline on 171 well-characterized E. coli reference genomes to validate:
- **AMR gene detection** (comparing to known AMR profiles)
- **Prophage prediction** (e.g., K-12 MG1655 has 4 known prophages)
- **Plasmid detection** (e.g., EC958 has 2 plasmids, JJ1886 has 5 plasmids)

**Key Feature**: Pipeline automatically downloads assemblies from NCBI - no manual download needed!

---

## Quick Start (5 minutes setup)

### On Beocat:

```bash
# 1. Navigate to COMPASS pipeline
cd /fastscratch/tylerdoe/COMPASS-pipeline

# 2. Pull latest validation setup (if not already done)
git pull origin v1.3-dev

# 3. Verify samplesheet exists
wc -l data/validation/validation_samplesheet.csv
# Should show: 172 (171 genomes + 1 header)

# 4. Submit validation run
sbatch data/validation/run_compass_validation.sh
```

**That's it!** The pipeline will:
1. Automatically download all 171 assemblies from NCBI
2. Run full COMPASS analysis (AMR, prophages, plasmids, MLST, etc.)
3. Generate MultiQC report with all results

---

## What Genomes Are Included?

### Tier 1: All-Features Genomes (14 genomes)
Perfect for validation - these have **known** AMR genes, prophages, AND plasmids:

- **EC958** (ST131): blaCTX-M-15, 2 plasmids, multiple prophages
- **JJ1886** (ST131): blaCTX-M-15, 5 plasmids, prophages
- **7 ETEC strains**: Enterotoxigenic E. coli reference genomes
- **K-12 MG1655**: 4 known prophages (Lambda, Rac, DLP12, Qin), no AMR, no plasmids
- **K-12 W3110**: Prophage comparison strain
- **CFT073**: Uropathogenic, pathogenicity islands
- **ATCC 25922**: Negative control (minimal AMR/prophages)

### Tier 2: FDA-ARGOS Genomes (50 genomes)
Quality-controlled reference genomes with **curated AMR profiles** from FDA

### Tier 3: Diverse E. coli Genomes (100 genomes)
Complete genomes representing phylogenetic diversity

### Tier 4: Major Sequence Types (7 genomes)
Representative genomes for clinically relevant STs (ST131, ST69, ST648, ST167)

**Total**: 171 reference genomes

---

## Monitoring the Run

```bash
# Check job status
squeue -u tylerdoe

# Follow output log
tail -f data/validation/compass_validation_<JOB_ID>.out

# Check for errors
tail -f data/validation/compass_validation_<JOB_ID>.err
```

---

## Expected Runtime

- **Download**: ~1-2 hours (171 assemblies, automatic)
- **Analysis**: ~24-48 hours (depends on cluster load)
- **Total**: 24-48 hours

**Resource allocation**:
- Time: 48 hours
- CPUs: 16
- Memory: 64GB
- Partition: ksu-gen-highmem.q

---

## Output Structure

Results will be in `data/validation/results/`:

```
results/
├── amrfinder/              # AMR gene detections (validate against FDA-ARGOS profiles)
├── vibrant/                # Prophage predictions (validate against K-12 MG1655 known prophages)
├── mobsuite/               # Plasmid typing (validate against EC958/JJ1886 known plasmids)
├── mlst/                   # Sequence typing (validate ST assignments)
├── multiqc/                # Aggregated QC report ← START HERE
│   └── multiqc_report.html
├── summary/                # Summary statistics
├── nextflow_report.html    # Nextflow execution report
├── nextflow_timeline.html  # Timeline visualization
└── nextflow_dag.html       # DAG visualization
```

---

## Validation Checks (After Run Completes)

### 1. Check K-12 MG1655 Prophages
**Expected**: 4 prophages (Lambda, Rac, DLP12, Qin)

```bash
ls data/validation/results/vibrant/K12_MG1655*
cat data/validation/results/vibrant/K12_MG1655*/VIBRANT_K12_MG1655*/VIBRANT_results_K12_MG1655*/VIBRANT_summary*
```

### 2. Check EC958 Plasmids
**Expected**: 2 plasmids (IncF, IncI1)

```bash
ls data/validation/results/mobsuite/EC958*
cat data/validation/results/mobsuite/EC958*/mobtyper_results.txt
```

### 3. Check JJ1886 Plasmids
**Expected**: 5 plasmids

```bash
cat data/validation/results/mobsuite/JJ1886*/mobtyper_results.txt
```

### 4. Check AMR Genes in EC958
**Expected**: blaCTX-M-15 (ESBL), aac(6')-Ib-cr, tetA, sul2, etc.

```bash
grep "bla" data/validation/results/amrfinder/EC958_amr.tsv
```

### 5. Check ATCC 25922 (Negative Control)
**Expected**: Minimal or no AMR genes, minimal prophages

```bash
wc -l data/validation/results/amrfinder/ATCC_25922_amr.tsv
ls data/validation/results/vibrant/ATCC_25922*
```

---

## Validation Metrics to Calculate

After the run completes, you can calculate:

1. **Sensitivity**: % of known AMR genes detected
   - Compare AMRFinder results to FDA-ARGOS curated profiles
   - Check EC958/JJ1886 known genes

2. **Specificity**: % of false positives
   - Check ATCC 25922 (should have minimal hits)
   - Check K-12 MG1655 (should have no AMR genes)

3. **Prophage accuracy**:
   - K-12 MG1655: Should detect 4 prophages
   - Compare sizes/positions to known prophages

4. **Plasmid detection**:
   - EC958: Should detect 2 plasmids
   - JJ1886: Should detect 5 plasmids

---

## Troubleshooting

### Problem: Assembly download fails

**Symptoms**: Error like "Could not download assembly GCF_XXXXXX"

**Solution**:
1. Check HPC internet connectivity to NCBI
2. Verify assembly accession is valid on NCBI website
3. Try restarting with `-resume` flag (already in script)

### Problem: Job runs out of memory

**Symptoms**: SLURM job killed, OOM (Out of Memory) error

**Solution**: Edit `run_compass_validation.sh`:
```bash
#SBATCH --mem=128G  # Double memory
```

### Problem: Job times out after 48 hours

**Symptoms**: Job killed after 48 hours, not all samples completed

**Solution**: Edit `run_compass_validation.sh`:
```bash
#SBATCH --time=96:00:00  # Increase to 96 hours (4 days)
```

Then restart with `-resume`:
```bash
sbatch data/validation/run_compass_validation.sh
```

### Problem: Some samples fail

**Symptoms**: Pipeline completes but some samples have errors

**Solution**:
1. Check which samples failed in MultiQC report
2. Review `.nextflow.log` for error messages
3. Common issues:
   - Assembly too fragmented (>1000 contigs) - may skip BUSCO
   - No prophages found - normal for some genomes
   - AMR genes but not on plasmids - also normal

---

## Next Steps (Future Session)

After the validation run completes:

1. **Download results to local machine**:
   ```bash
   # On your local machine
   scp -r tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/results .
   ```

2. **Review MultiQC report** in browser:
   - Open `results/multiqc/multiqc_report.html`
   - Check assembly quality (BUSCO completeness, N50, L50)
   - Review AMR gene counts per genome
   - Check prophage detection rates

3. **Create validation analysis script** (future work):
   - Parse COMPASS outputs vs. known features
   - Calculate sensitivity, specificity, precision
   - Generate validation report for publication

4. **Use for Paper 1**:
   - Add validation results to Methods section
   - Report metrics in Results section
   - Include validation table in Supplementary Materials

---

## Why These Genomes?

### K-12 MG1655
- **Most studied E. coli strain**
- 4 well-characterized prophages with known positions
- No AMR genes (perfect negative control for AMR)
- No plasmids (perfect negative control for plasmids)
- If pipeline misses Lambda prophage = **pipeline has issues**

### EC958 / JJ1886 (ST131)
- **Clinically relevant** multidrug-resistant strains
- Known AMR genes (blaCTX-M-15, aac, tet, sul)
- Known plasmids (5-6 total) with characterized replicons
- Known prophages carrying virulence factors
- **Perfect all-in-one validation strains**

### FDA-ARGOS (50 genomes)
- **Quality-controlled** by FDA
- **Curated AMR profiles** from WGS + phenotypic testing
- Gold standard for AMR gene validation
- If pipeline disagrees with FDA = investigate carefully

### ATCC 25922
- **Antibiotic susceptibility testing control strain**
- Minimal AMR genes (expected wild-type susceptible)
- Minimal prophages
- Perfect **negative control** - should have very few hits

---

## Contact

Questions? Check the main VALIDATION_GUIDE.md or session notes.

Tyler Doerks - tdoerks@vet.k-state.edu

---

**Version**: 1.0
**Date**: February 2026
**Pipeline**: COMPASS v1.3-dev
**Status**: Ready to run!
