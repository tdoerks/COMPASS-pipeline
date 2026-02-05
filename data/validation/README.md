# COMPASS Validation Dataset

## Overview

This directory contains scripts and data for validating the COMPASS pipeline against ~200 well-characterized E. coli reference genomes.

**Date Created**: February 5, 2026
**Branch**: v1.3-dev
**Expected Runtime**: 24-48 hours on HPC

---

## Dataset Composition

### Tier 1: All-Features Genomes (~12 genomes)
Genomes with AMR genes + prophages + plasmids:
- **EC958** (ST131): blaCTX-M-15, 2 plasmids, multiple prophages
- **JJ1886** (ST131): blaCTX-M-15, 5 plasmids, prophages
- **ETEC strains** (7): Enterotoxigenic E. coli reference genomes
- **VREC1428** (ST131 C1-M27): blaCTX-M-27, IncFIA plasmid

### Tier 2: Control Genomes (4 genomes)
Feature-specific controls:
- **K-12 MG1655**: Prophage control (4 prophages, no AMR, no plasmids)
- **K-12 W3110**: Prophage comparison strain
- **CFT073**: Uropathogenic, pathogenicity islands
- **ATCC 25922**: Negative control (minimal AMR/prophages)

### Tier 3: FDA-ARGOS Genomes (~50 genomes)
Quality-controlled reference genomes with curated AMR profiles from FDA database

### Tier 4: Diverse E. coli Genomes (~100 genomes)
Complete genomes representing phylogenetic diversity

### Tier 5: EnteroBase Representative Genomes (~30 genomes)
Genomes representing major E. coli sequence types

**Total**: ~196 genomes

---

## Quick Start

The COMPASS pipeline now supports direct assembly downloading via NCBI Entrez Direct. No manual pre-download required!

### Step 1: Verify Samplesheet

Check the validation samplesheet exists:

```bash
cat data/validation/validation_samplesheet.csv
```

**Format**: `sample,organism,assembly_accession`
**Currently**: 14 Tier 1 & 2 genomes (expand to all 196 as needed)

---

### Step 2: Submit SLURM Job

The pipeline will automatically download assemblies from NCBI:

```bash
# Submit validation run to HPC
sbatch data/validation/run_compass_validation.sh
```

**Input mode**: `assembly` (uses DOWNLOAD_ASSEMBLY module)
**Expected runtime**: 24-48 hours
**Output**: `data/validation/results/`

The pipeline will:
1. Download assemblies via NCBI Entrez Direct (containerized)
2. Run BUSCO and QUAST for assembly QC
3. Perform AMR, prophage, plasmid, and typing analysis
4. Generate comprehensive MultiQC report

---

## Monitoring Progress

```bash
# Check SLURM job status
squeue -u $USER

# Monitor Nextflow log
tail -f data/validation/compass_validation_<JOB_ID>.out

# Check for errors
tail -f data/validation/compass_validation_<JOB_ID>.err
```

---

## Output Structure

After completion, results will be in `data/validation/results/`:

```
results/
├── amrfinder/          # AMR gene detections
├── vibrant/            # Prophage predictions
├── mobsuite/           # Plasmid typing
├── mlst/               # Sequence typing
├── multiqc/            # Aggregated QC report
├── summary/            # Summary statistics
├── nextflow_report.html    # Nextflow execution report
├── nextflow_timeline.html  # Timeline visualization
└── nextflow_dag.html       # DAG visualization
```

---

## Next Steps (After Run Completes)

1. **Review MultiQC report**:
   - Open `results/multiqc/multiqc_report.html` in browser
   - Check assembly quality (BUSCO, N50)
   - Review AMR gene counts

2. **Create validation analysis** (future session):
   - Curate ground truth annotations
   - Compare COMPASS predictions vs. known features
   - Calculate sensitivity, specificity, precision
   - Generate validation report

3. **Update documentation**:
   - Add validation results to README
   - Update Paper 1 Methods section
   - Tag v1.3 release

---

## Troubleshooting

### Assembly download fails
- Check HPC internet connectivity to NCBI
- Verify assembly accessions are valid (use NCBI Assembly browser)
- Check DOWNLOAD_ASSEMBLY process logs
- Try downloading problematic accessions manually using esearch/efetch

### SLURM job fails
- Check error log: `compass_validation_<JOB_ID>.err`
- Ensure samplesheet exists and is valid
- Check module availability (Nextflow, Apptainer)
- Verify paths are correct

### Out of memory
- Increase memory in SLURM script (`#SBATCH --mem=128G`)
- Reduce parallelization (`--max_cpus 8`)

### Long runtime
- Check Nextflow log for bottlenecks
- Use `-resume` to restart from last successful step
- Consider running tiers separately

---

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu
Kansas State University College of Veterinary Medicine

---

**Last Updated**: February 5, 2026
**Status**: Ready for download and execution
