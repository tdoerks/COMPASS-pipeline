process DOWNLOAD_ASSEMBLY {
    tag "$sample"
    label 'process_low'

    // Use curlimages/curl - has curl pre-installed and works in read-only mode
    container = 'curlimages/curl:8.5.0'

    publishDir "${params.outdir}/assemblies", mode: 'copy'

    input:
    tuple val(sample), val(organism), val(assembly_accession)

    output:
    tuple val(sample), val(organism), path("${sample}.fasta"), emit: assembly
    path "versions.yml", emit: versions

    script:
    """
    #!/bin/sh
    # Download assembly using NCBI FTP (most reliable method)
    echo "Downloading ${assembly_accession}..." >&2

    # Construct FTP path from accession
    ACC_PREFIX=\$(echo ${assembly_accession} | sed 's/\\.[0-9]*\$//')
    FTP_PATH="https://ftp.ncbi.nlm.nih.gov/genomes/all/\${ACC_PREFIX:0:3}/\${ACC_PREFIX:4:3}/\${ACC_PREFIX:7:3}/\${ACC_PREFIX:10:3}/${assembly_accession}/${assembly_accession}_genomic.fna.gz"

    echo "Fetching from: \$FTP_PATH" >&2

    # Download with retries
    for i in 1 2 3; do
        curl -L -s "\$FTP_PATH" -o ${sample}.fasta.gz && break
        echo "Download attempt \$i failed, retrying..." >&2
        sleep 5
    done

    # Decompress
    gunzip ${sample}.fasta.gz 2>/dev/null || true

    # Check if download succeeded
    if [ ! -s ${sample}.fasta ]; then
        echo "ERROR: Failed to download ${assembly_accession}" >&2
        echo "Tried FTP path: \$FTP_PATH" >&2
        exit 1
    fi

    echo "Successfully downloaded ${assembly_accession}" >&2

    # Create versions file
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        curl: \$(curl --version 2>&1 | head -n1 | cut -d' ' -f2)
    END_VERSIONS
    """

    stub:
    """
    touch ${sample}.fasta
    echo '"${task.process}": {"curl": "7.81.0"}' > versions.yml
    """
}
