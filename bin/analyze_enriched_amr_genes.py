#!/usr/bin/env python3
"""
Analyze AMR genes that show significant enrichment on prophage-containing contigs.
Focus on genes with high % on prophage contigs vs background rate.
"""

import sys
import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

def load_amr_data(amr_path: Path) -> List[Dict]:
    """Load AMR data from combined results."""
    amr_genes = []
    with open(amr_path) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            amr_genes.append(row)
    return amr_genes

def load_prophage_data(vibrant_path: Path) -> Dict[str, List[Dict]]:
    """Load prophage data from VIBRANT results."""
    prophages_by_sample = defaultdict(list)

    with open(vibrant_path) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            sample_id = row['sample_id']
            contig_id = row.get('scaffold', row.get('contig_id', ''))

            # Parse coordinates
            fragment = row.get('fragment', '')
            if '_' in fragment:
                parts = fragment.split('_')
                if len(parts) >= 3:
                    try:
                        start = int(parts[1])
                        end = int(parts[2])
                    except ValueError:
                        continue
                else:
                    continue
            else:
                continue

            prophages_by_sample[sample_id].append({
                'contig': contig_id,
                'start': start,
                'end': end,
                'quality': row.get('quality', 'unknown'),
                'type': row.get('type', 'unknown')
            })

    return prophages_by_sample

def extract_source_from_sample_name(sample_name: str) -> str:
    """Extract source type from NARMS sample name (e.g., 25KS08GT06)."""
    try:
        source_code = sample_name[6:8]
        source_map = {
            'GT': 'Ground Turkey',
            'CB': 'Chicken Breast',
            'GB': 'Ground Beef',
            'PK': 'Pork',
            'CC': 'Chicken Carcass',
            'GC': 'Ground Chicken',
            'TC': 'Turkey Carcass',
            'CH': 'Chicken',
            'TK': 'Turkey',
            'BF': 'Beef',
            'SW': 'Swine',
        }
        return source_map.get(source_code.upper(), f'Other ({source_code})')
    except:
        return 'Unknown'

def calculate_enrichment(
    amr_genes: List[Dict],
    prophages_by_sample: Dict[str, List[Dict]]
) -> Tuple[Dict, Dict, Dict]:
    """
    Calculate enrichment statistics for each AMR gene.
    Returns: gene_stats, class_stats, detailed_records
    """

    gene_stats = defaultdict(lambda: {
        'total': 0,
        'on_prophage_contig': 0,
        'samples': set(),
        'samples_on_prophage': set(),
        'sources': defaultdict(int),
        'sources_on_prophage': defaultdict(int),
        'organisms': defaultdict(int),
        'organisms_on_prophage': defaultdict(int)
    })

    class_stats = defaultdict(lambda: {
        'total': 0,
        'on_prophage_contig': 0
    })

    detailed_records = []

    for amr in amr_genes:
        sample_id = amr['sample_id']
        gene_symbol = amr.get('Gene symbol', amr.get('gene', 'Unknown'))
        drug_class = amr.get('Class', amr.get('class', 'Unknown'))
        contig = amr.get('Contig id', amr.get('contig', ''))
        organism = amr.get('organism', 'Unknown')
        source = extract_source_from_sample_name(sample_id)

        # Parse AMR coordinates
        start_str = amr.get('Start', amr.get('start', '0'))
        end_str = amr.get('Stop', amr.get('end', '0'))
        try:
            amr_start = int(start_str)
            amr_end = int(end_str)
        except ValueError:
            continue

        # Update total counts
        gene_stats[gene_symbol]['total'] += 1
        gene_stats[gene_symbol]['samples'].add(sample_id)
        gene_stats[gene_symbol]['sources'][source] += 1
        gene_stats[gene_symbol]['organisms'][organism] += 1

        class_stats[drug_class]['total'] += 1

        # Check if on prophage contig
        on_prophage_contig = False
        prophage_quality = None
        prophage_type = None

        if sample_id in prophages_by_sample:
            for prophage in prophages_by_sample[sample_id]:
                if prophage['contig'] == contig:
                    on_prophage_contig = True
                    prophage_quality = prophage['quality']
                    prophage_type = prophage['type']
                    break

        if on_prophage_contig:
            gene_stats[gene_symbol]['on_prophage_contig'] += 1
            gene_stats[gene_symbol]['samples_on_prophage'].add(sample_id)
            gene_stats[gene_symbol]['sources_on_prophage'][source] += 1
            gene_stats[gene_symbol]['organisms_on_prophage'][organism] += 1

            class_stats[drug_class]['on_prophage_contig'] += 1

            detailed_records.append({
                'sample_id': sample_id,
                'gene': gene_symbol,
                'class': drug_class,
                'contig': contig,
                'amr_start': amr_start,
                'amr_end': amr_end,
                'organism': organism,
                'source': source,
                'prophage_quality': prophage_quality,
                'prophage_type': prophage_type
            })

    return gene_stats, class_stats, detailed_records

def analyze_enrichment(gene_stats: Dict, min_occurrences: int = 10) -> List[Dict]:
    """
    Analyze enrichment and return sorted list of genes.
    Filter to genes with at least min_occurrences total.
    """
    enrichment_results = []

    for gene, stats in gene_stats.items():
        total = stats['total']
        on_prophage = stats['on_prophage_contig']

        if total < min_occurrences:
            continue

        pct_on_prophage = (on_prophage / total * 100) if total > 0 else 0

        enrichment_results.append({
            'gene': gene,
            'total_occurrences': total,
            'on_prophage_contig': on_prophage,
            'pct_on_prophage': pct_on_prophage,
            'num_samples': len(stats['samples']),
            'num_samples_on_prophage': len(stats['samples_on_prophage']),
            'top_source': max(stats['sources'].items(), key=lambda x: x[1])[0] if stats['sources'] else 'Unknown',
            'top_source_on_prophage': max(stats['sources_on_prophage'].items(), key=lambda x: x[1])[0] if stats['sources_on_prophage'] else 'None',
            'top_organism': max(stats['organisms'].items(), key=lambda x: x[1])[0] if stats['organisms'] else 'Unknown',
            'top_organism_on_prophage': max(stats['organisms_on_prophage'].items(), key=lambda x: x[1])[0] if stats['organisms_on_prophage'] else 'None'
        })

    # Sort by % on prophage (descending)
    enrichment_results.sort(key=lambda x: x['pct_on_prophage'], reverse=True)

    return enrichment_results

def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_enriched_amr_genes.py <base_directory>")
        print("  base_directory should contain amr_combined.tsv and vibrant_combined.tsv")
        print("  OR provide path to parent directory containing multiple year directories")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    # Check if this is a multi-year directory structure
    year_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.isdigit() and len(d.name) == 4]

    all_amr_genes = []
    all_prophages = defaultdict(list)

    if year_dirs:
        print(f"📅 Detected multi-year directory structure with {len(year_dirs)} year directories")
        for year_dir in sorted(year_dirs):
            amr_path = year_dir / "amr_combined.tsv"
            vibrant_path = year_dir / "vibrant_combined.tsv"

            if amr_path.exists() and vibrant_path.exists():
                print(f"  Loading {year_dir.name}...")
                year_amr = load_amr_data(amr_path)
                year_prophages = load_prophage_data(vibrant_path)

                all_amr_genes.extend(year_amr)
                for sample_id, prophages in year_prophages.items():
                    all_prophages[sample_id].extend(prophages)
    else:
        # Single directory mode
        amr_path = base_dir / "amr_combined.tsv"
        vibrant_path = base_dir / "vibrant_combined.tsv"

        if not amr_path.exists() or not vibrant_path.exists():
            print(f"❌ Error: Could not find amr_combined.tsv or vibrant_combined.tsv in {base_dir}")
            sys.exit(1)

        print(f"📁 Loading data from {base_dir}")
        all_amr_genes = load_amr_data(amr_path)
        all_prophages = load_prophage_data(vibrant_path)

    print(f"✅ Loaded {len(all_amr_genes)} AMR genes from {len(all_prophages)} samples with prophages")

    # Calculate enrichment
    print("\n🔬 Calculating enrichment statistics...")
    gene_stats, class_stats, detailed_records = calculate_enrichment(all_amr_genes, all_prophages)

    # Analyze enrichment (genes with ≥10 occurrences)
    enrichment_results = analyze_enrichment(gene_stats, min_occurrences=10)

    # Print top enriched genes
    print("\n" + "="*100)
    print("🧬 TOP AMR GENES ENRICHED ON PROPHAGE-CONTAINING CONTIGS (≥10 total occurrences)")
    print("="*100)
    print(f"{'Gene':<20} {'Total':<8} {'On Phage':<10} {'% On Phage':<12} {'Samples':<10} {'Top Source':<20} {'Top Organism':<20}")
    print("-"*100)

    for result in enrichment_results[:30]:  # Top 30
        print(f"{result['gene']:<20} {result['total_occurrences']:<8} {result['on_prophage_contig']:<10} "
              f"{result['pct_on_prophage']:<12.1f} {result['num_samples']:<10} "
              f"{result['top_source']:<20} {result['top_organism']:<20}")

    # Drug class enrichment
    class_enrichment = []
    for drug_class, stats in class_stats.items():
        if stats['total'] >= 10:
            pct = (stats['on_prophage_contig'] / stats['total'] * 100) if stats['total'] > 0 else 0
            class_enrichment.append({
                'class': drug_class,
                'total': stats['total'],
                'on_prophage': stats['on_prophage_contig'],
                'pct': pct
            })

    class_enrichment.sort(key=lambda x: x['pct'], reverse=True)

    print("\n" + "="*100)
    print("💊 DRUG CLASS ENRICHMENT ON PROPHAGE-CONTAINING CONTIGS (≥10 total occurrences)")
    print("="*100)
    print(f"{'Drug Class':<30} {'Total':<8} {'On Phage':<10} {'% On Phage':<12}")
    print("-"*100)

    for result in class_enrichment[:20]:  # Top 20
        print(f"{result['class']:<30} {result['total']:<8} {result['on_prophage']:<10} {result['pct']:<12.1f}")

    # Export detailed enrichment CSV
    output_path = base_dir / "amr_enrichment_analysis.csv"
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['gene', 'total_occurrences', 'on_prophage_contig', 'pct_on_prophage',
                     'num_samples', 'num_samples_on_prophage', 'top_source',
                     'top_source_on_prophage', 'top_organism', 'top_organism_on_prophage']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enrichment_results)

    print(f"\n✅ Exported detailed enrichment analysis to: {output_path}")

    # Export individual occurrences of highly enriched genes
    highly_enriched = [r for r in enrichment_results if r['pct_on_prophage'] > 30 and r['total_occurrences'] >= 10]

    if highly_enriched:
        print(f"\n🎯 Found {len(highly_enriched)} highly enriched genes (>30% on prophage contigs, ≥10 occurrences)")

        enriched_genes = {r['gene'] for r in highly_enriched}
        enriched_records = [r for r in detailed_records if r['gene'] in enriched_genes]

        output_path = base_dir / "highly_enriched_amr_occurrences.csv"
        with open(output_path, 'w', newline='') as f:
            if enriched_records:
                fieldnames = list(enriched_records[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(enriched_records)

        print(f"✅ Exported {len(enriched_records)} individual occurrences to: {output_path}")

        # Print highly enriched genes
        print("\n" + "="*100)
        print("🔥 HIGHLY ENRICHED AMR GENES (>30% on prophage contigs)")
        print("="*100)
        for result in highly_enriched:
            print(f"  {result['gene']}: {result['pct_on_prophage']:.1f}% ({result['on_prophage_contig']}/{result['total_occurrences']})")

if __name__ == "__main__":
    main()
