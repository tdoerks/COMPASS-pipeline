# Pre-Launch Checklist

**Target**: Production-ready release for publication

---

## 1. Documentation & Session Notes ✅

- [x] Document current session work
- [ ] Create comprehensive README for main branch
- [ ] Document all analysis scripts with usage examples
- [ ] Write pipeline usage guide for collaborators

**Files to update:**
- `README.md` - Main pipeline documentation
- `ANALYSIS_GUIDE.md` - How to use analysis scripts
- Session notes current and archived

---

## 2. Branch Management & Cleanup

### Active Branches
- `main` - Production stable
- `v1.3-dev` - Current development (needs testing before merge)

### Tasks
- [ ] List all branches: `git branch -a`
- [ ] Identify stale branches (no commits in >30 days)
- [ ] Delete merged/abandoned branches locally
- [ ] Delete merged/abandoned branches on remote
- [ ] Test v1.3-dev thoroughly
- [ ] Merge v1.3-dev → main when ready
- [ ] Tag release version (e.g., `v1.3.0`)

**Critical fixes in v1.3-dev to merge:**
- ✅ Singularity UID resolution error
- ✅ Organism diversity in max_samples filtering
- ✅ Kansas phylogeny bash quoting error

**Commands:**
```bash
# List all branches
git branch -a

# List branches with last commit date
git for-each-ref --sort=-committerdate refs/heads/ --format='%(refname:short) %(committerdate:short)'

# Delete local branch
git branch -d <branch-name>

# Delete remote branch
git push origin --delete <branch-name>
```

---

## 3. Test Main Branch

### Test Datasets
- [ ] E. coli small test (10 samples)
- [ ] Multi-organism test (Campy, Salmonella, E. coli)
- [ ] Kansas dataset smoke test
- [ ] Verify Data Explorer functionality
- [ ] Verify all output files generated correctly

### Test Checklist
- [ ] Pipeline completes without errors
- [ ] Summary report generated (HTML + TSV)
- [ ] Data Explorer interactive
- [ ] MLST data present
- [ ] AMR data present
- [ ] BUSCO data present
- [ ] QC metrics present
- [ ] Prophage data present
- [ ] All tabs functional in Data Explorer

**Test command:**
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git checkout main
git pull origin main

# Run small test
sbatch test_compass_summary.sh
```

---

## 4. Analysis Results Assembly

### E. coli AMR-Prophage Analysis

**Completed (2021-2024):**
- [x] AMR analysis: `/homes/tylerdoe/comprehensive_amr_prophage_analysis_20260120/`
  - 396 AMR genes in prophages
  - Gene frequency by year
  - Drug class trends
  - Top samples
  - Gene co-occurrence
  - BLAST validation sequences (30 samples)
  - Statistical validation PASSED

- [x] AMR-prophage phylogeny: `/homes/tylerdoe/ecoli_amr_prophage_phylogeny_20260120/`
  - Tree file: `amr_prophage_tree.nwk`
  - 3,918 AMR-carrying prophage sequences
  - Metadata: `amr_prophage_metadata.tsv`

- [x] All-prophage phylogeny: `/homes/tylerdoe/ecoli_all_prophage_phylogeny_20260117/`
  - Tree file: `prophage_tree.nwk`
  - 500 subsampled prophages
  - Metadata: `prophage_metadata.tsv`

**In Progress (2020-2024):**
- [ ] Job 5986450 - Complete 2020-2024 analysis
  - Expected: ~480-520 AMR genes (5 years)
  - Runtime: 30-40 hours total
  - Check status: `squeue -j 5986450`

**Kansas 2021-2025 (In Progress):**
- [ ] Job 5988834 - Kansas AMR analysis (3 organisms)
- [ ] Job 5988832 - Kansas all-prophage phylogeny
- [ ] Job 5988833 - Kansas AMR-prophage phylogeny

### Tasks for Analysis Assembly
- [ ] Download all phylogenetic trees locally
- [ ] Visualize trees in iTOL (https://itol.embl.de/)
- [ ] Create publication-quality tree figures
- [ ] Compile summary statistics table
- [ ] Create supplementary data files
- [ ] Generate comparison plots (2021-2024 vs Kansas)

**Download commands:**
```bash
# E. coli phylogenies
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/ecoli_amr_prophage_phylogeny_20260120/amr_prophage_tree.nwk .
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/ecoli_amr_prophage_phylogeny_20260120/amr_prophage_metadata.tsv .
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/ecoli_all_prophage_phylogeny_20260117/prophage_tree.nwk ./all_prophage_tree.nwk

# AMR analysis results
scp -r tylerdoe@beocat.ksu.edu:/homes/tylerdoe/comprehensive_amr_prophage_analysis_20260120/ ./ecoli_2021-2024_amr_analysis/

# When complete:
scp -r tylerdoe@beocat.ksu.edu:/homes/tylerdoe/complete_amr_prophage_analysis_2020-2024_*/comprehensive/ ./ecoli_2020-2024_amr_analysis/
```

---

## 5. Zenodo Archive Preparation

### Repository Archive
- [ ] Create clean release branch
- [ ] Remove unnecessary session notes/temporary files
- [ ] Verify all scripts have proper headers and documentation
- [ ] Create `CITATION.cff` file
- [ ] Create `codemeta.json` file
- [ ] Update LICENSE file
- [ ] Create DOI-ready README

### Data Archive (Separate from code)
- [ ] E. coli 2021-2024 complete results
- [ ] E. coli 2020-2024 complete results (when Job 5986450 completes)
- [ ] Kansas 2021-2025 results (when jobs complete)
- [ ] Phylogenetic trees (all)
- [ ] AMR analysis summaries
- [ ] BLAST validation sequences

### Zenodo Upload Structure
```
COMPASS-Pipeline-v1.3/
├── code/
│   ├── main.nf
│   ├── modules/
│   ├── bin/
│   ├── templates/
│   └── README.md
├── analysis-scripts/
│   ├── AMR-prophage/
│   ├── phylogeny/
│   └── README.md
├── example-data/
│   └── small-test-dataset/
└── documentation/
    ├── USAGE.md
    ├── ANALYSIS_GUIDE.md
    └── TROUBLESHOOTING.md

COMPASS-Data-Publication/
├── ecoli-2020-2024/
│   ├── amr-analysis/
│   ├── phylogenies/
│   └── README.md
├── kansas-2021-2025/
│   ├── amr-analysis/
│   ├── phylogenies/
│   └── README.md
└── metadata/
    └── sample-information.tsv
```

### Zenodo Checklist
- [ ] Create Zenodo account/login
- [ ] Reserve DOI for code repository
- [ ] Reserve DOI for data archive
- [ ] Prepare metadata (title, authors, description, keywords)
- [ ] Upload code archive
- [ ] Upload data archive
- [ ] Link code DOI to data DOI
- [ ] Make both public
- [ ] Update README with DOI badges

**Metadata Template:**
```yaml
Title: COMPASS Pipeline v1.3 - Comprehensive Bacterial Genomics Analysis
Authors:
  - Tyler Doerksen (ORCID: ?)
  - [Add collaborators]
Description: |
  Nextflow pipeline for comprehensive bacterial genomics analysis including
  assembly, quality control, MLST typing, AMR detection, prophage prediction,
  and phylogenetic analysis. Designed for NARMS surveillance data.
Keywords:
  - Bacterial genomics
  - Nextflow
  - AMR surveillance
  - Prophage analysis
  - NARMS
  - E. coli
  - Salmonella
  - Campylobacter
License: MIT
Related Identifiers:
  - DOI: [Data archive DOI]
  - URL: https://github.com/tdoerks/COMPASS-pipeline
```

---

## 6. Static Publication Website

### GitHub Pages Setup
- [ ] Create `gh-pages` branch
- [ ] Set up static site generator (Jekyll or simple HTML)
- [ ] Create landing page with:
  - Pipeline overview
  - Quick start guide
  - Analysis results summary
  - Download links
  - Citation information
  - DOI badges

### Website Content
- [ ] Pipeline description
- [ ] Interactive Data Explorer demos
- [ ] Example outputs
- [ ] Usage documentation
- [ ] Publication links
- [ ] Contact information

**Commands:**
```bash
# Create gh-pages branch
git checkout --orphan gh-pages
git rm -rf .

# Add website files
# ...

git add .
git commit -m "Initial GitHub Pages site"
git push origin gh-pages

# Enable GitHub Pages in repo settings
```

---

## 7. Pre-Publication Verification

### Code Quality
- [ ] All scripts have proper error handling
- [ ] All scripts have usage examples
- [ ] No hardcoded paths (use parameters)
- [ ] Consistent coding style
- [ ] All TODOs resolved or documented

### Documentation Quality
- [ ] README is comprehensive
- [ ] Installation instructions tested
- [ ] Usage examples tested
- [ ] Troubleshooting guide complete
- [ ] All parameters documented

### Data Quality
- [ ] All analysis results validated
- [ ] Statistical tests passed
- [ ] Phylogenies look correct
- [ ] No obvious errors in outputs
- [ ] Sample metadata accurate

### Legal/Compliance
- [ ] License file present and correct
- [ ] No proprietary data included
- [ ] All dependencies properly cited
- [ ] Acknowledgments complete
- [ ] Funding information included

---

## Timeline Estimate

**Week 1: Code & Documentation**
- Clean up branches (1 day)
- Test main branch (2 days)
- Update documentation (2 days)

**Week 2: Analysis Assembly**
- Wait for running jobs to complete
- Download and organize results (1 day)
- Create visualizations (2 days)
- Statistical validation (1 day)

**Week 3: Archive & Publication**
- Prepare Zenodo archives (2 days)
- Upload and verify (1 day)
- Create static website (2 days)

**Week 4: Final Review**
- Peer review of documentation
- Test all download links
- Verify all DOIs work
- Final publication

---

## Critical Running Jobs Status

**As of Jan 23, 2026:**

| Job ID  | Name | Status | Expected Completion | Notes |
|---------|------|--------|---------------------|-------|
| 5986450 | E. coli 2020-2024 complete | Running 7+ hrs | ~30-40 hrs total | Critical for publication |
| 5988834 | Kansas AMR analysis | Running | 6-8 hrs | Multi-organism |
| 5988832 | Kansas all-prophage phylo | ? | ~22 hrs | Need to check status |
| 5988833 | Kansas AMR-prophage phylo | Running | After AMR completes | Depends on 5988834 |
| 5988835 | Latest 1000 bacteria | ? | Variable | Testing organism diversity fix |

**Next check:** Monitor job 5986450 closely - this is the 5-year dataset critical for publication.

---

## Notes

- **v1.3-dev has critical bug fixes** - must be merged to main before publication
- **Kansas multi-organism analysis** - adds comparative power to publication
- **E. coli 2020-2024** - complete temporal analysis (5 years)
- **Data Explorer** - interactive visualization is a key feature

---

## Contact for Questions

Tyler Doerksen - tdoerks@vet.k-state.edu

---

**Last Updated:** January 23, 2026
