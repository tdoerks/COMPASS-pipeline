# COMPASS Pipeline Feature Ideas & TODO

This file tracks ideas and enhancements for the COMPASS pipeline that can be implemented when ready.
Ideas are organized by priority and category.

---

## 🎯 High Priority

### 1. General Summary Report (High-Level Overview)
**Status**: Not Started
**Priority**: High
**Requested**: 2025-11-07

**Problem**: Current pipeline report drills too deep for initial data review. Need a high-level summary report that gives quick overview of results from each analysis module.

**Proposed Solution**:
- Create `bin/generate_summary_report.py` that reads all module outputs and creates:
  - **Executive Summary**: Sample count, overall QC stats, key findings
  - **Assembly QC Overview**: BUSCO/QUAST summary statistics (not individual samples)
  - **AMR Overview**: Top AMR genes detected, drug class distribution, % samples with AMR
  - **Phage Overview**: % samples with prophages, prophage quality distribution
  - **Typing Overview**: MLST scheme distribution, top serotypes
  - **Mobile Elements**: % samples with plasmids, average plasmids per sample
  - **AMR-Phage Summary**: % AMR on prophage contigs, top enriched genes

**Output Format Options**:
- [ ] HTML dashboard with summary cards
- [ ] Single-page PDF report
- [ ] TSV summary table
- [ ] All of the above

**Integration Point**:
- Add as final module in `workflows/complete_pipeline.nf`
- Or standalone script: `bin/generate_summary_report.py <results_dir>`

**Related Files**:
- `modules/combine_results.nf` - Current detailed report
- `bin/comprehensive_amr_analysis.py` - Similar approach for AMR-phage

**Notes**:
- Should complement (not replace) detailed `combine_results` report
- Useful for initial triage: "Did the pipeline work? What did we find?"
- Then drill down into detailed reports for specific findings

---

## 📊 Reporting & Visualization

### 2. Interactive AMR-Phage Dashboard
**Status**: Partially Implemented
**Priority**: Medium

**Current State**: `comprehensive_amr_analysis.py` generates HTML report
**Enhancement Ideas**:
- [ ] Add interactive filtering (by organism, year, source)
- [ ] Prophage quality filter
- [ ] Gene-level drill-down
- [ ] Export filtered results to CSV

### 3. Multi-Year Comparison Report
**Status**: Not Started
**Priority**: Medium

**Proposed Features**:
- Temporal trends in AMR prevalence
- Prophage detection rates over time
- Geographic patterns (if multi-state data)
- Source-stratified trends (Ground Beef vs Ground Turkey, etc.)

---

## 🧬 Analysis Enhancements

### 4. Prophage Integration Site Analysis
**Status**: Not Started
**Priority**: Medium

**Goal**: Identify common prophage integration sites (tRNA genes, specific chromosomal loci)

**Approach**:
- Parse VIBRANT prophage coordinates
- Map to reference genome annotations
- Identify tRNA integration sites
- Find conserved integration motifs

### 5. AMR Gene Context Analysis
**Status**: Not Started
**Priority**: Medium

**Goal**: Characterize genetic context around AMR genes (promoters, regulatory elements, nearby genes)

**Approach**:
- Extract ±5kb flanking regions around AMR genes
- Identify mobile element features (integrases, transposases, IS elements)
- Classify context: chromosome, plasmid, prophage, integron, transposon
- Compare contexts for same gene in different samples

### 6. Plasmid-Prophage-AMR Network Analysis
**Status**: Not Started
**Priority**: Medium

**Goal**: Visualize relationships between plasmids, prophages, and AMR genes as network graph

**Approach**:
- Nodes: AMR genes, plasmids, prophages, samples
- Edges: Co-occurrence, physical linkage
- Network metrics: Centrality, clustering
- Interactive visualization (D3.js or Plotly)

---

## 🔧 Pipeline Improvements

### 7. Better Error Handling for Failed Samples
**Status**: Not Started
**Priority**: High
**Reference**: TODO.md, ROADMAP.md

**Current Problem**: Pipeline fails if any sample fails
**Proposed Solution**:
- Add `errorStrategy = 'ignore'` to all modules (or make configurable)
- Collect failed samples into `failed_samples.txt`
- Generate QC report showing success/failure rates by module
- Continue pipeline with successful samples

### 8. Resume-Friendly Checkpointing
**Status**: Partially Implemented (Nextflow `-resume`)
**Priority**: Medium

**Enhancements**:
- Better work directory management
- Automatic cleanup of intermediate files for successful samples
- Option to resume from specific module (not just failed processes)

### 9. Resource Auto-Tuning
**Status**: Not Started
**Priority**: Low

**Goal**: Automatically adjust CPU/memory based on input size

**Approach**:
- Estimate assembly size from read count/quality
- Scale SPAdes memory allocation
- Dynamic VIBRANT resource allocation based on contig count
- Prevent over-allocation for small samples

---

## 📦 New Analysis Modules

### 10. Integron Detection
**Status**: Not Started
**Priority**: Medium

**Tools to Evaluate**:
- IntegronFinder
- Relationship to AMR gene cassettes

### 11. Insertion Sequence (IS) Element Detection
**Status**: Not Started
**Priority**: Low

**Goal**: Identify IS elements near AMR genes (markers of mobility)

### 12. Prophage Taxonomy/Classification
**Status**: Not Started
**Priority**: Medium

**Current State**: VIBRANT provides basic prophage classification
**Enhancements**:
- PHASTER-like taxonomy
- Prophage family classification
- Known prophage database matching

---

## 🎨 Output Improvements

### 13. Standardized Output Structure
**Status**: Not Started
**Priority**: High

**Goal**: Consistent output directory structure across all modules

**Proposed Structure**:
```
results/
├── summary/
│   ├── executive_summary.html      # NEW: High-level overview
│   ├── detailed_report.html        # Current combine_results
│   └── combined_results.tsv
├── qc/
│   ├── multiqc_report.html
│   ├── busco_summary/
│   └── quast_summary/
├── amr/
│   ├── amr_summary.tsv
│   ├── amrfinder_results/
│   └── resistance_gene_catalog.csv
├── phage/
│   ├── prophage_summary.tsv
│   ├── vibrant_results/
│   └── checkv_results/
├── typing/
│   ├── mlst_summary.tsv
│   └── sistr_summary.tsv
├── mobile_elements/
│   ├── plasmid_summary.tsv
│   └── mobsuite_results/
└── analysis/
    ├── amr_enrichment_analysis.csv
    ├── amr_prophage_colocalization.csv
    └── interactive_dashboard.html
```

### 14. Sample-Level Report Cards
**Status**: Not Started
**Priority**: Low

**Goal**: Individual HTML report for each sample with all results

**Useful For**:
- Quality control review
- Publication supplementary materials
- Sharing specific sample results

---

## 🧪 Testing & Validation

### 15. Test Dataset with Known Results
**Status**: Not Started
**Priority**: High

**Goal**: Create small test dataset with known AMR genes, prophages, etc.

**Approach**:
- Select 5-10 well-characterized reference genomes
- Document expected results for each module
- Automated testing: `pytest` or `nextflow test`

### 16. Benchmark Dataset Performance
**Status**: Not Started
**Priority**: Low

**Goal**: Compare COMPASS results to other pipelines (NCBI, Pathogen Detection, etc.)

---

## 📝 Documentation

### 17. Tutorial Notebooks
**Status**: Not Started
**Priority**: Medium

**Goal**: Jupyter notebooks demonstrating common analyses

**Topics**:
- Running pipeline on example data
- Interpreting AMR-phage results
- Multi-year comparative analysis
- Geographic/temporal patterns

### 18. Video Tutorials
**Status**: Not Started
**Priority**: Low

**Topics**:
- Pipeline setup and configuration
- Running on Beocat HPC
- Interpreting results
- Troubleshooting common errors

---

## 🔬 Research Questions to Address

### 19. AMR-Phage Co-Evolution Analysis
**Goal**: Test if specific AMR genes co-evolve with specific prophage types

**Approach**:
- Phylogenetic analysis of prophages carrying AMR
- Test for co-phylogeny (prophage tree vs host tree)
- Identify recent HGT events

### 20. Source Attribution Modeling
**Goal**: Predict food source from AMR-prophage profiles

**Approach**:
- Machine learning (Random Forest, SVM)
- Features: AMR genes, prophages, plasmids
- Cross-validation with NARMS metadata
- Important for outbreak investigation

---

## Implementation Notes

### How to Use This File

1. **Add New Ideas**: Append to appropriate section with date and brief description
2. **Update Status**: Change status as work progresses (Not Started → In Progress → Complete)
3. **Cross-Computer Work**: Commit this file after each session
4. **Prioritization**: Move items between priority levels as needed

### Status Labels
- **Not Started**: Idea documented, no implementation
- **In Progress**: Actively being developed
- **Testing**: Implemented, needs validation
- **Complete**: Finished and merged to main
- **On Hold**: Good idea, but waiting for dependency/resource

### Priority Labels
- **High**: Should implement soon (next 1-2 months)
- **Medium**: Useful, implement when time permits (3-6 months)
- **Low**: Nice to have, long-term goals (6+ months)

---

## Recently Completed

### ✅ AMR-Prophage Enrichment Analysis Suite (2025-11-07)
- `analyze_enriched_amr_genes.py` - Gene enrichment statistics
- `investigate_dfra51.py` - Deep dive into dfrA51 enrichment
- `investigate_mdsa_mdsb.py` - mdsA+mdsB co-occurrence analysis
- Comprehensive documentation in `analysis/` directory

### ✅ MOB-suite Fix (2025-11-07)
- Fixed `--run_typer` invalid argument error
- Now properly detects plasmids (was 0% before fix)

---

**Last Updated**: 2025-11-07
**Maintainer**: Tyler Doerks
**Contributors**: Tyler + Claude Code

Feel free to add, modify, or reorganize as needed!
