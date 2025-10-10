process DOWNLOAD_PROPHAGE_DB {
    tag "prophage_db"
    publishDir "${params.outdir}/databases", mode: 'copy'
    container = 'docker://staphb/diamond'

    output:
    path "prophage_db.dmnd", emit: db
    path "versions.yml", emit: versions

    script:
    if (params.prophage_db && file(params.prophage_db).exists()) {
        // Use existing local database
        """
        cp ${params.prophage_db} prophage_db.dmnd
        echo '"DOWNLOAD_PROPHAGE_DB": {"database": "local_copy", "source": "${params.prophage_db}"}' > versions.yml
        """
    } else {
        // Download and build database from Dryad
        """
        echo "Downloading Prophage-DB protein sequences from Dryad..."

        # Try direct download from Dryad
        wget -O prophage_proteins.faa.gz "https://datadryad.org/stash/downloads/file_stream/2907143" || \\
        curl -L -o prophage_proteins.faa.gz "https://datadryad.org/stash/downloads/file_stream/2907143" || \\
        {
            echo "ERROR: Automatic download failed due to Dryad access restrictions."
            echo "Please manually download the database from:"
            echo "https://datadryad.org/stash/dataset/doi:10.5061/dryad.3n5tb2rs5"
            echo ""
            echo "Download 'prophage_proteins.faa.gz' and either:"
            echo "1. Set params.prophage_db to point to a pre-built .dmnd file, or"
            echo "2. Place prophage_proteins.faa.gz in the work directory"
            exit 1
        }

        echo "Extracting protein sequences..."
        gunzip prophage_proteins.faa.gz

        echo "Building DIAMOND database (this may take several minutes)..."
        diamond makedb --in prophage_proteins.faa --db prophage_db --threads ${task.cpus}

        # Clean up intermediate files
        rm -f prophage_proteins.faa

        echo '"DOWNLOAD_PROPHAGE_DB": {"database": "Prophage-DB", "version": "2024-07-18", "source": "https://doi.org/10.5061/dryad.3n5tb2rs5"}' > versions.yml
        """
    }
}

process DIAMOND_PROPHAGE {
    tag "$sample_id"
    publishDir "${params.outdir}/diamond_prophage", mode: 'copy'
    container = 'docker://staphb/diamond'

    input:
    tuple val(sample_id), path(phage_sequences)
    path(prophage_db)

    output:
    tuple val(sample_id), path("${sample_id}_diamond_results.tsv"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    # Check if input file is empty
    if [ -s ${phage_sequences} ]; then
        diamond blastx \
            --query ${phage_sequences} \
            --db ${prophage_db} \
            --out ${sample_id}_diamond_results.tsv \
            --outfmt 6 \
            --evalue 1e-5 \
            --max-target-seqs 10 \
            --threads ${task.cpus}
    else
        echo "No phage sequences found - creating empty results file"
        touch ${sample_id}_diamond_results.tsv
    fi

    echo '"DIAMOND_PROPHAGE": {"diamond": "staphb"}' > versions.yml
    """
}
