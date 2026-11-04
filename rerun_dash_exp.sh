#!/bin/bash
set -euo pipefail

COMPASS=/fastscratch/tylerdoe/COMPASS-phage-therapy
OUTDIR=/fastscratch/tylerdoe/COMPASS-phage-therapy/results_stec_500_pt
TSV=/fastscratch/tylerdoe/COMPASS-phage-therapy/compass_summary_pt.tsv

cd "$COMPASS"

python3 bin/generate_compass_summary.py \
    --outdir "$OUTDIR" \
    --output_tsv "$TSV" \
    --output_html "$COMPASS/compass_summary.html"

echo "Done. HTML at: $COMPASS/compass_summary.html"
