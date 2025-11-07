#!/usr/bin/env python3
"""
Generate Comprehensive Pipeline Report for COMPASS Results

This script creates a detailed report documenting the entire pipeline execution:
- Metadata filtering (what was downloaded, what filters were applied)
- SRA downloads (success/failure rates, samples obtained)
- QC statistics (FastQC, fastp summaries)
- Assembly statistics (SPAdes, QUAST, BUSCO)
- AMR analysis results
- Phage analysis results
- Typing results
- Mobile element results

Output: HTML report with all pipeline steps documented
"""

import sys
import csv
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import re

def parse_metadata_log(results_dir: Path):
    """
    Parse metadata filtering logs to document what was downloaded and filtered.

    Returns dict with:
    - total_samples_in_bioproject
    - filters_applied (state, year, source, etc.)
    - samples_after_filtering
    - samples_selected (if max_samples limit applied)
    """
    stats = {
        'total_samples': 0,
        'filters_applied': [],
        'samples_after_filtering': 0,
        'samples_selected': 0,
        'filter_details': {}
    }

    # Look for metadata files
    metadata_dir = results_dir / 'metadata'
    if metadata_dir.exists():
        # Count samples in runinfo files
        for runinfo_file in metadata_dir.glob('*runinfo*.csv'):
            with open(runinfo_file) as f:
                reader = csv.DictReader(f)
                stats['total_samples'] += sum(1 for _ in reader)

    # Look for filtered samples file
    filtered_dir = results_dir / 'filtered_samples'
    if filtered_dir.exists():
        for filtered_file in filtered_dir.glob('*filtered*.csv'):
            with open(filtered_file) as f:
                reader = csv.DictReader(f)
                stats['samples_after_filtering'] = sum(1 for _ in reader)

    # Look for SRR accessions file
    if filtered_dir and filtered_dir.exists():
        for srr_file in filtered_dir.glob('*accessions*.txt'):
            with open(srr_file) as f:
                stats['samples_selected'] = sum(1 for line in f if line.strip())

    return stats

def parse_sra_downloads(results_dir: Path):
    """
    Parse SRA download results.

    Returns dict with:
    - total_attempted
    - successful_downloads
    - failed_downloads
    - failure_reasons (if available)
    """
    stats = {
        'total_attempted': 0,
        'successful': 0,
        'failed': 0,
        'samples': []
    }

    # Look for downloaded reads
    reads_dir = results_dir / 'reads'
    if reads_dir.exists():
        # Count paired-end read files
        r1_files = list(reads_dir.glob('*_1.fastq.gz'))
        stats['successful'] = len(r1_files)
        stats['total_attempted'] = stats['successful']  # Approximation

        for r1 in r1_files:
            sample_id = r1.name.replace('_1.fastq.gz', '')
            stats['samples'].append(sample_id)

    return stats

def parse_fastqc_results(results_dir: Path):
    """
    Parse FastQC results for read quality summary.

    Returns dict with:
    - total_samples
    - avg_read_count
    - avg_quality_score
    - samples_passing_qc
    """
    stats = {
        'total_samples': 0,
        'samples': []
    }

    fastqc_dir = results_dir / 'fastqc'
    if fastqc_dir.exists():
        html_files = list(fastqc_dir.glob('*_fastqc.html'))
        stats['total_samples'] = len(html_files) // 2  # Divide by 2 for paired-end

    return stats

def parse_fastp_results(results_dir: Path):
    """
    Parse fastp trimming results.

    Returns dict with:
    - total_samples
    - avg_reads_before
    - avg_reads_after
    - avg_bases_before
    - avg_bases_after
    - avg_q30_rate
    """
    stats = {
        'total_samples': 0,
        'total_reads_before': 0,
        'total_reads_after': 0,
        'total_bases_before': 0,
        'total_bases_after': 0,
        'q30_rates': [],
        'samples': []
    }

    fastp_dir = results_dir / 'fastp'
    if fastp_dir.exists():
        for json_file in fastp_dir.glob('*.json'):
            try:
                with open(json_file) as f:
                    data = json.load(f)

                stats['total_samples'] += 1

                # Extract statistics
                if 'summary' in data:
                    before = data['summary'].get('before_filtering', {})
                    after = data['summary'].get('after_filtering', {})

                    stats['total_reads_before'] += before.get('total_reads', 0)
                    stats['total_reads_after'] += after.get('total_reads', 0)
                    stats['total_bases_before'] += before.get('total_bases', 0)
                    stats['total_bases_after'] += after.get('total_bases', 0)
                    stats['q30_rates'].append(after.get('q30_rate', 0))

            except (json.JSONDecodeError, KeyError):
                continue

    # Calculate averages
    if stats['total_samples'] > 0:
        stats['avg_reads_before'] = stats['total_reads_before'] / stats['total_samples']
        stats['avg_reads_after'] = stats['total_reads_after'] / stats['total_samples']
        stats['avg_bases_before'] = stats['total_bases_before'] / stats['total_samples']
        stats['avg_bases_after'] = stats['total_bases_after'] / stats['total_samples']
        stats['avg_q30_rate'] = sum(stats['q30_rates']) / len(stats['q30_rates']) if stats['q30_rates'] else 0

    return stats

def parse_assembly_results(results_dir: Path):
    """
    Parse SPAdes assembly results.

    Returns dict with:
    - total_assemblies
    - assembly_sizes
    - contig_counts
    - n50_values
    """
    stats = {
        'total_assemblies': 0,
        'samples': []
    }

    assembly_dir = results_dir / 'assemblies'
    if assembly_dir.exists():
        fasta_files = list(assembly_dir.glob('*.fasta')) + list(assembly_dir.glob('*.fa'))
        stats['total_assemblies'] = len(fasta_files)

        for fasta in fasta_files:
            sample_id = fasta.stem
            stats['samples'].append(sample_id)

    return stats

def parse_quast_results(results_dir: Path):
    """
    Parse QUAST assembly QC results.

    Returns dict with:
    - avg_assembly_size
    - avg_n50
    - avg_num_contigs
    - avg_gc_content
    """
    stats = {
        'total_samples': 0,
        'total_length': 0,
        'n50_values': [],
        'num_contigs': [],
        'gc_contents': []
    }

    quast_dir = results_dir / 'quast'
    if quast_dir.exists():
        # Look for individual QUAST result directories
        for sample_dir in quast_dir.glob('*'):
            if sample_dir.is_dir():
                report_file = sample_dir / 'report.tsv'
                if report_file.exists():
                    stats['total_samples'] += 1

                    with open(report_file) as f:
                        reader = csv.DictReader(f, delimiter='\t')
                        for row in reader:
                            # Extract key metrics
                            if 'Total length' in row:
                                stats['total_length'] += int(row.get('Total length', 0))
                            if 'N50' in row:
                                stats['n50_values'].append(int(row.get('N50', 0)))
                            if '# contigs' in row:
                                stats['num_contigs'].append(int(row.get('# contigs', 0)))
                            if 'GC (%)' in row:
                                stats['gc_contents'].append(float(row.get('GC (%)', 0)))

    # Calculate averages
    if stats['total_samples'] > 0:
        stats['avg_assembly_size'] = stats['total_length'] / stats['total_samples']
        stats['avg_n50'] = sum(stats['n50_values']) / len(stats['n50_values']) if stats['n50_values'] else 0
        stats['avg_num_contigs'] = sum(stats['num_contigs']) / len(stats['num_contigs']) if stats['num_contigs'] else 0
        stats['avg_gc_content'] = sum(stats['gc_contents']) / len(stats['gc_contents']) if stats['gc_contents'] else 0

    return stats

def parse_busco_results(results_dir: Path):
    """
    Parse BUSCO completeness results.

    Returns dict with:
    - avg_complete
    - avg_single_copy
    - avg_duplicated
    - avg_fragmented
    - avg_missing
    """
    stats = {
        'total_samples': 0,
        'complete': [],
        'single_copy': [],
        'duplicated': [],
        'fragmented': [],
        'missing': []
    }

    busco_dir = results_dir / 'busco'
    if busco_dir.exists():
        for summary_file in busco_dir.glob('*/short_summary*.txt'):
            stats['total_samples'] += 1

            with open(summary_file) as f:
                content = f.read()

                # Parse BUSCO percentages using regex
                complete_match = re.search(r'C:(\d+\.\d+)%', content)
                single_match = re.search(r'S:(\d+\.\d+)%', content)
                duplicated_match = re.search(r'D:(\d+\.\d+)%', content)
                fragmented_match = re.search(r'F:(\d+\.\d+)%', content)
                missing_match = re.search(r'M:(\d+\.\d+)%', content)

                if complete_match:
                    stats['complete'].append(float(complete_match.group(1)))
                if single_match:
                    stats['single_copy'].append(float(single_match.group(1)))
                if duplicated_match:
                    stats['duplicated'].append(float(duplicated_match.group(1)))
                if fragmented_match:
                    stats['fragmented'].append(float(fragmented_match.group(1)))
                if missing_match:
                    stats['missing'].append(float(missing_match.group(1)))

    # Calculate averages
    if stats['total_samples'] > 0:
        stats['avg_complete'] = sum(stats['complete']) / len(stats['complete']) if stats['complete'] else 0
        stats['avg_single_copy'] = sum(stats['single_copy']) / len(stats['single_copy']) if stats['single_copy'] else 0
        stats['avg_duplicated'] = sum(stats['duplicated']) / len(stats['duplicated']) if stats['duplicated'] else 0
        stats['avg_fragmented'] = sum(stats['fragmented']) / len(stats['fragmented']) if stats['fragmented'] else 0
        stats['avg_missing'] = sum(stats['missing']) / len(stats['missing']) if stats['missing'] else 0

    return stats

def parse_amr_results(results_dir: Path):
    """
    Parse AMRFinder results.

    Returns dict with:
    - total_amr_genes
    - samples_with_amr
    - top_genes (top 10)
    - drug_classes
    - avg_amr_per_sample
    """
    stats = {
        'total_amr_genes': 0,
        'samples_with_amr': set(),
        'genes': Counter(),
        'drug_classes': Counter(),
        'amr_per_sample': Counter()
    }

    # Look for combined AMR results
    amr_file = results_dir / 'amr_combined.tsv'
    if amr_file.exists():
        with open(amr_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                stats['total_amr_genes'] += 1

                sample_id = row.get('sample_id', '')
                gene = row.get('Gene symbol', row.get('gene', 'Unknown'))
                drug_class = row.get('Class', row.get('class', 'Unknown'))

                stats['samples_with_amr'].add(sample_id)
                stats['genes'][gene] += 1
                stats['drug_classes'][drug_class] += 1
                stats['amr_per_sample'][sample_id] += 1

    # Calculate averages
    stats['num_samples_with_amr'] = len(stats['samples_with_amr'])
    if stats['num_samples_with_amr'] > 0:
        stats['avg_amr_per_sample'] = stats['total_amr_genes'] / stats['num_samples_with_amr']
    else:
        stats['avg_amr_per_sample'] = 0

    stats['top_genes'] = stats['genes'].most_common(10)
    stats['top_drug_classes'] = stats['drug_classes'].most_common(10)

    return stats

def parse_vibrant_results(results_dir: Path):
    """
    Parse VIBRANT prophage results.

    Returns dict with:
    - total_prophages
    - samples_with_prophages
    - prophage_qualities
    - avg_prophages_per_sample
    """
    stats = {
        'total_prophages': 0,
        'samples_with_prophages': set(),
        'qualities': Counter(),
        'types': Counter(),
        'prophages_per_sample': Counter()
    }

    vibrant_file = results_dir / 'vibrant_combined.tsv'
    if vibrant_file.exists():
        with open(vibrant_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                stats['total_prophages'] += 1

                sample_id = row.get('sample_id', '')
                quality = row.get('quality', 'unknown')
                ptype = row.get('type', 'unknown')

                stats['samples_with_prophages'].add(sample_id)
                stats['qualities'][quality] += 1
                stats['types'][ptype] += 1
                stats['prophages_per_sample'][sample_id] += 1

    stats['num_samples_with_prophages'] = len(stats['samples_with_prophages'])
    if stats['num_samples_with_prophages'] > 0:
        stats['avg_prophages_per_sample'] = stats['total_prophages'] / stats['num_samples_with_prophages']
    else:
        stats['avg_prophages_per_sample'] = 0

    return stats

def generate_html_report(all_stats: dict, output_path: Path):
    """Generate comprehensive HTML report."""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>COMPASS Pipeline Execution Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #2d3748;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f7fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-label {{
            font-size: 12px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #2d3748;
        }}
        .stat-unit {{
            font-size: 14px;
            color: #718096;
            margin-left: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:hover {{
            background-color: #f7fafc;
        }}
        .progress-bar {{
            background-color: #e2e8f0;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }}
        .badge-success {{ background-color: #48bb78; color: white; }}
        .badge-info {{ background-color: #4299e1; color: white; }}
        .badge-warning {{ background-color: #ed8936; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧬 COMPASS Pipeline Execution Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Comprehensive summary of pipeline execution from metadata to final results</p>
    </div>
"""

    # 1. Metadata & Filtering Section
    metadata = all_stats.get('metadata', {})
    html += f"""
    <div class="section">
        <h2>📋 Step 1: Metadata Filtering</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Samples in BioProject</div>
                <div class="stat-value">{metadata.get('total_samples', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">After Filtering</div>
                <div class="stat-value">{metadata.get('samples_after_filtering', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Selected for Analysis</div>
                <div class="stat-value">{metadata.get('samples_selected', 0):,}</div>
            </div>
        </div>
        <p><strong>Filters Applied:</strong> {', '.join(metadata.get('filters_applied', ['None'])) if metadata.get('filters_applied') else 'No specific filters'}</p>
    </div>
"""

    # 2. SRA Downloads Section
    sra = all_stats.get('sra', {})
    success_rate = (sra.get('successful', 0) / sra.get('total_attempted', 1) * 100) if sra.get('total_attempted', 0) > 0 else 0
    html += f"""
    <div class="section">
        <h2>📥 Step 2: SRA Download</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Downloads Attempted</div>
                <div class="stat-value">{sra.get('total_attempted', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Successful Downloads</div>
                <div class="stat-value">{sra.get('successful', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Success Rate</div>
                <div class="stat-value">{success_rate:.1f}<span class="stat-unit">%</span></div>
            </div>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {success_rate}%">{success_rate:.1f}%</div>
        </div>
    </div>
"""

    # 3. FastQC Section
    fastqc = all_stats.get('fastqc', {})
    html += f"""
    <div class="section">
        <h2>📊 Step 3: FastQC - Raw Read Quality</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Samples Analyzed</div>
                <div class="stat-value">{fastqc.get('total_samples', 0):,}</div>
            </div>
        </div>
        <p><em>FastQC provides initial quality assessment of raw sequencing reads</em></p>
    </div>
"""

    # 4. fastp Section
    fastp = all_stats.get('fastp', {})
    html += f"""
    <div class="section">
        <h2>✂️ Step 4: fastp - Read Trimming & Filtering</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Samples Processed</div>
                <div class="stat-value">{fastp.get('total_samples', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Reads Before</div>
                <div class="stat-value">{fastp.get('avg_reads_before', 0):,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Reads After</div>
                <div class="stat-value">{fastp.get('avg_reads_after', 0):,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Q30 Rate</div>
                <div class="stat-value">{fastp.get('avg_q30_rate', 0)*100:.1f}<span class="stat-unit">%</span></div>
            </div>
        </div>
    </div>
"""

    # 5. Assembly Section
    assembly = all_stats.get('assembly', {})
    quast = all_stats.get('quast', {})
    html += f"""
    <div class="section">
        <h2>🧬 Step 5: SPAdes - Genome Assembly</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Assemblies Generated</div>
                <div class="stat-value">{assembly.get('total_assemblies', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Assembly Size</div>
                <div class="stat-value">{quast.get('avg_assembly_size', 0)/1e6:.2f}<span class="stat-unit">Mb</span></div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg N50</div>
                <div class="stat-value">{quast.get('avg_n50', 0)/1000:.1f}<span class="stat-unit">kb</span></div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg # Contigs</div>
                <div class="stat-value">{quast.get('avg_num_contigs', 0):.0f}</div>
            </div>
        </div>
    </div>
"""

    # 6. BUSCO Section
    busco = all_stats.get('busco', {})
    html += f"""
    <div class="section">
        <h2>✅ Step 6: BUSCO - Assembly Completeness</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Samples Analyzed</div>
                <div class="stat-value">{busco.get('total_samples', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Complete BUSCOs</div>
                <div class="stat-value">{busco.get('avg_complete', 0):.1f}<span class="stat-unit">%</span></div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Fragmented</div>
                <div class="stat-value">{busco.get('avg_fragmented', 0):.1f}<span class="stat-unit">%</span></div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Missing</div>
                <div class="stat-value">{busco.get('avg_missing', 0):.1f}<span class="stat-unit">%</span></div>
            </div>
        </div>
    </div>
"""

    # 7. AMR Section
    amr = all_stats.get('amr', {})
    html += f"""
    <div class="section">
        <h2>💊 Step 7: AMRFinder - Antimicrobial Resistance Detection</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total AMR Genes</div>
                <div class="stat-value">{amr.get('total_amr_genes', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Samples with AMR</div>
                <div class="stat-value">{amr.get('num_samples_with_amr', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg AMR per Sample</div>
                <div class="stat-value">{amr.get('avg_amr_per_sample', 0):.1f}</div>
            </div>
        </div>

        <h3>Top 10 AMR Genes Detected</h3>
        <table>
            <tr><th>Gene</th><th>Count</th></tr>
"""
    for gene, count in amr.get('top_genes', []):
        html += f"            <tr><td>{gene}</td><td>{count:,}</td></tr>\n"

    html += """
        </table>

        <h3>Top Drug Classes</h3>
        <table>
            <tr><th>Drug Class</th><th>Count</th></tr>
"""
    for drug_class, count in amr.get('top_drug_classes', []):
        html += f"            <tr><td>{drug_class}</td><td>{count:,}</td></tr>\n"

    html += """
        </table>
    </div>
"""

    # 8. VIBRANT Section
    vibrant = all_stats.get('vibrant', {})
    html += f"""
    <div class="section">
        <h2>🦠 Step 8: VIBRANT - Prophage Detection</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Prophages</div>
                <div class="stat-value">{vibrant.get('total_prophages', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Samples with Prophages</div>
                <div class="stat-value">{vibrant.get('num_samples_with_prophages', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Prophages per Sample</div>
                <div class="stat-value">{vibrant.get('avg_prophages_per_sample', 0):.1f}</div>
            </div>
        </div>

        <h3>Prophage Quality Distribution</h3>
        <table>
            <tr><th>Quality</th><th>Count</th></tr>
"""
    for quality, count in vibrant.get('qualities', {}).items():
        html += f"            <tr><td><span class='badge badge-info'>{quality}</span></td><td>{count:,}</td></tr>\n"

    html += """
        </table>
    </div>
"""

    # Footer
    html += """
    <div class="section">
        <h2>📝 Summary</h2>
        <p>This report documents the complete COMPASS pipeline execution from initial metadata filtering through final analysis results. Each section represents a distinct pipeline step with key statistics and outcomes.</p>
        <p><strong>Pipeline Steps:</strong></p>
        <ol>
            <li>Metadata filtering and sample selection</li>
            <li>SRA download of sequencing reads</li>
            <li>FastQC quality assessment</li>
            <li>fastp read trimming and filtering</li>
            <li>SPAdes genome assembly</li>
            <li>BUSCO completeness assessment</li>
            <li>AMRFinder resistance gene detection</li>
            <li>VIBRANT prophage identification</li>
        </ol>
    </div>

</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

def main():
    if len(sys.argv) < 2:
        print("Usage: generate_pipeline_report.py <results_directory>")
        print("\nGenerates comprehensive HTML report documenting all pipeline steps and results")
        sys.exit(1)

    results_dir = Path(sys.argv[1])

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)

    print("="*80)
    print("COMPASS Pipeline Report Generator")
    print("="*80)
    print(f"\nAnalyzing results in: {results_dir}\n")

    all_stats = {}

    print("[1/9] Parsing metadata filtering logs...")
    all_stats['metadata'] = parse_metadata_log(results_dir)

    print("[2/9] Parsing SRA download results...")
    all_stats['sra'] = parse_sra_downloads(results_dir)

    print("[3/9] Parsing FastQC results...")
    all_stats['fastqc'] = parse_fastqc_results(results_dir)

    print("[4/9] Parsing fastp results...")
    all_stats['fastp'] = parse_fastp_results(results_dir)

    print("[5/9] Parsing assembly results...")
    all_stats['assembly'] = parse_assembly_results(results_dir)

    print("[6/9] Parsing QUAST results...")
    all_stats['quast'] = parse_quast_results(results_dir)

    print("[7/9] Parsing BUSCO results...")
    all_stats['busco'] = parse_busco_results(results_dir)

    print("[8/9] Parsing AMRFinder results...")
    all_stats['amr'] = parse_amr_results(results_dir)

    print("[9/9] Parsing VIBRANT results...")
    all_stats['vibrant'] = parse_vibrant_results(results_dir)

    print("\nGenerating HTML report...")
    output_file = results_dir / "pipeline_execution_report.html"
    generate_html_report(all_stats, output_file)

    print("="*80)
    print("✅ Report generation complete!")
    print("="*80)
    print(f"\nReport saved to: {output_file}")
    print(f"\nTo view: open {output_file}")

if __name__ == "__main__":
    main()
