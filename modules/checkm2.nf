process CHECKM2 {
    tag "$sample_id"
    publishDir "${params.outdir}/checkm2", mode: 'copy', pattern: "${sample_id}_checkm2/quality_report.tsv"
    container = 'quay.io/biocontainers/checkm2:1.0.2--pyh7cba7a3_0'
    errorStrategy = 'ignore'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_checkm2/quality_report.tsv"), emit: report, optional: true
    path "versions.yml", emit: versions

    script:
    def db_flag = params.checkm2_db ? "--database_path ${params.checkm2_db}" : "--database_path /tmp/checkm2_db/uniref100.KO.1.dmnd"
    """
    mkdir -p tmpdir
    checkm2 predict \\
        --threads ${task.cpus} \\
        --input ${assembly} \\
        --output-directory ${sample_id}_checkm2 \\
        ${db_flag} \\
        --tmpdir ./tmpdir \\
        --force

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        checkm2: \$(checkm2 --version 2>&1 | grep -oP '\\d+\\.\\d+\\.\\d+' | head -1)
    END_VERSIONS
    """
}
