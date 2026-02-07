process DOWNLOAD_ASSEMBLY {
    tag "$sample"
    label 'process_low'

    // Use NCBI's official entrez-direct container
    container = 'ncbi/edirect:latest'

    publishDir "${params.outdir}/assemblies", mode: 'copy'

    input:
    tuple val(sample), val(organism), val(assembly_accession)

    output:
    tuple val(sample), val(organism), path("${sample}.fasta"), emit: assembly
    path "versions.yml", emit: versions

    script:
    """
    # Download assembly using NCBI Entrez Direct
    echo "Downloading ${assembly_accession}..." >&2

    # Use esearch + efetch to download assembly
    esearch -db assembly -query "${assembly_accession}[Assembly Accession]" | \\
        efetch -format fasta > ${sample}.fasta

    # Check if download succeeded
    if [ ! -s ${sample}.fasta ]; then
        echo "ERROR: Failed to download ${assembly_accession}" >&2
        exit 1
    fi

    echo "Successfully downloaded ${assembly_accession} (\$(wc -l < ${sample}.fasta) lines)" >&2

    # Create versions file
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        entrez-direct: \$(esearch -version 2>&1 | head -n1 | awk '{print \$NF}')
    END_VERSIONS
    """

    stub:
    """
    touch ${sample}.fasta
    echo '"${task.process}": {"curl": "7.81.0"}' > versions.yml
    """
}
