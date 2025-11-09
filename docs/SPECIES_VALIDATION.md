# Species Validation

## Overview

The COMPASS pipeline now includes **automatic species validation** to detect mislabeled samples in NARMS data.

This addresses a known issue where samples are sometimes uploaded to the wrong BioProject (e.g., Salmonella sample labeled as E. coli).

## How It Works

### 1. MLST-Based Detection

After MLST analysis, the pipeline compares:
- **Expected organism** (from NARMS metadata/BioProject)
- **Detected organism** (from MLST scheme match)

MLST scheme mapping:
```
ecoli / ecoli_achtman        → Escherichia
senterica / senterica_achtman → Salmonella
campylobacter / cjejuni       → Campylobacter
```

### 2. Validation Results

Each sample gets a validation status:

| Status | Meaning |
|--------|---------|
| `MATCH` | Expected and detected organisms agree ✅ |
| `MISMATCH` | Species mismatch - sample likely mislabeled ⚠️ |
| `NO_MLST_HIT` | MLST found no scheme match (poor assembly?) |
| `UNKNOWN_SCHEME` | MLST found a scheme we don't recognize |

### 3. Outputs

The pipeline generates three files in `species_validation/`:

**a) Individual validation files**
```
species_validation/
├── SRR12345_species_check.tsv
├── SRR12346_species_check.tsv
└── ...
```

Each contains:
```
sample_id    expected_organism    mlst_scheme       detected_organism    match_status
SRR12345     Escherichia         ecoli_achtman     Escherichia         MATCH
SRR12346     Escherichia         senterica         Salmonella          MISMATCH
```

**b) Summary file** (`species_validation_summary.tsv`)
- All samples combined
- Can be imported to Excel/R for analysis

**c) Validation report** (`species_validation_report.txt`)
- Human-readable summary
- Lists all mismatches
- Provides recommendations

Example report:
```
================================================================================
SPECIES VALIDATION REPORT
================================================================================

Total samples validated: 3779

Validation Results:
--------------------------------------------------------------------------------
  MATCH                  3650 ( 96.6%)
  MISMATCH                 89 (  2.4%)
  NO_MLST_HIT              40 (  1.0%)

================================================================================
⚠️  SPECIES MISMATCHES DETECTED: 89 samples
================================================================================

These samples may be mislabeled in NARMS metadata:

Sample ID            Expected             MLST Detected        Scheme
--------------------------------------------------------------------------------
SRR27561134          Escherichia         Salmonella          senterica_achtman
SRR27561208          Salmonella          Escherichia         ecoli_achtman
...

RECOMMENDATION:
  - Review these samples for potential metadata errors
  - Consider excluding from organism-specific analyses
  - Report to NARMS database curators
```

## Real-Time Warnings

During pipeline execution, mismatches are flagged in the log:

```
⚠️  WARNING: Species mismatch for SRR27561134!
    Expected: Escherichia
    MLST detected: Salmonella (scheme: senterica_achtman)
    This sample may be mislabeled in NARMS metadata!
```

## What To Do With Mismatches

### Option 1: Review and Exclude (Recommended)
```bash
# View mismatches
cat results/species_validation/species_mismatches.tsv

# Create exclusion list
cut -f1 results/species_validation/species_mismatches.tsv | tail -n +2 > exclude_samples.txt

# Re-run pipeline excluding these samples (feature to be added)
```

### Option 2: Re-classify
If you trust MLST more than metadata:
- Use detected organism for downstream analysis
- Update your metadata accordingly

### Option 3: Manual Review
For critical analyses:
- Manually inspect assemblies
- Run Kraken2 for additional confirmation
- Check assembly quality (low quality → unreliable MLST)

## Known Limitations

1. **MLST requires good assemblies**
   - Poor assembly quality → no MLST hit → can't validate
   - Check `NO_MLST_HIT` samples with QUAST metrics

2. **Only validates organisms with MLST schemes**
   - Works for: E. coli, Salmonella, Campylobacter
   - Other organisms: would need Kraken2/CheckM

3. **Assumes MLST is correct**
   - MLST is highly reliable for species ID
   - But contaminated assemblies can give wrong hits
   - Cross-reference with assembly quality metrics

## Future Enhancements

Planned additions:
- [ ] Kraken2 integration for additional validation
- [ ] Automatic flagging in MultiQC report
- [ ] Option to auto-exclude mismatched samples
- [ ] Contamination detection (multiple MLST schemes)

## References

- MLST database: https://github.com/tseemann/mlst
- NARMS data: https://www.fda.gov/animal-veterinary/national-antimicrobial-resistance-monitoring-system
