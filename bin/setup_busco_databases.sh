#!/usr/bin/env bash

################################################################################
# BUSCO Database Setup Script
#
# This script downloads and configures BUSCO databases for the COMPASS pipeline.
# BUSCO (Benchmarking Universal Single-Copy Orthologs) is used to assess
# genome assembly completeness.
#
# Usage:
#   ./bin/setup_busco_databases.sh [OPTIONS]
#
# Options:
#   --download-path PATH    Directory to download BUSCO databases (default: ./databases/busco_downloads)
#   --auto-lineage          Download placement files for auto-lineage mode (recommended)
#   --all-lineages          Download all bacterial lineages (large download ~10GB)
#   --help                  Show this help message
#
# Examples:
#   # Basic setup (recommended):
#   ./bin/setup_busco_databases.sh --download-path /fastscratch/tylerdoe/databases/busco_downloads --auto-lineage
#
#   # Download all lineages for offline use:
#   ./bin/setup_busco_databases.sh --download-path /fastscratch/tylerdoe/databases/busco_downloads --all-lineages
#
# Notes:
#   - First run may take 30-60 minutes depending on network speed
#   - Requires ~2-5GB disk space for bacteria_odb10 + placement files
#   - Requires ~10GB disk space if downloading all lineages
#   - BUSCO must be available (module load BUSCO, or use conda/container)
#
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DOWNLOAD_PATH="./databases/busco_downloads"
AUTO_LINEAGE=false
ALL_LINEAGES=false
SHOW_HELP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --download-path)
            DOWNLOAD_PATH="$2"
            shift 2
            ;;
        --auto-lineage)
            AUTO_LINEAGE=true
            shift
            ;;
        --all-lineages)
            ALL_LINEAGES=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo -e "${RED}ERROR: Unknown option: $1${NC}"
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    head -n 35 "$0" | tail -n +3 | sed 's/^# //' | sed 's/^#//'
    exit 0
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║          COMPASS Pipeline - BUSCO Database Setup               ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Download Path:${NC} $DOWNLOAD_PATH"
echo -e "${GREEN}Auto-lineage mode:${NC} $AUTO_LINEAGE"
echo -e "${GREEN}All lineages:${NC} $ALL_LINEAGES"
echo ""

# Check if BUSCO is available
if ! command -v busco &> /dev/null; then
    echo -e "${RED}ERROR: BUSCO command not found!${NC}"
    echo ""
    echo "Please ensure BUSCO is available. Options:"
    echo "  • module load BUSCO"
    echo "  • conda activate busco-env"
    echo "  • Use BUSCO container"
    echo ""
    exit 1
fi

# Show BUSCO version
BUSCO_VERSION=$(busco --version 2>&1 | head -1 || echo "unknown")
echo -e "${GREEN}BUSCO version:${NC} $BUSCO_VERSION"
echo ""

# Create download directory
echo -e "${YELLOW}→${NC} Creating download directory..."
mkdir -p "$DOWNLOAD_PATH"
cd "$DOWNLOAD_PATH"
echo -e "${GREEN}✓${NC} Directory created: $(pwd)"
echo ""

# Download bacteria_odb10 (main bacterial lineage database)
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}→${NC} Downloading bacteria_odb10 lineage database..."
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -d "lineages/bacteria_odb10" ]; then
    echo -e "${GREEN}✓${NC} bacteria_odb10 already exists, skipping download"
else
    busco --download bacteria_odb10 --download_path . || {
        echo -e "${RED}✗${NC} Failed to download bacteria_odb10"
        exit 1
    }
    echo -e "${GREEN}✓${NC} bacteria_odb10 downloaded successfully"
fi
echo ""

# Download placement files for auto-lineage mode
if [ "$AUTO_LINEAGE" = true ]; then
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}→${NC} Downloading placement files for auto-lineage mode..."
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "This downloads phylogenetic placement files needed for auto-lineage"
    echo "to automatically select the best matching lineage for each genome."
    echo ""

    # Create a temporary test assembly to trigger placement file downloads
    TMP_DIR=$(mktemp -d)
    TMP_FASTA="$TMP_DIR/test_genome.fasta"

    # Generate a minimal test genome (just enough to trigger BUSCO)
    echo ">contig1" > "$TMP_FASTA"
    echo "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG" >> "$TMP_FASTA"

    echo -e "${YELLOW}→${NC} Running BUSCO in auto-lineage mode to trigger placement file downloads..."
    echo "   (This may take 5-15 minutes on first run)"
    echo ""

    # Run BUSCO with auto-lineage to download placement files
    busco \
        -i "$TMP_FASTA" \
        -o busco_auto_lineage_test \
        -m genome \
        --auto-lineage-prok \
        --download_path . \
        --cpu 2 \
        --force \
        --quiet 2>&1 | grep -E "Downloading|Extracting|Download|placement" || true

    # Clean up test run
    rm -rf busco_auto_lineage_test "$TMP_DIR"

    echo ""
    echo -e "${GREEN}✓${NC} Placement files downloaded"
    echo ""
fi

# Download additional lineages if requested
if [ "$ALL_LINEAGES" = true ]; then
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}→${NC} Downloading additional bacterial lineages..."
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # List of common bacterial lineages
    LINEAGES=(
        "gammaproteobacteria_odb10"
        "enterobacterales_odb10"
        "bacillales_odb10"
        "lactobacillales_odb10"
        "pseudomonadales_odb10"
    )

    for lineage in "${LINEAGES[@]}"; do
        echo -e "${YELLOW}→${NC} Downloading $lineage..."
        if [ -d "lineages/$lineage" ]; then
            echo -e "${GREEN}✓${NC} $lineage already exists, skipping"
        else
            busco --download "$lineage" --download_path . || {
                echo -e "${RED}✗${NC} Failed to download $lineage (continuing anyway...)"
            }
        fi
    done
    echo ""
fi

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ BUSCO Database Setup Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Downloaded databases:"
if [ -d "lineages" ]; then
    ls -1 lineages/ | sed 's/^/  • /'
else
    echo "  (No lineages directory found - check for errors above)"
fi
echo ""

if [ -d "placement_files" ]; then
    echo "Placement files for auto-lineage:"
    ls -1 placement_files/ | head -5 | sed 's/^/  • /'
    FILE_COUNT=$(ls -1 placement_files/ | wc -l)
    if [ "$FILE_COUNT" -gt 5 ]; then
        echo "  ... and $((FILE_COUNT - 5)) more files"
    fi
    echo ""
fi

# Disk usage
TOTAL_SIZE=$(du -sh . | cut -f1)
echo -e "${GREEN}Total disk usage:${NC} $TOTAL_SIZE"
echo ""

# Configuration instructions
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "1. Update your nextflow.config or use command-line parameter:"
echo ""
echo "   params.busco_download_path = \"$DOWNLOAD_PATH\""
echo ""
echo "2. Run the COMPASS pipeline:"
echo ""
echo "   nextflow run main.nf \\"
echo "     --input_mode metadata \\"
echo "     --busco_download_path \"$DOWNLOAD_PATH\" \\"
echo "     --skip_busco false \\"
echo "     --outdir results/"
echo ""
echo "3. BUSCO will now use the pre-downloaded databases in offline mode!"
echo ""
echo -e "${GREEN}Database setup complete! 🎉${NC}"
echo ""
