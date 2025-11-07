#!/usr/bin/env python3
"""
Deep dive analysis of dfrA51 (trimethoprim resistance gene)

This gene shows 83.3% enrichment on prophage contigs (10/12 occurrences).
Let's understand WHY and HOW this gene is spreading via prophages.

Questions to answer:
1. Which specific prophage types carry dfrA51?
2. Are the prophages complete or fragmented?
3. What are the genomic contexts (nearby genes)?
4. Why are 2 occurrences NOT on prophage contigs?
5. Are there patterns by year, food source, or location?
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter

def find_year_dirs(base_path):
    """Find all year result directories."""
    base_dir = Path(base_path)

    # Check for year directories (2021, 2022, etc.)
    year_dirs = []
    for d in base_dir.iterdir():
        if d.is_dir():
            # Check if directory name contains a year
            if any(year in d.name for year in ['2021', '2022', '2023', '2024', '2025']):
                year_dirs.append(d)

    if not year_dirs:
        # Maybe the base_dir itself contains the results
        if (base_dir / 'amr_combined.tsv').exists():
            year_dirs = [base_dir]

    return sorted(year_dirs)

def load_all_amr_genes(year_dirs):
    """Load all AMR genes from all years."""
    all_genes = []

    for year_dir in year_dirs:
        amr_file = year_dir / 'amr_combined.tsv'
        if not amr_file.exists():
            print(f"  ⚠️  No AMR file in {year_dir.name}")
            continue

        print(f"  Loading AMR from {year_dir.name}...")
        with open(amr_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                row['year_dir'] = year_dir.name
                all_genes.append(row)

    return all_genes

def load_all_prophages(year_dirs):
    """Load all prophage data from all years."""
    all_prophages = defaultdict(list)

    for year_dir in year_dirs:
        vibrant_file = year_dir / 'vibrant_combined.tsv'
        if not vibrant_file.exists():
            print(f"  ⚠️  No VIBRANT file in {year_dir.name}")
            continue

        print(f"  Loading prophages from {year_dir.name}...")
        with open(vibrant_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                sample_id = row['sample_id']
                all_prophages[sample_id].append(row)

    return all_prophages

def extract_year_from_sample(sample_name):
    """Extract year from NARMS sample name (e.g., 21KS08GT06 -> 2021)."""
    try:
        year_prefix = sample_name[:2]
        year = f"20{year_prefix}"
        return year
    except:
        return 'Unknown'

def extract_source_from_sample(sample_name):
    """Extract food source from NARMS sample name."""
    try:
        source_code = sample_name[6:8]
        source_map = {
            'GT': 'Ground Turkey',
            'CB': 'Chicken Breast',
            'GB': 'Ground Beef',
            'PK': 'Pork Chop',
            'CC': 'Chicken Carcass',
            'GC': 'Ground Chicken',
            'TC': 'Turkey Carcass',
        }
        return source_map.get(source_code, f'Other ({source_code})')
    except:
        return 'Unknown'

def main():
    if len(sys.argv) < 2:
        print("Usage: deep_dive_dfra51.py <results_directory>")
        print("\nExample: deep_dive_dfra51.py ~/compass_kansas_results")
        sys.exit(1)

    base_path = sys.argv[1]

    print("="*80)
    print("🔬 DEEP DIVE: dfrA51 (Trimethoprim Resistance)")
    print("="*80)
    print(f"\nAnalyzing: {base_path}\n")

    # Find year directories
    year_dirs = find_year_dirs(base_path)
    if not year_dirs:
        print(f"❌ No year directories found in {base_path}")
        sys.exit(1)

    print(f"Found {len(year_dirs)} year directories:")
    for d in year_dirs:
        print(f"  • {d.name}")
    print()

    # Load all data
    print("📊 Loading data...")
    all_amr = load_all_amr_genes(year_dirs)
    all_prophages = load_all_prophages(year_dirs)
    print(f"✅ Loaded {len(all_amr)} AMR genes from {len(all_prophages)} samples with prophages\n")

    # Filter to dfrA51 only
    dfra51_genes = [
        amr for amr in all_amr
        if amr.get('Gene symbol', amr.get('gene', '')) == 'dfrA51'
    ]

    print("="*80)
    print(f"📌 Found {len(dfra51_genes)} dfrA51 occurrences")
    print("="*80)
    print()

    if len(dfra51_genes) == 0:
        print("No dfrA51 genes found!")
        sys.exit(0)

    # Analyze each occurrence
    on_prophage = []
    not_on_prophage = []

    for amr in dfra51_genes:
        sample_id = amr['sample_id']
        contig = amr.get('Contig id', amr.get('contig', ''))

        # Get coordinates
        try:
            amr_start = int(amr.get('Start', amr.get('start', 0)))
            amr_end = int(amr.get('Stop', amr.get('end', 0)))
        except:
            continue

        # Extract metadata
        year = extract_year_from_sample(sample_id)
        source = extract_source_from_sample(sample_id)
        organism = amr.get('organism', 'Unknown')

        # Check if on prophage contig
        prophage_info = None
        if sample_id in all_prophages:
            for prophage in all_prophages[sample_id]:
                phage_contig = prophage.get('scaffold', prophage.get('contig_id', ''))
                if phage_contig == contig:
                    prophage_info = prophage
                    break

        record = {
            'sample_id': sample_id,
            'year': year,
            'source': source,
            'organism': organism,
            'contig': contig,
            'amr_start': amr_start,
            'amr_end': amr_end,
            'year_dir': amr['year_dir']
        }

        if prophage_info:
            record['prophage_quality'] = prophage_info.get('quality', 'unknown')
            record['prophage_type'] = prophage_info.get('type', 'unknown')
            record['prophage_fragment'] = prophage_info.get('fragment', '')
            record['prophage_protein'] = prophage_info.get('protein', '')
            on_prophage.append(record)
        else:
            not_on_prophage.append(record)

    # Display results
    enrichment_pct = (len(on_prophage) / len(dfra51_genes) * 100) if dfra51_genes else 0

    print(f"🎯 ENRICHMENT: {len(on_prophage)}/{len(dfra51_genes)} ({enrichment_pct:.1f}%) on prophage contigs")
    print()

    # Detailed analysis of prophage-associated dfrA51
    if on_prophage:
        print("="*80)
        print("🦠 dfrA51 ON PROPHAGE CONTIGS")
        print("="*80)
        print()

        # Group by prophage characteristics
        quality_counts = Counter(r['prophage_quality'] for r in on_prophage)
        type_counts = Counter(r['prophage_type'] for r in on_prophage)
        year_counts = Counter(r['year'] for r in on_prophage)
        source_counts = Counter(r['source'] for r in on_prophage)

        print("📊 Prophage Quality Distribution:")
        for quality, count in quality_counts.most_common():
            pct = count / len(on_prophage) * 100
            print(f"  {quality:.<20} {count:>3} ({pct:>5.1f}%)")
        print()

        print("📊 Prophage Type Distribution:")
        for ptype, count in type_counts.most_common():
            pct = count / len(on_prophage) * 100
            print(f"  {ptype:.<20} {count:>3} ({pct:>5.1f}%)")
        print()

        print("📊 Year Distribution:")
        for year, count in sorted(year_counts.items()):
            pct = count / len(on_prophage) * 100
            print(f"  {year:.<20} {count:>3} ({pct:>5.1f}%)")
        print()

        print("📊 Food Source Distribution:")
        for source, count in source_counts.most_common():
            pct = count / len(on_prophage) * 100
            print(f"  {source:.<20} {count:>3} ({pct:>5.1f}%)")
        print()

        # Show each occurrence
        print("📋 Individual Occurrences:")
        print("-"*80)
        print(f"{'Sample':<15} {'Year':<6} {'Source':<20} {'Quality':<12} {'Type':<15}")
        print("-"*80)
        for rec in sorted(on_prophage, key=lambda x: (x['year'], x['source'])):
            print(f"{rec['sample_id']:<15} {rec['year']:<6} {rec['source']:<20} "
                  f"{rec['prophage_quality']:<12} {rec['prophage_type']:<15}")
        print()

    # Analyze non-prophage dfrA51
    if not_on_prophage:
        print("="*80)
        print("❓ dfrA51 NOT on Prophage Contigs")
        print("="*80)
        print()
        print("These are the exceptions - let's see what's different:")
        print("-"*80)
        print(f"{'Sample':<15} {'Year':<6} {'Source':<20} {'Contig':<20}")
        print("-"*80)
        for rec in not_on_prophage:
            print(f"{rec['sample_id']:<15} {rec['year']:<6} {rec['source']:<20} {rec['contig']:<20}")
        print()
        print("💡 These may be on plasmids or chromosomally integrated")
        print("   Check MOB-suite results for plasmid associations")
        print()

    # Key findings summary
    print("="*80)
    print("🔍 KEY FINDINGS")
    print("="*80)
    print()

    print(f"1. ENRICHMENT: {enrichment_pct:.1f}% of dfrA51 on prophage contigs")
    print(f"   → {len(on_prophage)} out of {len(dfra51_genes)} total occurrences")
    print()

    if on_prophage:
        most_common_quality = quality_counts.most_common(1)[0]
        print(f"2. PROPHAGE QUALITY: {most_common_quality[0]} ({most_common_quality[1]}/{len(on_prophage)})")
        print(f"   → Most dfrA51-carrying prophages are {most_common_quality[0]}")
        print()

        if len(type_counts) == 1:
            print(f"3. PROPHAGE TYPE: ALL are '{list(type_counts.keys())[0]}'")
            print(f"   → Suggests specific prophage family carries dfrA51")
        else:
            most_common_type = type_counts.most_common(1)[0]
            print(f"3. PROPHAGE TYPE: {most_common_type[0]} ({most_common_type[1]}/{len(on_prophage)})")
        print()

        if source_counts:
            top_source = source_counts.most_common(1)[0]
            print(f"4. TOP FOOD SOURCE: {top_source[0]} ({top_source[1]}/{len(on_prophage)})")
            print()

        if year_counts:
            peak_year = max(year_counts.items(), key=lambda x: x[1])
            print(f"5. PEAK YEAR: {peak_year[0]} ({peak_year[1]} occurrences)")
            print()

    print("💡 BIOLOGICAL INTERPRETATION:")
    print("-"*80)
    if enrichment_pct > 75:
        print("The 83% enrichment strongly suggests that dfrA51 is primarily")
        print("spreading through prophage-mediated horizontal gene transfer.")
        print("This is likely a temperate phage that has integrated dfrA51")
        print("and is transmitting it across Salmonella populations.")
    print()

    if not_on_prophage:
        print(f"The {len(not_on_prophage)} exception(s) may represent:")
        print("  • Chromosomally integrated dfrA51 (ancient integration)")
        print("  • Plasmid-borne dfrA51 (different mobile element)")
        print("  • Prophage integration site we didn't detect")

    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print("="*80)

if __name__ == "__main__":
    main()
