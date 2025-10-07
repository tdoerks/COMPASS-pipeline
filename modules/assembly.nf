process ASSEMBLE_SPADES {
    tag "$sample_id"
    publishDir "${params.outdir}/assemblies", mode: 'copy'
    container = 'quay.io/biocontainers/spades:3.15.5--h95f258a_1'
    
    input:
    tuple val(sample_id), path(reads)
    
    output:
    tuple val(sample_id), path("${sample_id}_scaffolds.fasta"), emit: assembly
    path "versions.yml", emit: versions
    
    script:
    """
    # Determine if paired-end or single-end
    if [ \$(ls ${reads} | wc -l) -eq 2 ]; then
        # Paired-end
        R1=\$(ls ${reads} | grep "_1.fastq.gz")
        R2=\$(ls ${reads} | grep "_2.fastq.gz")
        
        spades.py \
            -1 \${R1} \
            -2 \${R2} \
            -o ${sample_id}_spades \
            --threads ${task.cpus} \
            --memory ${task.memory.toGiga()} \
            --careful \
            --only-assembler
    else
        # Single-end
        spades.py \
            -s ${reads} \
            -o ${sample_id}_spades \
            --threads ${task.cpus} \
            --memory ${task.memory.toGiga()} \
            --careful \
            --only-assembler
    fi
    
    # Copy scaffolds to output
    cp ${sample_id}_spades/scaffolds.fasta ${sample_id}_scaffolds.fasta
    
    echo '"ASSEMBLE_SPADES": {"spades": "3.15.5"}' > versions.yml
    """
}
