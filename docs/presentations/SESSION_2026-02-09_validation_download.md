# Validation Download Session - February 9, 2026

## Summary

Working on manual download of 170 validation genomes on local Windows machine after Beocat network blocks all NCBI access methods.

## E. coli Monthly 100 Status

**Problem**: Job 6301614 failed after 14 hours due to disk space exhaustion

**Error**: `Failed to publish file` - fastscratch filesystem at 100% capacity (88T/89T used)

**Action Taken**:
- Deleted archived results from fastscratch that exist in /bulk/tylerdoe/archives/
- Removed: ecoli_2020_all_narms, kansas_2020-2022_ecoli, results_ecoli_2023/2024, kansas_2021-2025_all_narms_v1.2mod
- Freed ~2TB (now at 98% usage)
- Still need to clean up old ecoli_monthly_100 runs and work directories

**Next Steps**:
- Continue cleanup to get below 90% usage
- Check sizes of ecoli_monthly_100_2026* directories to keep most complete one
- Restart job once sufficient space available

## Validation Download Progress

### Approach

Using manual download on Windows local machine with NCBI Datasets API because:
- Beocat blocks NCBI Datasets API (TLS timeout)
- Beocat blocks NCBI FTP (connection stalls)
- Beocat blocks NCBI E-utilities (HTTP 400)

### Windows Setup

```powershell
# Create download directory
New-Item -ItemType Directory -Path "$HOME\compass_validation_genomes" -Force
cd $HOME\compass_validation_genomes

# Download samplesheet
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tdoerks/COMPASS-pipeline/v1.3-dev/data/validation/validation_samplesheet.csv" -OutFile "validation_samplesheet.csv"

# Enable script execution
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force
```

### Download Script Evolution

**Attempt 1: FTP Direct URLs**
- Failed - all 404 errors
- Problem: FTP paths require assembly name (e.g., `GCF_000005845.2_ASM584v2/`) which we don't have in samplesheet

**Attempt 2: NCBI Datasets API** (Current)
- URL: `https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/$accession/download?include_annotation_type=GENOME_FASTA&filename=$accession.zip`
- Downloads zip, extracts FASTA, cleans up
- **GCF accessions (RefSeq)**: Working well (~80% success rate)
- **GCA accessions (GenBank)**: Failing with "file too small" API errors

### Current Results (First 14 Genomes)

**Successful (7)**:
- JJ1886 (GCF_000393015.1)
- VREC1428 (GCF_000747545.1)
- ETEC_TW10722 (GCA_016775345.1)
- ETEC_TW11681 (GCA_016775385.1)
- K12_MG1655 (GCF_000005845.2)
- CFT073 (GCF_000007445.1)
- ATCC_25922 (GCF_000987955.1)

**Failed (7)**:
- EC958 (GCF_000285655.1) - No FASTA in archive
- K12_W3110 (GCF_000010245.1) - No FASTA in archive
- ETEC_H10407 (GCA_016775285.1) - API error (file too small)
- ETEC_B7A (GCA_016775305.1) - API error
- ETEC_E24377A (GCA_016775325.1) - API error
- ETEC_TW10828 (GCA_016775365.1) - API error
- ETEC_TW14425 (GCA_016775405.1) - API error

### Pattern

- **RefSeq (GCF)**: ~80% success rate - mostly working
- **GenBank (GCA)**: High failure rate - API returns small/corrupt files

### Next Session Tasks

1. **Complete Download**: Let script finish all 170 genomes overnight
   - Prevent Windows sleep: `powercfg /change standby-timeout-ac 0`
   - Or manually set Power settings to "Never sleep"

2. **Handle Failures**: For failed downloads, try alternative methods:
   - Use NCBI Datasets CLI tool on Windows
   - Try direct FTP with proper assembly names (query NCBI API for paths)
   - Use Entrez Direct esearch/efetch if needed
   - Manual download for critical reference genomes

3. **Transfer to Beocat**: Once downloads complete
   ```bash
   # Create tar archive
   tar -czf validation_genomes.tar.gz assemblies/

   # Transfer via SCP
   scp validation_genomes.tar.gz tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/

   # Extract on Beocat
   ssh tylerdoe@beocat.ksu.edu
   cd /fastscratch/tylerdoe/COMPASS-pipeline/data/validation
   tar -xzf validation_genomes.tar.gz
   ```

4. **Create FASTA Samplesheet**: On Beocat
   ```bash
   cd /fastscratch/tylerdoe/COMPASS-pipeline/data/validation
   echo "sample,organism,fasta" > validation_samplesheet_fasta.csv
   for fasta in assemblies/*.fasta; do
       sample=$(basename "$fasta" .fasta)
       echo "$sample,Escherichia,$PWD/$fasta" >> validation_samplesheet_fasta.csv
   done
   ```

5. **Update and Submit Validation Job**:
   ```bash
   # Modify SLURM script to use fasta mode
   sed -i 's/--input_mode assembly/--input_mode fasta/' data/validation/run_compass_validation.sh
   sed -i 's/validation_samplesheet.csv/validation_samplesheet_fasta.csv/' data/validation/run_compass_validation.sh

   # Submit
   sbatch data/validation/run_compass_validation.sh
   ```

## Files

**Created on Windows**:
- `C:\Users\Tyler\compass_validation_genomes\download_genomes_datasets.ps1` - Download script using NCBI Datasets API
- `C:\Users\Tyler\compass_validation_genomes\validation_samplesheet.csv` - 170 genome accessions
- `C:\Users\Tyler\compass_validation_genomes\assemblies\*.fasta` - Downloaded genomes (in progress)

**Existing on Beocat**:
- `/tmp/COMPASS-pipeline/docs/presentations/MANUAL_VALIDATION_DOWNLOAD_GUIDE.md` - Complete manual download guide
- `/tmp/COMPASS-pipeline/data/validation/validation_samplesheet.csv` - 170 genome accessions
- `/tmp/COMPASS-pipeline/data/validation/run_compass_validation.sh` - SLURM script (needs modification for fasta mode)

## Expected Timeline

- **Tonight**: Windows download running (1-3 hours, ~120-140 successful)
- **Tomorrow**: Handle failures, create tar, transfer to Beocat (~1 hour)
- **Next Session**: Extract, create samplesheet, submit validation job (~15 min)
- **Validation Run**: 24-48 hours on Beocat

## Known Issues

1. **GCA accessions failing**: NCBI Datasets API returns errors for many GenBank accessions
   - May need alternative download method
   - Could use esearch/efetch on local machine
   - Some may require manual download

2. **Disk space on Beocat**: Still at 98% capacity
   - Need to finish cleanup before restarting E. coli Monthly 100
   - Consider archiving old monthly runs to /bulk

3. **Sleep mode**: Windows will stop script if computer sleeps
   - Must disable sleep or use caffeine utility

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu

**Status**: Validation download in progress on Windows
**Date**: February 9, 2026
**Branch**: v1.3-dev
