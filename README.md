# COMPASS Pipeline

**COMPASS**: COmprehensive Mobile element & Pathogen ASsessment Suite

An integrated Nextflow pipeline for comprehensive bacterial genomic analysis combining antimicrobial resistance (AMR) detection and phage characterization.

## Overview

COMPASS automates the analysis of bacterial genomes, providing:
- **Quality Control**: FastQC, fastp, BUSCO, QUAST, and MultiQC for comprehensive QC
- **Assembly Statistics**: Detailed metrics on assembly quality and contiguity
- **Strain Typing**: MLST for sequence type determination across 100+ species
- **Serotyping**: SISTR for Salmonella serovar prediction
- **Plasmid Detection**: MOB-suite for identifying and typing mobile genetic elements
- **AMR Detection**: AMRFinder+ and ABRicate for multi-database resistance screening
- **Phage Identification**: VIBRANT for prophage detection and lifestyle prediction
- **Prophage Analysis**: DIAMOND database comparison and CheckV quality assessment
- **Gene Prediction**: PHANOTATE for ORF calling in phage sequences
- **Integrated Reporting**: MultiQC aggregation and COMPASS summary TSV with all metrics

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
   - Raw read quality assessment with FastQC
   - Quality trimming with fastp
   - Genome assembly using SPAdes
   - Assembly quality assessment with BUSCO
   - Metadata integration for downstream analysis

3. **AMR Analysis** (`subworkflows/amr_analysis.nf`)
   - AMRFinder+ database download and management
   - Antimicrobial resistance gene detection

4. **Phage Analysis** (`subworkflows/phage_analysis.nf`)
   - VIBRANT prophage detection
   - DIAMOND prophage classification
   - CheckV quality assessment
   - PHANOTATE gene annotation

5. **Typing** (`subworkflows/typing.nf`)
   - MLST for strain typing (all bacteria)
   - SISTR for Salmonella serotyping (conditional)

6. **Mobile Elements** (`subworkflows/mobile_elements.nf`)
   - MOB-suite for plasmid detection and typing
   - Identification of mobile genetic elements

7. **Complete Pipeline** (`workflows/complete_pipeline.nf`)
   - Orchestrates all subworkflows
   - MultiQC for comprehensive QC reporting
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

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--filter_state` | State code (2-letter) | `KS` | `KS`, `CA`, `TX` |
| `--filter_year_start` | Minimum year | `null` | `2020` |
| `--filter_year_end` | Maximum year | `null` | `2023` |
| `--filter_source` | Source keyword | `null` | `chicken`, `clinical` |
| `--max_samples` | Maximum samples to process | `10000` | `5000`, `50000` |

### Database Paths

| Parameter | Description |
|-----------|-------------|
| `--amrfinder_db` | AMRFinder+ database directory |
| `--prophage_db` | Prophage DIAMOND database (.dmnd) |
| `--checkv_db` | CheckV database directory |
| `--busco_download_path` | BUSCO lineage datasets directory |

### BUSCO Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--busco_lineage` | BUSCO lineage dataset | `bacteria_odb10` |
| `--busco_mode` | BUSCO mode (genome, proteins, transcriptome) | `genome` |
| `--busco_download_path` | Path for BUSCO lineage datasets | See config |

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
├── fastqc/                      # Raw read quality assessment
│   ├── *_fastqc.html
│   └── *_fastqc.zip
├── fastp/                       # Read quality control and trimming reports
│   ├── *_fastp.json
│   └── *_fastp.html
├── trimmed_fastq/               # Quality-trimmed reads
│   └── *_trimmed*.fastq.gz
├── assemblies/                  # Assembled genomes
│   └── *_scaffolds.fasta
├── busco/                       # Assembly quality assessment
│   └── *_busco/
│       ├── short_summary.*.txt
│       └── full_table.tsv
├── mlst/                        # Strain typing results
│   └── *_mlst.tsv
├── sistr/                       # Salmonella serotyping (if applicable)
│   └── *_sistr.tsv
├── mobsuite/                    # Plasmid detection and typing
│   └── *_mobsuite/
│       ├── mobtyper_results.txt
│       └── plasmid_*.fasta
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
├── multiqc/                     # Comprehensive QC report
│   ├── multiqc_report.html
│   └── multiqc_data/
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

### Quality Control Reports

**FastQC** - Raw read quality assessment:
- `*_fastqc.html`: Interactive HTML report with per-base quality, GC content, adapter content, and more
- `*_fastqc.zip`: Archive containing all FastQC analysis files and plots

**fastp** - Trimming and post-QC reports:
- `*_fastp.html`: Interactive HTML report with quality metrics, filtering stats, and adapter detection
- `*_fastp.json`: Machine-readable JSON format with comprehensive QC data

These complementary tools provide before/after quality assessment for read trimming.

### Assembly Quality Assessment

**BUSCO** - Genome completeness and contamination:
- `short_summary.*.txt`: Summary statistics with percentages of complete, fragmented, and missing BUSCOs
- `full_table.tsv`: Detailed results for each BUSCO gene assessed
- Metrics include:
  - Complete and single-copy BUSCOs (C:S)
  - Complete and duplicated BUSCOs (C:D) - indicates potential contamination
  - Fragmented BUSCOs (F) - partial gene presence
  - Missing BUSCOs (M) - expected genes not found

### Strain Typing Results

**MLST** - Multi-locus sequence typing:
- `*_mlst.tsv`: Sequence type (ST) and allelic profile for each sample
- Automatically detects appropriate MLST scheme based on species
- Provides scheme name, ST number, and allele assignments

**SISTR** - Salmonella serotyping (Salmonella samples only):
- `*_sistr.tsv`: Serovar prediction, serogroup, H1/H2 antigens, and O antigens
- `*_sistr_allele.json`: Detailed allele calls and QC metrics
- Only runs on samples identified as Salmonella

### Mobile Elements Results

**MOB-suite** - Plasmid detection and typing:
- `mobtyper_results.txt`: Plasmid incompatibility groups and MOB types
- `plasmid_*.fasta`: Reconstructed plasmid sequences
- Identifies number of plasmids, types, and mobility characteristics

### AMRFinder Results

- `*_amr.tsv`: Detected resistance genes
- `*_mutations.tsv`: Point mutations conferring resistance

### MultiQC Report

- `multiqc_report.html`: Comprehensive HTML report aggregating all QC metrics
- `multiqc_data/`: Directory containing parsed data from all QC tools
- Includes FastQC, fastp, and BUSCO results in interactive visualizations

## Tools & Versions

| Tool | Version | Purpose |
|------|---------|---------|
| FastQC | 0.12.1 | Raw read quality assessment |
| fastp | 0.23.4 | Read quality trimming |
| SPAdes | 3.15.5 | Genome assembly |
| BUSCO | 5.7.1 | Assembly quality assessment |
| MLST | 2.23.0 | Multi-locus sequence typing |
| SISTR | 1.1.1 | Salmonella serotyping |
| MOB-suite | 3.1.9 | Plasmid detection and typing |
| AMRFinder+ | 3.12.8 | AMR gene detection |
| VIBRANT | 4.0 | Phage identification |
| DIAMOND | 2.0 | Prophage database search |
| CheckV | 1.0.2 | Phage quality assessment |
| PHANOTATE | 1.6.7 | Gene prediction |
| MultiQC | 1.25.1 | Aggregate QC reporting |

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
│   ├── busco.nf                # Assembly QC
│   ├── checkv.nf               # Phage quality control
│   ├── combine_results.nf      # Results aggregation
│   ├── diamond_prophage.nf     # Prophage classification
│   ├── fastp.nf                # Read trimming
│   ├── fastqc.nf               # Read QC
│   ├── metadata_filtering.nf   # NARMS data filtering
│   ├── mlst.nf                 # Strain typing
│   ├── mobsuite.nf             # Plasmid detection
│   ├── multiqc.nf              # Aggregate QC reporting
│   ├── phanotate.nf            # Gene prediction
│   ├── sistr.nf                # Salmonella serotyping
│   ├── sra_download.nf         # SRA data download
│   └── vibrant.nf              # Phage detection
├── subworkflows/                # Logical workflow components
│   ├── data_acquisition.nf     # Data download/filtering
│   ├── assembly.nf             # Assembly workflow with QC
│   ├── amr_analysis.nf         # AMR workflow
│   ├── phage_analysis.nf       # Phage workflow
│   ├── typing.nf               # MLST and serotyping
│   └── mobile_elements.nf      # Plasmid detection
└── workflows/                   # High-level workflows
    ├── complete_pipeline.nf    # Main orchestration workflow
    ├── integrated_analysis.nf  # Legacy combined analysis
    ├── full_pipeline.nf        # Legacy full pipeline
    └── metadata_to_results.nf  # Legacy metadata workflow
```

### Example 4: Limit number of samples

```bash
# Process only the first 100 samples after filtering
nextflow run main.nf \
    --filter_state "CA" \
    --filter_year_start 2020 \
    --max_samples 100 \
    --outdir california_limited
```

## Configuration

Edit `nextflow.config` to customize:
- Resource allocation (CPUs, memory)
- Container paths
- Database locations
- Executor settings (SLURM parameters)

## Citation

If you use COMPASS, please cite the individual tools:

**Quality Control:**
- **FastQC**: [Andrews, 2010](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/)
- **fastp**: [Chen et al., 2018](https://doi.org/10.1093/bioinformatics/bty560)
- **BUSCO**: [Manni et al., 2021](https://doi.org/10.1007/978-1-4939-9173-0_14)
- **MultiQC**: [Ewels et al., 2016](https://doi.org/10.1093/bioinformatics/btw354)

**Assembly:**
- **SPAdes**: [Bankevich et al., 2012](https://doi.org/10.1089/cmb.2012.0021)

**Typing & Characterization:**
- **MLST**: [Seemann, 2014](https://github.com/tseemann/mlst)
- **SISTR**: [Yoshida et al., 2016](https://doi.org/10.1371/journal.pone.0147101)
- **MOB-suite**: [Robertson & Nash, 2018](https://doi.org/10.1099/mgen.0.000206)

**Resistance & Virulence:**
- **AMRFinder+**: [Feldgarden et al., 2021](https://www.nature.com/articles/s41598-021-91456-0)

**Phage Analysis:**
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
