/*
 * PHASTER: PHAge Search Tool - Enhanced Report
 * More accurate prophage prediction than VIBRANT
 * https://phaster.ca/
 */

process PHASTER {
    tag "$sample_id"
    publishDir "${params.outdir}/phaster", mode: 'copy'

    // Note: PHASTER is web-based, but phispy can be used as alternative
    // Using phispy as the command-line alternative
    container = 'quay.io/biocontainers/phispy:4.2.21--pyhdfd78af_0'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_phaster"), emit: results
    tuple val(sample_id), path("${sample_id}_phaster/prophage_coordinates.tsv"), emit: coordinates, optional: true
    tuple val(sample_id), path("${sample_id}_phaster/prophage.fasta"), emit: sequences, optional: true
    path("${sample_id}_phaster/phispy.log"), emit: log

    script:
    """
    mkdir -p ${sample_id}_phaster

    # Run PhiSpy (command-line alternative to PHASTER)
    # PhiSpy is a prophage finder that uses similar algorithms
    PhiSpy.py \\
        ${assembly} \\
        --output_dir ${sample_id}_phaster \\
        --threads ${task.cpus} \\
        --phage_genes 1 \\
        --log ${sample_id}_phaster/phispy.log

    # PhiSpy outputs:
    # - prophage_coordinates.tsv (prophage regions)
    # - prophage.fasta (prophage sequences)
    # - bacteria.fasta (non-prophage regions)

    # If no prophages found, create empty files
    if [ ! -f "${sample_id}_phaster/prophage_coordinates.tsv" ]; then
        touch ${sample_id}_phaster/prophage_coordinates.tsv
        touch ${sample_id}_phaster/prophage.fasta
    fi
    """
}

/*
 * Alternative: PHASTER Web API
 * For more accurate results using the actual PHASTER server
 */
process PHASTER_WEB {
    tag "$sample_id"
    publishDir "${params.outdir}/phaster_web", mode: 'copy'

    // Uses custom Python script to submit to PHASTER web service
    container = 'python:3.11-slim'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_phaster_web"), emit: results
    path("${sample_id}_phaster_web/${sample_id}_summary.txt"), emit: summary

    script:
    """
    mkdir -p ${sample_id}_phaster_web

    # Install required packages
    pip install requests biopython --quiet

    # Submit to PHASTER web service
    # Note: This requires the phaster_submit.py helper script
    # For now, create a placeholder
    echo "PHASTER web submission requires manual upload or API script" > ${sample_id}_phaster_web/${sample_id}_summary.txt
    echo "Visit: https://phaster.ca/" >> ${sample_id}_phaster_web/${sample_id}_summary.txt
    echo "Upload assembly: ${assembly}" >> ${sample_id}_phaster_web/${sample_id}_summary.txt
    """
}
