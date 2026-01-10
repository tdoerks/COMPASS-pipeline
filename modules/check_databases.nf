/*
 * CHECK_DATABASES - Validate required databases exist before pipeline runs
 * Fails fast with helpful error messages if databases are missing
 */

process CHECK_DATABASES {
    label 'process_single'

    output:
    val true, emit: validated

    script:
    def busco_path = params.busco_download_path ?: '/tmp/busco_downloads'
    def prophage_db = params.prophage_db ?: ''
    def skip_busco = params.skip_busco ?: false
    def auto_lineage = params.busco_auto_lineage ?: false
    """
    #!/bin/bash
    set -e

    echo "════════════════════════════════════════════════════════════════"
    echo "COMPASS Pipeline - Database Validation"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    ERRORS=0
    WARNINGS=0

    # Check BUSCO databases (if not skipped)
    if [ "${skip_busco}" == "false" ]; then
        echo "→ Checking BUSCO databases..."

        # Check main bacteria lineage
        if [ -d "${busco_path}/lineages/bacteria_odb10" ]; then
            echo "  ✓ BUSCO bacteria_odb10 lineage found"
        else
            echo "  ❌ BUSCO bacteria_odb10 lineage NOT found!"
            echo "     Expected: ${busco_path}/lineages/bacteria_odb10"
            echo ""
            echo "     To fix, run:"
            echo "     ./bin/setup_busco_databases.sh \\\\"
            echo "         --download-path ${busco_path} \\\\"
            echo "         --auto-lineage"
            echo ""
            ERRORS=\$((ERRORS + 1))
        fi

        # Check placement files (if auto-lineage mode)
        if [ "${auto_lineage}" == "true" ]; then
            if [ -d "${busco_path}/placement_files" ] && [ -n "\$(ls -A ${busco_path}/placement_files 2>/dev/null)" ]; then
                echo "  ✓ BUSCO placement files found (auto-lineage mode)"
            else
                echo "  ❌ BUSCO placement files NOT found!"
                echo "     Auto-lineage mode requires placement files"
                echo "     Expected: ${busco_path}/placement_files/"
                echo ""
                echo "     To fix, run:"
                echo "     ./bin/setup_busco_databases.sh \\\\"
                echo "         --download-path ${busco_path} \\\\"
                echo "         --auto-lineage"
                echo ""
                ERRORS=\$((ERRORS + 1))
            fi
        fi
    else
        echo "→ BUSCO checks skipped (skip_busco = true)"
    fi

    echo ""

    # Check Prophage database
    echo "→ Checking Prophage database..."
    if [ -n "${prophage_db}" ] && [ -f "${prophage_db}" ]; then
        SIZE=\$(stat -f%z "${prophage_db}" 2>/dev/null || stat -c%s "${prophage_db}" 2>/dev/null || echo "0")
        if [ "\$SIZE" -gt 1000000 ]; then
            SIZE_MB=\$((\$SIZE / 1024 / 1024))
            echo "  ✓ Prophage database found (\${SIZE_MB} MB)"
        else
            echo "  ❌ Prophage database file is too small or empty!"
            echo "     File: ${prophage_db}"
            echo "     Size: \$SIZE bytes"
            ERRORS=\$((ERRORS + 1))
        fi
    else
        echo "  ❌ Prophage database NOT found!"
        echo "     Expected: ${prophage_db}"
        echo ""
        echo "     To fix, see: docs/DATABASE_SETUP.md"
        echo "     Or download from: https://datadryad.org/dataset/doi:10.5061/dryad.3n5tb2rs5"
        echo ""
        ERRORS=\$((ERRORS + 1))
    fi

    echo ""

    # Check AMRFinder database (just informational - auto-downloads)
    echo "→ Checking AMRFinder database..."
    if [ -n "${params.amrfinder_db}" ] && [ -d "${params.amrfinder_db}" ]; then
        echo "  ✓ AMRFinder database found"
    else
        echo "  ⚠️  AMRFinder database not found (will auto-download on first run)"
        echo "     This is normal - AMRFinder downloads its database automatically"
        WARNINGS=\$((WARNINGS + 1))
    fi

    echo ""
    echo "════════════════════════════════════════════════════════════════"

    # Summary
    if [ \$ERRORS -gt 0 ]; then
        echo "❌ Database validation FAILED (\$ERRORS error(s), \$WARNINGS warning(s))"
        echo ""
        echo "Please fix the errors above before running the pipeline."
        echo "See docs/DATABASE_SETUP.md for detailed setup instructions."
        echo "════════════════════════════════════════════════════════════════"
        exit 1
    elif [ \$WARNINGS -gt 0 ]; then
        echo "⚠️  Database validation PASSED with warnings (\$WARNINGS warning(s))"
        echo "════════════════════════════════════════════════════════════════"
    else
        echo "✅ All databases validated successfully!"
        echo "════════════════════════════════════════════════════════════════"
    fi

    echo ""
    """
}
