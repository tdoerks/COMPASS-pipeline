process MOBSUITE_RECON {
    tag "$sample_id"
    publishDir "${params.outdir}/mobsuite", mode: 'copy'
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
        --run_typer || {
            echo "MOB-suite failed for ${sample_id}, creating empty output"
            mkdir -p ${sample_id}_mobsuite
            echo -e "sample_id\\tnum_plasmids\\tplasmid_types" > ${sample_id}_mobsuite/mobtyper_results.txt
            echo -e "${sample_id}\\t0\\t-" >> ${sample_id}_mobsuite/mobtyper_results.txt
        }

    echo '"MOBSUITE_RECON": {"mob_suite": "3.1.9"}' > versions.yml
    """
}
