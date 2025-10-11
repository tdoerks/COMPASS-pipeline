process MULTIQC {
    publishDir "${params.outdir}/multiqc", mode: 'copy'
    container = 'quay.io/biocontainers/multiqc:1.25.1--pyhdfd78af_0'

    input:
    path('*')  // Collect all QC outputs

    output:
    path "multiqc_report.html", emit: report
    path "multiqc_data", emit: data
    path "versions.yml", emit: versions

    script:
    """
    multiqc . \\
        --filename multiqc_report.html \\
        --force \\
        --config ${params.multiqc_config ?: ''} \\
        --title "COMPASS Pipeline Report" \\
        --comment "Comprehensive bacterial genomics analysis" || {
            echo "MultiQC completed with warnings or partial results"
        }

    echo '"MULTIQC": {"multiqc": "1.25.1"}' > versions.yml
    """
}
