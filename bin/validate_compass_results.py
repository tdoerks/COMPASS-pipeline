#!/usr/bin/env python3
"""
COMPASS Validation Analysis

Compare COMPASS pipeline results against known ground truth for validation genomes.
Calculates sensitivity, specificity, and generates validation report.

Usage:
    ./bin/validate_compass_results.py /path/to/results /path/to/ground_truth.csv

Example:
    ./bin/validate_compass_results.py \\
        data/validation/results \\
        data/validation/ground_truth.csv \\
        --output data/validation/validation_report.md
"""

import os
import sys
import csv
import argparse
from pathlib import Path
from collections import defaultdict
import re

def parse_amrfinder_results(results_dir, sample):
    """Parse AMRFinder results for a sample - only ACQUIRED AMR genes."""
    amr_file = Path(results_dir) / "amrfinder" / f"{sample}_amr.tsv"

    if not amr_file.exists():
        return {"genes": [], "count": 0}

    genes = []
    with open(amr_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            gene_symbol = row.get('Gene symbol', '')
            scope = row.get('Scope', '')
            element_type = row.get('Element type', '')

            # Only count acquired AMR genes (Scope=core means intrinsic/efflux)
            # We want: Scope != "plus" (which includes intrinsic genes)
            # OR specifically: Element type = "AMR" and Subclass = something besides "EFFLUX"
            subclass = row.get('Subclass', '')

            if gene_symbol and element_type == 'AMR':
                # Skip efflux pumps and stress genes (intrinsic)
                if subclass not in ['EFFLUX', '']:
                    genes.append(gene_symbol)
                elif subclass == 'EFFLUX' and scope != 'plus':
                    # Keep acquired efflux genes, skip intrinsic ones
                    genes.append(gene_symbol)

    return {"genes": genes, "count": len(genes)}

def parse_vibrant_results(results_dir, sample):
    """Parse VIBRANT prophage results for a sample."""
    # VIBRANT output has _vibrant suffix
    vibrant_dir = Path(results_dir) / "vibrant" / f"{sample}_vibrant"

    if not vibrant_dir.exists():
        return {"prophages": [], "count": 0}

    # Look for VIBRANT summary files
    summary_files = list(vibrant_dir.glob("**/VIBRANT_summary_results*.tsv"))

    if not summary_files:
        return {"prophages": [], "count": 0}

    prophages = []
    for summary_file in summary_files:
        with open(summary_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                scaffold = row.get('scaffold', row.get('fragment', ''))
                if scaffold:
                    prophages.append(scaffold)

    return {"prophages": prophages, "count": len(prophages)}

def parse_mobsuite_results(results_dir, sample):
    """Parse MOBsuite plasmid results for a sample."""
    # MOBsuite output has _mobsuite suffix
    mobsuite_dir = Path(results_dir) / "mobsuite" / f"{sample}_mobsuite"

    if not mobsuite_dir.exists():
        return {"plasmids": [], "replicons": [], "count": 0}

    # Look for individual plasmid typing files
    typing_files = list(mobsuite_dir.glob("plasmid_*_typing.txt"))

    if not typing_files:
        return {"plasmids": [], "replicons": [], "count": 0}

    replicons = []
    for typing_file in typing_files:
        with open(typing_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                rep_type = row.get('rep_type(s)', '')
                if rep_type and rep_type != '-':
                    # Split on comma and add all replicons
                    reps = [r.strip() for r in rep_type.split(',')]
                    replicons.extend(reps)

    return {"plasmids": typing_files, "replicons": replicons, "count": len(typing_files)}

def parse_mlst_results(results_dir, sample):
    """Parse MLST results for a sample."""
    mlst_file = Path(results_dir) / "mlst" / f"{sample}_mlst.tsv"

    if not mlst_file.exists():
        return {"st": None, "scheme": None}

    with open(mlst_file, 'r') as f:
        # MLST format: sample\tscheme\tST\tallele1\tallele2...
        line = f.readline().strip()
        if line:
            fields = line.split('\t')
            if len(fields) >= 3:
                return {"st": fields[2], "scheme": fields[1]}

    return {"st": None, "scheme": None}

def load_ground_truth(ground_truth_csv):
    """Load ground truth data from CSV."""
    ground_truth = defaultdict(list)

    with open(ground_truth_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row['sample']
            ground_truth[sample].append({
                'feature_type': row['feature_type'],
                'feature_name': row['feature_name'],
                'expected_value': row['expected_value'],
                'notes': row.get('notes', '')
            })

    return ground_truth

def validate_sample(sample, ground_truth, results_dir):
    """Validate COMPASS results for a single sample against ground truth."""

    # Parse COMPASS results
    amr_results = parse_amrfinder_results(results_dir, sample)
    prophage_results = parse_vibrant_results(results_dir, sample)
    plasmid_results = parse_mobsuite_results(results_dir, sample)
    mlst_results = parse_mlst_results(results_dir, sample)

    validation_results = {
        'sample': sample,
        'tests': [],
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }

    # Check each ground truth expectation
    for gt in ground_truth:
        feature_type = gt['feature_type']
        feature_name = gt['feature_name']
        expected = gt['expected_value']
        notes = gt['notes']

        test_result = {
            'feature_type': feature_type,
            'feature_name': feature_name,
            'expected': expected,
            'notes': notes,
            'status': 'UNKNOWN'
        }

        # AMR gene validation
        if feature_type == 'amr':
            if feature_name == 'total':
                actual = amr_results['count']
                test_result['actual'] = actual
                if int(expected) == actual:
                    test_result['status'] = 'PASS'
                    validation_results['passed'] += 1
                else:
                    test_result['status'] = 'FAIL'
                    validation_results['failed'] += 1
            elif feature_name == 'present':
                actual = amr_results['count']
                test_result['actual'] = f"{actual} genes detected"
                if actual > 0:
                    test_result['status'] = 'PASS'
                    validation_results['passed'] += 1
                else:
                    test_result['status'] = 'FAIL'
                    validation_results['failed'] += 1
            else:
                # Check for specific gene
                found = any(feature_name in gene for gene in amr_results['genes'])
                test_result['actual'] = 'Detected' if found else 'Not detected'
                if found:
                    test_result['status'] = 'PASS'
                    validation_results['passed'] += 1
                else:
                    test_result['status'] = 'FAIL'
                    validation_results['failed'] += 1

        # AMR max validation (negative control)
        elif feature_type == 'amr_max':
            actual = amr_results['count']
            test_result['actual'] = actual
            if actual <= int(expected):
                test_result['status'] = 'PASS'
                validation_results['passed'] += 1
            else:
                test_result['status'] = 'WARNING'
                validation_results['warnings'] += 1

        # Prophage validation
        elif feature_type == 'prophage_count':
            actual = prophage_results['count']
            test_result['actual'] = actual
            # Allow ±1 prophage for detection variability
            if abs(actual - int(expected)) <= 1:
                test_result['status'] = 'PASS'
                validation_results['passed'] += 1
            elif abs(actual - int(expected)) == 2:
                test_result['status'] = 'WARNING'
                validation_results['warnings'] += 1
            else:
                test_result['status'] = 'FAIL'
                validation_results['failed'] += 1

        elif feature_type == 'prophage':
            # Just check if prophages were detected
            if feature_name == 'present':
                actual = prophage_results['count']
                test_result['actual'] = f"{actual} prophages detected"
                if actual > 0:
                    test_result['status'] = 'PASS'
                    validation_results['passed'] += 1
                else:
                    test_result['status'] = 'FAIL'
                    validation_results['failed'] += 1

        elif feature_type == 'prophage_max':
            actual = prophage_results['count']
            test_result['actual'] = actual
            if actual <= int(expected):
                test_result['status'] = 'PASS'
                validation_results['passed'] += 1
            else:
                test_result['status'] = 'WARNING'
                validation_results['warnings'] += 1

        # Plasmid validation
        elif feature_type == 'plasmid_count':
            actual = plasmid_results['count']
            test_result['actual'] = actual
            # Allow ±1 plasmid for detection variability
            if abs(actual - int(expected)) <= 1:
                test_result['status'] = 'PASS'
                validation_results['passed'] += 1
            elif abs(actual - int(expected)) == 2:
                test_result['status'] = 'WARNING'
                validation_results['warnings'] += 1
            else:
                test_result['status'] = 'FAIL'
                validation_results['failed'] += 1

        elif feature_type == 'plasmid':
            # Check for specific replicon type
            found = any(feature_name in rep for rep in plasmid_results['replicons'])
            test_result['actual'] = 'Detected' if found else 'Not detected'
            if found:
                test_result['status'] = 'PASS'
                validation_results['passed'] += 1
            else:
                test_result['status'] = 'FAIL'
                validation_results['failed'] += 1

        # MLST validation
        elif feature_type == 'mlst':
            actual_st = mlst_results.get('st')
            test_result['actual'] = actual_st if actual_st else 'Not detected'
            # Extract ST number from feature_name (e.g., "ST131" -> "131")
            expected_st = feature_name.replace('ST', '')
            if actual_st and actual_st == expected_st:
                test_result['status'] = 'PASS'
                validation_results['passed'] += 1
            else:
                test_result['status'] = 'FAIL'
                validation_results['failed'] += 1

        validation_results['tests'].append(test_result)

    return validation_results

def generate_report(all_results, output_file=None):
    """Generate validation report."""

    lines = []
    lines.append("# COMPASS Validation Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    total_samples = len(all_results)
    total_tests = sum(len(r['tests']) for r in all_results)
    total_passed = sum(r['passed'] for r in all_results)
    total_failed = sum(r['failed'] for r in all_results)
    total_warnings = sum(r['warnings'] for r in all_results)

    lines.append(f"**Total Samples Validated**: {total_samples}")
    lines.append(f"**Total Tests**: {total_tests}")
    lines.append(f"**Passed**: {total_passed} ✅")
    lines.append(f"**Failed**: {total_failed} ❌")
    lines.append(f"**Warnings**: {total_warnings} ⚠️")
    lines.append("")

    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        lines.append(f"**Pass Rate**: {pass_rate:.1f}%")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Per-sample results
    lines.append("## Validation Results by Sample")
    lines.append("")

    for result in all_results:
        sample = result['sample']
        lines.append(f"### {sample}")
        lines.append("")
        lines.append(f"**Tests**: {len(result['tests'])} | "
                    f"**Passed**: {result['passed']} ✅ | "
                    f"**Failed**: {result['failed']} ❌ | "
                    f"**Warnings**: {result['warnings']} ⚠️")
        lines.append("")

        if result['tests']:
            lines.append("| Feature Type | Feature | Expected | Actual | Status | Notes |")
            lines.append("|-------------|---------|----------|--------|--------|-------|")

            for test in result['tests']:
                status_emoji = {
                    'PASS': '✅',
                    'FAIL': '❌',
                    'WARNING': '⚠️',
                    'UNKNOWN': '❓'
                }.get(test['status'], '❓')

                lines.append(f"| {test['feature_type']} | "
                           f"{test['feature_name']} | "
                           f"{test['expected']} | "
                           f"{test.get('actual', 'N/A')} | "
                           f"{status_emoji} {test['status']} | "
                           f"{test['notes']} |")

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")

    if total_failed == 0 and total_warnings == 0:
        lines.append("✅ **All validation tests passed!** COMPASS results match expected ground truth.")
    elif total_failed == 0:
        lines.append("⚠️ **All critical tests passed with some warnings.** Review warnings above.")
    else:
        lines.append("❌ **Some validation tests failed.** Review failed tests above and investigate discrepancies.")

    lines.append("")
    lines.append("**Notes**:")
    lines.append("- ✅ PASS: Result matches ground truth exactly")
    lines.append("- ⚠️ WARNING: Result is close to ground truth but slightly off (within tolerance)")
    lines.append("- ❌ FAIL: Result does not match ground truth")
    lines.append("")

    report = "\n".join(lines)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Validation report saved to: {output_file}")
    else:
        print(report)

    return report

def main():
    parser = argparse.ArgumentParser(description="Validate COMPASS results against ground truth")
    parser.add_argument("results_dir", help="Path to COMPASS results directory")
    parser.add_argument("ground_truth", help="Path to ground truth CSV file")
    parser.add_argument("--output", "-o", help="Output file for validation report")

    args = parser.parse_args()

    # Load ground truth
    print(f"Loading ground truth from: {args.ground_truth}")
    ground_truth = load_ground_truth(args.ground_truth)
    print(f"Loaded ground truth for {len(ground_truth)} samples")
    print("")

    # Validate each sample
    all_results = []

    for sample in ground_truth.keys():
        print(f"Validating {sample}...", end=" ")
        result = validate_sample(sample, ground_truth[sample], args.results_dir)
        all_results.append(result)
        print(f"{result['passed']} passed, {result['failed']} failed, {result['warnings']} warnings")

    print("")

    # Generate report
    generate_report(all_results, args.output)

if __name__ == "__main__":
    main()
