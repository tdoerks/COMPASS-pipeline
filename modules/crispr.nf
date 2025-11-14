/*
 * CRISPR-Cas Array Detection
 *
 * Uses CRISPRCasFinder or MinCED to identify CRISPR arrays
 * Filters out CRISPR regions for later analysis (as requested by supervisor)
 */

process MINCED {
    tag "$sample_id"
    publishDir "${params.outdir}/crispr/minced", mode: 'copy'

    // MinCED is faster and more lightweight than CRISPRCasFinder
    container = 'staphb/minced:0.4.2'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path("${sample_id}_crispr"), emit: results
    tuple val(sample_id), path("${sample_id}_crispr/${sample_id}_crisprs.txt"), emit: crisprs, optional: true
    tuple val(sample_id), path("${sample_id}_crispr/${sample_id}_crispr_summary.csv"), emit: summary, optional: true

    script:
    """
    mkdir -p ${sample_id}_crispr

    # Run MinCED to detect CRISPR arrays
    minced \\
        -minNR 3 \\
        -minRL 23 \\
        -maxRL 47 \\
        -minSL 26 \\
        -maxSL 50 \\
        ${assembly} \\
        ${sample_id}_crispr/${sample_id}_crisprs.txt

    # Parse MinCED output to CSV for easier downstream analysis
    python3 <<'PYTHON_EOF'
import csv
import re

# Parse MinCED output
crisprs = []
current_crispr = None

try:
    with open('${sample_id}_crispr/${sample_id}_crisprs.txt', 'r') as f:
        for line in f:
            line = line.strip()

            # Detect new CRISPR array
            if line.startswith('CRISPR'):
                if current_crispr:
                    crisprs.append(current_crispr)

                # Parse: "CRISPR 1   Range: 145000 - 147000"
                match = re.search(r'CRISPR\\s+(\\d+)\\s+Range:\\s+(\\d+)\\s+-\\s+(\\d+)', line)
                if match:
                    current_crispr = {
                        'crispr_id': match.group(1),
                        'start': match.group(2),
                        'end': match.group(3),
                        'repeats': 0,
                        'spacers': 0
                    }

            # Count repeats
            elif line.startswith('Repeats:'):
                match = re.search(r'Repeats:\\s+(\\d+)', line)
                if match and current_crispr:
                    current_crispr['repeats'] = match.group(1)

            # Count spacers
            elif line.startswith('Spacers:'):
                match = re.search(r'Spacers:\\s+(\\d+)', line)
                if match and current_crispr:
                    current_crispr['spacers'] = match.group(1)

        # Add last CRISPR
        if current_crispr:
            crisprs.append(current_crispr)

    # Write CSV
    if crisprs:
        with open('${sample_id}_crispr/${sample_id}_crispr_summary.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['crispr_id', 'start', 'end', 'repeats', 'spacers'])
            writer.writeheader()
            writer.writerows(crisprs)
        print(f"Found {len(crisprs)} CRISPR arrays")
    else:
        # No CRISPRs found - create empty files
        open('${sample_id}_crispr/${sample_id}_crispr_summary.csv', 'w').close()
        print("No CRISPR arrays detected")

except FileNotFoundError:
    # MinCED didn't create output file (no CRISPRs)
    open('${sample_id}_crispr/${sample_id}_crisprs.txt', 'w').close()
    open('${sample_id}_crispr/${sample_id}_crispr_summary.csv', 'w').close()
    print("No CRISPR arrays detected")

PYTHON_EOF
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
