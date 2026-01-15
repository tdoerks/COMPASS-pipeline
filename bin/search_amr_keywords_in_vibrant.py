#!/usr/bin/env python3
"""
Search VIBRANT Prophage Annotations for AMR-Related Keywords

Since VIBRANT and AMRFinderPlus may use different gene names, this script
searches for general AMR-related keywords in VIBRANT annotations:
- resistance
- antibiotic
- multidrug
- efflux
- beta-lactam
- tetracycline
- aminoglycoside
- etc.

This will tell us if VIBRANT detected any AMR-related genes in prophages,
even if they're named differently than AMRFinderPlus.
"""

import sys
from pathlib import Path
from collections import defaultdict, Counter
import re

# AMR-related keywords to search for
AMR_KEYWORDS = [
    # General resistance terms
    'resistance', 'resistant', 'antibiotic', 'antimicrobial',
    'multidrug', 'MDR',

    # Mechanisms
    'efflux', 'pump',
    'beta-lactam', 'betalactam', 'β-lactam',
    'lactamase',

    # Drug classes
    'tetracycline', 'aminoglycoside', 'fluoroquinolone', 'quinolone',
    'macrolide', 'sulfonamide', 'trimethoprim', 'chloramphenicol',
    'fosfomycin', 'rifampin', 'colistin', 'polymyxin',

    # Specific mechanisms
    'acetyltransferase', 'methyltransferase', 'phosphotransferase',
    'nucleotidyltransferase',

    # Gene families
    'tet(', 'aac(', 'aph(', 'ant(',  # Common AMR gene prefixes
    'bla', 'CTX-M', 'NDM', 'KPC', 'OXA',  # Beta-lactamases
    'qnr', 'gyr', 'par',  # Quinolone resistance
    'erm', 'mef', 'mph',  # Macrolide resistance
    'sul', 'dfr',  # Sulfonamide/trimethoprim
    'mcr',  # Colistin resistance
]


def search_vibrant_for_amr_keywords(vibrant_dir, sample_id):
    """
    Search all VIBRANT annotation files for AMR-related keywords

    Returns: list of matches with {keyword, line, file, context}
    """
    matches = []

    sample_vibrant_dir = vibrant_dir / f"{sample_id}_vibrant" / f"VIBRANT_{sample_id}_contigs"

    if not sample_vibrant_dir.exists():
        print(f"  ⚠️  VIBRANT directory not found: {sample_vibrant_dir}")
        return matches

    # Get all text files to search
    annotation_files = []
    annotation_files.extend(sample_vibrant_dir.glob("**/*.tsv"))
    annotation_files.extend(sample_vibrant_dir.glob("**/*.txt"))
    annotation_files.extend(sample_vibrant_dir.glob("**/*.gff"))

    print(f"  Searching {len(annotation_files)} VIBRANT files for AMR keywords...")

    keyword_counts = Counter()

    for annot_file in annotation_files:
        try:
            with open(annot_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_lower = line.lower()

                    # Check each keyword
                    for keyword in AMR_KEYWORDS:
                        if keyword.lower() in line_lower:
                            matches.append({
                                'sample': sample_id,
                                'keyword': keyword,
                                'file': annot_file.name,
                                'line_number': line_num,
                                'context': line.strip()[:200],  # First 200 chars
                                'file_path': str(annot_file.relative_to(vibrant_dir))
                            })
                            keyword_counts[keyword] += 1

        except Exception as e:
            print(f"    ⚠️  Could not read {annot_file.name}: {e}")
            continue

    if keyword_counts:
        print(f"\n  ✅ Found AMR-related keywords:")
        for keyword, count in keyword_counts.most_common(10):
            print(f"    - '{keyword}': {count} occurrences")

    return matches


def analyze_sample(results_dir, sample_id, show_details=True):
    """Analyze a single sample"""

    results_dir = Path(results_dir)
    vibrant_dir = results_dir / "vibrant"

    print(f"\n{'='*80}")
    print(f"ANALYZING SAMPLE: {sample_id}")
    print(f"{'='*80}")

    # Search VIBRANT annotations
    matches = search_vibrant_for_amr_keywords(vibrant_dir, sample_id)

    if not matches:
        print(f"\n  ❌ No AMR-related keywords found in VIBRANT annotations")
        return []

    print(f"\n  ✅ Found {len(matches)} AMR-related annotations in VIBRANT files!")

    if show_details:
        print(f"\n  📝 Sample matches (showing first 20):")
        for i, match in enumerate(matches[:20], 1):
            print(f"    {i}. Keyword: '{match['keyword']}' in {match['file']}")
            print(f"       Context: {match['context'][:120]}...")

    return matches


def export_to_csv(matches, output_file):
    """Export matches to CSV"""
    import csv

    with open(output_file, 'w', newline='') as f:
        fieldnames = ['sample', 'keyword', 'file', 'line_number', 'context', 'file_path']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches)

    print(f"\n✅ Results exported to: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search_amr_keywords_in_vibrant.py <results_dir> [sample_id]")
        print("\nExamples:")
        print("  # Single sample:")
        print("  python3 search_amr_keywords_in_vibrant.py /path/to/results SRR13928113")
        print()
        print("  # All samples:")
        print("  python3 search_amr_keywords_in_vibrant.py /path/to/results")
        sys.exit(1)

    results_dir = Path(sys.argv[1])

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    vibrant_dir = results_dir / "vibrant"
    if not vibrant_dir.exists():
        print(f"❌ Error: VIBRANT directory not found: {vibrant_dir}")
        sys.exit(1)

    all_matches = []

    # Single sample mode
    if len(sys.argv) > 2:
        sample_id = sys.argv[2]
        matches = analyze_sample(results_dir, sample_id, show_details=True)
        all_matches.extend(matches)

    # All samples mode
    else:
        print(f"\n🔬 Searching all samples for AMR keywords in VIBRANT annotations...")
        vibrant_samples = sorted([d.name.replace('_vibrant', '')
                                 for d in vibrant_dir.glob('*_vibrant')])
        print(f"   Found {len(vibrant_samples)} samples with VIBRANT results\n")

        for i, sample_id in enumerate(vibrant_samples, 1):
            if i % 50 == 0:
                print(f"\n   Processed {i}/{len(vibrant_samples)} samples...\n")

            matches = analyze_sample(results_dir, sample_id, show_details=False)
            all_matches.extend(matches)

    # Print summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total AMR-related annotations found: {len(all_matches)}")

    if all_matches:
        # Count by keyword
        keyword_counts = Counter(m['keyword'] for m in all_matches)
        print(f"\nTop AMR keywords found:")
        for keyword, count in keyword_counts.most_common(15):
            print(f"  {keyword}: {count} occurrences")

        # Count by sample
        sample_counts = Counter(m['sample'] for m in all_matches)
        samples_with_amr = len(sample_counts)
        print(f"\nSamples with AMR-related annotations in prophages: {samples_with_amr}")

        print(f"\nTop samples with most AMR keywords:")
        for sample, count in sample_counts.most_common(10):
            print(f"  {sample}: {count} AMR-related annotations")

        # Export to CSV
        output_csv = Path.home() / "amr_keywords_in_vibrant.csv"
        export_to_csv(all_matches, output_csv)

        print(f"\n✅ CONCLUSION:")
        print(f"   VIBRANT detected AMR-related genes in {samples_with_amr} prophage/phage regions!")
        print(f"   This suggests prophages DO carry resistance-related genes,")
        print(f"   but they may be named differently than AMRFinderPlus genes.")

    else:
        print(f"\n❌ No AMR-related keywords found in VIBRANT annotations")
        print(f"\nThis suggests:")
        print(f"  - Prophages in this dataset don't carry resistance genes")
        print(f"  - OR VIBRANT doesn't annotate resistance genes with these keywords")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
