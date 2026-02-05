# Validation Pipeline Status - February 5, 2026

## Summary

Attempted to implement assembly download mode for validation pipeline. Hit container compatibility issues with Singularity/Apptainer on Beocat HPC.

## What We Accomplished

✅ **Assembly Download Mode Created**:
- New module: `modules/download_assembly.nf`
- New input mode: `--input_mode assembly`
- Integration into `workflows/complete_pipeline.nf`
- SLURM script: `data/validation/run_compass_validation.sh`

✅ **Validation Dataset Prepared**:
- 170 E. coli reference genomes in `data/validation/validation_samplesheet.csv`
- Tier 1 & 2: 14 core references (EC958, JJ1886, ETEC, K-12)
- Tier 3: 50 FDA-ARGOS genomes
- Tier 4: 100 diverse complete genomes
- Tier 5: 6 sequence type representatives

✅ **Python Script for Accession Collection**:
- `data/validation/get_validation_accessions.py`
- Programmatically queries NCBI Assembly database
- Successfully collected 156 new accessions (50+100+6)

## Current Blocker

❌ **Container Bash Compatibility Issue**:

**Problem**: All tested containers fail with `FATAL: stat /bin/bash: no such file or directory`

**Root Cause**: Beocat's Singularity/Apptainer expects `/bin/bash` but minimal containers only have `/bin/sh`

**Containers Tested**:
1. `quay.io/biocontainers/entrez-direct:16.2--he881be0_1` - Missing Perl Time::HiRes module
2. `ubuntu:22.04` - Read-only filesystem prevents package installation
3. `curlimages/curl:8.5.0` - No bash, only sh
4. `alpine:3.19` - No bash (exit code 255)
5. `biocontainers/biocontainers:v1.2.0_cv2` - Still failing with bash error

**Why This Is Hard**:
- Container filesystem is read-only in Singularity
- Can't install missing tools at runtime
- Need container with bash + wget/curl + gunzip pre-installed
- Minimal containers prioritize small size over compatibility

## Alternative Approaches to Consider

### Option 1: Manual Download + FASTA Mode ⭐ RECOMMENDED
**Approach**: Download assemblies manually using NCBI Datasets CLI on Beocat, then run pipeline with `--input_mode fasta`

**Steps**:
```bash
# On Beocat (outside container)
module load datasets  # if available
# OR use standalone binary in ~/bin

# Download all 170 assemblies
cd /fastscratch/tylerdoe/COMPASS-pipeline/data/validation
bash download_genomes.sh  # Uses datasets CLI

# Generate samplesheet with local paths
python create_samplesheet.py

# Run pipeline in fasta mode
sbatch run_compass_validation.sh  # Change --input_mode to fasta
```

**Pros**:
- Avoids container issues entirely
- Downloads happen once, reusable
- Can resume if network fails
- Proven workflow (like your FASTA runs)

**Cons**:
- Manual pre-download step
- Requires ~2-4 hours download time
- Takes up fastscratch space

### Option 2: Use Conda Instead of Containers
**Approach**: Install wget/curl via conda in process, bypass containers

**Changes Needed**:
- Add conda directive to DOWNLOAD_ASSEMBLY process
- Use `-profile conda` instead of `-profile beocat`

**Pros**:
- Conda can install tools at runtime
- No container compatibility issues

**Cons**:
- Slower (conda solves environment each time)
- Requires conda on HPC
- Different from rest of pipeline

### Option 3: Find/Build Compatible Container
**Approach**: Search for or build a container with bash + wget + gunzip

**Options**:
- Try `debian:stable-slim` or `ubuntu:20.04`
- Build custom Docker image, push to Docker Hub
- Use older BioContainer base

**Pros**:
- Maintains containerized approach
- Reusable for future

**Cons**:
- Time-consuming to test/build
- May hit same issues

### Option 4: Use Beocat Native Tools
**Approach**: Don't use containers for download step

**Changes Needed**:
```nextflow
process DOWNLOAD_ASSEMBLY {
    // Remove container directive entirely
    // Uses host's wget/curl
```

**Pros**:
- Guaranteed to work
- Uses Beocat's native tools

**Cons**:
- Breaks container isolation
- May not be allowed by HPC policy

## Recommended Path Forward

**Short-term (Tonight)**:
1. Restart E. coli Monthly 100 run (proven workflow)
2. Let validation wait until we have time to troubleshoot

**Medium-term (Next Session)**:
1. Use **Option 1** (manual download + FASTA mode)
2. Modify `run_compass_validation.sh` to use `--input_mode fasta`
3. Run validation with pre-downloaded assemblies
4. This will work 100% - same as your other runs

**Long-term (Future Improvement)**:
1. Build custom Docker image with all needed tools
2. Push to Docker Hub or Quay.io
3. Update DOWNLOAD_ASSEMBLY to use custom image
4. Contributes back to community

## Current E. coli Monthly 100 Status

- **Job**: 6227332 (cancelled to attempt validation)
- **Progress**: ~94.9% SRA download, 87.6% analysis complete
- **Samples**: 7,142 total
- **Recommendation**: Resume tonight with `-resume`

## Files Ready for Validation (When Container Fixed)

All code is committed to v1.3-dev branch:
- `modules/download_assembly.nf` - Download module (needs container fix)
- `data/validation/validation_samplesheet.csv` - 170 genomes
- `data/validation/get_validation_accessions.py` - Accession collector
- `data/validation/run_compass_validation.sh` - SLURM script
- `workflows/complete_pipeline.nf` - Integration complete
- `main.nf` - Assembly mode parsing

## Next Steps

1. **Tonight**: Restart E. coli Monthly 100 (`sbatch run_ecoli_monthly_100_2020-2026.sh`)

2. **Next Session**:
   - Decide on container approach vs manual download
   - If manual: run `download_genomes.sh`, switch to fasta mode
   - If container: continue debugging or build custom image

3. **After Validation Completes**:
   - Ground truth curation (manual)
   - Validation analysis script
   - Calculate sensitivity/specificity
   - Update Paper 1 Methods

## Commits Made This Session

1. `34c08ba` - Add assembly download mode for validation pipeline
2. `841e327` - Expand validation samplesheet to 170 E. coli reference genomes
3. `94e6fba` - Add session notes for assembly download mode implementation
4. `51f4c74` - Fix validation SLURM script module loading for Beocat
5. `dac279b` - Fix assembly download using curl instead of broken entrez-direct
6. `509d321` - Use curlimages/curl container with pre-installed curl
7. `066a6a3` - Use alpine container with wget for assembly downloads
8. `df20298` - Use biocontainers base image with bash support

All pushed to `v1.3-dev` branch.

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu
Kansas State University

---

**Status**: Assembly download blocked by container issues
**Recommendation**: Use manual download + FASTA mode for validation
**Priority**: Resume E. coli Monthly 100 run tonight
