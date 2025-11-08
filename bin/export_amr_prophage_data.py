#!/usr/bin/env python3
"""
Export AMR-prophage analysis data to CSV files for publication and visualization.
Creates multiple CSV files with different levels of detail.
"""
import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
import re

def parse_amr_genes(amr_file):
    """Extract AMR genes from AMRFinder results"""
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
                gene_class = parts[10] if len(parts) > 10 else "UNKNOWN"
                contig = parts[1]

                if element_type == 'AMR' and gene_symbol != 'NA':
                    genes.append({
                        'gene': gene_symbol,
                        'class': gene_class,
                        'contig': contig,
                        'start': int(parts[2]),
                        'end': int(parts[3])
                    })
    return genes

def parse_prophage_contigs(vibrant_phages_file):
    """Extract prophage-containing contigs"""
    prophage_contigs = set()
    if not Path(vibrant_phages_file).exists():
        return prophage_contigs

    with open(vibrant_phages_file) as f:
        for line in f:
            if line.startswith('>'):
                contig = '_'.join(line.strip()[1:].split('_')[:-2])
                prophage_contigs.add(contig)
    return prophage_contigs

def parse_prophage_functions(vibrant_annotations_file):
    """Extract prophage gene functional annotations"""
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

            ko_name = parts[4] if len(parts) > 4 else ""
            pfam_name = parts[9] if len(parts) > 9 else ""
            vog_name = parts[14] if len(parts) > 14 else ""

            function_category = categorize_prophage_function(ko_name, pfam_name, vog_name)
            if function_category:
                functions.append(function_category)

    return functions

def categorize_prophage_function(ko_name, pfam_name, vog_name):
    """Categorize prophage genes into functional classes"""
    combined = f"{ko_name} {pfam_name} {vog_name}".lower()

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

def export_all_data(results_dir, output_dir):
    """Export all analysis data to CSV files"""
    results_dir = Path(results_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    year = results_dir.name.split('_')[-1] if '_' in results_dir.name else 'unknown'

    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"
    mlst_dir = results_dir / "mlst"

    # Data structures
    sample_summary = []
    amr_gene_detail = []
    prophage_function_detail = []
    colocation_detail = []

    for amr_file in sorted(amr_dir.glob("*_amr.tsv")):
        sample_id = amr_file.stem.replace('_amr', '')

        # Parse data
        amr_genes = parse_amr_genes(amr_file)
        vibrant_phages_file = vibrant_dir / f"{sample_id}_phages.fna"
        prophage_contigs = parse_prophage_contigs(vibrant_phages_file)

        vibrant_sample_dir = vibrant_dir / f"{sample_id}_vibrant"
        vibrant_annotations = vibrant_sample_dir / f"VIBRANT_{sample_id}_scaffolds" / f"VIBRANT_results_{sample_id}_scaffolds" / f"VIBRANT_annotations_{sample_id}_scaffolds.tsv"
        prophage_functions = parse_prophage_functions(vibrant_annotations)

        mlst_file = mlst_dir / f"{sample_id}_mlst.tsv"
        st = parse_mlst(mlst_file)

        # Count AMR on prophages
        amr_on_prophage = 0
        amr_on_other = 0

        for amr in amr_genes:
            is_prophage = any(amr['contig'].startswith(pc) for pc in prophage_contigs)

            if is_prophage:
                amr_on_prophage += 1
                colocation_detail.append({
                    'year': year,
                    'sample_id': sample_id,
                    'st': st or 'Unknown',
                    'amr_gene': amr['gene'],
                    'amr_class': amr['class'],
                    'contig': amr['contig'],
                    'location': 'prophage'
                })
            else:
                amr_on_other += 1
                colocation_detail.append({
                    'year': year,
                    'sample_id': sample_id,
                    'st': st or 'Unknown',
                    'amr_gene': amr['gene'],
                    'amr_class': amr['class'],
                    'contig': amr['contig'],
                    'location': 'non-prophage'
                })

            # AMR gene detail
            amr_gene_detail.append({
                'year': year,
                'sample_id': sample_id,
                'st': st or 'Unknown',
                'gene': amr['gene'],
                'class': amr['class'],
                'contig': amr['contig'],
                'on_prophage': 'yes' if is_prophage else 'no'
            })

        # Prophage function detail
        function_counts = Counter(prophage_functions)
        for func, count in function_counts.items():
            prophage_function_detail.append({
                'year': year,
                'sample_id': sample_id,
                'st': st or 'Unknown',
                'function': func,
                'count': count
            })

        # Sample summary
        sample_summary.append({
            'year': year,
            'sample_id': sample_id,
            'st': st or 'Unknown',
            'total_amr_genes': len(amr_genes),
            'amr_on_prophage': amr_on_prophage,
            'amr_on_other': amr_on_other,
            'pct_on_prophage': (amr_on_prophage / len(amr_genes) * 100) if len(amr_genes) > 0 else 0,
            'num_prophage_contigs': len(prophage_contigs),
            'num_prophage_functions': len(set(prophage_functions)),
            'has_integrase': 'yes' if 'Integrase/Recombinase' in prophage_functions else 'no'
        })

    # Export CSVs
    print(f"\n📊 Exporting data for {year}...")

    # 1. Sample summary
    summary_file = output_dir / f"sample_summary_{year}.csv"
    with open(summary_file, 'w', newline='') as f:
        if sample_summary:
            writer = csv.DictWriter(f, fieldnames=sample_summary[0].keys())
            writer.writeheader()
            writer.writerows(sample_summary)
    print(f"  ✅ {summary_file}")

    # 2. AMR gene detail
    amr_file = output_dir / f"amr_gene_detail_{year}.csv"
    with open(amr_file, 'w', newline='') as f:
        if amr_gene_detail:
            writer = csv.DictWriter(f, fieldnames=amr_gene_detail[0].keys())
            writer.writeheader()
            writer.writerows(amr_gene_detail)
    print(f"  ✅ {amr_file}")

    # 3. Prophage function detail
    func_file = output_dir / f"prophage_functions_{year}.csv"
    with open(func_file, 'w', newline='') as f:
        if prophage_function_detail:
            writer = csv.DictWriter(f, fieldnames=prophage_function_detail[0].keys())
            writer.writeheader()
            writer.writerows(prophage_function_detail)
    print(f"  ✅ {func_file}")

    # 4. Co-location detail
    coloc_file = output_dir / f"amr_prophage_colocation_{year}.csv"
    with open(coloc_file, 'w', newline='') as f:
        if colocation_detail:
            writer = csv.DictWriter(f, fieldnames=colocation_detail[0].keys())
            writer.writeheader()
            writer.writerows(colocation_detail)
    print(f"  ✅ {coloc_file}")

    return len(sample_summary)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export_amr_prophage_data.py <results_dir> [output_dir]")
        print("\nExample:")
        print("  python3 export_amr_prophage_data.py /homes/tylerdoe/compass_kansas_results/results_kansas_2024 ~/amr_prophage_export")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "amr_prophage_export"

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    num_samples = export_all_data(results_dir, output_dir)

    print(f"\n✅ Export complete!")
    print(f"   Samples processed: {num_samples}")
    print(f"   Output directory: {output_dir}")
    print(f"\n📁 Files created:")
    for csv_file in sorted(output_dir.glob("*.csv")):
        print(f"   - {csv_file.name}")

if __name__ == "__main__":
    main()
