# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**COMPASS** (COmprehensive Mobile element & Pathogen ASsessment Suite) is a Nextflow DSL2 pipeline for bacterial genomic analysis, combining antimicrobial resistance (AMR) detection and phage characterization. Primary focus is on NARMS surveillance data (Salmonella, E. coli, Campylobacter).

## Project Structure

```
.
├── main.nf                      # Entry point for assembly-based analysis
├── main_metadata.nf             # Entry point for full pipeline (metadata → results)
├── nextflow.config              # Process resources, containers, SLURM configuration
├── workflows/
│   ├── integrated_analysis.nf   # AMR + Phage analysis workflow
│   ├── full_pipeline.nf         # SRA download → assembly → analysis
│   └── metadata_to_results.nf   # Complete: metadata filtering → analysis
└── modules/
    ├── metadata_filtering.nf    # NARMS BioProject download and filtering
    ├── sra_download.nf          # SRA read download (sra-tools)
    ├── assembly.nf              # SPAdes genome assembly
    ├── amrfinder.nf             # AMR gene detection (AMRFinder+)
    ├── vibrant.nf               # Phage identification (VIBRANT)
    ├── diamond_prophage.nf      # Prophage database comparison (DIAMOND)
    ├── checkv.nf                # Phage quality assessment (CheckV) - currently disabled
    ├── phanotate.nf             # Phage gene prediction (PHANOTATE)
    └── combine_results.nf       # Generate summary TSV and HTML report
```

## Running the Pipeline

### Test/Development
```bash
# Test with Kansas 2023 data (small dataset)
nextflow run main_metadata.nf \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --outdir test_results

# Or use SLURM script
sbatch test_kansas_pipeline.sh
```

### Production Run
```bash
# Full Kansas 2025 dataset
sbatch run_kansas_2025.sh

# Custom filtering
nextflow run main_metadata.nf \
    --filter_state "CA" \
    --filter_year_start 2020 \
    --filter_year_end 2023 \
    --filter_source "clinical" \
    --outdir results

# Limit number of samples (useful for testing or resource constraints)
nextflow run main_metadata.nf \
    --filter_state "CA" \
    --max_samples 100 \
    --outdir test_limited
```

### With Pre-assembled Genomes
```bash
# Create samplesheet.csv with columns: sample,organism,fasta
nextflow run main.nf --input samplesheet.csv --outdir results
```

## Architecture Details

### Three-Tiered Workflow System

1. **main.nf** → `AMR_PHAGE_ANALYSIS`: For pre-assembled genomes
2. **main_metadata.nf** → `METADATA_TO_RESULTS`: Full pipeline from NARMS metadata
3. **workflows/full_pipeline.nf** → `FULL_PIPELINE`: For custom SRR accessions

### Channel Transformations

Critical channel structure: `[meta, fasta]` where `meta` contains:
- `meta.id`: Sample identifier (SRR accession or custom ID)
- `meta.organism`: Organism name for AMRFinder (e.g., "Salmonella", "Escherichia", "Campylobacter")

**Key transformation points:**
- `metadata_to_results.nf:32-39`: Joins assembly output with organism metadata
- `integrated_analysis.nf:21`: Transforms for VIBRANT (requires `[sample_id, fasta]`)
- `full_pipeline.nf:27-33`: TODO comment indicates organism currently hardcoded

### NARMS BioProjects

Hardcoded in `modules/metadata_filtering.nf:14-24`:
- **Campylobacter**: PRJNA292664
- **Salmonella**: PRJNA292661
- **E. coli**: PRJNA292663

Metadata downloaded via entrez-direct, filtered by Python (pandas) on state, year, source. Results limited to first N samples via `params.max_samples` (default: 10,000).

### Database Requirements

Set in `nextflow.config` or via CLI:
- `--amrfinder_db`: AMRFinder+ database (auto-downloaded if empty)
- `--prophage_db`: DIAMOND-formatted prophage database (.dmnd file)
- `--checkv_db`: CheckV database directory

Current hardcoded paths in config:
```
prophage_db = "/homes/tylerdoe/databases/prophage_db.dmnd"
checkv_db = "/homes/tylerdoe/databases/checkv-db-v1.5"
```

### Container Strategy

All tools use Apptainer/Singularity containers from:
- quay.io/biocontainers (AMRFinder, entrez-direct, pandas, CheckV, PHANOTATE, sra-tools, SPAdes)
- docker://staphb/* (VIBRANT, DIAMOND)

Caching: `$HOME/.apptainer/cache` (set in nextflow.config:88)

### Parallelization

Configured in `nextflow.config` per-process:
- SRA download: 4 CPUs, 8GB RAM, 2h timeout
- SPAdes assembly: 8 CPUs, 32GB RAM, 12h timeout
- VIBRANT: 8 CPUs, 16GB RAM, 12h timeout
- Others: 1-4 CPUs, 2-8GB RAM

SLURM executor on `batch.q` queue.

## Known Issues & Workarounds

### Active Problems (from TODO.md and ROADMAP.md)

1. **CheckV disabled**: Database path issues in container. Commented out in `integrated_analysis.nf:4,26,41`
2. **PHANOTATE timeouts**: May need increased time limit in nextflow.config:54
3. **Hardcoded organism**: `full_pipeline.nf:31` sets organism="Salmonella" instead of reading from metadata
4. **No error handling**: Pipeline fails if any sample fails; needs individual sample error tolerance

### Entrez-direct Perl Warnings

Expected stderr warnings from metadata download process - these are non-fatal and can be ignored.

## Development Guidelines

### Adding New Analysis Modules

1. Create module file in `modules/` with standard Nextflow process structure
2. Define inputs/outputs following channel convention: `[meta, file]`
3. Specify container in process directive
4. Add resource requirements to `nextflow.config` with `withName:`
5. Import and call in appropriate workflow file
6. Update `combine_results.nf` if results need to be included in reports

### Modifying Resource Allocation

Edit `nextflow.config` process section. Example:
```groovy
withName: 'VIBRANT' {
    cpus = 16        // Increase parallelism
    memory = '32.GB' // Increase memory
    time = '24h'     // Extend timeout
}
```

### Testing Changes

Use small dataset (KS 2023) for rapid iteration:
```bash
nextflow run main_metadata.nf \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --outdir test_$(date +%Y%m%d)
```

Monitor with: `squeue -u $USER` or check `work/` directory for process logs.

### Output Structure

All results published to `${params.outdir}/`:
- `metadata/`: Downloaded NARMS runinfo CSVs
- `filtered_samples/`: Filtered sample lists and SRR accessions
- `amrfinder/`: AMR gene detection results (TSV)
- `vibrant/`: Phage identification results
- `diamond_prophage/`: Prophage database hits (TSV)
- `phanotate/`: Gene predictions (GFF)
- `summary/`: Combined TSV summary and HTML report

## Future Enhancements

High-priority additions (from ROADMAP.md):
- MLST for strain typing
- Plasmid detection (PlasmidFinder/MOB-suite)
- Serotyping (SISTR/SerotypeFinder)
- Virulence factor detection
- Assembly QC (CheckM/BUSCO)
- Better error handling for failed samples
- Geographic/temporal comparative analysis

## Configuration Notes

- Pipeline designed for SLURM HPC environment
- For other schedulers, modify `executor` in nextflow.config:20
- For local execution: set `process.executor = 'local'` and reduce resource requirements
- Resume failed runs: `nextflow run ... -resume`
