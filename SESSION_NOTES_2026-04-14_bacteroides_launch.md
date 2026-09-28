# Session Notes: 2026-04-14 - Bacteroides fragilis Study Launch

## Summary
Launched **Bacteroides fragilis** study (1,411 genomes) on COMPASS 1.2.0-candidate to test oxygen-dependent prophage burden hypothesis. Second obligate anaerobe in the oxygen gradient comparative study.

---

## Bacteroides fragilis Study Launch

### Study Setup
- **Organism**: Bacteroides fragilis (obligate anaerobe)
- **Pipeline**: COMPASS 1.2.0-candidate
- **Job ID**: 7643548
- **Status**: Launching (Nextflow workers initializing)
- **Sample count**: 1,411 genomes
- **Expected runtime**: 3-7 days

### Why Bacteroides fragilis?
1. **Obligate anaerobe** (like Fusobacterium)
2. **Most abundant gut bacteria** (~30% of human gut microbiome)
3. **Same niche as E. coli** (gut) but different oxygen requirement
4. **Perfect test organism**: Same environment, different metabolism
5. **Large sample size**: 1,411 genomes (vs Fusobacterium's 218)

### Hypothesis Being Tested
**Bacteroides (obligate anaerobe) should have LOW prophage burden (~1-2/genome) like Fusobacterium, NOT high like E. coli (8.2/genome)**

**Logic**:
- **Same niche** (human gut)
- **Different phylogeny** (Bacteroidetes vs Fusobacteria)
- **Same oxygen requirement** (obligate anaerobe)
- **Expected result**: Same LOW prophage burden
- **Validates**: Oxygen requirement (not niche or phylogeny) determines prophage burden

### Data Acquisition
```bash
# Fetched from NCBI SRA
Total found: 1,505 Bacteroides fragilis WGS samples
Retrieved: 1,411 SRR accessions (94% success)
Output: data/sra_accessions_bacteroides.txt
```

### Job Launch Details
```bash
# Location
cd /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/bacteroides_fragilis_study/

# Steps executed
python3 scripts/fetch_bacteroides.py         # Retrieved 1,411 accessions
python3 scripts/create_samplesheet.py        # Generated samplesheet
sbatch run_bacteroides.sh                    # Job 7643548

# Job parameters
#SBATCH --job-name=bacteroides
#SBATCH --time=672:00:00  # 28 days
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
```

### Current Job Status (as of launch)
```
Main job 7643548: Pending (waiting for compute node)
Nextflow workers: 5 running, 4 pending
  - Running on: hero33, mole049, warlock40 (×2), dwarf53
  - Pending: 4 additional workers queued
```

**Expected**: Main job should start within 5-10 minutes as Nextflow workers initialize

---

## Oxygen Gradient Study - Current Status

### Completed Studies

#### 1. Fusobacterium (Obligate Anaerobe) ✅
- **Status**: COMPLETE
- **Samples**: 218 genomes
- **Prophage burden**: **1.3 prophages/genome**
- **Key finding**: LOW burden (36% have zero prophages)
- **Pipeline**: 1.2.0-candidate
- **Job**: 7610190 (completed)

#### 2. Salmonella (Facultative Anaerobe) ✅
- **Status**: COMPLETE
- **Samples**: 2,737 genomes
- **Prophage burden**: **~4.2 prophages/genome**
- **Key finding**: MODERATE-HIGH burden
- **Pipeline**: 1.0.1
- **Previous study**

### Running Studies

#### 3. Bacteroides fragilis (Obligate Anaerobe) ⏳
- **Status**: LAUNCHING
- **Samples**: 1,411 genomes
- **Expected burden**: **1-2 prophages/genome** (LOW)
- **Pipeline**: 1.2.0-candidate
- **Job**: 7643548
- **Started**: 2026-04-14

#### 4. STEC/E. coli (Facultative Anaerobe) ⏳
- **Status**: RUNNING (1d 5h 29m)
- **Samples**: 7,340 genomes
- **Expected burden**: **8.2 prophages/genome** (HIGH)
- **Pipeline**: 1.1.0-candidate
- **Job**: 7614525
- **Progress**:
  - Downloads: 7,202/7,340 (98%)
  - Failed downloads: 366
  - Successful: 6,836 samples
  - FASTQC: 2,858/6,836 (42%)
  - FASTP: 2,857/6,836 (42%)
  - Assemblies: Ready to start

### Planned Studies

#### 5. Clostridium difficile (Obligate Anaerobe)
- **Metabolism**: Obligate anaerobe
- **Niche**: Gut (pathogen)
- **Expected**: ~1000 genomes
- **Hypothesis**: LOW prophage burden
- **Status**: Not yet created

#### 6. Prevotella (Obligate Anaerobe)
- **Metabolism**: Obligate anaerobe
- **Niche**: Oral/gut
- **Expected**: 300-500 genomes
- **Hypothesis**: LOW prophage burden
- **Status**: Not yet created

#### 7. Campylobacter jejuni (Microaerophile)
- **Metabolism**: Microaerophile (5% O₂)
- **Niche**: Gut (pathogen)
- **Expected**: ~2000 genomes
- **Hypothesis**: MODERATE prophage burden (3-4/genome)
- **Status**: Not yet created

#### 8. Helicobacter pylori (Microaerophile)
- **Metabolism**: Microaerophile
- **Niche**: Stomach
- **Expected**: ~1000 genomes
- **Hypothesis**: MODERATE prophage burden
- **Status**: Not yet created

#### 9. Mycobacterium tuberculosis (Obligate Aerobe)
- **Metabolism**: Obligate aerobe
- **Niche**: Lung (intracellular)
- **Expected**: ~5000 genomes
- **Hypothesis**: HIGH prophage burden (8-12/genome)
- **Status**: Not yet created

---

## Oxygen Gradient Hypothesis - Evidence So Far

### Current Data Points

| Organism | Metabolism | Samples | Prophages/Genome | Status |
|----------|------------|---------|------------------|--------|
| **Fusobacterium** | Obligate anaerobe | 218 | **1.3** | Complete ✓ |
| **Bacteroides** | Obligate anaerobe | 1,411 | **?** (Expected: 1-2) | Running |
| Salmonella | Facultative | 2,737 | **4.2** | Complete ✓ |
| E. coli (STEC) | Facultative | 7,340 | **?** (Expected: 8.2) | Running |

### Hypothesis Statement
**"Prophage burden inversely correlates with anaerobic lifestyle due to lack of oxidative stress-driven lysogeny selection"**

### Supporting Evidence
1. **Fusobacterium** (anaerobe): 1.3 prophages - **LOW** ✓
2. **Salmonella** (facultative): 4.2 prophages - **MODERATE** ✓
3. Literature: E. coli (facultative) = 8.2 prophages - **HIGH**
4. Literature: P. aeruginosa (aerobe) = 11-12 prophages - **VERY HIGH**

### Critical Test: Bacteroides
- **Same niche** as E. coli (gut)
- **Different oxygen requirement** (anaerobe vs facultative)
- **If Bacteroides has LOW burden** → Confirms oxygen > niche as driver
- **If Bacteroides has HIGH burden** → Refutes hypothesis

---

## Repository Status

### Files Created Today

#### Bacteroides fragilis Study
- `bacteroides_fragilis_study/scripts/fetch_bacteroides.py`
- `bacteroides_fragilis_study/scripts/create_samplesheet.py`
- `bacteroides_fragilis_study/run_bacteroides.sh`
- `bacteroides_fragilis_study/README.md`
- `bacteroides_fragilis_study/data/sra_accessions_bacteroides.txt` (1,411 accessions)
- `bacteroides_fragilis_study/data/samplesheet_bacteroides.txt`

#### Session Notes
- `SESSION_NOTES_2026-04-14_bacteroides_launch.md` (this file)

### Git Status
- **Branch**: scratch
- **Commits today**:
  1. Comprehensive Fusobacterium analysis notes
  2. Bacteroides fragilis study setup
  3. Session notes (pending)

### Pushed to Remote
- Repository: https://github.com/tdoerks/COMPASS-pipeline.git
- Branch: scratch
- Status: Up to date (need to push this session note)

---

## Pipeline Resource Allocation

### 1.2.0-candidate
- ✅ Fusobacterium: COMPLETE
- ⏳ Bacteroides: RUNNING (job 7643548)
- Available for: Clostridium, Prevotella (after Bacteroides)

### 1.1.0-candidate
- ⏳ STEC: RUNNING (job 7614525)
- Available after STEC completes

### 1.0.1
- ✅ Salmonella: COMPLETE (archived)
- Available for future studies

---

## Next Steps

### Immediate (Next Session)
1. **Monitor Bacteroides startup** (~10 minutes)
2. **Check STEC progress** (should be ~50-60% by now)
3. **Create Clostridium difficile study** (while Bacteroides runs)

### Short-term (This Week)
1. **Wait for Bacteroides completion** (~3-7 days)
2. **Wait for STEC completion** (~1-2 more days)
3. **Launch Clostridium** on 1.2.0 (after Bacteroides)
4. **Launch Prevotella** on 1.2.0 or 1.1.0

### Medium-term (Next 2 Weeks)
1. **Analyze Bacteroides results**
   - Compare to Fusobacterium (both anaerobes)
   - Compare to E. coli (same niche, different O₂)
2. **Analyze STEC results**
   - Compare to Salmonella (both facultative)
3. **Statistical analysis** across oxygen groups
4. **Manuscript preparation** begins

### Long-term (Next Month)
1. **Complete all anaerobes** (Bacteroides, Clostridium, Prevotella)
2. **Launch microaerophiles** (Campylobacter, Helicobacter)
3. **Launch aerobes** (Mycobacterium)
4. **Comprehensive oxygen gradient analysis**
5. **Publication submission**

---

## Key Decisions Made

### 1. Species-by-Species Approach
- **Decision**: Run each organism separately
- **Rationale**: Failure isolation, progress tracking, clean organization
- **Alternative considered**: Combined samplesheet (rejected)

### 2. Bacteroides First
- **Decision**: Launch Bacteroides before Clostridium
- **Rationale**:
  - Critical test of hypothesis (same niche as E. coli)
  - Large sample size (1,411 vs ~1000 for Clostridium)
  - Perfect comparison to Fusobacterium

### 3. Pipeline Version Separation
- **Decision**: Bacteroides on 1.2.0, STEC on 1.1.0
- **Rationale**: Avoid resource conflicts, can run simultaneously

---

## Technical Notes

### NCBI Data Retrieval
- **Search query**: `Bacteroides fragilis[Organism] AND illumina[Platform] AND GENOMIC[Source] AND WGS[Strategy]`
- **Total found**: 1,505 samples
- **Retrieved**: 1,411 accessions (94%)
- **Batch size**: 100 accessions per API call
- **Rate limiting**: 0.4s between requests
- **Runtime**: ~2 minutes for 16 batches

### SLURM Configuration
```bash
Job name: bacteroides
Time limit: 672:00:00 (28 days)
CPUs: 8
Memory: 32G
Queue: batch.q
Nextflow home: /fastscratch/tylerdoe/.nextflow_bacteroides
Work dir: work_bacteroides
Output: /fastscratch/tylerdoe/bacteroides_results/
```

### Expected Resource Usage
- **Runtime**: 3-7 days (1,411 samples)
- **Storage**: ~500-800 GB (assemblies, results)
- **Archive size**: ~300-400 GB (excluding FASTQs)

---

## Lessons Learned

### 1. Data Directory Creation
- **Issue**: `FileNotFoundError` when saving accessions
- **Solution**: `mkdir -p data` before running fetch script
- **Fix applied**: User created directory manually
- **Future**: Add directory creation to fetch script

### 2. Job Queue Understanding
- **Observation**: Main job pending while workers run
- **Normal behavior**: Nextflow spawns workers before main job starts
- **Expected pattern**: 5-10 workers running, then main job allocated

### 3. Large Sample Sets
- **Bacteroides**: 1,411 samples (6.5x Fusobacterium)
- **STEC**: 7,340 samples (33.7x Fusobacterium)
- **Impact**: Much longer runtimes, stronger statistical power
- **Benefit**: Robust hypothesis testing

---

## Current Active Studies Summary

### Running Now
1. **Bacteroides** (job 7643548): 1,411 samples, launching
2. **STEC** (job 7614525): 7,340 samples, 98% downloads, 42% QC

### Total Genomes Being Analyzed
- Bacteroides: 1,411
- STEC: 6,836 (after download failures)
- **Combined**: 8,247 genomes currently processing

### Disk Usage (Approximate)
- STEC: ~2-3 TB (in progress)
- Bacteroides: Will be ~500-800 GB
- **Total active**: ~2.5-3.8 TB

---

## Publication Status

### Manuscript Outline (Draft)
**Title**: "Oxygen Requirement Determines Prophage Burden: A Comparative Genomic Analysis Across Bacterial Metabolic Lifestyles"

**Current Evidence**:
- ✓ Obligate anaerobe: Fusobacterium (1.3 prophages)
- ⏳ Obligate anaerobe: Bacteroides (pending)
- ✓ Facultative: Salmonella (4.2 prophages)
- ⏳ Facultative: E. coli/STEC (pending)

**Strength**: 2 complete, 2 running (8,247 genomes processing)

**Next Needed**: Additional anaerobes (Clostridium, Prevotella) to strengthen pattern

---

## Oxygen Gradient Study - Timeline

### Week 1 (Current)
- ✓ Fusobacterium complete
- ⏳ Bacteroides launched
- ⏳ STEC running

### Week 2-3
- ⏳ Bacteroides completion expected
- ⏳ STEC completion expected
- Launch Clostridium
- Launch Prevotella

### Week 4-5
- Analyze Bacteroides, STEC
- Complete Clostridium, Prevotella
- Launch microaerophiles

### Week 6-8
- Complete microaerophiles
- Launch aerobes
- Begin manuscript

### Week 9-12
- Complete all studies
- Statistical analysis
- Manuscript submission

---

*Session conducted: 2026-04-14*
*Bacteroides job: 7643548 (1,411 genomes)*
*STEC job: 7614525 (7,340 genomes)*
*Pipeline: COMPASS 1.2.0-candidate (Bacteroides), 1.1.0-candidate (STEC)*

**Status: Bacteroides LAUNCHING, STEC RUNNING ✓**
