# Database Path Update Guide

## The Situation

You now have `/bulk/tylerdoe/` storage, which is better for databases than `/homes/` (which can get full).

## Current Hardcoded Paths in nextflow.config

```groovy
prophage_db = "/homes/tylerdoe/databases/prophage_db.dmnd"
prophage_metadata = "/homes/tylerdoe/databases/prophage_metadata.xlsx"
busco_download_path = "/homes/tylerdoe/databases/busco_downloads"
```

## Recommended Database Structure

Since you have `/bulk/` storage now, I recommend:

```
/bulk/tylerdoe/databases/
├── prophage_db.dmnd          # Large DIAMOND database
├── prophage_metadata.xlsx
└── busco_downloads/          # BUSCO lineages (can get large)
```

## How to Migrate

### Option 1: Move Databases to /bulk/ (Recommended)

```bash
# Create databases directory in bulk storage
mkdir -p /bulk/tylerdoe/databases

# Move databases from wherever they currently are
# If they're in /fastscratch:
mv /fastscratch/tylerdoe/databases/* /bulk/tylerdoe/databases/

# Or if they're in /homes:
mv /homes/tylerdoe/databases/* /bulk/tylerdoe/databases/

# Update nextflow.config
cd /fastscratch/tylerdoe/COMPASS-pipeline
# Edit nextflow.config and change paths to /bulk/tylerdoe/databases/
```

### Option 2: Use Command-Line Parameters (No Config Edit Needed)

You can override the config paths when running:

```bash
nextflow run main.nf \
    --prophage_db /bulk/tylerdoe/databases/prophage_db.dmnd \
    --busco_download_path /bulk/tylerdoe/databases/busco_downloads \
    ...
```

### Option 3: Keep in /fastscratch (Current Setup)

If databases are already in `/fastscratch/tylerdoe/databases/`, just update the config:

```groovy
prophage_db = "/fastscratch/tylerdoe/databases/prophage_db.dmnd"
prophage_metadata = "/fastscratch/tylerdoe/databases/prophage_metadata.xlsx"
busco_download_path = "/fastscratch/tylerdoe/databases/busco_downloads"
```

## Run check_databases.sh to See Current State

```bash
sbatch check_databases.sh
# Check output:
cat /fastscratch/tylerdoe/check_databases_*.out
```

This will show you where your databases currently are.

## Storage Comparison

| Location | Best For | Quota | Speed | Notes |
|----------|----------|-------|-------|-------|
| `/homes/` | Small files, configs | Limited (~20GB?) | Slow | Gets full easily |
| `/fastscratch/` | Active work, temp files | Larger | FAST | Node-local storage |
| `/bulk/` | Databases, archives | Large | Medium | Good for reference data |

## Recommendation

1. **Databases** → `/bulk/tylerdoe/databases/`
2. **Active work** → `/fastscratch/tylerdoe/COMPASS-pipeline/`
3. **Results** → `/fastscratch/tylerdoe/results_*` (then archive to /bulk when done)
4. **Nextflow work** → `/fastscratch/tylerdoe/work_*` (fast I/O needed)

## After Moving Databases

Update `nextflow.config` line 33-41:

```groovy
// Phage parameters
prophage_db = "/bulk/tylerdoe/databases/prophage_db.dmnd"
prophage_metadata = "/bulk/tylerdoe/databases/prophage_metadata.xlsx"

// BUSCO parameters
busco_download_path = "/bulk/tylerdoe/databases/busco_downloads"
```

Then commit and push the change!
