# COMPASS Pipeline

**COMPASS**: COmprehensive Mobile element & Pathogen ASsessment Suite

An integrated Nextflow pipeline for comprehensive bacterial genomic analysis combining antimicrobial resistance (AMR) detection and phage characterization.

## Overview

COMPASS automates the analysis of bacterial genomes, providing:
- **AMR Detection**: Antimicrobial resistance gene identification using AMRFinder+
- **Phage Identification**: Phage detection and lifestyle prediction with VIBRANT
- **Prophage Analysis**: Database comparison using DIAMOND
- **Quality Assessment**: Phage genome quality evaluation with CheckV
- **Gene Prediction**: ORF calling in phage sequences using PHANOTATE
- **Integrated Reporting**: Combined HTML reports with enhanced metrics

## Features

- **Flexible Input**: Process assemblies, raw reads, or download directly from NCBI SRA
- **NARMS Integration**: Built-in metadata filtering for NARMS surveillance BioProjects
- **Containerized**: All tools run in Apptainer/Singularity containers for reproducibility
- **HPC Ready**: Configured for SLURM cluster execution
- **Comprehensive Output**: Enhanced reports combining AMR and phage data

## Pipeline Architecture

COMPASS uses a modular architecture with the following components:

### Subworkflows

1. **Data Acquisition** (`subworkflows/data_acquisition.nf`)
   - Downloads and filters NARMS metadata
   - Downloads SRA data from NCBI
   - Supports metadata filtering or direct SRR accession lists

2. **Assembly** (`subworkflows/assembly.nf`)
   - Genome assembly using SPAdes
   - Metadata integration for downstream analysis

3. **AMR Analysis** (`subworkflows/amr_analysis.nf`)
   - AMRFinder+ database download and management
   - Antimicrobial resistance gene detection

4. **Phage Analysis** (`subworkflows/phage_analysis.nf`)
   - VIBRANT prophage detection
   - DIAMOND prophage classification
   - CheckV quality assessment
   - PHANOTATE gene annotation

5. **Complete Pipeline** (`workflows/complete_pipeline.nf`)
   - Orchestrates all subworkflows
   - Combines results for final reporting

## Quick Start

### Prerequisites

- Nextflow >= 24.04
- Apptainer/Singularity
- SLURM scheduler (or configure alternative executor)

### Installation

```bash
git clone https://github.com/tdoerks/COMPASS-pipeline.git
cd COMPASS-pipeline
```

### Basic Usage

COMPASS supports three input modes:

#### 1. FASTA Mode (Default)
Analyze pre-assembled genomes from a samplesheet:

```bash
nextflow run main.nf --input samplesheet.csv --outdir results
```

**Samplesheet format (CSV):**
```csv
sample,organism,fasta
Sample1,Salmonella,/path/to/assembly1.fasta
Sample2,Escherichia,/path/to/assembly2.fasta
Sample3,Campylobacter,/path/to/assembly3.fasta
```

**Required columns:**
- `sample`: Unique sample identifier
- `organism`: Organism name (for AMRFinder+)
- `fasta`: Path to assembly file

#### 2. NARMS Metadata Mode
Download and filter NARMS BioProject data automatically:

```bash
nextflow run main.nf \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2020 \
    --outdir results
```

**NARMS BioProjects:**
- **Campylobacter**: PRJNA292664
- **Salmonella**: PRJNA292661
- **E. coli**: PRJNA292663

#### 3. SRA List Mode
Process samples from a list of SRA accessions:

```bash
nextflow run main.nf \
    --input_mode sra_list \
    --input srr_accessions.txt \
    --outdir results
```

**SRA list format (TXT):**
```
SRR12345678
SRR12345679
SRR12345680
```

## Parameters

### Core Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `--input_mode` | Input mode: `fasta`, `metadata`, or `sra_list` | `fasta` | No |
| `--input` | Input file path (samplesheet CSV or SRR list TXT) | `samplesheet.csv` | Depends on mode |
| `--outdir` | Output directory | `results` | No |

### Metadata Filtering (for `metadata` mode)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--filter_state` | State code (2-letter) | `KS`, `CA`, `TX` |
| `--filter_year_start` | Minimum year | `2020` |
| `--filter_year_end` | Maximum year | `2023` |
| `--filter_source` | Source keyword | `chicken`, `clinical` |

### Database Paths

| Parameter | Description |
|-----------|-------------|
| `--amrfinder_db` | AMRFinder+ database directory |
| `--prophage_db` | Prophage DIAMOND database (.dmnd) |
| `--checkv_db` | CheckV database directory |

## Output Structure

```
results/
├── metadata/                    # NARMS metadata (if filtering used)
│   ├── campylobacter_metadata.csv
│   ├── salmonella_metadata.csv
│   └── ecoli_metadata.csv
├── filtered_samples/            # Filtered sample lists
│   ├── filtered_samples.csv
│   ├── srr_accessions.txt
│   └── *_srr_list.txt
├── amrfinder/                   # AMR detection results
│   ├── *_amr.tsv
│   └── *_mutations.tsv
├── vibrant/                     # Phage identification
│   └── *_vibrant/
├── diamond_prophage/            # Prophage comparisons
│   └── *_diamond_results.tsv
├── checkv/                      # Quality assessment
│   └── *_checkv/
├── phanotate/                   # Gene predictions
│   └── *_phanotate.gff
└── summary/                     # Integrated reports
    ├── phage_analysis_summary.tsv
    └── phage_analysis_report.html
```

## Output Files

### Summary Report (`summary/phage_analysis_summary.tsv`)

Tab-delimited file containing per-sample metrics:
- Total phages identified
- Lytic vs lysogenic counts
- Quality distribution (high/medium/low)
- Prophage database hits
- Best match identity
- Predicted gene counts

### HTML Report (`summary/phage_analysis_report.html`)

Interactive report with:
- Analysis overview statistics
- Quality distribution
- Detailed per-sample results table
- Tool version information

### AMRFinder Results

- `*_amr.tsv`: Detected resistance genes
- `*_mutations.tsv`: Point mutations conferring resistance

## Tools & Versions

| Tool | Version | Purpose |
|------|---------|---------|
| AMRFinder+ | 3.12.8 | AMR gene detection |
| VIBRANT | 4.0 | Phage identification |
| DIAMOND | 2.0 | Prophage database search |
| CheckV | 1.0.2 | Phage quality assessment |
| PHANOTATE | 1.6.7 | Gene prediction |

## Usage Examples

### Example 1: Pre-assembled FASTA files (default mode)

```bash
nextflow run main.nf \
    --input my_samples.csv \
    --outdir my_analysis
```

### Example 2: Kansas NARMS samples from 2020-2023 (metadata mode)

```bash
nextflow run main.nf \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2020 \
    --filter_year_end 2023 \
    --outdir kansas_2020-2023
```

### Example 3: California Salmonella from clinical sources (metadata mode)

```bash
nextflow run main.nf \
    --input_mode metadata \
    --filter_state "CA" \
    --filter_source "clinical" \
    --outdir california_clinical
```

### Example 4: Process specific SRA accessions (sra_list mode)

```bash
nextflow run main.nf \
    --input_mode sra_list \
    --input my_srr_list.txt \
    --outdir sra_analysis
```

## Directory Structure

```
COMPASS-pipeline/
├── main.nf                      # Main entry point
├── nextflow.config              # Pipeline configuration
├── modules/                     # Individual process definitions
│   ├── amrfinder.nf            # AMR detection
│   ├── assembly.nf             # Genome assembly
│   ├── checkv.nf               # Phage quality control
│   ├── combine_results.nf      # Results aggregation
│   ├── diamond_prophage.nf     # Prophage classification
│   ├── metadata_filtering.nf   # NARMS data filtering
│   ├── phanotate.nf            # Gene prediction
│   ├── sra_download.nf         # SRA data download
│   └── vibrant.nf              # Phage detection
├── subworkflows/                # Logical workflow components
│   ├── data_acquisition.nf     # Data download/filtering
│   ├── assembly.nf             # Assembly workflow
│   ├── amr_analysis.nf         # AMR workflow
│   └── phage_analysis.nf       # Phage workflow
└── workflows/                   # High-level workflows
    ├── complete_pipeline.nf    # Main orchestration workflow
    ├── integrated_analysis.nf  # Legacy combined analysis
    ├── full_pipeline.nf        # Legacy full pipeline
    └── metadata_to_results.nf  # Legacy metadata workflow
```

## Configuration

Edit `nextflow.config` to customize:
- Resource allocation (CPUs, memory)
- Container paths
- Database locations
- Executor settings (SLURM parameters)

## Citation

If you use COMPASS, please cite the individual tools:

- **AMRFinder+**: [Feldgarden et al., 2021](https://www.nature.com/articles/s41598-021-91456-0)
- **VIBRANT**: [Kieft et al., 2020](https://microbiomejournal.biomedcentral.com/articles/10.1186/s40168-020-00990-y)
- **DIAMOND**: [Buchfink et al., 2021](https://www.nature.com/articles/s41592-021-01101-x)
- **CheckV**: [Nayfach et al., 2021](https://www.nature.com/articles/s41587-020-00774-7)
- **PHANOTATE**: [McNair et al., 2019](https://academic.oup.com/bioinformatics/article/35/22/4537/5480131)

## License

MIT License

## Contributing

Issues and pull requests welcome at: https://github.com/tdoerks/COMPASS-pipeline

## Contact

- **Issues**: https://github.com/tdoerks/COMPASS-pipeline/issues
- **Author**: Tyler Doerksen (@tdoerks)

## Acknowledgments

Developed for bacterial genomics surveillance and characterization, with initial focus on NARMS data analysis.
