# Session Notes: 2026-04-17 - Fusobacterium Host Tree Metadata & iTOL Annotations

## Summary
Successfully fetched SRA metadata for 218 Fusobacterium samples and created iTOL annotation files for host genome phylogenetic tree visualization. Generated color strips for species, host organism, and isolation source.

## Work Completed

### 1. Fusobacterium Host Tree - Available on Beocat ✓

**Location**: `/fastscratch/tylerdoe/fusobacterium_results/analysis/host_phylogenomics/`

**Tree Details**:
- **File**: `host_tree.nwk`
- **Method**: FastTree maximum likelihood
- **Genes**: 20 core single-copy BUSCO genes
- **Samples**: 203 Fusobacterium genomes (from 218 successful assemblies)
- **Quality**: High bootstrap support (most nodes >95%)

**Tree Construction**:
- Core genes identified from `bacteria_odb10` BUSCO dataset
- Genes aligned with MAFFT
- Concatenated alignment: ~20 genes × 203 samples
- Tree built with FastTree (GTR+CAT model)
- Runtime: ~48 seconds

### 2. SRA Metadata Fetch - COMPLETED ✓

**Script**: `fetch_sra_metadata.py`

**Execution**:
```bash
cd /fastscratch/tylerdoe/fusobacterium_results/analysis/host_phylogenomics/
python3 fetch_sra_metadata.py
```

**Runtime**: ~15 minutes (NCBI rate limiting: 0.4s between requests)

**Output**: `fusobacterium_metadata.tsv` (63 KB)
- 218 samples
- 82 metadata fields

**Key Metadata Fields Available**:

| Field | Coverage | Description |
|-------|----------|-------------|
| `organism` | 217/218 (99.5%) | Fusobacterium species |
| `strain` | 213/218 (97.7%) | Strain identifier |
| `isolation_source` | 168/218 (77.1%) | Sample origin |
| `host` | 147/218 (67.4%) | Host organism |
| `geo_loc_name` | 173/218 (79.4%) | Geographic location |
| `lat_lon` | 145/218 (66.5%) | GPS coordinates |
| `sub_species` | 80/218 (36.7%) | Subspecies info |
| `collection_date` | 102/218 (46.8%) | Collection date |

**Other Useful Fields**:
- `host_tissue_sampled` (30 samples)
- `host_disease` (37 samples)
- `isolation-source` (alternative field, 34 samples)
- `biotic_relationship` (36 samples)

### 3. iTOL Annotation Files - CREATED ✓

**Script**: `create_itol_simple.py`

**Challenge Solved**:
- Tree labels: `SRRSRR123456` (double SRR prefix from BUSCO gene extraction)
- Metadata IDs: `SRR123456` (standard SRA format)
- Solution: Regex parsing to extract and match correctly

**Execution**:
```bash
python3 create_itol_simple.py
```

**Output Files**:

1. **`itol_organism.txt`** - Species/Organism Color Strip
   - 20 unique Fusobacterium species detected
   - Colors assigned to each species
   - Examples: *F. nucleatum*, *F. necrophorum*, *F. varium*, etc.

2. **`itol_host.txt`** - Host Organism Color Strip
   - 12 unique hosts identified
   - Examples: *Homo sapiens*, bovine, ovine, unknown

3. **`itol_isolation_source.txt`** - Isolation Source Color Strip
   - 30 unique isolation sources
   - Examples: human stool, blood, abscess, oral cavity
   - Legend limited to top 15 sources by frequency

**Matching Statistics**:
- Tree samples: 203
- Metadata samples: 218
- Successfully matched: 203/203 (100%)

### 4. Files Ready for Download

**On Beocat** (`/fastscratch/tylerdoe/fusobacterium_results/analysis/host_phylogenomics/`):
```
host_tree.nwk                    (6.5 KB)  - Phylogenetic tree
fusobacterium_metadata.tsv       (63 KB)   - Raw metadata
itol_organism.txt                          - Species color strip
itol_host.txt                              - Host color strip
itol_isolation_source.txt                  - Source color strip
```

**Download Command** (from local machine):
```bash
scp tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/fusobacterium_results/analysis/host_phylogenomics/host_tree.nwk .
scp tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/fusobacterium_results/analysis/host_phylogenomics/itol_*.txt .
```

### 5. iTOL Visualization Steps

1. Go to https://itol.embl.de
2. Click "Upload" and select `host_tree.nwk`
3. Drag and drop annotation files:
   - `itol_organism.txt` - Shows species diversity
   - `itol_host.txt` - Shows host range
   - `itol_isolation_source.txt` - Shows ecological niches
4. Customize colors, labels, and layout in iTOL interface
5. Export as SVG/PDF for publication

## Technical Details

### Script Improvements

**`create_itol_simple.py`** improvements over original:
- Handles `SRRSRR` prefix issue automatically
- Uses regex to extract SRR IDs: `re.findall(r'SRR(SRR\d+)', tree)`
- Writes files to current directory (no hardcoded paths)
- Cleans organism names (extracts Genus + species)
- Truncates long isolation sources to prevent legend overflow
- Limits isolation source legend to top 15 entries

**Color Palette**:
```python
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
```

### Data Quality

**Organism/Species Coverage**:
- 217/218 samples have organism annotation (99.5%)
- 20 distinct Fusobacterium species identified
- Species diversity suggests good representation across genus

**Host Diversity**:
- 147/218 samples have host info (67.4%)
- 12 unique hosts
- Includes human, bovine, ovine, and others

**Isolation Source Diversity**:
- 168/218 samples have isolation source (77.1%)
- 30 unique sources
- Covers clinical, gut, oral, environmental niches

## Repository Updates

### Files Added to COMPASS-pipeline/scratch:
- `fusobacterium_necrophorum_study/scripts/create_itol_simple.py`
- `SESSION_NOTES_2026-04-17_host_tree_metadata_itol.md` (this file)

### Git Commands:
```bash
cd /workspace/compass-pipeline
git add fusobacterium_necrophorum_study/scripts/create_itol_simple.py
git add SESSION_NOTES_2026-04-17_host_tree_metadata_itol.md
git commit -m "Add host tree metadata fetch and iTOL annotation generation"
git push origin scratch
```

## Analysis Opportunities

### Immediate: Visualize Host Tree with Metadata

**Questions to Explore**:
1. Do Fusobacterium species cluster by host type?
2. Do clinical isolates cluster separately from commensal?
3. Are certain species host-specific or generalist?
4. Geographic clustering within species?

### Short-term: Prophage Tree vs Host Tree Comparison

**Files Available**:
- Host tree: `host_phylogenomics/host_tree.nwk` (203 genomes, BUSCO genes)
- Prophage tree: `phylogenomics/prophage_tree.nwk` (28 prophages)

**Analysis**:
- Compare topologies (congruent = vertical inheritance)
- Robinson-Foulds distance
- Tanglegram visualization
- Identify species-specific vs promiscuous prophages

### Medium-term: Prophage Burden by Species/Host

**Hypothesis**: Different Fusobacterium species have different prophage burdens

**Data Available**:
- Prophage counts: `prophage_counts_per_sample.tsv`
- Species metadata: `fusobacterium_metadata.tsv` (organism field)
- Host metadata: `fusobacterium_metadata.tsv` (host field)

**Analysis**:
```python
# Merge prophage counts with metadata
# Test: Do F. nucleatum vs F. necrophorum differ in prophage burden?
# Test: Do human vs animal isolates differ?
# Test: Do clinical vs commensal differ?
```

### Long-term: Oxygen Gradient Study

**Current Progress**:
- ✓ Fusobacterium (obligate anaerobe) - 218 genomes, 1.3 prophages/genome
- ✓ Salmonella (facultative) - 2,737 genomes, ~4.2 prophages/genome
- ✓ Vibrio (facultative) - completed
- 🏃 STEC/E. coli (facultative) - 7,340 genomes, running (3d 16h)
- 📋 Bacteroides (obligate anaerobe) - ready to launch
- 📋 Clostridium difficile (obligate anaerobe) - ready to launch

## Other Studies Status

### STEC (E. coli) - RUNNING
- **Job**: 7614525
- **Runtime**: 3 days, 16 hours (as of 2026-04-17)
- **Samples**: 7,340
- **Status**: Analysis phase (VIBRANT, BUSCO, MOB-suite, AMRFinder running)
- **ETA**: 1-2 more days

### Bacteroides fragilis - NOT LAUNCHED
- **Samples**: 1,411 (prepared)
- **Study type**: Obligate anaerobe (for oxygen gradient comparison)
- **Status**: Scripts ready, awaiting launch decision

### Clostridium difficile - NOT LAUNCHED
- **Samples**: 9,133 (prepared)
- **Study type**: Obligate anaerobe (for oxygen gradient comparison)
- **Status**: Scripts ready, awaiting launch decision

## Next Steps

### Immediate:
1. ✓ Metadata fetched
2. ✓ iTOL files created
3. ✓ Session notes documented
4. Push to scratch branch
5. Download files and visualize in iTOL

### Short-term:
1. Wait for STEC completion (~1-2 days)
2. Analyze STEC results (7,340 genomes)
3. Compare prophage tree vs host tree (vertical vs horizontal transfer)
4. Explore species-specific prophage patterns

### Medium-term:
1. Launch Bacteroides study (obligate anaerobe)
2. Launch Clostridium difficile study (obligate anaerobe)
3. Test prophage burden vs species/host/niche
4. Manuscript outline: "Prophage burden in Fusobacterium genus"

### Long-term:
1. Complete oxygen gradient study (anaerobes vs facultative vs aerobes)
2. Manuscript: "Prophage burden inversely correlates with anaerobic lifestyle"
3. Functional analysis: oxidative stress genes in aerobe prophages

## Key Findings Preview

Based on metadata, we can now explore:

**Species Diversity** (20 species detected):
- *Fusobacterium nucleatum* (most common?)
- *Fusobacterium necrophorum*
- *Fusobacterium varium*
- *Fusobacterium periodonticum*
- Unclassified/novel Fusobacterium spp.

**Host Range** (12 hosts):
- Human (likely majority)
- Bovine
- Ovine
- Other animals

**Ecological Niches** (30 sources):
- Oral cavity (commensal)
- Gut/stool (commensal)
- Blood (invasive)
- Abscess (pathogenic)
- Tissue samples (clinical)

## Resources

**HPC**: Beocat (K-State)
- Results: `/fastscratch/tylerdoe/fusobacterium_results/`
- COMPASS pipeline: `/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/`

**Pipeline**: COMPASS v1.2.0-candidate

**Visualization**: iTOL (https://itol.embl.de)

**Metadata Source**: NCBI SRA (EUtils API)

---
*Session conducted: 2026-04-17*
*Metadata: 218 samples, 82 fields, 99.5% organism coverage*
*iTOL files: 20 species, 12 hosts, 30 isolation sources*
