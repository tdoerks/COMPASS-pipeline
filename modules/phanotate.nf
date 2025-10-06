process PHANOTATE {
    tag "$sample_id"
    publishDir "${params.outdir}/phanotate", mode: 'copy'

    input:
    tuple val(sample_id), path(fasta)

    output:
    tuple val(sample_id), path("${sample_id}_phanotate.gff"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    # Check if input file is empty or has no sequences
    if [ -s ${fasta} ] && grep -q ">" ${fasta}; then
        phanotate.py ${fasta} -o ${sample_id}_phanotate.gff -f gff3
    else
        echo "No phage sequences found - creating empty results file"
        touch ${sample_id}_phanotate.gff
    fi
    
    echo '"PHANOTATE": {"version": "1.6.7"}' > versions.yml
    """
}
