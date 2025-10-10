process DOWNLOAD_AMRFINDER_DB {
    tag "amrfinder_db"
    container 'quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0'

    output:
    path "amrfinder_db", emit: db
    path "versions.yml", emit: versions

    script:
    """
    # Use existing database
    ln -s ${params.amrfinder_db} amrfinder_db
    echo '"DOWNLOAD_AMRFINDER_DB": {"database": "local_copy"}' > versions.yml
    """
}

process AMRFINDER {
    tag "$meta.id"
    publishDir "${params.outdir}/amrfinder", mode: 'copy'
    container 'quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0'
    
    input:
    tuple val(meta), path(fasta)
    path(amrfinder_db)
    
    output:
    tuple val(meta), path("${meta.id}_amr.tsv"), emit: results
    tuple val(meta), path("${meta.id}_mutations.tsv"), emit: mutations, optional: true
    path "versions.yml", emit: versions
    
    script:
    def organism_flag = meta.organism ? "-O ${meta.organism}" : ""
    """
    amrfinder \\
        -n ${fasta} \\
        ${organism_flag} \\
        --plus \\
        --threads ${task.cpus} \\
        -d ${amrfinder_db} \\
        -o ${meta.id}_amr.tsv \\
        --mutation_all ${meta.id}_mutations.tsv
    
    echo '"AMRFINDER": {"version": "3.12.8"}' > versions.yml
    """
}
