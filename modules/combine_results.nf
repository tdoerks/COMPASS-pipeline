process COMBINE_RESULTS {
    publishDir "${params.outdir}/summary", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    input:
    path amr_results
    path vibrant_results
    path diamond_results

    output:
    path "combined_analysis_summary.tsv", emit: summary
    path "combined_analysis_report.html", emit: report
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

# ===== PROCESS AMR RESULTS =====
amr_files = glob.glob("*_amr.tsv")
amr_data = {}
for amr_file in amr_files:
    sample_id = Path(amr_file).stem.replace('_amr', '')
    
    if os.path.exists(amr_file) and os.path.getsize(amr_file) > 0:
        df = pd.read_csv(amr_file, sep='\\t')
        
        # Count AMR genes by class
        amr_count = len(df)
        amr_classes = df['Class'].value_counts().to_dict() if 'Class' in df.columns else {}
        
        # Get unique gene counts
        unique_genes = df['Gene symbol'].nunique() if 'Gene symbol' in df.columns else 0
        
        amr_data[sample_id] = {
            'total_amr_genes': amr_count,
            'unique_amr_genes': unique_genes,
            'amr_classes': amr_classes
        }
    else:
        amr_data[sample_id] = {
            'total_amr_genes': 0,
            'unique_amr_genes': 0,
            'amr_classes': {}
        }

# ===== PROCESS VIBRANT RESULTS =====
vibrant_dirs = glob.glob("*_vibrant")
for vdir in vibrant_dirs:
    sample_id = vdir.replace('_vibrant', '')
    
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
        lytic_count = len(df[df['type'] == 'lytic'])
        lysogenic_count = len(df[df['type'] == 'lysogenic'])
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

# ===== PROCESS DIAMOND RESULTS =====
diamond_files = glob.glob("*_diamond_results.tsv")
diamond_data = {}
for df_file in diamond_files:
    sample_id = Path(df_file).stem.replace('_diamond_results', '')
    
    if os.path.exists(df_file) and os.path.getsize(df_file) > 0:
        df = pd.read_csv(df_file, sep='\\t', header=None)
        hit_count = len(df)
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

# ===== PROCESS PHANOTATE RESULTS =====
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

# ===== COMBINE ALL RESULTS =====
all_samples = set()
for item in summary_data:
    all_samples.add(item['sample_id'])
all_samples.update(diamond_data.keys())
all_samples.update(phanotate_data.keys())
all_samples.update(amr_data.keys())

final_summary = []
for sample in sorted(all_samples):
    vibrant_info = next((item for item in summary_data if item['sample_id'] == sample), {})
    
    row = {
        'sample_id': sample,
        'total_amr_genes': amr_data.get(sample, {}).get('total_amr_genes', 0),
        'unique_amr_genes': amr_data.get(sample, {}).get('unique_amr_genes', 0),
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

summary_df = pd.DataFrame(final_summary)
summary_df.to_csv('combined_analysis_summary.tsv', sep='\\t', index=False)

# ===== CREATE ENHANCED HTML REPORT =====
# Calculate AMR statistics
total_amr = summary_df['total_amr_genes'].sum()
avg_amr_per_sample = summary_df['total_amr_genes'].mean()

# Get AMR class breakdown across all samples
all_amr_classes = {}
for sample_id in amr_data:
    for cls, count in amr_data[sample_id].get('amr_classes', {}).items():
        all_amr_classes[cls] = all_amr_classes.get(cls, 0) + count

top_amr_classes = sorted(all_amr_classes.items(), key=lambda x: x[1], reverse=True)[:5]

html_report = f'''
<!DOCTYPE html>
<html>
<head>
    <title>COMPASS Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 14px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #3498db; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #e8f4f8; }}
        .summary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white; padding: 25px; margin: 20px 0; border-radius: 10px; }}
        .summary h2 {{ color: white; border: none; margin-top: 0; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; }}
        .stat-box {{ text-align: center; }}
        .stat-number {{ font-size: 36px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .section {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .amr-section {{ border-left: 4px solid #e74c3c; }}
        .phage-section {{ border-left: 4px solid #3498db; }}
        .tools {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .tools ul {{ list-style-type: none; padding-left: 0; }}
        .tools li {{ padding: 8px 0; }}
        .tools li:before {{ content: "✓ "; color: #27ae60; font-weight: bold; }}
        .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 COMPASS: Combined AMR & Phage Analysis Report</h1>

        <div class="summary">
            <h2>Analysis Overview</h2>
            <div class="stat-grid">
                <div class="stat-box">
                    <div class="stat-number">{len(summary_df)}</div>
                    <div class="stat-label">Samples</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_amr}</div>
                    <div class="stat-label">AMR Genes</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{summary_df['total_phages'].sum()}</div>
                    <div class="stat-label">Phages</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{summary_df['lytic_phages'].sum()}</div>
                    <div class="stat-label">Lytic</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{summary_df['lysogenic_phages'].sum()}</div>
                    <div class="stat-label">Lysogenic</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{summary_df['prophage_hits'].sum()}</div>
                    <div class="stat-label">Prophage Hits</div>
                </div>
            </div>
        </div>

        <h2>📊 Detailed Results by Sample</h2>
        {summary_df.to_html(index=False, classes='data-table', escape=False)}

        <div class="section amr-section">
            <h2>🦠 Antimicrobial Resistance Summary</h2>
            <p><strong>Total AMR Genes Detected:</strong> {total_amr}</p>
            <p><strong>Average per Sample:</strong> {avg_amr_per_sample:.1f}</p>
            <p><strong>Samples with AMR:</strong> {len([s for s in summary_df['total_amr_genes'] if s > 0])} / {len(summary_df)}</p>
            
            <h3>Top AMR Classes Detected:</h3>
            <ul>
                {"".join([f"<li><strong>{cls}:</strong> {count} genes</li>" for cls, count in top_amr_classes])}
            </ul>
        </div>

        <div class="section phage-section">
            <h2>🦠 Phage Analysis Summary</h2>
            
            <h3>Quality Distribution</h3>
            <p><strong>High Quality:</strong> {summary_df['high_quality'].sum()} 
               ({round(summary_df['high_quality'].sum() / summary_df['total_phages'].sum() * 100, 1) if summary_df['total_phages'].sum() > 0 else 0}%)</p>
            <p><strong>Medium Quality:</strong> {summary_df['medium_quality'].sum()} 
               ({round(summary_df['medium_quality'].sum() / summary_df['total_phages'].sum() * 100, 1) if summary_df['total_phages'].sum() > 0 else 0}%)</p>
            <p><strong>Low Quality:</strong> {summary_df['low_quality'].sum()} 
               ({round(summary_df['low_quality'].sum() / summary_df['total_phages'].sum() * 100, 1) if summary_df['total_phages'].sum() > 0 else 0}%)</p>
            
            <h3>Lifestyle Distribution</h3>
            <p><strong>Lytic Phages:</strong> {summary_df['lytic_phages'].sum()} 
               ({round(summary_df['lytic_phages'].sum() / summary_df['total_phages'].sum() * 100, 1) if summary_df['total_phages'].sum() > 0 else 0}%)</p>
            <p><strong>Lysogenic Phages:</strong> {summary_df['lysogenic_phages'].sum()} 
               ({round(summary_df['lysogenic_phages'].sum() / summary_df['total_phages'].sum() * 100, 1) if summary_df['total_phages'].sum() > 0 else 0}%)</p>
            
            <h3>Gene Prediction</h3>
            <p><strong>Total Genes Predicted:</strong> {summary_df['predicted_genes'].sum()}</p>
            <p><strong>Average per Phage:</strong> {summary_df['predicted_genes'].sum() / summary_df['total_phages'].sum():.1f} 
               (if phages detected)</p>
        </div>

        <div class="tools">
            <h2>🔬 Analysis Pipeline</h2>
            <ul>
                <li><strong>AMRFinderPlus:</strong> Antimicrobial resistance gene identification</li>
                <li><strong>VIBRANT v4.0:</strong> Phage identification and lifestyle prediction</li>
                <li><strong>DIAMOND + Prophage-DB:</strong> Homology-based prophage detection</li>
                <li><strong>CheckV:</strong> Phage sequence quality assessment</li>
                <li><strong>PHANOTATE v1.6.7:</strong> Phage gene prediction</li>
            </ul>
        </div>

        <p style="margin-top: 30px; color: #7f8c8d; font-size: 12px;">
            Report generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
</body>
</html>
'''

with open('combined_analysis_report.html', 'w') as f:
    f.write(html_report)

with open('versions.yml', 'w') as f:
    f.write('"COMBINE_RESULTS":\\n  python: "3.8+"\\n  pandas: "1.5.3"\\n')
    """
}
