# Automated Database Downloads in COMPASS

## Overview

COMPASS is designed to automatically download and manage required databases to minimize manual setup. This document explains which databases auto-download and which require manual setup.

---

## ✅ Fully Automated Databases

### 1. **BUSCO Lineages** (v1.2+)
- **Auto-download**: YES
- **How it works**: BUSCO process checks if lineage exists, downloads if missing
- **Location**: `${params.busco_download_path}/lineages/bacteria_odb10/`
- **Size**: ~300MB
- **First run**: Downloads automatically (adds ~5 minutes)
- **Subsequent runs**: Uses cached database

```groovy
// Config (nextflow.config)
params.busco_download_path = "/homes/$USER/databases/busco_downloads"
```

### 2. **AMRFinder Database**
- **Auto-download**: YES (built-in to AMRFinder)
- **How it works**: AMRFinder downloads database on first run if not present
- **Location**: `${params.amrfinder_db}` or auto-managed
- **Size**: ~500MB
- **Update**: `amrfinder --update` (manual or scheduled)

```groovy
// Config
params.amrfinder_db = ""  // Empty = auto-download
```

### 3. **Abricate Databases**
- **Auto-download**: YES (built-in to Abricate)
- **Databases**: NCBI, CARD, ResFinder, ARG-ANNOT
- **How it works**: Abricate container includes databases
- **Update**: Container version update pulls new databases

---

## ⚠️ Manual Setup Required (Large Files)

### 1. **Prophage Database (DIAMOND)**
- **Auto-download**: NO (too large, ~1GB compressed)
- **Manual setup required**: YES
- **Reason**: Large file, one-time download from Dryad

**Setup Instructions:**
```bash
# 1. Download prophage protein sequences (1.01 GB)
cd /homes/$USER/databases
wget https://datadryad.org/stash/downloads/file_stream/356776 -O prophage_proteins.faa.gz

# 2. Decompress
gunzip prophage_proteins.faa.gz

# 3. Create DIAMOND database
module load diamond  # or use container
diamond makedb --in prophage_proteins.faa --db prophage_db

# 4. Update config
params.prophage_db = "/homes/$USER/databases/prophage_db.dmnd"
```

**Why manual?**
- Large file (1GB+ compressed, 2.8GB uncompressed)
- Requires DIAMOND database building step
- One-time setup, rarely updated
- Better to download once and reuse across projects

### 2. **Prophage Metadata (Excel)**
- **Auto-download**: NO (large file, ~87MB)
- **Manual setup required**: YES

**Setup Instructions:**
```bash
cd /homes/$USER/databases
wget https://datadryad.org/stash/downloads/file_stream/356780 -O prophage_metadata.xlsx

# Update config
params.prophage_metadata = "/homes/$USER/databases/prophage_metadata.xlsx"
```

**Why manual?**
- Large file (~90MB)
- Excel format (not standard bioinformatics database)
- Rarely updated
- Optional (pipeline runs without it, just no metadata enrichment)

### 3. **CheckV Database** (Currently Disabled)
- **Auto-download**: PLANNED
- **Manual setup for now**: YES

**Setup Instructions:**
```bash
cd /homes/$USER/databases
wget https://portal.nersc.gov/CheckV/checkv-db-v1.5.tar.gz
tar -xzf checkv-db-v1.5.tar.gz

# Update config
params.checkv_db = "/homes/$USER/databases/checkv-db-v1.5"
```

**Status**: CheckV is disabled due to container path issues. Re-enablement planned for v1.2.

---

## 🔄 Database Update Strategy

### Automated Updates (Future Enhancement)

**Planned for v1.3:**
```groovy
// Auto-update parameters
params.auto_update_databases = false  // Enable automatic updates
params.database_cache_days = 90       // Refresh if older than X days
```

**Would enable:**
- Periodic AMRFinder database updates
- BUSCO lineage version checking
- Abricate database updates

### Current Update Process (Manual)

**AMRFinder:**
```bash
apptainer exec docker://ncbi/amr:latest amrfinder --update
```

**BUSCO:**
```bash
# Download newer lineage version if available
busco --download bacteria_odb10 --download_path /path/to/busco_downloads
```

**Abricate:**
- Update via container version: Pull newer container
```bash
apptainer pull docker://quay.io/biocontainers/abricate:1.0.1--ha8f3691_1
```

---

## 📊 Database Size Summary

| Database | Compressed | Uncompressed | Auto-Download | Location |
|----------|------------|--------------|---------------|----------|
| BUSCO (bacteria_odb10) | 300MB | 300MB | ✅ YES | `busco_downloads/` |
| AMRFinder | 500MB | 500MB | ✅ YES | Auto-managed |
| Abricate DBs | Included | Included | ✅ YES | In container |
| Prophage proteins | 1.01GB | 2.8GB | ❌ NO | Manual setup |
| Prophage DIAMOND | - | 500MB | ❌ NO | Build required |
| Prophage metadata | 87MB | 87MB | ❌ NO | Manual setup |
| CheckV | 1.4GB | 2.6GB | ❌ NO | Manual setup |
| **Total (minimal)** | ~1.8GB | ~3.6GB | - | - |
| **Total (full)** | ~4.9GB | ~7.7GB | - | - |

---

## 🚀 First-Time Setup Workflow

### Minimal Setup (AMR + Phage IDs only)

```bash
# 1. Clone repository
git clone https://github.com/tdoerks/COMPASS-pipeline.git
cd COMPASS-pipeline

# 2. Setup Prophage database (one-time, ~10 minutes)
mkdir -p /homes/$USER/databases
cd /homes/$USER/databases

wget https://datadryad.org/stash/downloads/file_stream/356776 -O prophage_proteins.faa.gz
gunzip prophage_proteins.faa.gz
diamond makedb --in prophage_proteins.faa --db prophage_db

# 3. Update config
# Edit nextflow.config:
#   prophage_db = "/homes/$USER/databases/prophage_db.dmnd"

# 4. Run pipeline (BUSCO & AMRFinder auto-download on first run)
nextflow run main.nf --input samplesheet.csv --outdir results
```

**First run time**: +15 minutes for auto-downloads
**Subsequent runs**: No extra time (databases cached)

### Full Setup (With Metadata Enrichment)

```bash
# All of the above, plus:

# Download prophage metadata
cd /homes/$USER/databases
wget https://datadryad.org/stash/downloads/file_stream/356780 -O prophage_metadata.xlsx

# Update config:
#   prophage_metadata = "/homes/$USER/databases/prophage_metadata.xlsx"
```

---

## 🔧 Troubleshooting Database Issues

### BUSCO fails to download

**Error**: `Unable to download lineage`

**Solution**:
```bash
# Manual download
cd /homes/$USER/databases
mkdir -p busco_downloads
apptainer exec docker://quay.io/biocontainers/busco:5.7.1--pyhdfd78af_0 \
  busco --download bacteria_odb10 --download_path busco_downloads/
```

### AMRFinder database outdated

**Check version**:
```bash
amrfinder --database_version
```

**Update**:
```bash
amrfinder --update
```

### Prophage database version mismatch

**Error**: `Database was built with an incompatible version`

**Solution**: Rebuild with your DIAMOND version
```bash
diamond makedb --in prophage_proteins.faa --db prophage_db
```

### Disk space issues

**Check database sizes**:
```bash
du -sh /homes/$USER/databases/*
```

**Free up space**:
- BUSCO: Can delete older lineages
- AMRFinder: Clean old versions
- Work directories: `rm -rf work/` after successful runs

---

## 📝 Best Practices

### For Pipeline Developers

1. **Large databases (>500MB)**: Require manual setup
2. **Small databases (<100MB)**: Auto-download acceptable
3. **Frequently updated**: Auto-download with version check
4. **Rarely updated**: Manual setup preferred
5. **Container-included**: Ideal (Abricate model)

### For Pipeline Users

1. **Initial setup**: Budget 30-60 minutes for database downloads
2. **Shared systems**: Use shared database directory
   ```groovy
   params.busco_download_path = "/shared/databases/busco"
   params.prophage_db = "/shared/databases/prophage_db.dmnd"
   ```
3. **Regular updates**: Check for database updates quarterly
4. **Disk quotas**: Monitor database directory size

### For HPC Administrators

**Recommended shared setup**:
```bash
# Create shared database directory
mkdir -p /shared/databases/compass
chmod 755 /shared/databases/compass

# Setup databases (one-time)
cd /shared/databases/compass
# Download prophage, busco, etc.

# Users reference in their nextflow.config:
params.prophage_db = "/shared/databases/compass/prophage_db.dmnd"
params.busco_download_path = "/shared/databases/compass/busco_downloads"
```

---

## 🎯 Future Enhancements (Roadmap)

### v1.3: Smart Database Management
- [ ] Database version tracking
- [ ] Automatic update notifications
- [ ] Centralized database download script
- [ ] Database integrity checking (checksums)

### v1.4: Cloud-Ready Databases
- [ ] S3/Google Cloud Storage support
- [ ] Pre-built database images
- [ ] On-demand database provisioning

### v2.0: Database as Code
- [ ] Version-locked database manifests
- [ ] Reproducible database environments
- [ ] Database snapshot/restore

---

## 📚 References

**Database Sources:**
- Prophage-DB: https://datadryad.org/dataset/doi:10.5061/dryad.3n5tb2rs5
- AMRFinder: https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/
- BUSCO: https://busco.ezlab.org/
- CARD: https://card.mcmaster.ca/
- ResFinder: https://cge.food.dtu.dk/services/ResFinder/
- CheckV: https://bitbucket.org/berkeleylab/checkv/

**Update this document**: When adding new databases or changing auto-download behavior
