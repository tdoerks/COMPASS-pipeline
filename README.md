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

## Quick Start

### Prerequisites

- Nextflow >= 24.04
- Apptainer/Singularity
- SLURM scheduler (or configure alternative executor)

### Installation
```bash
git clone https://github.com/tdoerks/COMPASS-pipeline.git
cd COMPASS-pipeline
Basic Usage
bash# Analyze pre-assembled genomes
nextflow run main.nf --input samplesheet.csv --outdir results

# Download and filter NARMS data for Kansas samples
nextflow run main.nf \
    --filter_state "KS" \
    --filter_year_start 2020 \
    --outdir results
Input Formats
Samplesheet (CSV)
csvsample,organism,fasta
Sample1,Salmonella,/path/to/assembly1.fasta
Sample2,Escherichia,/path/to/assembly2.fasta
Sample3,Campylobacter,/path/to/assembly3.fasta
Required columns:

sample: Unique sample identifier
organism: Organism name (for AMRFinder+)
fasta: Path to assembly file

NARMS Metadata Filtering
COMPASS can automatically download and filter NARMS BioProject data:

Campylobacter: PRJNA292664
Salmonella: PRJNA292661
E. coli: PRJNA292663

Parameters
Core Parameters
ParameterDescriptionDefault--inputInput samplesheet CSVsamplesheet.csv--outdirOutput directoryresults
Metadata Filtering
ParameterDescriptionExample--filter_stateState code (2-letter)KS, CA, TX--filter_year_startMinimum year2020--filter_year_endMaximum year2023--filter_sourceSource keywordchicken, clinical
Database Paths
ParameterDescription--amrfinder_dbAMRFinder+ database directory--prophage_dbProphage DIAMOND database (.dmnd)--checkv_dbCheckV database directory
Output Structure
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
Output Files
Summary Report (summary/phage_analysis_summary.tsv)
Tab-delimited file containing per-sample metrics:

Total phages identified
Lytic vs lysogenic counts
Quality distribution (high/medium/low)
Prophage database hits
Best match identity
Predicted gene counts

HTML Report (summary/phage_analysis_report.html)
Interactive report with:

Analysis overview statistics
Quality distribution
Detailed per-sample results table
Tool version information

AMRFinder Results

*_amr.tsv: Detected resistance genes
*_mutations.tsv: Point mutations conferring resistance

Tools & Versions
ToolVersionPurposeAMRFinder+3.12.8AMR gene detectionVIBRANT4.0Phage identificationDIAMOND2.0Prophage database searchCheckV1.0.2Phage quality assessmentPHANOTATE1.6.7Gene prediction
Usage Examples
Example 1: Kansas NARMS samples from 2020-2023
bashnextflow run main.nf \
    --filter_state "KS" \
    --filter_year_start 2020 \
    --filter_year_end 2023 \
    --outdir kansas_2020-2023
Example 2: California Salmonella from clinical sources
bashnextflow run main.nf \
    --filter_state "CA" \
    --filter_source "clinical" \
    --outdir california_clinical
Example 3: Custom assemblies
bashnextflow run main.nf \
    --input my_samples.csv \
    --outdir my_analysis
Configuration
Edit nextflow.config to customize:

Resource allocation (CPUs, memory)
Container paths
Database locations
Executor settings (SLURM parameters)

Citation
If you use COMPASS, please cite the individual tools:

AMRFinder+: Feldgarden et al., 2021
VIBRANT: Kieft et al., 2020
DIAMOND: Buchfink et al., 2021
CheckV: Nayfach et al., 2021
PHANOTATE: McNair et al., 2019

License
MIT License
Contributing
Issues and pull requests welcome at: https://github.com/tdoerks/COMPASS-pipeline
Contact

Issues: https://github.com/tdoerks/COMPASS-pipeline/issues
Author: Tyler Doerksen (@tdoerks)

Acknowledgments
Developed for bacterial genomics surveillance and characterization, with initial focus on NARMS data analysis.
