/*
 * PHAGE_THERAPY_VIEWER - Build interactive phage therapy candidate viewer
 * Takes COMPASS summary TSV and generates a self-contained HTML report
 */

process PHAGE_THERAPY_VIEWER {
    publishDir "${params.outdir}/summary", mode: 'copy'
    label 'process_low'
    container 'quay.io/biocontainers/pandas:1.5.2'

    input:
    path(compass_tsv)

    output:
    path "phage_therapy_viewer.html", emit: html
    path "versions.yml",              emit: versions

    script:
    """
    build_phage_therapy_viewer.py \\
        --compass ${compass_tsv} \\
        --out phage_therapy_viewer.html

    cat <<-END_VERSIONS > versions.yml
    "PHAGE_THERAPY_VIEWER":
        python: \$(python3 --version | sed 's/Python //')
        build_phage_therapy_viewer: "1.0.0"
    END_VERSIONS
    """

    stub:
    """
    echo "<html><body><h1>Phage Therapy Viewer (stub)</h1></body></html>" > phage_therapy_viewer.html

    cat <<-END_VERSIONS > versions.yml
    "PHAGE_THERAPY_VIEWER":
        python: "3.10"
        build_phage_therapy_viewer: "1.0.0"
    END_VERSIONS
    """
}
