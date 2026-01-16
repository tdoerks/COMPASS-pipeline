# Session Notes - January 16, 2026

## Executive Summary

Tonight we launched **THREE major analyses** on the Kansas 2021-2025 NARMS dataset:

1. **Prophage Phylogeny** - Build phylogenetic tree of all prophages
2. **COMPASS Summary Report** - Fixed 3 bugs and regenerating with all fixes
3. **Prophage-AMR Analysis** - Compare 3 methods to find AMR genes in prophages

All three are running in parallel and are independent of each other.

---

## 1. PROPHAGE PHYLOGENY ANALYSIS

### Status: ✅ Submitted to SLURM

### What It Does
Builds a maximum-likelihood phylogenetic tree of ALL prophage sequences identified by VIBRANT across the entire dataset.

**Workflow**:
1. Extract all prophage sequences from VIBRANT output (`*_phages.fna`)
2. Subsample to 500 sequences if dataset too large
3. Align with MAFFT (multi-threaded)
4. Build tree with IQ-TREE (ModelFinder + 1000 bootstraps)
5. Generate visualization guide

### Script Created
- **File**: `run_prophage_phylogeny_complete.sh`
- **Type**: All-in-one SLURM script
- **Resources**: 16 CPUs, 32GB RAM, 48 hour time limit
- **Status**: Committed to git (commit `1e6916e`)

### How to Submit
```bash
screen -S phylo
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull origin v1.2-mod
sbatch run_prophage_phylogeny_complete.sh
# Ctrl-A + D to detach
```

### Output Location
```
/homes/tylerdoe/prophage_phylogeny_20260116/
├── prophages_all.fasta              # All prophage sequences
├── prophages_aligned.fasta          # MAFFT alignment
├── prophage_tree.treefile           # Best ML tree ⭐
├── prophage_tree.contree            # Consensus tree with bootstrap
├── prophage_tree.iqtree             # Full report
├── prophage_metadata.tsv            # Sample metadata
└── VISUALIZATION_GUIDE.md           # How to visualize
```

### Expected Runtime
- **Extraction**: 1-5 minutes
- **Alignment**: 10-60 minutes (depends on sequence count)
- **Tree building**: 30 minutes - 3 hours
- **Total**: ~1-4 hours

### What to Do with Results
1. Download tree: `scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_phylogeny_*/prophage_tree.treefile .`
2. Visualize at https://itol.embl.de/ (upload tree file)
3. Or use FigTree desktop app
4. Look for temporal/geographic/host clustering patterns
5. Check visualization guide for interpretation tips

### Key Questions to Answer
- Do prophages cluster by year (temporal evolution)?
- Do prophages cluster by bacterial host species?
- Are there distinct prophage clades?
- Do prophages carrying AMR genes cluster together?

---

## 2. COMPASS SUMMARY REPORT

### Status: 🔄 Regenerating with 3 bug fixes

### What We Fixed Tonight

#### Fix 1: QC Tab Position
**Problem**: Quality Control tab was 7th in tab order (buried)
**Solution**: Moved to 2nd position (right after Overview)
**Why**: QC metrics are critical, should be easily accessible

**New tab order**:
```
Overview → Quality Control → AMR Analysis → Plasmid → Prophage → Metadata → Strain Typing → Data Quality
```

#### Fix 2: Metadata Explorer Dropdown
**Problem**: Only showing 3 fields (bases, spots, Year) instead of ~15-18
**Root cause**: Case-sensitive column name mismatch
- CSV has `organism` (lowercase) but whitelist had `Organism`
- CSV has `Year` (capital Y) but whitelist had `year`

**Solution**: Fixed whitelist to match exact CSV column names:
```python
metadata_whitelist = {
    'organism',  # CHANGED from 'Organism'
    'Year',      # CHANGED from 'year'
    'Platform', 'Model', 'LibraryStrategy',
    'source_type', 'isolation_source', 'host',
    'geo_loc_name', 'ScientificName',
    'Run', 'BioSample', 'BioProject', 'SampleName',
    # ... more fields
}
```

#### Fix 3: Strain Typing Tab Empty
**Problem**: No MLST data showing despite 825 MLST files existing
**Root cause**: MLST files have NO HEADER ROW
- Script tried to access `df['SCHEME']` and `df['ST']` columns that don't exist
- MLST format: `FILE\tSCHEME\tST\tgene1\tgene2...` (data only, no header)

**Solution**: Read MLST files with `header=None` and use column positions:
```python
df = pd.read_csv(mlst_file, sep='\t', header=None)
scheme = str(df.iloc[0][1])  # Position 1 = SCHEME
st = str(df.iloc[0][2])      # Position 2 = ST
```

---

### ADDITIONAL ISSUES DISCOVERED

#### Issue 4: Metadata Dropdown Still Only 4 Fields
**Problem**: After first regeneration, dropdown still showed only 4 fields (bases, organism, spots, spots_with_mates)
**Root cause**: Ran only `generate_compass_summary.py` without `recreate_filtered_metadata.py` first!

The pipeline does a **2-step process**:
1. `recreate_filtered_metadata.py` - Scans result directories (quast, busco, mlst, etc.), finds analyzed samples, loads original metadata from `metadata/*.csv`, creates `filtered_samples/filtered_samples.csv`
2. `generate_compass_summary.py --metadata filtered_samples/filtered_samples.csv` - Uses that to add ALL SRA fields

**Solution**: Created wrapper script `regenerate_compass_report.sh` that does both steps (commit `5d699c6`)

#### Issue 5: BUSCO Data Missing from QC Tab
**Status**: May be expected - Kansas 2021-2025 dataset may not have BUSCO results

**Investigation**:
- Script looks for `busco/*/short_summary.*.txt` files
- Pipeline config has `skip_busco = false` by default
- BUT dataset may have been run with BUSCO skipped or BUSCO failed

**Resolution**:
- If BUSCO directory exists with results → Script will find them automatically
- If BUSCO was skipped → QC tab will only show QUAST metrics (N50, contigs, etc.)
- This is expected behavior - not all datasets have BUSCO data
- Original pipeline report likely also didn't have BUSCO for this dataset

### Files Modified
- **Script**: `bin/generate_compass_summary.py`
- **Commit**: `65bd92d` - "Fix COMPASS report: move QC tab, fix metadata dropdown, fix MLST parsing"
- **Status**: Committed and pushed to git

### How to Regenerate Report (CORRECTED)

**IMPORTANT**: The pipeline uses a 2-step process:
1. **Step 1**: `recreate_filtered_metadata.py` - Rebuilds filtered_samples.csv from analyzed samples
2. **Step 2**: `generate_compass_summary.py` - Generates report WITH full SRA metadata

**Use the wrapper script** (does both steps automatically):
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull origin v1.2-mod

# Proper way (same as pipeline does)
./regenerate_compass_report.sh \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
    compass_summary.html

# Output: compass_summary.html (in current directory)
```

**What was wrong before**: You ran only step 2 without step 1, so it didn't have the filtered_samples.csv with all SRA metadata fields!

### What to Check When Report Finishes
1. ✅ QC tab is now 2nd (after Overview)
2. ✅ Metadata dropdown shows ~15-18 fields (organism, Platform, BioProject, etc.)
3. ✅ Strain Typing tab shows MLST schemes and STs for all 825 samples
4. ✅ Interactive charts still work properly

### Current Status
**Running in separate terminal session** (user didn't want to interrupt it)

Last seen output:
```
Parsing MLST results...
  Found 825 MLST files
  Samples with MLST: ['SRR17839118', 'SRR22741510', ...]
  Schemes found: {'ecoli_achtman_4', 'senterica_achtman_2', 'campylobacter'}
  STs found: {'21', '770', '1844', ...}

Parsing SISTR serovar predictions...
Parsing AMRFinder results...
Parsing MOB-suite plasmid results...
```

Should finish in a few minutes (just parsing CSV files at this point).

---

## 3. PROPHAGE-AMR ANALYSIS

### Status: ✅ Running on SLURM (Job 5753576)

### What It Does
Runs **THREE complementary methods** to definitively answer:
**"Do prophages carry AMR genes in the Kansas 2021-2025 dataset?"**

### Three Methods Explained

#### Method 1: Coordinate-Based (FAST - seconds)
**Script**: `bin/analyze_true_amr_prophage_colocation.py`

**How it works**:
1. Parse AMR gene coordinates from AMRFinderPlus (contig, start, end)
2. Parse prophage boundaries from VIBRANT (contig, start, end)
3. Check if AMR coordinates fall inside prophage boundaries

**Pros**: Very fast, uses existing results
**Cons**: Requires exact coordinate matching

**Output**:
- `method1_coordinate_based.csv`
- `method1_coordinate_based.html` (interactive report)

---

#### Method 2: Annotation Search (FAST - seconds)
**Script**: `bin/search_amr_in_vibrant_annotations.py`

**How it works**:
1. Get AMR gene names from AMRFinderPlus (e.g., "tetA", "blaCTX-M")
2. Search VIBRANT annotation files for those gene names
3. If found → gene is in prophage

**Expected result**: Typically finds 0 matches
**Why**: VIBRANT uses viral databases (VOG, KEGG) not AMR-specific gene names

**Output**: `method2_annotation_search.csv`

---

#### Method 3: Direct AMRFinder Scan (SLOW - hours) ⭐ **MOST DEFINITIVE**
**Script**: `bin/run_amrfinder_on_prophages.py`

**How it works**:
1. Extract prophage DNA sequences from VIBRANT (`*_phages.fna`)
2. Run AMRFinderPlus directly on those sequences
3. Report which AMR genes detected

**Pros**: Most direct, no coordinate/annotation issues, clear biological answer
**Cons**: Slow (~1-2 min per sample)

**Container fix applied**:
- Uses Apptainer with `docker://` prefix
- Auto-detects AMRFinder database at `/homes/tylerdoe/databases/amrfinder_db`

**Test result** (sample SRR13928113): **0 AMR genes in prophages** ✅

**Output**: `method3_direct_scan.csv`

---

### Master Script
**File**: `run_complete_prophage_amr_analysis.sh`

Runs all 3 methods sequentially on the full dataset and generates a comparison report.

**Resources**: 4 CPUs, 16GB RAM, 48 hour time limit

**How to submit**:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch run_complete_prophage_amr_analysis.sh
```

### Output Location
```
/homes/tylerdoe/prophage_amr_analysis_20260116/
├── method1_coordinate_based.csv
├── method1_coordinate_based.html        # Interactive HTML report
├── method2_annotation_search.csv
├── method2_annotation_search.log
├── method3_direct_scan.csv             # Most important!
├── method3_direct_scan.log
└── analysis_comparison_report.txt      # Comparison of all 3 methods
```

### Expected Runtime
- **Method 1**: ~10 seconds
- **Method 2**: ~10 seconds
- **Method 3**: ~24-48 hours (1-2 min × ~825 samples)
- **Total**: ~1-2 days

### Interpreting Results

#### Scenario A: 0 AMR genes in prophages
**Meaning**: AMR genes are chromosomal, not prophage-mediated
**Implication**: Prophage transduction is NOT a major mechanism for AMR spread
**Biological value**: Still a scientifically valuable finding!

#### Scenario B: AMR genes found in prophages
**Meaning**: Prophages DO carry resistance genes
**Implication**: Prophage-mediated transduction may contribute to AMR spread
**Next steps**:
- Identify which AMR genes are most common
- Analyze temporal trends (increasing over time?)
- Examine geographic patterns
- Consider drug classes affected

### Current Status
**Submitted to SLURM** - Check with:
```bash
squeue -u tylerdoe
sacct -j 5753576
```

Monitor progress by checking the output file:
```bash
tail -f /homes/tylerdoe/slurm-prophage-amr-5753576.out
```

---

## Git Status

### Branch: `v1.2-mod`

### Recent Commits (Tonight)
1. `1e6916e` - Add all-in-one prophage phylogeny analysis script
2. `65bd92d` - Fix COMPASS report: move QC tab, fix metadata dropdown, fix MLST parsing
3. `b84d487` - Add comprehensive session notes for January 16, 2026
4. `5d699c6` - Add wrapper script for proper COMPASS report regeneration

### Files Added/Modified Tonight
- ✅ `run_prophage_phylogeny_complete.sh` (NEW)
- ✅ `regenerate_compass_report.sh` (NEW - wrapper script)
- ✅ `run_complete_prophage_amr_analysis.sh` (already existed)
- ✅ `bin/generate_compass_summary.py` (MODIFIED - 3 bug fixes)
- ✅ `bin/run_amrfinder_on_prophages.py` (MODIFIED - container fix from previous session)
- ✅ `SESSION_NOTES_2026-01-16.md` (NEW)

### All Changes Committed and Pushed
```bash
git status
# On branch v1.2-mod
# Your branch is up to date with 'origin/v1.2-mod'.
# nothing to commit, working tree clean
```

---

## Jobs Currently Running

### Check Job Status
```bash
squeue -u tylerdoe
```

**Expected jobs**:
1. **Job 5753576**: Prophage-AMR analysis (3 methods)
2. **New job**: Prophage phylogeny (if submitted)

### Monitor Jobs
```bash
# Watch job queue
watch -n 30 squeue -u tylerdoe

# Check job details
sacct -j <JOB_ID> --format=JobID,JobName,State,Elapsed,MaxRSS

# View output logs
tail -f /homes/tylerdoe/slurm-prophage-amr-5753576.out
tail -f /homes/tylerdoe/slurm-prophage-phylo-*.out
```

### Screen Sessions
If you started screen sessions:
```bash
# List screens
screen -ls

# Reattach to phylo screen
screen -r phylo

# Detach: Ctrl-A then D
```

---

## What to Do When Jobs Finish

### 1. Prophage Phylogeny ✅
```bash
cd /homes/tylerdoe/prophage_phylogeny_20260116/

# Check output files
ls -lh

# Read the guide
cat VISUALIZATION_GUIDE.md

# Download tree to your local machine
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_phylogeny_*/prophage_tree.treefile .

# Visualize at https://itol.embl.de/
# Upload prophage_tree.treefile
```

### 2. COMPASS Summary Report ✅
```bash
# Find the report
ls -lh ~/compass_summary_report_kansas_2021-2025_all_narms_v1.2mod.html

# Download to local machine
scp tylerdoe@beocat.ksu.edu:~/compass_summary_report_*.html .

# Open in browser
# Check:
# - QC tab is 2nd position
# - Metadata dropdown has ~15 fields
# - Strain Typing tab shows MLST data
```

### 3. Prophage-AMR Analysis ✅
```bash
cd /homes/tylerdoe/prophage_amr_analysis_20260116/

# Read the comparison report
cat analysis_comparison_report.txt

# Check key result from Method 3 (most important)
head -20 method3_direct_scan.csv

# View interactive HTML report from Method 1
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_amr_analysis_*/method1_coordinate_based.html .
```

**Key question to answer**: Did Method 3 find any AMR genes in prophages?

---

## Key Files and Paths Reference

### Input Data
- **Results directory**: `/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod/`
- **AMRFinder results**: `amrfinder/*_amr.tsv`
- **VIBRANT prophages**: `vibrant/*_phages.fna`
- **MLST results**: `mlst/*_mlst.tsv` (825 files)
- **SISTR results**: `sistr/*_sistr.tsv` (148 files)

### Output Directories
- **Phylogeny**: `/homes/tylerdoe/prophage_phylogeny_20260116/`
- **AMR analysis**: `/homes/tylerdoe/prophage_amr_analysis_20260116/`
- **COMPASS report**: `~/compass_summary_report_kansas_2021-2025_all_narms_v1.2mod.html`

### Scripts
- **Phylogeny**: `run_prophage_phylogeny_complete.sh`
- **AMR analysis**: `run_complete_prophage_amr_analysis.sh`
- **Report generator**: `bin/generate_compass_summary.py`

### SLURM Logs
- **AMR analysis**: `/homes/tylerdoe/slurm-prophage-amr-5753576.out`
- **Phylogeny**: `/homes/tylerdoe/slurm-prophage-phylo-*.out`

---

## Timeline Summary

**Evening session: January 16, 2026**

1. **Fixed COMPASS report bugs** (3 issues)
   - Moved QC tab to 2nd position
   - Fixed metadata dropdown (case-sensitive column names)
   - Fixed MLST parsing (no header row issue)

2. **Created prophage phylogeny script**
   - All-in-one SLURM script
   - Combines extraction, alignment, tree building
   - Generates visualization guide

3. **Submitted prophage-AMR analysis**
   - Runs all 3 methods to find AMR in prophages
   - Most important: Method 3 (direct AMRFinder scan)
   - Expected runtime: 1-2 days

4. **Started COMPASS report regeneration**
   - Running in separate terminal (didn't want to interrupt)
   - Should finish soon (just parsing CSV files)

---

## Next Session To-Do

### When Jobs Finish
- [ ] Download prophage phylogenetic tree
- [ ] Visualize tree with iTOL (https://itol.embl.de/)
- [ ] Review prophage-AMR comparison report
- [ ] Check if Method 3 found any AMR genes in prophages
- [ ] Download updated COMPASS report
- [ ] Verify all 3 bug fixes worked correctly

### Analysis Questions to Answer
1. **Phylogeny**: Do prophages cluster by year/host/geography?
2. **AMR**: Are AMR genes present in prophage DNA? (Method 3 result)
3. **Comparison**: Do all 3 AMR detection methods agree?

### Potential Follow-Up Analyses
- If AMR genes found in prophages → Identify which genes, temporal trends
- If no AMR in prophages → Confirmed negative result (still publishable!)
- Cross-reference phylogeny with AMR results (do AMR-carrying prophages cluster?)

---

## Important Notes

### Container Fix (From Previous Session)
The `run_amrfinder_on_prophages.py` script now:
- Uses `docker://` prefix for Apptainer container
- Auto-detects AMRFinder database at `/homes/tylerdoe/databases/amrfinder_db`
- Properly mounts volumes for input/output

**Test confirmed**: Script works on HPC without direct AMRFinder install ✅

### MLST File Format
MLST files have **NO HEADER ROW**:
```
FILE                            SCHEME              ST    gene1    gene2...
SRR13928113_contigs.fasta      ecoli_achtman_4     355   adk(36)  fumC(24)...
```

Must use `pd.read_csv(..., header=None)` and column positions!

### Case-Sensitive Column Names
When whitelisting metadata fields, **exact case matters**:
- CSV: `organism` → Whitelist: `organism` ✅
- CSV: `Year` → Whitelist: `Year` ✅
- Mismatch = field won't show in dropdown ❌

---

## System Info

- **HPC**: Beocat (Kansas State University)
- **Working directory**: `/fastscratch/tylerdoe/COMPASS-pipeline`
- **Results directory**: `/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod`
- **Container runtime**: Apptainer (system-wide at `/usr/bin/apptainer`)
- **Git branch**: `v1.2-mod`

---

## Quick Command Reference

### Check job status
```bash
squeue -u tylerdoe
sacct -j <JOB_ID>
```

### Monitor logs
```bash
tail -f /homes/tylerdoe/slurm-*.out
```

### Screen management
```bash
screen -ls                    # List sessions
screen -r <name>              # Reattach
# Ctrl-A + D to detach
```

### Download results
```bash
# Phylogeny tree
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_phylogeny_*/prophage_tree.treefile .

# COMPASS report
scp tylerdoe@beocat.ksu.edu:~/compass_summary_report_*.html .

# AMR analysis
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_amr_analysis_*/analysis_comparison_report.txt .
```

---

**Session End Time**: January 16, 2026 (evening)
**Status**: ✅ All 3 analyses running/completed
**Ready to Resume**: Yes - just check job status and download results when done

**Last Updated**: 2026-01-16
**Next Session**: Review results, download files, interpret findings
