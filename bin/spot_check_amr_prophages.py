#!/usr/bin/env python3
"""
Spot Check AMR-in-Prophage Results - Manual Validation

Deep-dive validation on selected samples to confirm AMR genes are
truly located in prophage DNA. Extracts sequences and prepares for BLAST.

Usage:
    # Check specific samples
    python3 spot_check_amr_prophages.py /bulk/path/to/results SRR12345678 SRR12345679

    # Check top N samples with most AMR genes
    python3 spot_check_amr_prophages.py /bulk/path/to/results --top 5

    # Generate BLAST-ready FASTA
    python3 spot_check_amr_prophages.py /bulk/path/to/results SRR12345678 --blast-output prophages_for_blast.fasta

Author: Claude + Tyler Doerks
Date: January 2026
"""

import sys
import argparse
from pathlib import Path
from Bio import SeqIO
from collections import Counter


def extract_prophage_sequence(results_dir, sample_id, prophage_id=None):
    """
    Extract specific prophage sequence(s) from VIBRANT output

    Args:
        results_dir: Path to results directory
        sample_id: Sample ID (e.g., SRR12345678)
        prophage_id: Specific prophage ID to extract (optional, extracts all if None)

    Returns: list of SeqRecord objects
    """
    results_dir = Path(results_dir)
    vibrant_dir = results_dir / "vibrant"
    phage_file = vibrant_dir / f"{sample_id}_phages.fna"

    if not phage_file.exists():
        print(f"  ❌ Prophage file not found: {phage_file}")
        return []

    prophage_seqs = []
    try:
        for record in SeqIO.parse(phage_file, "fasta"):
            if prophage_id is None or prophage_id in record.id:
                prophage_seqs.append(record)
    except Exception as e:
        print(f"  ❌ Error reading prophage file: {e}")
        return []

    return prophage_seqs


def get_amr_genes_from_prophages(results_dir, sample_id):
    """
    Get AMR genes detected in prophages for this sample

    Reads whole-genome AMRFinder results and checks which contigs are prophages

    Returns: list of dicts with gene info
    """
    results_dir = Path(results_dir)
    amr_file = results_dir / "amrfinder" / f"{sample_id}_amr.tsv"

    if not amr_file.exists():
        print(f"  ❌ AMR file not found: {amr_file}")
        return []

    # Get prophage contig IDs
    prophage_seqs = extract_prophage_sequence(results_dir, sample_id)
    prophage_contigs = {seq.id for seq in prophage_seqs}

    # Parse AMR results
    amr_genes = []
    try:
        with open(amr_file, 'r') as f:
            lines = f.readlines()

            # Find header
            header_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('#') or line.startswith('Protein') or line.startswith('Contig'):
                    header_idx = i
                    break

            # Parse data
            for line in lines[header_idx + 1:]:
                if line.startswith('#') or not line.strip():
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 11:
                    continue

                contig = parts[1]
                gene_symbol = parts[5]
                element_type = parts[8]

                # Check if this AMR gene is on a prophage contig
                if element_type == 'AMR' and gene_symbol != 'NA':
                    # Check if contig matches any prophage ID
                    is_in_prophage = any(prophage_id in contig for prophage_id in prophage_contigs)

                    if is_in_prophage:
                        amr_genes.append({
                            'gene': gene_symbol,
                            'class': parts[10] if len(parts) > 10 else '',
                            'contig': contig,
                            'start': parts[2] if len(parts) > 2 else '',
                            'end': parts[3] if len(parts) > 3 else '',
                            'method': parts[7] if len(parts) > 7 else ''
                        })

    except Exception as e:
        print(f"  ⚠️  Error parsing AMR file: {e}")

    return amr_genes


def analyze_prophage_characteristics(prophage_seq):
    """
    Analyze prophage sequence characteristics

    Helps identify if it looks like real phage DNA
    """
    seq_len = len(prophage_seq.seq)

    # Calculate GC content
    gc_count = prophage_seq.seq.count('G') + prophage_seq.seq.count('C')
    gc_content = (gc_count / seq_len) * 100 if seq_len > 0 else 0

    # Check for Ns (assembly gaps)
    n_count = prophage_seq.seq.count('N') + prophage_seq.seq.count('n')
    n_pct = (n_count / seq_len) * 100 if seq_len > 0 else 0

    return {
        'length': seq_len,
        'gc_content': gc_content,
        'n_count': n_count,
        'n_pct': n_pct
    }


def spot_check_sample(results_dir, sample_id):
    """
    Perform detailed validation on a single sample

    Returns: validation report dict
    """
    print(f"\n" + "="*80)
    print(f"SPOT CHECK: {sample_id}")
    print("="*80)

    results_dir = Path(results_dir)

    # Get AMR genes in prophages
    amr_genes = get_amr_genes_from_prophages(results_dir, sample_id)

    print(f"\n🦠 AMR Genes in Prophages: {len(amr_genes)}")

    if not amr_genes:
        print(f"  ℹ️  No AMR genes found in prophages for this sample")
        return None

    # Show genes
    print(f"\n  Genes found:")
    for gene_info in amr_genes:
        print(f"    • {gene_info['gene']} ({gene_info['class']})")
        print(f"      Contig: {gene_info['contig']}")
        print(f"      Location: {gene_info['start']}-{gene_info['end']}")
        print(f"      Method: {gene_info['method']}")

    # Extract prophage sequences
    prophage_seqs = extract_prophage_sequence(results_dir, sample_id)

    print(f"\n🧬 Prophage Sequences: {len(prophage_seqs)}")

    # Analyze each prophage
    print(f"\n  Prophage Characteristics:")
    for seq in prophage_seqs:
        chars = analyze_prophage_characteristics(seq)
        print(f"\n    {seq.id}:")
        print(f"      Length: {chars['length']:,} bp")
        print(f"      GC content: {chars['gc_content']:.1f}%")
        print(f"      Assembly gaps (Ns): {chars['n_count']} ({chars['n_pct']:.2f}%)")

        # Interpretation
        if chars['length'] < 5000:
            print(f"      ⚠️  SHORT - Possible fragment or cryptic prophage")
        elif chars['length'] > 80000:
            print(f"      ✅ LARGE - Possible complete prophage or jumbo phage")
        else:
            print(f"      ✅ TYPICAL - Size consistent with prophage")

        if chars['n_pct'] > 1.0:
            print(f"      ⚠️  HIGH N% - Assembly quality concerns")

    return {
        'sample': sample_id,
        'amr_gene_count': len(amr_genes),
        'amr_genes': amr_genes,
        'prophage_count': len(prophage_seqs),
        'prophages': prophage_seqs
    }


def export_for_blast(samples_data, output_fasta):
    """
    Export prophage sequences to FASTA for BLAST analysis

    This allows manual verification that sequences are phage DNA
    """
    print(f"\n" + "="*80)
    print(f"EXPORTING SEQUENCES FOR BLAST VALIDATION")
    print("="*80)

    all_seqs = []
    for data in samples_data:
        if data is None:
            continue

        sample = data['sample']
        for seq in data['prophages']:
            # Rename to include sample ID
            seq.id = f"{sample}_{seq.id}"
            seq.description = f"sample={sample} length={len(seq.seq)}bp"
            all_seqs.append(seq)

    if not all_seqs:
        print(f"❌ No sequences to export")
        return

    # Write FASTA
    SeqIO.write(all_seqs, output_fasta, "fasta")

    print(f"\n✅ Exported {len(all_seqs)} prophage sequences to: {output_fasta}")
    print(f"\n📋 BLAST Validation Steps:")
    print(f"  1. Upload to NCBI BLAST: https://blast.ncbi.nlm.nih.gov/Blast.cgi")
    print(f"  2. Choose 'Nucleotide BLAST' (blastn)")
    print(f"  3. Select database: 'Nucleotide collection (nr/nt)'")
    print(f"  4. Run BLAST")
    print(f"\n🔍 What to Look For:")
    print(f"  ✅ PASS: Top hits are phage/prophage sequences")
    print(f"  ⚠️  WARNING: Mixed hits (some phage, some bacterial)")
    print(f"  🚨 FAIL: Top hits are bacterial chromosomal sequences (not phage)")


def generate_spot_check_report(samples_data, output_file=None):
    """Generate summary report"""

    report_lines = []
    report_lines.append("\n" + "="*80)
    report_lines.append("SPOT CHECK VALIDATION REPORT")
    report_lines.append("="*80)

    valid_samples = [d for d in samples_data if d is not None]

    if not valid_samples:
        report_lines.append("\n❌ No samples analyzed")
        print('\n'.join(report_lines))
        return

    report_lines.append(f"\n📊 Summary:")
    report_lines.append(f"  Samples checked: {len(valid_samples)}")
    report_lines.append(f"  Total AMR genes in prophages: {sum(d['amr_gene_count'] for d in valid_samples)}")
    report_lines.append(f"  Total prophage sequences: {sum(d['prophage_count'] for d in valid_samples)}")

    # Gene statistics
    all_genes = []
    for data in valid_samples:
        all_genes.extend([g['gene'] for g in data['amr_genes']])

    gene_counts = Counter(all_genes)

    report_lines.append(f"\n🧬 Top AMR Genes Found:")
    for gene, count in gene_counts.most_common(10):
        report_lines.append(f"  {gene}: {count}")

    # Prophage size distribution
    all_lengths = []
    for data in valid_samples:
        all_lengths.extend([len(seq.seq) for seq in data['prophages']])

    if all_lengths:
        import statistics
        report_lines.append(f"\n📏 Prophage Size Distribution:")
        report_lines.append(f"  Mean: {statistics.mean(all_lengths):,.0f} bp")
        report_lines.append(f"  Median: {statistics.median(all_lengths):,.0f} bp")
        report_lines.append(f"  Range: {min(all_lengths):,} - {max(all_lengths):,} bp")

    report_lines.append(f"\n✅ NEXT STEPS:")
    report_lines.append(f"  1. BLAST validate: Use exported FASTA to confirm phage identity")
    report_lines.append(f"  2. Visualize: Use visualize_amr_prophage_context.py for gene maps")
    report_lines.append(f"  3. Literature check: Compare genes to published phage-AMR studies")

    report_lines.append("\n" + "="*80 + "\n")

    # Print and optionally save
    for line in report_lines:
        print(line)

    if output_file:
        with open(output_file, 'w') as f:
            f.write('\n'.join(report_lines))
        print(f"✅ Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Spot check AMR-prophage results with detailed validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check specific samples
  %(prog)s /bulk/path/results SRR12345678 SRR12345679

  # Generate BLAST file
  %(prog)s /bulk/path/results SRR12345678 --blast-output for_blast.fasta

  # Save detailed report
  %(prog)s /bulk/path/results SRR12345678 --report spot_check_report.txt

Output:
  - Detailed sequence characteristics
  - AMR gene locations
  - FASTA file for BLAST validation
  - Validation recommendations
        """
    )

    parser.add_argument('results_dir', help='Results directory (contains vibrant/ and amrfinder/)')
    parser.add_argument('samples', nargs='*', help='Sample IDs to check (e.g., SRR12345678)')
    parser.add_argument('--blast-output', '-b', help='Output FASTA file for BLAST validation')
    parser.add_argument('--report', '-r', help='Save report to file')

    args = parser.parse_args()

    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    if not args.samples:
        print(f"❌ Error: No samples specified")
        print(f"   Usage: {sys.argv[0]} <results_dir> <sample1> <sample2> ...")
        sys.exit(1)

    # Analyze each sample
    samples_data = []
    for sample_id in args.samples:
        data = spot_check_sample(results_dir, sample_id)
        samples_data.append(data)

    # Generate report
    generate_spot_check_report(samples_data, args.report)

    # Export for BLAST if requested
    if args.blast_output:
        export_for_blast(samples_data, args.blast_output)


if __name__ == '__main__':
    main()
