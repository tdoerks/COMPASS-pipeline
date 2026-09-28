/*
 * ECTYPER - E. coli / Shigella in silico serotyping (O:H) + pathotype and stx subtyping
 * The O-antigen is a major phage receptor, so O:H type matters for phage therapy matching.
 * ECTyper aborts unless its ~900 MB species MASH sketch (+ .txt metadata) exists; prepared once
 * by bin/setup_phage_therapy_dbs.sh and passed with -r (the container's own path is read-only).
 */

process ECTYPER {
    tag "$sample_id"
    publishDir "${params.outdir}/ectyper", mode: 'copy', pattern: "${sample_id}_ectyper.tsv"
    container 'quay.io/biocontainers/ectyper:2.0.0--pyhdfd78af_4'
    errorStrategy 'ignore'

    input:
    tuple val(sample_id), path(assembly), val(organism)

    output:
    tuple val(sample_id), path("${sample_id}_ectyper.tsv"), emit: results
    path "versions.yml", emit: versions

    when:
    organism =~ /(?i)escherichia|shigella|e\.\s*coli/

    script:
    """
    ectyper \\
        -i ${assembly} \\
        -o ectyper_out \\
        -r ${params.ectyper_mash} \\
        --pathotype \\
        --cores ${task.cpus}

    # output.tsv holds one row per input; tag it with the sample id
    awk -v s="${sample_id}" 'BEGIN{FS=OFS="\\t"} NR==1{print; next} {\$1=s; print}' ectyper_out/output.tsv > ${sample_id}_ectyper.tsv

    printf '"%s":\\n    ectyper: "%s"\\n' "${task.process}" "\$(ectyper --version 2>&1 | grep -oE '[0-9]+\\.[0-9]+\\.[0-9]+' | head -1)" > versions.yml
    """
}
