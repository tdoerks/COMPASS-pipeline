/*
 * PADLOC - anti-phage defence system detection (second caller alongside DefenseFinder)
 *
 * Why both: DefenseFinder and PADLOC use different model sets and disagree at the edges, so
 * a system called by BOTH is a confident call and one called by only one is worth a second look.
 *
 * Gene calling: when Prokka ran, PADLOC is given its .faa + .gff so DefenseFinder/PADLOC/Prokka
 * all describe the SAME genes; otherwise PADLOC falls back to --fna and calls genes itself
 * (prodigal), in which case its protein IDs will not match DefenseFinder's.
 *
 * Database: installed once (compute nodes have no internet) by bin/setup_phage_therapy_dbs.sh.
 * padloc 2.0.0 ignores --data and always reads/creates <install>/data (/usr/local/data, read-only
 * in the container), so the database is bind-mounted over that path instead of passed as a flag.
 */

process PADLOC {
    tag "$sample_id"
    publishDir "${params.outdir}/padloc", mode: 'copy', pattern: "${sample_id}_padloc*"
    container 'quay.io/biocontainers/padloc:2.0.0--hdfd78af_1'
    errorStrategy 'ignore'
    containerOptions { params.padloc_db
        ? (workflow.containerEngine == 'docker' ? "-v ${params.padloc_db}:/usr/local/data"
                                                : "--bind ${params.padloc_db}:/usr/local/data")
        : '' }

    input:
    tuple val(sample_id), path(assembly), path(faa), path(gff)

    output:
    tuple val(sample_id), path("${sample_id}_padloc.csv"), emit: csv, optional: true
    tuple val(sample_id), path("${sample_id}_padloc.gff"), emit: gff, optional: true
    path "versions.yml", emit: versions

    script:
    // Prokka output when present (same gene calls as the rest of the run), else nucleotide input
    def input_args = (faa && gff) ? "--faa ${faa} --gff ${gff}" : "--fna ${assembly}"
    """
    padloc ${input_args} --outdir padloc_out --cpu ${task.cpus}

    # padloc names outputs after the input file stem — normalise to the sample id
    for ext in csv gff; do
        f=\$(ls padloc_out/*_padloc.\${ext} 2>/dev/null | head -1)
        [ -n "\$f" ] && cp "\$f" ${sample_id}_padloc.\${ext} || true
    done

    printf '"%s":\\n    padloc: "%s"\\n' "${task.process}" "\$(padloc --version 2>&1 | grep -oE '[0-9]+\\.[0-9]+\\.[0-9]+' | head -1)" > versions.yml
    """
}
