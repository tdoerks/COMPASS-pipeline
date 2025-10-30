process COMBINE_RESULTS {
    publishDir "${params.outdir}/summary", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    output:
    path "combined_analysis_summary.tsv", emit: summary
    path "compass_report.html", emit: report
    path "versions.yml", emit: versions

    script:
    """
    # Generate TSV summary
    generate_compass_summary.py --outdir ${params.outdir} --output combined_analysis_summary.tsv

    # Generate comprehensive HTML report
    generate_report_v3.py ${params.outdir} -o compass_report.html

    echo '"COMBINE_RESULTS": {"version": "1.0.0"}' > versions.yml
    """
}
