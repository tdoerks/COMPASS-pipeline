process MULTIQC {
    publishDir "${params.outdir}/multiqc", mode: 'copy'
    container = 'quay.io/biocontainers/multiqc:1.25.1--pyhdfd78af_0'

    input:
    path(qc_files)  // Accept files without staging to let MultiQC handle them

    output:
    path "multiqc_report.html", emit: report
    path "multiqc_report_data", emit: data
    path "versions.yml", emit: versions

    script:
    def config_opt = params.multiqc_config ? "--config ${params.multiqc_config}" : ""
    """
    # MultiQC scans all input files and directories
    # QUAST directories are passed directly to avoid filename collisions
    multiqc . \\
        --filename multiqc_report.html \\
        --force \\
        ${config_opt} \\
        --title "COMPASS Pipeline Report" \\
        --comment "Comprehensive bacterial genomics analysis" || {
            echo "MultiQC completed with warnings or partial results"
        }

    echo '"MULTIQC": {"multiqc": "1.25.1"}' > versions.yml
    """
}
