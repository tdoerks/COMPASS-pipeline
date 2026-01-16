# Configuration Files

This directory contains environment-specific configuration files for the COMPASS pipeline.

## Configuration Structure

- **base.config**: Default resource requirements and container settings used across all profiles
- **beocat.config**: Kansas State University's Beocat cluster configuration
- **ceres.config**: USDA ARS SCINet Ceres cluster configuration

## Usage

Specify a profile when running the pipeline:

```bash
# Run on Beocat cluster
nextflow run main.nf -profile beocat

# Run on Ceres cluster
nextflow run main.nf -profile ceres

# Run locally (standard profile - default)
nextflow run main.nf -profile standard
```

## Adding a New HPC Environment

To add a new HPC environment:

1. Create a new config file in this directory (e.g., `my_cluster.config`)
2. Add the profile to `nextflow.config`:
   ```groovy
   profiles {
       my_cluster {
           includeConfig 'conf/my_cluster.config'
       }
   }
   ```

### Example Config Template

```groovy
/*
 * My Cluster Configuration
 */

process {
    executor = 'slurm'  // or 'pbs', 'sge', etc.
    queue = 'default'

    errorStrategy = { task.exitStatus in [143,137,104,134,139] ? 'retry' : 'finish' }
    maxRetries = 3
}

params {
    max_memory = 250.GB
    max_cpus = 32
    max_time = 7.d
}

executor {
    queueSize = 100
    submitRateLimit = '10 sec'
}
```

## Profile-Specific Parameters

You can override parameters for specific profiles:

```bash
# Override output directory for Beocat
nextflow run main.nf -profile beocat --outdir /path/to/beocat/results

# Override database paths for Ceres
nextflow run main.nf -profile ceres \
    --prophage_db /project/myproject/databases/prophage_db.dmnd \
    --checkv_db /project/myproject/databases/checkv-db-v1.5
```
