#!/usr/bin/env python3
"""
Comprehensive Prophage Analysis Dashboard

Generates detailed prophage analysis including:
1. Overall prophage statistics
2. Prophage type distribution (lytic vs lysogenic)
3. Prophage quality assessment
4. Sample-level patterns
5. Organism/source/temporal breakdowns
6. Prophage functional diversity

Creates HTML dashboard with visualizations and detailed statistics.
"""

import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

def load_prophage_data(base_dir):
    """Load VIBRANT combined prophage data."""
    vibrant_path = base_dir / "vibrant_combined.tsv"

    if not vibrant_path.exists():
        print(f"❌ Error: {vibrant_path} not found")
        print("   Run create_combined_files.sh first!")
        sys.exit(1)

    print(f"📊 Loading prophage data from {vibrant_path}")
    df = pd.read_csv(vibrant_path, sep='\t')
    print(f"✅ Loaded {len(df)} prophage predictions from {df['sample_id'].nunique()} samples")

    return df

def calculate_overall_statistics(df, total_samples):
    """Calculate overall prophage statistics."""
    stats = {
        'total_prophages': len(df),
        'samples_with_prophages': df['sample_id'].nunique(),
        'samples_without_prophages': total_samples - df['sample_id'].nunique(),
        'pct_samples_with_prophages': (df['sample_id'].nunique() / total_samples * 100) if total_samples > 0 else 0,
        'avg_prophages_per_sample': len(df) / df['sample_id'].nunique() if df['sample_id'].nunique() > 0 else 0,
        'prophages_per_sample_dist': df.groupby('sample_id').size().describe().to_dict()
    }

    return stats

def analyze_prophage_types(df):
    """Analyze prophage lifestyle types (lytic vs lysogenic) with normalization options."""
    print("\n🔬 Analyzing prophage types...")

    num_samples = df['sample_id'].nunique()

    # Total counts (raw sum)
    type_counts = df['type'].value_counts()

    # Per-genome counts (normalized by number of samples)
    type_per_genome = {ptype: count / num_samples for ptype, count in type_counts.items()}

    # Unique counts per genome (deduplicated - count samples that have each type)
    type_unique = df.groupby('type')['sample_id'].nunique().to_dict()
    type_unique_per_genome = {ptype: count / num_samples for ptype, count in type_unique.items()}

    type_stats = {
        'counts': type_counts.to_dict(),
        'percentages': (type_counts / len(df) * 100).to_dict(),
        'per_genome': type_per_genome,
        'unique_per_genome': type_unique_per_genome,
        'num_samples': num_samples
    }

    print(f"  Prophage Types:")
    for ptype, count in type_counts.items():
        pct = count / len(df) * 100
        per_genome = type_per_genome[ptype]
        unique = type_unique_per_genome[ptype]
        print(f"    • {ptype}: {count:,} ({pct:.1f}%) | {per_genome:.2f}/genome | {unique:.2%} unique")

    return type_stats

def analyze_prophage_quality(df):
    """Analyze prophage quality scores with normalization options."""
    print("\n💎 Analyzing prophage quality...")

    num_samples = df['sample_id'].nunique()

    # Total counts (raw sum)
    quality_counts = df['quality'].value_counts()

    # Per-genome counts (normalized by number of samples)
    quality_per_genome = {qual: count / num_samples for qual, count in quality_counts.items()}

    # Unique counts per genome (deduplicated - count samples that have each quality)
    quality_unique = df.groupby('quality')['sample_id'].nunique().to_dict()
    quality_unique_per_genome = {qual: count / num_samples for qual, count in quality_unique.items()}

    quality_stats = {
        'counts': quality_counts.to_dict(),
        'percentages': (quality_counts / len(df) * 100).to_dict(),
        'per_genome': quality_per_genome,
        'unique_per_genome': quality_unique_per_genome,
        'num_samples': num_samples
    }

    print(f"  Prophage Quality:")
    for quality, count in quality_counts.items():
        pct = count / len(df) * 100
        per_genome = quality_per_genome[quality]
        unique = quality_unique_per_genome[quality]
        print(f"    • {quality}: {count:,} ({pct:.1f}%) | {per_genome:.2f}/genome | {unique:.2%} unique")

    return quality_stats

def analyze_sample_patterns(df, total_samples):
    """Analyze prophage distribution across samples."""
    print("\n📊 Analyzing sample patterns...")

    prophages_per_sample = df.groupby('sample_id').size()

    # Create distribution bins
    bins = [0, 1, 5, 10, 20, prophages_per_sample.max() + 1]
    labels = ['1', '2-5', '6-10', '11-20', '20+']

    prophage_bins = pd.cut(prophages_per_sample, bins=bins, labels=labels, include_lowest=True)
    bin_counts = prophage_bins.value_counts().sort_index()

    pattern_stats = {
        'min': int(prophages_per_sample.min()),
        'max': int(prophages_per_sample.max()),
        'median': float(prophages_per_sample.median()),
        'mean': float(prophages_per_sample.mean()),
        'std': float(prophages_per_sample.std()),
        'distribution': bin_counts.to_dict()
    }

    print(f"  Prophages per Sample:")
    print(f"    • Min: {pattern_stats['min']}")
    print(f"    • Max: {pattern_stats['max']}")
    print(f"    • Median: {pattern_stats['median']:.1f}")
    print(f"    • Mean: {pattern_stats['mean']:.2f}")
    print(f"    • Std Dev: {pattern_stats['std']:.2f}")

    print(f"\n  Distribution:")
    for bin_label, count in bin_counts.items():
        pct = count / len(prophages_per_sample) * 100
        print(f"    • {bin_label} prophages: {count} samples ({pct:.1f}%)")

    return pattern_stats

def parse_vibrant_annotations(base_dir):
    """Parse VIBRANT annotation files to extract prophage functional categories."""
    print("\n🧬 Parsing prophage functional annotations...")

    vibrant_dir = base_dir / "vibrant"
    if not vibrant_dir.exists():
        print("  ⚠️  VIBRANT directory not found, skipping functional analysis")
        return None

    # Define functional category keywords
    function_keywords = {
        'DNA Packaging': ['terminase', 'portal', 'scaffolding', 'DNA-packaging', 'packaging protein', 'head-tail connector'],
        'Structural': ['capsid', 'coat protein', 'tail', 'baseplate', 'head protein', 'neck', 'collar', 'major capsid', 'minor capsid'],
        'Lysis': ['holin', 'lysin', 'endolysin', 'spanin', 'lysis protein', 'murein hydrolase'],
        'Regulation': ['antitermination', 'repressor', 'regulator', 'cro protein', 'cI protein', 'transcriptional', 'anti-repressor'],
        'DNA Modification': ['recombinase', 'integrase', 'helicase', 'primase', 'polymerase', 'ligase', 'exonuclease', 'endonuclease', 'DNA replication'],
        'Tail Fiber': ['tail fiber', 'tail spike', 'tail tip', 'receptor binding'],
        'Other': []  # Catch-all for characterized proteins
    }

    functional_data = Counter()
    hypothetical_count = 0
    total_proteins = 0
    samples_processed = 0
    debug_annotations = []  # Collect sample annotations for debugging

    # Process each VIBRANT directory
    for sample_dir in sorted(vibrant_dir.glob("*_vibrant")):
        sample_id = sample_dir.name.replace('_vibrant', '')

        # Look for annotation file
        annot_pattern = f"VIBRANT_annotations_{sample_id}_contigs.tsv"
        annot_files = list(sample_dir.rglob(annot_pattern))

        if not annot_files:
            continue

        samples_processed += 1
        try:
            df_annot = pd.read_csv(annot_files[0], sep='\t')

            # Debug: Show columns from first file
            if samples_processed == 1:
                print(f"  📋 Annotation file columns: {list(df_annot.columns)}")

            # Find protein annotation column
            protein_col = None
            for col in ['protein', 'annotation', 'product', 'description', 'AMG KO', 'AMG KO name']:
                if col in df_annot.columns:
                    protein_col = col
                    break

            if not protein_col:
                if samples_processed == 1:
                    print(f"  ⚠️  Warning: No recognized annotation column found in {annot_files[0].name}")
                continue

            # Debug: Show first few annotations
            if samples_processed == 1:
                print(f"  📝 Using column: '{protein_col}'")
                print(f"  📝 Sample annotations (first 5):")
                for ann in df_annot[protein_col].dropna().head(5):
                    print(f"      - {ann}")

            # Categorize each annotation
            for annotation in df_annot[protein_col].dropna():
                total_proteins += 1
                annotation_lower = str(annotation).lower()

                # Collect debug samples
                if len(debug_annotations) < 10:
                    debug_annotations.append(annotation)

                # Skip hypothetical/unknown proteins
                if any(x in annotation_lower for x in ['hypothetical', 'duf', 'unknown function', 'uncharacterized', 'putative']):
                    hypothetical_count += 1
                    continue

                # Categorize by keyword matching
                categorized = False
                for category, keywords in function_keywords.items():
                    if category == 'Other':
                        continue
                    if any(keyword.lower() in annotation_lower for keyword in keywords):
                        functional_data[category] += 1
                        categorized = True
                        break

                # If not categorized and not hypothetical, mark as "Other"
                if not categorized:
                    functional_data['Other'] += 1

        except Exception as e:
            print(f"    Warning: Could not parse {annot_files[0].name}: {e}")
            continue

        if samples_processed % 100 == 0:
            print(f"    Processed {samples_processed} samples...")

    if functional_data:
        print(f"\n  ✅ Analyzed {total_proteins:,} proteins from {samples_processed} samples")
        print(f"  📊 Functional Categories:")
        for category, count in functional_data.most_common():
            pct = count / total_proteins * 100 if total_proteins > 0 else 0
            print(f"    • {category}: {count:,} ({pct:.1f}%)")
        print(f"    • Hypothetical/Unknown: {hypothetical_count:,} ({hypothetical_count/total_proteins*100:.1f}%)")

        functional_stats = {
            'counts': dict(functional_data),
            'percentages': {cat: (count / total_proteins * 100) for cat, count in functional_data.items()},
            'hypothetical_count': hypothetical_count,
            'total_proteins': total_proteins,
            'samples_processed': samples_processed
        }

        return functional_stats
    else:
        print("  ⚠️  No functional annotations found")
        return None

def create_visualizations(df, stats, output_dir):
    """Create comprehensive visualization dashboard."""
    print("\n📊 Generating visualizations...")

    # Validate required columns
    required_cols = ['type', 'quality', 'sample_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"  ❌ Error: Missing required columns: {missing_cols}")
        print(f"  Available columns: {list(df.columns)}")
        raise ValueError(f"DataFrame missing required columns: {missing_cols}")

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")

    # Create figure with multiple subplots - expanded for functional categories
    has_functional = stats.get('functional') is not None
    fig = plt.figure(figsize=(24, 16) if has_functional else (20, 12))
    gs = fig.add_gridspec(4 if has_functional else 3, 3, hspace=0.3, wspace=0.3)

    # Title
    fig.suptitle('Comprehensive Prophage Analysis Dashboard\nKansas 2021-2025 NARMS Dataset',
                 fontsize=20, fontweight='bold', y=0.98)

    # 1. Prophage Type Distribution (Pie Chart)
    ax1 = fig.add_subplot(gs[0, 0])
    type_counts = df['type'].value_counts()
    colors_type = ['#FF6B6B', '#4ECDC4', '#95E1D3']
    wedges, texts, autotexts = ax1.pie(type_counts.values, labels=type_counts.index,
                                         autopct='%1.1f%%', colors=colors_type[:len(type_counts)],
                                         startangle=90, textprops={'fontsize': 10, 'weight': 'bold'})
    ax1.set_title('Prophage Lifestyle Types', fontsize=12, fontweight='bold', pad=10)

    # 2. Prophage Quality Distribution (Pie Chart)
    ax2 = fig.add_subplot(gs[0, 1])
    quality_counts = df['quality'].value_counts()
    colors_quality = ['#FFD93D', '#6BCB77', '#4D96FF', '#C3C3C3']
    wedges, texts, autotexts = ax2.pie(quality_counts.values, labels=quality_counts.index,
                                         autopct='%1.1f%%', colors=colors_quality[:len(quality_counts)],
                                         startangle=90, textprops={'fontsize': 10, 'weight': 'bold'})
    ax2.set_title('Prophage Quality Assessment', fontsize=12, fontweight='bold', pad=10)

    # 3. Sample Coverage (Pie Chart)
    ax3 = fig.add_subplot(gs[0, 2])
    coverage_data = [stats['overall']['samples_with_prophages'],
                     stats['overall']['samples_without_prophages']]
    coverage_labels = ['With Prophages', 'Without Prophages']
    colors_coverage = ['#95E1D3', '#E8E8E8']
    wedges, texts, autotexts = ax3.pie(coverage_data, labels=coverage_labels,
                                         autopct='%1.1f%%', colors=colors_coverage,
                                         startangle=90, textprops={'fontsize': 10, 'weight': 'bold'})
    ax3.set_title(f'Sample Coverage (n={stats["overall"]["samples_with_prophages"] + stats["overall"]["samples_without_prophages"]})',
                  fontsize=12, fontweight='bold', pad=10)

    # 4. Prophages per Sample Distribution (Bar Chart)
    ax4 = fig.add_subplot(gs[1, 0])
    prophages_per_sample = df.groupby('sample_id').size()
    bins = [0, 1, 5, 10, 20, prophages_per_sample.max() + 1]
    labels = ['1', '2-5', '6-10', '11-20', '20+']
    prophage_bins = pd.cut(prophages_per_sample, bins=bins, labels=labels, include_lowest=True)
    bin_counts = prophage_bins.value_counts().sort_index()

    colors_bins = ['#FF6B6B', '#FFA07A', '#FFD93D', '#6BCB77', '#4D96FF']
    ax4.bar(range(len(bin_counts)), bin_counts.values, color=colors_bins[:len(bin_counts)])
    ax4.set_xticks(range(len(bin_counts)))
    ax4.set_xticklabels(bin_counts.index, fontsize=10)
    ax4.set_xlabel('Number of Prophages', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Number of Samples', fontsize=11, fontweight='bold')
    ax4.set_title(f'Prophages per Sample Distribution\n(Mean: {prophages_per_sample.mean():.1f})',
                  fontsize=12, fontweight='bold', pad=10)
    ax4.grid(axis='y', alpha=0.3)

    # 5. Prophage Type by Quality (Stacked Bar)
    ax5 = fig.add_subplot(gs[1, 1])
    try:
        # Create crosstab and verify it has data
        type_quality_crosstab = pd.crosstab(df['type'], df['quality'])

        # Check if crosstab is empty or has no data
        if type_quality_crosstab.empty or type_quality_crosstab.sum().sum() == 0:
            # Fallback: show simple message
            ax5.text(0.5, 0.5, 'Insufficient data for\nType x Quality crosstab',
                    ha='center', va='center', fontsize=12, transform=ax5.transAxes)
            ax5.set_title('Prophage Type by Quality', fontsize=12, fontweight='bold', pad=10)
        else:
            # Plot crosstab
            type_quality_crosstab.plot(kind='bar', stacked=True, ax=ax5,
                                        color=['#FFD93D', '#6BCB77', '#4D96FF', '#C3C3C3'])
            ax5.set_xlabel('Prophage Type', fontsize=11, fontweight='bold')
            ax5.set_ylabel('Count', fontsize=11, fontweight='bold')
            ax5.set_title('Prophage Type by Quality', fontsize=12, fontweight='bold', pad=10)
            ax5.legend(title='Quality', loc='upper right', fontsize=9)
            ax5.grid(axis='y', alpha=0.3)
            plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')
    except Exception as e:
        # Fallback on any error
        print(f"  Warning: Could not create Type x Quality crosstab: {e}")
        ax5.text(0.5, 0.5, 'Error creating crosstab\nSee log for details',
                ha='center', va='center', fontsize=12, transform=ax5.transAxes)
        ax5.set_title('Prophage Type by Quality', fontsize=12, fontweight='bold', pad=10)

    # 6. Top 15 Samples by Prophage Count (Horizontal Bar)
    ax6 = fig.add_subplot(gs[1, 2])
    top_samples = prophages_per_sample.nlargest(15).sort_values()
    ax6.barh(range(len(top_samples)), top_samples.values, color='#4ECDC4')
    ax6.set_yticks(range(len(top_samples)))
    ax6.set_yticklabels(top_samples.index, fontsize=8)
    ax6.set_xlabel('Number of Prophages', fontsize=11, fontweight='bold')
    ax6.set_title('Top 15 Samples by Prophage Count', fontsize=12, fontweight='bold', pad=10)
    ax6.grid(axis='x', alpha=0.3)

    # 7. Functional Categories (if available)
    if has_functional and stats['functional']:
        # 7a. Functional Categories Pie Chart
        ax7a = fig.add_subplot(gs[2, 0])
        func_counts = Counter(stats['functional']['counts'])
        colors_func = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF']
        wedges, texts, autotexts = ax7a.pie(func_counts.values(), labels=func_counts.keys(),
                                             autopct='%1.1f%%', colors=colors_func[:len(func_counts)],
                                             startangle=90, textprops={'fontsize': 9, 'weight': 'bold'})
        ax7a.set_title('Prophage Functional Categories\n(Characterized Proteins)',
                       fontsize=12, fontweight='bold', pad=10)

        # 7b. Functional Categories Bar Chart
        ax7b = fig.add_subplot(gs[2, 1:])
        categories = list(stats['functional']['counts'].keys())
        counts = [stats['functional']['counts'][c] for c in categories]
        bars = ax7b.barh(range(len(categories)), counts, color=colors_func[:len(categories)])
        ax7b.set_yticks(range(len(categories)))
        ax7b.set_yticklabels(categories, fontsize=10)
        ax7b.set_xlabel('Number of Proteins', fontsize=11, fontweight='bold')
        ax7b.set_title(f'Prophage Protein Functions\n({stats["functional"]["total_proteins"]:,} total proteins analyzed)',
                       fontsize=12, fontweight='bold', pad=10)
        ax7b.grid(axis='x', alpha=0.3)

        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            pct = stats['functional']['percentages'][categories[i]]
            ax7b.text(bar.get_width() + max(counts)*0.01, bar.get_y() + bar.get_height()/2,
                     f'{count:,} ({pct:.1f}%)', va='center', fontsize=9)

    # 8. Summary Statistics Box
    summary_row = 3 if has_functional else 2
    ax8 = fig.add_subplot(gs[summary_row, :])
    ax8.axis('off')

    summary_text = f"""
    📊 SUMMARY STATISTICS

    Overall:
    • Total Prophages: {stats['overall']['total_prophages']:,}
    • Samples with Prophages: {stats['overall']['samples_with_prophages']:,} ({stats['overall']['pct_samples_with_prophages']:.1f}%)
    • Average Prophages per Sample: {stats['overall']['avg_prophages_per_sample']:.2f}

    Prophage Types:
    {chr(10).join([f"    • {ptype}: {count:,} ({stats['types']['percentages'][ptype]:.1f}%)" for ptype, count in stats['types']['counts'].items()])}

    Quality Distribution:
    {chr(10).join([f"    • {quality}: {count:,} ({stats['quality']['percentages'][quality]:.1f}%)" for quality, count in stats['quality']['counts'].items()])}

    Prophages per Sample:
    • Min: {stats['patterns']['min']}, Max: {stats['patterns']['max']}, Median: {stats['patterns']['median']:.1f}
    • Mean: {stats['patterns']['mean']:.2f} ± {stats['patterns']['std']:.2f} (std dev)
    """

    if has_functional and stats['functional']:
        summary_text += f"""
    Functional Categories (Top 3):
    {chr(10).join([f"    • {cat}: {count:,} ({stats['functional']['percentages'][cat]:.1f}%)"
                   for cat, count in Counter(stats['functional']['counts']).most_common(3)])}
    • Hypothetical/Unknown: {stats['functional']['hypothetical_count']:,} ({stats['functional']['hypothetical_count']/stats['functional']['total_proteins']*100:.1f}%)
    """

    ax8.text(0.05, 0.95, summary_text, transform=ax8.transAxes,
             fontsize=11, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    # Save figure
    output_file = output_dir / "prophage_comprehensive_dashboard.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Dashboard saved to: {output_file}")
    return output_file

def generate_html_report(df, stats, output_dir):
    """Generate interactive HTML report."""
    print("\n📄 Generating HTML report...")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prophage Analysis Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
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
            margin: 0;
            font-size: 2.5em;
        }}
        header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px;
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
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 1em;
            opacity: 0.95;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f7fafc;
        }}
        .dashboard-img {{
            width: 100%;
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        .info-box {{
            background: #f8f9fa;
            border-left: 5px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .normalization-toggle {{
            background: #f0f4ff;
            border: 2px solid #667eea;
            border-radius: 10px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
        }}
        .normalization-toggle h3 {{
            color: #667eea;
            margin: 0 0 15px 0;
            font-size: 1.3em;
        }}
        .toggle-options {{
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }}
        .toggle-option {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        }}
        .toggle-option input[type="radio"] {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}
        .toggle-option label {{
            font-size: 1.1em;
            font-weight: 500;
            cursor: pointer;
        }}
        .current-mode {{
            background: #d1fae5;
            border-left: 5px solid #10b981;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            font-weight: bold;
            color: #065f46;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🦠 Prophage Analysis Dashboard</h1>
            <p>Kansas 2021-2025 NARMS Dataset</p>
            <p>Comprehensive Prophage Distribution & Characteristics</p>
        </header>

        <div class="content">
            <section class="section">
                <h2>📊 Key Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Prophages</div>
                        <div class="stat-value">{stats['overall']['total_prophages']:,}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Samples with Prophages</div>
                        <div class="stat-value">{stats['overall']['samples_with_prophages']}</div>
                        <div class="stat-label">{stats['overall']['pct_samples_with_prophages']:.1f}% of samples</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Avg Prophages/Sample</div>
                        <div class="stat-value">{stats['overall']['avg_prophages_per_sample']:.1f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Max Prophages in Sample</div>
                        <div class="stat-value">{stats['patterns']['max']}</div>
                    </div>
                </div>
            </section>

            <section class="section">
                <div class="normalization-toggle">
                    <h3>📊 Display Mode</h3>
                    <div class="toggle-options">
                        <div class="toggle-option">
                            <input type="radio" id="mode-total" name="display-mode" value="total" checked>
                            <label for="mode-total">Total Counts</label>
                        </div>
                        <div class="toggle-option">
                            <input type="radio" id="mode-pergenome" name="display-mode" value="pergenome">
                            <label for="mode-pergenome">Per-Genome</label>
                        </div>
                        <div class="toggle-option">
                            <input type="radio" id="mode-unique" name="display-mode" value="unique">
                            <label for="mode-unique">Unique per Genome</label>
                        </div>
                    </div>

                    <div class="current-mode" id="current-mode-display">
                        Current Mode: <span id="mode-name">Total Counts</span> - <span id="mode-description">Raw sum of all features</span>
                    </div>

                    <div class="info-box" style="text-align: left;">
                        <strong>Display Modes:</strong>
                        <ul>
                            <li><strong>Total Counts:</strong> Raw sum of all features across all samples</li>
                            <li><strong>Per-Genome:</strong> Average number of features per sample (total / {stats['types']['num_samples']} samples)</li>
                            <li><strong>Unique per Genome:</strong> Percentage of samples containing each feature type</li>
                        </ul>
                    </div>
                </div>
            </section>

            <section class="section">
                <h2>📈 Visual Dashboard</h2>
                <img src="prophage_comprehensive_dashboard.png" alt="Prophage Dashboard" class="dashboard-img">
            </section>

            <section class="section">
                <h2>🔬 Prophage Type Distribution</h2>
                <table id="prophage-type-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th class="count-column">Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for ptype, count in stats['types']['counts'].items():
        pct = stats['types']['percentages'][ptype]
        html_content += f"""
                        <tr>
                            <td><strong>{ptype}</strong></td>
                            <td>{count:,}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

    html_content += """
                    </tbody>
                </table>

                <div class="info-box">
                    <strong>💡 What are lytic vs lysogenic prophages?</strong>
                    <ul>
                        <li><strong>Lytic:</strong> Prophages that replicate and lyse (burst) the host cell to release new virions</li>
                        <li><strong>Lysogenic:</strong> Prophages that integrate into the host chromosome and replicate along with it</li>
                    </ul>
                </div>
            </section>

            <section class="section">
                <h2>💎 Quality Assessment</h2>
                <table id="prophage-quality-table">
                    <thead>
                        <tr>
                            <th>Quality</th>
                            <th class="count-column">Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for quality, count in stats['quality']['counts'].items():
        pct = stats['quality']['percentages'][quality]
        html_content += f"""
                        <tr>
                            <td><strong>{quality}</strong></td>
                            <td>{count:,}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

    html_content += f"""
                    </tbody>
                </table>
            </section>

            <section class="section">
                <h2>📊 Sample Distribution</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Prophages per Sample</th>
                            <th>Number of Samples</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    prophages_per_sample = df.groupby('sample_id').size()
    for bin_label, count in stats['patterns']['distribution'].items():
        pct = count / len(prophages_per_sample) * 100
        html_content += f"""
                        <tr>
                            <td><strong>{bin_label}</strong></td>
                            <td>{count}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

    html_content += f"""
                    </tbody>
                </table>

                <div class="info-box">
                    <strong>📈 Distribution Statistics:</strong>
                    <ul>
                        <li>Mean: {stats['patterns']['mean']:.2f} prophages per sample</li>
                        <li>Median: {stats['patterns']['median']:.1f} prophages per sample</li>
                        <li>Standard Deviation: {stats['patterns']['std']:.2f}</li>
                        <li>Range: {stats['patterns']['min']} - {stats['patterns']['max']} prophages</li>
                    </ul>
                </div>
            </section>

            <section class="section">
                <h2>🎯 Key Findings</h2>
                <div class="info-box">
                    <h3>Summary</h3>
                    <ul>
                        <li><strong>High Prophage Prevalence:</strong> {stats['overall']['pct_samples_with_prophages']:.1f}% of samples contain prophages, indicating widespread lysogenic bacteriophage integration</li>
                        <li><strong>Average Burden:</strong> Samples with prophages carry an average of {stats['overall']['avg_prophages_per_sample']:.1f} prophage regions</li>
                        <li><strong>Variable Load:</strong> Prophage burden varies from {stats['patterns']['min']} to {stats['patterns']['max']} prophages per sample</li>
                        <li><strong>Quality Distribution:</strong> Most prophages are classified in quality categories that reflect VIBRANT's confidence in predictions</li>
                    </ul>
                </div>
            </section>
"""

    # Add functional categories section if available
    if stats.get('functional'):
        html_content += """
            <section class="section">
                <h2>🧬 Prophage Functional Categories</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Functional Category</th>
                            <th>Protein Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for category, count in Counter(stats['functional']['counts']).most_common():
            pct = stats['functional']['percentages'][category]
            html_content += f"""
                        <tr>
                            <td><strong>{category}</strong></td>
                            <td>{count:,}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

        html_content += f"""
                        <tr style="background: #f0f0f0;">
                            <td><strong>Hypothetical/Unknown</strong></td>
                            <td>{stats['functional']['hypothetical_count']:,}</td>
                            <td>{stats['functional']['hypothetical_count']/stats['functional']['total_proteins']*100:.1f}%</td>
                        </tr>
                    </tbody>
                </table>

                <div class="info-box">
                    <strong>🔬 Functional Analysis:</strong>
                    <ul>
                        <li>Total Proteins Analyzed: {stats['functional']['total_proteins']:,}</li>
                        <li>Samples Processed: {stats['functional']['samples_processed']}</li>
                        <li><strong>DNA Packaging:</strong> Proteins involved in packaging viral DNA into capsids</li>
                        <li><strong>Structural:</strong> Capsid, tail, and virion structural components</li>
                        <li><strong>Lysis:</strong> Proteins that lyse the host cell to release virions</li>
                        <li><strong>Regulation:</strong> Transcriptional regulators and repressors</li>
                        <li><strong>DNA Modification:</strong> Recombination, replication, and DNA manipulation</li>
                        <li><strong>Tail Fiber:</strong> Host recognition and receptor binding proteins</li>
                    </ul>
                </div>
            </section>
"""

    # Add JavaScript for normalization toggle
    html_content += f"""
        </div>
    </div>

    <script>
        // Data for all display modes
        const prophageTypeData = {{
            total: {dict(stats['types']['counts'])},
            pergenome: {dict(stats['types']['per_genome'])},
            unique: {dict(stats['types']['unique_per_genome'])}
        }};

        const prophageQualityData = {{
            total: {dict(stats['quality']['counts'])},
            pergenome: {dict(stats['quality']['per_genome'])},
            unique: {dict(stats['quality']['unique_per_genome'])}
        }};

        const numSamples = {stats['types']['num_samples']};

        const modeDescriptions = {{
            total: {{
                name: 'Total Counts',
                description: 'Raw sum of all features'
            }},
            pergenome: {{
                name: 'Per-Genome',
                description: 'Average per sample (Total / ' + numSamples + ')'
            }},
            unique: {{
                name: 'Unique per Genome',
                description: 'Percentage of samples with feature'
            }}
        }};

        // Update display when mode changes
        document.querySelectorAll('input[name="display-mode"]').forEach(radio => {{
            radio.addEventListener('change', function() {{
                const mode = this.value;
                updateDisplay(mode);
            }});
        }});

        function updateDisplay(mode) {{
            // Update mode description
            document.getElementById('mode-name').textContent = modeDescriptions[mode].name;
            document.getElementById('mode-description').textContent = modeDescriptions[mode].description;

            // Update tables
            updateTable('prophage-type-table', prophageTypeData[mode], mode);
            updateTable('prophage-quality-table', prophageQualityData[mode], mode);
        }}

        function updateTable(tableId, data, mode) {{
            const table = document.getElementById(tableId);
            if (!table) return;

            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {{
                const typeCell = row.cells[0].querySelector('strong');
                const countCell = row.cells[1];
                const pctCell = row.cells[2];

                if (!typeCell) return;

                const type = typeCell.textContent.trim();
                const value = data[type];

                if (value !== undefined) {{
                    if (mode === 'total') {{
                        countCell.textContent = Math.round(value).toLocaleString();
                        // Percentage calculation for total mode
                        const totalSum = Object.values(data).reduce((a, b) => a + b, 0);
                        const pct = (value / totalSum * 100).toFixed(1);
                        pctCell.textContent = pct + '%';
                    }} else if (mode === 'pergenome') {{
                        countCell.textContent = value.toFixed(2);
                        pctCell.textContent = 'avg per sample';
                    }} else if (mode === 'unique') {{
                        const pct = (value * 100).toFixed(1);
                        countCell.textContent = pct + '%';
                        const sampleCount = Math.round(value * numSamples);
                        pctCell.textContent = sampleCount.toLocaleString() + ' of ' + numSamples.toLocaleString() + ' samples';
                    }}
                }}
            }});
        }}

        // Initialize with total mode
        updateDisplay('total');
    </script>
</body>
</html>
"""

    output_file = output_dir / "prophage_comprehensive_report.html"
    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"✅ HTML report saved to: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 comprehensive_prophage_dashboard.py <base_directory>")
        print("  base_directory should contain vibrant_combined.tsv")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        sys.exit(1)

    print("=" * 80)
    print("🦠 COMPREHENSIVE PROPHAGE ANALYSIS DASHBOARD")
    print("=" * 80)
    print(f"Data directory: {base_dir}")
    print()

    # Load data
    df = load_prophage_data(base_dir)

    # Estimate total samples (you can adjust this or pass as parameter)
    total_samples = 825  # Based on your dataset

    # Calculate statistics
    print("\n" + "=" * 80)
    print("📊 CALCULATING STATISTICS")
    print("=" * 80)

    stats = {
        'overall': calculate_overall_statistics(df, total_samples),
        'types': analyze_prophage_types(df),
        'quality': analyze_prophage_quality(df),
        'patterns': analyze_sample_patterns(df, total_samples),
        'functional': parse_vibrant_annotations(base_dir)
    }

    # Create visualizations
    print("\n" + "=" * 80)
    print("🎨 GENERATING VISUALIZATIONS")
    print("=" * 80)

    dashboard_file = create_visualizations(df, stats, base_dir)
    html_file = generate_html_report(df, stats, base_dir)

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated files:")
    print(f"  📊 {dashboard_file}")
    print(f"  📄 {html_file}")
    print(f"\nTo view:")
    print(f"  1. Download the HTML file:")
    print(f"     scp tylerdoe@beocat.ksu.edu:{html_file} .")
    print(f"  2. Open in your browser")
    print()

if __name__ == "__main__":
    main()
