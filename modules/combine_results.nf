process COMBINE_RESULTS {
    publishDir "${params.outdir}/summary", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    output:
    path "combined_analysis_summary.tsv", emit: summary
    path "versions.yml", emit: versions

    script:
    """
    generate_compass_summary.py --outdir ${params.outdir} --output combined_analysis_summary.tsv

    echo '"COMBINE_RESULTS": {"version": "1.0.0"}' > versions.yml
    """
}
