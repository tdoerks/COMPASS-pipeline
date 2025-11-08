#!/usr/bin/env python3
"""
Species Comparison Analysis: AMR-Prophage Associations
Compare E. coli, Salmonella, and Campylobacter for differences in:
- Prophage prevalence
- AMR gene prevalence
- AMR-prophage co-location rates
- Drug class distributions
- Specific AMR genes enriched per species
"""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import csv

def parse_metadata(metadata_file):
    """Parse organism information from filtered_samples.csv"""
    organism_map = {}

    if not Path(metadata_file).exists():
        return organism_map

    with open(metadata_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row['Run']  # SRR accession
            organism = row['Organism']
            organism_map[sample_id] = organism

    return organism_map

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

def analyze_all_species(results_dir):
    """Analyze AMR-prophage associations for all species"""
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"
    metadata_file = results_dir / "filtered_samples" / "filtered_samples.csv"

    # Get organism mapping
    organism_map = parse_metadata(metadata_file)

    # Data structures by species
    species_data = defaultdict(lambda: {
        'samples': 0,
        'samples_with_amr': 0,
        'samples_with_prophage': 0,
        'samples_with_colocation': 0,
        'total_amr_genes': 0,
        'amr_on_prophage': 0,
        'amr_genes': Counter(),
        'amr_classes': Counter(),
        'amr_genes_on_prophage': Counter(),
        'amr_classes_on_prophage': Counter(),
        'prophage_contigs': 0
    })

    # Process all samples
    for amr_file in sorted(amr_dir.glob("*_amr.tsv")):
        sample_id = amr_file.stem.replace('_amr', '')

        # Get organism
        organism = organism_map.get(sample_id, 'Unknown')
        if organism == 'Unknown':
            continue

        species = species_data[organism]
        species['samples'] += 1

        # Parse data
        contig_amr = parse_amr_by_contig(amr_file)
        vibrant_phages_file = vibrant_dir / f"{sample_id}_phages.fna"
        prophage_contigs = parse_prophage_contigs(vibrant_phages_file)

        # Track prophage presence
        if prophage_contigs:
            species['samples_with_prophage'] += 1
            species['prophage_contigs'] += len(prophage_contigs)

        # Track AMR genes
        has_amr = False
        has_colocation = False

        for contig, amr_genes in contig_amr.items():
            is_prophage = any(contig.startswith(pc) for pc in prophage_contigs)

            for amr in amr_genes:
                has_amr = True
                species['total_amr_genes'] += 1
                species['amr_genes'][amr['gene']] += 1
                species['amr_classes'][amr['class']] += 1

                if is_prophage:
                    has_colocation = True
                    species['amr_on_prophage'] += 1
                    species['amr_genes_on_prophage'][amr['gene']] += 1
                    species['amr_classes_on_prophage'][amr['class']] += 1

        if has_amr:
            species['samples_with_amr'] += 1
        if has_colocation:
            species['samples_with_colocation'] += 1

    return species_data

def calculate_enrichment(species_data, gene, organism):
    """Calculate if a gene is enriched in one species vs others"""
    org_data = species_data[organism]

    # Gene frequency in this organism
    org_gene_count = org_data['amr_genes'][gene]
    org_total_genes = org_data['total_amr_genes']

    if org_total_genes == 0:
        return 0, 0

    org_freq = org_gene_count / org_total_genes

    # Gene frequency in all other organisms
    other_gene_count = 0
    other_total_genes = 0

    for other_org, other_data in species_data.items():
        if other_org != organism:
            other_gene_count += other_data['amr_genes'][gene]
            other_total_genes += other_data['total_amr_genes']

    if other_total_genes == 0:
        return 0, 0

    other_freq = other_gene_count / other_total_genes

    # Enrichment ratio
    if other_freq == 0:
        enrichment = float('inf') if org_freq > 0 else 0
    else:
        enrichment = org_freq / other_freq

    return enrichment, org_gene_count

def print_analysis(species_data, results_dir):
    """Print comprehensive species comparison"""

    print("\n" + "="*85)
    print("Species Comparison: AMR-Prophage Associations")
    print("E. coli vs Salmonella vs Campylobacter")
    print(f"Results: {results_dir}")
    print("="*85)

    # Overall summary table
    print(f"\n📊 Overall Species Comparison:")
    print(f"  {'Species':<25} {'Samples':<10} {'w/AMR':<10} {'w/Prophage':<12} {'w/Co-location':<15}")
    print("  " + "-"*75)

    for organism in sorted(species_data.keys()):
        data = species_data[organism]
        print(f"  {organism:<25} {data['samples']:<10} {data['samples_with_amr']:<10} "
              f"{data['samples_with_prophage']:<12} {data['samples_with_colocation']:<15}")

    # AMR statistics
    print(f"\n💊 AMR Gene Statistics by Species:")
    print(f"  {'Species':<25} {'Total AMR':<12} {'On Prophage':<15} {'% on Prophage':<15} {'Avg per Sample'}")
    print("  " + "-"*85)

    for organism in sorted(species_data.keys()):
        data = species_data[organism]
        pct_prophage = (data['amr_on_prophage'] / data['total_amr_genes'] * 100) if data['total_amr_genes'] > 0 else 0
        avg_per_sample = data['total_amr_genes'] / data['samples'] if data['samples'] > 0 else 0

        print(f"  {organism:<25} {data['total_amr_genes']:<12} {data['amr_on_prophage']:<15} "
              f"{pct_prophage:<14.1f}% {avg_per_sample:.1f}")

    # Prophage prevalence
    print(f"\n🦠 Prophage Prevalence:")
    print(f"  {'Species':<25} {'Samples w/Prophage':<20} {'% Samples':<12} {'Avg Contigs/Sample'}")
    print("  " + "-"*75)

    for organism in sorted(species_data.keys()):
        data = species_data[organism]
        pct_samples = (data['samples_with_prophage'] / data['samples'] * 100) if data['samples'] > 0 else 0
        avg_contigs = data['prophage_contigs'] / data['samples_with_prophage'] if data['samples_with_prophage'] > 0 else 0

        print(f"  {organism:<25} {data['samples_with_prophage']:<20} {pct_samples:<11.1f}% {avg_contigs:.1f}")

    # Co-location rates
    print(f"\n🔗 AMR-Prophage Co-location Rates:")
    print(f"  {'Species':<25} {'Samples w/Co-location':<22} {'% of AMR samples':<20}")
    print("  " + "-"*70)

    for organism in sorted(species_data.keys()):
        data = species_data[organism]
        pct_coloc = (data['samples_with_colocation'] / data['samples_with_amr'] * 100) if data['samples_with_amr'] > 0 else 0

        print(f"  {organism:<25} {data['samples_with_colocation']:<22} {pct_coloc:.1f}%")

    # Top AMR genes per species
    print(f"\n🧬 Top 10 AMR Genes per Species:")

    for organism in sorted(species_data.keys()):
        data = species_data[organism]
        print(f"\n  {organism}:")
        print(f"    {'Gene':<25} {'Count':<10} {'% of samples':<15} {'On Prophage'}")
        print("    " + "-"*65)

        for gene, count in data['amr_genes'].most_common(10):
            pct_samples = (count / data['samples'] * 100) if data['samples'] > 0 else 0
            on_prophage = data['amr_genes_on_prophage'][gene]
            pct_prophage = (on_prophage / count * 100) if count > 0 else 0

            print(f"    {gene:<25} {count:<10} {pct_samples:<14.1f}% {on_prophage} ({pct_prophage:.0f}%)")

    # Species-enriched genes
    print(f"\n🎯 Species-Enriched AMR Genes:")
    print(f"  (≥5x enrichment, ≥10 occurrences)")

    for organism in sorted(species_data.keys()):
        data = species_data[organism]
        enriched = []

        for gene, count in data['amr_genes'].most_common():
            if count < 10:
                continue
            enrichment, gene_count = calculate_enrichment(species_data, gene, organism)
            if enrichment >= 5:
                enriched.append((gene, enrichment, gene_count))

        if enriched:
            print(f"\n  {organism}:")
            print(f"    {'Gene':<25} {'Count':<10} {'Enrichment'}")
            print("    " + "-"*50)
            for gene, enrich, count in sorted(enriched, key=lambda x: x[1], reverse=True)[:10]:
                enrich_str = f"{enrich:.1f}x" if enrich != float('inf') else "Unique"
                print(f"    {gene:<25} {count:<10} {enrich_str}")

    # Drug class comparison
    print(f"\n💊 Drug Class Distribution by Species:")

    for organism in sorted(species_data.keys()):
        data = species_data[organism]
        print(f"\n  {organism} - Top 10 Drug Classes:")
        print(f"    {'Drug Class':<40} {'Count':<10} {'On Prophage'}")
        print("    " + "-"*65)

        for drug_class, count in data['amr_classes'].most_common(10):
            on_prophage = data['amr_classes_on_prophage'][drug_class]
            pct = (on_prophage / count * 100) if count > 0 else 0
            print(f"    {drug_class:<40} {count:<10} {on_prophage} ({pct:.0f}%)")

    # Key findings
    print(f"\n💡 Key Findings:")

    # Which species has highest prophage-AMR rate?
    max_rate_org = None
    max_rate = 0
    for organism, data in species_data.items():
        if data['total_amr_genes'] > 0:
            rate = data['amr_on_prophage'] / data['total_amr_genes'] * 100
            if rate > max_rate:
                max_rate = rate
                max_rate_org = organism

    if max_rate_org:
        print(f"  • {max_rate_org} has highest AMR-on-prophage rate: {max_rate:.1f}%")

    # Which species has most diverse AMR?
    max_diversity_org = None
    max_diversity = 0
    for organism, data in species_data.items():
        diversity = len(data['amr_genes'])
        if diversity > max_diversity:
            max_diversity = diversity
            max_diversity_org = organism

    if max_diversity_org:
        print(f"  • {max_diversity_org} has highest AMR gene diversity: {max_diversity} unique genes")

    # Which species has most prophages?
    max_prophage_org = None
    max_prophage_rate = 0
    for organism, data in species_data.items():
        if data['samples'] > 0:
            rate = data['samples_with_prophage'] / data['samples'] * 100
            if rate > max_prophage_rate:
                max_prophage_rate = rate
                max_prophage_org = organism

    if max_prophage_org:
        print(f"  • {max_prophage_org} has highest prophage prevalence: {max_prophage_rate:.1f}% of samples")

def main():
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    else:
        results_dir = Path("/homes/tylerdoe/compass_kansas_results/results_kansas_2024")

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    print(f"📊 Analyzing species-specific AMR-prophage associations...")

    species_data = analyze_all_species(results_dir)

    if not species_data:
        print("❌ No data found!")
        sys.exit(1)

    print_analysis(species_data, results_dir)

    print("\n" + "="*85)
    print("✅ Analysis complete!")
    print("="*85 + "\n")

if __name__ == "__main__":
    main()
