# COMPASS Pipeline Troubleshooting Session - January 13, 2025

## Session Summary

**MAJOR BREAKTHROUGH!** Found and fixed the root cause of metadata fields showing only 2-3 instead of 40+.

## Critical Bug Found and Fixed ✅

### The Bug
**Location**: `bin/generate_compass_summary.py` line 3462

**Problem**: Column reordering code was explicitly DROPPING all SRA metadata columns!

```python
# OLD CODE (BUG):
column_order = [col for col in column_order if col in df.columns]
df = df[column_order]  # ← Only kept 27 hardcoded columns, dropped all 49 metadata fields!
```

This filtered the DataFrame to only the 27 explicitly listed analysis columns (organism, year, assembly stats, AMR, MLST, etc.), completely dropping all SRA metadata fields (Platform, Model, LibraryStrategy, BioProject, LibraryLayout, BioSample, etc.)

### The Fix (Commit ecaf3d6)

```python
# NEW CODE (FIXED):
# Reorder columns: put known analysis columns first, then append ALL remaining columns (metadata)
# This preserves all SRA metadata fields (Platform, Model, LibraryStrategy, BioProject, etc.)
column_order = [col for col in column_order if col in df.columns]
other_columns = [col for col in df.columns if col not in column_order]
df = df[column_order + other_columns]  # Keep ALL columns!
```

**What This Does**:
- Puts known analysis columns (organism, year, assembly stats, AMR, etc.) at the FRONT
- Appends ALL remaining metadata columns AFTER
- **Never drops any columns**

**Expected Result**:
- `compass_summary.tsv`: ~76 columns (27 analysis + 49 metadata) instead of 27
- HTML Metadata Explorer: Shows "49 Metadata Fields Available" instead of "3 Fields"
- Dropdown: 40+ field options (Platform, Model, LibraryStrategy, BioProject, etc.)

## Diagnostic Journey (How We Found It)

### 1. Initial Symptoms
- Report showed only 2-3 metadata fields (organism, year, maybe source)
- Expected 40+ fields from SRA runinfo
- Sample count showed 6 instead of 5 (minor issue, not related)

### 2. Verification Steps
✅ **filtered_samples.csv exists** - 49 columns with all SRA metadata
✅ **Sample IDs match** - All 6 samples in both files (SRR35618478, SRR35618477, etc.)
✅ **File path correct** - Using `/fastscratch/tylerdoe/test_5samples_v1.2mod/filtered_samples/filtered_samples.csv`
✅ **parse_metadata() code correct** - Properly reads all 49 columns and stores in dictionary
✅ **Row building code correct** - Properly adds all metadata fields to each row dict

### 3. The Smoking Gun
```bash
$ head -1 compass_summary.tsv | tr '\t' '\n' | wc -l
27  # ← Only 27 columns in output!

$ head -1 filtered_samples.csv | tr ',' '\n' | wc -l  
49  # ← But 49 columns in input!

$ grep "df = df\[column_order\]" bin/generate_compass_summary.py
df = df[column_order]  # ← FOUND IT! This line drops all metadata!
```

### 4. Root Cause Analysis
The code was:
1. ✅ Reading all 49 columns from CSV
2. ✅ Storing all fields in metadata dictionary
3. ✅ Adding all fields to each row
4. ✅ Creating DataFrame with all columns
5. ❌ **Then immediately filtering to only 27 columns before saving!**

## Files Modified

### Commit ecaf3d6 (Latest)
- **bin/generate_compass_summary.py** (lines 3460-3464)
  - Changed column reordering to preserve ALL columns
  - Added comments explaining the fix

## Current Status

### ✅ Fixed
- **Column filtering bug** - All metadata columns now preserved
- Code pushed to v1.2-mod branch (commit ecaf3d6)

### ⏳ Pending Test
- Need full pipeline run with new code to verify fix works end-to-end
- User has another run in progress with OLD code (will still show 27 columns)
- After that run finishes, need to:
  1. Pull latest code (git pull origin v1.2-mod)
  2. Run fresh test: sbatch run_5sample_test.sh
  3. Verify compass_summary.tsv has ~76 columns
  4. Verify HTML shows 40+ metadata fields

### ⚠️ Still To Debug
- **MLST data not displaying** - Files exist with valid data, but not showing in report
  - Debug output added in previous session (commit 05e7051)
  - Will see debug messages in next pipeline run
- **Sample count showing 6 instead of 5** - Minor issue, filtering selected 6 samples

## Technical Details

### Data Flow (Now Fixed)
1. **Input**: `filtered_samples.csv` - 49 columns, 6 samples
2. **parse_metadata()**: Reads all 49 columns → dict with 48 fields per sample (excludes 'Run')
3. **Row building**: Adds all 48 metadata fields + 27 analysis fields = 75 total fields
4. **DataFrame creation**: df has all 75 columns
5. **Column reordering** (FIXED): Reorders but keeps all 75 columns
6. **Output**: `compass_summary.tsv` - 75 columns (27 analysis + 48 metadata)

### Metadata Columns Being Preserved (Examples)
- Platform, Model (e.g., "ILLUMINA", "Illumina MiSeq")
- LibraryStrategy, LibrarySelection, LibrarySource, LibraryLayout
- BioProject, BioSample, SRAStudy
- ReleaseDate, LoadDate, spots, bases
- organism, Year, source (user-added fields)
- And 40+ more SRA runinfo fields!

### HTML Report Impact
The HTML report's Metadata Explorer dynamically reads column names from the TSV:
- Counts available metadata fields
- Populates dropdown with field names
- Creates visualizations based on selected field

With the fix:
- Will show "49 Metadata Fields Available" (not "3")
- Dropdown will have 40+ options (not 3)
- Users can explore Platform, Model, BioProject, Library details, etc.

## Commands for Next Session

### 1. Pull Latest Code
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull origin v1.2-mod
git log --oneline -1
# Should show: ecaf3d6 CRITICAL FIX: Preserve all metadata columns
```

### 2. Submit Test Run
```bash
sbatch run_5sample_test.sh
# Monitor: tail -f /homes/tylerdoe/slurm-<JOB_ID>.out
```

### 3. Verify Fix After Run Completes
```bash
# Check column count
head -1 /fastscratch/tylerdoe/test_5samples_v1.2mod/summary/compass_summary.tsv | tr '\t' '\n' | wc -l
# Expected: ~76 columns (not 27)

# Check metadata fields in HTML
grep "Metadata Fields Available" /fastscratch/tylerdoe/test_5samples_v1.2mod/summary/compass_summary.html -A 3
# Expected: Shows "49" or similar (not "3")

# Download and review HTML report
scp tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/test_5samples_v1.2mod/summary/compass_summary.html .
# Open in browser and verify:
# - Metadata Explorer dropdown has 40+ field options
# - Can select Platform, Model, LibraryStrategy, BioProject, etc.
# - Visualizations work for different metadata fields
```

### 4. Check MLST Debug Output (Still Pending)
```bash
# Look for debug messages in SLURM log
grep -i "searching for mlst\|found.*mlst files\|parsing.*mlst" /homes/tylerdoe/slurm-<JOB_ID>.out

# These should show:
# - "Searching for MLST files in: /fastscratch/tylerdoe/test_5samples_v1.2mod/mlst"
# - "Found 6 MLST files: [...]"
# - "Parsing SRR35618477_mlst.tsv: columns: ['FILE', 'SCHEME', 'ST', ...]"
# - "Sample SRR35618477: scheme=campylobacter, ST=10387"
```

## Questions Answered

**Q: Why was metadata working before but broke?**
A: It wasn't working - it always had this bug. The column filtering code was added early in development and never noticed because we weren't testing with real SRA metadata files.

**Q: Why did parse_metadata() look correct but still fail?**
A: parse_metadata() WAS correct! The bug was AFTER - in the column reordering step that happened right before saving the TSV.

**Q: Will this affect existing runs?**
A: No - this only affects new runs. Old runs with 27-column TSVs won't be retroactively fixed, but can be regenerated by re-running the pipeline.

## Commits This Session

### ecaf3d6 - CRITICAL FIX: Preserve all metadata columns in compass_summary.tsv
- Fixed column filtering bug in bin/generate_compass_summary.py
- Changed from `df = df[column_order]` to `df = df[column_order + other_columns]`
- Preserves all SRA metadata fields for HTML Metadata Explorer

## Next Session Goals

1. ✅ Verify metadata fix works (should see 40+ fields)
2. 🔍 Debug MLST display issue (files exist, parsing unclear)
3. 📊 Test full enhanced report functionality
4. 🚀 If all working, run full Kansas 2021-2025 analysis

## Branch Status
- **Branch**: v1.2-mod
- **Latest Commit**: ecaf3d6 (CRITICAL FIX: Preserve all metadata columns)
- **Pending**: Full pipeline test with fix

---

**Session End**: January 13, 2025 ~12:00 AM
**Status**: Critical bug fixed, ready for testing tomorrow
**Next Step**: Pull latest code and run full pipeline test

## E. coli 2020 Run - Cancelled for Testing

**Job Details:**
- **Job ID**: 5681279
- **Job Name**: compass_ecoli_2020
- **Script**: `/fastscratch/tylerdoe/COMPASS-pipeline/run_ecoli_2020_fastscratch.sh`
- **Started**: January 13, 2026 at 10:27 AM
- **Runtime when cancelled**: 1 day, 2 hours, 36 minutes
- **Progress when cancelled**: 
  - 2264 samples downloaded (9 failed)
  - 383 of 2255 samples assembled (17%)
  - 119 QUAST, 123 AMRFinder, 461 ABRicate completed
  - Still in assembly/annotation phase

**Reason for Cancellation**: 
Need to test metadata columns fix with 5-sample test run before continuing large production run.

**To Resume After Test:**
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull origin v1.2-mod  # Get latest fixes
sbatch run_ecoli_2020_fastscratch.sh  # Will use -resume to continue from sample 383
```

**Work Directory**: Will be preserved for -resume
- Location: `/fastscratch/tylerdoe/COMPASS-pipeline/work_*` (check script for exact name)
- Contains: Cached results for first 383 assembled samples
- Will NOT need to re-download or re-assemble those samples

**SLURM Logs**:
- Output: `/homes/tylerdoe/slurm-5681279.out`
- Error: `/homes/tylerdoe/slurm-5681279.err`

---

