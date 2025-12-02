process ASSEMBLE_SPADES {
    tag "$sample_id"
    publishDir "${params.outdir}/assemblies", mode: 'copy', pattern: "${sample_id}_contigs.fasta"
    publishDir "${params.outdir}/assemblies/failed", mode: 'copy', pattern: "*.failed.log"
    container = 'quay.io/biocontainers/spades:3.15.5--h95f258a_1'
    errorStrategy { task.attempt <= 1 ? params.assembly_error_strategy : 'ignore' }
    maxRetries 1

    input:
    tuple val(sample_id), path(reads)

    output:
    tuple val(sample_id), path("${sample_id}_contigs.fasta"), emit: assembly
    path "versions.yml", emit: versions, optional: true
    path "${sample_id}.failed.log", emit: failed, optional: true

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
            --isolate \
            --only-assembler
    else
        # Single-end
        spades.py \
            -s ${reads} \
            -o ${sample_id}_spades \
            --threads ${task.cpus} \
            --memory ${task.memory.toGiga()} \
            --isolate \
            --only-assembler
    fi

    # Check if assembly succeeded - use contigs only (isolate mode best practice)
    if [ -f ${sample_id}_spades/contigs.fasta ] && [ -s ${sample_id}_spades/contigs.fasta ]; then
        # Contigs generated successfully
        echo "✅ Assembly succeeded for ${sample_id} - using contigs.fasta"
        cp ${sample_id}_spades/contigs.fasta ${sample_id}_contigs.fasta
        echo '"ASSEMBLE_SPADES": {"spades": "3.15.5"}' > versions.yml
    else
        # Assembly completely failed - log it and exit with error
        echo "❌ Assembly failed for ${sample_id}" | tee ${sample_id}.failed.log
        echo "SPAdes did not produce contigs.fasta" | tee -a ${sample_id}.failed.log
        echo "Check ${sample_id}_spades/spades.log and warnings.log for details" | tee -a ${sample_id}.failed.log

        # Copy SPAdes log to failed log
        if [ -f ${sample_id}_spades/spades.log ]; then
            echo "" >> ${sample_id}.failed.log
            echo "=== SPAdes Log (last 50 lines) ===" >> ${sample_id}.failed.log
            tail -50 ${sample_id}_spades/spades.log >> ${sample_id}.failed.log
        fi

        if [ -f ${sample_id}_spades/warnings.log ]; then
            echo "" >> ${sample_id}.failed.log
            echo "=== SPAdes Warnings ===" >> ${sample_id}.failed.log
            cat ${sample_id}_spades/warnings.log >> ${sample_id}.failed.log
        fi

        # Exit with error - errorStrategy 'ignore' will skip this sample
        exit 1
    fi
    """
}
