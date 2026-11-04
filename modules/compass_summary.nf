/*
 * COMPASS_SUMMARY - Generate comprehensive summary report
 * Combines all analysis results into TSV and HTML reports
 */

process COMPASS_SUMMARY {
    publishDir "${params.outdir}/summary", mode: 'copy', pattern: "compass_summary.*"
    label 'process_low'
    container 'quay.io/biocontainers/pandas:1.5.2'

    input:
    path(metadata, stageAs: 'metadata.csv')  // Optional metadata file
    val(ready)                               // Signal that all analyses are complete

    output:
    path "compass_summary.tsv", emit: tsv
    path "compass_summary.html", emit: html
    path "versions.yml", emit: versions

    script:
    def outdir_abs = file(params.outdir).toAbsolutePath()
    """
    echo "==================================================="
    echo "COMPASS Enhanced Summary Report Generation"
    echo "==================================================="
    echo ""

    # Step 1: Recreate filtered metadata from analyzed samples
    # This only succeeds for SRA-download modes that populate \${outdir}/metadata.
    # For FASTA/assembly input there is no metadata/ directory, so this is expected
    # to fail and we fall back to the staged samplesheet below.
    echo "Step 1: Recreating filtered metadata from analyzed samples..."
    recreate_filtered_metadata.py --outdir ${outdir_abs} || {
        echo "⚠️  WARNING: Metadata recreation failed (expected for FASTA/assembly input)"
    }
    echo ""

    # Step 2: Pick a metadata source for the summary report.
    # Preference order:
    #   1. Recreated filtered_samples.csv  (rich SRA runinfo; metadata/sra_list modes)
    #   2. Staged metadata file            (input samplesheet for FASTA/assembly modes,
    #                                        which carries 'sample' and 'organism')
    echo "Step 2: Selecting metadata source..."
    META_ARG=""
    if [ -f "${outdir_abs}/filtered_samples/filtered_samples.csv" ]; then
        echo "  → Using recreated filtered_samples.csv"
        META_ARG="--metadata ${outdir_abs}/filtered_samples/filtered_samples.csv"
    elif [ -s metadata.csv ]; then
        echo "  → Using staged samplesheet/metadata file (metadata.csv)"
        META_ARG="--metadata metadata.csv"
    else
        echo "  → No metadata source available; Metadata Explorer fields will be omitted"
    fi
    echo ""

    # Step 3: Generate comprehensive enhanced HTML report
    echo "Step 3: Generating enhanced COMPASS summary report..."
    generate_compass_summary.py \\
        --outdir ${outdir_abs} \\
        \$META_ARG \\
        --output_tsv compass_summary.tsv \\
        --output_html compass_summary.html || {
            echo "❌ Summary generation failed, creating minimal outputs"
            echo -e "sample_id\\tstatus" > compass_summary.tsv
            echo -e "unknown\\tfailed" >> compass_summary.tsv
            echo "<html><body><h1>Summary generation failed</h1></body></html>" > compass_summary.html
        }
    echo ""
    echo "✅ COMPASS summary report complete!"
    echo ""

    cat <<-END_VERSIONS > versions.yml
    "COMPASS_SUMMARY":
        pandas: \$(python -c "import pandas; print(pandas.__version__)")
        compass_summary: "1.2.0"
    END_VERSIONS
    """

    stub:
    """
    echo -e "sample_id\\torganism\\tnum_contigs\\tn50\\tmdr_status" > compass_summary.tsv
    echo -e "test_sample\\tEscherichia\\t50\\t100000\\tNo" >> compass_summary.tsv
    echo "<html><body><h1>COMPASS Summary (stub)</h1></body></html>" > compass_summary.html

    cat <<-END_VERSIONS > versions.yml
    "COMPASS_SUMMARY":
        pandas: "1.5.2"
        compass_summary: "1.2.0"
    END_VERSIONS
    """
}
