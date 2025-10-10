# COMPASS Pipeline Configuration Profiles

This directory contains modular configuration files for running COMPASS on different HPC systems.

## Available Profiles

### Base Configuration (`base.config`)
- Default resource requirements for all processes
- Automatic retry strategy with resource scaling
- Memory doubles on each retry attempt
- Handles common exit codes (OOM, timeout, etc.)

### Beocat (`beocat.config`)
**Kansas State University Beocat HPC Cluster**
- SLURM executor with `batch.q` queue
- Max resources: 64 CPUs, 256 GB RAM, 7 days
- Apptainer/Singularity enabled
- Contact: beocat-help@cis.ksu.edu

### Ceres (`ceres.config`)
**USDA SCINet Ceres HPC Cluster**
- SLURM executor with intelligent queue selection
  - `short` queue (< 48 hours) for most processes
  - `medium` queue (< 7 days) for long-running processes
- Max resources: 48 CPUs, 384 GB RAM, 14 days
- High-memory nodes available: 80 CPUs, 1.5 TB RAM
- Contact: scinet-vrsc@usda.gov

### Atlas (`atlas.config`)
**USDA SCINet Atlas HPC Cluster**
- SLURM executor with `atlas` queue
- Max resources: 96 CPUs, 384 GB RAM, 14 days
- High-memory nodes available: 96 CPUs, 1.5 TB RAM
- Contact: scinet-vrsc@usda.gov

## Usage

### Running with a Profile

To use a specific profile, add the `-profile` flag:

```bash
# Run on Beocat
nextflow run main.nf -profile beocat --input samplesheet.csv

# Run on Ceres
nextflow run main.nf -profile ceres --input samplesheet.csv

# Run on Atlas
nextflow run main.nf -profile atlas --input samplesheet.csv

# Run locally (for testing)
nextflow run main.nf -profile standard --input samplesheet.csv
```

### Multiple Profiles

You can combine profiles (comma-separated):

```bash
nextflow run main.nf -profile beocat,singularity --input samplesheet.csv
```

## Error/Retry Strategy

All profiles include automatic error handling:

1. **Automatic Retries**: Up to 3 attempts for failed processes
2. **Resource Scaling**: Memory doubles on each retry
3. **Exit Code Handling**: Automatically retries common failure codes:
   - 143: SIGTERM (timeout)
   - 137: SIGKILL (out of memory)
   - 104: Connection reset
   - 134, 139, 140: Segmentation faults

### Example Retry Behavior

If VIBRANT fails due to memory:
- **Attempt 1**: 16 GB memory → Fails with OOM
- **Attempt 2**: 32 GB memory → Fails with OOM
- **Attempt 3**: 64 GB memory → Succeeds

## Resource Limits

Each profile defines maximum resource limits to prevent over-allocation:

| Profile | Max CPUs | Max Memory | Max Time |
|---------|----------|------------|----------|
| Beocat  | 64       | 256 GB     | 7 days   |
| Ceres   | 48       | 384 GB     | 14 days  |
| Atlas   | 96       | 384 GB     | 14 days  |

These limits are automatically enforced by the `check_max()` function in `base.config`.

## Execution Reports

All HPC profiles automatically generate execution reports in `${params.outdir}/pipeline_info/`:

- **Timeline**: Visual timeline of process execution
- **Report**: Resource usage statistics
- **Trace**: Detailed execution trace
- **DAG**: Pipeline directed acyclic graph

## Customizing Configurations

### For Your HPC System

To create a config for your HPC:

1. Copy an existing config (e.g., `beocat.config`)
2. Modify executor, queue, and resource limits
3. Add to `nextflow.config` profiles section:
   ```groovy
   profiles {
       myhpc {
           includeConfig 'conf/myhpc.config'
       }
   }
   ```

### For Specific Runs

Override parameters on the command line:

```bash
# Use more memory for assembly
nextflow run main.nf -profile beocat \
    --input samples.csv \
    --max_memory 512.GB

# Use different queue
nextflow run main.nf -profile ceres \
    --input samples.csv \
    -with-slurm --queue priority
```

## Troubleshooting

### Pipeline Fails with "Executor not found"
- Check that SLURM is available: `which sbatch`
- Use `-profile standard` for local execution

### Out of Memory Errors
- Check retry attempts in execution report
- Increase `max_memory` parameter
- Consider using high-memory nodes

### Jobs Timeout
- Increase `max_time` parameter
- Check queue limits with `sinfo` (SLURM)

### Container Issues
- Verify Apptainer/Singularity is installed
- Check cache directory permissions
- Clear cache: `rm -rf ~/.apptainer/cache`

## Support

- **Beocat**: beocat-help@cis.ksu.edu
- **SCINet (Ceres/Atlas)**: scinet-vrsc@usda.gov
- **COMPASS Issues**: https://github.com/tdoerks/COMPASS-pipeline/issues
