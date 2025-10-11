process MLST {
    tag "$sample_id"
    publishDir "${params.outdir}/mlst", mode: 'copy'
    container = 'quay.io/biocontainers/mlst:2.23.0--hdfd78af_1'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_mlst.tsv"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    # Run MLST with automatic scheme detection
    mlst \\
        --threads ${task.cpus} \\
        ${assembly} > ${sample_id}_mlst.tsv || {
            echo "MLST failed for ${sample_id}, creating empty output"
            echo -e "FILE\\tSCHEME\\tST\\tALLELES" > ${sample_id}_mlst.tsv
            echo -e "${assembly}\\t-\\t-\\t-" >> ${sample_id}_mlst.tsv
        }

    echo '"MLST": {"mlst": "2.23.0"}' > versions.yml
    """
}
