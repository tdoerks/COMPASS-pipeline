#!/usr/bin/env python3
"""
Assess Prophage Genome Completeness from VIBRANT Output

Questions to answer:
1. Are we getting full prophage genomes or just gene predictions?
2. What's the size distribution of prophages?
3. Are prophages circular or linear fragments?
4. Quality metrics for each prophage

Outputs:
- Completeness report (HTML + CSV)
- Size distribution plots
- Recommendations for downstream analysis
"""

import os
import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
from Bio import SeqIO
import statistics

def analyze_vibrant_output(vibrant_dir):
    """
    Analyze VIBRANT output to assess prophage completeness

    VIBRANT outputs:
    - *.phages_combined.fna - All predicted prophages
    - prophages/*.fasta - Individual prophage sequences
    - *.gff - Gene annotations
    """
    print(f"Analyzing VIBRANT output in {vibrant_dir}...")

    results = []

    # Find all sample directories
    vibrant_path = Path(vibrant_dir)
    if not vibrant_path.exists():
        print(f"Error: {vibrant_dir} not found")
        return results

    # Look for VIBRANT output directories
    for sample_dir in vibrant_path.iterdir():
        if not sample_dir.is_dir():
            continue

        sample_id = sample_dir.name

        # Find phages_combined.fna file
        phage_files = list(sample_dir.rglob("*.phages_combined.fna"))

        if not phage_files:
            print(f"  {sample_id}: No prophages found")
            continue

        for phage_file in phage_files:
            print(f"  Analyzing {sample_id}...")

            # Parse prophage sequences
            for record in SeqIO.parse(phage_file, "fasta"):
                prophage_id = record.id
                sequence_length = len(record.seq)

                # Check if description has fragment info
                description = record.description

                # VIBRANT naming: usually includes contig and coordinates
                # Example: NODE_1_fragment_1
                is_fragment = "fragment" in prophage_id.lower()

                # Estimate completeness based on size
                # Typical prophage: 20-60 kb
                # Small fragments: < 10 kb
                # Large complete: > 15 kb
                if sequence_length < 10000:
                    completeness = "Fragment/Incomplete"
                    quality = "Low"
                elif sequence_length < 15000:
                    completeness = "Partial"
                    quality = "Medium"
                elif sequence_length < 60000:
                    completeness = "Likely Complete"
                    quality = "High"
                else:
                    completeness = "Large/Complex"
                    quality = "High"

                # Check for circularity markers
                # (VIBRANT doesn't explicitly mark this, but can check sequence)
                is_circular = check_circularity(record.seq)

                results.append({
                    'sample_id': sample_id,
                    'prophage_id': prophage_id,
                    'length': sequence_length,
                    'is_fragment': is_fragment,
                    'completeness': completeness,
                    'quality': quality,
                    'is_circular': is_circular,
                    'description': description
                })

    print(f"\nTotal prophages analyzed: {len(results)}")
    return results


def check_circularity(seq, overlap_len=50):
    """
    Check if sequence might be circular by comparing ends
    """
    if len(seq) < overlap_len * 2:
        return False

    start = str(seq[:overlap_len])
    end = str(seq[-overlap_len:])

    # Simple check: do ends match? (real circularity check is more complex)
    similarity = sum(1 for a, b in zip(start, end) if a == b) / overlap_len

    return similarity > 0.9  # 90% similarity at ends


def generate_summary_stats(results):
    """Calculate summary statistics"""

    if not results:
        return {}

    lengths = [r['length'] for r in results]

    completeness_counts = Counter(r['completeness'] for r in results)
    quality_counts = Counter(r['quality'] for r in results)
    circular_count = sum(1 for r in results if r['is_circular'])
    fragment_count = sum(1 for r in results if r['is_fragment'])

    return {
        'total_prophages': len(results),
        'total_samples': len(set(r['sample_id'] for r in results)),
        'mean_length': statistics.mean(lengths),
        'median_length': statistics.median(lengths),
        'min_length': min(lengths),
        'max_length': max(lengths),
        'completeness_distribution': dict(completeness_counts),
        'quality_distribution': dict(quality_counts),
        'circular_count': circular_count,
        'circular_pct': circular_count / len(results) * 100,
        'fragment_count': fragment_count,
        'fragment_pct': fragment_count / len(results) * 100,
        'complete_count': completeness_counts.get('Likely Complete', 0) + completeness_counts.get('Large/Complex', 0),
        'complete_pct': (completeness_counts.get('Likely Complete', 0) + completeness_counts.get('Large/Complex', 0)) / len(results) * 100
    }


def generate_html_report(results, summary, output_file):
    """Generate HTML report with completeness assessment"""

    print(f"\nGenerating report: {output_file}")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prophage Genome Completeness Assessment</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .content {{ padding: 40px; }}
        h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card h4 {{ font-size: 0.9em; opacity: 0.9; margin-bottom: 10px; }}
        .stat-card .value {{ font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }}
        .alert-box {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .info-box {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .success-box {{
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        tbody tr:hover {{ background: #f7fafc; }}
        .quality-high {{ color: #10b981; font-weight: bold; }}
        .quality-medium {{ color: #f59e0b; font-weight: bold; }}
        .quality-low {{ color: #ef4444; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 Prophage Genome Completeness Assessment</h1>
            <p>VIBRANT Output Analysis - Kansas E. coli</p>
        </header>

        <div class="content">
            <section>
                <h2>📊 Summary Statistics</h2>

                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Total Prophages</h4>
                        <div class="value">{summary['total_prophages']}</div>
                        <p>Across {summary['total_samples']} samples</p>
                    </div>
                    <div class="stat-card">
                        <h4>Likely Complete</h4>
                        <div class="value">{summary['complete_pct']:.1f}%</div>
                        <p>{summary['complete_count']} prophages</p>
                    </div>
                    <div class="stat-card">
                        <h4>Mean Length</h4>
                        <div class="value">{summary['mean_length']/1000:.1f}kb</div>
                        <p>Median: {summary['median_length']/1000:.1f}kb</p>
                    </div>
                    <div class="stat-card">
                        <h4>Circular</h4>
                        <div class="value">{summary['circular_pct']:.1f}%</div>
                        <p>{summary['circular_count']} prophages</p>
                    </div>
                </div>

                <div class="{'success-box' if summary['complete_pct'] > 50 else 'alert-box'}">
                    <h3>🔍 Assessment</h3>
                    <p><strong>Genome Completeness:</strong> {summary['complete_pct']:.1f}% of prophages appear to be complete or near-complete (>15kb)</p>
                    <p><strong>Fragments:</strong> {summary['fragment_pct']:.1f}% are small fragments (<10kb)</p>
                    <p><strong>Circularity:</strong> {summary['circular_pct']:.1f}% show evidence of circular genomes</p>
                </div>

                <h3>Completeness Distribution</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for category, count in summary['completeness_distribution'].items():
        pct = count / summary['total_prophages'] * 100
        html += f"""
                        <tr>
                            <td><strong>{category}</strong></td>
                            <td>{count}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

    html += f"""
                    </tbody>
                </table>

                <h3>Size Distribution</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Size Range</th>
                            <th>Count</th>
                            <th>Typical Classification</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>&lt; 10 kb</td>
                            <td>{sum(1 for r in results if r['length'] < 10000)}</td>
                            <td>Fragment/Incomplete</td>
                        </tr>
                        <tr>
                            <td>10-15 kb</td>
                            <td>{sum(1 for r in results if 10000 <= r['length'] < 15000)}</td>
                            <td>Partial prophage</td>
                        </tr>
                        <tr>
                            <td>15-30 kb</td>
                            <td>{sum(1 for r in results if 15000 <= r['length'] < 30000)}</td>
                            <td>Small complete prophage</td>
                        </tr>
                        <tr>
                            <td>30-60 kb</td>
                            <td>{sum(1 for r in results if 30000 <= r['length'] < 60000)}</td>
                            <td>Typical complete prophage</td>
                        </tr>
                        <tr>
                            <td>&gt; 60 kb</td>
                            <td>{sum(1 for r in results if r['length'] >= 60000)}</td>
                            <td>Large/jumbo prophage</td>
                        </tr>
                    </tbody>
                </table>

                <h2>🎯 Recommendations for Analysis</h2>

                <div class="info-box">
                    <h4>Can we do phylogeny?</h4>
                    <p><strong>{'YES' if summary['complete_pct'] > 30 else 'LIMITED'}</strong> - {summary['complete_pct']:.1f}% of prophages are complete enough for phylogenetic analysis.</p>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        <li>Use prophages &gt;15kb for phylogeny</li>
                        <li>Exclude fragments &lt;10kb</li>
                        <li>Total suitable: {summary['complete_count']} prophages</li>
                    </ul>
                </div>

                <div class="info-box">
                    <h4>What are we actually getting from VIBRANT?</h4>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        <li><strong>Gene predictions:</strong> ✅ Yes - VIBRANT identifies prophage genes</li>
                        <li><strong>Prophage boundaries:</strong> ✅ Yes - but may be inaccurate ({summary['fragment_pct']:.1f}% are small fragments)</li>
                        <li><strong>Complete genomes:</strong> {'✅' if summary['complete_pct'] > 50 else '⚠️'} Partial - {summary['complete_pct']:.1f}% appear complete</li>
                        <li><strong>Circular genomes:</strong> ⚠️ Limited - {summary['circular_pct']:.1f}% show circularity</li>
                    </ul>
                </div>

                <div class="alert-box">
                    <h4>⚠️ Important Notes</h4>
                    <p><strong>VIBRANT provides:</strong> Prophage gene predictions and estimated boundaries, NOT fully assembled circular phage genomes.</p>
                    <p><strong>For complete genomes:</strong> Use viralFlye (v1.3-dev branch) to assemble actual circular viral genomes from reads.</p>
                    <p><strong>For better boundaries:</strong> Use PhiSpy/PHASTER (v1.3-dev branch) for more accurate prophage coordinates.</p>
                </div>

                <h2>📋 Next Steps</h2>
                <ol style="line-height: 2; margin-left: 30px;">
                    <li><strong>Phylogeny:</strong> Can proceed with {summary['complete_count']} complete prophages (&gt;15kb)</li>
                    <li><strong>Diversity analysis:</strong> Use all prophages, but weight by completeness</li>
                    <li><strong>Movement tracking:</strong> Can track prophages across samples using gene content</li>
                    <li><strong>For publication:</strong> Consider running viralFlye on subset for true complete genomes</li>
                </ol>
            </section>
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Report generated: {output_file}")


def save_csv(results, output_file):
    """Save detailed results to CSV"""

    with open(output_file, 'w', newline='') as f:
        fieldnames = ['sample_id', 'prophage_id', 'length', 'is_fragment',
                     'completeness', 'quality', 'is_circular', 'description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ CSV saved: {output_file}")


def main():
    # Paths
    vibrant_dir = os.path.expanduser('~/compass_kansas_results/results_kansas_*/vibrant')
    output_html = os.path.expanduser('~/compass_kansas_results/publication_analysis/reports/PROPHAGE_COMPLETENESS_ASSESSMENT.html')
    output_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/prophage_completeness.csv')

    print("=" * 70)
    print("Prophage Genome Completeness Assessment")
    print("=" * 70)

    # Analyze VIBRANT output
    results = analyze_vibrant_output(vibrant_dir)

    if not results:
        print("\n⚠️  No prophages found. Check VIBRANT output directory.")
        return

    # Calculate summary stats
    summary = generate_summary_stats(results)

    # Generate reports
    generate_html_report(results, summary, output_html)
    save_csv(results, output_csv)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   Total prophages: {summary['total_prophages']}")
    print(f"   Likely complete: {summary['complete_pct']:.1f}%")
    print(f"   Mean length: {summary['mean_length']/1000:.1f} kb")
    print(f"   Circular: {summary['circular_pct']:.1f}%")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
