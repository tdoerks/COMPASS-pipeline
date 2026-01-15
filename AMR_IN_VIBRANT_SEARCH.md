# Searching for AMR Genes in VIBRANT Prophage Annotations

## Two Complementary Approaches

We have two different methods to find AMR genes in prophages:

### 1. Coordinate-Based Method (`analyze_true_amr_prophage_colocation.py`)
- Parses AMRFinderPlus coordinates (contig, start, end)
- Parses VIBRANT prophage coordinates (contig, start, end)
- Checks if AMR gene coordinates fall within prophage boundaries
- **Pro**: Precise physical co-location
- **Con**: Requires exact contig name matching

### 2. Annotation-Based Method (`search_amr_in_vibrant_annotations.py`) ⭐ **NEW**
- Gets AMR gene names from AMRFinderPlus
- Searches VIBRANT's annotation files for those gene names
- If VIBRANT annotated the same gene in a prophage → it's co-located!
- **Pro**: Uses VIBRANT's own gene annotations
- **Con**: Relies on consistent gene naming

## Why Use the Annotation-Based Method?

If the coordinate-based method returns 0 results, the annotation-based method can help determine:

1. **True negative**: AMR genes are truly not in prophages (both methods return 0)
2. **Naming mismatch**: AMR genes ARE in prophages but coordinate matching failed (annotation method finds them)
3. **Different annotation**: VIBRANT detected the genes but named them differently

## Usage

### Test Single Sample
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Test on one sample
./bin/search_amr_in_vibrant_annotations.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
    SRR13928113
```

### Search All Samples
```bash
# Search all samples in the results directory
./bin/search_amr_in_vibrant_annotations.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod
```

This will:
1. Find all samples with AMR results
2. Extract AMR gene names (mdtM, tet(A), etc.)
3. Search VIBRANT annotation files for those genes
4. Report matches

## Output

### Console Output
```
================================================================================
ANALYZING SAMPLE: SRR13928113
================================================================================
  Found 4 AMR genes in AMRFinderPlus results:
    - mdtM (EFFLUX)
    - aac(3)-IId (AMINOGLYCOSIDE)
    - tet(A) (TETRACYCLINE)
    - blaCTX-M-15 (BETA-LACTAM)

  Searching VIBRANT annotations for these genes...
  Searching 47 VIBRANT annotation files...
    ✓ Found 'tet(A)' in VIBRANT_annotations_SRR13928113_contigs.tsv
    ✓ Found 'tet(A)' in VIBRANT_phages_SRR13928113_contigs.fasta

  ✅ Found 2 matches in VIBRANT annotations!
```

### CSV Export
File: `~/amr_in_vibrant_annotations.csv`

Columns:
- `sample`: Sample ID
- `gene`: AMR gene name
- `class`: Drug class (from AMRFinderPlus)
- `file`: VIBRANT file where gene was found
- `prophage_id`: Prophage/phage ID
- `amr_contig`: Original contig from AMRFinderPlus
- `amr_start`, `amr_end`: Coordinates from AMRFinderPlus
- `file_path`: Full path to VIBRANT file

## Interpreting Results

### Scenario 1: Both Methods Find 0 Co-locations
**Interpretation**: AMR genes are truly not located in prophage regions in this dataset
**Conclusion**: Real biological result - prophages don't carry AMR genes here

### Scenario 2: Coordinate Method = 0, Annotation Method > 0
**Interpretation**: AMR genes ARE in prophages, but coordinate matching failed
**Possible causes**:
- Contig names don't match between AMRFinder and VIBRANT
- Different coordinate systems
- Different assembly versions

**Action**: Investigate contig naming and coordinate systems

### Scenario 3: Both Methods Find Co-locations
**Interpretation**: High confidence - AMR genes confirmed in prophages by both methods
**Conclusion**: Strong evidence of prophage-mediated AMR gene mobility

## Next Steps

After running both scripts:

1. **Compare results**: How many samples show co-location in each method?
2. **Investigate discrepancies**: If results differ, check contig naming
3. **Biological interpretation**: What does it mean if prophages don't carry AMR?

## Files

- `bin/analyze_true_amr_prophage_colocation.py` - Coordinate-based method
- `bin/search_amr_in_vibrant_annotations.py` - Annotation-based method (NEW)
- `bin/debug_colocation.py` - Troubleshooting tool

---

**Created**: January 2026
**Purpose**: Complement coordinate-based AMR-prophage analysis with gene name searching
