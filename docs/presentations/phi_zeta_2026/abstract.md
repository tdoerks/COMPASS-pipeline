# Phi Zeta Research Day 2026 - Abstract Submission

## Metadata

**Title:** COMPASS: A Comprehensive Pipeline for Surveillance of Antimicrobial Resistance and Prophage-Mediated Horizontal Gene Transfer in Veterinary Pathogens

**Category:** Applied Science

**Presentation Type:** Oral Presentation (Preferred) / Poster

**Keywords:** antimicrobial resistance, prophages, horizontal gene transfer, surveillance, bioinformatics, E. coli, Salmonella, Campylobacter

**Authors:**
- Tyler Doerks, PhD candidate, Department of Diagnostic Medicine/Pathobiology, Kansas State University College of Veterinary Medicine
- [Add your advisor/collaborators here]

**Contact:** tdoerks@vet.k-state.edu

---

## Abstract

**Background:** Antimicrobial resistance (AMR) represents a critical threat to both human and veterinary medicine. Bacteriophages (prophages) integrated into bacterial genomes can serve as vectors for horizontal transfer of AMR genes between pathogens, yet this mechanism remains understudied in veterinary surveillance systems.

**Objective:** We developed COMPASS (Comprehensive Omics Analysis Pipeline for Surveillance and Study), an automated bioinformatics pipeline to investigate AMR gene carriage by prophages in veterinary pathogens and track temporal evolution of AMR-prophage associations.

**Methods:** COMPASS integrates whole-genome sequencing data from NCBI SRA with comprehensive analysis modules including: (1) genome assembly and quality control, (2) AMR gene detection using AMRFinder Plus and multi-database screening (CARD, ResFinder), (3) prophage prediction and annotation (VIBRANT, PHANOTATE), (4) molecular typing (MLST) and plasmid reconstruction (MOB-suite), and (5) phylogenetic analysis. We applied COMPASS to 733 Kansas isolates (2021-2025) representing three major veterinary pathogens (Campylobacter, Salmonella, E. coli) and performed temporal analysis of 2,000+ E. coli genomes (2021-2024).

**Results:** Analysis revealed 396 AMR genes in E. coli prophages, including resistance determinants for β-lactams, aminoglycosides, and trimethoprim. Phylogenetic reconstruction of AMR-carrying prophages identified distinct lineages persisting across multiple years, suggesting stable prophage-mediated AMR transmission networks. Kansas multi-organism surveillance detected 21 prophage-associated AMR genes, with dfrA51 (trimethoprim resistance) predominating across species boundaries.

**Conclusions:** COMPASS provides veterinary researchers with an accessible, comprehensive tool for AMR surveillance that reveals the critical role of prophages in resistance dissemination. These findings support enhanced monitoring of prophage-mediated horizontal gene transfer in veterinary pathogens.

---

## Abstract (Plain Text for PDF Form)

**Word Count:** 267 words

```
COMPASS: A Comprehensive Pipeline for Surveillance of Antimicrobial Resistance and Prophage-Mediated Horizontal Gene Transfer in Veterinary Pathogens

Background: Antimicrobial resistance (AMR) represents a critical threat to both human and veterinary medicine. Bacteriophages (prophages) integrated into bacterial genomes can serve as vectors for horizontal transfer of AMR genes between pathogens, yet this mechanism remains understudied in veterinary surveillance systems.

Objective: We developed COMPASS (Comprehensive Omics Analysis Pipeline for Surveillance and Study), an automated bioinformatics pipeline to investigate AMR gene carriage by prophages in veterinary pathogens and track temporal evolution of AMR-prophage associations.

Methods: COMPASS integrates whole-genome sequencing data from NCBI SRA with comprehensive analysis modules including: (1) genome assembly and quality control, (2) AMR gene detection using AMRFinder Plus and multi-database screening (CARD, ResFinder), (3) prophage prediction and annotation (VIBRANT, PHANOTATE), (4) molecular typing (MLST) and plasmid reconstruction (MOB-suite), and (5) phylogenetic analysis. We applied COMPASS to 733 Kansas isolates (2021-2025) representing three major veterinary pathogens (Campylobacter, Salmonella, E. coli) and performed temporal analysis of 2,000+ E. coli genomes (2021-2024).

Results: Analysis revealed 396 AMR genes in E. coli prophages, including resistance determinants for β-lactams, aminoglycosides, and trimethoprim. Phylogenetic reconstruction of AMR-carrying prophages identified distinct lineages persisting across multiple years, suggesting stable prophage-mediated AMR transmission networks. Kansas multi-organism surveillance detected 21 prophage-associated AMR genes, with dfrA51 (trimethoprim resistance) predominating across species boundaries.

Conclusions: COMPASS provides veterinary researchers with an accessible, comprehensive tool for AMR surveillance that reveals the critical role of prophages in resistance dissemination. These findings support enhanced monitoring of prophage-mediated horizontal gene transfer in veterinary pathogens.
```

---

## Submission Checklist

- [ ] Complete fillable PDF abstract template (download from Phi Zeta website)
- [ ] Copy abstract text above into PDF form
- [ ] Add all co-author names and affiliations
- [ ] Submit via online form by **January 31, 2026, 11:59 PM CST**
- [ ] Await notification of acceptance (February 14, 2026)

---

## Notes for Tyler

**Presentation Preference:**
- Request **Oral Presentation** (10-15 minutes)
- Computational work is better suited to oral format than poster
- Allows you to explain pipeline workflow and phylogenetic findings
- More time to discuss public health implications

**Key Selling Points:**
1. **Novel integration**: First comprehensive prophage-AMR surveillance tool
2. **Veterinary focus**: Directly applicable to clinical/diagnostic labs
3. **Multi-organism**: Not limited to single pathogen
4. **Temporal analysis**: Tracks evolution over time
5. **Open-source**: Available to veterinary research community

**Questions They Might Ask:**
- How long does COMPASS take per sample? (~30-45 min per genome on HPC)
- Can it run on local computers? (Yes, with Docker/Singularity)
- What sequencing platforms? (Any Illumina data, can adapt for ONT)
- How accurate is prophage detection? (VIBRANT: ~95% precision/recall)
- Cost per sample? (Primarily computing time, no software licensing)
