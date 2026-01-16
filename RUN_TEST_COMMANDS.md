# Commands to Run 5-Sample Test with All Fixes

Run these commands on Beocat to test the enhanced QC tab and verify all fixes:

```bash
# 1. Navigate to pipeline directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# 2. Pull latest code (has QC tab fix, metadata fix, debug output)
git pull origin v1.2-mod

# 3. Verify we have the latest commit (58f6e47)
git log --oneline -3
# Should show:
#   58f6e47 Improve COMPASS HTML report: metadata fields, MultiQC link, and empty MLST handling
#   172d69f (commit from other source - may vary)
#   2a31c21 Add native MultiQC charts to Quality Control tab

# 4. Submit test run
sbatch run_5sample_test.sh

# 5. Get the job ID and monitor
squeue -u tylerdoe
# Note the job ID (will be shown in output)

# 6. Monitor progress (replace XXXXX with your job ID)
tail -f /homes/tylerdoe/slurm-XXXXX.out
```

## What This Test Will Verify:

### ✅ Metadata Field Filtering (NEW - commit 58f6e47)
- **Expected**: Metadata Explorer dropdown shows ~18 useful fields (not 49)
- **Expected**: Fields shown: Run, BioSample, BioProject, Platform, Model, Organism, host, geo_loc_name, etc.
- **Expected**: Unused fields removed: MBases, MBytes, download_path, etc.

### ✅ MultiQC Link Removal (NEW - commit 58f6e47)
- **Expected**: No broken "../multiqc/multiqc_report.html" link in Quality Control tab
- **Expected**: Informative note about multiqc/ directory location
- **Expected**: All key QC metrics already embedded in native charts

### ✅ MLST Empty Data Handling (NEW - commit 58f6e47)
- **Expected**: If MLST data missing, shows "No MLST data available" message instead of blank chart
- **Expected**: Same for MLST schemes and serovars
- **Expected**: User can distinguish between missing data vs. rendering error

### ✅ Quality Control Tab Enhancement (from commit 2a31c21)
- **Expected**: Read Quality Scores chart displays (FastQC data)
- **Expected**: Read Processing Summary chart displays (read counts)
- **Expected**: All existing QC charts still work (N50, Length, Contigs, BUSCO)

### ✅ Metadata Columns Fix (from commit 622f5f6)
- **Expected**: compass_summary.tsv should have ~76 columns (not 27)
- **Expected**: Fields like Platform, Model, LibraryStrategy, BioProject present in TSV

## After Test Completes:

```bash
# Check if pipeline succeeded
echo "Exit code should be 0 for success"

# Verify column count in TSV
head -1 /fastscratch/tylerdoe/test_5samples_v1.2mod/summary/compass_summary.tsv | tr '\t' '\n' | wc -l
# Expected: ~76 columns (not 27)

# Check metadata fields in filtered CSV
head -1 /fastscratch/tylerdoe/test_5samples_v1.2mod/filtered_samples/filtered_samples.csv | tr ',' '\n' | wc -l
# Expected: 49 columns

# Look for max_samples debug output in SLURM log
grep -A 10 "Total filtered samples before max limit" /homes/tylerdoe/slurm-XXXXX.out

# Download HTML report to review
scp tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/test_5samples_v1.2mod/summary/compass_summary.html .
# Open in browser and verify:
#   1. Metadata Explorer has ~18 field options (not 49)
#   2. Quality Control tab shows native Read QC charts (no broken MultiQC link)
#   3. MLST tab shows data or friendly "No data available" message
```

## Expected Test Duration:
- **Total time**: ~30-60 minutes for 5 samples
- **Phases**:
  - Metadata download: 1-2 min
  - SRA download: 5-10 min
  - Assembly (Shovill): 10-20 min
  - Annotation (Bakta/AMRFinder/etc): 10-20 min
  - Summary generation: 1-2 min

## If Test Fails:
Check SLURM logs for errors:
```bash
cat /homes/tylerdoe/slurm-XXXXX.err
tail -100 /homes/tylerdoe/slurm-XXXXX.out
```

Report any errors and we'll debug!
