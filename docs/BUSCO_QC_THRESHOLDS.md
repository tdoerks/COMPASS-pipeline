# BUSCO QC Thresholds for Contamination Detection

## Overview

BUSCO (Benchmarking Universal Single-Copy Orthologs) QC is used to detect contamination and assess assembly quality in the COMPASS pipeline. High duplication of single-copy genes is a strong indicator of mixed cultures or contamination.

## Default Thresholds

### 1. Maximum Duplicated BUSCOs: **5.0%** (CRITICAL)

**Rationale:**
- Single-copy genes should appear exactly once in a pure bacterial genome
- Duplication > 5% strongly suggests:
  - **Contamination**: Mixed bacterial cultures
  - **Co-infection**: Multiple strains of same species
  - **Assembly artifacts**: Improper read merging (less common)

**Literature Support:**
- Simão et al. (2015) - BUSCO paper: "Duplication rates > 5% indicate contamination"
- Parks et al. (2015) - CheckM: Uses similar 5% threshold for contamination
- NCBI GenBank: Flags assemblies with > 10% duplication as suspicious

**Action:** Samples exceeding this threshold are **FAILED** and excluded from downstream analysis.

**Adjusting:**
```bash
# More stringent (3%)
--busco_qc_max_duplicated 3.0

# More permissive (8%) - not recommended for publication
--busco_qc_max_duplicated 8.0
```

### 2. Minimum Complete BUSCOs: **80.0%**

**Rationale:**
- High-quality bacterial genomes should have 90-99% complete BUSCOs
- 80% threshold allows for some lineage-specific gene loss
- Below 80% suggests:
  - **Poor assembly quality**: Fragmentation, low coverage
  - **Wrong lineage**: Using incorrect BUSCO database
  - **Incomplete genome**: Plasmid-only or partial assembly

**Literature Support:**
- Manni et al. (2021) - BUSCO update: "Complete > 95% for high-quality genomes"
- Our experience: 80% allows for reduced genomes (e.g., host-adapted strains)

**Action:** Samples below this threshold are **FAILED**.

**Adjusting:**
```bash
# High-quality only (90%)
--busco_qc_min_complete 90.0

# Permissive for reduced genomes (70%)
--busco_qc_min_complete 70.0
```

### 3. Maximum Fragmented BUSCOs: **10.0%**

**Rationale:**
- Fragmented BUSCOs indicate genes split across multiple contigs
- High fragmentation suggests poor assembly contiguity
- This is a **WARNING**, not a failure threshold

**Action:** Samples exceeding this trigger **WARN** status (still processed).

**Adjusting:**
```bash
# Strict contiguity requirement (5%)
--busco_qc_max_fragmented 5.0

# Permissive (15%)
--busco_qc_max_fragmented 15.0
```

### 4. Maximum Missing BUSCOs: **20.0%**

**Rationale:**
- Missing BUSCOs indicate incomplete assembly or lineage mismatch
- 20% allows for some gene loss in specialized bacteria
- Complements the 80% completeness threshold

**Action:** Samples exceeding this are **FAILED**.

**Adjusting:**
```bash
# Strict completeness (10%)
--busco_qc_max_missing 10.0

# Permissive (30%)
--busco_qc_max_missing 30.0
```

## Status Categories

### PASS ✅
- All thresholds met
- Clean, high-quality assembly
- Safe for downstream analysis

### WARN ⚠️
- Non-critical warnings (e.g., fragmentation)
- Still processed in pipeline
- Review recommended but not required

### FAILED ❌
- Critical issues detected (duplication, low completeness)
- **Excluded from downstream analysis**
- Likely contamination or poor quality

## Organism-Specific Considerations

### Salmonella (NARMS Primary Target)
- Expected complete BUSCOs: **95-98%**
- Expected duplication: **< 1%**
- Genome size: ~4.5-5.5 Mb
- **Recommendation:** Use default thresholds

### E. coli
- Expected complete BUSCOs: **95-99%**
- Expected duplication: **< 1%**
- Genome size: ~4.5-5.5 Mb
- **Recommendation:** Use default thresholds

### Campylobacter
- Expected complete BUSCOs: **90-95%** (naturally reduced genome)
- Expected duplication: **< 1%**
- Genome size: ~1.6-1.9 Mb
- **Recommendation:** Consider lowering completeness to 75%
```bash
--busco_qc_min_complete 75.0
```

## Real-World Examples

### Example 1: Clean Sample
```
Complete: 96.8% (601/621 BUSCOs)
Single-copy: 95.9%
Duplicated: 0.9% (6 BUSCOs)
Fragmented: 1.8%
Missing: 1.4%
Status: PASS ✅
```

### Example 2: Contaminated Sample
```
Complete: 98.4% (611/621 BUSCOs)
Single-copy: 91.1%
Duplicated: 7.3% (45 BUSCOs) ❌
Fragmented: 1.0%
Missing: 0.6%
Status: FAILED (contamination)
```
**Interpretation:** Despite high completeness, 7.3% duplication indicates likely contamination with another strain or species.

### Example 3: Poor Assembly
```
Complete: 68.4% (425/621 BUSCOs)
Single-copy: 67.8%
Duplicated: 0.6%
Fragmented: 15.9%
Missing: 15.7%
Status: FAILED (low completeness)
```
**Interpretation:** Low completeness and high fragmentation suggest failed assembly or low coverage.

### Example 4: Borderline Warning
```
Complete: 94.2% (585/621 BUSCOs)
Single-copy: 91.1%
Duplicated: 3.1% (19 BUSCOs)
Fragmented: 3.6%
Missing: 2.2%
Status: WARN ⚠️ (moderate duplication)
```
**Interpretation:** Slightly elevated duplication (3.1%) triggers warning but passes QC. Manual review recommended.

## Integration with Assembly QC

BUSCO QC complements Assembly QC:

| Metric | Assembly QC | BUSCO QC |
|--------|-------------|----------|
| Contiguity | N50, L50, contig count | Fragmented BUSCOs |
| Completeness | Total length | Complete BUSCOs, Missing BUSCOs |
| Contamination | **Not detected** | **Duplicated BUSCOs** ✅ |
| Quality | N content | Complete BUSCOs |

**Pipeline Flow:**
```
Raw Reads
  ↓
SPAdes Assembly
  ↓
Assembly QC (N50, length, contigs)
  ↓ [Pass]
BUSCO Analysis
  ↓
BUSCO QC (duplication, completeness) ← Contamination detection
  ↓ [Pass]
Downstream Analysis (AMR, Phage)
```

## Skipping BUSCO QC (Not Recommended)

To skip BUSCO QC entirely:
```bash
nextflow run main_metadata.nf --skip_busco_qc true
```

**Warning:** This disables contamination detection. Only use for:
- Trusted, pre-validated assemblies
- Testing/development
- Resource constraints (BUSCO is computationally expensive)

## Error Handling Strategy

Control what happens when samples fail BUSCO QC:

```bash
# Default: Skip failed samples, continue with others
--busco_error_strategy ignore

# Retry failed samples once (may help with timeout issues)
--busco_error_strategy retry

# Stop entire pipeline if any sample fails
--busco_error_strategy terminate
```

## References

1. Simão FA et al. (2015) BUSCO: assessing genome assembly and annotation completeness with single-copy orthologs. *Bioinformatics* 31:3210-3212.

2. Manni M et al. (2021) BUSCO Update: Novel and Streamlined Workflows along with Broader and Deeper Phylogenetic Coverage for Scoring of Eukaryotic, Prokaryotic, and Viral Genomes. *Mol Biol Evol* 38:4647-4654.

3. Parks DH et al. (2015) CheckM: assessing the quality of microbial genomes recovered from isolates, single cells, and metagenomes. *Genome Res* 25:1043-1055.

4. NCBI Genbank submission guidelines: https://www.ncbi.nlm.nih.gov/genbank/wgs_gapped/

## Support

For questions about BUSCO QC thresholds or contamination issues:
- Check `results/pipeline_info/busco_qc_summary.html` for detailed statistics
- Review individual sample reports in `results/busco_qc/`
- Adjust thresholds via command line parameters
- Contact: tylerdoe@ksu.edu
