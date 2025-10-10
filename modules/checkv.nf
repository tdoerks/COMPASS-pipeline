process CHECKV {
    tag "$sample_id"
    publishDir "${params.outdir}/checkv", mode: 'copy'
    container = 'quay.io/biocontainers/checkv:1.0.2--pyhdfd78af_0'
    
    input:
    tuple val(sample_id), path(phage_sequences)
    path(checkv_db)
    
    output:
    tuple val(sample_id), path("${sample_id}_checkv"), emit: results
    path "versions.yml", emit: versions
    
    script:
    """
    # Check if input file is empty or has no sequences
    if [ -s ${phage_sequences} ] && grep -q ">" ${phage_sequences}; then
        # Use the default CheckV database location in the container
        checkv end_to_end ${phage_sequences} ${sample_id}_checkv -t ${task.cpus} -d ${checkv_db}
    else
        echo "No phage sequences found - creating empty results directory"
        mkdir -p ${sample_id}_checkv
        touch ${sample_id}_checkv/quality_summary.tsv
    fi
    
    echo '"CHECKV": {"version": "1.0.2"}' > versions.yml
    """
}

process DOWNLOAD_CHECKV_DB {
    tag "$sample_id"
    publishDir "${params.outdir}/checkv_db", mode: 'copy'
    container = 'quay.io/biocontainers/checkv:1.0.2--pyhdfd78af_0'
    
    output:
    path "checkv_db", emit: db
    path "versions.yml", emit: versions
    
    script:
    """
    # Use existing database
    ln -s ${params.checkv_db} checkv_db
    echo '"DOWNLOAD_CHECKV_DB": {"database": "local_copy"}' > versions.yml
    """
}
