process QUAST {
    tag "$sample_id"
    publishDir "${params.outdir}/quast", mode: 'copy'
    container = 'quay.io/biocontainers/quast:5.2.0--py39pl5321h2add14b_1'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_quast"), emit: results
    path "${sample_id}_quast/report.tsv", emit: report
    path "versions.yml", emit: versions

    script:
    """
    # Run QUAST for assembly statistics
    quast.py \\
        ${assembly} \\
        --output-dir ${sample_id}_quast \\
        --threads ${task.cpus} \\
        --min-contig ${params.quast_min_contig ?: 500} \\
        --labels ${sample_id} || {
            echo "QUAST failed for ${sample_id}, creating empty output"
            mkdir -p ${sample_id}_quast
            echo -e "Assembly\\t${sample_id}" > ${sample_id}_quast/report.tsv
            echo -e "# contigs\\t0" >> ${sample_id}_quast/report.tsv
        }

    echo '"QUAST": {"quast": "5.2.0"}' > versions.yml
    """
}
