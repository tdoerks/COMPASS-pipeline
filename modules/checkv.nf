process CHECKV {
    tag "$sample_id"
    publishDir "${params.outdir}/checkv", mode: 'copy'

    container = 'quay.io/biocontainers/checkv:1.0.2--pyhdfd78af_0'

    input:
    tuple val(sample_id), path(phage_sequences)
    path checkv_db

    output:
    tuple val(sample_id), path("${sample_id}_checkv"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    # Check if input file is empty or has no sequences
    if [ -s ${phage_sequences} ] && grep -q ">" ${phage_sequences}; then
        # Use the provided CheckV database path
        checkv end_to_end ${phage_sequences} ${sample_id}_checkv -d ${checkv_db} -t ${task.cpus}
    else
        echo "No phage sequences found - creating empty results directory"
        mkdir -p ${sample_id}_checkv
        touch ${sample_id}_checkv/quality_summary.tsv
    fi

    echo '"CHECKV": {"version": "1.0.2"}' > versions.yml
    """
}
