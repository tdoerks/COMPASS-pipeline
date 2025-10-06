process VIBRANT {
    tag "$sample_id"
    publishDir "${params.outdir}/vibrant", mode: 'copy'
    container = 'docker://staphb/vibrant'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_vibrant"), emit: results
    tuple val(sample_id), path("${sample_id}_vibrant/VIBRANT_${sample_id}/VIBRANT_phages_${sample_id}/${sample_id}.phages_combined.fna"), emit: phages, optional: true
    path "versions.yml", emit: versions

    script:
    """
    # Create output directory
    mkdir -p ${sample_id}_vibrant

    # Run VIBRANT using the container (not manual path)
    VIBRANT_run.py -i ${assembly} -t ${task.cpus} -folder ${sample_id}_vibrant

    # Create versions file
    echo '"VIBRANT": {"version": "container"}' > versions.yml
    """
}
