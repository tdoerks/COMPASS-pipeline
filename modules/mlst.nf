process MLST {
    tag "$sample_id"
    publishDir "${params.outdir}/mlst", mode: 'copy', pattern: "${sample_id}_mlst.tsv"
    container = 'quay.io/biocontainers/mlst:2.23.0--hdfd78af_1'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_mlst.tsv"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    echo "==================================================="
    echo "MLST Strain Typing"
    echo "Sample: ${sample_id}"
    echo "==================================================="

    # Show available MLST schemes for debugging
    echo ""
    echo "Available MLST schemes in database:"
    mlst --list 2>/dev/null | grep -iE "(campylobacter|listeria|salmonella|escherichia|ecoli)" | head -10 || mlst --list 2>/dev/null | head -20 || echo "Could not list schemes"
    echo ""

    # Run MLST with automatic scheme detection
    echo "Running MLST analysis (automatic scheme detection)..."
    mlst \\
        --threads ${task.cpus} \\
        ${assembly} > ${sample_id}_mlst.tsv

    MLST_EXIT=\$?

    # Check if MLST found a matching scheme
    if [ \$MLST_EXIT -eq 0 ]; then
        # Check if result has a valid scheme (not just "-")
        SCHEME=\$(tail -n 1 ${sample_id}_mlst.tsv | cut -f2)
        if [ "\$SCHEME" = "-" ] || [ -z "\$SCHEME" ]; then
            echo "⚠️  WARNING: Automatic scheme detection found no match"

            # Try common foodborne pathogen schemes explicitly
            echo "Attempting explicit scheme matching for common foodborne pathogens..."
            FOUND_MATCH=0

            for EXPLICIT_SCHEME in campylobacter cjejuni_pubmlst campylobacter_jejuni_coli lmonocytogenes ecoli senterica; do
                if mlst --list 2>/dev/null | grep -q "\$EXPLICIT_SCHEME"; then
                    echo "  Trying scheme: \$EXPLICIT_SCHEME"
                    mlst --scheme \$EXPLICIT_SCHEME --threads ${task.cpus} ${assembly} > ${sample_id}_mlst_attempt.tsv 2>/dev/null
                    TEST_SCHEME=\$(tail -n 1 ${sample_id}_mlst_attempt.tsv | cut -f2)
                    if [ "\$TEST_SCHEME" != "-" ] && [ -n "\$TEST_SCHEME" ]; then
                        echo "  ✅ Success with scheme: \$EXPLICIT_SCHEME"
                        mv ${sample_id}_mlst_attempt.tsv ${sample_id}_mlst.tsv
                        FOUND_MATCH=1
                        break
                    fi
                fi
            done

            if [ \$FOUND_MATCH -eq 0 ]; then
                echo ""
                echo "❌ No MLST scheme found for this assembly"
                echo "Possible reasons:"
                echo "  - Organism-specific MLST scheme not in database"
                echo "  - Assembly quality too low for reliable typing"
                echo "  - Organism is not a well-characterized species with MLST"
                echo ""
                echo "Note: The MLST container may have an outdated database"
                echo "      Consider updating MLST database to latest PubMLST data"
            fi
        else
            echo "✅ MLST typing successful - Scheme: \$SCHEME"
        fi
    else
        echo "❌ MLST analysis failed, creating stub output"
        echo -e "FILE\\tSCHEME\\tST" > ${sample_id}_mlst.tsv
        echo -e "${assembly}\\t-\\t-" >> ${sample_id}_mlst.tsv
    fi

    echo "==================================================="

    echo '"MLST": {"mlst": "2.23.0"}' > versions.yml
    """
}
