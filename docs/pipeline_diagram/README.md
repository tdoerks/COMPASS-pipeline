# COMPASS Pipeline Workflow Diagram

This directory contains the COMPASS pipeline workflow visualization in metro map style, similar to nf-core pipelines.

## Files

- **`compass_pipeline.mmd`** - Mermaid diagram source file
- **`compass_pipeline.svg`** - Scalable vector graphic (for presentations, posters)
- **`compass_pipeline.png`** - PNG image (for slides, documents)

## Pipeline Overview

The COMPASS pipeline performs comprehensive analysis of bacterial genomes including:

### 🔵 Input & Download
- Metadata-based sample discovery (NCBI SRA)
- Direct accession list input
- FASTQ download with fasterq-dump

### 🟢 Quality Control
- Raw read QC (FASTQC)
- Adapter trimming and quality filtering (FASTP)

### 🟡 Assembly & Validation
- De novo assembly (SPADES)
- Assembly quality assessment (QUAST)
- Genome completeness checking (BUSCO)

### 🔴 Antimicrobial Resistance (AMR)
- **Primary**: AMRFinder Plus (NCBI curated database)
- **Multi-database**: ABRICATE screening against:
  - NCBI AMRFinderPlus
  - CARD (Comprehensive Antibiotic Resistance Database)
  - ResFinder
  - ARG-ANNOT
  - VFDB (Virulence Factor Database)

### 🟣 Prophage Analysis
- Prophage prediction and extraction (VIBRANT)
- Secondary gene annotation (PHANOTATE)
- Prophage-AMR integration analysis

### 🔵 Molecular Typing & Plasmids
- Multi-locus sequence typing (MLST)
- Plasmid reconstruction and typing (MOB-suite)

### 🟢 Reporting
- Integrated quality report (MultiQC)
- Interactive Data Explorer dashboard

## Rendering the Diagram

### Option 1: GitHub (Automatic)
GitHub automatically renders `.mmd` files when viewed in the repository.

### Option 2: Command Line (requires mermaid-cli)

```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate SVG
mmdc -i compass_pipeline.mmd -o compass_pipeline.svg

# Generate PNG (high resolution for presentations)
mmdc -i compass_pipeline.mmd -o compass_pipeline.png -w 2400 -H 1800
```

### Option 3: Online Editor
1. Go to https://mermaid.live/
2. Paste contents of `compass_pipeline.mmd`
3. Export as SVG or PNG

### Option 4: VS Code Extension
Install "Markdown Preview Mermaid Support" extension to preview in VS Code.

## Usage in Presentations

### For PowerPoint/Keynote:
1. Use the PNG version (`compass_pipeline.png`)
2. Insert as image
3. Scale to fit slide

### For LaTeX/Beamer:
1. Use the SVG version (`compass_pipeline.svg`)
2. Include with `\includegraphics` or convert to PDF

### For Markdown Presentations:
1. Embed directly:
```markdown
![COMPASS Pipeline](docs/pipeline_diagram/compass_pipeline.png)
```

## Color Coding

- **Blue** (Input/Download): Data acquisition
- **Green** (QC): Quality control steps
- **Yellow** (Assembly): Genome assembly and validation
- **Red** (AMR): Antimicrobial resistance detection - KEY FOCUS
- **Purple** (Prophage): Prophage analysis - KEY FOCUS
- **Light Blue** (Typing): Molecular typing and plasmids
- **Green** (Output): Final reports and results

## Pipeline Highlights

### Key Features:
✅ **Automated**: End-to-end from SRA to results
✅ **Comprehensive**: AMR, prophages, typing, plasmids
✅ **Reproducible**: Nextflow + Singularity containers
✅ **Scalable**: Parallel processing, HPC-ready
✅ **Interactive**: Data Explorer for result browsing

### Novel Contributions:
🔬 **Prophage-AMR Integration**: First comprehensive analysis linking prophage carriage to AMR genes
🔬 **Multi-organism**: Works with any bacterial species (E. coli, Salmonella, Campylobacter, etc.)
🔬 **Temporal Analysis**: Designed for time-series surveillance studies

## Citation

If you use this diagram or pipeline in presentations or publications, please cite:

```
Doerks, T. (2026). COMPASS: Comprehensive Omics Analysis Pipeline for
Surveillance and Study of bacterial pathogens.
Kansas State University College of Veterinary Medicine.
```

## Related Documentation

- **Pipeline README**: `/README.md`
- **User Guide**: `/docs/user_guide.md` (TODO)
- **Session Notes**: `/SESSION_2026-01-23.md`
- **Phi Zeta Presentation**: `/docs/presentations/phi_zeta_2026/`
