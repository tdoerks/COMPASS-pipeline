#!/usr/bin/env python3
"""
Search VIBRANT Prophage Annotations for AMR Genes

This script takes a different approach to finding AMR genes in prophages:
1. Get AMR gene names from AMRFinderPlus results
2. Search VIBRANT's annotation files for those specific gene names
3. If VIBRANT annotated the AMR gene within a prophage region → it's co-located!

This complements the coordinate-based approach by using VIBRANT's own gene annotations.
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict
import re

def parse_amr_genes(amr_file):
    """
    Parse AMRFinderPlus to get list of AMR gene names

    Returns: list of dicts with {gene, class, subclass, contig, start, end}
    """
    amr_genes = []

    if not Path(amr_file).exists():
        return amr_genes

    with open(amr_file) as f:
        header = next(f, None)
        if not header:
            return amr_genes

        for line in f:
            if line.startswith('#'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 11:
                continue

            gene_symbol = parts[5]
            element_type = parts[8]

            # Only AMR genes (not virulence, stress, etc.)
            if element_type != 'AMR' or gene_symbol == 'NA':
                continue

            amr_genes.append({
                'gene': gene_symbol,
                'class': parts[10] if len(parts) > 10 else '',
                'subclass': parts[11] if len(parts) > 11 else '',
                'contig': parts[1],
                'start': int(parts[2]),
                'end': int(parts[3])
            })

    return amr_genes


def search_vibrant_annotations(vibrant_dir, sample_id, amr_gene_names):
    """
    Search VIBRANT annotation files for specific AMR gene names

    VIBRANT creates several annotation files:
    - VIBRANT_annotations_*.tsv (main gene annotations)
    - VIBRANT_genome_quality_*.tsv (quality info)
    - Various HMM tables

    Returns: list of matches with {gene, prophage_id, annotation, file}
    """
    matches = []

    sample_vibrant_dir = vibrant_dir / f"{sample_id}_vibrant" / f"VIBRANT_{sample_id}_contigs"

    if not sample_vibrant_dir.exists():
        print(f"  ⚠️  VIBRANT directory not found: {sample_vibrant_dir}")
        return matches

    # Search in all TSV files
    annotation_files = list(sample_vibrant_dir.glob("**/*.tsv"))

    print(f"  Searching {len(annotation_files)} VIBRANT annotation files...")

    for annot_file in annotation_files:
        try:
            with open(annot_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Search for each AMR gene name
                for gene_name in amr_gene_names:
                    # Create regex pattern that matches the gene name
                    # Handle special characters in gene names like tet(A), aac(3)-IId
                    escaped_gene = re.escape(gene_name)
                    pattern = re.compile(rf'\b{escaped_gene}\b', re.IGNORECASE)

                    if pattern.search(content):
                        matches.append({
                            'gene': gene_name,
                            'file': annot_file.name,
                            'file_path': str(annot_file.relative_to(vibrant_dir)),
                            'sample': sample_id
                        })
                        print(f"    ✓ Found '{gene_name}' in {annot_file.name}")

        except Exception as e:
            print(f"    ⚠️  Could not read {annot_file.name}: {e}")
            continue

    # Also search in GFF file for gene annotations
    gff_file = sample_vibrant_dir / f"{sample_id}_contigs.prodigal.gff"
    if gff_file.exists():
        try:
            with open(gff_file, 'r') as f:
                content = f.read()
                for gene_name in amr_gene_names:
                    escaped_gene = re.escape(gene_name)
                    pattern = re.compile(rf'\b{escaped_gene}\b', re.IGNORECASE)

                    if pattern.search(content):
                        matches.append({
                            'gene': gene_name,
                            'file': gff_file.name,
                            'file_path': str(gff_file.relative_to(vibrant_dir)),
                            'sample': sample_id
                        })
                        print(f"    ✓ Found '{gene_name}' in {gff_file.name}")
        except Exception as e:
            print(f"    ⚠️  Could not read GFF: {e}")

    return matches


def get_prophage_context(vibrant_dir, sample_id, gene_name):
    """
    Try to determine which prophage region contains the gene

    Returns: dict with prophage info if found
    """
    sample_vibrant_dir = vibrant_dir / f"{sample_id}_vibrant" / f"VIBRANT_{sample_id}_contigs"

    # Check if gene is in phages FASTA (means it's in a prophage)
    phages_fasta = vibrant_dir / f"{sample_id}_phages.fna"
    if phages_fasta.exists():
        try:
            with open(phages_fasta, 'r') as f:
                current_prophage = None
                for line in f:
                    if line.startswith('>'):
                        current_prophage = line.strip()[1:].split()[0]
                    elif gene_name.lower() in line.lower():
                        return {'prophage_id': current_prophage, 'found_in_fasta': True}
        except Exception as e:
            pass

    return {'prophage_id': 'Unknown', 'found_in_fasta': False}


def analyze_sample(results_dir, sample_id):
    """Analyze a single sample"""

    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"

    amr_file = amr_dir / f"{sample_id}_amr.tsv"

    print(f"\n{'='*80}")
    print(f"ANALYZING SAMPLE: {sample_id}")
    print(f"{'='*80}")

    # Parse AMR genes
    amr_genes = parse_amr_genes(amr_file)

    if not amr_genes:
        print(f"  ⚠️  No AMR genes found in {amr_file}")
        return []

    print(f"  Found {len(amr_genes)} AMR genes in AMRFinderPlus results:")
    amr_gene_names = set()
    for gene in amr_genes:
        print(f"    - {gene['gene']} ({gene['class']})")
        amr_gene_names.add(gene['gene'])

    # Search VIBRANT annotations
    print(f"\n  Searching VIBRANT annotations for these genes...")
    matches = search_vibrant_annotations(vibrant_dir, sample_id, amr_gene_names)

    if not matches:
        print(f"\n  ❌ None of the AMR genes were found in VIBRANT prophage annotations")
        return []

    print(f"\n  ✅ Found {len(matches)} matches in VIBRANT annotations!")

    # Enrich matches with prophage context
    enriched_matches = []
    for match in matches:
        context = get_prophage_context(vibrant_dir, sample_id, match['gene'])
        match.update(context)

        # Get AMR gene details
        gene_details = next((g for g in amr_genes if g['gene'] == match['gene']), {})
        match.update({
            'class': gene_details.get('class', ''),
            'subclass': gene_details.get('subclass', ''),
            'amr_contig': gene_details.get('contig', ''),
            'amr_start': gene_details.get('start', ''),
            'amr_end': gene_details.get('end', '')
        })

        enriched_matches.append(match)

    return enriched_matches


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search_amr_in_vibrant_annotations.py <results_dir> [sample_id]")
        print("\nExamples:")
        print("  # Single sample:")
        print("  python3 search_amr_in_vibrant_annotations.py /path/to/results SRR13928113")
        print()
        print("  # All samples:")
        print("  python3 search_amr_in_vibrant_annotations.py /path/to/results")
        sys.exit(1)

    results_dir = Path(sys.argv[1])

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    amr_dir = results_dir / "amrfinder"
    if not amr_dir.exists():
        print(f"❌ Error: AMRFinder directory not found: {amr_dir}")
        sys.exit(1)

    all_matches = []

    # Single sample mode
    if len(sys.argv) > 2:
        sample_id = sys.argv[2]
        matches = analyze_sample(results_dir, sample_id)
        all_matches.extend(matches)

    # All samples mode
    else:
        print(f"\n🔬 Searching all samples for AMR genes in VIBRANT annotations...")
        amr_files = sorted(amr_dir.glob("*_amr.tsv"))
        print(f"   Found {len(amr_files)} samples\n")

        for i, amr_file in enumerate(amr_files, 1):
            sample_id = amr_file.stem.replace('_amr', '')

            if i % 50 == 0:
                print(f"\n   Processed {i}/{len(amr_files)} samples...\n")

            matches = analyze_sample(results_dir, sample_id)
            all_matches.extend(matches)

    # Print summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total matches: {len(all_matches)}")

    if all_matches:
        print(f"\nAMR genes found in VIBRANT prophage annotations:")

        # Count by gene
        gene_counts = defaultdict(int)
        for match in all_matches:
            gene_counts[match['gene']] += 1

        for gene, count in sorted(gene_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {gene}: {count} samples")

        # Export to CSV
        output_csv = Path.home() / "amr_in_vibrant_annotations.csv"
        with open(output_csv, 'w', newline='') as f:
            fieldnames = ['sample', 'gene', 'class', 'subclass', 'file',
                         'prophage_id', 'found_in_fasta', 'amr_contig',
                         'amr_start', 'amr_end', 'file_path']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_matches)

        print(f"\n✅ Results exported to: {output_csv}")
    else:
        print(f"\n❌ No AMR genes found in VIBRANT annotations across any samples")
        print(f"\nThis suggests:")
        print(f"  - AMR genes are truly not located within prophage regions")
        print(f"  - OR VIBRANT doesn't annotate AMR genes with the same names as AMRFinderPlus")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
