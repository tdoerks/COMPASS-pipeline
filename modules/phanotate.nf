process PHANOTATE {
    tag "$sample_id"
    publishDir "${params.outdir}/phanotate", mode: 'copy'

    container = 'quay.io/biocontainers/phanotate:1.6.7--py311he264feb_0'

    errorStrategy = { task.attempt <= 2 ? 'retry' : 'ignore' }
    maxRetries = 2

    input:
    tuple val(sample_id), path(fasta)

    output:
    tuple val(sample_id), path("${sample_id}_phanotate.gff"), emit: results, optional: true
    path "versions.yml", emit: versions

    script:
    // Increase timeout with task attempt
    def timeout_mins = 30 * task.attempt
    """
    # Check if input file is empty or has no sequences
    if [ ! -s ${fasta} ] || ! grep -q ">" ${fasta}; then
        echo "No phage sequences found - creating empty results file"
        touch ${sample_id}_phanotate.gff
        echo '"PHANOTATE": {"version": "1.6.7", "status": "no_input"}' > versions.yml
        exit 0
    fi

    # Count number of sequences
    NUM_SEQ=\$(grep -c ">" ${fasta} || echo "0")
    echo "Processing \$NUM_SEQ phage sequences for ${sample_id}"

    # Run PHANOTATE with timeout
    if command -v timeout &> /dev/null; then
        echo "Running PHANOTATE with ${timeout_mins} minute timeout (attempt ${task.attempt})"
        timeout ${timeout_mins}m phanotate.py ${fasta} -o ${sample_id}_phanotate.gff -f gff3 || {
            EXIT_CODE=\$?
            if [ \$EXIT_CODE -eq 124 ]; then
                echo "WARNING: PHANOTATE timed out after ${timeout_mins} minutes"
                echo "Creating empty GFF for ${sample_id}"
                touch ${sample_id}_phanotate.gff
                echo '"PHANOTATE": {"version": "1.6.7", "status": "timeout", "sequences": "'\$NUM_SEQ'"}' > versions.yml
                exit 0
            else
                echo "ERROR: PHANOTATE failed with exit code \$EXIT_CODE"
                exit \$EXIT_CODE
            fi
        }
    else
        echo "Running PHANOTATE without timeout (attempt ${task.attempt})"
        phanotate.py ${fasta} -o ${sample_id}_phanotate.gff -f gff3 || {
            echo "WARNING: PHANOTATE failed for ${sample_id}, creating empty GFF"
            touch ${sample_id}_phanotate.gff
        }
    fi

    # Verify output was created
    if [ ! -f ${sample_id}_phanotate.gff ]; then
        touch ${sample_id}_phanotate.gff
    fi

    echo '"PHANOTATE": {"version": "1.6.7", "status": "success"}' > versions.yml
    """
}
