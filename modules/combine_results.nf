process COMBINE_RESULTS {
    publishDir "${params.outdir}/summary", mode: 'copy'
    container = 'python:3.9'

    output:
    path "combined_analysis_summary.tsv", emit: summary
    path "compass_report.html", emit: report
    path "versions.yml", emit: versions

    script:
    def metadata_arg = params.prophage_metadata ? "--prophage-metadata ${params.prophage_metadata}" : ""
    """
    # Install required Python packages
    pip install pandas openpyxl > /dev/null 2>&1

    # Generate TSV summary
    generate_compass_summary.py --outdir ${params.outdir} --output combined_analysis_summary.tsv

    # Generate comprehensive HTML report with optional metadata enrichment
    generate_report_v3.py ${params.outdir} -o compass_report.html ${metadata_arg}

    echo '"COMBINE_RESULTS": {"version": "1.1.0"}' > versions.yml
    """
}
