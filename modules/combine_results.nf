process COMBINE_RESULTS {
    publishDir "${params.outdir}/summary", mode: 'copy'

    input:
    path vibrant_results
    path diamond_results

    output:
    path "phage_analysis_summary.tsv", emit: summary
    path "phage_analysis_report.html", emit: report
    path "versions.yml", emit: versions

    script:
    """
    #!/usr/bin/env python3

import pandas as pd
import glob
import os
from pathlib import Path

# Initialize summary data
summary_data = []

# Process VIBRANT results - get both counts and quality info
vibrant_dirs = glob.glob("*_vibrant")
for vdir in vibrant_dirs:
    sample_id = vdir.replace('_vibrant', '')
    
    # Find genome quality file
    quality_files = glob.glob(f"{vdir}/VIBRANT_*/VIBRANT_results_*/VIBRANT_genome_quality_*.tsv")
    
    phage_count = 0
    lytic_count = 0
    lysogenic_count = 0
    high_quality = 0
    medium_quality = 0
    low_quality = 0
    
    if quality_files and os.path.exists(quality_files[0]):
        df = pd.read_csv(quality_files[0], sep='\\t')
        phage_count = len(df)
        
        # Count lifestyle types
        lytic_count = len(df[df['type'] == 'lytic'])
        lysogenic_count = len(df[df['type'] == 'lysogenic'])
        
        # Count quality levels
        high_quality = len(df[df['Quality'].str.contains('high', case=False, na=False)])
        medium_quality = len(df[df['Quality'].str.contains('medium', case=False, na=False)])
        low_quality = len(df[df['Quality'].str.contains('low', case=False, na=False)])
    
    summary_data.append({
        'sample_id': sample_id,
        'total_phages': phage_count,
        'lytic_phages': lytic_count,
        'lysogenic_phages': lysogenic_count,
        'high_quality': high_quality,
        'medium_quality': medium_quality,
        'low_quality': low_quality
    })

# Process DIAMOND results - get hit counts and best matches
diamond_files = glob.glob("*_diamond_results.tsv")
diamond_data = {}
for df_file in diamond_files:
    sample_id = Path(df_file).stem.replace('_diamond_results', '')
    
    if os.path.exists(df_file) and os.path.getsize(df_file) > 0:
        df = pd.read_csv(df_file, sep='\\t', header=None)
        hit_count = len(df)
        
        # Get best hit (lowest e-value, highest bit score)
        best_hit = df.iloc[0] if len(df) > 0 else None
        best_identity = best_hit[2] if best_hit is not None else 0
        best_match = best_hit[1] if best_hit is not None else "None"
        
        diamond_data[sample_id] = {
            'prophage_hits': hit_count,
            'best_identity': round(best_identity, 1),
            'best_match': best_match
        }
    else:
        diamond_data[sample_id] = {
            'prophage_hits': 0,
            'best_identity': 0,
            'best_match': "None"
        }

# Process PHANOTATE results - count predicted genes
phanotate_files = glob.glob("*_phanotate.gff")
phanotate_data = {}
for gff_file in phanotate_files:
    sample_id = Path(gff_file).stem.replace('_phanotate', '')
    
    gene_count = 0
    if os.path.exists(gff_file) and os.path.getsize(gff_file) > 0:
        with open(gff_file, 'r') as f:
            for line in f:
                if not line.startswith('>') and not line.startswith('#') and 'CDS' in line:
                    gene_count += 1
    
    phanotate_data[sample_id] = gene_count

# Combine all results
all_samples = set()
for item in summary_data:
    all_samples.add(item['sample_id'])
all_samples.update(diamond_data.keys())
all_samples.update(phanotate_data.keys())

final_summary = []
for sample in sorted(all_samples):
    # Get VIBRANT data
    vibrant_info = next((item for item in summary_data if item['sample_id'] == sample), {})
    
    row = {
        'sample_id': sample,
        'total_phages': vibrant_info.get('total_phages', 0),
        'lytic_phages': vibrant_info.get('lytic_phages', 0),
        'lysogenic_phages': vibrant_info.get('lysogenic_phages', 0),
        'high_quality': vibrant_info.get('high_quality', 0),
        'medium_quality': vibrant_info.get('medium_quality', 0),
        'low_quality': vibrant_info.get('low_quality', 0),
        'prophage_hits': diamond_data.get(sample, {}).get('prophage_hits', 0),
        'best_match_identity': diamond_data.get(sample, {}).get('best_identity', 0),
        'best_prophage_match': diamond_data.get(sample, {}).get('best_match', 'None'),
        'predicted_genes': phanotate_data.get(sample, 0)
    }
    
    final_summary.append(row)

# Create summary DataFrame and save
summary_df = pd.DataFrame(final_summary)
summary_df.to_csv('phage_analysis_summary.tsv', sep='\\t', index=False)

# Create enhanced HTML report
html_report = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Phage Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #e8f4f8; }}
        .summary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 25px; margin: 20px 0; border-radius: 10px; }}
        .summary h2 {{ color: white; border: none; }}
        .stat-box {{ display: inline-block; margin: 15px 20px; }}
        .stat-number {{ font-size: 36px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .tools {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .tools ul {{ list-style-type: none; padding-left: 0; }}
        .tools li {{ padding: 8px 0; }}
        .tools li:before {{ content: "✓ "; color: #27ae60; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🦠 Enhanced Phage Analysis Report</h1>
        
        <div class="summary">
            <h2>Analysis Overview</h2>
            <div class="stat-box">
                <div class="stat-number">{len(summary_df)}</div>
                <div class="stat-label">Samples Analyzed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{summary_df['total_phages'].sum()}</div>
                <div class="stat-label">Total Phages Identified</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{summary_df['lytic_phages'].sum()}</div>
                <div class="stat-label">Lytic Phages</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{summary_df['lysogenic_phages'].sum()}</div>
                <div class="stat-label">Lysogenic Phages</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{summary_df['prophage_hits'].sum()}</div>
                <div class="stat-label">Prophage Database Hits</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{summary_df['predicted_genes'].sum()}</div>
                <div class="stat-label">Genes Predicted</div>
            </div>
        </div>
        
        <h2>📊 Detailed Results by Sample</h2>
        {summary_df.to_html(index=False, classes='data-table', escape=False)}
        
        <h2>📈 Quality Distribution</h2>
        <p><strong>High Quality Phages:</strong> {summary_df['high_quality'].sum()} 
           ({round(summary_df['high_quality'].sum() / summary_df['total_phages'].sum() * 100, 1) if summary_df['total_phages'].sum() > 0 else 0}%)</p>
        <p><strong>Medium Quality Phages:</strong> {summary_df['medium_quality'].sum()} 
           ({round(summary_df['medium_quality'].sum() / summary_df['total_phages'].sum() * 100, 1) if summary_df['total_phages'].sum() > 0 else 0}%)</p>
        <p><strong>Low Quality Phages:</strong> {summary_df['low_quality'].sum()} 
           ({round(summary_df['low_quality'].sum() / summary_df['total_phages'].sum() * 100, 1) if summary_df['total_phages'].sum() > 0 else 0}%)</p>
        
        <div class="tools">
            <h2>🔬 Analysis Tools Used</h2>
            <ul>
                <li><strong>VIBRANT v4.0:</strong> Phage identification, lifestyle prediction (lytic/lysogenic), and quality assessment</li>
                <li><strong>DIAMOND + Prophage-DB:</strong> Homology-based prophage detection and database matching</li>
                <li><strong>PHANOTATE v1.6.7:</strong> Gene prediction and ORF identification in phage sequences</li>
            </ul>
        </div>
        
        <p style="margin-top: 30px; color: #7f8c8d; font-size: 12px;">
            Report generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
</body>
</html>
'''

with open('phage_analysis_report.html', 'w') as f:
    f.write(html_report)

# Create versions file
with open('versions.yml', 'w') as f:
    f.write('"COMBINE_RESULTS":\\n  python: "3.8+"\\n  pandas: "1.5.3"\\n')
    """
}
