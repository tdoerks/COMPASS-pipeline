process FASTP {
    tag "$sample_id"
    publishDir "${params.outdir}/fastp", mode: 'copy', pattern: "*.{json,html}"
    publishDir "${params.outdir}/trimmed_fastq", mode: 'copy', pattern: "*_trimmed*.fastq.gz"
    container = 'quay.io/biocontainers/fastp:0.23.4--hadf994f_3'

    input:
    tuple val(sample_id), path(reads)

    output:
    tuple val(sample_id), path("*_trimmed*.fastq.gz"), emit: reads
    path "${sample_id}_fastp.json", emit: json
    path "${sample_id}_fastp.html", emit: html
    path "versions.yml", emit: versions

    script:
    def is_paired = reads instanceof List && reads.size() == 2

    if (is_paired) {
        """
        fastp \\
            -i ${reads[0]} \\
            -I ${reads[1]} \\
            -o ${sample_id}_trimmed_1.fastq.gz \\
            -O ${sample_id}_trimmed_2.fastq.gz \\
            --thread ${task.cpus} \\
            --json ${sample_id}_fastp.json \\
            --html ${sample_id}_fastp.html \\
            --detect_adapter_for_pe \\
            --cut_front \\
            --cut_tail \\
            --cut_mean_quality 20 \\
            --length_required 50 \\
            --qualified_quality_phred 20

        echo '"FASTP": {"fastp": "0.23.4"}' > versions.yml
        """
    } else {
        """
        fastp \\
            -i ${reads} \\
            -o ${sample_id}_trimmed.fastq.gz \\
            --thread ${task.cpus} \\
            --json ${sample_id}_fastp.json \\
            --html ${sample_id}_fastp.html \\
            --cut_front \\
            --cut_tail \\
            --cut_mean_quality 20 \\
            --length_required 50 \\
            --qualified_quality_phred 20

        echo '"FASTP": {"fastp": "0.23.4"}' > versions.yml
        """
    }
}
