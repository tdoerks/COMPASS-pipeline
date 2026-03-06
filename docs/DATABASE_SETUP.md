# Database Setup Guide

This guide explains how to download and set up the required databases for the COMPASS pipeline.

## Required Databases

### 1. Prophage Database (Required for phage analysis)

The prophage database is used by DIAMOND to identify and classify phage sequences detected by VIBRANT.

**Source**: [Prophage-DB on Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.3n5tb2rs5)

**Download and Setup:**

```bash
# Create databases directory
mkdir -p /homes/$USER/databases
cd /homes/$USER/databases

# Download prophage protein sequences (1.01 GB)
wget https://datadryad.org/stash/downloads/file_stream/356776 -O prophage_proteins.faa.gz

# Decompress
gunzip prophage_proteins.faa.gz

# Create DIAMOND database
module load diamond  # or use container
diamond makedb --in prophage_proteins.faa --db prophage_db

# Verify the database was created
ls -lh prophage_db.dmnd
```

**Expected output**: `prophage_db.dmnd` file (~500MB)

**Pipeline parameter**: `--prophage_db /homes/$USER/databases/prophage_db.dmnd`

---

### 2. Prophage Metadata (Required for detailed phage information)

The metadata file contains detailed information about each prophage in the database, including:
- Host taxonomy (phylum, genus, species)
- Environment of isolation
- Quality metrics (CheckV quality, completeness)
- Geographic coordinates
- Functional annotations (AMG genes)

**Source**: [Prophage-DB Metadata on Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.3n5tb2rs5)

**Download and Setup:**

```bash
cd /homes/$USER/databases

# Download metadata file (90.65 MB)
wget https://datadryad.org/stash/downloads/file_stream/356780 -O prophage_metadata.xlsx

# Verify the file
ls -lh prophage_metadata.xlsx
```

**Expected output**: `prophage_metadata.xlsx` file (~87-91 MB)

**Pipeline parameter**: `--prophage_metadata /homes/$USER/databases/prophage_metadata.xlsx`

**What it contains:**
- **Table 1**: Prophage genome metadata (356,776 entries)
  - File names and contig IDs
  - Host taxonomy (domain, phylum, class, order, family, genus, species)
  - Environment and isolation source
  - Geographic coordinates (latitude, longitude)
  - Quality metrics (CheckV quality, completeness %, contamination)
  - Gene counts (total, viral, host)

- **Table 2**: Auxiliary Metabolic Gene (AMG) metadata
  - KO (KEGG Orthology) annotations
  - Pfam domain annotations
  - VOG (Virus Orthologous Groups) annotations

**How it's used:**
- When DIAMOND finds a match between your sample and a known prophage, the pipeline looks up that prophage in the metadata
- The report then shows detailed information about the matched prophage (host, environment, quality, etc.)
- This helps you understand what type of phages are present in your samples

---

### 3. CheckV Database (Optional - currently disabled)

CheckV assesses the quality and completeness of phage genomes.

**Source**: [CheckV Database](https://portal.nersc.gov/CheckV/)

**Download and Setup:**

```bash
cd /homes/$USER/databases

# Download and extract CheckV database
wget https://portal.nersc.gov/CheckV/checkv-db-v1.5.tar.gz
tar -xzf checkv-db-v1.5.tar.gz

# Verify
ls -lh checkv-db-v1.5/
```

**Pipeline parameter**: `--checkv_db /homes/$USER/databases/checkv-db-v1.5`

**Note**: CheckV is currently disabled in the pipeline due to container path issues. This will be fixed in a future release.

---

### 4. AMRFinder+ Database (Auto-downloaded)

AMRFinder+ database is automatically downloaded by the pipeline on first run.

**Manual download (optional):**

```bash
mkdir -p /homes/$USER/databases/amrfinder
cd /homes/$USER/databases/amrfinder

# Download latest database
amrfinder --update
```

**Pipeline parameter**: `--amrfinder_db /homes/$USER/databases/amrfinder`

---

### 5. BUSCO Lineage Datasets (Recommended: Pre-download)

BUSCO (Benchmarking Universal Single-Copy Orthologs) assesses genome assembly completeness by searching for conserved genes.

**⚠️  Important**: While BUSCO can auto-download databases, **pre-downloading is strongly recommended** to avoid network issues during pipeline runs.

**Quick Setup Script (Recommended):**

```bash
# Navigate to COMPASS pipeline directory
cd /path/to/COMPASS-pipeline

# Run the automated setup script
./bin/setup_busco_databases.sh \
    --download-path /fastscratch/$USER/databases/busco_downloads \
    --auto-lineage

# This downloads:
# - bacteria_odb10 lineage dataset (~1.5 GB)
# - Placement files for auto-lineage mode (~500 MB)
```

**Manual download (alternative):**

```bash
mkdir -p /fastscratch/$USER/databases/busco_downloads

# Download bacteria dataset
busco --download bacteria_odb10 --download_path /fastscratch/$USER/databases/busco_downloads

# For auto-lineage mode, run once to download placement files
# (creates a test genome and runs BUSCO to trigger downloads)
echo ">test" > test.fasta
echo "ATCGATCGATCGATCGATCG" >> test.fasta
busco -i test.fasta -o test_busco -m genome --auto-lineage-prok \
    --download_path /fastscratch/$USER/databases/busco_downloads --force --quiet
rm -rf test.fasta test_busco
```

**Pipeline parameters**:

```bash
--busco_download_path /fastscratch/$USER/databases/busco_downloads
--busco_auto_lineage true  # Recommended for accurate completeness assessment
--skip_busco false
```

**Auto-lineage vs Fixed Lineage:**

- **Auto-lineage** (default in COMPASS): Analyzes genome and selects best matching lineage (e.g., `enterobacterales_odb10` for *E. coli*)
  - More accurate completeness scores
  - Requires placement files (~500 MB additional)
  - Recommended for production use

- **Fixed lineage**: Uses `bacteria_odb10` for all samples
  - Faster, less specific
  - No placement files needed
  - Good for quick testing

---

## Configuration

After downloading databases, update `nextflow.config` or provide parameters at runtime:

### Update nextflow.config

```groovy
params {
    // Phage parameters
    prophage_db = "/homes/$USER/databases/prophage_db.dmnd"
    prophage_metadata = "/homes/$USER/databases/prophage_metadata.xlsx"
    checkv_db = "/homes/$USER/databases/checkv-db-v1.5"

    // AMR parameters
    amrfinder_db = "/homes/$USER/databases/amrfinder"

    // BUSCO parameters
    busco_download_path = "/homes/$USER/databases/busco_downloads"
}
```

### Or provide at runtime

```bash
nextflow run main.nf \
    --prophage_db /homes/$USER/databases/prophage_db.dmnd \
    --prophage_metadata /homes/$USER/databases/prophage_metadata.xlsx \
    --checkv_db /homes/$USER/databases/checkv-db-v1.5 \
    --outdir results
```

---

## Verify Database Setup

Run this script to verify all databases are properly configured:

```bash
#!/bin/bash

echo "Checking COMPASS databases..."
echo ""

# Check prophage database
if [ -f "/homes/$USER/databases/prophage_db.dmnd" ]; then
    size=$(du -h /homes/$USER/databases/prophage_db.dmnd | cut -f1)
    echo "✅ Prophage DIAMOND database: $size"
else
    echo "❌ Prophage DIAMOND database not found"
fi

# Check prophage metadata
if [ -f "/homes/$USER/databases/prophage_metadata.xlsx" ]; then
    size=$(du -h /homes/$USER/databases/prophage_metadata.xlsx | cut -f1)
    echo "✅ Prophage metadata: $size"
else
    echo "❌ Prophage metadata not found"
fi

# Check CheckV database
if [ -d "/homes/$USER/databases/checkv-db-v1.5" ]; then
    echo "✅ CheckV database found"
else
    echo "⚠️  CheckV database not found (optional)"
fi

echo ""
echo "Database check complete!"
```

---

## Disk Space Requirements

| Database | Compressed | Uncompressed | Final Size |
|----------|------------|--------------|------------|
| Prophage proteins (faa.gz) | 1.01 GB | 2.8 GB | - |
| Prophage DIAMOND (.dmnd) | - | - | ~500 MB |
| Prophage metadata (.xlsx) | 90 MB | 90 MB | 90 MB |
| BUSCO bacteria_odb10 | - | - | ~1.5 GB |
| BUSCO placement files | - | - | ~500 MB |
| AMRFinderPlus database | - | - | ~500 MB |
| CheckV database (optional) | 1.4 GB | 2.6 GB | 2.6 GB |
| **Total (required)** | | | **~3.1 GB** |
| **Total (with CheckV)** | | | **~5.7 GB** |

---

## Troubleshooting

### BUSCO Errors

**Error**: `md5 hash is incorrect` or `deleting corrupted file`

**Cause**: Network interruption during download or BUSCO server issues.

**Solution**:
```bash
# Remove corrupted files
rm -rf /fastscratch/$USER/databases/busco_downloads/placement_files/*.tar.gz

# Re-run setup script
./bin/setup_busco_databases.sh \
    --download-path /fastscratch/$USER/databases/busco_downloads \
    --auto-lineage
```

**Error**: `BUSCO command not found`

**Solution**:
```bash
# On HPC with modules
module load BUSCO

# Or activate conda environment
conda activate busco-env

# Verify
busco --version
```

**Error**: Pipeline fails at BUSCO step with "Not a valid path value"

**Cause**: BUSCO failed and pipeline received a sample ID instead of a file path.

**Solution**: This is now fixed in the pipeline (v1.2-mod). BUSCO failures are gracefully handled and won't crash the pipeline. Update to the latest version:
```bash
git pull origin v1.2-mod
```

**Temporary workaround** (skip BUSCO for testing):
```bash
nextflow run main.nf --skip_busco true ...
```

### DIAMOND database errors

**Error**: `Database was built with an incompatible version`

**Solution**: Rebuild the database with your version of DIAMOND:
```bash
diamond makedb --in prophage_proteins.faa --db prophage_db
```

### Metadata file errors

**Error**: `Cannot read Excel file` or `openpyxl not found`

**Solution**: The container includes all required dependencies. If running locally, install:
```bash
pip install pandas openpyxl
```

### CheckV database path issues

**Note**: CheckV is currently disabled in the pipeline. This feature is under development.

---

## References

**Prophage-DB**:
- **Paper**: [Add citation when published]
- **Data**: https://datadryad.org/dataset/doi:10.5061/dryad.3n5tb2rs5
- **Description**: Comprehensive database of 356,776 prophage sequences from bacterial and archaeal genomes

**CheckV**:
- **Paper**: Nayfach et al. (2021) Nature Biotechnology
- **Website**: https://bitbucket.org/berkeleylab/checkv/

**DIAMOND**:
- **Paper**: Buchfink et al. (2021) Nature Methods
- **Website**: https://github.com/bbuchfink/diamond

---

## Questions?

For issues with database setup, please open an issue at:
https://github.com/tdoerks/COMPASS-pipeline/issues
