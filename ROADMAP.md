# COMPASS Pipeline Roadmap

## Current Status (October 2025)
✅ **Working:**
- Full end-to-end pipeline: Metadata → SRA → Assembly → AMR + Phage Analysis
- AMRFinder for resistance gene detection
- VIBRANT for phage identification  
- DIAMOND for prophage database matching
- PHANOTATE for phage gene prediction
- Combined HTML report generation
- Parallelized execution (up to 30 concurrent downloads, 10 assemblies)

🔧 **In Progress:**
- Testing on Kansas NARMS 2023 and 2025 datasets
- CheckV quality assessment (database path issues)

---

## Short-term Improvements

### 1. Fix Current Issues
- [ ] **CheckV database path** - Resolve container database location
- [ ] **PHANOTATE timeout** - Increase time limits or make optional
- [ ] **Entrez-direct Perl warnings** - Use newer container or suppress stderr
- [ ] **Error handling** - Allow pipeline to continue when individual samples fail

### 2. Enhanced Filtering
- [ ] Filter by **host** (human, chicken, cattle, swine)
- [ ] Filter by **isolation source** (clinical, food, environmental)
- [ ] Filter by **geography** (county-level, not just state)
- [ ] Filter by **collection date** (not just publication date)

### 3. Performance Optimization
- [x] Parallelize sample processing
- [ ] Optimize resource allocation per process
- [ ] Add checkpoint/restart capability
- [ ] Cache intermediate results more efficiently

---

## Medium-term Enhancements

### Genomic Analysis Modules

#### 4. Typing & Classification
- [ ] **MLST** (Multi-Locus Sequence Typing) - Track strain distribution
  - Tool: `mlst`
  - Output: Sequence types, allelic profiles
  - Use case: Outbreak investigation, epidemiology

- [ ] **Serotyping** - Organism-specific identification
  - `SISTR` for Salmonella
  - `SerotypeFinder` for E. coli
  - `ClermonTyping` for E. coli phylogroups
  - Use case: Regulatory reporting, source tracking

#### 5. Mobile Genetic Elements
- [ ] **Plasmid Detection** - Track mobile AMR
  - Tools: `PlasmidFinder`, `MOB-suite`
  - Output: Plasmid types, incompatibility groups
  - Use case: Understanding AMR transmission

- [ ] **Integron Detection** - Mobile resistance cassettes
  - Tool: `IntegronFinder`
  - Output: Gene cassettes, integrase genes
  - Use case: Horizontal gene transfer analysis

#### 6. Virulence Analysis
- [ ] **Virulence Factor Detection**
  - Tools: `VFDB`, `VirulenceFinder`
  - Output: Toxins, adhesins, invasins, secretion systems
  - Use case: Pathogenicity assessment

#### 7. Phylogenetics
- [ ] **SNP Analysis** - Evolutionary relationships
  - Tools: `snippy`, `parsnp`, `kSNP3`
  - Output: SNP matrices, phylogenetic trees
  - Use case: Outbreak clustering, transmission chains

- [ ] **Pan-genome Analysis**
  - Tools: `Roary`, `PIRATE`, `PPanGGOLiN`
  - Output: Core/accessory genome, unique genes
  - Use case: Population structure, niche adaptation

#### 8. Advanced Resistance
- [ ] **Comprehensive AMR prediction**
  - Add `ResFinder` alongside AMRFinder
  - Point mutation detection (quinolones, colistin)
  - Resistance mechanism annotation

#### 9. Quality Control
- [ ] **Assembly QC**
  - `CheckM` for completeness/contamination
  - `BUSCO` for gene completeness
  - `QUAST` for assembly statistics
  - Auto-filter low-quality assemblies

#### 10. Annotation
- [ ] **Functional Annotation**
  - Tools: `Prokka`, `Bakta`, `PGAP`
  - Output: GFF3, GenBank files
  - Use case: Detailed genomic characterization

---

## Long-term Vision

### 11. Reporting & Visualization
- [ ] **Interactive HTML reports**
  - AMR heatmaps by sample
  - Phage distribution charts  
  - Geographic distribution maps
  - Temporal trend analysis
  - Phylogenetic trees (interactive)

- [ ] **Dashboard interface**
  - Real-time pipeline monitoring
  - Sample quality metrics
  - Comparative analysis views

### 12. Database Integration
- [ ] Local database for results storage
- [ ] Query interface for historical data
- [ ] Export to standard formats (NCBI, GISAID)

### 13. Comparative Analysis
- [ ] **Batch comparison mode**
  - Compare multiple cohorts
  - Temporal analysis
  - Geographic patterns
  - Source attribution

### 14. Custom Organism Support
- [x] Custom NCBI search module (created, not integrated)
- [ ] Support for non-NARMS datasets
- [ ] User-provided genome upload
- [ ] Custom reference database support

### 15. Cloud/HPC Portability
- [ ] AWS/Google Cloud execution profiles
- [ ] Containerization complete (Docker/Singularity)
- [ ] Conda environment support
- [ ] Multi-cluster compatibility

---

## Research Applications

### Potential Use Cases
1. **Public Health Surveillance**
   - Track AMR trends over time
   - Identify emerging resistance mechanisms
   - Monitor phage-bacteria dynamics

2. **Outbreak Investigation**
   - Rapid strain typing
   - Source attribution
   - Transmission network reconstruction

3. **One Health Integration**
   - Compare human/animal/environmental isolates
   - Track AMR transmission across sectors
   - Identify high-risk reservoirs

4. **Regulatory Support**
   - NARMS reporting automation
   - Quality assurance/quality control
   - Standardized analysis protocols

---

## Technical Debt

### Code Quality
- [ ] Add comprehensive error handling
- [ ] Unit tests for modules
- [ ] Integration tests for workflows
- [ ] Documentation for each module
- [ ] Code style consistency

### Performance
- [ ] Profile resource usage
- [ ] Optimize container sizes
- [ ] Reduce redundant computation
- [ ] Improve I/O efficiency

---

## Community & Collaboration

### Documentation
- [ ] User guide with examples
- [ ] Developer guide for module creation
- [ ] Video tutorials
- [ ] FAQs

### Outreach
- [ ] Publish preprint/paper
- [ ] Present at conferences
- [ ] Engage with NARMS community
- [ ] Collaborate with CDC/USDA/FDA

---

## Notes
- Priority items marked with ⭐ in future updates
- Timeline estimates TBD based on resources
- Feedback welcome via GitHub issues
- Module suggestions can be submitted via pull requests

Last updated: October 2025
