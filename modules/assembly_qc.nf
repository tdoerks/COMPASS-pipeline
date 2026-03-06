process ASSEMBLY_QC {
    tag "$sample_id"
    publishDir "${params.outdir}/assembly_qc", mode: 'copy'
    container = 'quay.io/biocontainers/python:3.9'

    input:
    tuple val(sample_id), path(assembly)

    output:
    tuple val(sample_id), path(assembly), path("${sample_id}_assembly_qc.json"), emit: qc_pass
    path "${sample_id}_assembly_qc.json", emit: qc_metrics
    path "${sample_id}.qc_failed.txt", optional: true, emit: qc_failed

    script:
    """
    #!/usr/bin/env python3
    import json
    from pathlib import Path

    # Assembly QC thresholds (configurable via params)
    MIN_CONTIGS = ${params.assembly_qc_min_contigs ?: 1}
    MAX_CONTIGS = ${params.assembly_qc_max_contigs ?: 1000}
    MIN_TOTAL_LENGTH = ${params.assembly_qc_min_length ?: 1000000}  # 1 Mb
    MIN_N50 = ${params.assembly_qc_min_n50 ?: 10000}  # 10 kb
    MAX_N_CONTENT = ${params.assembly_qc_max_n_pct ?: 5.0}  # 5%

    def calculate_assembly_stats(fasta_file):
        \"\"\"Calculate basic assembly statistics\"\"\"
        contig_lengths = []
        total_n = 0

        with open(fasta_file) as f:
            current_seq = []
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if current_seq:
                        seq = ''.join(current_seq)
                        contig_lengths.append(len(seq))
                        total_n += seq.upper().count('N')
                        current_seq = []
                else:
                    current_seq.append(line)

            # Last sequence
            if current_seq:
                seq = ''.join(current_seq)
                contig_lengths.append(len(seq))
                total_n += seq.upper().count('N')

        if not contig_lengths:
            return None

        # Calculate stats
        contig_lengths.sort(reverse=True)
        total_length = sum(contig_lengths)
        num_contigs = len(contig_lengths)

        # Calculate N50
        cumsum = 0
        n50 = 0
        for length in contig_lengths:
            cumsum += length
            if cumsum >= total_length / 2:
                n50 = length
                break

        # Calculate L50 (number of contigs needed to reach N50)
        cumsum = 0
        l50 = 0
        for length in contig_lengths:
            cumsum += length
            l50 += 1
            if cumsum >= total_length / 2:
                break

        n_content_pct = (total_n / total_length * 100) if total_length > 0 else 0

        return {
            'num_contigs': num_contigs,
            'total_length': total_length,
            'longest_contig': contig_lengths[0],
            'shortest_contig': contig_lengths[-1],
            'mean_contig_length': total_length / num_contigs,
            'n50': n50,
            'l50': l50,
            'n_content_pct': round(n_content_pct, 2),
            'total_n_bases': total_n
        }

    def check_qc_pass(stats):
        \"\"\"Check if assembly passes QC thresholds\"\"\"
        failures = []

        if stats['num_contigs'] < MIN_CONTIGS:
            failures.append(f"Too few contigs: {stats['num_contigs']} < {MIN_CONTIGS}")

        if stats['num_contigs'] > MAX_CONTIGS:
            failures.append(f"Too many contigs: {stats['num_contigs']} > {MAX_CONTIGS} (possibly fragmented)")

        if stats['total_length'] < MIN_TOTAL_LENGTH:
            failures.append(f"Assembly too small: {stats['total_length']} bp < {MIN_TOTAL_LENGTH} bp")

        if stats['n50'] < MIN_N50:
            failures.append(f"N50 too low: {stats['n50']} < {MIN_N50}")

        if stats['n_content_pct'] > MAX_N_CONTENT:
            failures.append(f"Too many Ns: {stats['n_content_pct']}% > {MAX_N_CONTENT}%")

        return len(failures) == 0, failures

    # Run QC
    assembly_file = Path("${assembly}")
    sample = "${sample_id}"

    if not assembly_file.exists():
        # Assembly file doesn't exist - SPAdes must have failed
        result = {
            'sample': sample,
            'qc_status': 'FAILED',
            'reason': 'Assembly file not found (SPAdes failed)',
            'stats': None
        }

        with open(f"{sample}.qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: FAILED\\n")
            f.write(f"Reason: Assembly file not found (SPAdes likely failed)\\n")

        with open(f"{sample}_assembly_qc.json", 'w') as f:
            json.dump(result, f, indent=2)

        exit(1)  # Exit with error if errorStrategy allows

    # Calculate assembly stats
    stats = calculate_assembly_stats(assembly_file)

    if stats is None:
        # Empty assembly file
        result = {
            'sample': sample,
            'qc_status': 'FAILED',
            'reason': 'Empty assembly file (no contigs)',
            'stats': None
        }

        with open(f"{sample}.qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: FAILED\\n")
            f.write(f"Reason: Empty assembly file\\n")

        with open(f"{sample}_assembly_qc.json", 'w') as f:
            json.dump(result, f, indent=2)

        exit(1)

    # Check QC thresholds
    qc_pass, failures = check_qc_pass(stats)

    result = {
        'sample': sample,
        'qc_status': 'PASS' if qc_pass else 'WARN',
        'stats': stats,
        'thresholds': {
            'min_contigs': MIN_CONTIGS,
            'max_contigs': MAX_CONTIGS,
            'min_total_length': MIN_TOTAL_LENGTH,
            'min_n50': MIN_N50,
            'max_n_pct': MAX_N_CONTENT
        }
    }

    if not qc_pass:
        result['qc_warnings'] = failures

        # Create warning file (but don't fail - just warn)
        with open(f"{sample}.qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: WARNING (below QC thresholds)\\n")
            f.write(f"Assembly stats:\\n")
            for key, value in stats.items():
                f.write(f"  {key}: {value}\\n")
            f.write(f"\\nQC warnings:\\n")
            for warning in failures:
                f.write(f"  - {warning}\\n")

    # Write QC metrics
    with open(f"{sample}_assembly_qc.json", 'w') as f:
        json.dump(result, f, indent=2)

    # Print summary
    print(f"\\n{'='*60}")
    print(f"Assembly QC: {sample}")
    print(f"{'='*60}")
    print(f"Status: {result['qc_status']}")
    print(f"Contigs: {stats['num_contigs']:,}")
    print(f"Total length: {stats['total_length']:,} bp")
    print(f"N50: {stats['n50']:,} bp")
    print(f"L50: {stats['l50']}")
    print(f"N content: {stats['n_content_pct']}%")

    if not qc_pass:
        print(f"\\nWarnings:")
        for warning in failures:
            print(f"  ⚠️  {warning}")

    print(f"{'='*60}\\n")
    """
}
