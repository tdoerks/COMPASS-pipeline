# COMPASS Development Session — July 30–31, 2026

**Branch:** `1.1.0` (run from `/fastscratch/tylerdoe/COMPASS-1.1.0` on Beocat)
**Status:** E. coli MIC/AST test batch (20 samples) finally running clean in `--input_mode fasta`; 6k bulk download in progress

---

## 🎯 Session Goals

1. Diagnose why the `compass-ecoli` run (job 10228569, Jul 23) failed
2. Fix and rerun the E. coli MIC/AST test batch (20 samples)
3. Prep the full ~5,589-sample run

---

## ✅ What we did

### Root cause 1: Container bind mount of missing directory → exit 255 on ALL steps

**Symptom:** Every containerized process died immediately with exit 255:
```
FATAL: container creation failed: mount .../COMPASS-1.1.0/databases: doesn't exist
```

**Cause:** `nextflow.config` line 128 runs every container with:
```
runOptions = "--no-home --contain --bind ${params.database_dir}:${params.database_dir}..."
```
`params.database_dir` defaults to `${projectDir}/databases`. When launching from
`/fastscratch/tylerdoe/COMPASS-1.1.0`, Apptainer refuses to start any container if the
bind *source* doesn't exist. The real databases live at `/fastscratch/tylerdoe/databases`
— not inside the clone.

**Fix:** Pass `--database_dir /fastscratch/tylerdoe/databases` in the sbatch. This makes
the bind source a real directory (not a missing symlink). Added to `run_compass_ecoli.sbatch`:
```bash
--database_dir "/fastscratch/tylerdoe/databases" \
```

**Important:** Symlinks don't work here. Apptainer binds the symlink path but can't follow
the symlink's target through `--contain`, so the container still can't see the files.
Point at the **real directory** directly.

---

### Root cause 2: `--prophage_db` path outside the container bind → cp fails

**Symptom:** After fix 1, `DOWNLOAD_PROPHAGE_DB` still failed:
```
cp /homes/tylerdoe/databases/prophage_db.dmnd .
WARNING: ... chdir /homes/tylerdoe: no such file or directory
cp: cannot stat '...prophage_db.dmnd': No such file or directory
```

**Cause:** The sbatch overrode `--prophage_db` with `/homes/tylerdoe/databases/...`. Under
`--contain --no-home`, `/homes` is not mounted, so the container's `cp` can't find the file.
The campy run that worked used the exact same path — it worked because the campy run launched
from `$HOME/COMPASS-pipeline` where `/homes` *is* on the bind path as the projectDir parent.
Launching from `/fastscratch` breaks that implicit mount.

**Fix:** Point `--prophage_db` at the path inside the `--database_dir` bind:
```bash
PROPHAGE_DB="/fastscratch/tylerdoe/databases/prophage_db.dmnd"
```

**Key rule:** Any path passed to COMPASS params that gets used inside a container must live
*under* `params.database_dir` (the bound path) or `/fastscratch` (auto-mounted). `/homes`
is not available under `--contain` unless it is the projectDir.

---

### Root cause 3: `DOWNLOAD_ASSEMBLY` uses broken efetch method — HTTP 400/429

**Symptom:** After fixes 1+2, all `DOWNLOAD_ASSEMBLY` tasks failed:
- First run: `429 Too Many Requests` (rate-limiting)
- After adding throttle (`maxForks=2`, `errorStrategy='retry'`): `400 Bad Request` + `EMPTY RESULT`

**Cause:** The `DOWNLOAD_ASSEMBLY` module uses `esearch -db assembly | efetch -format fasta`,
which queries NCBI's Assembly *metadata* database — not a sequence database. Fetching
`-format fasta` from `-db assembly` returns empty/400 regardless of rate limiting. The method
is fundamentally broken for pulling genome FASTAs. (An API key would NOT have fixed this.)

**Fix:** Pre-download genomes using the **NCBI `datasets` CLI** (the correct modern tool),
then run COMPASS with `--input_mode fasta` pointing at local FASTAs. This is exactly how the
`data/validation/` framework worked for the ~200 E. coli reference genome validation.

**Step-by-step for the E. coli MIC/AST test batch (20 samples):**

```bash
cd /fastscratch/tylerdoe/COMPASS-1.1.0

# 1. extract accessions (strip Windows \r)
tail -n +2 samplesheet_test.csv | tr -d '\r' | cut -d, -f3 > accs.txt

# 2. bulk download (one API call, all accessions)
~/bin/datasets download genome accession --inputfile accs.txt \
  --include genome --filename genomes.zip
unzip -oq genomes.zip -d genomes_dl

# 3. build fasta samplesheet (NOTE: tr -d '\r' is required — Windows line endings break glob)
echo "sample,fasta,organism" > samplesheet_fasta.csv
tail -n +2 samplesheet_test.csv | tr -d '\r' | while IFS=, read -r s org acc; do
  f=$(echo "$PWD/genomes_dl/ncbi_dataset/data/$acc/"*.fna)
  echo "$s,$f,$org" >> samplesheet_fasta.csv
done

# 4. copy sbatch and retarget to fasta mode
cp run_compass_ecoli.sbatch run_compass_fasta.sbatch
sed -i -e 's|--input_mode assembly|--input_mode fasta|' \
       -e 's|samplesheet_test.csv|samplesheet_fasta.csv|' \
       -e 's|results_mic_ecoli_test|results_mic_ecoli_fasta|' run_compass_fasta.sbatch

sbatch run_compass_fasta.sbatch   # job 10430853 — ran clean ✅
```

**Result:** Job 10430853 ran clean — QUAST, AMRFINDER, ABRICATE (×4 DBs), VIBRANT,
DIAMOND_PROPHAGE, MLST, SISTR, MOBSUITE_RECON all completed. Zero NCBI calls during pipeline.

---

## 📋 Underlying config smell (not yet fixed)

`nextflow.config` lines 38/39/46 hardcode `${projectDir}/databases/...` for `prophage_db`,
`prophage_metadata`, and `busco_download_path` instead of `${params.database_dir}/...`.
This means those three params can't be overridden via `--database_dir` alone — they always
resolve relative to the launch dir. Any run not launched from a dir containing a `databases/`
symlink or subdirectory breaks. A future fix: replace `${projectDir}/databases` with
`${params.database_dir}` in those three lines.

---

## 🚀 6k run prep (in progress)

**Approach:** Same `--input_mode fasta` workflow, batched `datasets` download.

```bash
cd /fastscratch/tylerdoe/COMPASS-1.1.0
tail -n +2 samplesheet.csv | tr -d '\r' | cut -d, -f3 > accs_full.txt  # 5589 accessions
split -l 500 accs_full.txt batch_
for b in batch_*; do
  ~/bin/datasets download genome accession --inputfile "$b" \
    --include genome --filename "${b}.zip"
  unzip -oq "${b}.zip" -d "${b}_dl"
  rm "${b}.zip"
done
find batch_*_dl -name "*.fna" | wc -l   # should be 5589
```

Disk: 32 TB free on `/fastscratch` — not a concern.
BUSCO: off (`--skip_busco`) matching test batch.
Head-job: bump `NXF_OPTS='-Xmx12g'`, keep 7-day walltime.

**Status:** Bulk download in progress (July 31).

---

## Key lessons for future E. coli / COMPASS runs on Beocat

| Problem | Symptom | Fix |
|---|---|---|
| Missing `databases/` dir | exit 255, container creation failed | `--database_dir /fastscratch/tylerdoe/databases` |
| `--prophage_db` outside bind | `cp: cannot stat`, exit 1 | Point to path inside `--database_dir` |
| `esearch\|efetch` for assembly download | HTTP 400/429, empty result | Pre-download with `datasets`; use `--input_mode fasta` |
| Windows `\r` in samplesheet | Glob fails, `*` in fasta paths | `tr -d '\r'` when reading the CSV |
