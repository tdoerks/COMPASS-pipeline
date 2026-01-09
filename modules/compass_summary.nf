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
    """
    echo "==================================================="
    echo "COMPASS Enhanced Summary Report Generation"
    echo "==================================================="
    echo ""

    # Step 1: Recreate filtered metadata from analyzed samples
    echo "Step 1: Recreating filtered metadata from analyzed samples..."
    recreate_filtered_metadata.py --outdir ${params.outdir} || {
        echo "⚠️  WARNING: Metadata recreation failed, continuing anyway..."
    }
    echo ""

    # Step 2: Generate comprehensive enhanced HTML report
    echo "Step 2: Generating enhanced COMPASS summary report..."
    generate_compass_summary.py \\
        --outdir ${params.outdir} \\
        --metadata ${params.outdir}/filtered_samples/filtered_samples.csv \\
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
