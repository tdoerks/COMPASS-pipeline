#!/usr/bin/env python3
"""
Contig-level analysis proving physical linkage between AMR genes and prophages.
Identifies which contigs contain both AMR genes and prophage sequences.
"""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import re

def parse_amr_contigs(amr_file):
    """Extract AMR genes and their contigs from AMRFinder results"""
    amr_by_contig = defaultdict(list)

    if not Path(amr_file).exists():
        return amr_by_contig

    with open(amr_file) as f:
        header = next(f, None)
        if not header:
            return amr_by_contig

        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 9:
                contig = parts[1]
                element_type = parts[8]
                gene_symbol = parts[5]
                gene_class = parts[10] if len(parts) > 10 else "UNKNOWN"

                # Only AMR genes (exclude virulence/stress)
                if element_type == 'AMR' and gene_symbol != 'NA':
                    amr_by_contig[contig].append({
                        'gene': gene_symbol,
                        'class': gene_class,
                        'start': int(parts[2]),
                        'end': int(parts[3])
                    })

    return amr_by_contig

def parse_prophage_contigs(vibrant_phages_file):
    """Extract prophage-containing contigs from VIBRANT phages.fna"""
    prophage_contigs = set()

    if not Path(vibrant_phages_file).exists():
        return prophage_contigs

    with open(vibrant_phages_file) as f:
        for line in f:
            if line.startswith('>'):
                # Extract contig name from header
                # Format: >NODE_1_length_423855_cov_13.011484_fragment_4
                contig = line.strip()[1:].split('_fragment')[0]
                if '_fragment' in line:
                    # Remove the fragment suffix to get original contig name
                    contig = '_'.join(line.strip()[1:].split('_')[:-2])
                else:
                    contig = line.strip()[1:].split()[0]
                prophage_contigs.add(contig)

    return prophage_contigs

def parse_mobsuite(mobsuite_file):
    """Parse MOBsuite plasmid detection results"""
    if not Path(mobsuite_file).exists():
        return 0, []

    with open(mobsuite_file) as f:
        header = next(f, None)
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                num_plasmids = int(parts[1]) if parts[1].isdigit() else 0
                plasmid_types = parts[2] if len(parts) > 2 and parts[2] != '-' else None
                return num_plasmids, plasmid_types

    return 0, None

def parse_mlst(mlst_file):
    """Parse MLST sequence type"""
    if not Path(mlst_file).exists():
        return None

    with open(mlst_file) as f:
        line = f.readline().strip()
        parts = line.split('\t')
        if len(parts) >= 3:
            st = parts[2]
            return st if st != '-' else None

    return None

def analyze_colocation(results_dir):
    """Analyze AMR-prophage co-location across all samples"""
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"
    mobsuite_dir = results_dir / "mobsuite"
    mlst_dir = results_dir / "mlst"

    # Summary statistics
    samples_analyzed = 0
    samples_with_colocation = 0
    total_amr_genes = 0
    amr_on_prophage_contigs = 0
    amr_on_nonprophage_contigs = 0

    # Detailed tracking
    colocated_samples = []
    amr_gene_locations = Counter()  # AMR gene -> "prophage" or "non-prophage"
    amr_classes_on_prophages = Counter()

    # Sequence type distribution
    st_distribution = Counter()
    st_with_colocation = Counter()

    # Process all samples
    for amr_file in sorted(amr_dir.glob("*_amr.tsv")):
        sample_id = amr_file.stem.replace('_amr', '')

        # Parse data
        amr_by_contig = parse_amr_contigs(amr_file)

        vibrant_phages_file = vibrant_dir / f"{sample_id}_phages.fna"
        prophage_contigs = parse_prophage_contigs(vibrant_phages_file)

        mobsuite_file = mobsuite_dir / f"{sample_id}_mobsuite" / "mobtyper_results.txt"
        num_plasmids, plasmid_types = parse_mobsuite(mobsuite_file)

        mlst_file = mlst_dir / f"{sample_id}_mlst.tsv"
        st = parse_mlst(mlst_file)

        if st:
            st_distribution[st] += 1

        if not amr_by_contig:
            continue

        samples_analyzed += 1

        # Track AMR genes on prophage vs non-prophage contigs
        sample_amr_on_prophage = []
        sample_amr_on_other = []

        for contig, amr_genes in amr_by_contig.items():
            is_prophage_contig = any(contig.startswith(pc) for pc in prophage_contigs)

            for amr_info in amr_genes:
                gene = amr_info['gene']
                gene_class = amr_info['class']

                total_amr_genes += 1

                if is_prophage_contig:
                    amr_on_prophage_contigs += 1
                    amr_gene_locations[f"{gene}_prophage"] += 1
                    amr_classes_on_prophages[gene_class] += 1
                    sample_amr_on_prophage.append({
                        'gene': gene,
                        'class': gene_class,
                        'contig': contig
                    })
                else:
                    amr_on_nonprophage_contigs += 1
                    amr_gene_locations[f"{gene}_other"] += 1
                    sample_amr_on_other.append({
                        'gene': gene,
                        'class': gene_class,
                        'contig': contig
                    })

        # Track samples with co-location
        if sample_amr_on_prophage:
            samples_with_colocation += 1
            if st:
                st_with_colocation[st] += 1

            colocated_samples.append({
                'sample': sample_id,
                'st': st,
                'num_plasmids': num_plasmids,
                'amr_on_prophage': len(sample_amr_on_prophage),
                'amr_on_other': len(sample_amr_on_other),
                'prophage_amr_genes': sample_amr_on_prophage,
                'other_amr_genes': sample_amr_on_other
            })

    return {
        'samples_analyzed': samples_analyzed,
        'samples_with_colocation': samples_with_colocation,
        'total_amr_genes': total_amr_genes,
        'amr_on_prophage_contigs': amr_on_prophage_contigs,
        'amr_on_nonprophage_contigs': amr_on_nonprophage_contigs,
        'colocated_samples': colocated_samples,
        'amr_gene_locations': amr_gene_locations,
        'amr_classes_on_prophages': amr_classes_on_prophages,
        'st_distribution': st_distribution,
        'st_with_colocation': st_with_colocation
    }

def print_analysis(data, results_dir):
    """Print comprehensive analysis report"""

    print("\n" + "="*85)
    print("AMR-Prophage Physical Co-location Analysis")
    print("Direct Evidence of AMR Genes on Prophage-Containing Contigs")
    print(f"Results: {results_dir}")
    print("="*85)

    print(f"\n📊 Overall Statistics:")
    print(f"  Samples analyzed: {data['samples_analyzed']}")
    print(f"  Samples with AMR on prophage contigs: {data['samples_with_colocation']} "
          f"({data['samples_with_colocation']/data['samples_analyzed']*100:.1f}%)")
    print(f"\n  Total AMR genes detected: {data['total_amr_genes']}")
    print(f"  AMR genes on PROPHAGE contigs: {data['amr_on_prophage_contigs']} "
          f"({data['amr_on_prophage_contigs']/data['total_amr_genes']*100:.1f}%)")
    print(f"  AMR genes on NON-PROPHAGE contigs: {data['amr_on_nonprophage_contigs']} "
          f"({data['amr_on_nonprophage_contigs']/data['total_amr_genes']*100:.1f}%)")

    # AMR classes on prophages
    print(f"\n💊 AMR Drug Classes Found on Prophage Contigs:")
    print(f"  {'Drug Class':<30} {'Count':<10}")
    print("  " + "-"*45)
    for drug_class, count in data['amr_classes_on_prophages'].most_common():
        print(f"  {drug_class:<30} {count:<10}")

    # Which specific AMR genes are on prophages vs not
    print(f"\n🧬 AMR Gene Distribution (Prophage vs Non-Prophage Contigs):")

    # Group by gene
    genes = set()
    for key in data['amr_gene_locations'].keys():
        gene = key.replace('_prophage', '').replace('_other', '')
        genes.add(gene)

    print(f"  {'Gene':<25} {'On Prophage':<15} {'On Other':<15} {'% Prophage'}")
    print("  " + "-"*75)

    for gene in sorted(genes):
        prophage_count = data['amr_gene_locations'].get(f"{gene}_prophage", 0)
        other_count = data['amr_gene_locations'].get(f"{gene}_other", 0)
        total = prophage_count + other_count

        if total > 0:
            pct = (prophage_count / total) * 100
            print(f"  {gene:<25} {prophage_count:<15} {other_count:<15} {pct:>6.1f}%")

    # Sequence type analysis
    print(f"\n🔬 Sequence Type Distribution:")
    print(f"  {'ST':<10} {'Total Samples':<15} {'With Prophage-AMR':<20} {'% with Prophage-AMR'}")
    print("  " + "-"*70)

    for st, count in data['st_distribution'].most_common(15):
        coloc_count = data['st_with_colocation'].get(st, 0)
        pct = (coloc_count / count) * 100 if count > 0 else 0
        print(f"  {st:<10} {count:<15} {coloc_count:<20} {pct:>6.1f}%")

    # Example samples
    print(f"\n📋 Examples of Samples with AMR-Prophage Co-location:")
    print(f"  {'Sample':<20} {'ST':<8} {'Plasmids':<10} {'AMR on Prophage':<18} {'AMR on Other'}")
    print("  " + "-"*75)

    for sample_data in sorted(data['colocated_samples'],
                             key=lambda x: x['amr_on_prophage'],
                             reverse=True)[:20]:
        st_str = sample_data['st'] if sample_data['st'] else 'Unknown'
        print(f"  {sample_data['sample']:<20} {st_str:<8} {sample_data['num_plasmids']:<10} "
              f"{sample_data['amr_on_prophage']:<18} {sample_data['amr_on_other']}")

    # Detailed example
    if data['colocated_samples']:
        print(f"\n🔍 Detailed Example - {data['colocated_samples'][0]['sample']}:")
        example = data['colocated_samples'][0]

        if example['prophage_amr_genes']:
            print(f"\n  AMR Genes on Prophage Contigs:")
            for amr in example['prophage_amr_genes']:
                print(f"    ✅ {amr['gene']:<20} ({amr['class']:<20}) on {amr['contig']}")

        if example['other_amr_genes']:
            print(f"\n  AMR Genes on Non-Prophage Contigs:")
            for amr in example['other_amr_genes']:
                print(f"    ⚪ {amr['gene']:<20} ({amr['class']:<20}) on {amr['contig']}")

def main():
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    else:
        results_dir = Path("/homes/tylerdoe/compass_kansas_results/results_kansas_2024")

    data = analyze_colocation(results_dir)

    if data['samples_analyzed'] == 0:
        print("❌ No samples with AMR data found!")
        sys.exit(1)

    print_analysis(data, results_dir)

    print("\n" + "="*85)
    print("✅ Analysis complete!")
    print("="*85 + "\n")

if __name__ == "__main__":
    main()
