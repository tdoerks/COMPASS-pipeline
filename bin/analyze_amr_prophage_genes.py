#!/usr/bin/env python3
"""
Deep analysis of AMR gene and prophage gene function associations.
Identifies correlations between specific AMR genes and prophage functional classes.
"""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import re

def parse_amr_genes(amr_file):
    """Extract AMR gene names from AMRFinder results"""
    genes = []
    if not Path(amr_file).exists():
        return genes

    with open(amr_file) as f:
        header = next(f, None)
        if not header:
            return genes

        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 9:
                element_type = parts[8]
                gene_symbol = parts[5]

                if element_type == 'AMR' and gene_symbol != 'NA':
                    genes.append(gene_symbol)
    return genes

def parse_prophage_gene_functions(vibrant_annotations_file):
    """Extract prophage gene functional annotations from VIBRANT"""
    functions = []
    if not Path(vibrant_annotations_file).exists():
        return functions

    with open(vibrant_annotations_file) as f:
        header = next(f, None)
        if not header:
            return functions

        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue

            # Extract functional annotations from multiple columns
            ko_name = parts[4] if len(parts) > 4 else ""
            pfam_name = parts[9] if len(parts) > 9 else ""
            vog_name = parts[14] if len(parts) > 14 else ""

            # Categorize prophage genes by function
            function_category = categorize_prophage_function(ko_name, pfam_name, vog_name)
            if function_category:
                functions.append(function_category)

    return functions

def categorize_prophage_function(ko_name, pfam_name, vog_name):
    """Categorize prophage genes into functional classes"""
    combined = f"{ko_name} {pfam_name} {vog_name}".lower()

    # Define functional categories
    if any(term in combined for term in ['integrase', 'recombinase', 'transposase']):
        return 'Integrase/Recombinase'
    elif any(term in combined for term in ['terminase', 'portal']):
        return 'DNA_Packaging'
    elif any(term in combined for term in ['tail', 'baseplate', 'fiber']):
        return 'Tail_Assembly'
    elif any(term in combined for term in ['capsid', 'head', 'coat']):
        return 'Head/Capsid'
    elif any(term in combined for term in ['lyso', 'lysis', 'holin', 'spanin', 'endopeptidase']):
        return 'Lysis'
    elif any(term in combined for term in ['replication', 'primase', 'helicase', 'polymerase']):
        return 'DNA_Replication'
    elif any(term in combined for term in ['repressor', 'regulator', 'antitermination']):
        return 'Regulation'
    elif any(term in combined for term in ['recombinase', 'excisionase']):
        return 'Recombination'
    elif any(term in combined for term in ['antirepressor', 'anti-repressor']):
        return 'Antirepressor'
    elif any(term in combined for term in ['methylase', 'methyltransferase']):
        return 'DNA_Modification'
    elif any(term in combined for term in ['endonuclease', 'nuclease']):
        return 'Nuclease'
    else:
        return None

def analyze_associations(results_dir):
    """Analyze AMR-prophage gene function associations"""
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"

    if not amr_dir.exists():
        print(f"❌ Error: AMR directory not found: {amr_dir}")
        sys.exit(1)
    if not vibrant_dir.exists():
        print(f"❌ Error: VIBRANT directory not found: {vibrant_dir}")
        sys.exit(1)

    # Data structures
    sample_data = []
    amr_function_cooccur = defaultdict(lambda: defaultdict(int))
    all_amr_genes = Counter()
    all_prophage_functions = Counter()

    # Parse all samples
    for amr_file in amr_dir.glob("*_amr.tsv"):
        sample_id = amr_file.stem.replace('_amr', '')

        # Find VIBRANT annotations
        vibrant_sample_dir = vibrant_dir / f"{sample_id}_vibrant"
        vibrant_annotations = vibrant_sample_dir / f"VIBRANT_{sample_id}_scaffolds" / f"VIBRANT_results_{sample_id}_scaffolds" / f"VIBRANT_annotations_{sample_id}_scaffolds.tsv"

        amr_genes = parse_amr_genes(amr_file)
        prophage_functions = parse_prophage_gene_functions(vibrant_annotations)

        if not amr_genes or not prophage_functions:
            continue

        sample_data.append({
            'sample': sample_id,
            'amr_genes': amr_genes,
            'prophage_functions': prophage_functions,
            'amr_count': len(amr_genes),
            'function_count': len(prophage_functions)
        })

        # Track frequencies
        all_amr_genes.update(amr_genes)
        all_prophage_functions.update(prophage_functions)

        # Track co-occurrences
        for amr in set(amr_genes):  # Use set to count once per sample
            for function in set(prophage_functions):
                amr_function_cooccur[amr][function] += 1

    return sample_data, amr_function_cooccur, all_amr_genes, all_prophage_functions

def print_analysis(sample_data, amr_function_cooccur, all_amr_genes, all_prophage_functions, results_dir):
    """Print comprehensive analysis"""

    print("\n" + "="*80)
    print(f"AMR Gene - Prophage Function Association Analysis")
    print(f"Results: {results_dir}")
    print("="*80)

    print(f"\n📊 Dataset Summary:")
    print(f"  Samples with both AMR and prophage data: {len(sample_data)}")
    print(f"  Unique AMR genes: {len(all_amr_genes)}")
    print(f"  Prophage functional categories: {len(all_prophage_functions)}")

    # Top AMR genes
    print(f"\n🦠 Top 15 AMR Genes:")
    print(f"  {'Gene':<25} {'Samples':<10} {'% of samples'}")
    print("  " + "-"*55)
    for gene, count in all_amr_genes.most_common(15):
        pct = (count / len(sample_data)) * 100
        print(f"  {gene:<25} {count:<10} {pct:>6.1f}%")

    # Prophage function distribution
    print(f"\n🧬 Prophage Function Distribution:")
    print(f"  {'Function Category':<30} {'Count':<10} {'% of samples'}")
    print("  " + "-"*60)
    for function, count in all_prophage_functions.most_common():
        pct = (count / len(sample_data)) * 100
        print(f"  {function:<30} {count:<10} {pct:>6.1f}%")

    # Strong AMR-Function associations
    print(f"\n🔗 Strong AMR - Prophage Function Associations:")
    print(f"  (Co-occurring in ≥15 samples)")
    print(f"  {'AMR Gene':<25} {'Prophage Function':<30} {'Co-occur':<10} {'% of AMR samples'}")
    print("  " + "-"*85)

    associations = []
    for amr, function_counts in amr_function_cooccur.items():
        amr_total = all_amr_genes[amr]
        for function, cooccur_count in function_counts.items():
            if cooccur_count >= 15:
                pct_amr = (cooccur_count / amr_total) * 100
                associations.append((amr, function, cooccur_count, amr_total, pct_amr))

    # Sort by co-occurrence
    associations.sort(key=lambda x: x[2], reverse=True)

    for amr, function, cooccur, amr_total, pct in associations[:50]:
        print(f"  {amr:<25} {function:<30} {cooccur:<10} {pct:>6.1f}%")

    # Key insights
    print(f"\n💡 Key Insights:")

    # Which AMR genes are most associated with integrases?
    integrase_amr = [(amr, amr_function_cooccur[amr]['Integrase/Recombinase'])
                     for amr in all_amr_genes if amr_function_cooccur[amr]['Integrase/Recombinase'] >= 10]
    integrase_amr.sort(key=lambda x: x[1], reverse=True)

    if integrase_amr:
        print(f"\n  📌 AMR genes frequently co-occurring with Integrases/Recombinases:")
        for amr, count in integrase_amr[:10]:
            print(f"     {amr:<25} {count} samples")

    # Samples with high prophage function diversity
    print(f"\n🎯 Samples with Highest Prophage Functional Diversity:")
    print(f"  {'Sample ID':<20} {'AMR genes':<12} {'Unique functions':<18} {'Total'}")
    print("  " + "-"*65)

    sorted_samples = sorted(sample_data,
                          key=lambda x: len(set(x['prophage_functions'])),
                          reverse=True)

    for sample in sorted_samples[:20]:
        unique_functions = len(set(sample['prophage_functions']))
        total = sample['amr_count'] + unique_functions
        print(f"  {sample['sample']:<20} {sample['amr_count']:<12} {unique_functions:<18} {total}")

def main():
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    else:
        results_dir = Path("/homes/tylerdoe/compass_kansas_results/results_kansas_2024")

    sample_data, amr_function_cooccur, all_amr_genes, all_prophage_functions = analyze_associations(results_dir)

    if not sample_data:
        print("❌ No samples with both AMR and prophage function data found!")
        sys.exit(1)

    print_analysis(sample_data, amr_function_cooccur, all_amr_genes, all_prophage_functions, results_dir)

    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
