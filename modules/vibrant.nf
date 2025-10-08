process VIBRANT {
    tag "$sample_id"
    publishDir "${params.outdir}/vibrant", mode: 'copy'
    
    container = 'docker://staphb/vibrant'
    
    input:
    tuple val(sample_id), path(assembly)
    
    output:
    tuple val(sample_id), path("${sample_id}_vibrant"), emit: results
    tuple val(sample_id), path("${sample_id}_phages.fna"), emit: phages
    path "versions.yml", emit: versions
    
    script:
    """
    # Create output directory
    mkdir -p ${sample_id}_vibrant
    
    # Run VIBRANT using the container
    VIBRANT_run.py -i ${assembly} -t ${task.cpus} -folder ${sample_id}_vibrant
    
    # Extract phages - copy the combined phages file to expected output location
    if [ -f "${sample_id}_vibrant/VIBRANT_${assembly.baseName}/VIBRANT_phages_${assembly.baseName}/${assembly.baseName}.phages_combined.fna" ]; then
        cp ${sample_id}_vibrant/VIBRANT_${assembly.baseName}/VIBRANT_phages_${assembly.baseName}/${assembly.baseName}.phages_combined.fna ${sample_id}_phages.fna
    else
        # Create empty file if no phages found
        touch ${sample_id}_phages.fna
    fi
    
    # Create versions file
    echo '"VIBRANT": {"version": "container"}' > versions.yml
    """
}
