#!/usr/bin/env python3
"""
Multi-Factor AMR-Prophage Analysis
Kansas E. coli Study 2021-2025

Explores complex interactions between:
- AMR genes/classes
- Prophage presence/proximity
- Food source types
- Organism/species
- Temporal patterns (year)

Generates:
1. Multi-dimensional association patterns
2. Food-specific prophage-AMR trends
3. Temporal trends by food source
4. Species-specific patterns
5. Interactive visualization dashboard
"""

import csv
import json
import re
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime
import sys

# ============================================================================
# DATA LOADING
# ============================================================================

def extract_food_source_from_sample_name(sample_name):
    """Extract food source from NARMS sample naming convention"""
    if not sample_name:
        return 'Unknown'

    # Extract product code pattern
    matches = re.findall(r'\d([A-Z]{2})\d', sample_name)
    if len(matches) >= 2:
        product_code = matches[1]  # Second match is the product code

        source_map = {
            'GB': 'Ground Beef',
            'CB': 'Chicken/Poultry',
            'GT': 'Ground Turkey',
            'PC': 'Pork Products',
            'CL': 'Chicken Liver',
            'CG': 'Chicken Gizzards',
            'CH': 'Chicken Hearts',
            'TK': 'Turkey',
            'BF': 'Beef',
        }

        return source_map.get(product_code, f'Other ({product_code})')

    return 'Unknown'

def load_metadata_files(base_dir):
    """Load metadata from all year directories"""
    print("Loading metadata from year directories...")

    metadata = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        metadata_file = base_path / f"results_kansas_{year}" / "filtered_samples" / "filtered_samples.csv"

        if not metadata_file.exists():
            continue

        print(f"  Loading {year} metadata...")
        with open(metadata_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                srr_id = row['Run']
                sample_name = row.get('SampleName', '')
                organism = row.get('organism', 'Unknown')

                food_source = extract_food_source_from_sample_name(sample_name)

                metadata[srr_id] = {
                    'sample_name': sample_name,
                    'food_source': food_source,
                    'organism': organism,
                    'year': str(year)
                }

    print(f"  Loaded metadata for {len(metadata)} samples")
    return metadata

def load_colocation_data(csv_file):
    """Load AMR-prophage colocation CSV"""
    print(f"Loading co-location data from {csv_file}...")
    data = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    print(f"  Loaded {len(data)} AMR-prophage associations")
    return data

# ============================================================================
# MULTI-FACTOR ANALYSIS
# ============================================================================

def analyze_multifactor_patterns(colocation_data, metadata):
    """
    Analyze complex interactions between AMR, prophage, food, species, and time
    """
    print("\nAnalyzing multi-factor patterns...")

    # Data structures for different dimensional slices

    # 3-way: Food × AMR Class × Proximity
    food_amr_proximity = defaultdict(lambda: defaultdict(lambda: Counter()))

    # 3-way: Year × Food × AMR Class
    year_food_amr = defaultdict(lambda: defaultdict(lambda: Counter()))

    # 3-way: Food × AMR Class × Organism
    food_amr_organism = defaultdict(lambda: defaultdict(lambda: Counter()))

    # 4-way: Year × Food × AMR Class × Proximity
    year_food_amr_proximity = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: Counter())))

    # Track samples for each combination
    food_year_samples = defaultdict(lambda: defaultdict(set))
    food_amr_samples = defaultdict(lambda: defaultdict(set))

    # Proximal vs non-proximal by food and year
    food_year_proximal = defaultdict(lambda: defaultdict(int))
    food_year_total = defaultdict(lambda: defaultdict(int))

    for row in colocation_data:
        sample_id = row['sample']
        amr_gene = row['amr_gene']
        amr_class = row['amr_class']
        category = row['category']
        year = row['year']

        # Get metadata
        if sample_id not in metadata:
            continue

        food_source = metadata[sample_id]['food_source']
        organism = metadata[sample_id]['organism']

        # Categorize proximity
        if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
            proximity = 'Proximal'
        else:
            proximity = 'Non-Proximal'

        # Populate data structures
        food_amr_proximity[food_source][amr_class][proximity] += 1
        year_food_amr[year][food_source][amr_class] += 1
        food_amr_organism[food_source][amr_class][organism] += 1
        year_food_amr_proximity[year][food_source][amr_class][proximity] += 1

        food_year_samples[food_source][year].add(sample_id)
        food_amr_samples[food_source][amr_class].add(sample_id)

        food_year_total[food_source][year] += 1
        if proximity == 'Proximal':
            food_year_proximal[food_source][year] += 1

    return {
        'food_amr_proximity': food_amr_proximity,
        'year_food_amr': year_food_amr,
        'food_amr_organism': food_amr_organism,
        'year_food_amr_proximity': year_food_amr_proximity,
        'food_year_samples': food_year_samples,
        'food_amr_samples': food_amr_samples,
        'food_year_proximal': food_year_proximal,
        'food_year_total': food_year_total
    }

def identify_key_patterns(analysis_data):
    """Identify the most interesting patterns in the data"""

    patterns = {
        'high_risk_combinations': [],  # Food × AMR with high proximal rates
        'temporal_shifts': [],  # Food × AMR combinations changing over time
        'food_specific_amr': [],  # AMR classes specific to certain food sources
    }

    food_amr_proximity = analysis_data['food_amr_proximity']
    year_food_amr = analysis_data['year_food_amr']
    food_amr_samples = analysis_data['food_amr_samples']

    # Find high-risk food-AMR combinations (high proximal percentage)
    for food_source in food_amr_proximity:
        for amr_class in food_amr_proximity[food_source]:
            proximal = food_amr_proximity[food_source][amr_class].get('Proximal', 0)
            non_proximal = food_amr_proximity[food_source][amr_class].get('Non-Proximal', 0)
            total = proximal + non_proximal

            if total >= 10:  # Minimum threshold
                proximal_pct = (proximal / total * 100) if total > 0 else 0

                if proximal_pct > 5:  # Above baseline
                    patterns['high_risk_combinations'].append({
                        'food': food_source,
                        'amr_class': amr_class,
                        'proximal_pct': proximal_pct,
                        'total_instances': total,
                        'proximal_count': proximal
                    })

    # Sort by proximal percentage
    patterns['high_risk_combinations'].sort(key=lambda x: x['proximal_pct'], reverse=True)

    # Find food-specific AMR patterns
    for food_source in food_amr_samples:
        for amr_class in food_amr_samples[food_source]:
            # Check how dominant this food source is for this AMR class
            samples_in_this_food = len(food_amr_samples[food_source][amr_class])

            # Count total samples with this AMR across all foods
            total_samples_with_amr = sum(
                len(food_amr_samples[f][amr_class])
                for f in food_amr_samples if amr_class in food_amr_samples[f]
            )

            if total_samples_with_amr >= 10:  # Minimum threshold
                dominance_pct = (samples_in_this_food / total_samples_with_amr * 100)

                if dominance_pct > 60:  # Food source accounts for >60% of this AMR
                    patterns['food_specific_amr'].append({
                        'food': food_source,
                        'amr_class': amr_class,
                        'dominance_pct': dominance_pct,
                        'samples_in_food': samples_in_this_food,
                        'total_samples': total_samples_with_amr
                    })

    patterns['food_specific_amr'].sort(key=lambda x: x['dominance_pct'], reverse=True)

    return patterns

# ============================================================================
# HTML REPORT GENERATION
# ============================================================================

def generate_html_report(output_file, analysis_data, patterns, metadata):
    """Generate comprehensive multi-factor analysis HTML report"""

    print(f"\nGenerating HTML report: {output_file}")

    food_amr_proximity = analysis_data['food_amr_proximity']
    year_food_amr = analysis_data['year_food_amr']
    food_year_samples = analysis_data['food_year_samples']
    food_year_proximal = analysis_data['food_year_proximal']
    food_year_total = analysis_data['food_year_total']

    # Get top food sources by sample count
    food_sample_counts = {
        food: sum(len(samples) for samples in years.values())
        for food, years in food_year_samples.items()
    }
    top_foods = sorted(food_sample_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    # Prepare data for temporal chart
    years = sorted(set(year for data in year_food_amr.keys() for year in [data]))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Factor AMR-Prophage Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}

        .container {{
            max-width: 1600px;
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

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .content {{
            padding: 40px;
        }}

        h2 {{
            color: #667eea;
            font-size: 2em;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        h3 {{
            color: #764ba2;
            font-size: 1.5em;
            margin: 25px 0 15px 0;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
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

        tbody tr:hover {{
            background: #f7fafc;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin: 30px 0;
        }}

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

        .highlight {{
            background: #fef3c7;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-danger {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge-info {{
            background: #dbeafe;
            color: #1e40af;
        }}

        footer {{
            background: #2d3748;
            color: white;
            padding: 30px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 Multi-Factor AMR-Prophage Analysis</h1>
            <p>Complex Interactions: AMR × Prophage × Food × Species × Time</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Kansas E. coli Study 2021-2025</p>
            <p style="font-size: 0.85em;">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>

        <div class="content">
            <section id="overview">
                <h2>📊 Analysis Overview</h2>

                <div class="alert-box">
                    <h4>🔍 Research Questions</h4>
                    <ul style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                        <li>Which food sources show the highest AMR-prophage proximity rates?</li>
                        <li>Are there food-specific AMR patterns?</li>
                        <li>How do these patterns change over time (2021-2025)?</li>
                        <li>Do different species show different food-AMR associations?</li>
                    </ul>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Food Sources</h4>
                        <div class="value">{len(food_amr_proximity)}</div>
                        <p>Analyzed</p>
                    </div>
                    <div class="stat-card">
                        <h4>Years</h4>
                        <div class="value">{len(years)}</div>
                        <p>2021-2025</p>
                    </div>
                    <div class="stat-card">
                        <h4>High-Risk Combos</h4>
                        <div class="value">{len(patterns['high_risk_combinations'])}</div>
                        <p>Food×AMR patterns</p>
                    </div>
                </div>
            </section>

            <section id="high-risk">
                <h2>⚠️ High-Risk Food-AMR Combinations</h2>

                <div class="info-box">
                    <h4>🎯 Priority Surveillance Targets</h4>
                    <p>Food-AMR combinations with elevated prophage proximity rates (>5% proximal)</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Food Source</th>
                            <th>AMR Class</th>
                            <th>Total Instances</th>
                            <th>Proximal Count</th>
                            <th>Proximal %</th>
                            <th>Risk Level</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for combo in patterns['high_risk_combinations'][:20]:
        risk_level = 'High' if combo['proximal_pct'] > 10 else 'Moderate'
        badge_class = 'badge-danger' if combo['proximal_pct'] > 10 else 'badge-warning'

        html += f"""
                        <tr>
                            <td><strong>{combo['food']}</strong></td>
                            <td>{combo['amr_class']}</td>
                            <td>{combo['total_instances']}</td>
                            <td><span class="highlight">{combo['proximal_count']}</span></td>
                            <td>{combo['proximal_pct']:.1f}%</td>
                            <td><span class="badge {badge_class}">{risk_level}</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="food-specific">
                <h2>🍗 Food-Specific AMR Patterns</h2>

                <div class="info-box">
                    <h4>📈 Dominant Food-AMR Associations</h4>
                    <p>AMR classes that are predominantly found in specific food sources (>60% dominance)</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Food Source</th>
                            <th>AMR Class</th>
                            <th>Samples in This Food</th>
                            <th>Total Samples</th>
                            <th>Dominance %</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for pattern in patterns['food_specific_amr'][:15]:
        html += f"""
                        <tr>
                            <td><strong>{pattern['food']}</strong></td>
                            <td>{pattern['amr_class']}</td>
                            <td>{pattern['samples_in_food']}</td>
                            <td>{pattern['total_samples']}</td>
                            <td><span class="highlight">{pattern['dominance_pct']:.1f}%</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="temporal">
                <h2>📅 Temporal Trends by Food Source</h2>

                <div class="info-box">
                    <h4>⏱️ Year-over-Year Changes</h4>
                    <p>Proximal AMR-prophage rates by food source over time</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Food Source</th>
"""

    for year in sorted(years):
        html += f"                            <th>{year}</th>\n"

    html += """
                            <th>Trend</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for food, sample_count in top_foods:
        html += f"                        <tr>\n"
        html += f"                            <td><strong>{food}</strong></td>\n"

        proximal_rates = []
        for year in sorted(years):
            total = food_year_total[food].get(year, 0)
            proximal = food_year_proximal[food].get(year, 0)
            rate = (proximal / total * 100) if total > 0 else 0
            proximal_rates.append(rate)

            if total > 0:
                html += f"                            <td>{rate:.1f}% ({proximal}/{total})</td>\n"
            else:
                html += f"                            <td>-</td>\n"

        # Simple trend indicator
        if len(proximal_rates) >= 2 and proximal_rates[-1] > proximal_rates[0]:
            trend = "↑ Increasing"
            badge = "badge-danger"
        elif len(proximal_rates) >= 2 and proximal_rates[-1] < proximal_rates[0]:
            trend = "↓ Decreasing"
            badge = "badge-info"
        else:
            trend = "→ Stable"
            badge = "badge-warning"

        html += f"                            <td><span class='badge {badge}'>{trend}</span></td>\n"
        html += f"                        </tr>\n"

    html += f"""
                    </tbody>
                </table>
            </section>

            <section id="conclusions">
                <h2>📝 Key Findings</h2>

                <div class="alert-box">
                    <h4>✅ Summary</h4>
                    <ul style="line-height: 2; margin-left: 30px; margin-top: 10px;">
                        <li><strong>High-risk combinations:</strong> {len(patterns['high_risk_combinations'])} food-AMR pairs with elevated prophage proximity</li>
                        <li><strong>Food-specific patterns:</strong> {len(patterns['food_specific_amr'])} AMR classes show strong food source associations</li>
                        <li><strong>Top food source:</strong> {top_foods[0][0] if top_foods else 'N/A'} with {top_foods[0][1] if top_foods else 0} total associations</li>
                    </ul>
                </div>

                <h3>Public Health Implications</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li>Target surveillance on high-risk food-AMR combinations</li>
                    <li>Monitor temporal trends for emerging patterns</li>
                    <li>Consider food-specific intervention strategies</li>
                    <li>Investigate why certain AMR classes cluster in specific food sources</li>
                </ul>
            </section>
        </div>

        <footer>
            <p><strong>Multi-Factor AMR-Prophage Analysis</strong></p>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Kansas E. coli Study 2021-2025</p>
        </footer>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Report generated: {output_file}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    # File paths
    colocation_csv = Path.home() / 'compass_kansas_results' / 'publication_analysis' / 'tables' / 'kansas_ALL_years_amr_phage_colocation.csv'
    base_dir = Path.home() / 'compass_kansas_results'
    output_html = Path.home() / 'compass_kansas_results' / 'publication_analysis' / 'reports' / 'KANSAS_MULTIFACTOR_ANALYSIS.html'

    print("=" * 70)
    print("Multi-Factor AMR-Prophage Analysis")
    print("AMR × Prophage × Food × Species × Time")
    print("=" * 70)

    # Load data
    metadata = load_metadata_files(base_dir)
    colocation_data = load_colocation_data(colocation_csv)

    # Run analysis
    analysis_data = analyze_multifactor_patterns(colocation_data, metadata)

    # Identify key patterns
    patterns = identify_key_patterns(analysis_data)

    # Generate report
    generate_html_report(output_html, analysis_data, patterns, metadata)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_html}")
    print(f"\n📈 Key Findings:")
    print(f"   - High-risk combinations: {len(patterns['high_risk_combinations'])}")
    print(f"   - Food-specific AMR patterns: {len(patterns['food_specific_amr'])}")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
