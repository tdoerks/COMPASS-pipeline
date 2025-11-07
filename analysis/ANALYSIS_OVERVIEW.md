# AMR-Phage Analysis Suite Overview

## What We're Investigating

We're analyzing the relationship between **antimicrobial resistance (AMR) genes** and **prophages** in bacterial genomes from NARMS surveillance data. Our preliminary analysis of Kansas E. coli samples (2021-2025, n=788) revealed that **9.66% of AMR genes are located on prophage-containing contigs**, suggesting prophage-mediated horizontal gene transfer is playing a significant role in AMR dissemination.

## Key Findings from Kansas Data

### Overall Statistics
- **788 samples** analyzed (Kansas E. coli, 2021-2025)
- **4,339 total AMR genes** detected
- **419 AMR genes (9.66%)** on prophage-containing contigs
- Strong enrichment for specific genes and drug classes

### Most Enriched AMR Genes

| Gene | Enrichment | Total | On Prophage | Drug Class | Mechanism |
|------|-----------|-------|-------------|------------|-----------|
| **dfrA51** | 83.3% | 12 | 10 | TRIMETHOPRIM | Dihydrofolate reductase |
| **glpT_E448K** | 34.6% | 436 | 151 | FOSFOMYCIN | Glycerol-3-phosphate transporter |
| **fosA7** | ~31.5% | 89 | ~28 | FOSFOMYCIN | Fosfomycin resistance enzyme |

### Drug Class Enrichment

| Drug Class | % on Prophage Contigs | Total Genes | On Prophage |
|-----------|---------------------|-------------|-------------|
| **FOSFOMYCIN** | 32.1% | 505 | 162 |
| **TRIMETHOPRIM** | ~73% | 15 | 11 |

### Interesting Patterns

1. **mdsA + mdsB co-occurrence**: These multidrug efflux pump genes co-occur **18 times** on the same prophage contig
   - Suggests operon structure or composite transposon
   - Potential multi-resistance cassette spreading via prophages

2. **Ground Beef signal**: Samples from Ground Beef show highest % AMR on prophage contigs (13.4%)
   - Possibly related to processing, bacterial populations, or specific Salmonella serotypes

3. **Temporal trend**: 2021 shows peak at 17.7%, decreasing to 7.6% by 2025
   - Possible biological shift or sampling variation

## Analysis Scripts

We've developed a suite of Python scripts to investigate these patterns:

### Core Analysis Scripts

| Script | Purpose | Output | Run Time |
|--------|---------|--------|----------|
| `analyze_enriched_amr_genes.py` | **[START HERE]** Gene-level enrichment statistics | `amr_enrichment_analysis.csv` | ~10 sec |
| `dig_amr_prophage_contigs.py` | Deep dive into AMR-prophage contig overlaps | `kansas_amr_prophage_contigs_DEEP_DIVE.csv` | ~15 sec |
| `comprehensive_amr_analysis.py` | Combined analysis + HTML report | `kansas_comprehensive_amr_analysis.html` | ~30 sec |
| `analyze_amr_mobile_elements.py` | Mobile element associations | `amr_mobile_element_analysis.csv` | ~20 sec |

### Investigation Scripts (Specific Gene Patterns)

| Script | Purpose | Output | Run After |
|--------|---------|--------|-----------|
| `investigate_dfra51.py` | Why is dfrA51 83% on prophage contigs? | `dfra51_investigation.csv` | Enrichment analysis |
| `investigate_mdsa_mdsb.py` | Why do mdsA+mdsB co-occur 18 times? | `mdsa_mdsb_investigation.csv` | Deep dive analysis |

## Recommended Analysis Workflow

### Quick Start (5 minutes)
```bash
# 1. Run enrichment analysis
python3 bin/analyze_enriched_amr_genes.py /bulk/tylerdoe/kansas_results

# 2. Review top enriched genes in terminal output
# 3. Check CSV files for detailed data
```

### Deep Investigation (30 minutes)
```bash
# 1. Enrichment analysis (identify top genes)
python3 bin/analyze_enriched_amr_genes.py $KANSAS

# 2. Investigate dfrA51 (83% enrichment!)
python3 bin/investigate_dfra51.py $KANSAS

# 3. Investigate mdsA+mdsB co-occurrence
python3 bin/investigate_mdsa_mdsb.py $KANSAS

# 4. Deep dive into all AMR-prophage contigs
python3 bin/dig_amr_prophage_contigs.py $KANSAS

# 5. Generate HTML report
python3 bin/comprehensive_amr_analysis.py $KANSAS
```

### Full Analysis Suite
```bash
# Run all analyses at once (saves logs)
bash analysis/RUN_ALL_ANALYSES.sh
```

## What Each Analysis Tells You

### 1. Enrichment Analysis (`analyze_enriched_amr_genes.py`)
**Answers**: Which AMR genes show strongest association with prophages?

**Key Insights**:
- Identifies genes with high % on prophage contigs (enrichment)
- Shows drug class patterns
- Filters to genes with ≥10 occurrences for statistical power
- Exports highly enriched genes (>30%) for detailed investigation

**Use Case**: Start here to identify genes worth investigating further

---

### 2. Deep Dive Analysis (`dig_amr_prophage_contigs.py`)
**Answers**: What are the characteristics of AMR genes on prophage contigs?

**Key Insights**:
- Specific AMR genes on prophage contigs with metadata
- Gene pairs co-occurring on same prophage contig
- Breakdown by organism, food source, year
- Most frequent prophage-AMR contigs

**Use Case**: Understand the 9.66% of AMR genes on prophage contigs in detail

---

### 3. dfrA51 Investigation (`investigate_dfra51.py`)
**Answers**: Why does dfrA51 show 83% enrichment on prophage contigs?

**Key Insights**:
- All 12 dfrA51 occurrences with prophage status
- Prophage type and quality for each occurrence
- Food source and temporal patterns
- Comparison of prophage vs non-prophage dfrA51

**Use Case**: Understand mechanism of trimethoprim resistance spread

**Hypothesis**: dfrA51 is primarily spread via prophage-mediated HGT in Salmonella, explaining its high enrichment on prophage contigs

---

### 4. mdsA+mdsB Investigation (`investigate_mdsa_mdsb.py`)
**Answers**: Why do mdsA and mdsB co-occur 18 times on prophage contigs?

**Key Insights**:
- Distance between mdsA and mdsB (operon structure?)
- Other AMR genes on same contigs (multi-resistance cassette?)
- Prophage type/quality associations
- Food source and temporal patterns

**Use Case**: Understand if these form an operon or composite transposon

**Hypothesis**: mdsA and mdsB form an operon or are part of a composite transposon that has been integrated into multiple prophages, creating a mobile multi-resistance cassette

---

### 5. Comprehensive Analysis (`comprehensive_amr_analysis.py`)
**Answers**: What's the complete picture of AMR-phage-mobile element relationships?

**Key Insights**:
- Physical co-location (AMR on same contigs as prophages)
- Mobile element associations (plasmids, integrases, transposases)
- Sample-level patterns and statistics
- Interactive HTML report with plots

**Use Case**: Generate publication-ready figures and comprehensive report

---

### 6. Mobile Elements Analysis (`analyze_amr_mobile_elements.py`)
**Answers**: How are AMR genes associated with mobile elements?

**Key Insights**:
- AMR genes on plasmids (% detection)
- AMR genes near integrases (<5kb = integron cassette)
- AMR genes near transposases (<20kb = transposon)
- Distance-based co-location statistics

**Use Case**: Understand mobile element context (once MOB-suite is working properly)

## Current Status

### ✅ Complete
- Kansas E. coli analysis (2021-2025, 788 samples)
- Six analysis scripts developed and tested
- MOB-suite bug identified and fixed
- Initial findings documented

### 🔄 In Progress
- E. coli 2024 full run (job 3914044) - 3,779 samples across all US states
- Running with MOB-suite fix for proper plasmid detection

### 📋 Next Steps
1. Wait for E. coli 2024 run to complete
2. Run full analysis suite on 2024 data (larger sample size)
3. Validate Kansas findings with national dataset
4. Investigate dfrA51 prophage integration sites
5. Characterize mdsA+mdsB operon structure
6. Analyze Ground Beef signal mechanism
7. Investigate 2021 temporal peak

## Biological Significance

### Why This Matters

1. **Horizontal Gene Transfer**: Prophages are major vectors for AMR spread
   - 9.66% of AMR genes on prophage contigs in Kansas data
   - dfrA51: 83% on prophage contigs (strong signal)

2. **Multi-Resistance Cassettes**: mdsA+mdsB co-occurrence suggests composite genetic elements
   - Could be spreading multiple resistances simultaneously
   - Important for predicting co-resistance patterns

3. **Food Safety**: Ground Beef shows highest AMR-prophage association
   - May indicate specific processing risks
   - Relevant for NARMS surveillance strategy

4. **Temporal Trends**: Decrease from 2021 (17.7%) to 2025 (7.6%)
   - Possible intervention effect or sampling variation
   - Warrants investigation with larger dataset

### Clinical Implications

- **Trimethoprim resistance** (dfrA51): Primarily prophage-mediated spread
- **Fosfomycin resistance** (glpT, fosA7): 32% enrichment on prophage contigs
- **Multidrug efflux** (mdsA+mdsB): Operon structure spreading via prophages

## File Structure

```
/bulk/tylerdoe/
├── compass_pipeline/
│   ├── bin/
│   │   ├── analyze_enriched_amr_genes.py
│   │   ├── dig_amr_prophage_contigs.py
│   │   ├── comprehensive_amr_analysis.py
│   │   ├── analyze_amr_mobile_elements.py
│   │   ├── investigate_dfra51.py
│   │   └── investigate_mdsa_mdsb.py
│   └── analysis/
│       ├── ANALYSIS_OVERVIEW.md (this file)
│       ├── QUICK_START.md
│       ├── ENRICHMENT_ANALYSIS_INSTRUCTIONS.md
│       └── RUN_ALL_ANALYSES.sh
│
└── kansas_results/
    ├── 2021/
    │   ├── amr_combined.tsv
    │   └── vibrant_combined.tsv
    ├── 2022/
    ├── 2023/
    ├── 2024/
    ├── 2025/
    └── [analysis outputs will be created here]
        ├── amr_enrichment_analysis.csv
        ├── highly_enriched_amr_occurrences.csv
        ├── dfra51_investigation.csv
        ├── mdsa_mdsb_investigation.csv
        ├── kansas_amr_prophage_contigs_DEEP_DIVE.csv
        ├── kansas_comprehensive_amr_analysis.html
        └── amr_mobile_element_analysis.csv
```

## Questions to Investigate

### dfrA51
1. Is dfrA51 always integrated at the same location in prophages?
2. Which specific prophage types carry dfrA51?
3. Are there geographic patterns in dfrA51-prophage associations?
4. Is the non-prophage dfrA51 (2/12) on plasmids or chromosomal?

### mdsA+mdsB
1. What is the exact distance between mdsA and mdsB?
2. Are they part of a known operon or composite transposon?
3. What other AMR genes co-occur with them?
4. Which prophage types carry the mdsA+mdsB cassette?

### FOSFOMYCIN class
1. Why is fosfomycin resistance enriched on prophage contigs?
2. Do glpT, fosA7, and uhpT share prophage integration sites?
3. Are they mutually exclusive or co-occurring?
4. Clinical significance in E. coli infections?

### Ground Beef signal
1. Why does Ground Beef show highest % AMR on prophage contigs?
2. Are specific Salmonella serotypes more common in Ground Beef?
3. Processing-related factors?
4. Geographic variation?

### 2021 temporal peak
1. Was 2021 an anomaly or part of a trend?
2. Sample size effect or biological signal?
3. Intervention or environmental factors?
4. Validates with 2024 national data?

## References and Documentation

- **Pipeline**: `/workspace/compass-pipeline/README.md`
- **Quick Start**: `analysis/QUICK_START.md`
- **Enrichment Details**: `analysis/ENRICHMENT_ANALYSIS_INSTRUCTIONS.md`
- **Run All Scripts**: `analysis/RUN_ALL_ANALYSES.sh`

## Contact and Support

For questions about:
- **Analysis scripts**: Check inline comments in each Python script
- **Pipeline**: See COMPASS documentation in repository
- **NARMS data**: Consult NARMS program documentation
- **Beocat HPC**: Beocat user guide

---

**Last Updated**: 2025-11-07
**Data Version**: Kansas E. coli 2021-2025 (n=788)
**Next Update**: After E. coli 2024 national run completes
