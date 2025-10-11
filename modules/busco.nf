process BUSCO {
    tag "$sample_id"
    publishDir "${params.outdir}/busco", mode: 'copy'
    container = 'quay.io/biocontainers/busco:5.7.1--pyhdfd78af_0'

    input:
    tuple val(sample_id), path(assembly)

    output:
    path "${sample_id}_busco", emit: results
    path "${sample_id}_busco/short_summary.*.txt", emit: summary
    path "versions.yml", emit: versions

    script:
    def lineage = params.busco_lineage ?: 'bacteria_odb10'
    def mode = params.busco_mode ?: 'genome'
    """
    # Run BUSCO
    busco \\
        -i ${assembly} \\
        -o ${sample_id}_busco \\
        -m ${mode} \\
        -l ${lineage} \\
        --cpu ${task.cpus} \\
        --offline \\
        --download_path ${params.busco_download_path ?: '/tmp/busco_downloads'} \\
        --force

    echo '"BUSCO": {"busco": "5.7.1"}' > versions.yml
    """
}

process DOWNLOAD_BUSCO_LINEAGE {
    publishDir "${params.outdir}/databases/busco", mode: 'copy'
    container = 'quay.io/biocontainers/busco:5.7.1--pyhdfd78af_0'

    output:
    path "busco_downloads", emit: lineage_path
    path "versions.yml", emit: versions

    script:
    def lineage = params.busco_lineage ?: 'bacteria_odb10'
    """
    # Create download directory
    mkdir -p busco_downloads

    # Download BUSCO lineage dataset
    busco \\
        --download ${lineage} \\
        --download_path busco_downloads

    echo '"DOWNLOAD_BUSCO_LINEAGE": {"busco": "5.7.1"}' > versions.yml
    """
}
