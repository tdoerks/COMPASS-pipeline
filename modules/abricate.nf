process ABRICATE {
    tag "$sample_id-$db"
    publishDir "${params.outdir}/abricate", mode: 'copy'
    container = 'quay.io/biocontainers/abricate:1.0.1--ha8f3691_1'

    input:
    tuple val(sample_id), path(assembly)
    each db

    output:
    tuple val(sample_id), val(db), path("${sample_id}_${db}.tsv"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    # Run ABRicate against specified database
    abricate \\
        --db ${db} \\
        --minid ${params.abricate_minid ?: 75} \\
        --mincov ${params.abricate_mincov ?: 50} \\
        ${assembly} > ${sample_id}_${db}.tsv || {
            echo "ABRicate failed for ${sample_id} on ${db}, creating empty output"
            echo -e "#FILE\\tSEQUENCE\\tSTART\\tEND\\tSTRAND\\tGENE\\tCOVERAGE\\tCOVERAGE_MAP\\tGAPS\\t%COVERAGE\\t%IDENTITY\\tDATABASE\\tACCESSION\\tPRODUCT\\tRESISTANCE" > ${sample_id}_${db}.tsv
        }

    echo '"ABRICATE": {"abricate": "1.0.1"}' > versions.yml
    """
}

process ABRICATE_SUMMARY {
    publishDir "${params.outdir}/abricate", mode: 'copy'
    container = 'quay.io/biocontainers/abricate:1.0.1--ha8f3691_1'

    input:
    path(results)

    output:
    path "abricate_summary.tsv", emit: summary
    path "versions.yml", emit: versions

    script:
    """
    # Create summary across all samples and databases
    abricate --summary ${results} > abricate_summary.tsv || {
        echo "ABRicate summary failed, creating empty output"
        echo -e "FILE\\tNUM_FOUND" > abricate_summary.tsv
    }

    echo '"ABRICATE_SUMMARY": {"abricate": "1.0.1"}' > versions.yml
    """
}
