# Running Jobs Status - January 20, 2026

Check this file tomorrow to see what needs attention!

## Jobs Currently Running

### Job 5824288 - AMR-Prophage Phylogeny (2021-2024)
- **Status**: Running (started ~21 hours ago)
- **Expected completion**: 3-4 days from start (~Jan 23-24)
- **Progress**: Extracting 3,918 AMR-carrying prophage sequences, then MAFFT alignment
- **Resources**: 96 hours, 16 CPUs, 32GB RAM
- **Output location**: `/homes/tylerdoe/ecoli_amr_prophage_phylogeny_YYYYMMDD/`
- **What to check**:
  ```bash
  tail -50 ~/slurm-ecoli-amr-prophage-phylo-5824288.out
  ```
- **When complete**: Download tree files, visualize in iTOL, color by year

### Job 5824321 - All-Prophage Phylogeny (2021-2024)
- **Status**: Running (started ~21 hours ago)
- **Expected completion**: ~22 hours total (~Jan 21)
- **Progress**: MAFFT alignment on 500 subsampled prophages
- **Resources**: 48 hours, 16 CPUs, 32GB RAM
- **Bug fix applied**: MAFFT stderr redirect fixed
- **Output location**: `/homes/tylerdoe/ecoli_all_prophage_phylogeny_YYYYMMDD/`
- **What to check**:
  ```bash
  tail -50 ~/slurm-ecoli-all-prophage-phylo-5824321.out
  ```
- **When complete**: Provides background context for AMR-prophage tree

### Job ????? - Comprehensive AMR-Prophage Analysis
- **Status**: Unknown (was queued as Job 5824378, may have run)
- **Expected runtime**: 1-2 hours
- **What it does**: Gene frequency, drug class trends, co-occurrence, BLAST export
- **Output location**: `/homes/tylerdoe/comprehensive_amr_prophage_analysis_YYYYMMDD/`
- **What to check**:
  ```bash
  ls -lht ~/slurm-amr-prophage-comprehensive-*.out | head -3
  ls -ld ~/comprehensive_amr_prophage_analysis_*
  ```
- **When complete**: Review summary_statistics.txt, BLAST sequences_for_blast.fasta

### Job ????? - Latest 1000 Bacteria Analysis
- **Status**: Just submitted
- **Expected completion**: 5-7 days
- **What it does**: COMPASS pipeline on 1000 most recent bacterial genomes (any species)
- **Output location**: `/fastscratch/tylerdoe/latest_1000_bacteria_YYYYMMDD/`
- **What to check**:
  ```bash
  squeue -u tylerdoe | grep latest
  tail -100 ~/slurm-compass-latest-1000-*.out
  ```
- **When complete**: Check organism diversity in Data Explorer

## Recently Completed Jobs

### Job 5785740 - E. coli 2020 COMPASS Pipeline ✅
- **Status**: COMPLETED
- **Completion**: January 20, 2026
- **Runtime**: ~2 days
- **Output location**: `/fastscratch/tylerdoe/ecoli_2020_all_narms/`
- **Report**: `/fastscratch/tylerdoe/ecoli_2020_all_narms/summary/compass_summary.html`
- **Note**: Contains E. coli, Salmonella, Campylobacter (metadata filter issue - not critical)
- **Action needed**: Transfer to bulk storage
  ```bash
  rsync -avh --progress /fastscratch/tylerdoe/ecoli_2020_all_narms/ /bulk/tylerdoe/archives/ecoli_2020_all_narms/
  ```

## Commands for Tomorrow

### Check all running jobs:
```bash
squeue -u tylerdoe
```

### Check specific job progress:
```bash
# AMR-prophage phylogeny
tail -100 ~/slurm-ecoli-amr-prophage-phylo-5824288.out

# All-prophage phylogeny
tail -100 ~/slurm-ecoli-all-prophage-phylo-5824321.out

# Comprehensive analysis (if it ran)
ls -lht ~/comprehensive_amr_prophage_analysis_*/
cat ~/comprehensive_amr_prophage_analysis_*/summary_statistics.txt

# Latest 1000 bacteria
tail -100 ~/slurm-compass-latest-1000-*.out
```

### Check for newly completed jobs:
```bash
sacct -u tylerdoe --starttime=$(date -d '1 day ago' +%Y-%m-%d) --format=JobID,JobName,State,Elapsed | grep COMPLETED
```

## What to Do When Jobs Complete

### When AMR-Prophage Phylogeny (5824288) completes:
1. Check output directory exists:
   ```bash
   ls -lh ~/ecoli_amr_prophage_phylogeny_YYYYMMDD/
   ```
2. Download files:
   ```bash
   # On your local machine
   scp tylerdoe@beocat.ksu.edu:~/ecoli_amr_prophage_phylogeny_YYYYMMDD/amr_prophage_tree.nwk .
   scp tylerdoe@beocat.ksu.edu:~/ecoli_amr_prophage_phylogeny_YYYYMMDD/amr_prophage_metadata.tsv .
   ```
3. Visualize in iTOL (https://itol.embl.de/)
4. Color by year to see temporal clustering
5. Document findings and add to analysis branch

### When All-Prophage Phylogeny (5824321) completes:
1. Check if tree file exists:
   ```bash
   ls -lh ~/ecoli_all_prophage_phylogeny_YYYYMMDD/prophage_tree.nwk
   ```
2. Compare to AMR-prophage tree
3. Document whether AMR-prophages are specific lineages or distributed

### When Comprehensive Analysis completes:
1. Review summary:
   ```bash
   cat ~/comprehensive_amr_prophage_analysis_YYYYMMDD/summary_statistics.txt
   ```
2. Send BLAST sequences to collaborator:
   ```bash
   # sequences_for_blast.fasta contains 30 prophages for validation
   ```
3. Review all CSV files for publication figures:
   - gene_frequency.csv
   - drug_class_trends.csv
   - top_samples.csv
   - gene_cooccurrence.csv
   - prophage_characteristics.csv

### When Latest 1000 Bacteria completes:
1. Check organism diversity:
   ```bash
   # Open Data Explorer in browser
   firefox /fastscratch/tylerdoe/latest_1000_bacteria_YYYYMMDD/summary/compass_summary.html
   ```
2. Document which organisms worked well
3. Identify any edge cases or failures
4. Compare AMR patterns across diverse species

## Data Management

### Transfers Needed:
- [x] Transfer E. coli 2020 to bulk storage (in progress)
- [ ] Clean up fastscratch after confirming bulk transfer
- [ ] Archive phylogeny results to analysis branch when complete

### Bulk Storage Status:
```
/bulk/tylerdoe/archives/
├── kansas_2021_ecoli/
├── kansas_2022_ecoli/
├── results_ecoli_2023/
├── results_ecoli_all_2024/
└── ecoli_2020_all_narms/  (transferring)
```

## Key Findings So Far

### E. coli Prophage-AMR (2021-2024)
- **Total**: 396 AMR genes in prophages
- **Validation**: PASSED ✅ (2.73% in prophages, 84% mobile genes)
- **Years**: 2021 (74), 2022 (108), 2023 (94), 2024 (120)
- **Top drug classes**: Trimethoprim (66%), Aminoglycosides (18%), Sulfonamides (7%)

### Publication Status:
- ✅ Statistical validation complete
- ✅ Method 3 (gold standard) for all years
- 🔄 Phylogenetic analyses running
- 🔄 Comprehensive analysis running/pending
- 📋 Still needed: BLAST validation, literature comparison, figures

## Notes

- **Bug found**: E. coli 2020 run pulled all NARMS organisms (E. coli, Salmonella, Campylobacter) due to default metadata filter. Not critical for analysis, just note the diversity.
- **Latest 1000 bacteria**: Real stress test of pipeline on maximum diversity
- **Phylogenies**: Using 96h time limit after first jobs timed out at 24h
- **MAFFT fix**: Fixed stderr redirect that was corrupting alignment files

## Next Session Checklist

- [ ] Check if phylogenies completed
- [ ] Review comprehensive analysis results
- [ ] Check organism diversity in latest 1000 bacteria run
- [ ] Verify E. coli 2020 transfer to bulk completed
- [ ] Download phylogeny tree files if ready
- [ ] Send BLAST sequences to collaborator
- [ ] Start creating publication figures from comprehensive analysis CSVs

---

**Last updated**: January 20, 2026, 10:00 PM CST
**Branch**: analysis
**Next check**: January 21, 2026
