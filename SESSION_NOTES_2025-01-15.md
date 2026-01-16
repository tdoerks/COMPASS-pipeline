# Session Notes - January 15, 2025

## Status: In Progress - Fixing Container Issue for Prophage AMR Script

### What We're Working On
Created a new script to run AMRFinderPlus directly on prophage DNA sequences to definitively answer: **Do prophages carry AMR genes?**

### Problem We're Solving Right Now
The script `bin/run_amrfinder_on_prophages.py` is trying to use Apptainer to run AMRFinderPlus, but encountering a container image format issue.

**Error Message**:
```
⚠️  AMRFinder failed: FATAL:   While checking container encryption:
could not open image /fastscratch/tylerdoe/COMPASS-pipeline/quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0:
failed to retrieve path for /fast
```

**Root Cause**:
- Script is passing a Docker image path (`quay.io/biocontainers/...`) to Apptainer
- Apptainer needs either:
  1. A `.sif` file (Singularity Image Format)
  2. A `docker://` prefix to pull from Docker Hub

### What We Need to Do Next

#### Option 1: Find Existing Container Cache (RECOMMENDED)
Nextflow has already pulled this container when running the pipeline. Find where it's cached:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Find cached container images
find work -name "*amrfinder*.sif" 2>/dev/null | head -3
find work_5sample_test -name "*.sif" 2>/dev/null | head -3

# Check Apptainer cache directories
ls ~/.apptainer/cache/
echo $APPTAINER_CACHEDIR
echo $SINGULARITY_CACHEDIR

# Look in Nextflow work directories
find . -name "*.sif" 2>/dev/null | grep -i amr
```

Once found, update the script to use the `.sif` file path.

#### Option 2: Add docker:// Prefix
Modify the script to use `docker://quay.io/biocontainers/...` which tells Apptainer to pull from Docker registry.

**Update this line in `bin/run_amrfinder_on_prophages.py`**:
```python
# Current (line 82):
container = 'quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0'

# Change to:
container = 'docker://quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0'
```

### Files Created This Session

1. **`bin/run_amrfinder_on_prophages.py`** ✅ (needs container fix)
   - Direct AMRFinder scan on prophage sequences
   - Most definitive method to find AMR genes in prophages
   - Currently fails on container image loading

2. **`PROPHAGE_AMR_ANALYSIS_GUIDE.md`** ✅
   - Complete user guide for all 3 analysis methods
   - Usage examples and interpretation

3. **`AMR_IN_VIBRANT_SEARCH.md`** ✅ (updated)
   - Technical documentation for all methods
   - Now documents all 3 approaches

### Three Analysis Methods Summary

| Method | Script | Status | Speed | Best For |
|--------|--------|--------|-------|----------|
| 1. Coordinate | `analyze_true_amr_prophage_colocation.py` | ✅ Working | Fast (seconds) | Quick overview |
| 2. Annotation | `search_amr_in_vibrant_annotations.py` | ✅ Working | Fast | Troubleshooting |
| 3. Direct Scan | `run_amrfinder_on_prophages.py` | 🔧 Fixing container | Slow (1-2 min/sample) | Definitive answer |

### Current Test Sample
- **Sample ID**: SRR13928113
- **Whole-genome AMR**: 4 genes (mdtM, glpT_E448K, blaEC, acrF)
- **Prophages identified**: 5 regions
- **Status**: Waiting to run AMRFinder on prophage sequences

### System Info
- **HPC**: Beocat (Kansas State University)
- **Container runtime**: Apptainer installed at `/usr/bin/apptainer`
- **Working directory**: `/fastscratch/tylerdoe/COMPASS-pipeline`
- **Results directory**: `/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod`

### Git Status
- **Branch**: `v1.2-mod`
- **Last commits**:
  - `03ebf50` - Fix AMRFinder script to use Apptainer container on HPC
  - `f99791c` - Add comprehensive prophage AMR analysis guide
  - `3777d85` - Add direct AMRFinder scan on prophage sequences

### Next Steps (In Order)

1. **Find container cache location** (run commands above)
2. **Fix container path** in script:
   - Either: Use existing `.sif` file from cache
   - Or: Add `docker://` prefix to pull image
3. **Test script** on single sample:
   ```bash
   ./bin/run_amrfinder_on_prophages.py \
       /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
       SRR13928113
   ```
4. **Interpret results**:
   - If AMR genes found → Prophages DO carry resistance
   - If 0 genes found → Prophages DON'T carry resistance
5. **Scale up** if interesting results found

### Quick Fix to Try First

**Edit `bin/run_amrfinder_on_prophages.py` line 82:**

```python
# Change:
container = 'quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0'

# To:
container = 'docker://quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0'
```

Then test again. This tells Apptainer to pull from Docker registry.

### Alternative: Use Nextflow to Run AMRFinder

If container issues persist, we could:
1. Create a small Nextflow process that runs AMRFinder
2. Leverage Nextflow's container management
3. Let Nextflow handle all the container details

### Background Context

**Why this analysis matters**:
- Prophages are mobile genetic elements
- If AMR genes exist in prophages, they can spread via phage infection
- Previous coordinate-based method found **0 co-locations**
- Need to verify with direct AMR scanning to be sure

**What we've ruled out**:
- ✅ AMR genes and prophages are on different contigs (coordinate analysis)
- ✅ VIBRANT doesn't use AMR gene names in annotations (keyword search)
- ⏳ **Still need**: Direct AMRFinder scan on prophage DNA (definitive answer)

### Files Modified But Not Committed

None - all changes have been committed and pushed.

### Commands User Should Try Next

```bash
# 1. Find where containers are cached
cd /fastscratch/tylerdoe/COMPASS-pipeline
find work -name "*amrfinder*.sif" 2>/dev/null | head -5

# 2. Quick fix: Add docker:// prefix
sed -i "s|container = 'quay.io|container = 'docker://quay.io|" bin/run_amrfinder_on_prophages.py

# 3. Test again
./bin/run_amrfinder_on_prophages.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
    SRR13928113

# 4. If that works, commit the fix
git add bin/run_amrfinder_on_prophages.py
git commit -m "Add docker:// prefix to container image path"
git push origin v1.2-mod
```

### Expected Output When Working

```
================================================================================
ANALYZING SAMPLE: SRR13928113
================================================================================

  📊 Whole-genome AMRFinder: 4 AMR genes detected
     Sample genes: mdtM, glpT_E448K, blaEC, acrF

  🦠 VIBRANT identified 5 prophage/phage regions

  🔍 Running AMRFinderPlus on prophage sequences...
     (Using Apptainer container - this may take 1-2 minutes)

  ✅ AMRFinder on prophage DNA: 1 AMR genes detected

  🎯 AMR GENES FOUND IN PROPHAGES:
     • tet(A) (TETRACYCLINE) - BLAST

  📊 COMPARISON:
     Whole genome: 4 AMR genes
     Prophage DNA: 1 AMR genes
     Prophage carries 25.0% of total AMR genes
```

---

## Previous Session Summary

We created three complementary methods to find AMR genes in prophages:

1. **Coordinate-based** (fast) - Check if AMR gene coordinates overlap prophage boundaries
2. **Annotation search** (troubleshooting) - Search VIBRANT files for AMR gene names
3. **Direct scan** (definitive) - Run AMRFinderPlus on extracted prophage sequences

Method 1 and 2 both returned 0 results. Method 3 is the most direct and will give us the definitive biological answer, but we need to fix the container issue first.

---

**Last Updated**: January 15, 2025
**Current Status**: 🔧 Fixing Apptainer container image loading issue
**Ready to Resume**: Yes - see "Commands User Should Try Next" above
