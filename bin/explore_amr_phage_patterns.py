#!/usr/bin/env python3
"""
Exploratory AMR-Phage Pattern Analysis

This script performs broad exploratory analysis to find potential associations
between AMR genes and phages, even when they're not physically co-located:

1. Sample-level co-occurrence patterns
   - Which AMR genes tend to appear in samples with prophages?
   - Which AMR classes are enriched in prophage-positive samples?

2. Contig-level associations
   - Do certain contigs carry both AMR and phages?
   - Are there specific contig size/coverage patterns?

3. Gene family clustering
   - Do samples with specific phage types have specific AMR profiles?
   - Are there AMR-phage "signatures" in subsets of samples?

4. Temporal/spatial patterns
   - Are AMR-phage associations changing over time?
   - Do certain organisms show different patterns?

5. Network analysis
   - Which AMR genes co-occur most frequently with prophage presence?
   - Are there AMR gene clusters associated with phage carriage?
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
import json

# ============================================================================
# DATA LOADING
# ============================================================================

def load_amr_data(results_dir):
    """
    Load all AMR data from AMRFinder results

    Returns: dict[sample_id] -> list of AMR gene dicts
    """
    amr_dir = Path(results_dir) / "amrfinder"
    amr_data = {}

    for amr_file in amr_dir.glob("*_amr.tsv"):
        sample_id = amr_file.stem.replace('_amr', '')
        genes = []

        with open(amr_file) as f:
            header = next(f, None)
            if not header:
                continue

            for line in f:
                if line.startswith('#'):
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 11:
                    continue

                element_type = parts[8]
                if element_type != 'AMR':
                    continue

                genes.append({
                    'contig': parts[1],
                    'gene': parts[5],
                    'class': parts[10],
                    'subclass': parts[11] if len(parts) > 11 else ''
                })

        if genes:
            amr_data[sample_id] = genes

    return amr_data


def load_vibrant_data(results_dir):
    """
    Load prophage presence/absence from VIBRANT

    Returns: dict[sample_id] -> list of prophage dicts
    """
    vibrant_dir = Path(results_dir) / "vibrant"
    vibrant_data = {}

    for sample_dir in vibrant_dir.glob("*_vibrant"):
        sample_id = sample_dir.name.replace('_vibrant', '')

        # Check for phage sequences (simple presence/absence)
        phage_fasta = vibrant_dir / f"{sample_id}_phages.fna"

        prophages = []
        if phage_fasta.exists():
            with open(phage_fasta) as f:
                for line in f:
                    if line.startswith('>'):
                        # Parse header for contig info
                        header = line.strip()[1:].split()[0]
                        # Extract contig name (remove fragment suffix)
                        contig_parts = header.split('_')
                        try:
                            fragment_idx = contig_parts.index('fragment')
                            contig = '_'.join(contig_parts[:fragment_idx])
                        except ValueError:
                            contig = header

                        prophages.append({
                            'id': header,
                            'contig': contig
                        })

        if prophages:
            vibrant_data[sample_id] = prophages

    return vibrant_data


def extract_source_from_sample_name(sample_name):
    """
    Extract source type from NARMS sample name format

    Format: YYKSXXTTNN where:
    - YY = year
    - KS = state
    - XX = sample number
    - TT = source type (GT, CB, GB, PK, etc.)
    - NN = sample sequence

    Common source codes:
    - GT = Ground Turkey
    - CB = Chicken Breast
    - GB = Ground Beef
    - PK = Pork
    - CC = Cecal Contents
    - SW = Swine
    - etc.
    """
    if not sample_name or len(sample_name) < 8:
        return 'Unknown'

    # Try to extract 2-letter code (usually positions 6-8)
    # Format is typically like: 25KS08GT06
    try:
        # Remove year prefix (first 2 digits)
        without_year = sample_name[2:]
        # Remove state code (KS)
        without_state = without_year[2:]
        # Remove sample number (next 2 digits)
        without_num = without_state[2:]
        # Extract source code (next 2 letters)
        source_code = without_num[:2]

        # Map to full names
        source_map = {
            'GT': 'Ground Turkey',
            'CB': 'Chicken Breast',
            'GB': 'Ground Beef',
            'PK': 'Pork',
            'CC': 'Cecal Contents',
            'SW': 'Swine',
            'CT': 'Cattle',
            'CK': 'Chicken',
            'TK': 'Turkey',
            'PT': 'Poultry',
            'BF': 'Beef',
        }

        return source_map.get(source_code.upper(), f'Other ({source_code})')
    except:
        return 'Unknown'


def load_metadata(results_dir):
    """Load sample metadata"""
    metadata_file = Path(results_dir) / "filtered_samples" / "filtered_samples.csv"
    metadata = {}

    if not metadata_file.exists():
        return metadata

    with open(metadata_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row['Run']
            organism = row.get('organism', row.get('Organism', 'Unknown'))
            year = row.get('Year', '')
            if not year and 'Collection_Date' in row:
                year = row['Collection_Date'][:4] if row['Collection_Date'] else 'Unknown'

            # Extract source from sample name
            sample_name = row.get('SampleName', row.get('Sample Name', ''))
            source = extract_source_from_sample_name(sample_name)

            metadata[sample_id] = {
                'organism': organism,
                'year': year,
                'source': source,
                'sample_name': sample_name
            }

    return metadata


# ============================================================================
# ANALYSIS 1: SAMPLE-LEVEL CO-OCCURRENCE
# ============================================================================

def analyze_sample_cooccurrence(amr_data, vibrant_data, metadata):
    """
    Analyze which AMR genes/classes co-occur with prophage presence at sample level
    """
    print("\n" + "="*80)
    print("ANALYSIS 1: SAMPLE-LEVEL CO-OCCURRENCE")
    print("="*80)

    # Categorize samples
    samples_with_phage = set(vibrant_data.keys())
    samples_with_amr = set(amr_data.keys())
    all_samples = samples_with_phage | samples_with_amr

    both = samples_with_phage & samples_with_amr
    phage_only = samples_with_phage - samples_with_amr
    amr_only = samples_with_amr - samples_with_phage
    neither = all_samples - (samples_with_phage | samples_with_amr)

    print(f"\n📊 Sample Categories:")
    print(f"  Total samples: {len(all_samples)}")
    print(f"  AMR + Prophage: {len(both)} ({len(both)/len(all_samples)*100:.1f}%)")
    print(f"  AMR only: {len(amr_only)} ({len(amr_only)/len(all_samples)*100:.1f}%)")
    print(f"  Prophage only: {len(phage_only)} ({len(phage_only)/len(all_samples)*100:.1f}%)")
    print(f"  Neither: {len(neither)} ({len(neither)/len(all_samples)*100:.1f}%)")

    # AMR genes enriched in prophage+ samples
    genes_in_phage_pos = Counter()
    genes_in_phage_neg = Counter()
    classes_in_phage_pos = Counter()
    classes_in_phage_neg = Counter()

    for sample_id, genes in amr_data.items():
        has_phage = sample_id in samples_with_phage

        for gene_data in genes:
            gene = gene_data['gene']
            gene_class = gene_data['class']

            if has_phage:
                genes_in_phage_pos[gene] += 1
                classes_in_phage_pos[gene_class] += 1
            else:
                genes_in_phage_neg[gene] += 1
                classes_in_phage_neg[gene_class] += 1

    print(f"\n🧬 AMR Genes: Prophage+ vs Prophage-")
    print(f"  {'Gene':<25} {'Phage+':<10} {'Phage-':<10} {'Enrichment'}")
    print("  " + "-"*65)

    # Calculate enrichment (ratio of frequencies)
    total_phage_pos = len(both)
    total_phage_neg = len(amr_only)

    gene_enrichments = []
    for gene in genes_in_phage_pos.keys():
        freq_pos = genes_in_phage_pos[gene] / total_phage_pos if total_phage_pos > 0 else 0
        freq_neg = genes_in_phage_neg[gene] / total_phage_neg if total_phage_neg > 0 else 0
        enrichment = freq_pos / freq_neg if freq_neg > 0 else float('inf')

        gene_enrichments.append({
            'gene': gene,
            'phage_pos': genes_in_phage_pos[gene],
            'phage_neg': genes_in_phage_neg[gene],
            'enrichment': enrichment
        })

    # Show top enriched genes (present in at least 5 phage+ samples)
    gene_enrichments.sort(key=lambda x: x['enrichment'], reverse=True)
    for item in gene_enrichments[:20]:
        if item['phage_pos'] >= 5:  # Filter for statistical significance
            enr = item['enrichment']
            enr_str = f"{enr:.2f}x" if enr != float('inf') else "Only phage+"
            print(f"  {item['gene']:<25} {item['phage_pos']:<10} {item['phage_neg']:<10} {enr_str}")

    print(f"\n💊 Drug Classes: Prophage+ vs Prophage-")
    print(f"  {'Drug Class':<40} {'Phage+':<10} {'Phage-':<10} {'Enrichment'}")
    print("  " + "-"*75)

    class_enrichments = []
    for drug_class in classes_in_phage_pos.keys():
        freq_pos = classes_in_phage_pos[drug_class] / total_phage_pos if total_phage_pos > 0 else 0
        freq_neg = classes_in_phage_neg[drug_class] / total_phage_neg if total_phage_neg > 0 else 0
        enrichment = freq_pos / freq_neg if freq_neg > 0 else float('inf')

        class_enrichments.append({
            'class': drug_class,
            'phage_pos': classes_in_phage_pos[drug_class],
            'phage_neg': classes_in_phage_neg[drug_class],
            'enrichment': enrichment
        })

    class_enrichments.sort(key=lambda x: x['enrichment'], reverse=True)
    for item in class_enrichments[:15]:
        if item['phage_pos'] >= 5:
            enr = item['enrichment']
            enr_str = f"{enr:.2f}x" if enr != float('inf') else "Only phage+"
            print(f"  {item['class']:<40} {item['phage_pos']:<10} {item['phage_neg']:<10} {enr_str}")

    return {
        'gene_enrichments': gene_enrichments,
        'class_enrichments': class_enrichments,
        'sample_stats': {
            'both': len(both),
            'amr_only': len(amr_only),
            'phage_only': len(phage_only)
        }
    }


# ============================================================================
# ANALYSIS 2: CONTIG-LEVEL PATTERNS
# ============================================================================

def analyze_contig_patterns(amr_data, vibrant_data):
    """
    Analyze patterns at the contig level - same contig carrying both
    """
    print("\n" + "="*80)
    print("ANALYSIS 2: CONTIG-LEVEL PATTERNS")
    print("="*80)

    # Find contigs with both AMR and phages
    shared_contigs = defaultdict(lambda: {'samples': set(), 'amr_genes': Counter(), 'amr_classes': Counter()})

    for sample_id in set(amr_data.keys()) & set(vibrant_data.keys()):
        amr_contigs = {gene['contig'] for gene in amr_data[sample_id]}
        phage_contigs = {phage['contig'] for phage in vibrant_data[sample_id]}

        for contig in amr_contigs & phage_contigs:
            shared_contigs[contig]['samples'].add(sample_id)

            # Collect AMR genes on this contig
            for gene_data in amr_data[sample_id]:
                if gene_data['contig'] == contig:
                    shared_contigs[contig]['amr_genes'][gene_data['gene']] += 1
                    shared_contigs[contig]['amr_classes'][gene_data['class']] += 1

    print(f"\n🧬 Contigs Carrying Both AMR and Prophage:")
    print(f"  Total unique contigs with both: {len(shared_contigs)}")
    print(f"  Total samples affected: {len(set().union(*[data['samples'] for data in shared_contigs.values()]))}")

    if shared_contigs:
        print(f"\n  Top Contigs (by sample frequency):")
        print(f"  {'Contig':<40} {'Samples':<10} {'AMR Genes'}")
        print("  " + "-"*70)

        sorted_contigs = sorted(shared_contigs.items(),
                               key=lambda x: len(x[1]['samples']),
                               reverse=True)

        for contig, data in sorted_contigs[:20]:
            genes_str = ', '.join([f"{g}({c})" for g, c in data['amr_genes'].most_common(5)])
            print(f"  {contig[:40]:<40} {len(data['samples']):<10} {genes_str[:50]}")

    return shared_contigs


# ============================================================================
# ANALYSIS 3: AMR PROFILE CLUSTERING
# ============================================================================

def analyze_amr_profiles(amr_data, vibrant_data, metadata):
    """
    Look for distinct AMR profiles in prophage+ vs prophage- samples
    """
    print("\n" + "="*80)
    print("ANALYSIS 3: AMR PROFILE PATTERNS")
    print("="*80)

    # Build AMR profiles (gene presence/absence per sample)
    profiles_with_phage = []
    profiles_without_phage = []

    for sample_id, genes in amr_data.items():
        has_phage = sample_id in vibrant_data
        gene_set = set([g['gene'] for g in genes])

        if has_phage:
            profiles_with_phage.append(gene_set)
        else:
            profiles_without_phage.append(gene_set)

    # Find common AMR gene combinations in each group
    print(f"\n🔍 Common AMR Gene Combinations:")

    # Count co-occurring gene pairs
    def count_gene_pairs(profiles):
        pair_counts = Counter()
        for profile in profiles:
            genes = sorted(profile)
            for i, g1 in enumerate(genes):
                for g2 in genes[i+1:]:
                    pair_counts[(g1, g2)] += 1
        return pair_counts

    pairs_with_phage = count_gene_pairs(profiles_with_phage)
    pairs_without_phage = count_gene_pairs(profiles_without_phage)

    print(f"\n  Top Gene Pairs in Prophage+ Samples:")
    print(f"  {'Gene 1':<20} {'Gene 2':<20} {'Count':<10} {'% of Phage+ Samples'}")
    print("  " + "-"*70)

    for (g1, g2), count in pairs_with_phage.most_common(15):
        pct = count / len(profiles_with_phage) * 100 if profiles_with_phage else 0
        print(f"  {g1:<20} {g2:<20} {count:<10} {pct:>6.1f}%")

    return {
        'profiles_with_phage': len(profiles_with_phage),
        'profiles_without_phage': len(profiles_without_phage),
        'top_pairs_with_phage': pairs_with_phage.most_common(20),
        'top_pairs_without_phage': pairs_without_phage.most_common(20)
    }


# ============================================================================
# ANALYSIS 4: TEMPORAL/ORGANISM PATTERNS
# ============================================================================

def analyze_temporal_patterns(amr_data, vibrant_data, metadata):
    """
    Look for temporal, organism-specific, and source-specific patterns
    """
    print("\n" + "="*80)
    print("ANALYSIS 4: TEMPORAL, ORGANISM & SOURCE PATTERNS")
    print("="*80)

    # Organize by organism, year, and source
    by_organism = defaultdict(lambda: {'phage_pos': 0, 'phage_neg': 0, 'total_amr': 0})
    by_year = defaultdict(lambda: {'phage_pos': 0, 'phage_neg': 0, 'total_amr': 0})
    by_source = defaultdict(lambda: {'phage_pos': 0, 'phage_neg': 0, 'total_amr': 0, 'samples': set()})

    all_samples = set(amr_data.keys()) | set(vibrant_data.keys())

    for sample_id in all_samples:
        meta = metadata.get(sample_id, {})
        organism = meta.get('organism', 'Unknown')
        year = meta.get('year', 'Unknown')
        source = meta.get('source', 'Unknown')

        has_phage = sample_id in vibrant_data
        has_amr = sample_id in amr_data
        amr_count = len(amr_data.get(sample_id, []))

        if has_phage:
            by_organism[organism]['phage_pos'] += 1
            by_year[year]['phage_pos'] += 1
            by_source[source]['phage_pos'] += 1
        else:
            by_organism[organism]['phage_neg'] += 1
            by_year[year]['phage_neg'] += 1
            by_source[source]['phage_neg'] += 1

        by_organism[organism]['total_amr'] += amr_count
        by_year[year]['total_amr'] += amr_count
        by_source[source]['total_amr'] += amr_count
        by_source[source]['samples'].add(sample_id)

    print(f"\n🦠 Prophage Prevalence by Organism:")
    print(f"  {'Organism':<20} {'Phage+':<10} {'Phage-':<10} {'% Phage+':<12} {'Avg AMR/Sample'}")
    print("  " + "-"*80)

    for organism in sorted(by_organism.keys()):
        data = by_organism[organism]
        total = data['phage_pos'] + data['phage_neg']
        pct_phage = data['phage_pos'] / total * 100 if total > 0 else 0
        avg_amr = data['total_amr'] / total if total > 0 else 0
        print(f"  {organism:<20} {data['phage_pos']:<10} {data['phage_neg']:<10} {pct_phage:>6.1f}%      {avg_amr:>6.1f}")

    print(f"\n📅 Prophage Prevalence by Year:")
    print(f"  {'Year':<10} {'Phage+':<10} {'Phage-':<10} {'% Phage+':<12} {'Avg AMR/Sample'}")
    print("  " + "-"*70)

    for year in sorted(by_year.keys()):
        data = by_year[year]
        total = data['phage_pos'] + data['phage_neg']
        pct_phage = data['phage_pos'] / total * 100 if total > 0 else 0
        avg_amr = data['total_amr'] / total if total > 0 else 0
        print(f"  {year:<10} {data['phage_pos']:<10} {data['phage_neg']:<10} {pct_phage:>6.1f}%      {avg_amr:>6.1f}")

    print(f"\n🔬 Prophage Prevalence by Isolation Source:")
    print(f"  {'Source':<40} {'Total':<8} {'Phage+':<10} {'Phage-':<10} {'% Phage+':<12} {'Avg AMR'}")
    print("  " + "-"*100)

    # Sort by total samples (most common sources first)
    sorted_sources = sorted(by_source.items(),
                           key=lambda x: len(x[1]['samples']),
                           reverse=True)

    for source, data in sorted_sources:
        total = data['phage_pos'] + data['phage_neg']
        if total < 3:  # Skip sources with very few samples
            continue
        pct_phage = data['phage_pos'] / total * 100 if total > 0 else 0
        avg_amr = data['total_amr'] / total if total > 0 else 0

        # Shorten very long source names
        source_display = source[:40] if len(source) <= 40 else source[:37] + "..."
        print(f"  {source_display:<40} {total:<8} {data['phage_pos']:<10} {data['phage_neg']:<10} {pct_phage:>6.1f}%      {avg_amr:>6.1f}")

    # Highlight interesting patterns
    print(f"\n💡 Key Observations:")

    # Find sources with highest prophage prevalence (min 10 samples)
    high_phage_sources = [(src, data) for src, data in by_source.items()
                          if (data['phage_pos'] + data['phage_neg']) >= 10]
    if high_phage_sources:
        high_phage_sources.sort(key=lambda x: x[1]['phage_pos'] / (x[1]['phage_pos'] + x[1]['phage_neg']),
                               reverse=True)
        if high_phage_sources:
            top_src, top_data = high_phage_sources[0]
            top_total = top_data['phage_pos'] + top_data['phage_neg']
            top_pct = top_data['phage_pos'] / top_total * 100
            print(f"  • Highest prophage prevalence: {top_src[:50]} ({top_pct:.1f}%, n={top_total})")

    # Find sources with highest AMR burden
    high_amr_sources = [(src, data) for src, data in by_source.items()
                        if (data['phage_pos'] + data['phage_neg']) >= 10]
    if high_amr_sources:
        high_amr_sources.sort(key=lambda x: x[1]['total_amr'] / (x[1]['phage_pos'] + x[1]['phage_neg']),
                             reverse=True)
        if high_amr_sources:
            top_src, top_data = high_amr_sources[0]
            top_total = top_data['phage_pos'] + top_data['phage_neg']
            top_avg = top_data['total_amr'] / top_total
            print(f"  • Highest AMR burden: {top_src[:50]} ({top_avg:.1f} genes/sample, n={top_total})")

    return {
        'by_organism': dict(by_organism),
        'by_year': dict(by_year),
        'by_source': {k: {key: val for key, val in v.items() if key != 'samples'}
                     for k, v in by_source.items()}
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 explore_amr_phage_patterns.py <results_dir> [output_json]")
        print("\nExamples:")
        print("  python3 explore_amr_phage_patterns.py results_kansas_2021")
        print("  python3 explore_amr_phage_patterns.py ~/compass_kansas_results/results_kansas_2022 patterns.json")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    output_json = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not results_dir.exists():
        print(f"❌ Error: Directory not found: {results_dir}")
        sys.exit(1)

    print("\n🔬 Loading data...")
    amr_data = load_amr_data(results_dir)
    vibrant_data = load_vibrant_data(results_dir)
    metadata = load_metadata(results_dir)

    print(f"  ✅ Loaded {len(amr_data)} samples with AMR data")
    print(f"  ✅ Loaded {len(vibrant_data)} samples with prophage data")
    print(f"  ✅ Loaded {len(metadata)} sample metadata entries")

    # Run analyses
    results = {}

    results['cooccurrence'] = analyze_sample_cooccurrence(amr_data, vibrant_data, metadata)
    results['contig_patterns'] = analyze_contig_patterns(amr_data, vibrant_data)
    results['profile_patterns'] = analyze_amr_profiles(amr_data, vibrant_data, metadata)
    results['temporal_patterns'] = analyze_temporal_patterns(amr_data, vibrant_data, metadata)

    # Save results if output file specified
    if output_json:
        # Convert sets to lists for JSON serialization
        def serialize_for_json(obj):
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, defaultdict):
                return dict(obj)
            elif isinstance(obj, Counter):
                return dict(obj)
            return obj

        with open(output_json, 'w') as f:
            json.dump(results, f, default=serialize_for_json, indent=2)
        print(f"\n✅ Results saved to: {output_json}")

    print("\n" + "="*80)
    print("✅ Exploratory analysis complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
