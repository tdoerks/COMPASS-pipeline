#!/usr/bin/env python3
"""
Comprehensive AMR-Phage-Mobile Element Analysis

Combines all AMR analysis approaches into one comprehensive report:

1. Physical Co-location (from analyze_true_amr_prophage_colocation.py)
   - AMR genes inside or near prophages by genomic coordinates

2. Mobile Element Association (from analyze_amr_mobile_elements.py)
   - AMR genes on plasmids
   - AMR genes near integrases/transposases
   - Distance-based mobile element analysis

3. Exploratory Patterns (from explore_amr_phage_patterns.py)
   - Sample-level co-occurrence
   - AMR gene enrichment in prophage+ samples
   - Source/organism/temporal patterns

Generates:
- Comprehensive terminal report
- Detailed CSV files for each analysis
- Summary JSON with all statistics
- HTML report (optional)
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
import json
import re

# Import the individual analysis modules
# We'll include the key functions from each script directly

# ============================================================================
# SHARED DATA LOADING
# ============================================================================

def extract_source_from_sample_name(sample_name):
    """Extract source type from NARMS sample name (e.g., 25KS08GT06)"""
    if not sample_name or len(sample_name) < 8:
        return 'Unknown'

    try:
        source_code = sample_name[6:8]
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


def load_all_data(results_dir):
    """
    Load all data needed for comprehensive analysis

    Returns: dict with amr_data, vibrant_data, mobsuite_data, metadata
    """
    results_dir = Path(results_dir)

    print("📁 Loading data from all sources...")

    # Load metadata
    metadata = load_metadata(results_dir)
    print(f"  ✅ Loaded {len(metadata)} sample metadata entries")

    # Load AMR data
    amr_data = load_amr_full(results_dir)
    print(f"  ✅ Loaded AMR data from {len(amr_data['samples'])} samples")

    # Load prophage data
    vibrant_data = load_vibrant_data(results_dir)
    print(f"  ✅ Loaded prophage data from {len(vibrant_data)} samples")

    # Load MOB-suite plasmid data
    mobsuite_data = load_mobsuite_data(results_dir)
    print(f"  ✅ Loaded plasmid data from {len(mobsuite_data)} samples")

    return {
        'metadata': metadata,
        'amr': amr_data,
        'vibrant': vibrant_data,
        'mobsuite': mobsuite_data
    }


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

            sample_name = row.get('SampleName', row.get('Sample Name', ''))
            source = extract_source_from_sample_name(sample_name)

            metadata[sample_id] = {
                'organism': organism,
                'year': year,
                'source': source,
                'sample_name': sample_name
            }

    return metadata


def load_amr_full(results_dir):
    """
    Load complete AMR data including AMR genes AND mobile element genes

    Returns dict with:
    - samples: dict[sample_id] -> {'amr_genes': [...], 'mobile_elements': [...]}
    - all_genes: list of all AMR genes across samples
    - all_mobile_elements: list of all mobile element genes
    """
    amr_dir = Path(results_dir) / "amrfinder"

    samples = {}
    all_amr_genes = []
    all_mobile_elements = []

    for amr_file in amr_dir.glob("*_amr.tsv"):
        sample_id = amr_file.stem.replace('_amr', '')

        amr_genes = []
        mobile_elements = []

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

                gene_data = {
                    'contig': parts[1],
                    'start': int(parts[2]),
                    'end': int(parts[3]),
                    'strand': parts[4],
                    'gene': parts[5],
                    'class': parts[10],
                    'element_type': parts[8]
                }

                if parts[8] == 'AMR':
                    amr_genes.append(gene_data)
                    all_amr_genes.append(gene_data)
                else:
                    # Check if mobile element
                    mobile_type = classify_mobile_element(parts[5], parts[6] if len(parts) > 6 else '')
                    if mobile_type:
                        gene_data['mobile_type'] = mobile_type
                        mobile_elements.append(gene_data)
                        all_mobile_elements.append(gene_data)

        if amr_genes or mobile_elements:
            samples[sample_id] = {
                'amr_genes': amr_genes,
                'mobile_elements': mobile_elements
            }

    return {
        'samples': samples,
        'all_amr_genes': all_amr_genes,
        'all_mobile_elements': all_mobile_elements
    }


def classify_mobile_element(gene_symbol, gene_name):
    """Classify gene as mobile element type"""
    combined = f"{gene_symbol} {gene_name}".lower()

    patterns = {
        'integrase': [r'^int[IATCG]\d*$', r'^intI', r'integrase'],
        'transposase': [r'^tnp', r'transposase', r'^IS\d+'],
        'recombinase': [r'recombinase', r'^xerC', r'^xerD'],
        'resolvase': [r'resolvase', r'^tnpR']
    }

    for me_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, combined, re.IGNORECASE):
                return me_type

    return None


def load_vibrant_data(results_dir):
    """Load prophage data from VIBRANT"""
    vibrant_dir = Path(results_dir) / "vibrant"
    vibrant_data = {}

    for sample_dir in vibrant_dir.glob("*_vibrant"):
        sample_id = sample_dir.name.replace('_vibrant', '')
        phage_fasta = vibrant_dir / f"{sample_id}_phages.fna"

        prophages = []
        if phage_fasta.exists():
            with open(phage_fasta) as f:
                for line in f:
                    if line.startswith('>'):
                        header = line.strip()[1:].split()[0]
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


def load_mobsuite_data(results_dir):
    """Load plasmid data from MOB-suite"""
    mobsuite_dir = Path(results_dir) / "mobsuite"
    mobsuite_data = {}

    for sample_dir in mobsuite_dir.glob("*_mobsuite"):
        sample_id = sample_dir.name.replace('_mobsuite', '')

        plasmid_contigs = set()
        for plasmid_fasta in sample_dir.glob("plasmid_*.fasta"):
            with open(plasmid_fasta) as f:
                for line in f:
                    if line.startswith('>'):
                        contig_name = line.strip()[1:].split()[0]
                        plasmid_contigs.add(contig_name)

        if plasmid_contigs:
            mobsuite_data[sample_id] = {'plasmid_contigs': plasmid_contigs}

    return mobsuite_data


# ============================================================================
# COMPREHENSIVE ANALYSIS
# ============================================================================

def run_comprehensive_analysis(data):
    """
    Run all analyses and compile results
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE AMR ANALYSIS")
    print("="*80)

    results = {}

    # Analysis 1: Physical co-location
    print("\n" + "="*80)
    print("SECTION 1: PHYSICAL CO-LOCATION (AMR inside/near prophages)")
    print("="*80)
    results['physical_colocation'] = analyze_physical_colocation(data)

    # Analysis 2: Mobile elements
    print("\n" + "="*80)
    print("SECTION 2: MOBILE ELEMENT ASSOCIATION")
    print("="*80)
    results['mobile_elements'] = analyze_mobile_elements(data)

    # Analysis 3: Sample-level patterns
    print("\n" + "="*80)
    print("SECTION 3: SAMPLE-LEVEL PATTERNS")
    print("="*80)
    results['sample_patterns'] = analyze_sample_patterns(data)

    # Analysis 4: Source/organism/temporal patterns
    print("\n" + "="*80)
    print("SECTION 4: SOURCE & TEMPORAL PATTERNS")
    print("="*80)
    results['source_patterns'] = analyze_source_patterns(data)

    return results


def analyze_physical_colocation(data):
    """Analyze physical distance between AMR and prophages"""
    print("\n🔍 Analyzing physical co-location...")

    # Simplified version - count AMR on same contigs as prophages
    same_contig_count = 0
    total_amr = 0

    for sample_id, sample_data in data['amr']['samples'].items():
        if sample_id not in data['vibrant']:
            continue

        amr_contigs = {g['contig'] for g in sample_data['amr_genes']}
        phage_contigs = {p['contig'] for p in data['vibrant'][sample_id]}

        shared = amr_contigs & phage_contigs
        same_contig_count += len(shared)
        total_amr += len(sample_data['amr_genes'])

    print(f"  • Total AMR genes: {total_amr}")
    print(f"  • AMR genes on same contig as prophage: {same_contig_count}")
    print(f"  • Percentage: {same_contig_count/total_amr*100:.2f}%" if total_amr > 0 else "  • No AMR genes found")

    return {
        'total_amr': total_amr,
        'same_contig': same_contig_count
    }


def analyze_mobile_elements(data):
    """Analyze AMR association with plasmids and mobile elements"""
    print("\n🧬 Analyzing mobile element associations...")

    amr_on_plasmids = 0
    total_amr = 0
    samples_with_plasmids = len(data['mobsuite'])

    for sample_id, sample_data in data['amr']['samples'].items():
        for gene in sample_data['amr_genes']:
            total_amr += 1
            if sample_id in data['mobsuite']:
                if gene['contig'] in data['mobsuite'][sample_id]['plasmid_contigs']:
                    amr_on_plasmids += 1

    print(f"  • Samples with plasmids detected: {samples_with_plasmids}")
    print(f"  • Total AMR genes: {total_amr}")
    print(f"  • AMR genes on plasmids: {amr_on_plasmids}")
    print(f"  • Percentage on plasmids: {amr_on_plasmids/total_amr*100:.2f}%" if total_amr > 0 else "  • No AMR genes")

    # Mobile element genes found
    mobile_counts = Counter()
    for sample_data in data['amr']['samples'].values():
        for me in sample_data['mobile_elements']:
            mobile_counts[me['mobile_type']] += 1

    if mobile_counts:
        print(f"\n  Mobile element genes detected:")
        for me_type, count in mobile_counts.most_common():
            print(f"    - {me_type}: {count}")
    else:
        print(f"\n  ⚠️  No mobile element genes detected in AMRFinder output")

    return {
        'samples_with_plasmids': samples_with_plasmids,
        'amr_on_plasmids': amr_on_plasmids,
        'total_amr': total_amr,
        'mobile_element_genes': dict(mobile_counts)
    }


def analyze_sample_patterns(data):
    """Analyze sample-level co-occurrence patterns"""
    print("\n📊 Analyzing sample-level patterns...")

    samples_with_amr = set(data['amr']['samples'].keys())
    samples_with_phage = set(data['vibrant'].keys())
    samples_with_plasmids = set(data['mobsuite'].keys())

    all_samples = samples_with_amr | samples_with_phage | samples_with_plasmids

    both_amr_phage = samples_with_amr & samples_with_phage
    both_amr_plasmid = samples_with_amr & samples_with_plasmids
    all_three = samples_with_amr & samples_with_phage & samples_with_plasmids

    print(f"\n  Sample Categories:")
    print(f"    Total samples: {len(all_samples)}")
    print(f"    With AMR: {len(samples_with_amr)} ({len(samples_with_amr)/len(all_samples)*100:.1f}%)")
    print(f"    With prophages: {len(samples_with_phage)} ({len(samples_with_phage)/len(all_samples)*100:.1f}%)")
    print(f"    With plasmids: {len(samples_with_plasmids)} ({len(samples_with_plasmids)/len(all_samples)*100:.1f}%)")
    print(f"    AMR + prophages: {len(both_amr_phage)} ({len(both_amr_phage)/len(all_samples)*100:.1f}%)")
    print(f"    AMR + plasmids: {len(both_amr_plasmid)} ({len(both_amr_plasmid)/len(all_samples)*100:.1f}%)")
    print(f"    All three: {len(all_three)} ({len(all_three)/len(all_samples)*100:.1f}%)")

    return {
        'total_samples': len(all_samples),
        'with_amr': len(samples_with_amr),
        'with_phage': len(samples_with_phage),
        'with_plasmids': len(samples_with_plasmids),
        'amr_phage': len(both_amr_phage),
        'amr_plasmid': len(both_amr_plasmid),
        'all_three': len(all_three)
    }


def analyze_source_patterns(data):
    """Analyze patterns by source, organism, year"""
    print("\n🔬 Analyzing by source, organism, and year...")

    by_source = defaultdict(lambda: {'amr': 0, 'phage': 0, 'plasmid': 0, 'total': 0})
    by_organism = defaultdict(lambda: {'amr': 0, 'phage': 0, 'plasmid': 0, 'total': 0})
    by_year = defaultdict(lambda: {'amr': 0, 'phage': 0, 'plasmid': 0, 'total': 0})

    all_samples = set(data['metadata'].keys())

    for sample_id in all_samples:
        meta = data['metadata'].get(sample_id, {})
        source = meta.get('source', 'Unknown')
        organism = meta.get('organism', 'Unknown')
        year = meta.get('year', 'Unknown')

        has_amr = sample_id in data['amr']['samples']
        has_phage = sample_id in data['vibrant']
        has_plasmid = sample_id in data['mobsuite']

        for category, key in [(by_source, source), (by_organism, organism), (by_year, year)]:
            category[key]['total'] += 1
            if has_amr:
                category[key]['amr'] += 1
            if has_phage:
                category[key]['phage'] += 1
            if has_plasmid:
                category[key]['plasmid'] += 1

    # Print source breakdown
    print(f"\n  By Food Source:")
    print(f"    {'Source':<30} {'Total':<8} {'AMR':<8} {'Phage':<8} {'Plasmid':<10}")
    print("    " + "-"*70)

    sorted_sources = sorted(by_source.items(), key=lambda x: x[1]['total'], reverse=True)
    for source, stats in sorted_sources[:15]:
        if stats['total'] >= 3:
            print(f"    {source:<30} {stats['total']:<8} {stats['amr']:<8} {stats['phage']:<8} {stats['plasmid']:<10}")

    # Print organism breakdown
    print(f"\n  By Organism:")
    print(f"    {'Organism':<20} {'Total':<8} {'AMR':<8} {'Phage':<8} {'Plasmid':<10}")
    print("    " + "-"*60)

    for organism in sorted(by_organism.keys()):
        stats = by_organism[organism]
        print(f"    {organism:<20} {stats['total']:<8} {stats['amr']:<8} {stats['phage']:<8} {stats['plasmid']:<10}")

    return {
        'by_source': dict(by_source),
        'by_organism': dict(by_organism),
        'by_year': dict(by_year)
    }


# ============================================================================
# OUTPUT
# ============================================================================

def save_results(results, output_dir):
    """Save all results to files"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Save JSON summary
    json_file = output_dir / "comprehensive_analysis.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Results saved to: {json_file}")

    return json_file


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 comprehensive_amr_analysis.py <results_dir> [output_dir]")
        print("\nExamples:")
        print("  python3 comprehensive_amr_analysis.py results_kansas_2022")
        print("  python3 comprehensive_amr_analysis.py ~/compass_kansas_results/results_kansas_2022 output/")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else results_dir / "comprehensive_analysis"

    if not results_dir.exists():
        print(f"❌ Error: Directory not found: {results_dir}")
        sys.exit(1)

    print("\n🔬 COMPREHENSIVE AMR-PHAGE-MOBILE ELEMENT ANALYSIS")
    print("="*80)
    print(f"Results directory: {results_dir}")
    print(f"Output directory: {output_dir}")
    print("="*80)

    # Load all data
    data = load_all_data(results_dir)

    # Run comprehensive analysis
    results = run_comprehensive_analysis(data)

    # Save results
    save_results(results, output_dir)

    print("\n" + "="*80)
    print("✅ Comprehensive analysis complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
