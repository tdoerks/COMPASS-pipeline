process DOWNLOAD_SRA {
    tag "$srr_id"
    publishDir "${params.outdir}/fastq", mode: 'copy'
    container = 'quay.io/biocontainers/sra-tools:3.0.3--h87f3376_0'
    
    input:
    val srr_id
    
    output:
    tuple val(srr_id), path("${srr_id}_*.fastq.gz"), emit: reads
    path "versions.yml", emit: versions
    
    script:
    """
    # Download and convert to FASTQ with fasterq-dump
    fasterq-dump ${srr_id} \
        --threads ${task.cpus} \
        --split-files \
        --skip-technical \
        --progress
    
    # Compress the FASTQ files
    gzip ${srr_id}*.fastq
    
    echo '"DOWNLOAD_SRA": {"sra-tools": "3.0.3"}' > versions.yml
    """
}
