process BUSCO {
    tag "$sample_id"
    publishDir "${params.outdir}/busco", mode: 'copy', pattern: "${sample_id}_busco"
    container = 'quay.io/biocontainers/busco:5.7.1--pyhdfd78af_0'
    errorStrategy = 'ignore'  // Continue pipeline even if BUSCO fails

    input:
    tuple val(sample_id), path(assembly)

    output:
    path "${sample_id}_busco", emit: results, optional: true
    path "${sample_id}_busco/short_summary.*.txt", emit: summary, optional: true
    path "versions.yml", emit: versions

    script:
    def mode = params.busco_mode ?: 'genome'
    def download_path = params.busco_download_path ?: '/tmp/busco_downloads'
    def auto_lineage = params.busco_auto_lineage ?: false
    def lineage = params.busco_lineage ?: 'bacteria_odb10'

    if (auto_lineage) {
        """
        # Create download directory for lineage datasets
        mkdir -p ${download_path}

        # Run BUSCO with auto-lineage mode for prokaryotes
        echo "Running BUSCO in auto-lineage mode for prokaryotes..."
        busco \\
            -i ${assembly} \\
            -o ${sample_id}_busco \\
            -m ${mode} \\
            --auto-lineage-prok \\
            --cpu ${task.cpus} \\
            --download_path ${download_path} \\
            --force

        echo '"BUSCO": {"busco": "5.7.1", "mode": "auto-lineage-prok"}' > versions.yml
        """
    } else {
        """
        # Auto-download lineage dataset if not present
        if [ ! -d "${download_path}/lineages/${lineage}" ]; then
            echo "BUSCO lineage ${lineage} not found. Downloading..."
            mkdir -p ${download_path}
            busco --download ${lineage} --download_path ${download_path}
        else
            echo "BUSCO lineage ${lineage} found at ${download_path}/lineages/${lineage}"
        fi

        # Run BUSCO with specified lineage
        busco \\
            -i ${assembly} \\
            -o ${sample_id}_busco \\
            -m ${mode} \\
            -l ${lineage} \\
            --cpu ${task.cpus} \\
            --offline \\
            --download_path ${download_path} \\
            --force

        echo '"BUSCO": {"busco": "5.7.1", "lineage": "${lineage}"}' > versions.yml
        """
    }
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
