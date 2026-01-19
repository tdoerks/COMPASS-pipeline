#!/usr/bin/env python3
"""
Validate AMR-in-Prophage Results - Statistical Consistency Checks

This script analyzes Method 3 (direct AMRFinder scan) results to verify
the findings are statistically reasonable and biologically plausible.

Quick validation checks without requiring re-scanning or BLAST.

Usage:
    # Single dataset
    python3 validate_amr_prophage_statistics.py method3_results.csv

    # Multiple datasets (2021-2024)
    python3 validate_amr_prophage_statistics.py ecoli_2021/method3_direct_scan.csv ecoli_2022/method3_direct_scan.csv

    # With output file
    python3 validate_amr_prophage_statistics.py method3_results.csv --output validation_report.txt

Author: Claude + Tyler Doerks
Date: January 2026
"""

import sys
import csv
import argparse
from pathlib import Path
from collections import Counter, defaultdict
import statistics


# Known mobile AMR gene families (commonly found in phages/plasmids)
MOBILE_AMR_GENES = {
    # Tetracycline
    'tet', 'tetA', 'tetB', 'tetC', 'tetD', 'tetE', 'tetG', 'tetM', 'tetO', 'tetX',
    # Aminoglycosides
    'aac', 'aad', 'aph', 'ant', 'str', 'strA', 'strB',
    # Beta-lactams
    'bla', 'TEM', 'SHV', 'CTX-M', 'OXA', 'CMY',
    # Sulfonamides
    'sul', 'sul1', 'sul2', 'sul3',
    # Trimethoprim
    'dfr', 'dfrA', 'dfrB',
    # Chloramphenicol
    'cat', 'catA', 'catB', 'cmlA', 'floR',
    # Macrolides
    'erm', 'ere', 'mph', 'mef',
    # Quinolones (mobile)
    'qnr', 'qnrA', 'qnrB', 'qnrS', 'aac(6\')-Ib-cr'
}

# Chromosomal AMR (rare in phages - suspicious if found)
CHROMOSOMAL_AMR_GENES = {
    'gyrA', 'gyrB', 'parC', 'parE',  # Quinolone resistance (mutations)
    'rpoB',  # Rifampin resistance (mutations)
    'folP', 'folA',  # Folate pathway (chromosomal)
}


def parse_method3_csv(csv_file):
    """
    Parse Method 3 (direct AMRFinder scan) CSV results

    Expected format:
    sample,gene,class,subclass,method,prophage_contig,whole_genome_amr_count,prophage_count

    Returns: list of dicts
    """
    results = []

    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found: {csv_file}")
        return results

    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip rows with no gene (empty samples)
                if row.get('gene') == 'None' or not row.get('gene'):
                    continue
                results.append(row)
    except Exception as e:
        print(f"❌ Error parsing CSV: {e}")
        return []

    return results


def check_proportion(results):
    """
    Check if proportion of AMR in prophages is reasonable

    Expected: 1-10% of total AMR burden
    Suspicious: >30%
    """
    print("\n" + "="*80)
    print("CHECK 1: Proportion of AMR in Prophages")
    print("="*80)

    if not results:
        print("❌ No data to analyze")
        return False

    # Get total AMR genes across all samples
    total_genome_amr = 0
    total_prophage_amr = len(results)  # Each row is a prophage AMR gene
    samples = set()

    for row in results:
        samples.add(row['sample'])
        try:
            total_genome_amr += int(row.get('whole_genome_amr_count', 0))
        except (ValueError, TypeError):
            pass

    # Calculate proportion
    if total_genome_amr > 0:
        proportion = (total_prophage_amr / total_genome_amr) * 100
    else:
        proportion = 0

    print(f"\n📊 Overall Statistics:")
    print(f"  Samples analyzed: {len(samples)}")
    print(f"  Total AMR genes in whole genomes: {total_genome_amr}")
    print(f"  Total AMR genes in prophages: {total_prophage_amr}")
    print(f"  Proportion in prophages: {proportion:.2f}%")

    # Interpret
    print(f"\n🔍 Interpretation:")
    if proportion < 1:
        print(f"  ✅ VERY LOW ({proportion:.2f}%) - Typical for most datasets")
        print(f"     Most AMR genes are chromosomal, not mobile")
        status = "PASS"
    elif 1 <= proportion <= 10:
        print(f"  ✅ LOW-MODERATE ({proportion:.2f}%) - Expected range")
        print(f"     Consistent with mobile AMR gene prevalence")
        status = "PASS"
    elif 10 < proportion <= 30:
        print(f"  ⚠️  MODERATE-HIGH ({proportion:.2f}%) - Worth investigating")
        print(f"     Higher than typical, but possible in highly mobile populations")
        status = "WARNING"
    else:
        print(f"  🚨 VERY HIGH ({proportion:.2f}%) - SUSPICIOUS!")
        print(f"     >30% is unusual - may indicate false positives or unique population")
        status = "SUSPICIOUS"

    return status


def check_gene_types(results):
    """
    Check if AMR gene types are appropriate for prophages

    Expected: Mobile genes (tet, aph, sul, bla, etc.)
    Suspicious: Chromosomal mutation genes (gyrA, parC, rpoB)
    """
    print("\n" + "="*80)
    print("CHECK 2: AMR Gene Types (Mobile vs Chromosomal)")
    print("="*80)

    mobile_genes = []
    chromosomal_genes = []
    unknown_genes = []

    for row in results:
        gene = row.get('gene', '')

        # Check if gene is in mobile list
        is_mobile = any(mobile in gene for mobile in MOBILE_AMR_GENES)
        is_chromosomal = any(chrom in gene for chrom in CHROMOSOMAL_AMR_GENES)

        if is_chromosomal:
            chromosomal_genes.append(gene)
        elif is_mobile:
            mobile_genes.append(gene)
        else:
            unknown_genes.append(gene)

    total = len(results)

    print(f"\n🧬 Gene Classification:")
    print(f"  Mobile AMR genes: {len(mobile_genes)} ({len(mobile_genes)/total*100:.1f}%)")
    print(f"  Chromosomal genes: {len(chromosomal_genes)} ({len(chromosomal_genes)/total*100:.1f}%)")
    print(f"  Unknown/Other: {len(unknown_genes)} ({len(unknown_genes)/total*100:.1f}%)")

    # Show top mobile genes
    if mobile_genes:
        mobile_counts = Counter(mobile_genes)
        print(f"\n  Top Mobile Genes:")
        for gene, count in mobile_counts.most_common(10):
            print(f"    {gene}: {count}")

    # Flag chromosomal genes
    if chromosomal_genes:
        print(f"\n  🚨 Chromosomal Genes Found (SUSPICIOUS):")
        chrom_counts = Counter(chromosomal_genes)
        for gene, count in chrom_counts.most_common():
            print(f"    {gene}: {count} occurrences")

    print(f"\n🔍 Interpretation:")
    if len(chromosomal_genes) == 0 and len(mobile_genes) > total * 0.5:
        print(f"  ✅ EXPECTED - Mostly mobile AMR genes, no chromosomal genes")
        status = "PASS"
    elif len(chromosomal_genes) > 0 and len(chromosomal_genes) < total * 0.1:
        print(f"  ⚠️  WARNING - Found {len(chromosomal_genes)} chromosomal genes (<10%)")
        print(f"     May be false positives or misannotations")
        status = "WARNING"
    elif len(chromosomal_genes) >= total * 0.1:
        print(f"  🚨 SUSPICIOUS - {len(chromosomal_genes)} chromosomal genes (≥10%)")
        print(f"     Chromosomal genes should not be in prophages")
        status = "SUSPICIOUS"
    else:
        print(f"  ⚠️  UNKNOWN - Many genes not in reference lists")
        status = "WARNING"

    return status


def check_sample_distribution(results):
    """
    Check distribution of AMR genes across samples

    Expected: Many samples with 1-3 genes each
    Suspicious: One sample with 50+ genes
    """
    print("\n" + "="*80)
    print("CHECK 3: Sample Distribution")
    print("="*80)

    # Count genes per sample
    sample_gene_counts = Counter()
    for row in results:
        sample_gene_counts[row['sample']] += 1

    gene_counts = list(sample_gene_counts.values())

    print(f"\n📊 Distribution Statistics:")
    print(f"  Samples with AMR in prophages: {len(sample_gene_counts)}")
    print(f"  Total AMR genes found: {sum(gene_counts)}")
    print(f"  Mean genes per sample: {statistics.mean(gene_counts):.2f}")
    print(f"  Median genes per sample: {statistics.median(gene_counts):.1f}")
    print(f"  Max genes in single sample: {max(gene_counts)}")
    print(f"  Min genes in single sample: {min(gene_counts)}")

    # Histogram
    print(f"\n📈 Distribution Histogram:")
    count_bins = Counter()
    for count in gene_counts:
        if count == 1:
            count_bins['1 gene'] += 1
        elif count <= 3:
            count_bins['2-3 genes'] += 1
        elif count <= 5:
            count_bins['4-5 genes'] += 1
        elif count <= 10:
            count_bins['6-10 genes'] += 1
        else:
            count_bins['>10 genes'] += 1

    for bin_name in ['1 gene', '2-3 genes', '4-5 genes', '6-10 genes', '>10 genes']:
        if bin_name in count_bins:
            count = count_bins[bin_name]
            bar = '█' * (count // 2)
            print(f"  {bin_name:12s}: {count:4d} samples {bar}")

    # Show outliers
    outliers = [(sample, count) for sample, count in sample_gene_counts.most_common(5) if count > 10]
    if outliers:
        print(f"\n  🚨 Outlier Samples (>10 genes):")
        for sample, count in outliers:
            print(f"    {sample}: {count} genes")

    print(f"\n🔍 Interpretation:")
    mean_val = statistics.mean(gene_counts)
    max_val = max(gene_counts)

    if mean_val <= 3 and max_val <= 10:
        print(f"  ✅ EXPECTED - Most samples have 1-3 genes, no major outliers")
        status = "PASS"
    elif mean_val <= 5 and max_val <= 20:
        print(f"  ⚠️  MODERATE - Slightly higher than typical, but reasonable")
        status = "WARNING"
    else:
        print(f"  🚨 SUSPICIOUS - High gene counts or major outliers present")
        print(f"     Check outlier samples for false positives")
        status = "SUSPICIOUS"

    return status


def check_drug_classes(results):
    """
    Check drug class distribution

    Expected: Diverse classes (tetracycline, aminoglycoside, beta-lactam, etc.)
    Suspicious: Only one class or unusual classes
    """
    print("\n" + "="*80)
    print("CHECK 4: Drug Class Distribution")
    print("="*80)

    drug_classes = []
    for row in results:
        drug_class = row.get('class', '').strip()
        if drug_class and drug_class != 'None':
            drug_classes.append(drug_class)

    if not drug_classes:
        print("❌ No drug class information available")
        return "UNKNOWN"

    class_counts = Counter(drug_classes)

    print(f"\n💊 Drug Classes Found:")
    print(f"  Total classes: {len(class_counts)}")
    print(f"  Total genes: {len(drug_classes)}")

    print(f"\n  Distribution:")
    for drug_class, count in class_counts.most_common():
        pct = (count / len(drug_classes)) * 100
        bar = '█' * int(pct / 2)
        print(f"    {drug_class:30s}: {count:4d} ({pct:5.1f}%) {bar}")

    print(f"\n🔍 Interpretation:")
    if len(class_counts) >= 5:
        print(f"  ✅ DIVERSE - {len(class_counts)} drug classes represented")
        print(f"     Indicates genuine mobile AMR diversity")
        status = "PASS"
    elif len(class_counts) >= 3:
        print(f"  ⚠️  MODERATE - {len(class_counts)} drug classes")
        print(f"     Acceptable but less diverse than expected")
        status = "WARNING"
    elif len(class_counts) == 1:
        print(f"  🚨 SUSPICIOUS - Only 1 drug class found")
        print(f"     Unusual uniformity - may indicate contamination or artifact")
        status = "SUSPICIOUS"
    else:
        print(f"  ⚠️  LIMITED - {len(class_counts)} drug classes")
        status = "WARNING"

    return status


def generate_summary(check_results, results, output_file=None):
    """Generate overall summary and recommendations"""

    summary = []
    summary.append("\n" + "="*80)
    summary.append("OVERALL VALIDATION SUMMARY")
    summary.append("="*80)

    # Count statuses
    status_counts = Counter(check_results.values())

    summary.append(f"\n✅ Checks Passed: {status_counts.get('PASS', 0)}")
    summary.append(f"⚠️  Warnings: {status_counts.get('WARNING', 0)}")
    summary.append(f"🚨 Suspicious: {status_counts.get('SUSPICIOUS', 0)}")

    # Overall conclusion
    summary.append(f"\n🎯 OVERALL CONCLUSION:")

    if status_counts.get('SUSPICIOUS', 0) > 0:
        summary.append(f"  🚨 SUSPICIOUS - Some checks flagged serious concerns")
        summary.append(f"     Recommend manual validation of flagged samples")
        summary.append(f"     Consider re-running analysis or checking for artifacts")
    elif status_counts.get('WARNING', 0) > 1:
        summary.append(f"  ⚠️  CAUTION - Multiple warnings detected")
        summary.append(f"     Results may be valid but worth spot-checking")
        summary.append(f"     Consider manual validation of a few samples")
    else:
        summary.append(f"  ✅ PASSED - Results appear statistically reasonable")
        summary.append(f"     Findings are consistent with expected AMR-prophage biology")
        summary.append(f"     Safe to proceed with analysis")

    # Recommendations
    summary.append(f"\n📋 RECOMMENDATIONS:")
    summary.append(f"  1. Manual spot-check: Validate 5-10 samples with BLAST")
    summary.append(f"  2. Visualize gene context: Use visualize_amr_prophage_context.py")
    summary.append(f"  3. Literature comparison: Check if genes match published studies")
    summary.append(f"  4. Document validation: Include this report in supplementary data")

    summary.append(f"\n" + "="*80 + "\n")

    # Print summary
    for line in summary:
        print(line)

    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write('\n'.join(summary))
        print(f"✅ Summary saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate AMR-in-prophage results with statistical checks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single dataset
  %(prog)s method3_direct_scan.csv

  # Multiple datasets
  %(prog)s ecoli_2021/method3_direct_scan.csv ecoli_2022/method3_direct_scan.csv

  # With output
  %(prog)s results.csv --output validation_report.txt

Interpretation:
  PASS - Results look statistically reasonable
  WARNING - Minor concerns, consider spot-checking
  SUSPICIOUS - Serious concerns, recommend manual validation
        """
    )

    parser.add_argument('csv_files', nargs='+', help='Method 3 CSV result files')
    parser.add_argument('--output', '-o', help='Output file for summary report')

    args = parser.parse_args()

    # Parse all CSV files
    all_results = []
    for csv_file in args.csv_files:
        print(f"\n📂 Loading: {csv_file}")
        results = parse_method3_csv(csv_file)
        print(f"   Found {len(results)} AMR genes in prophages")
        all_results.extend(results)

    if not all_results:
        print("\n❌ No data to analyze")
        sys.exit(1)

    print(f"\n✅ Total AMR genes across all datasets: {len(all_results)}")

    # Run all checks
    check_results = {}
    check_results['proportion'] = check_proportion(all_results)
    check_results['gene_types'] = check_gene_types(all_results)
    check_results['distribution'] = check_sample_distribution(all_results)
    check_results['drug_classes'] = check_drug_classes(all_results)

    # Generate summary
    generate_summary(check_results, all_results, args.output)


if __name__ == '__main__':
    main()
