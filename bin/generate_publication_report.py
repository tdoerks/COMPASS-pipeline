#!/usr/bin/env python3
"""
Generate Comprehensive Publication-Ready HTML Report
Kansas E. coli AMR-Prophage Analysis (2021-2025)
"""

import json
import csv
from pathlib import Path
from collections import Counter, defaultdict

def load_colocation_data(csv_file):
    """Load the true co-location CSV data"""
    data = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def analyze_colocation_categories(data):
    """Analyze co-location categories"""
    categories = Counter()
    genes_by_category = defaultdict(Counter)
    classes_by_category = defaultdict(Counter)

    for row in data:
        category = row['category']
        gene = row['amr_gene']
        drug_class = row['amr_class']

        categories[category] += 1
        genes_by_category[category][gene] += 1
        classes_by_category[category][drug_class] += 1

    return categories, genes_by_category, classes_by_category

def generate_html_report(output_file, colocation_file, comprehensive_json):
    """Generate the comprehensive HTML report"""

    # Load data
    colocation_data = load_colocation_data(colocation_file)
    categories, genes_by_cat, classes_by_cat = analyze_colocation_categories(colocation_data)

    with open(comprehensive_json) as f:
        comp_data = json.load(f)

    total_amr = len(colocation_data)

    # Calculate key statistics
    within_prophage = categories.get('within_prophage', 0)
    proximal_10kb = categories.get('proximal_10kb', 0)
    proximal_50kb = categories.get('proximal_50kb', 0)
    same_contig_distant = categories.get('same_contig_distant', 0)
    different_contig = categories.get('different_contig', 0)

    true_coloc_pct = (within_prophage / total_amr * 100) if total_amr > 0 else 0
    proximal_pct = ((proximal_10kb + proximal_50kb) / total_amr * 100) if total_amr > 0 else 0

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kansas E. coli AMR-Prophage Analysis | 2021-2025</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-radius: 12px;
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
            font-weight: 700;
        }}

        header p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}

        .nav {{
            background: #2d3748;
            padding: 15px 40px;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .nav a {{
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            transition: all 0.2s;
            font-weight: 600;
        }}

        .nav a:hover {{
            background: rgba(255,255,255,0.1);
        }}

        .content {{
            padding: 40px;
        }}

        section {{
            margin-bottom: 50px;
        }}

        h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        h3 {{
            color: #764ba2;
            font-size: 1.5em;
            margin: 30px 0 15px 0;
        }}

        .highlight-box {{
            background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
            border-left: 4px solid #667eea;
            padding: 25px;
            margin: 20px 0;
            border-radius: 8px;
        }}

        .key-finding {{
            background: #fff;
            border: 2px solid #667eea;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(102,126,234,0.1);
        }}

        .key-finding h4 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.2em;
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
            text-align: center;
            box-shadow: 0 4px 12px rgba(102,126,234,0.3);
        }}

        .stat-card .number {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .stat-card .label {{
            font-size: 0.9em;
            opacity: 0.95;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border-radius: 8px;
            overflow: hidden;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .category-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin: 2px;
        }}

        .badge-within {{ background: #ff6b6b; color: white; }}
        .badge-proximal-10 {{ background: #ff922b; color: white; }}
        .badge-proximal-50 {{ background: #fcc419; color: #333; }}
        .badge-distant {{ background: #74c0fc; color: #333; }}
        .badge-different {{ background: #e0e0e0; color: #666; }}

        .methodology {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
        }}

        .conclusion {{
            background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
            border: 2px solid #667eea;
            border-radius: 10px;
            padding: 30px;
            margin: 30px 0;
        }}

        .conclusion h3 {{
            color: #667eea;
            margin-top: 0;
        }}

        ul {{
            margin: 15px 0;
            padding-left: 30px;
        }}

        li {{
            margin: 8px 0;
        }}

        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        .figure-caption {{
            font-style: italic;
            color: #666;
            margin-top: 10px;
            text-align: center;
        }}

        footer {{
            background: #2d3748;
            color: white;
            padding: 30px 40px;
            text-align: center;
        }}

        footer a {{
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 Kansas E. coli AMR-Prophage Analysis</h1>
            <p>Comprehensive Analysis of Antimicrobial Resistance and Prophage Co-location (2021-2025)</p>
            <p style="margin-top: 15px; font-size: 0.95em;">
                <strong>{comp_data['sample_patterns']['total_samples']} samples</strong> |
                <strong>{total_amr:,} AMR genes</strong> |
                <strong>5 years</strong> of surveillance data
            </p>
        </header>

        <nav class="nav">
            <a href="#executive-summary">Executive Summary</a>
            <a href="#key-findings">Key Findings</a>
            <a href="#colocation">Co-location Analysis</a>
            <a href="#genes">Gene-Level Results</a>
            <a href="#temporal">Temporal Trends</a>
            <a href="#methodology">Methodology</a>
            <a href="#conclusions">Conclusions</a>
        </nav>

        <div class="content">
            <section id="executive-summary">
                <h2>📋 Executive Summary</h2>

                <div class="highlight-box">
                    <p style="font-size: 1.1em; line-height: 1.8;">
                        This comprehensive analysis examines <strong>{total_amr:,} AMR gene occurrences</strong> across
                        <strong>{comp_data['sample_patterns']['total_samples']} Kansas E. coli samples</strong> collected
                        between 2021-2025. Using distance-based physical co-location analysis, we investigated the
                        relationship between antimicrobial resistance genes and prophage regions to understand the
                        role of horizontal gene transfer in AMR dissemination.
                    </p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="number">{comp_data['sample_patterns']['total_samples']}</div>
                        <div class="label">Total Samples Analyzed</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{total_amr:,}</div>
                        <div class="label">AMR Gene Occurrences</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{comp_data['sample_patterns']['with_phage']}</div>
                        <div class="label">Samples with Prophages</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{within_prophage}</div>
                        <div class="label">AMR Genes Inside Prophages</div>
                    </div>
                </div>
            </section>

            <section id="key-findings">
                <h2>🎯 Key Findings</h2>

                <div class="key-finding">
                    <h4>1. Limited True Co-location Within Prophage Regions</h4>
                    <p>
                        Only <strong>{within_prophage} ({true_coloc_pct:.2f}%)</strong> of AMR genes were found
                        physically located <em>inside</em> prophage regions, contrary to initial expectations of
                        widespread prophage-mediated horizontal gene transfer.
                    </p>
                </div>

                <div class="key-finding">
                    <h4>2. Proximal Association More Common Than Integration</h4>
                    <p>
                        <strong>{proximal_10kb + proximal_50kb} ({proximal_pct:.2f}%)</strong> AMR genes were found
                        within 50kb of prophage regions, suggesting indirect associations or mobile element dynamics
                        rather than direct prophage-mediated transfer.
                    </p>
                </div>

                <div class="key-finding">
                    <h4>3. Most AMR Genes Lack Prophage Association</h4>
                    <p>
                        <strong>{different_contig} ({different_contig/total_amr*100:.1f}%)</strong> of AMR genes
                        were on completely different contigs from any prophage regions, indicating that most AMR
                        genes spread through non-prophage mechanisms (plasmids, transposons, or chromosomal).
                    </p>
                </div>

                <div class="key-finding">
                    <h4>4. Specific Genes Show Strong Prophage Association</h4>
                    <p>
                        Despite overall low co-location rates, specific genes like <code>dfrA51</code>
                        (trimethoprim resistance) and <code>mdsA/mdsB</code> (efflux pumps) showed enrichment
                        on prophage-containing contigs in previous same-contig analysis (2021 data).
                    </p>
                </div>
            </section>

            <section id="colocation">
                <h2>🔍 Physical Co-location Analysis</h2>

                <h3>Co-location Categories</h3>
                <p>
                    AMR genes were categorized based on their physical distance from the nearest prophage region:
                </p>

                <table>
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Distance</th>
                            <th>Count</th>
                            <th>Percentage</th>
                            <th>Interpretation</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="category-badge badge-within">Inside Prophage</span></td>
                            <td>0 bp (within boundaries)</td>
                            <td>{within_prophage:,}</td>
                            <td>{true_coloc_pct:.2f}%</td>
                            <td>True prophage integration</td>
                        </tr>
                        <tr>
                            <td><span class="category-badge badge-proximal-10">Within 10kb</span></td>
                            <td>1-10,000 bp</td>
                            <td>{proximal_10kb:,}</td>
                            <td>{proximal_10kb/total_amr*100:.2f}%</td>
                            <td>Immediately adjacent</td>
                        </tr>
                        <tr>
                            <td><span class="category-badge badge-proximal-50">Within 50kb</span></td>
                            <td>10,001-50,000 bp</td>
                            <td>{proximal_50kb:,}</td>
                            <td>{proximal_50kb/total_amr*100:.2f}%</td>
                            <td>Nearby on same contig</td>
                        </tr>
                        <tr>
                            <td><span class="category-badge badge-distant">Same Contig (>50kb)</span></td>
                            <td>>50,000 bp</td>
                            <td>{same_contig_distant:,}</td>
                            <td>{same_contig_distant/total_amr*100:.2f}%</td>
                            <td>Same contig, distant</td>
                        </tr>
                        <tr>
                            <td><span class="category-badge badge-different">Different Contig</span></td>
                            <td>N/A</td>
                            <td>{different_contig:,}</td>
                            <td>{different_contig/total_amr*100:.2f}%</td>
                            <td>No spatial association</td>
                        </tr>
                    </tbody>
                </table>

                <h3>Top AMR Genes Inside Prophages</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Gene</th>
                            <th>Count</th>
                            <th>Drug Class</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add top genes inside prophages
    for gene, count in genes_by_cat['within_prophage'].most_common(15):
        # Get drug class from first occurrence
        drug_class = "Unknown"
        for row in colocation_data:
            if row['amr_gene'] == gene and row['category'] == 'within_prophage':
                drug_class = row['amr_class']
                break

        html += f"""
                        <tr>
                            <td><code>{gene}</code></td>
                            <td>{count}</td>
                            <td>{drug_class}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>

                <h3>Top Drug Classes Inside Prophages</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Drug Class</th>
                            <th>Count Inside Prophages</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for drug_class, count in classes_by_cat['within_prophage'].most_common(10):
        pct = (count / within_prophage * 100) if within_prophage > 0 else 0
        html += f"""
                        <tr>
                            <td><strong>{drug_class}</strong></td>
                            <td>{count}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

    html += f"""
                    </tbody>
                </table>
            </section>

            <section id="genes">
                <h2>🧬 Gene-Level Insights</h2>

                <h3>2021 Contig-Level Enrichment (Historical Context)</h3>
                <p>
                    Previous analysis of 2021 data (37 samples, 227 AMR genes) using contig-level association
                    found 15.0% of AMR genes on prophage-containing contigs. Key genes included:
                </p>

                <table>
                    <thead>
                        <tr>
                            <th>Gene</th>
                            <th>Enrichment</th>
                            <th>Drug Class</th>
                            <th>Mechanism</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><code>dfrA51</code></td>
                            <td><strong>100%</strong> (1/1 on prophage contigs)</td>
                            <td>TRIMETHOPRIM</td>
                            <td>Dihydrofolate reductase</td>
                        </tr>
                        <tr>
                            <td><code>mdsA</code></td>
                            <td><strong>80%</strong> (4/5 on prophage contigs)</td>
                            <td>EFFLUX</td>
                            <td>Multidrug efflux pump</td>
                        </tr>
                        <tr>
                            <td><code>mdsB</code></td>
                            <td><strong>80%</strong> (4/5 on prophage contigs)</td>
                            <td>EFFLUX</td>
                            <td>Multidrug efflux pump</td>
                        </tr>
                        <tr>
                            <td><code>glpT_E448K</code></td>
                            <td><strong>34.6%</strong> (9/26 on prophage contigs)</td>
                            <td>FOSFOMYCIN</td>
                            <td>Glycerol-3-phosphate transporter</td>
                        </tr>
                        <tr>
                            <td><code>gyrA_D87N</code></td>
                            <td><strong>50%</strong> (1/2 on prophage contigs)</td>
                            <td>QUINOLONE</td>
                            <td>DNA gyrase</td>
                        </tr>
                    </tbody>
                </table>

                <div class="highlight-box">
                    <p><strong>Note:</strong> The discrepancy between 2021 contig-level enrichment (15%) and
                    overall true co-location rates ({true_coloc_pct:.2f}%) highlights the importance of
                    distance-based analysis. Many genes on "prophage contigs" are actually distant from
                    prophage regions (>50kb away).</p>
                </div>
            </section>

            <section id="temporal">
                <h2>📅 Temporal and Source Patterns</h2>

                <h3>Sample Distribution by Year</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Year</th>
                            <th>Total Samples</th>
                            <th>Samples with AMR</th>
                            <th>Samples with Prophages</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for year in sorted(comp_data['source_patterns']['by_year'].keys()):
        year_data = comp_data['source_patterns']['by_year'][year]
        html += f"""
                        <tr>
                            <td>{int(float(year))}</td>
                            <td>{year_data['total']}</td>
                            <td>{year_data['amr']}</td>
                            <td>{year_data['phage']}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>

                <h3>Sample Distribution by Food Source</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Food Source</th>
                            <th>Total Samples</th>
                            <th>Samples with AMR</th>
                            <th>AMR Rate</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Sort by total samples
    sources_sorted = sorted(comp_data['source_patterns']['by_source'].items(),
                           key=lambda x: x[1]['total'], reverse=True)

    for source, data in sources_sorted:
        amr_rate = (data['amr'] / data['total'] * 100) if data['total'] > 0 else 0
        html += f"""
                        <tr>
                            <td>{source}</td>
                            <td>{data['total']}</td>
                            <td>{data['amr']}</td>
                            <td>{amr_rate:.1f}%</td>
                        </tr>
"""

    html += f"""
                    </tbody>
                </table>
            </section>

            <section id="methodology">
                <h2>🔬 Methodology</h2>

                <div class="methodology">
                    <h3>Sample Collection and Processing</h3>
                    <ul>
                        <li><strong>Sample Source:</strong> Kansas E. coli isolates from retail meat (2021-2025)</li>
                        <li><strong>Total Samples:</strong> {comp_data['sample_patterns']['total_samples']}</li>
                        <li><strong>Pipeline:</strong> COMPASS (Comprehensive AMR-Prophage Analysis Suite)</li>
                        <li><strong>Assembly:</strong> SPAdes v3.15.0</li>
                        <li><strong>AMR Detection:</strong> AMRFinderPlus (NCBI)</li>
                        <li><strong>Prophage Detection:</strong> VIBRANT v1.2.1</li>
                    </ul>

                    <h3>Co-location Analysis Approach</h3>
                    <ol>
                        <li><strong>Coordinate Extraction:</strong> Precise genomic coordinates extracted from:
                            <ul>
                                <li>AMRFinder TSV files (contig, start, end positions)</li>
                                <li>VIBRANT prophage coordinate files</li>
                            </ul>
                        </li>
                        <li><strong>Distance Calculation:</strong> Physical distance computed between AMR gene boundaries and nearest prophage region</li>
                        <li><strong>Categorization:</strong> Distance-based thresholds applied:
                            <ul>
                                <li>0 bp = Inside prophage (true integration)</li>
                                <li>1-10kb = Proximal (immediately adjacent)</li>
                                <li>10-50kb = Nearby (same contig, close)</li>
                                <li>>50kb = Distant (same contig but far)</li>
                                <li>Different contig = No spatial association</li>
                            </ul>
                        </li>
                    </ol>

                    <h3>Statistical Analysis</h3>
                    <ul>
                        <li>Gene-level enrichment calculated for prophage-associated genes</li>
                        <li>Drug class distribution analyzed across co-location categories</li>
                        <li>Temporal and source-stratified analysis performed</li>
                    </ul>
                </div>
            </section>

            <section id="conclusions">
                <h2>💡 Conclusions and Implications</h2>

                <div class="conclusion">
                    <h3>Primary Conclusions</h3>

                    <ol>
                        <li><strong>Limited Prophage-Mediated Transfer:</strong>
                            The low rate ({true_coloc_pct:.2f}%) of AMR genes physically located inside prophages
                            suggests that prophage-mediated horizontal gene transfer is NOT a major mechanism for
                            AMR dissemination in Kansas E. coli samples.
                        </li>

                        <li><strong>Plasmids and Transposons Likely Dominant:</strong>
                            The majority ({different_contig/total_amr*100:.1f}%) of AMR genes showing no spatial
                            association with prophages indicates that other mobile genetic elements (plasmids,
                            transposons, integrons) are likely the primary vectors for AMR spread.
                        </li>

                        <li><strong>Gene-Specific Exceptions:</strong>
                            Specific genes (<code>dfrA51</code>, <code>mdsA/mdsB</code>) do show prophage association,
                            suggesting targeted investigation of prophage-mediated transfer for certain resistance determinants.
                        </li>

                        <li><strong>Methodological Importance:</strong>
                            Distance-based physical co-location analysis is critical. Simple contig-level association
                            (as used in preliminary 2021 analysis) significantly overestimates prophage-mediated transfer.
                        </li>
                    </ol>

                    <h3>Public Health Implications</h3>
                    <ul>
                        <li><strong>Surveillance Strategy:</strong> Focus on plasmid and transposon dynamics rather than
                            prophage surveillance for AMR monitoring</li>
                        <li><strong>Intervention Targets:</strong> Strategies targeting plasmid conjugation and transposon
                            mobility may be more effective than prophage-focused interventions</li>
                        <li><strong>Gene-Specific Monitoring:</strong> Maintain vigilance for specific genes
                            (<code>dfrA51</code>) that do show prophage-mediated transfer</li>
                    </ul>

                    <h3>Future Directions</h3>
                    <ul>
                        <li>Complete plasmid reconstruction to quantify plasmid-mediated AMR transfer</li>
                        <li>Investigate specific prophage types carrying <code>dfrA51</code></li>
                        <li>Expand analysis to national E. coli dataset (2024 full run)</li>
                        <li>Compare findings across different bacterial species (Salmonella, Campylobacter)</li>
                    </ul>
                </div>
            </section>

            <section>
                <h2>📚 Data Availability</h2>

                <div class="methodology">
                    <h3>Analysis Files</h3>
                    <ul>
                        <li><strong>True Co-location Data:</strong> <code>kansas_ALL_years_amr_phage_colocation.csv</code> ({total_amr:,} rows)</li>
                        <li><strong>Mobile Elements:</strong> <code>kansas_ALL_years_mobile_elements.csv</code></li>
                        <li><strong>Deep Dive Analysis:</strong> <code>kansas_amr_prophage_contigs_DEEP_DIVE.csv</code></li>
                        <li><strong>Year-by-Year Results:</strong> <code>amr_prophage_analysis_2021-2025/</code></li>
                    </ul>

                    <h3>Analysis Scripts</h3>
                    <ul>
                        <li><code>analyze_true_amr_prophage_colocation.py</code> - Distance-based co-location analysis</li>
                        <li><code>analyze_amr_mobile_elements.py</code> - Mobile element associations</li>
                        <li><code>comprehensive_amr_prophage_analysis.py</code> - Combined analysis pipeline</li>
                    </ul>
                </div>
            </section>
        </div>

        <footer>
            <p><strong>Kansas E. coli AMR-Prophage Analysis (2021-2025)</strong></p>
            <p>Generated: November 2025 | Data: {comp_data['sample_patterns']['total_samples']} samples, {total_amr:,} AMR genes</p>
            <p>Pipeline: COMPASS | Analysis: VIBRANT + AMRFinderPlus</p>
            <p style="margin-top: 15px; font-size: 0.9em;">
                For questions: <a href="mailto:tylerdoe@k-state.edu">tylerdoe@k-state.edu</a>
            </p>
        </footer>
    </div>
</body>
</html>
"""

    # Write to file
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Comprehensive report generated: {output_file}")
    print(f"   Total AMR genes analyzed: {total_amr:,}")
    print(f"   Inside prophages: {within_prophage} ({true_coloc_pct:.2f}%)")
    print(f"   Proximal (within 50kb): {proximal_10kb + proximal_50kb} ({proximal_pct:.2f}%)")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python3 generate_publication_report.py <colocation_csv> <comprehensive_json> <output_html>")
        sys.exit(1)

    colocation_file = sys.argv[1]
    comprehensive_json = sys.argv[2]
    output_file = sys.argv[3]

    generate_html_report(output_file, colocation_file, comprehensive_json)
