/*
 * viralFlye: De novo assembly of viral/phage genomes from metagenomic data
 * Part of the Flye assembler
 * Assembles complete, circular viral genomes from raw reads
 */

process VIRALFLYE {
    tag "$sample_id"
    publishDir "${params.outdir}/viralflye", mode: 'copy'

    container = 'staphb/flye:2.9.3'

    cpus = { check_max( 16, 'cpus' ) }
    memory = { check_max( 32.GB * task.attempt, 'memory' ) }
    time = { check_max( 8.h * task.attempt, 'time' ) }

    input:
    tuple val(sample_id), path(reads)

    output:
    tuple val(sample_id), path("${sample_id}_viralflye"), emit: results
    tuple val(sample_id), path("${sample_id}_viralflye/assembly.fasta"), emit: assembly, optional: true
    tuple val(sample_id), path("${sample_id}_viralflye/assembly_graph.gfa"), emit: graph, optional: true
    path("${sample_id}_viralflye/flye.log"), emit: log

    script:
    def input_reads = reads instanceof List ? reads.join(' ') : reads
    def read_type = reads.toString().contains('.fastq') ? 'nano-raw' : 'nano-raw'

    // Detect if paired-end Illumina or single-end
    def is_paired = reads instanceof List && reads.size() == 2

    """
    # viralFlye mode for viral genome assembly
    # Uses --meta mode optimized for viral sequences

    if [ "${is_paired}" = "true" ]; then
        # Paired-end Illumina reads - concatenate for metagenomic mode
        cat ${input_reads} > combined_reads.fastq

        flye \\
            --meta \\
            --threads ${task.cpus} \\
            --out-dir ${sample_id}_viralflye \\
            --reads combined_reads.fastq
    else
        # Single-end or already combined
        flye \\
            --meta \\
            --threads ${task.cpus} \\
            --out-dir ${sample_id}_viralflye \\
            --reads ${reads}
    fi

    # If assembly failed, create empty files
    if [ ! -f "${sample_id}_viralflye/assembly.fasta" ]; then
        mkdir -p ${sample_id}_viralflye
        touch ${sample_id}_viralflye/assembly.fasta
        touch ${sample_id}_viralflye/assembly_graph.gfa
        echo "Assembly failed or no contigs assembled" > ${sample_id}_viralflye/flye.log
    fi
    """
}

/*
 * viralVerify: Classify contigs as viral or bacterial
 * Identifies which assembled contigs are actually viral
 */
process VIRALVERIFY {
    tag "$sample_id"
    publishDir "${params.outdir}/viralverify", mode: 'copy'

    container = 'quay.io/biocontainers/viralverify:1.1--pyhdfd78af_0'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_viralverify"), emit: results
    tuple val(sample_id), path("${sample_id}_viralverify/*_result_table.csv"), emit: table
    tuple val(sample_id), path("${sample_id}_viralverify/Prediction_results_fasta"), emit: sequences, optional: true

    script:
    """
    mkdir -p ${sample_id}_viralverify

    # Run viralVerify to classify contigs
    viralverify \\
        -f ${assembly} \\
        --hmm /viralverify/nbc_hmms.hmm \\
        -o ${sample_id}_viralverify \\
        -t ${task.cpus}

    # viralVerify creates subdirectories with classifications:
    # - Prediction_results_fasta/ (viral, plasmid, chromosome predictions)
    # - *_result_table.csv (classification results)
    """
}

/*
 * Extract viral contigs from assembly
 * Uses viralVerify results to extract only viral sequences
 */
process EXTRACT_VIRAL_CONTIGS {
    tag "$sample_id"
    publishDir "${params.outdir}/viral_contigs", mode: 'copy'

    container = 'biocontainers/biopython:v1.78_cv1'

    input:
    tuple val(sample_id), path(assembly), path(viralverify_results)

    output:
    tuple val(sample_id), path("${sample_id}_viral_contigs.fasta"), emit: viral_contigs
    tuple val(sample_id), path("${sample_id}_viral_stats.txt"), emit: stats

    script:
    """
    #!/usr/bin/env python3
    from Bio import SeqIO
    import csv
    import os

    # Parse viralVerify results
    viral_contigs = set()
    result_file = None

    # Find the result table CSV
    for root, dirs, files in os.walk('${viralverify_results}'):
        for f in files:
            if f.endswith('_result_table.csv'):
                result_file = os.path.join(root, f)
                break

    if result_file and os.path.exists(result_file):
        with open(result_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Look for 'Virus' or 'Plasmid' predictions
                prediction = row.get('Prediction', '')
                if 'Virus' in prediction or 'Circular' in prediction:
                    contig_name = row.get('Contig name', '')
                    if contig_name:
                        viral_contigs.add(contig_name)

    # Extract viral contigs from assembly
    viral_count = 0
    total_length = 0

    with open('${sample_id}_viral_contigs.fasta', 'w') as out_f:
        for record in SeqIO.parse('${assembly}', 'fasta'):
            if record.id in viral_contigs:
                SeqIO.write(record, out_f, 'fasta')
                viral_count += 1
                total_length += len(record.seq)

    # Write statistics
    with open('${sample_id}_viral_stats.txt', 'w') as stats_f:
        stats_f.write(f"Sample: ${sample_id}\\n")
        stats_f.write(f"Viral contigs identified: {viral_count}\\n")
        stats_f.write(f"Total viral sequence length: {total_length} bp\\n")
        stats_f.write(f"Average contig length: {total_length/viral_count if viral_count > 0 else 0:.0f} bp\\n")

    # If no viral contigs found, create empty file
    if viral_count == 0:
        open('${sample_id}_viral_contigs.fasta', 'w').close()
    """
}
