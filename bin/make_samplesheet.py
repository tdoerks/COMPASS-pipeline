#!/usr/bin/env python3
"""Isolates-browser export (TSV or CSV) -> COMPASS assembly-mode samplesheet
(sample,organism,assembly_accession). Auto-detects delimiter.
Default: keep only isolates with a GCA/GCF assembly AND >=1 interpreted AST result (R/I/S);
--all keeps isolates whose AST is all ND/absent."""
import csv, sys, argparse

ORG_MAP = {"E.coli and Shigella":"Escherichia","Salmonella enterica":"Salmonella",
           "Campylobacter jejuni":"Campylobacter","Klebsiella pneumoniae":"Klebsiella_pneumoniae"}
def org(g):
    g=(g or "").strip(); return ORG_MAP.get(g, g.split()[0].split(".")[0].capitalize() if g else "")
def has_ast(s):
    return any("=" in p and p.split("=",1)[1].strip().upper() in ("R","I","S") for p in (s or "").split(","))

ap=argparse.ArgumentParser(); ap.add_argument("infile"); ap.add_argument("-o","--output",default="samplesheet.csv")
ap.add_argument("--all",action="store_true"); a=ap.parse_args()

with open(a.infile,newline='') as f:
    header=f.readline()
delim='\t' if '\t' in header else ','      # NCBI Isolates Browser = TSV; fall back to CSV
sys.stderr.write(f"delimiter detected: {'TAB' if delim==chr(9) else 'COMMA'}\n")

seen,rows,no_asm,no_ast=set(),[],0,0
with open(a.infile,newline='') as f:
    for row in csv.DictReader(f,delimiter=delim):
        gca=(row.get("Assembly") or "").strip()
        if not gca.startswith(("GCA_","GCF_")): no_asm+=1; continue
        if gca in seen: continue
        if not a.all and not has_ast(row.get("AST phenotypes","")): no_ast+=1; continue
        seen.add(gca); rows.append((gca.replace(".","_"), org(row.get("#Organism group","")), gca))

with open(a.output,"w",newline='') as f:
    w=csv.writer(f); w.writerow(["sample","organism","assembly_accession"]); w.writerows(rows)
sys.stderr.write(f"{len(rows)} samples -> {a.output} | skipped no-assembly:{no_asm} all-ND-AST:{no_ast}\n")
