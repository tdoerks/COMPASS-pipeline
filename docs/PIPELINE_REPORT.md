# COMPASS Pipeline Execution Report

## Overview

The pipeline execution report provides a comprehensive summary of all COMPASS pipeline steps and results in a single, easy-to-read HTML document.

## What's Included

The report documents every stage of the pipeline with key statistics:

### 1. **Metadata Filtering**
- Total samples in BioProject
- Samples after filtering
- Samples selected for analysis
- Filters applied (state, year, source, etc.)

### 2. **SRA Download**
- Downloads attempted
- Successful downloads
- Success rate with progress bar

### 3. **FastQC - Raw Read Quality**
- Samples analyzed
- Initial quality assessment

### 4. **fastp - Read Trimming & Filtering**
- Samples processed
- Average reads before/after trimming
- Average Q30 rate
- Base quality statistics

### 5. **SPAdes - Genome Assembly**
- Assemblies generated
- Average assembly size (Mb)
- Average N50 (kb)
- Average number of contigs
- GC content

### 6. **BUSCO - Assembly Completeness**
- Samples analyzed
- Average complete BUSCOs (%)
- Average fragmented/missing percentages

### 7. **AMRFinder - Antimicrobial Resistance**
- Total AMR genes detected
- Samples with AMR
- Average AMR per sample
- **Top 10 AMR genes** with counts
- **Top drug classes** with counts

### 8. **VIBRANT - Prophage Detection**
- Total prophages detected
- Samples with prophages
- Average prophages per sample
- Prophage quality distribution (complete, medium, low)

### 9. **MLST - Sequence Typing** *(if applicable)*
- Samples typed
- Unique sequence types
- Novel STs detected
- Top 10 sequence types

### 10. **SISTR - Salmonella Serotyping** *(if applicable)*
- Samples serotyped
- Unique serotypes
- Top 10 serotypes

### 11. **MOB-suite - Plasmid Detection** *(if applicable)*
- Total plasmids detected
- Samples with plasmids
- Average plasmids per sample
- Top 10 Inc types

## Usage

### Basic Usage

```bash
# Generate report for a single results directory
python3 bin/generate_pipeline_report.py /path/to/results

# Example with Kansas E. coli results
python3 bin/generate_pipeline_report.py /homes/tylerdoe/kansas_ecoli_results/2024
```

### Multi-Year Analysis

If you have results organized by year, run the report on each year directory:

```bash
# Generate reports for each year
for year in 2021 2022 2023 2024 2025; do
    python3 bin/generate_pipeline_report.py /path/to/results/$year
done
```

### Expected Directory Structure

The report generator looks for these files in the results directory:

```
results/
├── metadata/
│   └── *runinfo*.csv
├── filtered_samples/
│   ├── *filtered*.csv
│   └── *accessions*.txt
├── reads/
│   └── *_1.fastq.gz, *_2.fastq.gz
├── fastqc/
│   └── *_fastqc.html
├── fastp/
│   └── *.json
├── assemblies/
│   └── *.fasta
├── quast/
│   └── */report.tsv
├── busco/
│   └── */short_summary*.txt
├── amr_combined.tsv
├── vibrant_combined.tsv
├── mlst_combined.tsv (optional)
├── sistr_combined.tsv (optional)
└── mobsuite_combined.tsv (optional)
```

## Output

The script generates:

**`pipeline_execution_report.html`** - Beautiful, self-contained HTML report

Features:
- Responsive design
- Color-coded sections
- Statistics cards
- Progress bars
- Tables with top genes/types
- No external dependencies (can be viewed offline)

## Viewing the Report

### On Local Computer

```bash
# Open directly in browser
open pipeline_execution_report.html  # macOS
xdg-open pipeline_execution_report.html  # Linux
start pipeline_execution_report.html  # Windows
```

### From Beocat

```bash
# Copy report to your local computer
scp tylerdoe@beocat.cis.ksu.edu:/path/to/results/pipeline_execution_report.html .

# Then open locally
open pipeline_execution_report.html
```

## Example Output

### Terminal Output

```
================================================================================
COMPASS Pipeline Report Generator
================================================================================

Analyzing results in: /homes/tylerdoe/kansas_ecoli_results/2024

[1/12] Parsing metadata filtering logs...
[2/12] Parsing SRA download results...
[3/12] Parsing FastQC results...
[4/12] Parsing fastp results...
[5/12] Parsing assembly results...
[6/12] Parsing QUAST results...
[7/12] Parsing BUSCO results...
[8/12] Parsing AMRFinder results...
[9/12] Parsing VIBRANT results...
[10/12] Parsing MLST results...
[11/12] Parsing SISTR results...
[12/12] Parsing MOB-suite results...

Generating HTML report...
================================================================================
✅ Report generation complete!
================================================================================

Report saved to: /homes/tylerdoe/kansas_ecoli_results/2024/pipeline_execution_report.html

To view: open /homes/tylerdoe/kansas_ecoli_results/2024/pipeline_execution_report.html
```

### HTML Report Sections

The HTML report includes:

1. **Header** - Pipeline name, generation date, description
2. **Step-by-step sections** - Each with stat cards and tables
3. **Summary** - List of all pipeline steps performed

#### Stat Cards

Each section has visual stat cards showing key metrics:

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ TOTAL SAMPLES       │  │ QC PASS RATE        │  │ SAMPLES WITH AMR    │
│                     │  │                     │  │                     │
│      788            │  │     98.5%           │  │      756            │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

#### Tables

Top genes, drug classes, serotypes shown in sortable tables:

```
Top 10 AMR Genes Detected
─────────────────────────────────
Gene             Count
─────────────────────────────────
glpT_E448K       436
mdsA             88
mdsB             89
fosA7            89
dfrA51           12
```

## Tips

1. **Run after pipeline completes** - Wait for all jobs to finish for complete statistics
2. **One report per year** - If analyzing multiple years, generate separate reports
3. **Share easily** - HTML file is self-contained, can email or share via cloud
4. **Update FEATURE_IDEAS.md** - If you want customizations, add them there

## Troubleshooting

### "Results directory not found"
Check the path is correct and points to a directory with COMPASS results

### "No data in sections"
Ensure combined result files exist (`amr_combined.tsv`, `vibrant_combined.tsv`, etc.)
Check that pipeline completed successfully

### "Module import errors"
Ensure you're using Python 3.6+ with standard library (no external dependencies needed)

## Integration with Pipeline

To automatically generate this report at the end of each pipeline run, add to your workflow:

```groovy
// In workflows/complete_pipeline.nf
process GENERATE_REPORT {
    publishDir "${params.outdir}/reports", mode: 'copy'

    input:
    path(results_dir)

    output:
    path("pipeline_execution_report.html")

    script:
    """
    python3 ${projectDir}/bin/generate_pipeline_report.py ${results_dir}
    """
}
```

## See Also

- `FEATURE_IDEAS.md` - For enhancement requests
- `bin/generate_summary_report.py` - Alternative high-level summary report
- `bin/comprehensive_amr_analysis.py` - Detailed AMR-phage analysis
- `analysis/QUICK_START.md` - Guide for deep dive analyses
