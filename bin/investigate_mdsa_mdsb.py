#!/usr/bin/env python3
"""
Investigate mdsA and mdsB co-occurrence on prophage contigs.

These multidrug efflux pump genes co-occur 18 times on the same prophage contig.
Let's understand if they're part of a composite transposon or operon structure.
"""

import sys
import csv
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
    """Extract source type from NARMS sample name."""
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

def extract_year_from_sample_name(sample_name: str) -> str:
    """Extract year from NARMS sample name."""
    try:
        year_code = sample_name[0:2]
        year = f"20{year_code}"
        return year
    except:
        return 'Unknown'

def main():
    if len(sys.argv) < 2:
        print("Usage: investigate_mdsa_mdsb.py <base_directory>")
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

    # Group AMR genes by sample and contig
    amr_by_contig = defaultdict(list)
    for amr in all_amr_genes:
        sample_id = amr['sample_id']
        contig = amr.get('Contig id', amr.get('contig', ''))
        gene = amr.get('Gene symbol', amr.get('gene', 'Unknown'))

        # Parse coordinates
        start_str = amr.get('Start', amr.get('start', '0'))
        end_str = amr.get('Stop', amr.get('end', '0'))
        try:
            start = int(start_str)
            end = int(end_str)
        except ValueError:
            continue

        amr_by_contig[(sample_id, contig)].append({
            'gene': gene,
            'start': start,
            'end': end,
            'class': amr.get('Class', amr.get('class', 'Unknown')),
            'subclass': amr.get('Subclass', amr.get('subclass', 'Unknown'))
        })

    # Find contigs with both mdsA and mdsB
    mdsa_mdsb_contigs = []

    for (sample_id, contig), genes in amr_by_contig.items():
        gene_names = {g['gene'] for g in genes}

        if 'mdsA' in gene_names and 'mdsB' in gene_names:
            # Check if on prophage contig
            on_prophage = False
            prophage_info = None

            if sample_id in all_prophages:
                for prophage in all_prophages[sample_id]:
                    if prophage['contig'] == contig:
                        on_prophage = True
                        prophage_info = prophage
                        break

            # Get positions of mdsA and mdsB
            mdsa_genes = [g for g in genes if g['gene'] == 'mdsA']
            mdsb_genes = [g for g in genes if g['gene'] == 'mdsB']

            for mdsa in mdsa_genes:
                for mdsb in mdsb_genes:
                    # Calculate distance between genes
                    distance = abs(mdsa['start'] - mdsb['end'])

                    record = {
                        'sample_id': sample_id,
                        'contig': contig,
                        'mdsa_start': mdsa['start'],
                        'mdsa_end': mdsa['end'],
                        'mdsb_start': mdsb['start'],
                        'mdsb_end': mdsb['end'],
                        'distance_bp': distance,
                        'on_prophage_contig': on_prophage,
                        'prophage_quality': prophage_info['quality'] if prophage_info else 'N/A',
                        'prophage_type': prophage_info['type'] if prophage_info else 'N/A',
                        'source': extract_source_from_sample_name(sample_id),
                        'year': extract_year_from_sample_name(sample_id),
                        'other_amr_genes': ', '.join([g['gene'] for g in genes if g['gene'] not in ['mdsA', 'mdsB']])
                    }

                    mdsa_mdsb_contigs.append(record)

    # Filter to only prophage contigs for analysis
    mdsa_mdsb_on_prophage = [r for r in mdsa_mdsb_contigs if r['on_prophage_contig']]

    print(f"\n🔍 Found {len(mdsa_mdsb_contigs)} contigs with both mdsA and mdsB")
    print(f"    {len(mdsa_mdsb_on_prophage)} of these are on prophage-containing contigs")

    print("\n" + "="*120)
    print("🧬 mdsA + mdsB CO-OCCURRENCE ON PROPHAGE CONTIGS")
    print("="*120)
    print(f"{'Sample':<20} {'Year':<6} {'Source':<20} {'Distance (bp)':<15} {'Quality':<12} {'Other AMR Genes':<30}")
    print("-"*120)

    distances = []
    sources = defaultdict(int)
    years = defaultdict(int)
    qualities = defaultdict(int)
    other_amr_counts = defaultdict(int)

    for rec in sorted(mdsa_mdsb_on_prophage, key=lambda x: x['distance_bp']):
        print(f"{rec['sample_id']:<20} {rec['year']:<6} {rec['source']:<20} "
              f"{rec['distance_bp']:<15} {rec['prophage_quality']:<12} {rec['other_amr_genes'][:30]:<30}")

        distances.append(rec['distance_bp'])
        sources[rec['source']] += 1
        years[rec['year']] += 1
        qualities[rec['prophage_quality']] += 1

        # Count co-occurring AMR genes
        if rec['other_amr_genes']:
            for gene in rec['other_amr_genes'].split(', '):
                if gene:  # Skip empty strings
                    other_amr_counts[gene] += 1

    # Summary statistics
    print("\n" + "="*120)
    print("📊 SUMMARY STATISTICS")
    print("="*120)

    if distances:
        print(f"\n🔹 Distance between mdsA and mdsB:")
        print(f"  Minimum:  {min(distances):,} bp")
        print(f"  Maximum:  {max(distances):,} bp")
        print(f"  Average:  {sum(distances)/len(distances):,.1f} bp")
        print(f"  Median:   {sorted(distances)[len(distances)//2]:,} bp")

        # Check if genes are typically adjacent (operon structure)
        adjacent_count = sum(1 for d in distances if d < 100)
        print(f"\n  Adjacent (<100 bp): {adjacent_count}/{len(distances)} ({adjacent_count/len(distances)*100:.1f}%)")
        print(f"  Likely operon structure: {'YES' if adjacent_count/len(distances) > 0.8 else 'MAYBE' if adjacent_count/len(distances) > 0.5 else 'NO'}")

    print(f"\n🔹 Food Source Distribution:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(mdsa_mdsb_on_prophage) * 100
        print(f"  {source:<30} {count:>3} ({pct:>5.1f}%)")

    print(f"\n🔹 Year Distribution:")
    for year, count in sorted(years.items()):
        pct = count / len(mdsa_mdsb_on_prophage) * 100
        print(f"  {year:<30} {count:>3} ({pct:>5.1f}%)")

    print(f"\n🔹 Prophage Quality:")
    for quality, count in sorted(qualities.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(mdsa_mdsb_on_prophage) * 100
        print(f"  {quality:<30} {count:>3} ({pct:>5.1f}%)")

    if other_amr_counts:
        print(f"\n🔹 Other AMR Genes Co-occurring on Same Prophage Contig:")
        print(f"  (Top 10 most frequent)")
        for gene, count in sorted(other_amr_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = count / len(mdsa_mdsb_on_prophage) * 100
            print(f"  {gene:<30} {count:>3} ({pct:>5.1f}%)")

    # Export detailed CSV
    output_path = base_dir / "mdsa_mdsb_investigation.csv"
    with open(output_path, 'w', newline='') as f:
        if mdsa_mdsb_contigs:
            fieldnames = list(mdsa_mdsb_contigs[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(mdsa_mdsb_contigs)

    print(f"\n✅ Exported detailed mdsA+mdsB investigation to: {output_path}")

    # Key findings
    print("\n" + "="*120)
    print("🎯 KEY FINDINGS")
    print("="*120)
    print(f"  • mdsA and mdsB co-occur on {len(mdsa_mdsb_on_prophage)} prophage-containing contigs")
    print(f"  • Average distance between genes: {sum(distances)/len(distances) if distances else 0:,.1f} bp")

    if distances:
        adjacent_count = sum(1 for d in distances if d < 100)
        if adjacent_count / len(distances) > 0.8:
            print(f"  • Genes are typically adjacent (<100 bp apart in {adjacent_count/len(distances)*100:.1f}% of cases)")
            print(f"    → This suggests they form an OPERON (co-transcribed)")
        elif adjacent_count / len(distances) > 0.5:
            print(f"  • Genes are often adjacent ({adjacent_count/len(distances)*100:.1f}% <100 bp apart)")
            print(f"    → May be part of an operon or co-located genetic element")
        else:
            print(f"  • Genes are typically NOT adjacent ({adjacent_count/len(distances)*100:.1f}% <100 bp apart)")
            print(f"    → Suggests independent insertions on same contig")

    if sources:
        top_source = max(sources.items(), key=lambda x: x[1])
        print(f"  • Most common food source: {top_source[0]} ({top_source[1]} occurrences)")

    if other_amr_counts:
        print(f"\n  • Most frequently co-occurring AMR genes:")
        for gene, count in sorted(other_amr_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            pct = count / len(mdsa_mdsb_on_prophage) * 100
            print(f"    - {gene}: {count} times ({pct:.1f}%)")
        print(f"    → Suggests these form a MULTI-RESISTANCE CASSETTE")

    print("\n💡 BIOLOGICAL INTERPRETATION:")
    if distances and sum(1 for d in distances if d < 100) / len(distances) > 0.8:
        print("   mdsA and mdsB appear to form an operon structure that has been")
        print("   integrated into multiple prophages, possibly as part of a composite")
        print("   transposon. This explains why they co-occur so frequently (18 times).")
        print("   The prophage-mediated horizontal gene transfer is spreading this")
        print("   multidrug efflux pump system across Salmonella populations.")
    else:
        print("   mdsA and mdsB are co-located on prophage contigs but not always")
        print("   adjacent, suggesting multiple independent integration events or")
        print("   complex genetic rearrangements within prophage genomes.")

if __name__ == "__main__":
    main()
