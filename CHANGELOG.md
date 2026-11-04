# Changelog

All notable changes to COMPASS are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0]

This release centers on a major new interactive HTML summary report with a dynamic
Metadata Explorer, plus AMRFinder accuracy fixes, hardened FASTA-input support, and
release cleanup.

### Added
- **COMPASS Summary report** (`bin/generate_compass_summary.py`) — a rich, self-contained
  HTML report generated at the end of every run.
- **Metadata Explorer** — dynamic pivot-table exploration of results:
  - Faceted filtering and a filterable data table
  - Categorical group-by across COMPASS fields
  - Auto-detection of all SRA metadata fields
  - Support for FASTA/assembly inputs (samplesheet metadata passed through)
- **Virulence factor tracking** — parses AMRFinder `--plus` VIRULENCE rows.
- `recreate_filtered_metadata.py` — rebuilds the sample list from results / QUAST dirs.
- Automated-analysis disclaimer in the summary report.

### Changed
- **Dashboard export** now emits TSV instead of CSV (matches the paper + pipeline output).
- **Reference-database paths are parameterized** — no hardcoded paths. Defaults resolve
  under `${projectDir}/databases` via a new `--database_dir`; override individually with
  `--prophage_db`, `--prophage_metadata`, `--busco_download_path`. See `docs/DATABASE_SETUP.md`.

### Fixed
- **AMRFinder organism mapping** uses correct species names and handles unsupported organisms.
- **FASTA-only input** robustness — defensive checks for missing columns (`assembly_quality`,
  `mdr_status`, `num_contigs`, `n50`, `num_prophages`, `num_amr_genes`, `num_plasmids`).
- Datetime shadowing in HTML report generation.
- `COMPASS_SUMMARY` now uses an absolute output path so helper scripts can read results.
- More reliable run-directory and branch detection (`SLURM_SUBMIT_DIR`, fresh clones).

### Maintenance
- Removed development/scratch files for a clean release.

**Full changelog:** https://github.com/tdoerks/COMPASS-pipeline/compare/1.0.0...1.1.0

## [1.0.0]

### Added
- Initial COMPASS pipeline: data acquisition, assembly, assembly QC (BUSCO/QUAST),
  AMR analysis (AMRFinder/abricate), typing (MLST/SISTR), mobile-element analysis
  (MOB-suite), prophage analysis (VIBRANT/DIAMOND/PHANOTATE), and an HTML summary report.
