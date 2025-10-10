# Database Setup Guide

This guide provides instructions for setting up the required databases for the COMPASS pipeline.

## Automatic Downloads

The pipeline will attempt to automatically download the following databases:

1. **AMRFinderPlus Database** - Downloaded automatically on first run
2. **Prophage-DB** - Attempted automatic download from Dryad
3. **CheckV Database** - Must be manually downloaded and specified in config

## Manual Database Setup

### 1. AMRFinderPlus Database

The AMRFinderPlus database is downloaded automatically by the pipeline. No manual setup required.

### 2. Prophage-DB (for DIAMOND searches)

**Automatic Download:**
The pipeline will attempt to download and build the Prophage-DB DIAMOND database automatically. This requires:
- ~1 GB download
- ~10-15 minutes to build the database
- Sufficient disk space (~2-3 GB during build)

**Manual Download (if automatic fails):**

If the automatic download fails due to Dryad access restrictions, follow these steps:

1. Visit the Prophage-DB Dryad repository:
   ```
   https://datadryad.org/stash/dataset/doi:10.5061/dryad.3n5tb2rs5
   ```

2. Download the file `prophage_proteins.faa.gz` (July 18, 2024 version, ~1 GB)

3. Build the DIAMOND database:
   ```bash
   # Extract the file
   gunzip prophage_proteins.faa.gz

   # Build DIAMOND database
   diamond makedb --in prophage_proteins.faa --db prophage_db
   ```

4. Update your `nextflow.config` to point to the database:
   ```groovy
   params {
       prophage_db = "/path/to/prophage_db.dmnd"
   }
   ```

**Alternative: Use pre-built database**

If you already have a built `prophage_db.dmnd` file, simply set the path in your config:
```groovy
params {
    prophage_db = "/homes/yourname/databases/prophage_db.dmnd"
}
```

### 3. CheckV Database

CheckV database must be downloaded and set up manually.

**Download and Setup:**

1. Download the CheckV database:
   ```bash
   # Create database directory
   mkdir -p ~/databases
   cd ~/databases

   # Download CheckV database (v1.5)
   wget https://portal.nersc.gov/CheckV/checkv-db-v1.5.tar.gz

   # Extract
   tar -xzf checkv-db-v1.5.tar.gz
   ```

2. Update your `nextflow.config`:
   ```groovy
   params {
       checkv_db = "/homes/yourname/databases/checkv-db-v1.5"
   }
   ```

## Database Locations

### Recommended Directory Structure

```
~/databases/
├── checkv-db-v1.5/
│   ├── genome_db/
│   ├── hmm_db/
│   └── ...
├── prophage_db.dmnd
└── amrfinder_db/  (auto-created by pipeline)
```

### Disk Space Requirements

| Database | Download Size | Installed Size |
|----------|---------------|----------------|
| AMRFinderPlus | ~50 MB | ~200 MB |
| Prophage-DB | ~1 GB | ~1.5 GB |
| CheckV | ~1.3 GB | ~1.3 GB |

## Configuration

Update your `nextflow.config` with the database paths:

```groovy
params {
    // AMRFinder database (leave empty for auto-download)
    amrfinder_db = ""

    // Prophage database (leave empty for auto-download, or provide path)
    prophage_db = ""
    // OR
    prophage_db = "/homes/yourname/databases/prophage_db.dmnd"

    // CheckV database (required)
    checkv_db = "/homes/yourname/databases/checkv-db-v1.5"
}
```

## Troubleshooting

### Prophage-DB Download Fails

**Problem:** Dryad blocks automated downloads with CAPTCHA

**Solution 1:** Use a web browser
1. Visit https://datadryad.org/stash/dataset/doi:10.5061/dryad.3n5tb2rs5
2. Click "Download Dataset" button
3. Extract and follow manual setup instructions above

**Solution 2:** Use institutional access
If your institution has Dryad access, try downloading from a campus network or VPN.

**Solution 3:** Alternative mirrors
Check if the Prophage-DB authors provide alternative download locations in the paper:
- Paper: https://environmentalmicrobiome.biomedcentral.com/articles/10.1186/s40793-024-00659-1

### CheckV Database Issues

**Problem:** CheckV fails with database error

**Solution:** Ensure the database path points to the directory containing `genome_db` and `hmm_db` subdirectories:
```bash
ls ${checkv_db}/
# Should show: genome_db/  hmm_db/  README.txt  ...
```

### Disk Space Issues

**Problem:** Not enough space to build databases

**Solution:**
1. Use a different location with more space
2. Clean up old pipeline work directories: `nextflow clean -f`
3. Build databases on a system with more space, then copy the `.dmnd` file

## Database Updates

### Checking for Updates

- **AMRFinderPlus:** Check https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/
- **Prophage-DB:** Check https://datadryad.org/stash/dataset/doi:10.5061/dryad.3n5tb2rs5
- **CheckV:** Check https://bitbucket.org/berkeleylab/checkv/

### Updating Databases

To update a database:
1. Download the new version
2. Update the path in `nextflow.config`
3. Re-run the pipeline

## References

- **Prophage-DB:** Song W, et al. (2024). Environmental Microbiome. https://doi.org/10.1186/s40793-024-00659-1
- **CheckV:** Nayfach S, et al. (2021). Nature Biotechnology. https://doi.org/10.1038/s41587-020-00774-7
- **AMRFinderPlus:** Feldgarden M, et al. (2021). Scientific Reports. https://doi.org/10.1038/s41598-021-91456-0
