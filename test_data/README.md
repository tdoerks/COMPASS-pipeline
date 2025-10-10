# COMPASS Test Data

This directory contains minimal test data for validating the COMPASS pipeline installation and functionality.

## Test Dataset

The test dataset includes:
- **2 bacterial genome assemblies** (small contigs for quick processing)
- **Samplesheet CSV** defining sample metadata
- **Test configuration profile** for fast execution

## Quick Test Run

Run the test pipeline to verify your installation:

```bash
# From the COMPASS-pipeline directory
nextflow run main.nf -profile test

# Or specify the test config explicitly
nextflow run main.nf -c conf/test.config
```

### Expected Results

The test run should complete in **15-30 minutes** (depending on database downloads) and generate:

- `test_results/` directory with all pipeline outputs
- AMRFinder results for test samples
- Phage identification via VIBRANT
- Combined summary report and HTML visualization
- Execution timeline and resource usage reports

## Test Samples

### test_genome1.fasta
- **Organism**: Salmonella enterica
- **Size**: Small test genome (~50-100 contigs)
- **Expected AMR genes**: 2-5 resistance genes
- **Expected phages**: 0-2 prophages

### test_genome2.fasta
- **Organism**: Escherichia coli
- **Size**: Small test genome (~50-100 contigs)
- **Expected AMR genes**: 1-3 resistance genes
- **Expected phages**: 0-2 prophages

## Creating Test Genomes

If you need to replace the test genomes, you can download small assemblies from NCBI:

```bash
# Example: Download a small Salmonella genome
datasets download genome accession GCF_000006945.2 \
    --include genome \
    --filename test_genome1.zip

unzip test_genome1.zip
mv ncbi_dataset/data/GCF_000006945.2/*.fna test_genome1.fasta
```

Or use synthetic/simulated genomes for truly minimal test data.

## Customizing Test Parameters

Edit `conf/test.config` to modify:
- Resource allocations (CPUs, memory, time)
- Database paths
- Output directory
- Container engine (Docker vs Apptainer)

## Troubleshooting Test Runs

### Test fails with "command not found"
- Check that Nextflow is installed: `nextflow -version`
- Check that container engine is available: `apptainer --version` or `docker --version`

### Database download fails
- Check internet connectivity
- Try pre-downloading databases manually (see `docs/DATABASE_SETUP.md`)
- Set database paths in `conf/test.config`

### Out of memory errors
- Increase memory in `conf/test.config`
- Check available system resources
- Use smaller test genomes

### Container pull fails
- Check container cache directory permissions
- Clear cache: `rm -rf ~/.apptainer/cache`
- Try different container mirror

## CI/CD Integration

This test profile is designed for continuous integration testing:

```yaml
# Example GitHub Actions workflow
name: Test Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Nextflow
        run: curl -s https://get.nextflow.io | bash
      - name: Run Test
        run: ./nextflow run main.nf -profile test,docker
```

## Validation

The test run validates:
- ✅ All pipeline processes execute successfully
- ✅ Container images are accessible
- ✅ Database downloads work (if applicable)
- ✅ AMR detection produces results
- ✅ Phage identification runs
- ✅ Summary report is generated
- ✅ No critical errors or warnings

## Performance Benchmarking

Use the test profile for benchmarking:

```bash
# Run with different executors
nextflow run main.nf -profile test  # local
nextflow run main.nf -profile test,beocat  # SLURM

# Compare execution times
grep "Duration" test_results/pipeline_info/execution_trace_test.txt
```

## Support

If the test run fails, please:
1. Check the execution trace: `test_results/pipeline_info/execution_trace_test.txt`
2. Review error logs in `.nextflow.log`
3. Open an issue at: https://github.com/tdoerks/COMPASS-pipeline/issues

Include:
- Nextflow version
- Container engine and version
- Operating system
- Full error message
- Execution trace file
