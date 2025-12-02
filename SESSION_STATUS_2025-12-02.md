# COMPASS Pipeline v1.2-mod Session Status
## Date: December 2, 2025

---

## 🎯 Current Status Summary

### ✅ COMPLETED TODAY
1. **Fixed SPAdes assembly bug** - Removed incompatible `--careful` flag when using `--isolate` mode
2. **Created phylogeny workflow** - Added subsampling, alignment, and tree-building scripts
3. **Fixed empty metadata file** - Created script to regenerate prophage metadata from FASTA headers

### ⏳ IN PROGRESS
1. **MAFFT Alignment Running** - Stuck at step 87/199 for extended period
   - Location: `/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny/`
   - Command: `bash run_align_subsample.sh`
   - Input: 200 subsampled prophages (from 3,369 total)
   - Output will be: `subsample_aligned.fasta`

2. **Job 4332062** - Running for 1+ days on dwarf53 (phylogeny-related, check status)

### ❌ NEEDS RETRY
1. **Test Pipeline Run** - Failed due to temporary Slurm controller connection issue
   - Last job: 4386154
   - SPAdes assemblies: ✅ **WORKING NOW** (5/5 succeeded after fix)
   - DIAMOND_PROPHAGE: Failed with "Unable to contact slurm controller"
   - **Action**: Just rerun `sbatch test_v1.2mod_fastscratch_5samples.sh`

---

## 📁 Important File Locations

### On Beocat

**Pipeline Code:**
- Main repo: `/fastscratch/tylerdoe/COMPASS-pipeline` (v1.2-mod branch)
- Alternate: `~/COMPASS-pipeline`

**Results & Data:**
- Results archive: `/bulk/tylerdoe/archives/compass_kansas_results/`
- Phylogeny work: `/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny/`
  - `complete_prophages.fasta` (100MB, 3,369 sequences)
  - `prophage_metadata.tsv` (regenerated, all fields populated)
  - `subsample_prophages.fasta` (200 sequences)
  - `subsample_metadata.tsv` (200 entries)
  - `subsample_aligned.fasta` (CURRENTLY BEING CREATED - alignment running)

**Test Run Outputs:**
- Slurm logs: `/homes/tylerdoe/test_v12mod_*.out` and `*.err`
- Work directory: `/fastscratch/tylerdoe/work_v12mod_test/`
- Output directory: `/fastscratch/tylerdoe/test_v1.2mod_5samples/`

### On GitHub
- Repo: https://github.com/tdoerks/COMPASS-pipeline
- Branch: `v1.2-mod`
- Latest commits:
  - `4734960` - Fix SPAdes --careful and --isolate incompatibility
  - `ae022da` - Add script to fix empty prophage metadata file
  - `50be318` - Add phylogeny subsampling workflow scripts

---

## 🔧 Recent Fixes Applied

### 1. SPAdes Assembly Fix (CRITICAL)
**Problem:** All assemblies failing with error:
```
== Error ==  you cannot specify --mismatch-correction or --careful in isolate mode!
```

**Solution:** Removed `--careful` flag from `modules/assembly.nf`
- File: `modules/assembly.nf` lines 31-32, 41-42
- Changed: Removed `--careful \` from both paired-end and single-end SPAdes commands
- Status: ✅ FIXED - Verified working in job 4386154

**Code location:** `/fastscratch/tylerdoe/COMPASS-pipeline/modules/assembly.nf`

### 2. Empty Prophage Metadata Fix
**Problem:** `prophage_metadata.tsv` only had header (1 line, 0 prophages)

**Solution:** Created `fix_prophage_metadata.py` to regenerate from FASTA headers
- Script: `fix_prophage_metadata.py`
- Extracts: prophage_id, sample_id, length, completeness from FASTA headers
- Note: Year and organism set to "Unknown" (fine for phylogeny)
- Status: ✅ FIXED - 3,369 entries regenerated

**Usage:**
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
python3 fix_prophage_metadata.py
```

---

## 🧬 Phylogeny Workflow (NEW)

### Purpose
Build phylogenetic tree from 3,369 prophage sequences (too many for practical analysis)

### Three-Step Workflow

**Step 1: Subsample** ✅ DONE
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
bash run_subsample_phylogeny.sh
```
- Selects 200 representative prophages
- Balances across years and organisms
- Output: `subsample_prophages.fasta` (13M)

**Step 2: Align** ⏳ CURRENTLY RUNNING
```bash
bash run_align_subsample.sh
```
- Uses MAFFT (8 threads)
- Currently: STEP 87/199 (seems stuck)
- Output: `subsample_aligned.fasta`
- **Issue**: Alignment appears stalled at step 87 for extended time

**Step 3: Build Tree** ⏸️ WAITING FOR ALIGNMENT
```bash
sbatch build_phylogeny_subsample.slurm
```
- Uses IQ-TREE with 1000 bootstrap replicates
- Resources: 16 cores, 32GB RAM, 12 hours
- Output: `subsample_tree.treefile` (Newick format for iTOL)

### Script Locations
- `run_subsample_phylogeny.sh` - Subsampling wrapper
- `run_align_subsample.sh` - MAFFT alignment wrapper
- `build_phylogeny_subsample.slurm` - IQ-TREE job script
- All in: `/fastscratch/tylerdoe/COMPASS-pipeline/`

### Data Locations
All phylogeny files in: `/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny/`

---

## 🚨 Known Issues & Troubleshooting

### Issue 1: MAFFT Alignment Stuck
**Status:** Alignment at STEP 87/199 for extended period (30+ minutes no progress)

**Possible causes:**
1. Dealing with very long sequences (mean: 62kb, max: 111kb)
2. High memory usage triggering memsave mode
3. Process might be hung

**Next steps:**
1. Wait another 30-60 minutes to see if it progresses
2. If still stuck, Ctrl+C and check for partial output
3. Consider:
   - Running on a compute node with more memory (submit as Slurm job)
   - Further subsampling to 100 sequences
   - Using FastTree instead of MAFFT for initial alignment

**Alternative alignment approach:**
```bash
# If MAFFT is too slow, try submitting as a job:
cat > align_mafft.slurm << 'EOF'
#!/bin/bash
#SBATCH --job-name=mafft_align
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=6:00:00
#SBATCH --output=mafft_%j.out

cd /bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny
module load MAFFT
mafft --auto --thread 16 subsample_prophages.fasta > subsample_aligned.fasta
EOF

sbatch align_mafft.slurm
```

### Issue 2: Slurm Controller Connection Failures
**Error:** `sbatch: error: Batch job submission failed: Unable to contact slurm controller (connect failure)`

**Root cause:** Temporary Slurm system issue, NOT a pipeline bug

**Solution:** Just retry the job submission
```bash
sbatch test_v1.2mod_fastscratch_5samples.sh
```

**Note:** This error occurred AFTER SPAdes fix was verified working (5/5 assemblies succeeded)

### Issue 3: Stale File Handle Error (ORIGINAL CONCERN)
**Status:** ❓ NOT OBSERVED YET

**What we were checking for:** Errors like `Stale file handle` or `ESTALE` when accessing fastscratch

**Latest test results:** Failed before reaching stages where this typically occurs

**Next test:** Need clean run to completion to verify if stale handle issue still exists

---

## 🔄 Next Steps / Action Items

### Immediate (This Afternoon)
1. **Check MAFFT alignment status**
   - If still at step 87: Kill and rerun as Slurm job with more memory
   - If completed: Proceed to tree building

2. **Rerun pipeline test**
   ```bash
   cd /fastscratch/tylerdoe/COMPASS-pipeline
   git pull origin v1.2-mod  # Get latest fixes
   sbatch test_v1.2mod_fastscratch_5samples.sh
   ```
   - Should now complete assemblies successfully
   - Watch for any stale file handle errors in later stages

3. **Check on long-running job 4332062**
   ```bash
   squeue -u tylerdoe
   # If still running after 1+ days, check what it's doing:
   # Find the job script that created it
   ```

### Once Alignment Completes
```bash
cd /bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny

# Verify alignment file exists and is not empty
ls -lh subsample_aligned.fasta

# Build phylogenetic tree
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch build_phylogeny_subsample.slurm

# Monitor tree building (1-4 hours expected)
tail -f iqtree_subsample_*.out
```

### Once Tree Builds
```bash
# Download tree file to local computer
scp tylerdoe@beocat.cis.ksu.edu:/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny/subsample_tree.treefile .
scp tylerdoe@beocat.cis.ksu.edu:/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny/subsample_metadata.tsv .

# Visualize at https://itol.embl.de/
# Upload both files for annotated tree
```

### Verify Full Pipeline
Once test completes successfully:
- Check all stages completed
- Verify no stale file handle errors
- If clean: v1.2-mod is ready for production use
- If issues: Document and create GitHub issue

---

## 📊 Test Pipeline Configuration

**Script:** `test_v1.2mod_fastscratch_5samples.sh`

**Settings:**
- Branch: v1.2-mod
- Location: `/fastscratch/tylerdoe/COMPASS-pipeline`
- Filter: Kansas 2023 samples
- Max samples: 5 (for quick test)
- Skip BUSCO: Yes
- Output: `/fastscratch/tylerdoe/test_v1.2mod_5samples`
- Work dir: `/fastscratch/tylerdoe/work_v12mod_test`
- Resume: Yes (enabled)

**Expected runtime:** 30 minutes - 2 hours for 5 samples

**What to check:**
1. All assemblies succeed (SPAdes) ✅ VERIFIED
2. VIBRANT prophage detection completes
3. DIAMOND_PROPHAGE analysis succeeds (previously failed due to Slurm glitch)
4. PHANOTATE annotation works
5. Summary generation completes
6. **NO stale file handle errors** (this was original concern)

---

## 🌳 Git Branch Strategy

### v1.2-stable
- Last stable release
- Known to work on Beocat
- No recent changes

### v1.2-mod (CURRENT WORK BRANCH)
- Started from v1.2-stable
- Added fixes and improvements
- Recent changes:
  - SPAdes `--careful` flag removal
  - Phylogeny subsampling scripts
  - Metadata regeneration script
  - Various test scripts

**Merge to stable:** Once v1.2-mod passes full test run cleanly

---

## 💻 Commands Cheat Sheet

### Check Running Jobs
```bash
squeue -u tylerdoe
```

### Check Recent Logs
```bash
ls -lht /homes/tylerdoe/test_v12mod_*.out | head -3
tail -50 /homes/tylerdoe/test_v12mod_<JOBID>.out
tail -50 /homes/tylerdoe/test_v12mod_<JOBID>.err
```

### Pull Latest Code
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull origin v1.2-mod
```

### Check Phylogeny Files
```bash
ls -lh /bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny/
```

### Kill Stuck MAFFT Alignment
```bash
# If alignment is stuck, Ctrl+C in that terminal
# Or find and kill the process:
ps aux | grep mafft
kill <PID>
```

### Monitor Alignment (if running as job)
```bash
tail -f mafft_*.out
# Or check progress:
tail -20 mafft_*.out
```

---

## 📝 Notes for Future Work

### Potential Enhancements
1. **Phylogeny with year/organism metadata** - Need to map SRR IDs back to sample metadata
2. **Larger subsample** - If 200 sequences builds tree quickly, try 500 or 1000
3. **Full tree** - If needed, build tree from all 3,369 prophages (will take days)
4. **Protein-based phylogeny** - Use protein sequences instead of nucleotides for better resolution

### Documentation Needed
1. Update README with phylogeny workflow
2. Document SPAdes fix in CHANGELOG
3. Create troubleshooting guide for common errors

### Testing Needed
1. Full pipeline run with all samples (not just 5)
2. Verify stale file handle issue is resolved
3. Test on different data (E. coli, other organisms)

---

## 🔗 Related Files in This Session

**Created today:**
- `run_subsample_phylogeny.sh` - Subsample wrapper
- `run_align_subsample.sh` - Alignment wrapper
- `build_phylogeny_subsample.slurm` - Tree building job
- `fix_prophage_metadata.py` - Metadata regeneration script
- `check_phylogeny_status.sh` - Status checker (in /tmp, not committed)

**Modified today:**
- `modules/assembly.nf` - Removed `--careful` flag

**All changes pushed to:** https://github.com/tdoerks/COMPASS-pipeline/tree/v1.2-mod

---

## 🎓 What We Learned

1. **SPAdes 3.15.5 incompatibility** - Cannot use `--careful` with `--isolate` mode
2. **Prophage metadata extraction** - Original script failed silently, needed manual fix
3. **Large dataset phylogeny** - 3,369 sequences requires subsampling for practical analysis
4. **MAFFT challenges** - Very long sequences (50-100kb) can slow alignment significantly
5. **Slurm glitches** - "Unable to contact slurm controller" errors are transient, just retry

---

## 📞 Quick Reference

**User:** tylerdoe
**Server:** beocat.cis.ksu.edu (icr-helios login node)
**GitHub Repo:** https://github.com/tdoerks/COMPASS-pipeline
**Branch:** v1.2-mod
**Email for job notifications:** tdoerks@vet.k-state.edu

**Active terminal sessions:**
1. MAFFT alignment running (check status)
2. General commands / job monitoring

---

**Last Updated:** December 2, 2025, ~1:00 PM CST
**Session End Reason:** User picking up work on different computer this afternoon
**Resume Point:** Check alignment status, rerun pipeline test, verify SPAdes fix

---

## ✅ Success Criteria for Today

- [✅] Fixed SPAdes assembly failures
- [⏳] Complete MAFFT alignment (in progress, possibly stuck)
- [⏸️] Build phylogenetic tree (waiting for alignment)
- [🔄] Verify pipeline runs clean on 5 samples (retry needed)
- [❓] Confirm no stale file handle errors (pending full run)

**Overall Progress:** 60% complete - Main fixes done, validation pending
