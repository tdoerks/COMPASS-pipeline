# Test Data Examples

This directory contains example input files for testing the COMPASS pipeline.

## Quick Start Tests

### 1. FASTA Mode Test
Edit `example_samplesheet.csv` with your actual assembly paths, then:
```bash
nextflow run main.nf \
    --input test_data/example_samplesheet.csv \
    --outdir test_results_fasta \
    -resume
```

### 2. SRA Download Test
Edit `example_srr_list.txt` with valid SRA accessions (preferably small datasets), then:
```bash
nextflow run main.nf \
    --input_mode sra_list \
    --input test_data/example_srr_list.txt \
    --outdir test_results_sra \
    -resume
```

### 3. NARMS Metadata Test
```bash
nextflow run main.nf \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --max_samples 5 \
    --outdir test_results_narms \
    -resume
```

## Finding Small Test Datasets

### Good Small SRA Datasets for Testing:
```bash
# Search for small bacterial genomes (< 100MB)
esearch -db sra -query "Salmonella[ORGN] AND bacterial[STRA]" | \
  efetch -format runinfo | \
  awk -F',' '$5 < 100000000 {print $1}' | \
  head -5 > small_test_samples.txt
```

### Or Use NARMS with Heavy Filtering:
- Set `--max_samples 3` for quick tests
- Use recent years (2024-2025) which have fewer samples
- Filter by specific isolation source

## Expected Runtime

**Single sample (FASTA mode):**
- MLST: ~1-2 min
- BUSCO: ~5-10 min
- QUAST: ~1 min
- MOB-suite: ~2-5 min
- SISTR: ~1-2 min (Salmonella only)
- ABRicate: ~2-3 min per database
- AMRFinder: ~2-5 min
- VIBRANT: ~5-15 min
- Total: ~20-40 min per sample

**Single sample (SRA mode):** Add ~10-30 min for download + assembly

**Parallel execution:** Scales linearly with available resources
