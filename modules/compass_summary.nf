process COMPASS_SUMMARY {
    publishDir "${params.outdir}", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    input:
    path(outdir)

    output:
    path "compass_summary.tsv", emit: summary
    path "versions.yml", emit: versions

    script:
    """
    # Generate comprehensive COMPASS summary
    generate_compass_summary.py \\
        --outdir ${params.outdir} \\
        --output compass_summary.tsv || {
            echo "Summary generation failed, creating minimal output"
            echo -e "sample_id\\tstatus" > compass_summary.tsv
            echo -e "unknown\\tfailed" >> compass_summary.tsv
        }

    echo '"COMPASS_SUMMARY": {"version": "1.0"}' > versions.yml
    """
}
