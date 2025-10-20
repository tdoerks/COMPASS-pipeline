process DOWNLOAD_AMRFINDER_DB {
    tag "amrfinder_db"
    container = 'quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0'

    output:
    path "amrfinder_db", emit: db
    path "versions.yml", emit: versions

    script:
    if (params.amrfinder_db && params.amrfinder_db != "") {
        """
        # Use existing database
        ln -s ${params.amrfinder_db} amrfinder_db
        echo '"DOWNLOAD_AMRFINDER_DB": {"database": "local_copy"}' > versions.yml
        """
    } else {
        """
        # Download and prepare latest database
        amrfinder_update --force_update --database amrfinder_db

        # Verify database was created (check for any version subdirectory)
        if [ ! -d "amrfinder_db" ] || [ -z "\$(find amrfinder_db -name 'AMRProt' 2>/dev/null)" ]; then
            echo "ERROR: AMRFinder database download failed" >&2
            ls -la amrfinder_db/ || true
            exit 1
        fi

        echo '"DOWNLOAD_AMRFINDER_DB": {"version": "latest", "source": "NCBI"}' > versions.yml
        """
    }
}

process AMRFINDER {
    tag "$meta.id"
    publishDir "${params.outdir}/amrfinder", mode: 'copy'
    container = 'quay.io/biocontainers/ncbi-amrfinderplus:3.12.8--h283d18e_0'
    
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
    # Find the actual database directory (handles versioned subdirectories)
    DB_PATH=\$(find ${amrfinder_db} -name "AMRProt" -type f | head -1 | xargs dirname)
    if [ -z "\$DB_PATH" ]; then
        DB_PATH="${amrfinder_db}"
    fi

    amrfinder \\
        -n ${fasta} \\
        ${organism_flag} \\
        --plus \\
        --threads ${task.cpus} \\
        -d \$DB_PATH \\
        -o ${meta.id}_amr.tsv \\
        --mutation_all ${meta.id}_mutations.tsv

    echo '"AMRFINDER": {"version": "3.12.8"}' > versions.yml
    """
}
