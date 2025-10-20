process COMBINE_RESULTS {
    publishDir "${params.outdir}/summary", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    input:
    path amr_results
    path vibrant_results
    path diamond_results
    path abricate_summary, stageAs: 'abricate_summary.tsv'
    path quast_reports
    path busco_summaries
    path mlst_results
    path sistr_results
    path metadata, stageAs: 'sample_metadata.csv'

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
import re

# Initialize summary data
summary_data = []

# ===== PROCESS SAMPLE METADATA =====
metadata_dict = {}
if os.path.exists('sample_metadata.csv') and os.path.getsize('sample_metadata.csv') > 0:
    meta_df = pd.read_csv('sample_metadata.csv')
    for idx, row in meta_df.iterrows():
        srr_id = row['Run'] if 'Run' in meta_df.columns else None
        if srr_id:
            # Extract year from ReleaseDate if available
            year = None
            if 'ReleaseDate' in meta_df.columns and pd.notna(row['ReleaseDate']):
                try:
                    year = pd.to_datetime(row['ReleaseDate']).year
                except:
                    pass

            # Extract state from sample name (pattern: digits + STATE + digits, e.g., 19KS07)
            state = 'Unknown'
            for col in ['Sample Name', 'LibraryName', 'SampleName']:
                if col in meta_df.columns and pd.notna(row[col]):
                    match = re.search(r'\\d{{2}}([A-Z]{{2}})\\d{{2}}', str(row[col]))
                    if match:
                        state = match.group(1)
                        break

            # Extract source
            source = 'Unknown'
            for col in ['isolation_source', 'host', 'Sample Name']:
                if col in meta_df.columns and pd.notna(row[col]):
                    source = str(row[col])
                    break

            metadata_dict[srr_id] = {{
                'year': year if year else 'Unknown',
                'state': state,
                'source': source[:50] if len(source) > 50 else source,  # Limit length
                'organism': row['organism'] if 'organism' in meta_df.columns else 'Unknown'
            }}

# ===== PROCESS AMR RESULTS =====
amr_files = glob.glob("*_amr.tsv")
amr_data = {}
amr_gene_details = {}  # Store detailed gene information for each sample
for amr_file in amr_files:
    sample_id = Path(amr_file).stem.replace('_amr', '')

    if os.path.exists(amr_file) and os.path.getsize(amr_file) > 0:
        df = pd.read_csv(amr_file, sep='\\t')

        # Count AMR genes by class
        amr_count = len(df)
        amr_classes = df['Class'].value_counts().to_dict() if 'Class' in df.columns else {}

        # Get unique gene counts
        unique_genes = df['Gene symbol'].nunique() if 'Gene symbol' in df.columns else 0

        # Store detailed gene information
        gene_list = []
        for idx, row in df.iterrows():
            gene_info = {{
                'gene': row.get('Gene symbol', 'Unknown'),
                'class': row.get('Class', 'Unknown'),
                'subclass': row.get('Subclass', ''),
                'method': row.get('Method', ''),
                'identity': row.get('% Identity to reference sequence', 'N/A')
            }}
            gene_list.append(gene_info)

        amr_data[sample_id] = {{
            'total_amr_genes': amr_count,
            'unique_amr_genes': unique_genes,
            'amr_classes': amr_classes
        }}
        amr_gene_details[sample_id] = gene_list
    else:
        amr_data[sample_id] = {{
            'total_amr_genes': 0,
            'unique_amr_genes': 0,
            'amr_classes': {{}}
        }}
        amr_gene_details[sample_id] = []

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

# ===== PROCESS QUAST RESULTS =====
quast_files = glob.glob("*_quast/report.tsv")
quast_data = {}
for quast_file in quast_files:
    sample_id = Path(quast_file).parent.stem.replace('_quast', '')

    if os.path.exists(quast_file) and os.path.getsize(quast_file) > 0:
        df = pd.read_csv(quast_file, sep='\\t')
        if not df.empty and len(df.columns) > 1:
            quast_data[sample_id] = {
                'num_contigs': df.loc[df.iloc[:, 0] == '# contigs', df.columns[1]].values[0] if '# contigs' in df.iloc[:, 0].values else 0,
                'largest_contig': df.loc[df.iloc[:, 0] == 'Largest contig', df.columns[1]].values[0] if 'Largest contig' in df.iloc[:, 0].values else 0,
                'total_length': df.loc[df.iloc[:, 0] == 'Total length', df.columns[1]].values[0] if 'Total length' in df.iloc[:, 0].values else 0,
                'n50': df.loc[df.iloc[:, 0] == 'N50', df.columns[1]].values[0] if 'N50' in df.iloc[:, 0].values else 0,
                'gc_percent': df.loc[df.iloc[:, 0] == 'GC (%)', df.columns[1]].values[0] if 'GC (%)' in df.iloc[:, 0].values else 0
            }
    else:
        quast_data[sample_id] = {'num_contigs': 0, 'largest_contig': 0, 'total_length': 0, 'n50': 0, 'gc_percent': 0}

# ===== PROCESS BUSCO RESULTS =====
busco_files = glob.glob("*_busco/short_summary.*.txt")
busco_data = {}
for busco_file in busco_files:
    sample_id = Path(busco_file).parent.stem.replace('_busco', '')

    if os.path.exists(busco_file) and os.path.getsize(busco_file) > 0:
        with open(busco_file, 'r') as f:
            content = f.read()
            # Parse BUSCO summary: C:99.1%[S:98.8%,D:0.3%],F:0.3%,M:0.6%,n:124
            import re
            match = re.search(r'C:([\d.]+)%.*F:([\d.]+)%.*M:([\d.]+)%', content)
            if match:
                busco_data[sample_id] = {
                    'complete': float(match.group(1)),
                    'fragmented': float(match.group(2)),
                    'missing': float(match.group(3))
                }
            else:
                busco_data[sample_id] = {'complete': 0, 'fragmented': 0, 'missing': 0}
    else:
        busco_data[sample_id] = {'complete': 0, 'fragmented': 0, 'missing': 0}

# ===== PROCESS MLST RESULTS =====
mlst_files = glob.glob("*_mlst.tsv")
mlst_data = {}
for mlst_file in mlst_files:
    sample_id = Path(mlst_file).stem.replace('_mlst', '')

    if os.path.exists(mlst_file) and os.path.getsize(mlst_file) > 0:
        df = pd.read_csv(mlst_file, sep='\\t', header=None)
        if not df.empty and len(df.columns) >= 3:
            mlst_data[sample_id] = {
                'scheme': df.iloc[0, 1] if pd.notna(df.iloc[0, 1]) else 'Unknown',
                'st': df.iloc[0, 2] if pd.notna(df.iloc[0, 2]) else 'Unknown'
            }
    else:
        mlst_data[sample_id] = {'scheme': 'Unknown', 'st': 'Unknown'}

# ===== PROCESS SISTR RESULTS =====
sistr_files = glob.glob("*_sistr.tsv")
sistr_data = {}
for sistr_file in sistr_files:
    sample_id = Path(sistr_file).stem.replace('_sistr', '')

    if os.path.exists(sistr_file) and os.path.getsize(sistr_file) > 0:
        df = pd.read_csv(sistr_file, sep='\\t')
        if not df.empty:
            sistr_data[sample_id] = {
                'serovar': df.iloc[0]['serovar'] if 'serovar' in df.columns else 'Unknown',
                'serogroup': df.iloc[0]['serogroup'] if 'serogroup' in df.columns else 'Unknown',
                'h1': df.iloc[0]['h1'] if 'h1' in df.columns else '',
                'h2': df.iloc[0]['h2'] if 'h2' in df.columns else ''
            }
    else:
        sistr_data[sample_id] = {'serovar': 'Unknown', 'serogroup': 'Unknown', 'h1': '', 'h2': ''}

# ===== PROCESS ABRICATE SUMMARY =====
abricate_data = {}
if os.path.exists('abricate_summary.tsv') and os.path.getsize('abricate_summary.tsv') > 0:
    ab_df = pd.read_csv('abricate_summary.tsv', sep='\\t')
    if not ab_df.empty and 'NUM_FOUND' in ab_df.columns:
        for idx, row in ab_df.iterrows():
            sample_id = row.iloc[0]  # First column is sample ID
            if sample_id not in abricate_data:
                abricate_data[sample_id] = {}
            # Store database-specific counts
            db_name = row['DATABASE'] if 'DATABASE' in ab_df.columns else 'unknown'
            abricate_data[sample_id][db_name] = row['NUM_FOUND']

# ===== COMBINE ALL RESULTS =====
all_samples = set()
for item in summary_data:
    all_samples.add(item['sample_id'])
all_samples.update(diamond_data.keys())
all_samples.update(phanotate_data.keys())
all_samples.update(amr_data.keys())
all_samples.update(quast_data.keys())
all_samples.update(busco_data.keys())
all_samples.update(mlst_data.keys())
all_samples.update(sistr_data.keys())
all_samples.update(abricate_data.keys())

final_summary = []
for sample in sorted(all_samples):
    vibrant_info = next((item for item in summary_data if item['sample_id'] == sample), {})
    sample_meta = metadata_dict.get(sample, {})

    row = {
        'sample_id': sample,
        # Metadata
        'year': sample_meta.get('year', 'Unknown'),
        'state': sample_meta.get('state', 'Unknown'),
        'source': sample_meta.get('source', 'Unknown'),
        'organism': sample_meta.get('organism', 'Unknown'),
        # Assembly QC
        'num_contigs': quast_data.get(sample, {}).get('num_contigs', 'N/A'),
        'total_length': quast_data.get(sample, {}).get('total_length', 'N/A'),
        'n50': quast_data.get(sample, {}).get('n50', 'N/A'),
        'gc_percent': quast_data.get(sample, {}).get('gc_percent', 'N/A'),
        'busco_complete': busco_data.get(sample, {}).get('complete', 'N/A'),
        'busco_fragmented': busco_data.get(sample, {}).get('fragmented', 'N/A'),
        'busco_missing': busco_data.get(sample, {}).get('missing', 'N/A'),
        # Typing
        'mlst_scheme': mlst_data.get(sample, {}).get('scheme', 'Unknown'),
        'mlst_st': mlst_data.get(sample, {}).get('st', 'Unknown'),
        'sistr_serovar': sistr_data.get(sample, {}).get('serovar', 'Unknown'),
        'sistr_serogroup': sistr_data.get(sample, {}).get('serogroup', 'Unknown'),
        # AMR
        'total_amr_genes': amr_data.get(sample, {}).get('total_amr_genes', 0),
        'unique_amr_genes': amr_data.get(sample, {}).get('unique_amr_genes', 0),
        'abricate_card': abricate_data.get(sample, {}).get('card', 0),
        'abricate_ncbi': abricate_data.get(sample, {}).get('ncbi', 0),
        'abricate_resfinder': abricate_data.get(sample, {}).get('resfinder', 0),
        # Phage
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

# Prepare data for charts
import json

# AMR genes per sample (top 10 samples)
amr_per_sample = summary_df.nlargest(10, 'total_amr_genes')[['sample_id', 'total_amr_genes']]
amr_chart_labels = amr_per_sample['sample_id'].tolist()
amr_chart_data = amr_per_sample['total_amr_genes'].tolist()

# Phage lifestyle distribution
lytic_total = summary_df['lytic_phages'].sum()
lysogenic_total = summary_df['lysogenic_phages'].sum()

# BUSCO completeness per sample
busco_per_sample = summary_df[summary_df['busco_complete'] != 'N/A'].copy()
busco_per_sample['busco_complete'] = busco_per_sample['busco_complete'].astype(float)
busco_chart_labels = busco_per_sample['sample_id'].tolist()
busco_chart_data = busco_per_sample['busco_complete'].tolist()

# Top serovars
serovar_counts = summary_df[summary_df['sistr_serovar'] != 'Unknown']['sistr_serovar'].value_counts().head(5)
serovar_chart_labels = serovar_counts.index.tolist()
serovar_chart_data = serovar_counts.values.tolist()

# ===== CORRELATION ANALYSIS =====
# Calculate correlations between AMR and phage metrics
correlation_insights = []

# AMR vs Phage count
amr_phage_corr = summary_df[['total_amr_genes', 'total_phages']].corr().iloc[0, 1]
correlation_insights.append(f"AMR genes vs Total phages: {amr_phage_corr:.3f}")

# AMR vs Lysogenic phages (hypothesis: lysogenic phages may carry AMR genes)
if summary_df['lysogenic_phages'].sum() > 0:
    amr_lysogenic_corr = summary_df[['total_amr_genes', 'lysogenic_phages']].corr().iloc[0, 1]
    correlation_insights.append(f"AMR genes vs Lysogenic phages: {amr_lysogenic_corr:.3f}")

# Assembly quality vs AMR (better assemblies may detect more genes)
if summary_df['n50'].replace('N/A', 0).astype(float).sum() > 0:
    n50_numeric = summary_df['n50'].replace('N/A', 0).astype(float)
    amr_numeric = summary_df['total_amr_genes'].astype(float)
    n50_amr_corr = pd.DataFrame({{'n50': n50_numeric, 'amr': amr_numeric}}).corr().iloc[0, 1]
    correlation_insights.append(f"Assembly N50 vs AMR genes: {n50_amr_corr:.3f}")

# Samples with both AMR and phages
samples_with_both = len(summary_df[(summary_df['total_amr_genes'] > 0) & (summary_df['total_phages'] > 0)])
samples_with_amr_only = len(summary_df[(summary_df['total_amr_genes'] > 0) & (summary_df['total_phages'] == 0)])
samples_with_phage_only = len(summary_df[(summary_df['total_amr_genes'] == 0) & (summary_df['total_phages'] > 0)])
samples_with_neither = len(summary_df[(summary_df['total_amr_genes'] == 0) & (summary_df['total_phages'] == 0)])

html_report = f'''
<!DOCTYPE html>
<html>
<head>
    <title>COMPASS Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
        .chart-container {{ margin: 30px 0; padding: 20px; background-color: white; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; margin: 20px 0; }}
        canvas {{ max-height: 400px; }}
        .table-controls {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
        .table-controls input {{ padding: 8px; margin-right: 10px; border: 1px solid #ddd; border-radius: 3px; width: 300px; }}
        .table-controls select {{ padding: 8px; border: 1px solid #ddd; border-radius: 3px; }}
        th {{ cursor: pointer; user-select: none; position: relative; }}
        th:hover {{ background-color: #2980b9; }}
        th.sort-asc:after {{ content: " ▲"; position: absolute; right: 5px; }}
        th.sort-desc:after {{ content: " ▼"; position: absolute; right: 5px; }}
        .data-table {{ width: 100%; }}
        .expand-btn {{ cursor: pointer; color: #3498db; font-weight: bold; user-select: none; }}
        .expand-btn:hover {{ color: #2980b9; text-decoration: underline; }}
        .gene-details {{ background-color: #ecf0f1; padding: 15px; margin: 10px 0; border-left: 4px solid #e74c3c; }}
        .gene-details table {{ width: 100%; font-size: 12px; background-color: white; }}
        .gene-details th {{ background-color: #e74c3c; color: white; }}
        .gene-details td {{ border: 1px solid #ddd; padding: 6px; }}
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

        <div class="section" style="border-left: 4px solid #2ecc71;">
            <h2>✅ Assembly Quality Summary</h2>
            <p><strong>Average N50:</strong> {summary_df['n50'].replace('N/A', 0).astype(float).mean():.0f} bp</p>
            <p><strong>Average BUSCO Complete:</strong> {summary_df['busco_complete'].replace('N/A', 0).astype(float).mean():.1f}%</p>
            <p><strong>Average Total Length:</strong> {summary_df['total_length'].replace('N/A', 0).astype(float).mean():.0f} bp</p>
            <p><strong>Samples passing QC (BUSCO >90%):</strong> {len([x for x in summary_df['busco_complete'] if x != 'N/A' and float(x) > 90])} / {len(summary_df)}</p>
        </div>

        <div class="section" style="border-left: 4px solid #9b59b6;">
            <h2>🔬 Typing Summary</h2>
            <p><strong>Unique MLST Sequence Types:</strong> {len(summary_df['mlst_st'].unique())}</p>
            <p><strong>Unique Serovars (SISTR):</strong> {len(summary_df['sistr_serovar'].unique())}</p>
            <h3>Top 5 Sequence Types:</h3>
            <ul>
                {"".join([f"<li><strong>ST-{st}:</strong> {count} samples</li>" for st, count in summary_df[summary_df['mlst_st'] != 'Unknown']['mlst_st'].value_counts().head(5).items()])}
            </ul>
            <h3>Top 5 Serovars:</h3>
            <ul>
                {"".join([f"<li><strong>{serovar}:</strong> {count} samples</li>" for serovar, count in summary_df[summary_df['sistr_serovar'] != 'Unknown']['sistr_serovar'].value_counts().head(5).items()])}
            </ul>
        </div>

        <h2>📈 Interactive Visualizations</h2>

        <div class="chart-grid">
            <div class="chart-container">
                <h3>Top 10 Samples by AMR Genes</h3>
                <canvas id="amrChart"></canvas>
            </div>

            <div class="chart-container">
                <h3>Phage Lifestyle Distribution</h3>
                <canvas id="phageLifestyleChart"></canvas>
            </div>
        </div>

        <div class="chart-grid">
            <div class="chart-container">
                <h3>BUSCO Completeness by Sample</h3>
                <canvas id="buscoChart"></canvas>
            </div>

            <div class="chart-container">
                <h3>Top 5 Serovars</h3>
                <canvas id="serovarChart"></canvas>
            </div>
        </div>

        <div class="section" style="border-left: 4px solid #f39c12;">
            <h2>📉 Correlation Analysis: AMR & Phage Relationships</h2>

            <h3>Statistical Correlations</h3>
            <p>Pearson correlation coefficients between key metrics (ranges from -1 to +1):</p>
            <ul>
                {"".join([f"<li>{insight}</li>" for insight in correlation_insights])}
            </ul>

            <h3>Sample Distribution</h3>
            <table style="width: auto; font-size: 14px;">
                <tr>
                    <th>Category</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
                <tr>
                    <td>Samples with both AMR genes and phages</td>
                    <td>{samples_with_both}</td>
                    <td>{round(samples_with_both / len(summary_df) * 100, 1)}%</td>
                </tr>
                <tr>
                    <td>Samples with AMR genes only (no phages)</td>
                    <td>{samples_with_amr_only}</td>
                    <td>{round(samples_with_amr_only / len(summary_df) * 100, 1)}%</td>
                </tr>
                <tr>
                    <td>Samples with phages only (no AMR genes)</td>
                    <td>{samples_with_phage_only}</td>
                    <td>{round(samples_with_phage_only / len(summary_df) * 100, 1)}%</td>
                </tr>
                <tr>
                    <td>Samples with neither</td>
                    <td>{samples_with_neither}</td>
                    <td>{round(samples_with_neither / len(summary_df) * 100, 1)}%</td>
                </tr>
            </table>

            <p style="margin-top: 15px;"><em>Note: Correlation values near +1 indicate positive relationship, near -1 indicate negative relationship, and near 0 indicate no linear relationship.</em></p>
        </div>

        <h2>📊 Detailed Results by Sample</h2>

        <div class="table-controls">
            <strong>Table Controls:</strong><br><br>
            <input type="text" id="tableSearch" placeholder="Search table..." onkeyup="filterTable()">
            <select id="columnFilter" onchange="filterTable()">
                <option value="">Filter by column...</option>
                <option value="state">State</option>
                <option value="organism">Organism</option>
                <option value="sistr_serovar">Serovar</option>
                <option value="mlst_st">Sequence Type</option>
            </select>
            <button onclick="resetFilters()" style="padding: 8px 15px; background-color: #95a5a6; color: white; border: none; border-radius: 3px; cursor: pointer;">Reset Filters</button>
            <span id="rowCount" style="margin-left: 20px; font-weight: bold;"></span>
        </div>

        <div id="tableWrapper">
            {summary_df.to_html(index=False, classes='data-table', table_id='resultsTable', escape=False)}
        </div>

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
            <h3>Assembly QC</h3>
            <ul>
                <li><strong>QUAST:</strong> Assembly quality statistics (N50, contigs, length)</li>
                <li><strong>BUSCO:</strong> Genome completeness assessment</li>
            </ul>
            <h3>Typing & Characterization</h3>
            <ul>
                <li><strong>MLST:</strong> Multi-locus sequence typing for strain identification</li>
                <li><strong>SISTR:</strong> Salmonella in silico serotyping</li>
            </ul>
            <h3>Antimicrobial Resistance</h3>
            <ul>
                <li><strong>AMRFinderPlus:</strong> NCBI AMR gene identification</li>
                <li><strong>ABRicate:</strong> Multi-database AMR screening (CARD, ResFinder, NCBI, ARG-ANNOT)</li>
            </ul>
            <h3>Phage Analysis</h3>
            <ul>
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

    <script>
        // AMR Gene Details Data
        const amrGeneDetails = {json.dumps(amr_gene_details)};

        // AMR Genes per Sample Chart
        const amrCtx = document.getElementById('amrChart').getContext('2d');
        new Chart(amrCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(amr_chart_labels)},
                datasets: [{{
                    label: 'AMR Genes',
                    data: {json.dumps(amr_chart_data)},
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Number of AMR Genes' }}
                    }},
                    x: {{
                        title: {{ display: true, text: 'Sample ID' }}
                    }}
                }}
            }}
        }});

        // Phage Lifestyle Distribution Chart
        const phageCtx = document.getElementById('phageLifestyleChart').getContext('2d');
        new Chart(phageCtx, {{
            type: 'pie',
            data: {{
                labels: ['Lytic', 'Lysogenic'],
                datasets: [{{
                    data: [{lytic_total}, {lysogenic_total}],
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(155, 89, 182, 0.7)'
                    ],
                    borderColor: [
                        'rgba(52, 152, 219, 1)',
                        'rgba(155, 89, 182, 1)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ font: {{ size: 14 }} }}
                    }}
                }}
            }}
        }});

        // BUSCO Completeness Chart
        const buscoCtx = document.getElementById('buscoChart').getContext('2d');
        new Chart(buscoCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(busco_chart_labels)},
                datasets: [{{
                    label: 'BUSCO Complete %',
                    data: {json.dumps(busco_chart_data)},
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{ display: true, text: 'Completeness (%)' }}
                    }},
                    x: {{
                        title: {{ display: true, text: 'Sample ID' }}
                    }}
                }}
            }}
        }});

        // Serovar Distribution Chart
        const serovarCtx = document.getElementById('serovarChart').getContext('2d');
        new Chart(serovarCtx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(serovar_chart_labels)},
                datasets: [{{
                    data: {json.dumps(serovar_chart_data)},
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(155, 89, 182, 0.7)',
                        'rgba(241, 196, 15, 0.7)',
                        'rgba(231, 76, 60, 0.7)'
                    ],
                    borderColor: [
                        'rgba(52, 152, 219, 1)',
                        'rgba(46, 204, 113, 1)',
                        'rgba(155, 89, 182, 1)',
                        'rgba(241, 196, 15, 1)',
                        'rgba(231, 76, 60, 1)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ font: {{ size: 12 }} }}
                    }}
                }}
            }}
        }});

        // ===== TABLE SORTING AND FILTERING =====
        let sortDirection = {{}};

        // Add click handlers to table headers for sorting
        document.addEventListener('DOMContentLoaded', function() {{
            const table = document.getElementById('resultsTable');
            const headers = table.querySelectorAll('th');

            headers.forEach((header, index) => {{
                header.addEventListener('click', () => sortTable(index));
            }});

            // Add expand buttons to sample_id cells
            addExpandButtons();

            updateRowCount();
        }});

        function addExpandButtons() {{
            const table = document.getElementById('resultsTable');
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {{
                const firstCell = row.cells[0];  // sample_id column
                const sampleId = firstCell.textContent.trim();

                // Only add button if there are AMR genes for this sample
                if (amrGeneDetails[sampleId] && amrGeneDetails[sampleId].length > 0) {{
                    const expandBtn = document.createElement('span');
                    expandBtn.className = 'expand-btn';
                    expandBtn.textContent = ' [+]';
                    expandBtn.onclick = (e) => {{
                        e.stopPropagation();
                        toggleGeneDetails(sampleId, row);
                    }};
                    firstCell.appendChild(expandBtn);
                }}
            }});
        }}

        function toggleGeneDetails(sampleId, row) {{
            const existingDetails = row.nextSibling;

            if (existingDetails && existingDetails.classList && existingDetails.classList.contains('details-row')) {{
                // Remove existing details
                existingDetails.remove();
                row.cells[0].querySelector('.expand-btn').textContent = ' [+]';
            }} else {{
                // Add details
                const genes = amrGeneDetails[sampleId];
                const detailsRow = document.createElement('tr');
                detailsRow.className = 'details-row';
                const detailsCell = document.createElement('td');
                detailsCell.colSpan = row.cells.length;

                let html = '<div class="gene-details"><h4>AMR Genes Detected in ' + sampleId + '</h4>';
                html += '<table><thead><tr><th>Gene</th><th>Class</th><th>Subclass</th><th>Method</th><th>Identity %</th></tr></thead><tbody>';

                genes.forEach(gene => {{
                    html += `<tr>
                        <td>${{gene.gene}}</td>
                        <td>${{gene.class}}</td>
                        <td>${{gene.subclass || 'N/A'}}</td>
                        <td>${{gene.method}}</td>
                        <td>${{gene.identity}}</td>
                    </tr>`;
                }});

                html += '</tbody></table></div>';
                detailsCell.innerHTML = html;
                detailsRow.appendChild(detailsCell);

                row.parentNode.insertBefore(detailsRow, row.nextSibling);
                row.cells[0].querySelector('.expand-btn').textContent = ' [-]';
            }}
        }}

        function sortTable(columnIndex) {{
            const table = document.getElementById('resultsTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const header = table.querySelectorAll('th')[columnIndex];

            // Toggle sort direction
            const currentDir = sortDirection[columnIndex] || 'asc';
            const newDir = currentDir === 'asc' ? 'desc' : 'asc';
            sortDirection[columnIndex] = newDir;

            // Remove sort indicators from all headers
            table.querySelectorAll('th').forEach(h => {{
                h.classList.remove('sort-asc', 'sort-desc');
            }});

            // Add sort indicator to current header
            header.classList.add(newDir === 'asc' ? 'sort-asc' : 'sort-desc');

            // Sort rows
            rows.sort((a, b) => {{
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();

                // Try numeric comparison first
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);

                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return newDir === 'asc' ? aNum - bNum : bNum - aNum;
                }}

                // Fall back to string comparison
                return newDir === 'asc'
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            }});

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }}

        function filterTable() {{
            const searchInput = document.getElementById('tableSearch').value.toLowerCase();
            const table = document.getElementById('resultsTable');
            const rows = table.querySelectorAll('tbody tr');
            let visibleCount = 0;

            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                if (text.includes(searchInput)) {{
                    row.style.display = '';
                    visibleCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});

            document.getElementById('rowCount').textContent = `Showing ${{visibleCount}} of ${{rows.length}} samples`;
        }}

        function resetFilters() {{
            document.getElementById('tableSearch').value = '';
            document.getElementById('columnFilter').value = '';
            filterTable();
        }}

        function updateRowCount() {{
            const table = document.getElementById('resultsTable');
            const rows = table.querySelectorAll('tbody tr');
            document.getElementById('rowCount').textContent = `Showing ${{rows.length}} of ${{rows.length}} samples`;
        }}
    </script>
</body>
</html>
'''

with open('combined_analysis_report.html', 'w') as f:
    f.write(html_report)

with open('versions.yml', 'w') as f:
    f.write('"COMBINE_RESULTS":\\n  python: "3.8+"\\n  pandas: "1.5.3"\\n')
    """
}
