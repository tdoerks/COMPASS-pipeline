# Claude Code — Session Notes

Last active: (updated 2026-09-28, session 18 — later)

## Environment
- WSL Ubuntu-24.04 on Windows (KSU — tylerdoe)
- Claude Code runs inside Docker: `ghcr.io/tdoerks/claude-nextflow:latest`
- Launch: `cd ~/claude-workspace && docker run -it --rm -v "$PWD:/workspace" ghcr.io/tdoerks/claude-nextflow:latest`
- `/workspace` = `~/claude-workspace` on WSL host — only mounted dir, persists across restarts
- ARBOR repo: `/workspace/ARBOR`, COMPASS repo: `/workspace/COMPASS-pipeline`, PHINDER repo: `/workspace/PHINDER`
- Beocat: `tylerdoe@icr-helios`, scratch at `/fastscratch/tylerdoe/`, bulk at `/bulk/tylerdoe/`
- NARMS bulk storage: `/bulk/tylerdoe/NARMS/` (uppercase)

## GitHub Auth (do once per container session)
```bash
mkdir -p ~/.config && ln -s /workspace/.gh-config ~/.config/gh   # restore saved creds (fastest)
gh auth setup-git   # wires gh credentials to git
# If creds expired, re-login: gh auth login (device flow → https://github.com/login/device)
# After login, save new creds: cp -r ~/.config/gh /workspace/.gh-config
```

## Current Work

### ARBOR (github.com/tdoerks/ARBOR) — `main` branch
- **Pipeline fully working** — job 10854668 (MultiQC + dashboard rerun after SPAdes version fix)
  - SPAdes version string fix: `grep -oE '[0-9]+\.[0-9]+\.[0-9]+'` instead of raw `spades.py --version 2>&1` (commit 5aab167)
  - LOFREQ_CALL: 16GB × attempt, 4h × attempt, maxRetries=2 (commits af67bd5, 014f01e)
  - Assembly skips pooled samples: `!meta.id.endsWith('_pooled')` (commit 5fd4455)
  - Dashboard built ✔ — find with: `find /fastscratch/tylerdoe/ARBOR/tests/beocat/results_remap_A03ref -name "*.html" | grep -i dashboard`
- **In silico pooling**: D3/D7/D14 pooled samples for LoFreq variant frequency estimation
  - Submit dir: `/fastscratch/tylerdoe/ARBOR/tests/beocat`
  - Submit: `cd /fastscratch/tylerdoe/ARBOR/tests/beocat && sbatch run_arbor.sbatch`
- **Results rsync to bulk** — check if completed
  - `rsync -av /fastscratch/tylerdoe/ARBOR/tests/beocat/results_remap_A03ref/ /bulk/tylerdoe/ARBOR/results_remap_A03ref/`
- **Next**: Confirm dashboard HTML opens correctly; set up Globus share on /bulk/tylerdoe/ARBOR/

### COMPASS (github.com/tdoerks/COMPASS-pipeline) — `scratch` = 1.2.0 RC, PR #10 open (scratch→main); `phage-therapy` = new branch off scratch
- **Location on Beocat**: `/fastscratch/tylerdoe/COMPASS-1.1.0/`
- **6k E. coli run COMPLETE** — 3,589 isolates from NCBI Pathogen Isolates (MicroBIGG-E), selected for having MIC/AST data
  - Results: `/fastscratch/tylerdoe/COMPASS-1.1.0/results_mic_ecoli_6k/`
  - Key stats: 99.6% MDR, median 12 prophages, 99.7% have ≥1 prophage
- **compass_summary.tsv** — regenerated manually (pipeline stub was only 2 lines):
  - `python3 bin/generate_compass_summary.py --outdir results_mic_ecoli_6k`
  - Outputs to `compass_summary.tsv` in current dir (default)
- **Viewer**: `COMPASS_TSV=compass_summary.tsv python3 bin/build_compass_viewer.py`
  - Copy to Windows: `scp tylerdoe@icr-helios:/fastscratch/tylerdoe/COMPASS-1.1.0/compass_mic_viewer.html /mnt/c/Users/tdoerks/Downloads/`
- **stx fixes (2026-09-17)** — three bugs fixed, all pushed to scratch:
  - Column mismatch: `top_vf_genes` → `top_virulence_genes` (generate_compass_summary.py)
  - `UnboundLocalError`: duplicate `from collections import Counter` inside function (generate_compass_summary.py)
  - Regex too strict: `\bstx\w*1\b` → `\bstx1|\bstxA\b` (VFDB uses stx1A/stx1B subunit names)
  - **Real stx count: 19 positive** (15 stx2, 2 stx1, 2 stx1+stx2) across 14 distinct STs — biologically valid
  - Dual-toxin strains: GCA_000819305_1 (ST10) + GCA_012708785_1 (ST11) — highest virulence
- **bin/stx_mlst_check.py** — prints MLST + stx genes for all stx-positive isolates
- **MLST tab improvements (commit 70dc73a)** — pushed to scratch:
  - Header shows unique ST count (e.g. "142 unique STs total")
  - Sort-by-count / sort-by-phage-burden toggle buttons
  - Amber bars + "stx" text badge for any ST containing stx-positive isolates
  - stx_count per ST tracked in mlst_summary() return value
- **STEC COMPASS run setup** — `bin/fetch_stec_samples.py` (committed, scratch branch):
  - Download NCBI Pathogen Isolates TSV: https://www.ncbi.nlm.nih.gov/pathogens/isolates/ → filter E. coli + stx VF genes → Download TSV
  - NCBI uses `estX-3` (AMRFinderPlus naming) not `stx` in AMR genotypes column — script handles both
  - Run: `python3 bin/fetch_stec_samples.py "isolates (3).tsv" --sort-date --max 500 --organism Escherichia --out samplesheet_stec_500.csv`
  - Also supports: `--no-stx-filter` (Shigella/any organism), `--sort-date` (newest first), `--organism`
  - 10,615 total STEC in `isolates (3).tsv` (no Has AMR filter); 500 most recent selected
  - Assemblies downloaded: `datasets download genome accession --inputfile <(awk -F, 'NR>1{print $3}' samplesheet_stec_500.csv) --include genome --filename stec_500_assemblies.zip`
  - FASTA samplesheet: `echo "sample,fasta,organism" > samplesheet_stec_500_fasta.csv && find $(pwd)/stec_500_assemblies/ncbi_dataset/data -name "*_genomic.fna" | while read f; do gca=$(basename $(dirname $f)); sample=$(echo $gca | tr '.' '_'); echo "${sample},${f},Escherichia"; done >> samplesheet_stec_500_fasta.csv`
- **phage-therapy branch** (commit b7557e7) — geNomad prophage module + ICTV exclusion tab + viewer as pipeline step
  - Job 11484915 COMPLETE — 11h57m, 6468 succeeded, 497 geNomad FAILED (apptainer /bulk not bound)
  - **Fix**: added `/bulk/tylerdoe` to apptainer bind mounts (commit b7557e7)
  - Rerun job 11503072 + 11519299 (Sep 28): geNomad still 95 FAILED (hidden by errorStrategy ignore) + PHAGE_THERAPY_VIEWER crashed
  - **Fix 639c6db**: viewer script chmod +x, called by name via PATH (like COMPASS_SUMMARY) — `python3 ${projectDir}/bin/...` fails under apptainer `--contain`
  - **Fix 687f8c9**: geNomad keys on first header word; VIBRANT `*_phages.fna` keeps full NCBI description → multiple prophages on one contig = duplicate IDs → "empty or contains multiple entries with the same identifier". Module now awk-sanitizes headers (whitespace→`_`, `_dupN` suffix)
  - **Job 11519817 COMPLETE** (55 min, `run_compass_phage_therapy_test.sbatch`, dir `/fastscratch/tylerdoe/COMPASS-phage-therapy/`) — GENOMAD_PROPHAGE **497/497, 0 failed** ✔, PHAGE_THERAPY_VIEWER ✔ — both fixes confirmed
  - Viewer: `results_stec_500_pt/summary/phage_therapy_viewer.html` (outdir per notes — `find . -name phage_therapy_viewer.html` if not there)
  - **Viewer caveats (DIAMOND accessions view)**: Name column all `—` (pipeline step has no internet → no `--resolve-names`); rows are reference ACCESSIONS (mostly `562.SAMN…` E. coli genomes, one metagenome contig `k141_…`), not phage families → one prophage type split across several accessions → max only 15%, 5 excluded / 45 "candidate" inflated
  - For named version: `python3 bin/build_phage_therapy_viewer.py --compass results_stec_500_pt/summary/compass_summary.tsv --resolve-names --out phage_therapy_viewer_named.html` (login node)
  - **Exclusion-tab bugs fixed (phage-therapy branch)**:
    - 59bd1f6: `top_prophage_matches` = top 3 DIAMOND rows OVERALL by pident (short 100% hits from ONE prophage) → isolates with ~8 prophages credited ~1. New summary column `prophage_best_matches` = best ref per prophage (qseqid, by bitscore); viewer uses it (falls back to old col). Result: max 15%→28.8%, excluded 5→21
    - 4e7e20b: geNomad lineage stops at FAMILY (no genus — old `parts[8]` genus read never worked). 541/547 STEC prophages = `Caudoviricetes;;` (no ICTV family: lambdoid/Stx phages lost family when Siphoviridae/Myoviridae abolished 2022) → were dropped as 'unclassified'. Now labeled by deepest rank "Caudoviricetes (no family)"
  - **Regenerate (no pipeline rerun)** — ORDER MATTERS, viewer reads the summary TSV:
    `python3 bin/generate_compass_summary.py --outdir results_stec_500_pt --output_tsv compass_summary_pt.tsv --output_html compass_summary_pt.html` then
    `python3 bin/build_phage_therapy_viewer.py --compass compass_summary_pt.tsv --resolve-names --out phage_therapy_viewer_pt.html` (login node, needs internet). Done 2026-09-28 ✔
  - **STEC results (2026-09-28)**: DIAMOND view — 21 refs >10% (top: E. coli/Shigella/O157 Sakai-matched prophages 21–29%). ICTV view — Caudoviricetes (no family) 98.8% (Exclude); named families rare: Straboviridae (T4-like) 1.6%, Autographiviridae (T7-like) 1.2%, Peduoviridae (P2, temperate) 1.0%, Drexlerviridae (T1-like) 0.8%, Inoviridae 0.6%, Chimalliviridae (phiKZ-like jumbo) 0.2%. Priority 1: 163
  - **Interpretation**: exclusion logic mainly argues against lambdoid/temperate phages. Lytic families (T4/T7/T1-like, jumbo) being rare AS PROPHAGES is expected (they don't lysogenize) — NOT evidence of susceptibility. Lytic success depends on receptors (O-antigen/capsule) + defense systems (CRISPR, R-M, Abi). Peduoviridae/Inoviridae shown as "candidate window" but are temperate/chronic — not therapy candidates
  - Harmless noise: "Could not parse prophage-AMR results … No columns to parse" = empty files (no prophage AMR); "Resolved 60/42 names" = SAMN IDs double-counted in counter
  - Check ignored failures: `L=.nextflow.log; grep GENOMAD_PROPHAGE $L | grep -oE "exit: [0-9]+" | sort | uniq -c`
  - Results in `results_stec_500_pt/`; after completion rebuild: `python3 bin/generate_compass_summary.py --outdir results_stec_500_pt && python3 bin/build_phage_therapy_viewer.py --compass compass_summary.tsv --out phage_therapy_viewer_pt.html`
  - Exclusion tab: "Source" dropdown → switch DIAMOND accessions ↔ ICTV families (geNomad)
  - **PHAGE_THERAPY_VIEWER** now a pipeline step — outputs `summary/phage_therapy_viewer.html` automatically; skip with `--skip_phage_therapy_viewer`
- **STEC run COMPLETE** — job 11403305, 10h49m, 497/497 samples ✔
  - Results: `/fastscratch/tylerdoe/COMPASS-1.1.0/results_stec_500/`
  - Viewer: `compass_mic_viewer.html` (1.8MB) — 497 isolates, 92 antibiotics, 100% MDR
  - stx detection fixed (commits 1e925a5, 6b7f920, b8e7e7b): VFDB misses non-O157 stx; fixed by adding NCBI metadata (stx_type from fetch_stec_samples.py) as authoritative source
  - **stx breakdown**: 353 stx2, 144 stx type unknown, 0 stx1 — 497/497 positive ✔
  - Rebuild viewer: `python3 bin/generate_compass_summary.py --outdir results_stec_500 --metadata samplesheet_stx_metadata.csv && COMPASS_TSV=compass_summary.tsv python3 bin/build_compass_viewer.py`
  - **Key findings**: 8 median prophages, 23 median AMR genes, 24 Inc plasmid groups, IncFIB dominant
- **Phage Therapy Viewer** — `bin/build_phage_therapy_viewer.py` (scratch branch, commit c335476+)
  - Run: `python3 bin/build_phage_therapy_viewer.py --compass compass_summary.tsv [--resolve-names] --out phage_therapy_viewer_stec.html`
  - `--resolve-names` queries NCBI for accession descriptions (~10-20s, requires internet)
  - Tabs: Overview | Candidate Ranking | AMR Profile | Prophage Landscape | Strain Diversity | Prophage Exclusion | Phage Matching (--phinder)
  - **Phage Therapy Score** = AMR Burden (0-5) + Prophage Susceptibility (0-5); Priority 1-4 tiers
  - **STEC results**: 165 Priority 1 candidates, 435/497 last-resort resistance, 497/497 MDR, 8.0 median prophages, 157 unique STs
  - **Prophage Exclusion tab**: 5 excluded families (>10%): Shigella sonnei, E. coli O16:H48, E. coli DSM 30083, E. coli generic, E. fergusonii — all core E. coli/Shigella lineage prophages
  - **Candidate window**: E. albertii, E. marmotae, E. ruysiae lineage prophages (<10% prevalence)
  - **Phage-therapy add-ons (3869f21, 2026-09-28)** — (1)+(2)+(3) of ranked ideas DONE:
    - `modules/defensefinder.nf` — DefenseFinder 3.0.0 on nucleotide assembly (pyrodigal; NO Prokka needed — skip_prokka=true default); `--skip-model-version-check` (else queries GitHub + writes $HOME → fails offline/--no-home); only activity=="Defense" counted
    - `modules/ectyper.nf` — ECTyper 2.0.0 `--pathotype` (O:H + STEC/EHEC + stx subtypes); Escherichia/Shigella only; ALWAYS needs 943 MB MASH sketch + `.msh.txt` passed via `-r` (else tries download into read-only container)
    - `bin/setup_phage_therapy_dbs.sh` — one-time, login node: models → `/fastscratch/tylerdoe/databases/defensefinder_models` (defense-finder-models 3.1.0 + CasFinder 3.1.0 ✔ installed), sketch → `/fastscratch/tylerdoe/databases/ectyper/` (was downloading)
    - params `skip_defensefinder/defensefinder_models`, `skip_ectyper/ectyper_mash` (paths in conf/beocat.config); modules skip with warning if path unset
    - COMPASS_SUMMARY ready-signal now `"ready:${n}"` (count of upstream results) → adding modules on -resume regenerates summary + viewer
    - Summary cols: defense_system_count/types/has_crispr_cas, o_type, h_type, serotype, ectyper_qc, pathotype, stx_subtypes
    - Viewer: **Defense & Receptors** tab (system prevalence, CRISPR-Cas %, median/priority tier, serotypes, pathotypes, stx subtypes); Serotype + Defense cols in Candidate Ranking; exclusion Lifestyle col — rare temperate/chronic → "Not a therapy phage"
    - Tested on source + mock data + JS runtime harness + `nextflow -preview`; **real containers NOT yet run**
    - **Next**: after sketch finishes (`Done.` printed) → `sbatch run_compass_phage_therapy_test.sbatch` (-resume; only 497 DEFENSEFINDER + 497 ECTYPER + summary + viewer). Check `DEFENSEFINDER 497 of 497` / `ECTYPER 497 of 497` with NO `failed:` (errorStrategy ignore hides failures) → if failures, read first task's `.command.err`
  - **Remaining ideas**: (4) cross with PHINDER library via --phinder (7 E. coli phages) — best after serotypes known; (5) vOTU clustering of prophages (95% ANI/85% AF) to split the 98.8% "no family" group; **cluster DIAMOND hits by matched prophage (not accession) in exclusion tab** — accession-level splitting understates prevalence; ST-level exclusion filter; cross with PHINDER library (--phinder flag already built)

### NARMS bulk storage cleanup — `/bulk/tylerdoe/NARMS/`
- **Goal**: Flatten FASTQs by year into `samples_clean/` folders, remove nested BaseSpace hash dirs
- **Structure**: `/bulk/tylerdoe/NARMS/2025/samples_clean/`, `/bulk/tylerdoe/NARMS/2026/` (flat)
- **Pass sample list**: 112 confirmed-pass 26KS samples (26KS01–26KS07) to move to `/bulk/tylerdoe/NARMS/2026/`
  - Script at `/workspace/copy_pass_samples.py` — finds each sample anywhere under NARMS and copies R1+R2 to flat 2026 folder
  - Get to Beocat: `wsl bash -c "cat ~/claude-workspace/copy_pass_samples.py | ssh tylerdoe@beocat.ksu.edu 'cat > /fastscratch/tylerdoe/copy_pass_samples.py'"`
  - Run on Beocat: `python3 /fastscratch/tylerdoe/copy_pass_samples.py`
- **BaseSpace permission issue**: dirs downloaded with `dr-x` — always `chmod -R u+w <folder>` before mv/rm
- **Progress so far**: 26KS01 + 26KS02 samples confirmed present in 2026 flat folder; 26KS03–07 still in unprocessed subfolders
- **Key finding**: Sxx slot numbers differ between pass list and disk filenames — that's normal, doesn't affect identity
- **One lib ID discrepancy**: pass list has 26KS02CL01-EC as `26DL039` but disk has `26DL038` — likely typo in pass list
- **Remaining run folders to process**: `2-23-26_NARMS_BWGS_2026-02-23`, `3_3_2026_NARMS_WGS_requeue_NEB`, `3-5-26_NARMS_USDA_BWGS_EM_2026-03-05`, `4-22-26_RVFV_req_NEB`, `ICA_Workflows_2026_04`, `NARMS-425401161`, `narms-435220242`, `Runs/` (has 16 unique March 3 requeue samples — don't delete without extracting those first)
- **Next**: Run copy_pass_samples.py on Beocat to bulk-copy all pass samples to flat 2026 folder

### PHINDER (github.com/tdoerks/PHINDER) — `main` = stable, `dev` = new features under test
- **Pipeline**: End-to-end phage isolate analysis — QC → assembly → CheckV → Pharokka → VIBRANT → DIAMOND → PHANOTATE → BacPhlip → AMRFinder Plus → geNomad → fastANI → PhageTerm → summary dashboard
- **Input modes**: SRA accessions, raw FASTQs, or pre-assembled FASTAs (`--input_mode assembly`)
- **Beocat locations**: `/fastscratch/tylerdoe/PHINDER/` (main runs), `/fastscratch/tylerdoe/PHINDER-dev/` (module testing)
- **Branching strategy**: `main` = stable tested; `dev` = new modules; merge via PR once proven
- **PR #6 MERGED (dev→main)**; **PR #7 MERGED 2026-09-28** (5e5f15b) — BacPhlip/Pharokka meta/MultiQC reads-mode fixes now on main
- **dev synced** with main via merge (70b2899) — identical trees; dev = main now (old "dev has extras" list below is stale: ANI/vConTACT2 are on main)
- **Publication scrub**: personal `--mail-user` removed from `bin/run_phinder_beocat.sh` (on stress-test branch, not yet on main)
- **Known bug (not fixed)**: `generate_phinder_summary.py` `parse_bacphlip_results` falls back to `glob("*.bacphlip")[0]` → a sample with missing BacPhlip shows ANOTHER sample's lifestyle on the dashboard. Fix on main after stress results
- **Dashboard sample discovery keys off `quast/*_quast`** → samples whose QUAST failed vanish from dashboard (stress scorer flags this as "Dashboard MISSING")

#### PHINDER stress test — `stress-test` branch (c3d2c61), Beocat dir `/fastscratch/tylerdoe/PHINDER-stress/`
- **Goal**: find what PHINDER can/can't handle, with known answers. Docs in `TEST_PHAGES.md`
- **Stress tier (47 samples)**: 31 simulated (19 verified RefSeq phages + E. coli K-12): architecture (phiX174, M13, MS2, Phi6, PM2, PRD1, T7/T5/T4, phiKZ 280kb, phage G 498kb), lifestyle (lambda/P22/Mu/P1), host/GC (phage K, L5, D29, crAss001), coverage T7 5x→10,000x, host contamination T7+10/50/90% E. coli, mixed (T7+lambda, T4+T7), negatives (E. coli only, random); + 7 real-read samples (SPAdes-compare reads) + 8 assembly-mode + 1 SRA
- **Breadth tier (1000 samples)**: `assets/stress_breadth_panel.tsv` — diversity-stratified RefSeq panel: 12 classes, 129 families, 230 host genera, 22 phyla, 131 archaeal, 65 jumbo; clean 100x each
- **Scripts**: `bin/stress_fetch_refs.py` (download+verify; `--panel` for breadth), `bin/stress_simulate.py` (pure-Python 2x150 simulator; `--breadth-panel`), `bin/stress_breadth_panel.py` (panel builder from `datasets summary virus genome taxon <Class> --refseq --complete-only --as-json-lines`), `bin/score_stress_test.py` (trace status + k-mer recovery/purity + CheckV/geNomad/BacPhlip/VIBRANT + geNomad-vs-NCBI taxonomy + per-group breakdown), `conf/stress.config` (retry 2x then ignore), `bin/run_phinder_stress_beocat.sh` (modes reads/assembly/sra from separate launch dirs; `MODES=breadth` for panel)
- **Job 11520464 RUNNING** — stress tier (reads→assembly→sra, then scoring). Log: `tail -f phinder_stress_11520464.log`
  - Progress (2026-09-28 evening): FastQC/fastp 38/38; SPAdes 46 attempts, 12 failed / 8 retries → **4 samples failed SPAdes all 3 attempts** (likely sim_random, real_phiX174, real_Ecoli_K12 + 1 TBD); 31 assemblies flowing through QUAST/CheckV/Pharokka/VIBRANT/geNomad etc.
  - Early: SPAdes failed `sim_random` (exit 21, expected — negative control), `real_phiX174` + `real_Ecoli_K12` (exit 255 — SRR001665/6 are 2008 Illumina GA runs, likely ~36bp reads too short for SPAdes k-mers; unconfirmed), 1 more unknown. Diagnose: see `.command.err` in `stress_runs/reads/work/<hash>`
- **Breadth**: 1000/1000 genomes fetched on Beocat ✔; simulate was running (~9 min, ~3.5 GB) → then `MODES=breadth sbatch bin/run_phinder_stress_beocat.sh` (~12k tasks, 2-3 days, resubmit to resume) — **check whether submitted**
- **Outputs**: `stress_runs/stress_scorecard.html` + `.tsv` + `_breakdown.tsv` (copy to Windows with scp)
- **Caveats**: PhageTerm on simulated reads meaningless (uniform read ends) — judge only real reads; `test_phages_20_sra.txt` 17 "diverse" SRRs are unverified placeholders (flagged in TEST_PHAGES.md); real SRR5131134/5/6 identities (lambda/T4/T7) unverified — scorer's recovery vs claimed ref will confirm
- **Local Nextflow in claude container is 26.04** — strict parser rejects `def check_max` in nextflow.config; use `NXF_SYNTAX_PARSER=v1` to test configs locally (Beocat 24.04 fine)
- **Nextflow config gotcha**: inside `trace { }` block `params.x` resolves to `trace.params.x`; and `params.outdir` isn't reliably visible in a `-c` config → pass `-with-trace <path>` on CLI instead
- **Publication scrub done** (d2803b2): db paths null in core config, site paths in `conf/beocat.config` (run scripts use `-profile slurm,beocat`), README rewritten (SPAdes not Unicycler, all 17 tools), CITATIONS.md created, version 1.0.0
- **main branch** (commit f70d142) — stable, all working modules:
  - FastQC, fastp, SPAdes, QUAST, CheckV, Pharokka, VIBRANT, DIAMOND prophage, PHANOTATE, BacPhlip
  - AMRFinder Plus, geNomad, fastANI, PhageTerm
  - Fix: geNomad cp-to-self (5b5cd2d); Pharokka renames `phanotate.faa` → `<sample_id>.faa`
  - **Host column** in Overview/Lifestyle/Annotation/Quality tabs (c045b19) + expanded `_HOST_PREFIX` map
  - **Disclaimer banner** at top (amber strip between header and stats bar, 60b07e5)
  - **Run Info tab** (60b07e5): run metadata (pipeline/Nextflow version, run name, samplesheet, input mode) + pipeline parameters + software versions harvested from published versions.yml files
- **dev branch** (commit 836d937) — everything on main PLUS:
  - **ANI species clustering**: Union-Find at 95% → Species Cluster column ✔ working
  - **vConTACT2**: container WORKING (build #10) — `ghcr.io/tdoerks/phinder-vcontact2:0.11.3`
    - Container fixes (all in `containers/vcontact2/Dockerfile`): numpy `np.warnings` sed patch, ClusterONE JAR wget from paccanarolab.org + openjdk, scipy `zip(*profiles.values)` → `profiles.values.T` patch, package-wide `zip(*x)` → `list(zip(*x))` sed (build #10 — matrices.py bool_membership failed at 86-genome scale AFTER ClusterONE detected 19 complexes)
    - Module fix (836d937): REMOVED faa rename logic — sample_ids/faa_files channels arrive in different orders, pairwise `cp A B && cp B A` swaps clobbered genome contents. Files already named `<sample_id>.faa` by Pharokka.
    - "No edge in the similarity network" now = warning not failure (legit for small dissimilar sets with --db None)
    - `--c1-bin /opt/conda/bin/cluster_one-1.0.jar` passed explicitly
  - **iPHoP**: module implemented (skip_iphop=true) — requires ~400GB database download
  - **Phylogenomics tab** + VC Cluster/Predicted Host columns in Taxonomy tab
- **Container rebuild gotcha**: same tag = Apptainer reuses stale cache. After each Actions rebuild: `rm -f /fastscratch/tylerdoe/PHINDER/apptainer_cache/*vcontact*` (shared cache dir, used by both PHINDER and PHINDER-dev). Module-only changes need NO cache clear.
- **Dashboard tabs**: Overview | Lifestyle | Annotation | Quality | Taxonomy | ANI | Phylogenomics(dev) | AMR & VF | Run Info
- **53 vs 86 mystery SOLVED**: resume run published only 53 QUAST dirs → summary only found 53 samples (sample discovery keys off `quast/*_quast`). Fresh rerun published all 86. If dashboard undercounts, check `ls results_*/quast | wc -l`.
- **Key biological results**:
  - phiKSUM = Lytic (VIBRANT + BacPhlip 0.995) ✓ matches paper; geNomad Caudoviricetes, unclassified family (novel)
  - All Fn phages: CARD AMR = 0, VFDB = 0, AMRFinder = 0 — safe therapeutic candidates
  - Salmonella phages → Drexlerviridae + Demerecviridae; Fn/Pg phages → novel (unclassified)
- **86-phage library** — `samplesheet_phage_library.csv`; host groups: Fusobacterium(15), Porphyromonas(4), C.difficile(17), Klebsiella(10), Pseudomonas(13), Staphylococcus(12), Salmonella(7), E.coli(7), Acinetobacter(1)
- **FNN alleged phage samples** — 3 Illumina samples from collaborator (SA_2/SA_3/SA_4 DNA CP04336)
  - Reads: `/fastscratch/tylerdoe/fnn_phage_alleged/SA_2_DNA_CP04336_S33_R1/R2.fastq.gz` (x3 samples)
  - Samplesheet: `/fastscratch/tylerdoe/PHINDER-dev/samplesheet_fnn_alleged.csv`
  - Run script: `run_phinder_fnn_alleged.sh` (in PHINDER-dev dir)
  - Job 11481827 finished — assemblies in `/fastscratch/tylerdoe/PHINDER-dev/results_20260924_094406/assemblies/`
  - **SA_4 = BACTERIAL CONTAMINATION** (COMPASS check job 11519589, `results_sa4_check/`, commits d0bf3ff/0f4889c on scratch):
    - 2.77 Mb, 976 contigs, N50 8 kb, **BUSCO 94.7% complete** → near-complete bacterial chromosome, not a phage prep
    - Likely NOT Fuso: GC 36.3% (Fn ~27%), partial MLST hit to **campylobacter** scheme, AMR erm(B)/aadE/tet(O) — oral Campylobacter (concisus/rectus/showae?) suspected, unconfirmed
    - VIBRANT found 22 viral regions (21 lytic) — possible real phage buried in it
    - **Next**: check SPAdes coverage for a high-cov phage-sized contig: `grep '^>' <SA_4 assembly> | sed 's/^>//' | sort -t_ -k6,6gr | head -15`; if found → extract → PHINDER `--input_mode assembly`; else tell collaborator prep is contaminated. Species ID via Kraken2/GTDB-Tk/BLAST of top contigs. SA_2/SA_3 not yet checked
  - Bug fixes (dev + fnn-reads-test branches, all pushed):
    - BACPHLIP: awk filter fix (uses `next`), threshold 500bp, `errorStrategy=ignore`
    - PHAROKKA: handle prodigal-gv.faa in meta mode
    - MultiQC: strip sample_id from FASTQC zip tuple (`.map { sid, zip -> zip }`)
  - PR #7 (fnn-reads-test -> main) MERGED 2026-09-28
  - **Next**: resolve SA_4 (above), check SA_2/SA_3 same way
- **Dev test run 11392176 PASSED**: all modules ✔ incl. vConTACT2 (6 Fn phages hit graceful no-edges path — too dissimilar with --db None, expected)
- **SPAdes mode discussion (2026-09-17)**: current pipeline uses `--isolate`; discussed switching to `--meta` (better for high/uneven phage coverage) and designed a full comparison test
- **spades-mode-test branch** (commit b33ecf7) — test all 6 SPAdes modes across phage types:
  - Modes: `isolate`, `meta`, `metaviral`, `rnaviral`, `careful`, `standard`
  - Sample types: dsDNA, ssDNA, ssRNA, dsRNA, bacterial (controls)
  - Entry point: `nextflow run main_compare.nf -profile slurm,beocat --compare_input samplesheets/samplesheet_spades_compare.csv`
  - Output: colored heatmap HTML (sample × mode, green=complete/red=failed) + TSV
  - **Key findings**: metaviral best for dsDNA, rnaviral best for ssRNA, Phi6 needs host depletion; recommend switching PHINDER default to `--metaviral`
  - Compare HTML: `results_spades_compare/spades_mode_comparison.html` (run `python3 bin/compare_spades_modes.py --quast-dir ... --samplesheet ... --outdir ...`)
  - **Beocat test dir**: `/fastscratch/tylerdoe/PHINDER-spades-test/` — cloned from scratch, on spades-mode-test branch
  - **Reads dir**: `/fastscratch/tylerdoe/PHINDER-spades-test/reads/`
  - **Existing dsDNA reads**: SRR5131134, SRR5131135, SRR5131136 (from earlier 3-phage test run at `/fastscratch/tylerdoe/PHINDER/results_3phages_20260603_170310/fastq/`)
  - **Downloaded reads** (in `/fastscratch/tylerdoe/PHINDER-spades-test/reads/`):
    - SRR001665 = ΦX174 (ssDNA, Illumina calibration standard — very high coverage)
    - SRR001666 = E. coli K-12 MG1655 (bacterial control)
    - SRR5131134/5/6 = dsDNA phages (copy from `/fastscratch/tylerdoe/PHINDER/results_3phages_20260603_170310/fastq/`)
  - **SRA-Toolkit on Beocat**: `module load SRA-Toolkit/3.0.3-gompi-2022a` then `fasterq-dump <SRR> --split-files --threads 4 --progress`
  - **Run script**: `run_spades_compare.sbatch` (commit 9b79726) — `sbatch run_spades_compare.sbatch` from PHINDER-spades-test dir
  - **All 7 samples now in samplesheet** (commit f250a11): 3×dsDNA, 1×ssDNA (ΦX174/SRR001665), 1×bacterial (E.coli K-12/SRR001666), 1×ssRNA (MS2/SRR31435157), 1×dsRNA (Phi6/SRR30985651)
  - **SPAdes compare job COMPLETE** — job 11415186; results in `results_spades_compare/`
    - Fresh start (work/ + .nextflow deleted): CheckV resume cache was resurrecting old tasks despite skip_checkv=true
    - Fix (commit 90da874): CheckV removed entirely from spades_mode_compare.nf — QUAST only
    - QUAST min-contig 500→100, errorStrategy=ignore (commit 4439064)
    - All 7 samples × 6 modes = 42 assemblies running; comparison HTML report at end
    - **Next**: when complete, check results_spades_compare/ for comparison HTML
  - **Sanger reads**: collaborator has Sanger F+R reads converted to FASTQ — discuss later; plan = assemble manually → FASTA → PHINDER assembly mode
- **Dashboard polish idea**: distinguish "vConTACT2 not run" vs "ran, no clusters formed" in Phylogenomics tab
- **Not on dashboard yet**: FastQC/fastp (MultiQC only), SPAdes contigs/N50 detail, DIAMOND prophage hits, PHANOTATE standalone calls
- **Heroic bug**: multi-line Groovy `${pairs}` interpolation breaks stripIndent → heredoc terminator not found
  - Fix: join multi-value content with ` && ` (single line) instead of `\n`
- **Log patterns**: `tail -f phinder_lib_<JOBID>.log` (library), `tail -f phinder_dev_<JOBID>.log` (dev), `tail -f phinder_spades_<JOBID>.log` (spades compare)

### 3D Prints (github.com/tdoerks/3d-prints) — NEW repo, `main`
- **Location in workspace**: `/workspace/3d-prints`
- **Structure**: `designs/lab/`, `designs/makerspace/`, `designs/personal/`
- **Scripts in repo** (all read, ready for printkit):
  - `designs/lab/qubit_holder/qubit_holder.py` — reagent holder, 45° bevel, engraved text, emblem, finger lifts, fit-test rings
  - `designs/lab/tapestation_holders/tapestation_holders.py` — tube holder modules, emblem system (double helix/single strand + badge), bowtie-key sockets on 10 mm grid, side-name engraving; uses shapely for 2D geometry
  - `designs/personal/essential_oil_modules/essential_oil_modules.py` — bottle holders auto-sized from diameter, same bowtie-key system
  - `designs/personal/chess_shakers/chess_shakers.py` — hollow chess figures, eccentric-circle printed threads, text via matplotlib TextPath, two-tone chessboard stand
  - `designs/personal/chess_shakers/render_preview.py` — ray-traced preview renderer (embree), smooth shading, AO, shadows, cut planes
- **Key shared patterns across all scripts**:
  - `manifold3d`: `Manifold`, `CrossSection`, `FillRule`, `JoinType`, `OpType` for all CSG
  - `trimesh`: export only (`mesh.vert_properties[:, :3]`, `mesh.tri_verts`)
  - `shapely`: 2D geometry for emblems (tapestation only)
  - `matplotlib.textpath.TextPath` → `to_polygons()` → `CrossSection` for text
  - Bowtie-key joinery: `KEY_NECK=5`, `KEY_FLARE=8`, `KEY_HALF=3.5`, 10 mm grid (identical in tapestation + oil modules)
  - Rounded block with chamfered bottom/top: `batch_hull([slab(base.offset(-chamfer)), slab(base)])` pattern
  - `watertight` check via `trimesh.Trimesh.is_watertight` after export
- **printkit** — planned Python package + CLI (not yet started):
  - `build`, `render`, `check`, `fittest` CLI commands
  - YAML design spec → STLs + preview PNGs + print notes markdown
  - Building blocks to extract: bodies, pockets, text, emblems, joinery, threads, fit-test rings
  - Checks: watertight, non-manifold, bed fit (Bambu A1 mini 180 mm), overhang >45°, min wall, interference
  - **Next step**: show package layout + YAML schema + CLI plan before writing any code; port qubit holder first as proof

### Platinum-Calibration (github.com/tdoerks/Platinum-Calibration)
- **Live site**: https://tdoerks.github.io/Platinum-Calibration/ (serves from `main`)
- **Newest branch**: `unified-rebuild` (July 13) — adds DYMO label printer tab, 1 commit ahead of main, 5 behind
- **Google Drive integration**: `google-drive-integration` branch — Phase 1 auth started (May 3) but never merged
- **Goal**: Add Microsoft backend (instead of Google Drive) + pipette serial number registry with auto-fill
  - When serial # typed → XLOOKUP auto-fills manufacturer/model/max volume from registry
  - New pipettes: fill manually → add to registry
- **Data storage decision**: Local dedicated PC (SQLite) rather than cloud — data stays in building
- **Next**: Finish Google Drive integration branch OR rewrite for Microsoft Graph API

### Lab Server / Open-Source Lab Tools
- **Repo**: github.com/tdoerks/open-source-lab-resources
- **Tools**: bacterial-isolation-tracker, checkin-board, freezer-inventory, pipetting-tutorial, miseq-pooling, etc.
- **Goal**: Host tools on a dedicated lab PC, accessible to team from anywhere, client data secure
- **Architecture**:
  ```
  Internet → Cloudflare Access (login gate, free up to 50 users)
                  ↓
            Cloudflare Tunnel (outbound, works through guest WiFi/NAT)
                  ↓
            Dedicated lab PC (nginx serves HTML, SQLite stores data)
  ```
- **Tested 2026-09-02**: Cloudflare quick tunnel working on current PC
  - Temp URL was: `https://shapes-prizes-advertiser-atom.trycloudflare.com` (expired)
  - Test command (WSL): `python3 -m http.server 8080` + `cloudflared tunnel --url http://localhost:8080`
- **Guest WiFi OK**: Cloudflare Tunnel is outbound-only, works through client isolation
- **Data security plan**: Data on local PC (not cloud), Cloudflare Access gates login by email
- **Auth plan**: Personal Microsoft 365 or Google account (NOT KSU — KSU IT controls those)
- **Next**: Set up dedicated PC with Ubuntu + nginx + Cloudflare named tunnel + Access login wall

### E-ink display (ordered 2026-08-24, arrives ~Aug 25-26)
- **Elecrow CrowPanel 2.13" ESP32-S3 e-ink** — ordered from Amazon ~$25
- Plan: Arduino sketch polls `https://raw.githubusercontent.com/tdoerks/open-source-lab-resources/main/checkin-board/status.json` every 10 min
- Displays: current status + note + QR code linking to web checkin-board
- Plugs in via USB-C (no built-in battery); 3D print case from Hale Library makerspace
- **Next**: Write Arduino sketch + flash via Arduino IDE

### BaseSpace download (pending)
- Run: `7-17-26_NARMS-NGS_BWGS_2026-07-17T21_35_42_9845731` (BCLConvert, 2GB)
- CLI: `C:\Users\tdoerks\Downloads\BaseSpace\bs.exe` — run from WSL terminal (not Docker)

## Skills to Add Later
- https://github.com/K-Dense-AI/scientific-agent-skills
- https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/research/bioinformatics/SKILL.md
- https://github.com/GPTomics/bioSkills/tree/main/primer-design
- https://skillsmp.com/ (skills marketplace — browse for relevant skills to install)

## Key Patterns
- **Pasting multi-line commands into Beocat terminal joins lines** → give ONE command per code block, paste each separately. Long lines (~>100 chars) also get spaces inserted at wrap points (breaks quoted paths/python -c) → keep commands short, use variables (e.g. `F=path` then `find $F …`)
- COMPASS log: `tail -f compass*stdout*<JOBID>*` (NOT `slurm-<JOBID>.out`)
- ARBOR log: `tail -f arbor_head_<JOBID>.log`
- Beocat jobs: `squeue -u tylerdoe`
- Lock file stuck: check `squeue`, cancel zombie job, then `rm -f .nextflow/cache/.../db/LOCK`
- SLURM preemption: just resubmit with `sbatch run_arbor.sbatch` (-resume handles it)
- Cancel duplicate job if submitted twice: `scancel <JOBID>`
- BaseSpace dirs have read-only permissions — `chmod u+w <dir>` before mv/rm

## How to Use This File
- At the start of a session, read this file to get context
- To save progress: "update CLAUDE.md with where we left off"
