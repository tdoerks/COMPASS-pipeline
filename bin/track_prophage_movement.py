#!/usr/bin/env python3
"""
Track Prophage Movement Across Samples, Time, and Species

Questions to answer:
1. Which prophages appear in multiple samples?
2. Do prophages move across years?
3. Do prophages cross species boundaries (E. coli, Salmonella, Campylobacter)?
4. Geographic movement (if data available)

Outputs:
- Movement tracking report (HTML)
- Shared prophage matrix (CSV)
- Temporal tracking table
"""

import csv
import os
from collections import defaultdict, Counter
from pathlib import Path

def load_metadata(base_dir):
    """Load sample metadata from filtered_samples.csv files"""
    print("Loading sample metadata...")

    metadata = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        metadata_file = base_path / f"results_kansas_{year}" / "filtered_samples" / "filtered_samples.csv"

        if not metadata_file.exists():
            continue

        with open(metadata_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                srr_id = row['Run']
                metadata[srr_id] = {
                    'year': year,
                    'organism': row.get('organism', 'Unknown'),
                    'sample_name': row.get('SampleName', '')
                }

    print(f"  Loaded {len(metadata)} samples")
    return metadata


def load_prophage_data(colocation_csv):
    """Load prophage data from co-location analysis"""
    print(f"Loading prophage data from {colocation_csv}...")

    # prophage_id -> list of samples
    prophage_samples = defaultdict(set)

    # sample -> list of prophages
    sample_prophages = defaultdict(set)

    with open(colocation_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row['sample']
            prophage_id = row.get('prophage_id', '')

            if prophage_id and prophage_id != 'None' and prophage_id != '':
                prophage_samples[prophage_id].add(sample)
                sample_prophages[sample].add(prophage_id)

    print(f"  Found {len(prophage_samples)} unique prophages")
    print(f"  Found {len(sample_prophages)} samples with prophages")

    return prophage_samples, sample_prophages


def track_prophage_movement(prophage_samples, metadata):
    """Track prophage movement across samples, time, species"""
    print("\nTracking prophage movement...")

    movement_data = []

    for prophage_id, samples in prophage_samples.items():
        if len(samples) < 2:
            continue  # Skip prophages in only 1 sample

        # Get metadata for all samples with this prophage
        years = set()
        organisms = set()
        sample_names = []

        for sample in samples:
            if sample in metadata:
                years.add(metadata[sample]['year'])
                organisms.add(metadata[sample]['organism'])
                sample_names.append(metadata[sample]['sample_name'])

        # Determine movement type
        crosses_years = len(years) > 1
        crosses_species = len(organisms) > 1

        movement_data.append({
            'prophage_id': prophage_id,
            'sample_count': len(samples),
            'years': sorted(years),
            'year_count': len(years),
            'organisms': sorted(organisms),
            'organism_count': len(organisms),
            'crosses_years': crosses_years,
            'crosses_species': crosses_species,
            'sample_names': sample_names[:5]  # First 5 samples
        })

    # Sort by sample count (most widespread first)
    movement_data.sort(key=lambda x: x['sample_count'], reverse=True)

    print(f"  Tracked {len(movement_data)} prophages appearing in multiple samples")

    return movement_data


def generate_summary_stats(movement_data):
    """Calculate summary statistics"""

    total_shared = len(movement_data)
    crosses_years_count = sum(1 for p in movement_data if p['crosses_years'])
    crosses_species_count = sum(1 for p in movement_data if p['crosses_species'])

    max_samples = max(p['sample_count'] for p in movement_data) if movement_data else 0

    return {
        'total_shared_prophages': total_shared,
        'crosses_years': crosses_years_count,
        'crosses_years_pct': crosses_years_count / total_shared * 100 if total_shared > 0 else 0,
        'crosses_species': crosses_species_count,
        'crosses_species_pct': crosses_species_count / total_shared * 100 if total_shared > 0 else 0,
        'max_sample_count': max_samples
    }


def generate_html_report(movement_data, summary, output_file):
    """Generate HTML report"""

    print(f"\nGenerating report: {output_file}")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Prophage Movement Tracking</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .content {{ padding: 40px; }}
        h2 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
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
        }}
        .stat-card .value {{ font-size: 2.5em; font-weight: bold; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        tbody tr:hover {{ background: #f7fafc; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            margin: 2px;
        }}
        .badge-year {{ background: #dbeafe; color: #1e40af; }}
        .badge-species {{ background: #fef3c7; color: #92400e; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🦠 Prophage Movement Tracking</h1>
            <p>Cross-Sample, Temporal & Species Analysis</p>
        </header>

        <div class="content">
            <h2>📊 Summary Statistics</h2>

            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Shared Prophages</h4>
                    <div class="value">{summary['total_shared_prophages']}</div>
                    <p>Found in 2+ samples</p>
                </div>
                <div class="stat-card">
                    <h4>Cross-Year Movement</h4>
                    <div class="value">{summary['crosses_years_pct']:.1f}%</div>
                    <p>{summary['crosses_years']} prophages</p>
                </div>
                <div class="stat-card">
                    <h4>Cross-Species</h4>
                    <div class="value">{summary['crosses_species_pct']:.1f}%</div>
                    <p>{summary['crosses_species']} prophages</p>
                </div>
                <div class="stat-card">
                    <h4>Most Widespread</h4>
                    <div class="value">{summary['max_sample_count']}</div>
                    <p>Samples with same prophage</p>
                </div>
            </div>

            <h2>🔍 Top 50 Most Widespread Prophages</h2>
            <table>
                <thead>
                    <tr>
                        <th>Prophage ID</th>
                        <th>Samples</th>
                        <th>Years</th>
                        <th>Organisms</th>
                        <th>Movement</th>
                    </tr>
                </thead>
                <tbody>
"""

    for p in movement_data[:50]:
        years_str = ', '.join(str(y) for y in p['years'])
        organisms_str = ', '.join(p['organisms'])

        badges = []
        if p['crosses_years']:
            badges.append('<span class="badge badge-year">Cross-Year</span>')
        if p['crosses_species']:
            badges.append('<span class="badge badge-species">Cross-Species</span>')
        badges_html = ' '.join(badges) if badges else '-'

        html += f"""
                    <tr>
                        <td><code>{p['prophage_id'][:60]}...</code></td>
                        <td><strong>{p['sample_count']}</strong></td>
                        <td>{years_str}</td>
                        <td>{organisms_str}</td>
                        <td>{badges_html}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Report generated: {output_file}")


def main():
    base_dir = os.path.expanduser('~/compass_kansas_results')
    colocation_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/kansas_ALL_years_amr_phage_colocation.csv')
    output_html = os.path.expanduser('~/compass_kansas_results/publication_analysis/reports/PROPHAGE_MOVEMENT_TRACKING.html')

    print("=" * 70)
    print("Prophage Movement Tracking Analysis")
    print("=" * 70)

    # Load data
    metadata = load_metadata(base_dir)
    prophage_samples, sample_prophages = load_prophage_data(colocation_csv)

    # Track movement
    movement_data = track_prophage_movement(prophage_samples, metadata)
    summary = generate_summary_stats(movement_data)

    # Generate report
    generate_html_report(movement_data, summary, output_html)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
