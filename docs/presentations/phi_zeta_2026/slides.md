# COMPASS: Surveillance of AMR and Prophage-Mediated Gene Transfer in Veterinary Pathogens

## Phi Zeta Research Day 2026

Tyler Doerks, PhD Candidate
Department of Diagnostic Medicine/Pathobiology
Kansas State University College of Veterinary Medicine

March 3, 2026

---

## Slide 1: Title Slide

**COMPASS: A Comprehensive Pipeline for Surveillance of Antimicrobial Resistance and Prophage-Mediated Horizontal Gene Transfer in Veterinary Pathogens**

Tyler Doerks, PhD Candidate
[Your Advisor], PhD
Department of Diagnostic Medicine/Pathobiology
Kansas State University College of Veterinary Medicine

Phi Zeta Research Day 2026
March 3, 2026

---

## Slide 2: The AMR Crisis in Veterinary Medicine

### Challenge
- Antimicrobial resistance threatens animal and human health
- CDC: >2.8 million resistant infections annually in US
- Veterinary pathogens serve as reservoirs for resistance genes

### Critical Gap
- **How do AMR genes spread between bacteria?**
- Prophages (integrated viral DNA) can transfer genes horizontally
- Limited tools to track prophage-mediated AMR dissemination

### Visual Suggestion
- Graphic showing bacteria sharing DNA via prophage
- Statistics on AMR impact

---

## Slide 3: Prophages as Vectors of Resistance

### What are Prophages?
- Bacteriophage DNA integrated into bacterial chromosomes
- ~50% of bacteria carry prophages
- Can excise and transfer genes to new hosts

### Link to AMR
- Prophages can carry antimicrobial resistance genes
- Enable horizontal gene transfer between species
- Rapid dissemination of resistance

### Problem
- **Existing surveillance overlooks prophage-AMR associations**

### Visual Suggestion
- Diagram of prophage lifecycle
- Animation showing horizontal gene transfer

---

## Slide 4: Study Objectives

1. **Develop COMPASS Pipeline**
   - Automated, comprehensive surveillance tool
   - Integrates AMR detection with prophage analysis

2. **Kansas Multi-Organism Surveillance**
   - 733 isolates (Campylobacter, Salmonella, E. coli)
   - 2021-2025 temporal coverage

3. **E. coli Temporal Study**
   - 2,000+ genomes across 2021-2024
   - Track AMR-prophage evolution over time

4. **Phylogenetic Analysis**
   - Identify AMR-prophage lineages
   - Detect transmission networks

---

## Slide 5: COMPASS Pipeline Overview

### ![Pipeline Diagram](../../pipeline_diagram/compass_pipeline.png)

**Workflow Stages:**
1. 🔵 **Input**: NCBI SRA metadata or accession lists
2. 🟢 **QC**: FASTQC, FASTP trimming
3. 🟡 **Assembly**: SPADES, QUAST, BUSCO
4. 🔴 **AMR**: AMRFinder Plus, ABRICATE (5 databases)
5. 🟣 **Prophage**: VIBRANT prediction, PHANOTATE annotation
6. 🔵 **Typing**: MLST, MOB-suite plasmids
7. 🟢 **Output**: MultiQC reports, Data Explorer

### Key Features
✅ Automated end-to-end
✅ Reproducible (Nextflow + containers)
✅ Scalable (HPC-ready)

---

## Slide 6: Data Sources & Methods

### Kansas Multi-Organism Dataset
- **Source**: Kansas veterinary diagnostic samples
- **Species**: Campylobacter, Salmonella, E. coli
- **Timeline**: 2021-2025
- **Sample size**: 733 genomes
- **Sequencing**: Illumina whole-genome sequencing

### E. coli Temporal Dataset
- **Source**: NCBI SRA (public data)
- **Species**: Escherichia coli
- **Timeline**: 2021-2024 (4 years)
- **Sample size**: 2,000+ genomes
- **Strategy**: Balanced sampling across years

---

## Slide 7: Computational Methods

### AMR Detection
- **Primary**: NCBI AMRFinder Plus (curated database)
- **Validation**: ABRICATE multi-database screening
  - CARD, ResFinder, ARG-ANNOT, VFDB

### Prophage Analysis
- **Prediction**: VIBRANT (machine learning-based)
- **Annotation**: PHANOTATE (gene calling optimized for phages)
- **AMR-Prophage Linking**: Custom integration analysis

### Phylogenetic Reconstruction
- **Alignment**: MAFFT (multiple sequence alignment)
- **Tree Building**: FastTree (GTR+Gamma, 1000 bootstraps)
- **Visualization**: iTOL (Interactive Tree of Life)

---

## Slide 8: Results - Kansas Multi-Organism Analysis

### Dataset Overview
- **733 genomes analyzed** across 3 species
- **825 samples had prophage predictions**

### Key Findings
- **21 AMR genes detected in prophages**
- **dfrA51 predominates**: 15/21 hits (71%)
  - Trimethoprim resistance
  - Found across multiple species

### Distribution
| Organism | Samples | Prophage-AMR | Rate |
|----------|---------|--------------|------|
| Campylobacter | ~250 | 7 | 2.8% |
| Salmonella | ~300 | 8 | 2.7% |
| E. coli | ~183 | 6 | 3.3% |

### Implication
🔬 **Cross-species prophage-mediated resistance transfer**

---

## Slide 9: Results - E. coli Temporal Study (2021-2024)

### Dataset
- **2,000+ E. coli genomes** from NCBI SRA
- **Balanced sampling**: ~500 per year

### Major Finding: 396 AMR Genes in Prophages

#### Resistance Classes Detected
- β-lactams (ampicillin, cephalosporins)
- Aminoglycosides (gentamicin, streptomycin)
- Trimethoprim/sulfonamides
- Tetracyclines
- Fluoroquinolones

### Temporal Trend
- **Prophage-AMR associations stable 2021-2024**
- Some lineages persist across all 4 years

---

## Slide 10: Phylogenetic Analysis - AMR-Prophage Lineages

### Analysis
- **3,918 AMR-carrying prophages** identified
- **Subsampled to 400** (representative, 100/year)
- **Phylogenetic tree** reveals distinct clades

### Key Observations

1. **Temporal Clustering**
   - Some prophage lineages year-specific
   - Others persist across multiple years

2. **Multi-Year Lineages**
   - Indicate stable prophage populations
   - Continuous circulation of AMR-prophages

3. **Rapid Evolution**
   - New branches emerge each year
   - Suggests ongoing horizontal gene transfer

### Visual
- **Show phylogenetic tree colored by year**
- Highlight persistent vs. transient lineages

---

## Slide 11: Case Study - dfrA51 Dominance

### Gene: dfrA51 (Dihydrofolate Reductase)
- **Resistance**: Trimethoprim
- **Clinical Relevance**: Common in veterinary medicine
- **Prevalence**: 71% of Kansas prophage-AMR hits

### Distribution Across Species
- Campylobacter ✓
- Salmonella ✓
- E. coli ✓

### Interpretation
🔬 **dfrA51-carrying prophage may be broadly mobile**
🔬 **Efficient cross-species transmission**
🔬 **Public health concern**: Resistance spreads across pathogen boundaries

---

## Slide 12: All-Prophage Phylogeny (E. coli)

### Analysis
- **494 prophage sequences** (not just AMR-carrying)
- **Complete prophages** from 2021-2024 E. coli dataset

### Findings
- Diverse prophage population in E. coli
- Some prophage families more prone to carrying AMR
- Certain clades enriched for resistance genes

### Comparison to AMR-Prophage Tree
- AMR-carrying prophages don't form single clade
- **Multiple independent AMR acquisition events**
- Horizontal transfer across diverse prophage backgrounds

### Visual
- **Side-by-side trees**: All-prophage vs AMR-prophage
- Highlight AMR-enriched clades

---

## Slide 13: Public Health & Veterinary Implications

### Surveillance Enhancement
✅ **COMPASS enables routine prophage-AMR monitoring**
✅ **Early detection of emerging resistance mechanisms**
✅ **Tracking horizontal gene transfer in real-time**

### Clinical Impact
- Informs treatment decisions
- Identifies high-risk prophage lineages
- Predicts resistance spread patterns

### One Health Connection
- Veterinary pathogens as AMR reservoirs
- Prophage-mediated transfer to human pathogens
- **Need for integrated surveillance**

### Policy Recommendations
- Include prophage analysis in AMR surveillance programs
- Monitor prophage-AMR associations over time
- Coordinate veterinary and human health monitoring

---

## Slide 14: Future Directions

### Technical Enhancements
1. **Long-read sequencing integration** (ONT, PacBio)
   - Better prophage assembly
   - Complete genome closure

2. **Metagenomic analysis**
   - Culture-independent surveillance
   - Capture unculturable prophages

3. **Machine learning**
   - Predict AMR acquisition risk
   - Identify prophage mobility factors

### Biological Questions
1. What drives prophage-AMR associations?
2. Can we interrupt horizontal transfer?
3. Geographic patterns in prophage-mediated resistance?

### Expansion
- More species (Listeria, Staphylococcus, Streptococcus)
- International datasets
- Longitudinal farm studies

---

## Slide 15: Conclusions & Acknowledgments

### Key Takeaways
1. **COMPASS: Comprehensive surveillance tool** for prophage-AMR analysis
2. **396 AMR genes in E. coli prophages** (2021-2024)
3. **21 prophage-AMR associations** in Kansas multi-organism dataset
4. **Phylogenetic evidence** of stable AMR-prophage transmission networks
5. **dfrA51 cross-species mobility** via prophages

### Impact
🔬 **First comprehensive prophage-AMR surveillance in veterinary pathogens**
🔬 **Reveals hidden mechanism of resistance dissemination**
🔬 **Open-source tool for research community**

### Acknowledgments
- [Your advisor and lab members]
- Kansas State University CVM
- [Funding sources if applicable]
- [Collaborators]

### Questions?

**Contact**: tdoerks@vet.k-state.edu
**GitHub**: [COMPASS-pipeline repository URL]

---

## Conversion Notes

### To PowerPoint (using Pandoc):
```bash
pandoc slides.md -o phi_zeta_2026.pptx --reference-doc=template.pptx
```

### To PDF (using Pandoc + Beamer):
```bash
pandoc slides.md -t beamer -o phi_zeta_2026.pdf
```

### Manual Creation Tips:
- Use consistent color scheme (match pipeline diagram colors)
- Keep bullet points to 5-7 per slide
- Use large fonts (24pt minimum)
- Include pipeline diagram on Slide 5
- Add phylogenetic tree images to Slides 10, 12
- Use data tables sparingly (3-4 rows max)
- Include logos: KSU CVM, Phi Zeta

### Timing (for 10-12 minute talk):
- Slides 1-4: Background (2-3 min)
- Slide 5-7: Methods (2-3 min)
- Slides 8-12: Results (4-5 min)
- Slides 13-15: Conclusions (2-3 min)
- Leave 3-5 min for questions
