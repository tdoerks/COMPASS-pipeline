process GENOMAD_PROPHAGE {
    tag "$sample_id"
    publishDir "${params.outdir}/genomad_prophage/${sample_id}", mode: 'copy'
    container = 'staphb/genomad:1.12.0'
    errorStrategy = 'ignore'

    input:
    tuple val(sample_id), path(phage_fasta)

    output:
    tuple val(sample_id), path("${sample_id}_genomad/"), emit: results, optional: true
    tuple val(sample_id), path("${sample_id}_genomad/${sample_id}_summary/${sample_id}_virus_summary.tsv"), emit: virus_summary, optional: true
    path "versions.yml", emit: versions

    script:
    def db = params.genomad_db ?: '/genomad_db'
    """
    # Skip if no prophages detected (empty FASTA from VIBRANT)
    # Use printf instead of heredoc to avoid Nextflow stripIndent/<<- tab-vs-space issue
    if [ ! -s "${phage_fasta}" ]; then
        echo "No prophage sequences found for ${sample_id} — skipping geNomad" >&2
        printf '"${task.process}":\\n    genomad: skipped_no_input\\n' > versions.yml
        exit 0
    fi

    # geNomad uses input filename stem as prefix — rename to sample_id
    [ "${phage_fasta}" != "${sample_id}.fasta" ] && cp ${phage_fasta} ${sample_id}.fasta || true

    genomad end-to-end \\
        ${sample_id}.fasta \\
        ${sample_id}_genomad \\
        ${db} \\
        --threads ${task.cpus} \\
        --splits 8 \\
        --enable-score-calibration

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        genomad: \$(genomad --version 2>&1 | head -1)
    END_VERSIONS
    """
}
