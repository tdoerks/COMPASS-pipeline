process DOWNLOAD_ASSEMBLY {
    tag "$sample"
    label 'process_low'

    // Use NCBI Entrez Direct for reliable assembly downloads
    container = 'quay.io/biocontainers/entrez-direct:16.2--he881be0_1'

    publishDir "${params.outdir}/assemblies", mode: 'copy'

    input:
    tuple val(sample), val(organism), val(assembly_accession)

    output:
    tuple val(sample), val(organism), path("${sample}.fasta"), emit: assembly
    path "versions.yml", emit: versions

    script:
    """
    # Download assembly using NCBI Entrez Direct
    echo "Downloading ${assembly_accession} using NCBI Entrez Direct..." >&2

    # Query NCBI Assembly database and fetch FASTA
    esearch -db assembly -query "${assembly_accession}[Assembly Accession]" | \\
        efetch -format fasta > ${sample}.fasta

    # Check if download succeeded
    if [ ! -s ${sample}.fasta ]; then
        echo "ERROR: Failed to download ${assembly_accession}" >&2
        echo "Assembly may not exist or NCBI service unavailable" >&2
        exit 1
    fi

    echo "Successfully downloaded ${assembly_accession}" >&2

    # Create versions file
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        entrez-direct: \$(esearch -version 2>&1 | head -n1 | sed 's/^[^0-9]*//')
    END_VERSIONS
    """

    stub:
    """
    touch ${sample}.fasta
    echo '"${task.process}": {"curl": "7.81.0"}' > versions.yml
    """
}
