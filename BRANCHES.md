# Branch Guide

## Active Branches

### `v1.0-stable` - **PRODUCTION/STABLE** 🟢
- **Status**: Working, tested version
- **Use for**: Production runs, generating results for analysis
- **Last tested**: October 2025 with Kansas 2023 samples (5 samples)
- **Features**:
  - ✅ Assembly (SPAdes)
  - ✅ AMR detection (AMRFinder+)
  - ✅ Phage detection (VIBRANT)
  - ✅ Phage identification (DIAMOND prophage)
  - ✅ MLST typing
  - ✅ SISTR serotyping
  - ✅ ABRicate
  - ✅ MOB-suite plasmid detection
  - ✅ Enhanced HTML report (v3) with:
    - Cross-reference table (AMR + Phage per sample)
    - Pie charts (AMR classes, Phage IDs)
    - DIAMOND phage identifications
    - All data embedded

**Known Issues:**
- CheckV disabled (2/5 samples completed - database path issues)
- Prophage database uses bacterial genome accessions, not phage names

**To use this branch:**
```bash
git checkout v1.0-stable
git pull origin v1.0-stable

# Run pipeline
sbatch run_playground_test.sh

# Generate report
./bin/generate_report_v3.py results_playground_test -o compass_report_v3.html
```

---

### `claude-dev-playground` - **DEVELOPMENT** 🔧
- **Status**: Active development
- **Use for**: Testing new features, improvements
- **Don't use for**: Production analyses (may be unstable)

**Current work:**
- Investigating CheckV failures
- Improving prophage database annotations
- Adding additional analyses

**To switch between branches:**
```bash
# Switch to stable for production
git checkout v1.0-stable

# Switch to playground for development
git checkout claude-dev-playground
```

---

### `main` - **ORIGINAL** 📦
- **Status**: Original code before Claude improvements
- **Use for**: Reference only
- **Notable missing features**:
  - No channel reusability fix
  - Missing MLST, SISTR, ABRicate, MOB-suite
  - No enhanced reports

---

## Workflow Recommendations

### For Production Data Collection:
1. Use `v1.0-stable` branch
2. Run with appropriate sample filters
3. Generate reports with `bin/generate_report_v3.py`
4. Results are reliable and reproducible

### For Testing New Features:
1. Use `claude-dev-playground` branch
2. Test with small datasets (--max_samples 5)
3. Don't rely on results for publications yet

### For Large Production Runs:
```bash
# On Beocat
cd /homes/tylerdoe/pipelines/compass-pipeline
git checkout v1.0-stable
git pull origin v1.0-stable

# Edit run script for your parameters
nano run_kansas_2025.sh

# Submit
sbatch run_kansas_2025.sh
```

---

## Version History

### v1.0-stable (October 2025)
- Fixed Nextflow channel consumption bug (MLST, SISTR, ABRicate, MOB-suite now work)
- Fixed SLURM memory allocation (8GB for Nextflow driver)
- Added enhanced reporting with cross-reference analysis
- Added DIAMOND phage identification to reports
- Tested with Kansas 2023 samples (5/5 successful)

---

## Questions?

- **Which branch should I use?** → `v1.0-stable` for real work
- **Can I switch branches?** → Yes! Just commit/stash changes first
- **Will my results directory conflict?** → No, use different `--outdir` names per branch
- **Can I merge playground back to stable?** → Yes, once features are tested

---

## Quick Commands

```bash
# See current branch
git branch

# Switch to stable
git checkout v1.0-stable

# Switch to playground
git checkout claude-dev-playground

# Update current branch
git pull origin $(git branch --show-current)

# See what changed between branches
git diff v1.0-stable..claude-dev-playground
```
