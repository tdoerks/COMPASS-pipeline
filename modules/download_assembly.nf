process DOWNLOAD_ASSEMBLY {
    tag "$sample"
    label 'process_low'

    container = 'quay.io/biocontainers/entrez-direct:16.2--he881be0_1'

    publishDir "${params.outdir}/assemblies", mode: 'copy'

    input:
    tuple val(sample), val(organism), val(assembly_accession)

    output:
    tuple val(sample), val(organism), path("${sample}.fasta"), emit: assembly
    path "versions.yml", emit: versions

    script:
    """
    # Download assembly using efetch
    esearch -db assembly -query "${assembly_accession}[Assembly Accession]" | \\
        efetch -format fasta > ${sample}.fasta

    # Check if download succeeded
    if [ ! -s ${sample}.fasta ]; then
        echo "ERROR: Failed to download ${assembly_accession}" >&2
        exit 1
    fi

    # Create versions file
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        entrez-direct: \$(esearch -version | grep "version" | sed 's/.*version //')
    END_VERSIONS
    """

    stub:
    """
    touch ${sample}.fasta
    echo '"${task.process}": {"entrez-direct": "16.2"}' > versions.yml
    """
}
