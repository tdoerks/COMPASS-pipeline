# MIC/AST → assembly-mode workflow

Turn an **NCBI Isolates Browser** export into a COMPASS `assembly`-mode run: for
bacteria that have phenotypic susceptibility (MIC/AST) data, feed their genome
**assembly accessions** to COMPASS, which downloads each FASTA itself
(`modules/download_assembly.nf`). No SRA reads, no SPAdes, no pre-staging.

## 1. Get the isolates export
In the [Isolates Browser](https://www.ncbi.nlm.nih.gov/pathogens/isolates/),
filter to your organism (optionally cross-selected from the AST Browser so every
isolate has MIC/AST), and **Download** the table (TSV; the file may be named
`.csv`). It carries `#Organism group`, `BioSample`, `Assembly` (GCA), and
`AST phenotypes` columns.

## 2. Build the samplesheet
```bash
python3 bin/make_samplesheet.py isolates.csv -o samplesheet.csv
```
- Auto-detects tab vs comma delimiter.
- Keeps only isolates that have a **GCA/GCF assembly** AND at least one
  **interpreted AST result** (`R`/`I`/`S`) — i.e. real MIC/AST data.
  Pass `--all` to keep isolates whose AST is all `ND`/absent.
- Maps `#Organism group` to a valid **AMRFinder+** organism (e.g.
  `E.coli and Shigella` → `Escherichia`).
- Emits `sample,organism,assembly_accession` (COMPASS `--input_mode assembly`).

Make a small test batch before committing cluster time:
```bash
head -n 21 samplesheet.csv > samplesheet_test.csv   # header + 20
wc -l samplesheet.csv samplesheet_test.csv
```

## 3. Run
Edit paths in `run_compass_ecoli.sbatch`, then:
```bash
sbatch run_compass_ecoli.sbatch
squeue -u $USER
tail -f compass.stdout.*
```
For the full run, point `INPUT` at `samplesheet.csv`, set a fresh `OUTDIR`/`-J`,
and export an `NCBI_API_KEY` (one Entrez download per genome — avoids rate limits
at scale).

## Notes
- Assembly mode skips read-based QC (no reads) but still runs MLST, serotyping,
  plasmids, AMRFinder+/ABRicate, and VIBRANT phage analysis on the contigs.
- Fully automated alternative: `bin/fetch_mic_samples.py` (on the
  `add-mic-sample-fetcher` branch) pulls has-MIC/AST genomes straight from NCBI
  FTP + BV-BRC into this same samplesheet format, skipping the manual download.
