/*
 * DEFENSEFINDER - Anti-phage defense system detection (R-M, Abi, CBASS, Gabija, CRISPR-Cas, ...)
 * DefenseFinder 3.x takes the nucleotide assembly and calls genes itself (pyrodigal), so this
 * does not depend on Prokka (skip_prokka = true by default).
 * Models are installed once (no internet on compute nodes): bin/setup_phage_therapy_dbs.sh
 * --skip-model-version-check: otherwise every task queries GitHub and writes to $HOME
 * (fails offline and under apptainer --no-home).
 */

process DEFENSEFINDER {
    tag "$sample_id"
    publishDir "${params.outdir}/defensefinder", mode: 'copy', pattern: "${sample_id}_defense_finder_*.tsv"
    container 'quay.io/biocontainers/defense-finder:3.0.0--pyhdfd78af_0'
    errorStrategy 'ignore'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_defense_finder_systems.tsv"), emit: systems
    tuple val(sample_id), path("${sample_id}_defense_finder_genes.tsv"), emit: genes, optional: true
    path "versions.yml", emit: versions

    script:
    """
    # DefenseFinder names outputs after the input file stem — stage as <sample_id>.fna
    cp -L ${assembly} ${sample_id}.fna

    defense-finder run \\
        --models-dir ${params.defensefinder_models} \\
        --index-dir . \\
        --skip-model-version-check \\
        --workers ${task.cpus} \\
        --out-dir df_out \\
        ${sample_id}.fna

    mv df_out/${sample_id}_defense_finder_systems.tsv .
    [ -f df_out/${sample_id}_defense_finder_genes.tsv ] && mv df_out/${sample_id}_defense_finder_genes.tsv . || true

    printf '"%s":\\n    defense-finder: "%s"\\n' "${task.process}" "\$(defense-finder version 2>&1 | grep -oE '[0-9]+\\.[0-9]+\\.[0-9]+' | head -1)" > versions.yml
    """
}
