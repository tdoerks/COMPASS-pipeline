process MOBSUITE_RECON {
    tag "$sample_id"
    publishDir "${params.outdir}/mobsuite", mode: 'copy', pattern: "${sample_id}_mobsuite"
    container = 'quay.io/biocontainers/mob_suite:3.1.9--pyhdfd78af_0'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_mobsuite"), emit: results
    tuple val(sample_id), path("${sample_id}_mobsuite/plasmid_*.fasta"), optional: true, emit: plasmids
    path "${sample_id}_mobsuite/mobtyper_results.txt", optional: true, emit: mobtyper
    path "versions.yml", emit: versions

    script:
    """
    # Run MOB-recon for plasmid reconstruction
    mob_recon \\
        --infile ${assembly} \\
        --outdir ${sample_id}_mobsuite \\
        --num_threads ${task.cpus} \\
        --force

    # Run MOB-typer on reconstructed plasmids if any were found
    if ls ${sample_id}_mobsuite/plasmid_*.fasta 1> /dev/null 2>&1; then
        # Plasmids found, run mob_typer on each
        for plasmid in ${sample_id}_mobsuite/plasmid_*.fasta; do
            mob_typer --infile \$plasmid --out_file \${plasmid%.fasta}_typing.txt --num_threads ${task.cpus} || true
        done

        # Create summary mobtyper_results.txt
        num_plasmids=\$(ls ${sample_id}_mobsuite/plasmid_*.fasta 2>/dev/null | wc -l)
        echo -e "sample_id\\tnum_plasmids\\tplasmid_types" > ${sample_id}_mobsuite/mobtyper_results.txt
        echo -e "${sample_id}\\t\${num_plasmids}\\tSee individual typing files" >> ${sample_id}_mobsuite/mobtyper_results.txt
    else
        # No plasmids found
        echo -e "sample_id\\tnum_plasmids\\tplasmid_types" > ${sample_id}_mobsuite/mobtyper_results.txt
        echo -e "${sample_id}\\t0\\t-" >> ${sample_id}_mobsuite/mobtyper_results.txt
    fi

    echo '"MOBSUITE_RECON": {"mob_suite": "3.1.9"}' > versions.yml
    """
}
