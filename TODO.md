# COMPASS Pipeline - TODO List

## ✅ Recently Completed (claude-dev-playground branch)
- [x] **MLST for strain typing** - Multi-locus sequence typing for all bacteria
- [x] **SISTR serotyping** - Salmonella in silico serotyping with conditional execution
- [x] **MOB-suite plasmid detection** - Plasmid reconstruction and typing
- [x] **BUSCO assembly QC** - Genome completeness and contamination assessment
- [x] **QUAST assembly statistics** - N50, contig counts, GC%, assembly length
- [x] **FastQC raw read QC** - Pre-trimming quality assessment
- [x] **fastp read trimming** - Quality filtering and adapter removal
- [x] **ABRicate multi-database AMR** - NCBI, CARD, ResFinder, ARG-ANNOT screening
- [x] **MultiQC reporting** - Aggregated QC reports across all tools
- [x] **COMPASS summary generator** - Integrated TSV summary with all metrics
- [x] **Typing subworkflow** - Organized MLST and serotyping
- [x] **Mobile elements subworkflow** - Plasmid and MGE analysis organization
- [x] **Enhanced AMR subworkflow** - AMRFinder+ and ABRicate integration
- [x] **Complete QC pipeline** - End-to-end quality control from reads to assemblies
- [x] **Comprehensive documentation** - README, CHANGELOG, citations

## Immediate Priorities
- [ ] Fix CheckV database path
- [ ] Fix PHANOTATE timeout issues
- [ ] Add error handling for failed samples (partial - error handling added to all new modules)
- [ ] Test parallelization at scale
- [ ] Test complete pipeline on real NARMS dataset

## High Priority Additions
- [ ] Virulence factor detection (VirulenceFinder/VFDB)
- [ ] Integron detection (IntegronFinder)
- [ ] PlasmidFinder (additional to MOB-suite)
- [ ] SerotypeFinder for E. coli

## Nice to Have
- [ ] SNP analysis for phylogenetics
- [ ] Pan-genome analysis
- [ ] Interactive visualizations
- [ ] Enhanced HTML reports with AMR heatmaps

## Future Vision
- [ ] Dashboard interface
- [ ] Database backend
- [ ] Cloud deployment options
