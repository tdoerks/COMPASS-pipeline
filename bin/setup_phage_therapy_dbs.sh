#!/bin/bash
#==============================================================================
# One-time database setup for the COMPASS phage-therapy add-ons.
# Run on a node WITH internet (Beocat login node), from the repo root:
#     bash bin/setup_phage_therapy_dbs.sh [/fastscratch/tylerdoe/databases]
#
#   DefenseFinder models -> <DB>/defensefinder_models              (params.defensefinder_models)
#   ECTyper MASH sketch  -> <DB>/ectyper/EnteroRef_GTDBSketch_20231003_V2.msh (+ .txt metadata)
#                                                                  (params.ectyper_mash)
# Safe to rerun: existing pieces are kept.
#==============================================================================
set -euo pipefail

DB="${1:-/fastscratch/tylerdoe/databases}"
DF_IMG="docker://quay.io/biocontainers/defense-finder:3.0.0--pyhdfd78af_0"
EC_IMG="docker://quay.io/biocontainers/ectyper:2.0.0--pyhdfd78af_4"
SKETCH_URL="https://zenodo.org/records/13969103/files/EnteroRef_GTDBSketch_20231003_V2.msh?download=1"

module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
export APPTAINER_CACHEDIR="${APPTAINER_CACHEDIR:-/fastscratch/tylerdoe/apptainer_cache}"

mkdir -p "${DB}/defensefinder_models" "${DB}/ectyper"

echo "== DefenseFinder models -> ${DB}/defensefinder_models"
if ls "${DB}/defensefinder_models" | grep -qi defense-finder-models && ls "${DB}/defensefinder_models" | grep -qi casfinder; then
    echo "   already installed: $(ls "${DB}/defensefinder_models" | tr '\n' ' ')"
else
    apptainer exec --bind "${DB}" "${DF_IMG}" defense-finder update --models-dir "${DB}/defensefinder_models"
    echo "   installed: $(ls "${DB}/defensefinder_models" | tr '\n' ' ')"
fi

SKETCH="${DB}/ectyper/EnteroRef_GTDBSketch_20231003_V2.msh"
echo "== ECTyper species sketch -> ${SKETCH}"
if [ -s "${SKETCH}" ]; then
    echo "   already downloaded ($(du -h "${SKETCH}" | cut -f1))"
else
    curl -L --fail --retry 3 -o "${SKETCH}.part" "${SKETCH_URL}" && mv "${SKETCH}.part" "${SKETCH}"
fi
# ECTyper insists on <sketch>.txt (mash info) next to the sketch, else it tries to re-download
if [ ! -s "${SKETCH}.txt" ]; then
    apptainer exec --bind "${DB}" "${EC_IMG}" mash info -t "${SKETCH}" > "${SKETCH}.txt"
fi
echo "   sketch $(du -h "${SKETCH}" | cut -f1), metadata $(wc -l < "${SKETCH}.txt") lines"

echo ""
echo "Done. conf/beocat.config already points at these paths:"
echo "   defensefinder_models = ${DB}/defensefinder_models"
echo "   ectyper_mash         = ${SKETCH}"
