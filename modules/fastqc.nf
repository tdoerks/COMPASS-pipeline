process FASTQC {
    tag "$sample_id"
    publishDir "${params.outdir}/fastqc", mode: 'copy'
    container = 'quay.io/biocontainers/fastqc:0.12.1--hdfd78af_0'

    input:
    tuple val(sample_id), path(reads)

    output:
    path "*.html", emit: html
    path "*.zip", emit: zip
    path "versions.yml", emit: versions

    script:
    """
    fastqc \\
        --threads ${task.cpus} \\
        --quiet \\
        ${reads}

    echo '"FASTQC": {"fastqc": "0.12.1"}' > versions.yml
    """
}
