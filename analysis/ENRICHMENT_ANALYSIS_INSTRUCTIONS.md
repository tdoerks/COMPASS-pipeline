# AMR Gene Enrichment Analysis Instructions

## Purpose
Analyze which AMR genes show significant enrichment on prophage-containing contigs compared to background rates.

## Script Location
`bin/analyze_enriched_amr_genes.py`

## Usage

### On Beocat (recommended)
Connect to Beocat and run the enrichment analysis on the Kansas combined results:

```bash
# Navigate to COMPASS directory
cd /bulk/tylerdoe/compass_pipeline

# Run enrichment analysis on Kansas multi-year data
python3 bin/analyze_enriched_amr_genes.py /bulk/tylerdoe/kansas_results

# The script will auto-detect year directories (2021/, 2022/, 2023/, etc.)
# and combine data from all years
```

### Output Files

The script generates two CSV files in the base directory:

1. **`amr_enrichment_analysis.csv`**
   - All AMR genes with ≥10 total occurrences
   - Columns: gene, total_occurrences, on_prophage_contig, pct_on_prophage, num_samples, etc.
   - Sorted by % on prophage (descending)

2. **`highly_enriched_amr_occurrences.csv`**
   - Individual occurrences of genes with >30% enrichment on prophage contigs
   - Includes sample_id, gene, class, contig, coordinates, organism, source, prophage quality/type
   - Useful for detailed investigation of specific highly enriched genes

### Terminal Output

The script prints:

1. **Top enriched AMR genes** (≥10 occurrences)
   - Shows gene name, total count, count on prophage contigs, %, samples, top source, top organism

2. **Drug class enrichment** (≥10 occurrences per class)
   - Shows which antimicrobial resistance classes are most enriched on prophage contigs

3. **Highly enriched genes list** (>30% on prophage contigs)
   - Quick summary of genes with strong prophage association

## Expected Findings (based on deep dive analysis)

From preliminary Kansas data analysis, we expect to see:

### Top enriched genes (>30% on prophage contigs):
- **dfrA51** (trimethoprim): ~83% on prophage contigs
- **glpT_E448K** (fosfomycin): ~35% on prophage contigs
- **fosA7** (fosfomycin): Likely high enrichment
- **mdsA, mdsB** (multidrug): Often co-occur on same prophage contig

### Top enriched drug classes:
- **FOSFOMYCIN**: ~32% on prophage contigs
- **TRIMETHOPRIM**: High due to dfrA51
- **MULTIDRUG**: mdsA/mdsB family genes

### Source patterns:
- **Ground Beef**: Highest % AMR on prophage contigs (~13.4%)
- **Ground Turkey**: Also elevated

### Temporal patterns:
- **2021**: Highest % AMR on prophage contigs (17.7%)
- Decreasing trend through 2025 (7.6%)

## Follow-up Analysis Ideas

Once you have the enrichment results:

1. **Investigate dfrA51**: Why is this trimethoprim resistance gene so highly enriched (83%) on prophage contigs?
   - Check if it's always integrated at same location
   - Look for specific prophage types carrying it
   - Geographic/temporal patterns

2. **Explore mdsA+mdsB co-occurrence**: These multidrug efflux genes co-occur 18 times on same prophage contig
   - Are they part of a composite transposon?
   - Always on same prophage type?
   - Associated with specific Salmonella serotypes?

3. **FOSFOMYCIN class enrichment**: Why is this class (32%) enriched on prophage contigs?
   - Multiple genes: glpT, fosA7, uhpT
   - Do they share prophage integration sites?
   - Clinical significance?

4. **Ground Beef signal**: Why does Ground Beef show highest % AMR on prophage contigs?
   - Processing differences?
   - Different bacterial populations?
   - Specific Salmonella serotypes more common?

5. **2021 temporal peak**: Why is 2021 highest year (17.7%) for AMR on prophage contigs?
   - Sample size effect?
   - Actual biological shift in AMR-prophage associations?
   - Geographic sampling differences?

## Script Features

- **Multi-year support**: Auto-detects year directories and combines all data
- **Minimum occurrence filter**: Only analyzes genes with ≥10 total occurrences (adjustable in code)
- **Source extraction**: Parses NARMS sample names to extract food source (GT=Ground Turkey, etc.)
- **Comprehensive statistics**: Gene-level and drug class-level enrichment
- **Detailed exports**: Both summary and individual occurrence CSVs for deep diving

## Example Run

```bash
$ python3 bin/analyze_enriched_amr_genes.py /bulk/tylerdoe/kansas_results

📅 Detected multi-year directory structure with 5 year directories
  Loading 2021...
  Loading 2022...
  Loading 2023...
  Loading 2024...
  Loading 2025...
✅ Loaded 4339 AMR genes from 788 samples with prophages

🔬 Calculating enrichment statistics...

====================================================================================================
🧬 TOP AMR GENES ENRICHED ON PROPHAGE-CONTAINING CONTIGS (≥10 total occurrences)
====================================================================================================
Gene                 Total    On Phage   % On Phage   Samples    Top Source           Top Organism
----------------------------------------------------------------------------------------------------
dfrA51               12       10         83.3         12         Ground Turkey        Salmonella enterica
glpT_E448K           436      151        34.6         436        Ground Turkey        Salmonella enterica
fosA7                89       28         31.5         89         Ground Turkey        Salmonella enterica
...

====================================================================================================
💊 DRUG CLASS ENRICHMENT ON PROPHAGE-CONTAINING CONTIGS (≥10 total occurrences)
====================================================================================================
Drug Class                     Total    On Phage   % On Phage
----------------------------------------------------------------------------------------------------
FOSFOMYCIN                     505      162        32.1
TRIMETHOPRIM                   15       11         73.3
...

🎯 Found 3 highly enriched genes (>30% on prophage contigs, ≥10 occurrences)
  dfrA51: 83.3% (10/12)
  glpT_E448K: 34.6% (151/436)
  fosA7: 31.5% (28/89)

✅ Exported detailed enrichment analysis to: /bulk/tylerdoe/kansas_results/amr_enrichment_analysis.csv
✅ Exported 189 individual occurrences to: /bulk/tylerdoe/kansas_results/highly_enriched_amr_occurrences.csv
```

## Integration with Other Analyses

This enrichment analysis complements:

1. **`comprehensive_amr_analysis.py`**: Broad overview of AMR-phage patterns
2. **`dig_amr_prophage_contigs.py`**: Deep dive into specific AMR-prophage contig overlaps
3. **`analyze_amr_mobile_elements.py`**: Plasmid and mobile element associations

Together, these scripts provide a complete picture of:
- Physical co-location (same contig)
- Mobile element associations (plasmids, transposons)
- Statistical enrichment (which genes show strongest prophage association)
- Sample-level and organism-level patterns
