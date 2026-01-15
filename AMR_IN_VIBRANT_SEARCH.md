# Searching for AMR Genes in VIBRANT Prophage Annotations

## Three Complementary Approaches

We have three different methods to find AMR genes in prophages:

### 1. Coordinate-Based Method (`analyze_true_amr_prophage_colocation.py`)
- Parses AMRFinderPlus coordinates (contig, start, end)
- Parses VIBRANT prophage coordinates (contig, start, end)
- Checks if AMR gene coordinates fall within prophage boundaries
- **Pro**: Precise physical co-location
- **Con**: Requires exact contig name matching

### 2. Annotation-Based Method (`search_amr_in_vibrant_annotations.py`)
- Gets AMR gene names from AMRFinderPlus
- Searches VIBRANT's annotation files for those gene names
- If VIBRANT annotated the same gene in a prophage → it's co-located!
- **Pro**: Uses VIBRANT's own gene annotations
- **Con**: Relies on consistent gene naming (VIBRANT uses VOG/KEGG IDs, not AMR gene names)

### 3. Direct AMRFinder Scan ⭐ **RECOMMENDED** (`run_amrfinder_on_prophages.py`)
- Extracts prophage sequences identified by VIBRANT
- Runs AMRFinderPlus **directly on prophage DNA**
- Most definitive approach - uses AMR-specific tool on phage-specific sequences
- **Pro**: Definitive answer - does prophage DNA contain AMR genes?
- **Con**: Computationally expensive (~1-2 minutes per sample)

## Which Method Should I Use?

### For Most Users: Method 3 (Direct AMRFinder Scan) ⭐
**Use this when**: You want a definitive answer about AMR genes in prophages
```bash
# Test single sample first (takes 1-2 minutes)
./bin/run_amrfinder_on_prophages.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
    SRR13928113
```

**Why this is best**:
- Most direct: Scans prophage DNA with AMR detection tool
- No coordinate matching issues
- No annotation format dependencies
- Definitive biological answer

**Limitation**: Slow for large datasets (1-2 min per sample)

### For Quick Analysis: Method 1 (Coordinate-Based)
**Use this when**: You need results across many samples quickly
```bash
./bin/analyze_true_amr_prophage_colocation.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod
```

**Why use this**:
- Very fast (seconds for hundreds of samples)
- Uses existing AMRFinder results
- No re-computation needed

**Limitation**: Requires coordinate matching (may miss edge cases)

### For Troubleshooting: Method 2 (Annotation Search)
**Use this when**: Method 1 returns 0 but you suspect AMR genes exist
- Helps diagnose if issue is annotation format vs. true negative
- **Note**: Generally returns 0 because VIBRANT doesn't use AMR gene names

## Usage Examples

### Method 3: Direct AMRFinder Scan (Recommended)

#### Test Single Sample
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Test on one sample
./bin/run_amrfinder_on_prophages.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
    SRR13928113
```

#### Run on All Samples (WARNING: Takes hours!)
```bash
# This will run AMRFinderPlus on every sample's prophage sequences
# Expect ~1-2 minutes per sample
./bin/run_amrfinder_on_prophages.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod
```

### Method 1: Coordinate-Based (Fast)
```bash
# Single sample
./bin/analyze_true_amr_prophage_colocation.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod

# Outputs CSV + HTML report
```

### Method 2: Annotation Search (For troubleshooting)
```bash
# Single sample
./bin/search_amr_in_vibrant_annotations.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
    SRR13928113
```

## Output Examples

### Method 3: Direct AMRFinder Scan Output
```
================================================================================
ANALYZING SAMPLE: SRR13928113
================================================================================

  📊 Whole-genome AMRFinder: 4 AMR genes detected
     Sample genes: mdtM, aac(3)-IId, tet(A), blaCTX-M-15

  🦠 VIBRANT identified 8 prophage/phage regions
     Prophage sequences: /path/to/SRR13928113_phages.fna

  🔍 Running AMRFinderPlus on prophage sequences...
     (This may take 1-2 minutes per sample)

  ✅ AMRFinder on prophage DNA: 1 AMR genes detected

  🎯 AMR GENES FOUND IN PROPHAGES:
     • tet(A) (TETRACYCLINE) - BLAST

  📊 COMPARISON:
     Whole genome: 4 AMR genes
     Prophage DNA: 1 AMR genes
     Prophage carries 25.0% of total AMR genes
```

### CSV Export
**Method 3**: `~/prophage_amr_direct_scan.csv`
- `sample`: Sample ID
- `gene`: AMR gene name detected in prophage
- `class`: Drug class
- `method`: Detection method (BLAST/HMM)
- `prophage_contig`: Prophage sequence ID
- `whole_genome_amr_count`: Total AMR genes in whole genome
- `prophage_count`: Number of prophages identified

**Method 1**: `~/true_amr_prophage_colocation.csv` + HTML report
- Detailed coordinate-based co-location results

**Method 2**: `~/amr_in_vibrant_annotations.csv`
- Gene name search results (typically empty)

## Interpreting Results

### Scenario 1: Direct Scan (Method 3) Finds AMR Genes in Prophages
**Result**: `AMRFinder on prophage DNA: 5 AMR genes detected`

**Interpretation**: ✅ **Definitive positive** - Prophages DO carry AMR genes
- AMR detection tool found resistance genes when scanning prophage DNA directly
- These genes are potentially mobile with the prophage
- High confidence result

**Next steps**:
- Examine which AMR genes are in prophages
- Analyze drug classes affected
- Consider temporal/geographic trends

### Scenario 2: All Methods Find 0 Co-locations
**Result**: All three methods return 0 AMR genes in prophages

**Interpretation**: ✅ **Definitive negative** - Prophages don't carry AMR genes
- Coordinate matching found no overlap
- Direct AMR scanning found nothing in prophage DNA
- Real biological finding for this dataset

**Biological implications**:
- AMR genes in this dataset are chromosomal, not prophage-mediated
- Resistance spread likely via other mechanisms (plasmids, conjugation)
- Still scientifically valuable finding!

### Scenario 3: Method 1 = 0, Method 3 > 0
**Result**: Coordinate method found 0, but direct scan found AMR genes

**Interpretation**: ⚠️ **Technical issue with coordinate matching**
- AMR genes ARE in prophages (confirmed by Method 3)
- Coordinate-based method missed them due to:
  - Contig naming differences
  - Coordinate system issues
  - Edge cases in boundary detection

**Action**: Use Method 3 results as definitive answer

### Scenario 4: Method 1 > 0, Method 3 = 0
**Result**: Coordinate method found co-locations, but direct scan found nothing

**Interpretation**: ⚠️ **Rare - likely false positives in coordinate matching**
- Direct scan is more definitive
- May indicate annotation artifacts
- Use Method 3 results as final answer

## Recommendation: Start with Method 3

For new analyses, we recommend:
1. **Test Method 3 on a few samples first** (5-10 samples)
2. If you find AMR genes in prophages → Great! Run on more samples
3. If you find 0 AMR genes → Confirms Method 1 result, true negative
4. Method 3 gives most confidence in your conclusions

## Files

- `bin/run_amrfinder_on_prophages.py` - **Direct AMRFinder scan (RECOMMENDED)**
- `bin/analyze_true_amr_prophage_colocation.py` - Coordinate-based method (fast)
- `bin/search_amr_in_vibrant_annotations.py` - Annotation search (troubleshooting)
- `bin/search_amr_keywords_in_vibrant.py` - Keyword search (troubleshooting)
- `bin/debug_colocation.py` - Debugging tool

---

**Created**: January 2026
**Purpose**: Complement coordinate-based AMR-prophage analysis with gene name searching
