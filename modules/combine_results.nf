process COMBINE_RESULTS {
    publishDir "${params.outdir}/summary", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    output:
    path "combined_analysis_summary.tsv", emit: summary
    path "compass_report.html", emit: report
    path "versions.yml", emit: versions

    script:
    def metadata_arg = params.prophage_metadata ? "--prophage-metadata ${params.prophage_metadata}" : ""
    """
    # Generate TSV summary
    generate_compass_summary.py --outdir ${params.outdir} --output combined_analysis_summary.tsv

    # Generate comprehensive HTML report with optional metadata enrichment
    generate_report_v3.py ${params.outdir} -o compass_report.html ${metadata_arg}

    echo '"COMBINE_RESULTS": {"version": "1.1.0"}' > versions.yml
    """
}
