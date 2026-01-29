# Session Notes - January 27, 2026

## Summary

Today's session focused on three major tasks:
1. **Interactive Accession List Generator** - Created user-friendly tool for custom NCBI sampling
2. **E. coli Monthly Sampling Run** - Launched 7,142-sample temporal study
3. **Phylogeny Trees** - Fixed timeout issues and tree visualization

---

## 1. Interactive Accession List Generator 🎯

### Problem
The COMPASS pipeline's built-in metadata filtering can't handle complex sampling strategies like "100 samples per month" or balanced temporal distributions.

### Solution
Created `generate_accession_list.py` - an interactive wizard that generates custom Python scripts to fetch SRA accessions from NCBI.

### Features
- **User-friendly prompts**: Organism, date range, sampling strategy (monthly/yearly/all)
- **Filters**: Platform (Illumina/PacBio/etc.), Library source (GENOMIC/METAGENOMIC), Geographic location
- **Auto-generates**: Python fetcher script + matching sbatch submission script
- **Smart estimation**: Calculates expected sample count and runtime

### Files Created
- `generate_accession_list.py` - Interactive generator tool
- `ACCESSION_LIST_TOOLS.md` - Comprehensive documentation with examples
- `fetch_ecoli_monthly_v2.py` - Working example (100 E. coli per month, 2020-2026)
- `run_ecoli_monthly_100_2020-2026.sh` - Submission script for the generated list

### Documentation
See `ACCESSION_LIST_TOOLS.md` for:
- When to use custom lists vs. built-in filtering
- Step-by-step guide
- Advanced examples (temporal trends, multi-organism, geographic comparisons)
- Troubleshooting tips

### Example Usage
```bash
python3 generate_accession_list.py
# Answer prompts:
# - Organism: Salmonella
# - Years: 2022-2024
# - Strategy: Monthly, 50 samples
# - Platform: Illumina
# Generates: fetch_salmonella_monthly_50_2022-2024.py + run script
```

---

## 2. E. coli Monthly 100 Sampling Run 🦠

### Goal
Study E. coli temporal evolution with balanced monthly sampling across 6 years.

### Dataset
- **Period**: January 2020 - January 2026 (73 months)
- **Strategy**: 100 random samples per month
- **Total**: 7,142 E. coli genomes
- **Filters**: Illumina platform, GENOMIC source
- **Note**: November 2020 had 0 accessions (data gap on NCBI)

### Accession List
Generated using `fetch_ecoli_monthly_v2.py`:
```bash
python3 fetch_ecoli_monthly_v2.py
# Output: sra_accessions_ecoli_monthly_100_2020-2026.txt
```

### Pipeline Run
**Job ID**: 6087505
**Script**: `run_ecoli_monthly_100_2020-2026.sh`
**Status**: Running on warlock36
**Started**: January 27, 2026 ~11:00 AM CST
**Time Limit**: 168 hours (7 days)
**Resources**: 8 CPUs, 32GB RAM

**Progress** (as of ~1 PM):
- Downloaded: 277/7,142 samples (3.9%)
- Assembly: 51 samples in progress
- Many tasks using cached results from previous runs (huge time saver!)
- 19 failed downloads (normal - some SRA accessions become unavailable)

### Output
Will be in: `/fastscratch/tylerdoe/ecoli_monthly_100_20260127/`

### Work Directory
`work_ecoli_monthly_100` - Uses `-resume` for fault tolerance

### Expected Results
- Full COMPASS analysis for all 7,142 samples
- Assembly QC (FastQC, FASTP, QUAST, BUSCO)
- AMR analysis (Abricate, AMRfinder)
- Prophage detection (VIBRANT, Phanotate, DIAMOND)
- Mobile elements (MOB-suite)
- MLST typing
- MultiQC summary report

---

## 3. Phylogeny Tree Analyses 🌳

### 3A. Kansas All-Prophage Phylogeny ✅ COMPLETED

**Job ID**: 6075471
**Status**: Completed successfully (12.5 hours)
**Output**: `/homes/tylerdoe/kansas_2021-2025_all_prophage_phylogeny_20260126/`

**Files**:
- `prophage_tree.nwk` - Original FastTree output
- `prophages_all.fasta` - All prophage sequences
- `prophages_subsampled.fasta` - Subsampled for alignment
- `prophages_aligned.fasta` - MAFFT alignment
- `prophage_metadata.tsv` - Sequence metadata

**Issue Encountered**: Invalid branch length error in iTOL
- **Cause**: Sequence IDs contain colons (e.g., `NODE_4:length_303155`), which conflict with Newick format (uses `:` for branch lengths)
- **Solution**: Created `fix_kansas_prophage_tree.sh`

**Fixed Files**:
- `prophage_tree_cleaned.nwk` - Ready for iTOL
- `prophage_metadata_cleaned.tsv` - Matching metadata with cleaned IDs

**To Download**:
```bash
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/kansas_2021-2025_all_prophage_phylogeny_20260126/prophage_tree_cleaned.nwk .
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/kansas_2021-2025_all_prophage_phylogeny_20260126/prophage_metadata_cleaned.tsv .
```

**Next Steps - iTOL Visualization** 🎨

**Goal**: Color-code tree by organism (E. coli, Salmonella, Campylobacter, etc.)

**Plan**:
1. Extract organism info from Kansas COMPASS results (MLST/typing)
2. Create iTOL annotation datasets:
   - Color strip showing organism
   - Simple labels with organism names
   - Optional clade background shading
3. Upload to iTOL for interactive visualization

**Why iTOL annotations** (not relabeling tree):
- Flexible - toggle colors/labels on/off
- No need to regenerate tree
- Can try different color schemes
- Easy to add more annotations later (AMR genes, prophage count, etc.)

**To Resume**: Need path to Kansas COMPASS results directory to extract organism typing

---

### 3B. E. coli AMR-Prophage Subsample Tree ⏱️ TIMEOUT → FIXED

**Job ID**: 6075158 (timed out)
**Script**: `run_ecoli_amr_prophage_subsample_tree.sh`
**Status**: Failed due to 24-hour timeout
**Runtime**: Exactly 24:00:30 (hit wall time)

**What it does**:
1. Subsamples AMR-carrying prophages (100 per year, 2021-2024 → ~400 total)
2. Multiple sequence alignment with MAFFT (2-5 hours)
3. Phylogenetic tree with FastTree (30-60 minutes)
4. Tree cleaning (remove colons from IDs)

**Fix Applied**: Increased time limit from 24 hours to 168 hours (7 days)

**To Restart**:
```bash
git pull  # Get updated script
sbatch run_ecoli_amr_prophage_subsample_tree.sh
```

**Expected Output**: `/homes/tylerdoe/ecoli_amr_prophage_phylogeny_YYYYMMDD/`
- `amr_prophage_subsample_tree_cleaned.nwk` - Ready for iTOL
- `amr_prophage_subsample_metadata.tsv` - Metadata
- `amr_prophages_subsample_aligned.fasta` - Alignment
- `amr_prophages_subsample.fasta` - Subsampled sequences

**Benefits of Subsampling**:
- Faster alignment (2-5 hrs vs 55-60 hrs for full dataset)
- Fits in 32GB memory (full dataset caused OOM)
- Easier tree visualization
- Representative temporal diversity preserved

**Research Questions**:
1. Do AMR-carrying prophages cluster by year?
2. Are there AMR-prophage lineages?
3. Which prophage clades carry more AMR genes?

---

## Files Modified/Created Today

### New Files
1. `generate_accession_list.py` - Interactive accession list generator
2. `ACCESSION_LIST_TOOLS.md` - Documentation
3. `fetch_ecoli_monthly_v2.py` - Example E. coli monthly sampler (fixed XML parsing)
4. `run_ecoli_monthly_100_2020-2026.sh` - Submission script for 7,142 samples
5. `fix_kansas_prophage_tree.sh` - Tree cleaning script for Kansas phylogeny
6. `sra_accessions_ecoli_monthly_100_2020-2026.txt` - 7,142 E. coli accessions

### Modified Files
1. `run_ecoli_amr_prophage_subsample_tree.sh` - Time limit: 24h → 168h
2. `fetch_ecoli_monthly.py` → `fetch_ecoli_monthly_v2.py` - Fixed CSV parsing issue (use XML instead)

---

## Current Active Jobs

| Job ID | Name | Status | Runtime | Purpose |
|--------|------|--------|---------|---------|
| 6087505 | ecoli_monthly_100 | Running | ~2 hours | Process 7,142 E. coli samples |

---

## Completed Jobs

| Job ID | Name | Status | Runtime | Output |
|--------|------|--------|---------|--------|
| 6075471 | kansas_all_prophage_phylo | ✅ Completed | 12.5 hours | Kansas prophage tree |
| 6075158 | ecoli_amr_subsample_tree | ⏱️ Timeout | 24 hours | Fixed, ready to restart |

---

## Next Session Tasks

### High Priority
1. **Restart E. coli AMR-prophage subsample tree** with 7-day limit
2. **Create iTOL annotations for Kansas tree** - color by organism
3. **Monitor E. coli monthly 100 run** - check progress, handle failures

### Medium Priority
4. Extract organism info from Kansas COMPASS results for iTOL annotations
5. Check on E. coli monthly 100 run after a few days (download MultiQC report)

### Low Priority
6. Test interactive accession generator with different organisms (Salmonella, Klebsiella)
7. Create example iTOL annotation files for documentation

---

## Key Lessons Learned

1. **CSV vs XML for NCBI**: RunInfo CSV parsing failed, XML format is more reliable
2. **Time limits for phylogeny**: 24 hours too short for MAFFT on large datasets; use 7 days
3. **Tree format issues**: Colons in sequence IDs break Newick format; clean before iTOL upload
4. **Caching is powerful**: Resume flag saved huge amounts of time (9,255 cached tasks!)
5. **Interactive tools are better**: Users prefer simple prompts over writing Python code

---

## Commands Reference

### Pull Latest Changes
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull
```

### Generate Custom Accession List
```bash
python3 generate_accession_list.py
# Follow prompts, generates both fetcher script and sbatch script
```

### Fix Tree Format
```bash
./fix_kansas_prophage_tree.sh
```

### Check Job Status
```bash
squeue -u tylerdoe
sacct -j JOBID --format=JobID,JobName,State,ExitCode,Elapsed
```

### Monitor Pipeline
```bash
tail -f /homes/tylerdoe/slurm-ecoli-monthly-100-JOBID.out
tail -f .nextflow.log
```

---

## Git Commits Today

1. `a1281b0` - Fix E. coli accession fetching script (use XML parsing)
2. `8f2350a` - Add interactive accession list generator and documentation
3. `c17e217` - Add sbatch script for E. coli monthly 100 sampling run
4. `4bc432d` - Increase time limit for AMR-prophage phylogeny to 7 days
5. `11e165c` - Add script to fix Kansas prophage tree colon issues

All commits on `v1.3-dev` branch.

---

## Notes

- The interactive accession list generator is a major improvement for reproducibility
- Users can now create complex sampling strategies without writing code
- Monthly sampling provides better temporal resolution than yearly
- Tree visualization improvements (iTOL annotations) will make organism patterns clearer
- Next session should focus on creating iTOL annotation files for Kansas tree

---

**Session End**: January 27, 2026 ~2:00 PM CST
