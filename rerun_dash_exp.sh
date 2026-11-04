#!/bin/bash
set -euo pipefail

COMPASS=/fastscratch/tylerdoe/COMPASS-phage-therapy
OUTDIR=/fastscratch/tylerdoe/COMPASS-phage-therapy/results_stec_500_pt
TSV=/fastscratch/tylerdoe/COMPASS-phage-therapy/compass_summary_pt.tsv

python3 "$COMPASS/bin/generate_compass_summary.py" \
    --outdir "$OUTDIR" \
    --output_tsv "$TSV"

echo "Done. HTML at: $OUTDIR/compass_summary.html"
