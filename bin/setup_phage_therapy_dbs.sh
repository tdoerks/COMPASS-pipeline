#!/bin/bash
#==============================================================================
# One-time database setup for the COMPASS phage-therapy add-ons.
# Run on a node WITH internet (Beocat login node), from the repo root:
#     bash bin/setup_phage_therapy_dbs.sh [/fastscratch/tylerdoe/databases]
#
#   DefenseFinder models -> <DB>/defensefinder_models              (params.defensefinder_models)
#   PADLOC database      -> <DB>/padloc_db                         (params.padloc_db)
#   ECTyper MASH sketch  -> <DB>/ectyper/EnteroRef_GTDBSketch_20231003_V2.msh (+ .txt metadata)
#                                                                  (params.ectyper_mash)
# Safe to rerun: existing pieces are kept.
#==============================================================================
set -euo pipefail

DB="${1:-/fastscratch/tylerdoe/databases}"
DF_IMG="docker://quay.io/biocontainers/defense-finder:3.0.0--pyhdfd78af_0"
EC_IMG="docker://quay.io/biocontainers/ectyper:2.0.0--pyhdfd78af_4"
PL_IMG="docker://quay.io/biocontainers/padloc:2.0.0--hdfd78af_1"
SKETCH_URL="https://zenodo.org/records/13969103/files/EnteroRef_GTDBSketch_20231003_V2.msh?download=1"

module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
export APPTAINER_CACHEDIR="${APPTAINER_CACHEDIR:-/fastscratch/tylerdoe/apptainer_cache}"

mkdir -p "${DB}/defensefinder_models" "${DB}/ectyper" "${DB}/padloc_db"

echo "== DefenseFinder models -> ${DB}/defensefinder_models"
if ls "${DB}/defensefinder_models" | grep -qi defense-finder-models && ls "${DB}/defensefinder_models" | grep -qi casfinder; then
    echo "   already installed: $(ls "${DB}/defensefinder_models" | tr '\n' ' ')"
else
    apptainer exec --bind "${DB}" "${DF_IMG}" defense-finder update --models-dir "${DB}/defensefinder_models"
    echo "   installed: $(ls "${DB}/defensefinder_models" | tr '\n' ' ')"
fi

echo "== PADLOC database -> ${DB}/padloc_db"
if [ -n "$(ls -A "${DB}/padloc_db" 2>/dev/null)" ]; then
    echo "   already installed ($(du -sh "${DB}/padloc_db" | cut -f1))"
else
    # padloc --db-update ignores --data and writes to its own install dir (/usr/local/data),
    # which is read-only in the container — so bind our directory over that path instead.
    apptainer exec --bind "${DB}/padloc_db:/usr/local/data" "${PL_IMG}" padloc --db-update \
        && echo "   installed ($(du -sh "${DB}/padloc_db" | cut -f1))" \
        || echo "   WARNING: padloc --db-update failed"
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
echo "   padloc_db            = ${DB}/padloc_db"
echo "   ectyper_mash         = ${SKETCH}"
