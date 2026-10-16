/*
 * CRISPR-Cas Array Detection
 *
 * Uses CRISPRCasFinder or MinCED to identify CRISPR arrays
 * Filters out CRISPR regions for later analysis (as requested by supervisor)
 */

process MINCED {
    tag "$sample_id"
    publishDir "${params.outdir}/crispr/minced", mode: 'copy'
    // biocontainer is Java + busybox only (no python) -> summary is built with awk from minced's GFF
    container 'quay.io/biocontainers/minced:0.4.2--hdfd78af_1'
    errorStrategy 'ignore'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_crispr"), emit: results
    tuple val(sample_id), path("${sample_id}_crispr/${sample_id}_crisprs.txt"), emit: crisprs, optional: true
    tuple val(sample_id), path("${sample_id}_crispr/${sample_id}_crispr_summary.csv"), emit: summary, optional: true
    // -spacers writes the spacer SEQUENCES: the input for matching spacers against phage genomes
    // (DefenseFinder/CRISPRCasFinder type the Cas systems but never give you the spacers)
    tuple val(sample_id), path("${sample_id}_crispr/*_spacers.fa"), emit: spacers, optional: true

    script:
    def out = "${sample_id}_crispr/${sample_id}_crisprs"
    """
    mkdir -p ${sample_id}_crispr

    # txt (human-readable) + gff (contig, start, end, repeat count per array) + spacer FASTA
    minced -spacers -minNR 3 -minRL 23 -maxRL 47 -minSL 26 -maxSL 50 \
        ${assembly} ${out}.txt ${out}.gff

    touch ${out}.txt ${out}.gff
    # GFF col 6 = number of repeats; spacers = repeats - 1. Contig kept for prophage/plasmid intersection.
    awk -F'\t' 'BEGIN { OFS=","; print "crispr_id,contig,start,end,repeats,spacers" }
                 \$3 == "repeat_region" { id=\$9; sub(/^ID=/, "", id); sub(/;.*/, "", id)
                                         print id, \$1, \$4, \$5, \$6, \$6 - 1 }' \
        ${out}.gff > ${sample_id}_crispr/${sample_id}_crispr_summary.csv
    echo "\$(( \$(wc -l < ${sample_id}_crispr/${sample_id}_crispr_summary.csv) - 1 )) CRISPR arrays"
    """
}

/*
 * CRISPRCasFinder - More comprehensive but slower
 * Detects CRISPR arrays AND Cas genes
 */
process CRISPRCASFINDER {
    tag "$sample_id"
    publishDir "${params.outdir}/crispr/crisprcasfinder", mode: 'copy'

    // Note: CRISPRCasFinder requires large database downloads
    container = 'unlhcc/crisprcasfinder:4.2.20'

    cpus = { check_max( 8, 'cpus' ) }
    memory = { check_max( 16.GB * task.attempt, 'memory' ) }
    time = { check_max( 6.h * task.attempt, 'time' ) }

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_ccf"), emit: results
    tuple val(sample_id), path("${sample_id}_ccf/result.json"), emit: json, optional: true

    script:
    """
    # CRISPRCasFinder.pl is more comprehensive but slower
    # Detects both CRISPR arrays and Cas genes

    mkdir -p ${sample_id}_ccf

    CRISPRCasFinder.pl \\
        -in ${assembly} \\
        -out ${sample_id}_ccf \\
        -cpuM ${task.cpus} \\
        -keep

    # If no results, create empty JSON
    if [ ! -f "${sample_id}_ccf/result.json" ]; then
        echo '{"crisprs": [], "cas_genes": []}' > ${sample_id}_ccf/result.json
    fi
    """
}

/*
 * Filter out CRISPR regions from assembly
 * Creates a CRISPR-masked assembly for downstream analysis
 */
process MASK_CRISPR_REGIONS {
    tag "$sample_id"
    publishDir "${params.outdir}/crispr/masked", mode: 'copy'

    container = 'biocontainers/biopython:v1.78_cv1'

    input:
    tuple val(sample_id), path(assembly), path(crispr_summary)

    output:
    tuple val(sample_id), path("${sample_id}_masked.fasta"), emit: masked_assembly
    tuple val(sample_id), path("${sample_id}_crispr_regions.bed"), emit: crispr_bed

    script:
    """
    #!/usr/bin/env python3
    from Bio import SeqIO
    import csv

    # Load CRISPR coordinates
    crispr_regions = []
    try:
        with open('${crispr_summary}', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['start'] and row['end']:
                    crispr_regions.append({
                        'start': int(row['start']),
                        'end': int(row['end'])
                    })
    except:
        pass  # No CRISPRs

    # Write BED file
    with open('${sample_id}_crispr_regions.bed', 'w') as bed:
        for i, region in enumerate(crispr_regions, 1):
            bed.write(f"crispr_{i}\\t{region['start']}\\t{region['end']}\\n")

    # Mask CRISPR regions (replace with Ns)
    masked_records = []
    for record in SeqIO.parse('${assembly}', 'fasta'):
        seq = list(str(record.seq))

        # Mask each CRISPR region
        for region in crispr_regions:
            start = region['start']
            end = region['end']
            # Replace with Ns
            for i in range(start, min(end, len(seq))):
                seq[i] = 'N'

        record.seq = ''.join(seq)
        masked_records.append(record)

    # Write masked assembly
    SeqIO.write(masked_records, '${sample_id}_masked.fasta', 'fasta')

    print(f"Masked {len(crispr_regions)} CRISPR regions")
    """
}
