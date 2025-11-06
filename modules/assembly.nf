process ASSEMBLE_SPADES {
    tag "$sample_id"
    publishDir "${params.outdir}/assemblies", mode: 'copy', pattern: "${sample_id}_scaffolds.fasta"
    publishDir "${params.outdir}/assemblies/failed", mode: 'copy', pattern: "*.failed.log"
    container = 'quay.io/biocontainers/spades:3.15.5--h95f258a_1'
    errorStrategy 'ignore'  // Continue pipeline even if this sample fails

    input:
    tuple val(sample_id), path(reads)

    output:
    tuple val(sample_id), path("${sample_id}_scaffolds.fasta"), emit: assembly
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

    # Check if assembly succeeded - use scaffolds if available, contigs as fallback
    if [ -f ${sample_id}_spades/scaffolds.fasta ] && [ -s ${sample_id}_spades/scaffolds.fasta ]; then
        # Scaffolds generated successfully
        echo "✅ Assembly succeeded for ${sample_id} - using scaffolds.fasta"
        cp ${sample_id}_spades/scaffolds.fasta ${sample_id}_scaffolds.fasta
        echo '"ASSEMBLE_SPADES": {"spades": "3.15.5"}' > versions.yml
    elif [ -f ${sample_id}_spades/contigs.fasta ] && [ -s ${sample_id}_spades/contigs.fasta ]; then
        # Only contigs generated (common when insert size cannot be estimated)
        echo "⚠️  Scaffolds not generated for ${sample_id}, using contigs.fasta instead"
        cp ${sample_id}_spades/contigs.fasta ${sample_id}_scaffolds.fasta
        echo '"ASSEMBLE_SPADES": {"spades": "3.15.5"}' > versions.yml
    else
        # Assembly completely failed - log it and exit with error
        echo "❌ Assembly failed for ${sample_id}" | tee ${sample_id}.failed.log
        echo "SPAdes did not produce scaffolds.fasta or contigs.fasta" | tee -a ${sample_id}.failed.log
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
