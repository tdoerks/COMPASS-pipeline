#!/usr/bin/env python3
"""
Temporal and Source Stratification Analysis
Analyzes how AMR-prophage associations change over:
- Time (year-by-year trends)
- Isolation source (clinical, environmental, food, etc.)
- State/geographic location
"""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import csv

def parse_metadata(metadata_file):
    """Parse full metadata from filtered_samples.csv"""
    metadata = {}

    if not Path(metadata_file).exists():
        return metadata

    with open(metadata_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row['Run']
            metadata[sample_id] = {
                'organism': row.get('Organism', 'Unknown'),
                'year': row.get('Collection_Date', '')[:4] if row.get('Collection_Date') else 'Unknown',
                'source': row.get('Isolation_source', 'Unknown'),
                'state': row.get('geo_loc_name_state_province', 'Unknown'),
                'bioproject': row.get('BioProject', '')
            }

    return metadata

def parse_amr_by_contig(amr_file):
    """Extract AMR genes grouped by contig"""
    contig_amr = defaultdict(list)

    if not Path(amr_file).exists():
        return contig_amr

    with open(amr_file) as f:
        header = next(f, None)
        if not header:
            return contig_amr

        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 11:
                contig = parts[1]
                element_type = parts[8]
                gene_symbol = parts[5]
                gene_class = parts[10]

                if element_type == 'AMR' and gene_symbol != 'NA':
                    contig_amr[contig].append({
                        'gene': gene_symbol,
                        'class': gene_class
                    })

    return contig_amr

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

def categorize_source(source_text):
    """Categorize isolation source into broad categories"""
    source_lower = source_text.lower()

    if any(term in source_lower for term in ['clinical', 'patient', 'blood', 'urine', 'fecal', 'feces', 'stool']):
        return 'Clinical'
    elif any(term in source_lower for term in ['food', 'meat', 'poultry', 'beef', 'pork', 'chicken', 'turkey']):
        return 'Food'
    elif any(term in source_lower for term in ['environment', 'water', 'soil', 'sediment']):
        return 'Environmental'
    elif any(term in source_lower for term in ['animal', 'livestock', 'cattle', 'swine', 'farm']):
        return 'Animal'
    else:
        return 'Other'

def analyze_stratified(results_dir):
    """Analyze with temporal and source stratification"""
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"
    metadata_file = results_dir / "filtered_samples" / "filtered_samples.csv"

    # Get metadata
    sample_metadata = parse_metadata(metadata_file)

    # Stratified data structures
    temporal_data = defaultdict(lambda: {
        'samples': 0,
        'samples_with_amr': 0,
        'samples_with_prophage': 0,
        'samples_with_colocation': 0,
        'total_amr': 0,
        'amr_on_prophage': 0,
        'top_genes': Counter(),
        'top_genes_on_prophage': Counter()
    })

    source_data = defaultdict(lambda: {
        'samples': 0,
        'samples_with_amr': 0,
        'samples_with_prophage': 0,
        'samples_with_colocation': 0,
        'total_amr': 0,
        'amr_on_prophage': 0,
        'top_genes': Counter(),
        'top_genes_on_prophage': Counter()
    })

    state_data = defaultdict(lambda: {
        'samples': 0,
        'samples_with_colocation': 0,
        'amr_on_prophage': 0
    })

    organism_temporal = defaultdict(lambda: defaultdict(lambda: {
        'samples': 0,
        'amr_on_prophage': 0,
        'total_amr': 0
    }))

    # Process all samples
    for amr_file in sorted(amr_dir.glob("*_amr.tsv")):
        sample_id = amr_file.stem.replace('_amr', '')

        # Get metadata
        meta = sample_metadata.get(sample_id, {})
        year = meta.get('year', 'Unknown')
        source_raw = meta.get('source', 'Unknown')
        state = meta.get('state', 'Unknown')
        organism = meta.get('organism', 'Unknown')

        if year == 'Unknown' or year == '':
            continue

        source_category = categorize_source(source_raw)

        # Parse data
        contig_amr = parse_amr_by_contig(amr_file)
        vibrant_phages_file = vibrant_dir / f"{sample_id}_phages.fna"
        prophage_contigs = parse_prophage_contigs(vibrant_phages_file)

        # Update counts
        temporal_data[year]['samples'] += 1
        source_data[source_category]['samples'] += 1
        state_data[state]['samples'] += 1
        organism_temporal[organism][year]['samples'] += 1

        has_prophage = len(prophage_contigs) > 0
        has_amr = len(contig_amr) > 0
        has_colocation = False

        if has_prophage:
            temporal_data[year]['samples_with_prophage'] += 1
            source_data[source_category]['samples_with_prophage'] += 1

        # Track AMR
        for contig, amr_genes in contig_amr.items():
            is_prophage = any(contig.startswith(pc) for pc in prophage_contigs)

            for amr in amr_genes:
                temporal_data[year]['total_amr'] += 1
                source_data[source_category]['total_amr'] += 1
                temporal_data[year]['top_genes'][amr['gene']] += 1
                source_data[source_category]['top_genes'][amr['gene']] += 1
                organism_temporal[organism][year]['total_amr'] += 1

                if is_prophage:
                    has_colocation = True
                    temporal_data[year]['amr_on_prophage'] += 1
                    source_data[source_category]['amr_on_prophage'] += 1
                    state_data[state]['amr_on_prophage'] += 1
                    temporal_data[year]['top_genes_on_prophage'][amr['gene']] += 1
                    source_data[source_category]['top_genes_on_prophage'][amr['gene']] += 1
                    organism_temporal[organism][year]['amr_on_prophage'] += 1

        if has_amr:
            temporal_data[year]['samples_with_amr'] += 1
            source_data[source_category]['samples_with_amr'] += 1

        if has_colocation:
            temporal_data[year]['samples_with_colocation'] += 1
            source_data[source_category]['samples_with_colocation'] += 1
            state_data[state]['samples_with_colocation'] += 1

    return temporal_data, source_data, state_data, organism_temporal

def print_analysis(temporal_data, source_data, state_data, organism_temporal, results_dir):
    """Print comprehensive stratified analysis"""

    print("\n" + "="*85)
    print("Temporal and Source Stratification Analysis")
    print("AMR-Prophage Associations Over Time and Across Sources")
    print(f"Results: {results_dir}")
    print("="*85)

    # Temporal trends
    print(f"\n📅 Year-by-Year Trends:")
    print(f"  {'Year':<8} {'Samples':<10} {'w/AMR':<10} {'w/Prophage':<12} {'AMR Total':<12} "
          f"{'On Prophage':<15} {'% on Prophage'}")
    print("  " + "-"*85)

    for year in sorted(temporal_data.keys()):
        data = temporal_data[year]
        pct = (data['amr_on_prophage'] / data['total_amr'] * 100) if data['total_amr'] > 0 else 0

        print(f"  {year:<8} {data['samples']:<10} {data['samples_with_amr']:<10} "
              f"{data['samples_with_prophage']:<12} {data['total_amr']:<12} "
              f"{data['amr_on_prophage']:<15} {pct:.1f}%")

    # Temporal trend analysis
    years_sorted = sorted(temporal_data.keys())
    if len(years_sorted) >= 2:
        first_year = years_sorted[0]
        last_year = years_sorted[-1]
        first_pct = (temporal_data[first_year]['amr_on_prophage'] / temporal_data[first_year]['total_amr'] * 100) \
            if temporal_data[first_year]['total_amr'] > 0 else 0
        last_pct = (temporal_data[last_year]['amr_on_prophage'] / temporal_data[last_year]['total_amr'] * 100) \
            if temporal_data[last_year]['total_amr'] > 0 else 0

        print(f"\n  📈 Trend: {first_year} ({first_pct:.1f}%) → {last_year} ({last_pct:.1f}%)")
        if last_pct > first_pct:
            print(f"     ⬆️  INCREASING prophage-AMR association (+{last_pct - first_pct:.1f} percentage points)")
        elif last_pct < first_pct:
            print(f"     ⬇️  DECREASING prophage-AMR association ({last_pct - first_pct:.1f} percentage points)")
        else:
            print(f"     ➡️  STABLE prophage-AMR association")

    # Source stratification
    print(f"\n🏥 Source Stratification:")
    print(f"  {'Source':<20} {'Samples':<10} {'w/AMR':<10} {'AMR Total':<12} "
          f"{'On Prophage':<15} {'% on Prophage'}")
    print("  " + "-"*80)

    for source in sorted(source_data.keys()):
        data = source_data[source]
        pct = (data['amr_on_prophage'] / data['total_amr'] * 100) if data['total_amr'] > 0 else 0

        print(f"  {source:<20} {data['samples']:<10} {data['samples_with_amr']:<10} "
              f"{data['total_amr']:<12} {data['amr_on_prophage']:<15} {pct:.1f}%")

    # Organism-specific temporal trends
    print(f"\n🦠 Organism-Specific Temporal Trends:")

    for organism in sorted(organism_temporal.keys()):
        org_data = organism_temporal[organism]
        print(f"\n  {organism}:")
        print(f"    {'Year':<8} {'Samples':<10} {'Total AMR':<12} {'On Prophage':<15} {'% on Prophage'}")
        print("    " + "-"*65)

        for year in sorted(org_data.keys()):
            data = org_data[year]
            pct = (data['amr_on_prophage'] / data['total_amr'] * 100) if data['total_amr'] > 0 else 0

            print(f"    {year:<8} {data['samples']:<10} {data['total_amr']:<12} "
                  f"{data['amr_on_prophage']:<15} {pct:.1f}%")

    # Geographic distribution
    print(f"\n🗺️  Geographic Distribution (Top 15 States):")
    print(f"  {'State':<20} {'Samples':<10} {'w/Co-location':<18} {'% with Co-location'}")
    print("  " + "-"*70)

    state_sorted = sorted(state_data.items(),
                         key=lambda x: x[1]['samples'],
                         reverse=True)

    for state, data in state_sorted[:15]:
        pct = (data['samples_with_colocation'] / data['samples'] * 100) if data['samples'] > 0 else 0
        print(f"  {state:<20} {data['samples']:<10} {data['samples_with_colocation']:<18} {pct:.1f}%")

    # Top genes by year
    print(f"\n🧬 Trending AMR Genes Over Time:")

    # Find genes that increased over time
    gene_trends = defaultdict(list)
    for year in sorted(temporal_data.keys()):
        for gene, count in temporal_data[year]['top_genes_on_prophage'].most_common(5):
            total_gene_count = temporal_data[year]['top_genes'][gene]
            pct = (count / total_gene_count * 100) if total_gene_count > 0 else 0
            gene_trends[gene].append((year, count, pct))

    print(f"\n  Top 10 AMR Genes on Prophages (most recent year):")
    if years_sorted:
        latest_year = years_sorted[-1]
        print(f"    {'Gene':<25} {'Count':<10} {'% on Prophage'}")
        print("    " + "-"*50)

        for gene, count in temporal_data[latest_year]['top_genes_on_prophage'].most_common(10):
            total = temporal_data[latest_year]['top_genes'][gene]
            pct = (count / total * 100) if total > 0 else 0
            print(f"    {gene:<25} {count:<10} {pct:.1f}%")

    # Source-specific genes
    print(f"\n💊 Top AMR Genes by Source:")

    for source in sorted(source_data.keys()):
        if source_data[source]['samples'] < 5:  # Skip sources with few samples
            continue

        print(f"\n  {source} (Top 5 genes on prophages):")
        print(f"    {'Gene':<25} {'Count':<10} {'% on Prophage'}")
        print("    " + "-"*50)

        for gene, count in source_data[source]['top_genes_on_prophage'].most_common(5):
            total = source_data[source]['top_genes'][gene]
            pct = (count / total * 100) if total > 0 else 0
            print(f"    {gene:<25} {count:<10} {pct:.1f}%")

    # Key findings
    print(f"\n💡 Key Findings:")

    # Which source has highest prophage-AMR rate?
    max_source = None
    max_source_pct = 0
    for source, data in source_data.items():
        if data['total_amr'] > 0:
            pct = data['amr_on_prophage'] / data['total_amr'] * 100
            if pct > max_source_pct:
                max_source_pct = pct
                max_source = source

    if max_source:
        print(f"  • {max_source} samples have highest prophage-AMR rate: {max_source_pct:.1f}%")

    # Which year had most samples?
    if temporal_data:
        max_year = max(temporal_data.items(), key=lambda x: x[1]['samples'])
        print(f"  • {max_year[0]} had the most samples analyzed: {max_year[1]['samples']}")

    # Overall trend direction
    if len(years_sorted) >= 3:
        early_years = years_sorted[:len(years_sorted)//2]
        late_years = years_sorted[len(years_sorted)//2:]

        early_avg_pct = sum(
            (temporal_data[y]['amr_on_prophage'] / temporal_data[y]['total_amr'] * 100)
            if temporal_data[y]['total_amr'] > 0 else 0
            for y in early_years
        ) / len(early_years)

        late_avg_pct = sum(
            (temporal_data[y]['amr_on_prophage'] / temporal_data[y]['total_amr'] * 100)
            if temporal_data[y]['total_amr'] > 0 else 0
            for y in late_years
        ) / len(late_years)

        print(f"  • Early period avg: {early_avg_pct:.1f}% → Late period avg: {late_avg_pct:.1f}%")

def main():
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    else:
        results_dir = Path("/homes/tylerdoe/compass_kansas_results/results_kansas_2024")

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    print(f"📊 Analyzing temporal and source stratification...")

    temporal_data, source_data, state_data, organism_temporal = analyze_stratified(results_dir)

    if not temporal_data:
        print("❌ No data found!")
        sys.exit(1)

    print_analysis(temporal_data, source_data, state_data, organism_temporal, results_dir)

    print("\n" + "="*85)
    print("✅ Analysis complete!")
    print("="*85 + "\n")

if __name__ == "__main__":
    main()
