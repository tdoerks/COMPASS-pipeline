process DOWNLOAD_PROPHAGE_DB {
    tag "prophage_db"
    publishDir "${params.outdir}/databases", mode: 'copy'
    container = 'staphb/diamond'

    output:
    path "prophage_db.dmnd", emit: db
    path "versions.yml", emit: versions

    script:
    """
    cp /homes/tylerdoe/databases/prophage_db.dmnd .
    echo '"DOWNLOAD_PROPHAGE_DB": {"database": "local_copy"}' > versions.yml
    """
}

process DIAMOND_PROPHAGE {
    tag "$sample_id"
    publishDir "${params.outdir}/diamond_prophage", mode: 'copy'
    container = 'staphb/diamond'

    input:
    tuple val(sample_id), path(phage_sequences)
    path(prophage_db)

    output:
    tuple val(sample_id), path("${sample_id}_diamond_results.tsv"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    # Check if input file is empty
    if [ -s ${phage_sequences} ]; then
        diamond blastx \
            --query ${phage_sequences} \
            --db ${prophage_db} \
            --out ${sample_id}_diamond_results.tsv \
            --outfmt 6 \
            --evalue 1e-5 \
            --max-target-seqs 10 \
            --threads ${task.cpus}
    else
        echo "No phage sequences found - creating empty results file"
        touch ${sample_id}_diamond_results.tsv
    fi

    echo '"DIAMOND_PROPHAGE": {"diamond": "staphb"}' > versions.yml
    """
}
