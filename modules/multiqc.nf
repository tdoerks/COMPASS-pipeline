process MULTIQC {
    publishDir "${params.outdir}/multiqc", mode: 'copy'
    container = 'quay.io/biocontainers/multiqc:1.25.1--pyhdfd78af_0'

    input:
    path(qc_files)  // Accept files without staging to let MultiQC handle them

    output:
    path "multiqc_report.html", emit: report
    path "multiqc_data", emit: data
    path "versions.yml", emit: versions

    script:
    """
    # Create unique directory structure for each file type to avoid collisions
    mkdir -p qc_data

    # Copy files with index to ensure uniqueness
    i=0
    for file in ${qc_files}; do
        # Get file extension and basename
        ext="\${file##*.}"
        base="\${file%.*}"

        # Create subdirectory based on file type if possible
        if [[ \$file == *"quast"* ]]; then
            cp -r \$file qc_data/quast_\${i}_\$(basename \$file) || true
        elif [[ \$file == *"busco"* ]]; then
            cp -r \$file qc_data/busco_\${i}_\$(basename \$file) || true
        elif [[ \$file == *"fastqc"* ]]; then
            cp -r \$file qc_data/fastqc_\${i}_\$(basename \$file) || true
        elif [[ \$file == *"fastp"* ]]; then
            cp -r \$file qc_data/fastp_\${i}_\$(basename \$file) || true
        else
            cp -r \$file qc_data/file_\${i}_\$(basename \$file) || true
        fi
        i=\$((i+1))
    done

    multiqc qc_data \\
        --filename multiqc_report.html \\
        --force \\
        --config ${params.multiqc_config ?: ''} \\
        --title "COMPASS Pipeline Report" \\
        --comment "Comprehensive bacterial genomics analysis" || {
            echo "MultiQC completed with warnings or partial results"
        }

    echo '"MULTIQC": {"multiqc": "1.25.1"}' > versions.yml
    """
}
