#!/usr/bin/env python3
"""
Visualize AMR Gene Context in Prophages

Creates simple text-based gene maps showing AMR gene positions
within prophage sequences. Helps identify false positives and
understand gene organization.

Usage:
    # Visualize specific sample
    python3 visualize_amr_prophage_context.py /bulk/path/results SRR12345678

    # Save output to file
    python3 visualize_amr_prophage_context.py /bulk/path/results SRR12345678 --output gene_map.txt

    # Multiple samples
    python3 visualize_amr_prophage_context.py /bulk/path/results SRR12345678 SRR12345679

Author: Claude + Tyler Doerks
Date: January 2026
"""

import sys
import argparse
from pathlib import Path
from Bio import SeqIO


def parse_amr_results(results_dir, sample_id):
    """Parse AMRFinder results for this sample"""

    amr_file = Path(results_dir) / "amrfinder" / f"{sample_id}_amr.tsv"

    if not amr_file.exists():
        return []

    amr_genes = []
    try:
        with open(amr_file, 'r') as f:
            lines = f.readlines()

            # Find header
            header_idx = 0
            for i, line in enumerate(lines):
                if 'Contig id' in line or 'Protein identifier' in line:
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
                start = int(parts[2]) if parts[2].isdigit() else 0
                end = int(parts[3]) if parts[3].isdigit() else 0
                gene_symbol = parts[5]
                element_type = parts[8]

                if element_type == 'AMR' and gene_symbol != 'NA':
                    amr_genes.append({
                        'contig': contig,
                        'start': start,
                        'end': end,
                        'gene': gene_symbol,
                        'class': parts[10] if len(parts) > 10 else '',
                        'strand': parts[4] if len(parts) > 4 else '+'
                    })

    except Exception as e:
        print(f"  ⚠️  Error parsing AMR file: {e}")

    return amr_genes


def get_prophage_sequences(results_dir, sample_id):
    """Get prophage sequences from VIBRANT output"""

    vibrant_dir = Path(results_dir) / "vibrant"
    phage_file = vibrant_dir / f"{sample_id}_phages.fna"

    if not phage_file.exists():
        return []

    try:
        return list(SeqIO.parse(phage_file, "fasta"))
    except Exception as e:
        print(f"  ⚠️  Error reading prophage file: {e}")
        return []


def find_amr_in_prophage(prophage_seq, amr_genes):
    """
    Find which AMR genes are located in this prophage sequence

    Returns: list of AMR genes that match this prophage contig
    """
    matching_genes = []

    prophage_id = prophage_seq.id

    for gene in amr_genes:
        # Check if contig ID matches prophage ID
        if prophage_id in gene['contig'] or gene['contig'] in prophage_id:
            matching_genes.append(gene)

    return matching_genes


def draw_gene_map(prophage_seq, amr_genes, width=100):
    """
    Draw a simple text-based gene map

    Args:
        prophage_seq: BioPython SeqRecord
        amr_genes: List of AMR genes on this prophage
        width: Width of the map in characters

    Returns: list of strings (lines of the map)
    """
    lines = []
    seq_len = len(prophage_seq.seq)

    lines.append(f"\n{'='*width}")
    lines.append(f"Prophage: {prophage_seq.id}")
    lines.append(f"Length: {seq_len:,} bp")
    lines.append(f"AMR genes: {len(amr_genes)}")
    lines.append(f"{'='*width}")

    if not amr_genes:
        lines.append("\n  (No AMR genes found in this prophage)")
        return lines

    # Draw scale
    lines.append(f"\nScale:")
    scale_line = "0" + " " * (width - 20) + f"{seq_len:,} bp"
    lines.append(scale_line)

    # Draw prophage as a line
    prophage_line = "[" + "-" * (width - 2) + "]"
    lines.append(prophage_line)

    # Draw each AMR gene
    lines.append(f"\nAMR Genes:")
    for gene_info in amr_genes:
        gene_name = gene_info['gene']
        start = gene_info['start']
        end = gene_info['end']
        strand = gene_info['strand']
        drug_class = gene_info['class']

        # Calculate position on map
        rel_start = int((start / seq_len) * (width - 2))
        rel_end = int((end / seq_len) * (width - 2))
        gene_width = max(1, rel_end - rel_start)

        # Draw gene
        gene_line = " " * rel_start
        if strand == '+':
            gene_line += ">" * gene_width
        else:
            gene_line += "<" * gene_width

        # Add label
        label = f"  {gene_name} ({drug_class})"
        label += f" | {start:,}-{end:,} bp ({strand})"

        lines.append(gene_line + label)

    return lines


def visualize_sample(results_dir, sample_id):
    """
    Create gene maps for all prophages in this sample that contain AMR genes
    """
    print(f"\n" + "="*100)
    print(f"SAMPLE: {sample_id}")
    print("="*100)

    # Get prophages
    prophages = get_prophage_sequences(results_dir, sample_id)
    print(f"\n🦠 Total prophages: {len(prophages)}")

    if not prophages:
        print(f"  ❌ No prophage sequences found")
        return []

    # Get AMR genes
    amr_genes = parse_amr_results(results_dir, sample_id)
    print(f"💊 Total AMR genes (whole genome): {len(amr_genes)}")

    # Find prophages with AMR genes
    maps = []
    prophages_with_amr = 0

    for prophage_seq in prophages:
        matching_amr = find_amr_in_prophage(prophage_seq, amr_genes)

        if matching_amr:
            prophages_with_amr += 1
            gene_map = draw_gene_map(prophage_seq, matching_amr)
            maps.extend(gene_map)

    print(f"🎯 Prophages with AMR genes: {prophages_with_amr}")

    if prophages_with_amr == 0:
        print(f"\n  ℹ️  No AMR genes found in prophage sequences")
        print(f"     This sample does not carry AMR genes in prophages")

    return maps


def main():
    parser = argparse.ArgumentParser(
        description='Visualize AMR gene context in prophages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single sample
  %(prog)s /bulk/path/results SRR12345678

  # Multiple samples
  %(prog)s /bulk/path/results SRR12345678 SRR12345679

  # Save to file
  %(prog)s /bulk/path/results SRR12345678 --output gene_maps.txt

Output:
  Simple text-based gene maps showing:
  - Prophage length
  - AMR gene positions
  - Gene orientation (strand)
  - Drug class

Reading the Map:
  [---->>>---<<<------]  Prophage sequence
       ^^^              AMR gene on + strand (forward)
          ^^^           AMR gene on - strand (reverse)
        """
    )

    parser.add_argument('results_dir', help='Results directory')
    parser.add_argument('samples', nargs='+', help='Sample IDs')
    parser.add_argument('--output', '-o', help='Save output to file')
    parser.add_argument('--width', '-w', type=int, default=100, help='Map width (default: 100)')

    args = parser.parse_args()

    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    # Visualize each sample
    all_maps = []

    for sample_id in args.samples:
        maps = visualize_sample(results_dir, sample_id)
        all_maps.extend(maps)

    # Print maps
    for line in all_maps:
        print(line)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(all_maps))
        print(f"\n✅ Gene maps saved to: {args.output}")

    print(f"\n" + "="*100)
    print(f"VISUALIZATION COMPLETE")
    print("="*100)
    print(f"\n💡 TIP: Use these maps to:")
    print(f"   • Verify AMR genes are actually in prophage regions")
    print(f"   • Check gene positions (start, end, strand)")
    print(f"   • Identify potential false positives")
    print(f"   • Understand AMR gene organization in prophages")


if __name__ == '__main__':
    main()
