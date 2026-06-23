#!/usr/bin/env python3
"""
fetch_mic_samples.py — Build a COMPASS assembly-mode samplesheet of bacterial
genomes that have phenotypic susceptibility (MIC / AST) data, merged from two
public sources and deduplicated by NCBI GCA/GCF assembly accession.

Sources
-------
* NCBI Pathogen Detection (the system behind MicroBIGG-E): per-organism metadata
  TSVs on FTP carry an `AST_phenotypes` column (S/I/R interpretations, e.g.
  `ciprofloxacin=R`) and an `asm_acc` GCA accession. No auth. Tens of thousands
  of isolates across ~106 organisms.
* BV-BRC genome_amr (laboratory_typing_method = MIC): true MIC values (mg/L) for
  ~625 genomes that have a resolvable GCA/GCF accession. No auth.

Output is COMPASS `assembly` input mode: a samplesheet of
`sample,organism,assembly_accession`. COMPASS itself downloads each FASTA from
NCBI (modules/download_assembly.nf), so we only emit accessions.

Usage
-----
    # smoke test
    python fetch_mic_samples.py --organisms Campylobacter --max 20 --output-dir /tmp/mic_test
    # everything, both sources merged
    python fetch_mic_samples.py --output-dir ./mic_all
    # one source only
    python fetch_mic_samples.py --source ncbi --output-dir ./ncbi_only

Outputs (in --output-dir)
    samplesheet.csv          sample,organism,assembly_accession   (COMPASS assembly mode)
    mic_metadata.csv         per-genome phenotype: sir_<drug> (NCBI) + mic_<drug> (BV-BRC)
    by_organism/<org>.csv    samplesheet split per organism, for batching the cluster run
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict

# --- NCBI Pathogen Detection -------------------------------------------------
PD_BASE = "https://ftp.ncbi.nlm.nih.gov/pathogen/Results/"

# --- BV-BRC ------------------------------------------------------------------
BVBRC = "https://www.bv-brc.org/api"
BATCH = 500
AMR_LIMIT = 25000

GCA_RE = re.compile(r"GC[AF]_\d+\.\d+")   # NCBI assembly accession pattern


# ============================================================================
# Shared helpers
# ============================================================================
def clean_sample_id(accession):
    """Filename-safe sample id from an accession (GCA_005281955.1 -> GCA_005281955_1)."""
    return accession.replace(".", "_")


def dequote(s):
    """Strip CSV-style quoting that NCBI's TSV uses for fields containing commas."""
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1].replace('""', '"')
    return s


def safe_filename(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "unknown"


def http_get(url, timeout=60, retries=3, accept=None):
    headers = {"Accept": accept} if accept else {}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429,) or e.code >= 500:
                time.sleep(2 ** attempt)
            else:
                raise
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return b""


# ============================================================================
# NCBI Pathogen Detection
# ============================================================================
def list_pd_organisms():
    html = http_get(PD_BASE, timeout=30).decode(errors="replace")
    orgs = re.findall(r'href="([A-Z][A-Za-z0-9_]+)/"', html)
    # Drop non-organism helper dirs
    return [o for o in orgs if o not in ("BioProject_Hierarchy",)]


def latest_pdg(org):
    html = http_get(f"{PD_BASE}{org}/", timeout=30).decode(errors="replace")
    dirs = re.findall(r'href="(PDG\d+\.\d+)/"', html)
    if not dirs:
        return None
    return sorted(dirs, key=lambda d: int(d.split(".")[-1]))[-1]


def parse_ast(s):
    """Parse 'drug=R,drug=S,...' into {drug: interpretation}."""
    out = {}
    for part in s.split(","):
        part = part.strip()
        if "=" in part:
            drug, val = part.split("=", 1)
            drug = drug.strip().lower()
            val = val.strip()
            if drug and val:
                out[drug] = val
    return out


def stream_pd_metadata(org, limit=None):
    """
    Stream the latest metadata.tsv for one organism, yielding dicts for rows that
    have AST data AND a GCA/GCF assembly accession. Streams line-by-line so the
    ~800 MB files never load into memory.
    """
    pdg = latest_pdg(org)
    if not pdg:
        return
    url = f"{PD_BASE}{org}/{pdg}/Metadata/{pdg}.metadata.tsv"

    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=120)
    except Exception as e:
        print(f"  [{org}] skip: {e}", flush=True)
        return

    with resp:
        header_line = resp.readline().decode(errors="replace").rstrip("\n")
        if not header_line:
            return
        header = header_line.split("\t")
        idx = {name: i for i, name in enumerate(header)}

        i_asm = idx.get("asm_acc")
        i_ast = idx.get("AST_phenotypes")
        if i_asm is None or i_ast is None:
            return  # this organism's table has no AST/assembly columns

        i_org = idx.get("scientific_name", idx.get("taxgroup_name"))
        i_bio = idx.get("biosample_acc")
        i_strain = idx.get("strain")

        n = 0
        for raw in resp:
            cols = raw.decode(errors="replace").rstrip("\n").split("\t")
            if len(cols) <= max(i_asm, i_ast):
                continue
            asm = dequote(cols[i_asm])
            ast = dequote(cols[i_ast])
            if not ast or ast.upper() in ("NULL", "NA"):
                continue
            if not GCA_RE.fullmatch(asm):
                continue
            organism = dequote(cols[i_org]) if (i_org is not None and i_org < len(cols)) else org
            yield {
                "assembly_accession": asm,
                "organism": organism or org,
                "biosample": dequote(cols[i_bio]) if (i_bio is not None and i_bio < len(cols)) else "",
                "strain": dequote(cols[i_strain]) if (i_strain is not None and i_strain < len(cols)) else "",
                "sir": parse_ast(ast),
            }
            n += 1
            if limit and n >= limit:
                return


def fetch_ncbi_pd(organisms=None, max_total=None):
    """Sweep NCBI Pathogen Detection. Returns {accession: record}."""
    if organisms is None:
        print("Listing NCBI Pathogen Detection organisms...", flush=True)
        organisms = list_pd_organisms()
        print(f"  {len(organisms)} organisms to sweep", flush=True)

    records = {}
    for org in organisms:
        before = len(records)
        remaining = (max_total - len(records)) if max_total else None
        if remaining is not None and remaining <= 0:
            break
        for rec in stream_pd_metadata(org, limit=remaining):
            acc = rec["assembly_accession"]
            if acc not in records:
                records[acc] = rec
            if max_total and len(records) >= max_total:
                break
        kept = len(records) - before
        if kept:
            print(f"  [{org}] +{kept} (total {len(records)})", flush=True)
    print(f"NCBI Pathogen Detection: {len(records)} isolates with AST + assembly", flush=True)
    return records


# ============================================================================
# BV-BRC
# ============================================================================
def bvbrc_get(table, rql, retries=3):
    url = f"{BVBRC}/{table}/?{rql}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(2 ** attempt)
            else:
                raise
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return []


def find_assembly_accession(genome):
    """BV-BRC stores the GCA/GCF accession inconsistently across fields — search all."""
    for field in ("assembly_accession", "genbank_accessions", "refseq_accessions"):
        val = genome.get(field, "")
        if isinstance(val, list):
            val = " ".join(val)
        m = GCA_RE.search(val or "")
        if m:
            return m.group(0)
    return None


def fetch_bvbrc_mic(species=None, max_total=None):
    """Return {accession: record} for BV-BRC genomes with lab MIC + a GCA accession."""
    filters = ["eq(laboratory_typing_method,MIC)"]
    if species:
        filters.append(f"eq(genome_name,*{urllib.parse.quote(species)}*)")
    rql = "&".join(filters) + (
        f"&limit({AMR_LIMIT})&select(genome_id,antibiotic,measurement,"
        f"measurement_value,measurement_unit)")
    print("Querying BV-BRC genome_amr (MIC)...", flush=True)
    rows = bvbrc_get("genome_amr", rql)
    print(f"  {len(rows)} MIC records", flush=True)

    mic_by_genome = defaultdict(dict)
    for row in rows:
        gid = row.get("genome_id")
        ab = (row.get("antibiotic") or "").strip().lower()
        if gid and ab:
            mic_by_genome[gid][ab] = row.get("measurement") or row.get("measurement_value") or ""

    genome_ids = list(mic_by_genome.keys())
    print(f"  {len(genome_ids)} genomes with MIC; fetching assembly accessions...", flush=True)

    records = {}
    for i in range(0, len(genome_ids), BATCH):
        batch = genome_ids[i:i + BATCH]
        rql = (f"in(genome_id,({','.join(batch)}))&limit({BATCH})"
               f"&select(genome_id,species,assembly_accession,genbank_accessions,refseq_accessions)")
        for g in bvbrc_get("genome", rql):
            acc = find_assembly_accession(g)
            if not acc:
                continue
            records[acc] = {
                "assembly_accession": acc,
                "organism": g.get("species", ""),
                "biosample": "",
                "strain": "",
                "mic": mic_by_genome.get(g["genome_id"], {}),
            }
            if max_total and len(records) >= max_total:
                break
        time.sleep(0.3)
        if max_total and len(records) >= max_total:
            break
    print(f"BV-BRC: {len(records)} genomes with MIC + assembly", flush=True)
    return records


# ============================================================================
# Merge + output
# ============================================================================
def merge_sources(ncbi, bvbrc):
    """Merge two {accession: record} dicts into one, combining sir{} and mic{}."""
    merged = {}
    for acc in set(ncbi) | set(bvbrc):
        n = ncbi.get(acc, {})
        b = bvbrc.get(acc, {})
        sources = []
        if n:
            sources.append("ncbi_pd")
        if b:
            sources.append("bvbrc")
        merged[acc] = {
            "assembly_accession": acc,
            "organism": n.get("organism") or b.get("organism") or "",
            "biosample": n.get("biosample") or b.get("biosample") or "",
            "strain": n.get("strain") or b.get("strain") or "",
            "sources": "+".join(sources),
            "sir": n.get("sir", {}),
            "mic": b.get("mic", {}),
        }
    return merged


def write_outputs(merged, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    by_org_dir = os.path.join(output_dir, "by_organism")
    os.makedirs(by_org_dir, exist_ok=True)

    records = sorted(merged.values(), key=lambda r: (r["organism"], r["assembly_accession"]))

    # samplesheet.csv (COMPASS assembly mode)
    sheet = os.path.join(output_dir, "samplesheet.csv")
    with open(sheet, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sample", "organism", "assembly_accession"])
        w.writeheader()
        for r in records:
            w.writerow({
                "sample": clean_sample_id(r["assembly_accession"]),
                "organism": r["organism"] or "Unknown",
                "assembly_accession": r["assembly_accession"],
            })

    # by_organism split
    per_org = defaultdict(list)
    for r in records:
        per_org[r["organism"] or "Unknown"].append(r)
    for org, recs in per_org.items():
        path = os.path.join(by_org_dir, safe_filename(org) + ".csv")
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["sample", "organism", "assembly_accession"])
            w.writeheader()
            for r in recs:
                w.writerow({
                    "sample": clean_sample_id(r["assembly_accession"]),
                    "organism": r["organism"] or "Unknown",
                    "assembly_accession": r["assembly_accession"],
                })

    # mic_metadata.csv (wide: sir_<drug> + mic_<drug>)
    all_sir = sorted({d for r in records for d in r["sir"]})
    all_mic = sorted({d for r in records for d in r["mic"]})
    meta = os.path.join(output_dir, "mic_metadata.csv")
    base_cols = ["sample", "assembly_accession", "organism", "sources", "biosample", "strain"]
    fields = base_cols + [f"sir_{d.replace(' ', '_')}" for d in all_sir] \
                       + [f"mic_{d.replace(' ', '_')}" for d in all_mic]
    with open(meta, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in records:
            row = {
                "sample": clean_sample_id(r["assembly_accession"]),
                "assembly_accession": r["assembly_accession"],
                "organism": r["organism"],
                "sources": r["sources"],
                "biosample": r["biosample"],
                "strain": r["strain"],
            }
            for d in all_sir:
                row[f"sir_{d.replace(' ', '_')}"] = r["sir"].get(d, "")
            for d in all_mic:
                row[f"mic_{d.replace(' ', '_')}"] = r["mic"].get(d, "")
            w.writerow(row)

    return sheet, meta, per_org


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=["both", "ncbi", "bvbrc"], default="both",
                        help="Which phenotype source(s) to pull (default: both)")
    parser.add_argument("--organisms", default=None,
                        help="Comma-separated NCBI PD organism dir names to restrict to "
                             "(default: all). Also used as BV-BRC species filter when single.")
    parser.add_argument("--max", type=int, default=None,
                        help="Cap total genomes per source (for testing)")
    parser.add_argument("--output-dir", default="./mic_run",
                        help="Output directory (created if absent)")
    args = parser.parse_args()

    organisms = [o.strip() for o in args.organisms.split(",")] if args.organisms else None

    ncbi_records = {}
    bvbrc_records = {}

    if args.source in ("both", "ncbi"):
        ncbi_records = fetch_ncbi_pd(organisms=organisms, max_total=args.max)

    if args.source in ("both", "bvbrc"):
        species = organisms[0].replace("_", " ") if (organisms and len(organisms) == 1) else None
        bvbrc_records = fetch_bvbrc_mic(species=species, max_total=args.max)

    merged = merge_sources(ncbi_records, bvbrc_records)
    print(f"\nMerged total: {len(merged)} unique assemblies "
          f"({len(ncbi_records)} NCBI PD, {len(bvbrc_records)} BV-BRC, "
          f"{len(set(ncbi_records) & set(bvbrc_records))} in both)", flush=True)

    if not merged:
        print("No records — check filters/source.")
        sys.exit(0)

    sheet, meta, per_org = write_outputs(merged, args.output_dir)

    print(f"\nWrote:")
    print(f"  {sheet}  ({len(merged)} genomes)")
    print(f"  {meta}")
    print(f"  {os.path.join(args.output_dir, 'by_organism')}/  ({len(per_org)} organisms)")
    print(f"\nPer-organism counts (top 20):")
    for org, recs in sorted(per_org.items(), key=lambda kv: -len(kv[1]))[:20]:
        print(f"  {len(recs):6d}  {org}")


if __name__ == "__main__":
    main()
