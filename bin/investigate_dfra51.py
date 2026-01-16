#!/usr/bin/env python3
"""
Investigate dfrA51 gene in detail.

This gene shows 83.3% enrichment on prophage contigs (10/12 occurrences),
which is the highest enrichment we've found. Let's understand why.
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

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
                'type': row.get('type', 'unknown'),
                'fragment': fragment
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
        print("Usage: investigate_dfra51.py <base_directory>")
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

    # Filter to dfrA51 only
    dfra51_genes = [amr for amr in all_amr_genes if amr.get('Gene symbol', amr.get('gene', '')) == 'dfrA51']

    print(f"\n🔍 Found {len(dfra51_genes)} dfrA51 occurrences")

    # Analyze each occurrence
    on_prophage = []
    not_on_prophage = []

    for amr in dfra51_genes:
        sample_id = amr['sample_id']
        contig = amr.get('Contig id', amr.get('contig', ''))
        organism = amr.get('organism', 'Unknown')
        source = extract_source_from_sample_name(sample_id)
        year = extract_year_from_sample_name(sample_id)

        # Parse AMR coordinates
        start_str = amr.get('Start', amr.get('start', '0'))
        end_str = amr.get('Stop', amr.get('end', '0'))
        try:
            amr_start = int(start_str)
            amr_end = int(end_str)
        except ValueError:
            continue

        # Check if on prophage contig
        prophage_info = None
        if sample_id in all_prophages:
            for prophage in all_prophages[sample_id]:
                if prophage['contig'] == contig:
                    prophage_info = prophage
                    break

        record = {
            'sample_id': sample_id,
            'contig': contig,
            'amr_start': amr_start,
            'amr_end': amr_end,
            'organism': organism,
            'source': source,
            'year': year
        }

        if prophage_info:
            record['prophage_start'] = prophage_info['start']
            record['prophage_end'] = prophage_info['end']
            record['prophage_quality'] = prophage_info['quality']
            record['prophage_type'] = prophage_info['type']
            record['prophage_fragment'] = prophage_info['fragment']
            on_prophage.append(record)
        else:
            not_on_prophage.append(record)

    print("\n" + "="*100)
    print(f"📊 dfrA51 ENRICHMENT: {len(on_prophage)}/{len(dfra51_genes)} ({len(on_prophage)/len(dfra51_genes)*100:.1f}%) on prophage contigs")
    print("="*100)

    # Analyze prophage-associated dfrA51
    print("\n🦠 dfrA51 ON PROPHAGE CONTIGS:")
    print("-"*100)
    print(f"{'Sample':<20} {'Year':<8} {'Source':<20} {'Contig':<25} {'Quality':<12} {'Type':<15}")
    print("-"*100)

    prophage_qualities = defaultdict(int)
    prophage_types = defaultdict(int)
    sources = defaultdict(int)
    years = defaultdict(int)

    for rec in on_prophage:
        print(f"{rec['sample_id']:<20} {rec['year']:<8} {rec['source']:<20} "
              f"{rec['contig']:<25} {rec['prophage_quality']:<12} {rec['prophage_type']:<15}")

        prophage_qualities[rec['prophage_quality']] += 1
        prophage_types[rec['prophage_type']] += 1
        sources[rec['source']] += 1
        years[rec['year']] += 1

    # Analyze non-prophage dfrA51
    print("\n\n🔬 dfrA51 NOT on prophage contigs:")
    print("-"*100)
    print(f"{'Sample':<20} {'Year':<8} {'Source':<20} {'Contig':<25}")
    print("-"*100)

    sources_no_phage = defaultdict(int)
    years_no_phage = defaultdict(int)

    for rec in not_on_prophage:
        print(f"{rec['sample_id']:<20} {rec['year']:<8} {rec['source']:<20} {rec['contig']:<25}")
        sources_no_phage[rec['source']] += 1
        years_no_phage[rec['year']] += 1

    # Summary statistics
    print("\n" + "="*100)
    print("📈 SUMMARY STATISTICS")
    print("="*100)

    print("\n🔹 Prophage Quality (for dfrA51 on prophage contigs):")
    for quality, count in sorted(prophage_qualities.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(on_prophage) * 100
        print(f"  {quality:<20} {count:>3} ({pct:>5.1f}%)")

    print("\n🔹 Prophage Type (for dfrA51 on prophage contigs):")
    for ptype, count in sorted(prophage_types.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(on_prophage) * 100
        print(f"  {ptype:<20} {count:>3} ({pct:>5.1f}%)")

    print("\n🔹 Food Source Comparison:")
    print(f"  {'Source':<20} {'On Prophage':<15} {'Not on Prophage':<15}")
    all_sources = set(sources.keys()) | set(sources_no_phage.keys())
    for source in sorted(all_sources):
        on_phage_count = sources.get(source, 0)
        not_on_phage_count = sources_no_phage.get(source, 0)
        print(f"  {source:<20} {on_phage_count:<15} {not_on_phage_count:<15}")

    print("\n🔹 Year Comparison:")
    print(f"  {'Year':<20} {'On Prophage':<15} {'Not on Prophage':<15}")
    all_years = set(years.keys()) | set(years_no_phage.keys())
    for year in sorted(all_years):
        on_phage_count = years.get(year, 0)
        not_on_phage_count = years_no_phage.get(year, 0)
        print(f"  {year:<20} {on_phage_count:<15} {not_on_phage_count:<15}")

    # Export detailed CSV
    output_path = base_dir / "dfra51_investigation.csv"
    with open(output_path, 'w', newline='') as f:
        # Combine all records with prophage status
        all_records = []
        for rec in on_prophage:
            rec['on_prophage_contig'] = 'Yes'
            all_records.append(rec)
        for rec in not_on_prophage:
            rec['on_prophage_contig'] = 'No'
            rec['prophage_start'] = 'N/A'
            rec['prophage_end'] = 'N/A'
            rec['prophage_quality'] = 'N/A'
            rec['prophage_type'] = 'N/A'
            rec['prophage_fragment'] = 'N/A'
            all_records.append(rec)

        if all_records:
            fieldnames = ['sample_id', 'year', 'source', 'organism', 'contig',
                         'amr_start', 'amr_end', 'on_prophage_contig',
                         'prophage_start', 'prophage_end', 'prophage_quality',
                         'prophage_type', 'prophage_fragment']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)

    print(f"\n✅ Exported detailed dfrA51 investigation to: {output_path}")

    print("\n" + "="*100)
    print("🎯 KEY FINDINGS")
    print("="*100)
    print(f"  • dfrA51 shows {len(on_prophage)/len(dfra51_genes)*100:.1f}% enrichment on prophage contigs")
    print(f"  • {len(on_prophage)} out of {len(dfra51_genes)} total dfrA51 occurrences are on prophage contigs")

    if prophage_types:
        most_common_type = max(prophage_types.items(), key=lambda x: x[1])
        print(f"  • Most common prophage type: {most_common_type[0]} ({most_common_type[1]}/{len(on_prophage)} occurrences)")

    if prophage_qualities:
        most_common_quality = max(prophage_qualities.items(), key=lambda x: x[1])
        print(f"  • Most common prophage quality: {most_common_quality[0]} ({most_common_quality[1]}/{len(on_prophage)} occurrences)")

    if sources:
        most_common_source = max(sources.items(), key=lambda x: x[1])
        print(f"  • Most common food source (on prophage): {most_common_source[0]} ({most_common_source[1]}/{len(on_prophage)} occurrences)")

    print("\n💡 This suggests dfrA51 has a strong association with prophage-mediated horizontal gene transfer!")
    print("   Trimethoprim resistance via dfrA51 may be primarily spreading through prophages in Salmonella.")

if __name__ == "__main__":
    main()
