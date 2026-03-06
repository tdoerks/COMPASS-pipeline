process QC_SUMMARY {
    publishDir "${params.outdir}/pipeline_info", mode: 'copy'
    container = 'quay.io/biocontainers/python:3.9'

    input:
    path qc_files

    output:
    path "assembly_qc_summary.txt", emit: summary
    path "assembly_qc_summary.csv", emit: csv
    path "assembly_qc_summary.html", emit: html

    script:
    """
    #!/usr/bin/env python3
    import json
    import glob
    from pathlib import Path

    # Collect all QC JSON files
    qc_files = glob.glob("*.json")

    if not qc_files:
        print("No QC files found!")
        # Create empty files
        Path("assembly_qc_summary.txt").touch()
        Path("assembly_qc_summary.csv").touch()
        Path("assembly_qc_summary.html").touch()
        exit(0)

    results = []
    for qc_file in qc_files:
        with open(qc_file) as f:
            results.append(json.load(f))

    # Categorize results
    passed = [r for r in results if r['qc_status'] == 'PASS']
    warned = [r for r in results if r['qc_status'] == 'WARN']
    failed = [r for r in results if r['qc_status'] == 'FAILED']

    total = len(results)
    pass_rate = len(passed) / total * 100 if total > 0 else 0

    # Generate text summary
    with open("assembly_qc_summary.txt", 'w') as f:
        f.write("="*80 + "\\n")
        f.write("ASSEMBLY QC SUMMARY\\n")
        f.write("="*80 + "\\n\\n")

        f.write(f"Total samples processed: {total}\\n")
        f.write(f"  ✅ Passed QC: {len(passed)} ({len(passed)/total*100:.1f}%)\\n")
        f.write(f"  ⚠️  QC warnings: {len(warned)} ({len(warned)/total*100:.1f}%)\\n")
        f.write(f"  ❌ Failed: {len(failed)} ({len(failed)/total*100:.1f}%)\\n")
        f.write("\\n")

        if failed:
            f.write(f"\\nFailed samples ({len(failed)}/):\\n")
            f.write("-"*80 + "\\n")
            for r in failed:
                f.write(f"  {r['sample']}: {r.get('reason', 'Unknown')}\\n")

        if warned:
            f.write(f"\\nSamples with QC warnings ({len(warned)}):\\n")
            f.write("-"*80 + "\\n")
            for r in warned:
                f.write(f"\\n  {r['sample']}:\\n")
                stats = r.get('stats', {})
                f.write(f"    Contigs: {stats.get('num_contigs', 'N/A'):,}\\n")
                f.write(f"    Total length: {stats.get('total_length', 'N/A'):,} bp\\n")
                f.write(f"    N50: {stats.get('n50', 'N/A'):,} bp\\n")
                f.write(f"    Warnings:\\n")
                for warn in r.get('qc_warnings', []):
                    f.write(f"      - {warn}\\n")

        f.write("\\n" + "="*80 + "\\n")

    # Generate CSV for easy parsing
    with open("assembly_qc_summary.csv", 'w') as f:
        f.write("sample,status,num_contigs,total_length,n50,l50,n_content_pct,warnings\\n")
        for r in results:
            sample = r['sample']
            status = r['qc_status']
            stats = r.get('stats', {})

            if stats:
                num_contigs = stats.get('num_contigs', '')
                total_length = stats.get('total_length', '')
                n50 = stats.get('n50', '')
                l50 = stats.get('l50', '')
                n_pct = stats.get('n_content_pct', '')
            else:
                num_contigs = total_length = n50 = l50 = n_pct = ''

            warnings = '; '.join(r.get('qc_warnings', [])) if 'qc_warnings' in r else r.get('reason', '')

            f.write(f"{sample},{status},{num_contigs},{total_length},{n50},{l50},{n_pct},\\"{warnings}\\"\\n")

    # Generate HTML report
    with open("assembly_qc_summary.html", 'w') as f:
        f.write(f'''<!DOCTYPE html>
<html>
<head>
    <title>Assembly QC Summary</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
        .status-pass {{ color: #10b981; font-weight: bold; }}
        .status-warn {{ color: #f59e0b; font-weight: bold; }}
        .status-fail {{ color: #ef4444; font-weight: bold; }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{ color: #333; margin-top: 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Assembly QC Summary</h1>
        <p>COMPASS Pipeline Quality Control Report</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Total Samples</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(passed)}</div>
            <div class="stat-label">✅ Passed QC</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(warned)}</div>
            <div class="stat-label">⚠️ Warnings</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(failed)}</div>
            <div class="stat-label">❌ Failed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{pass_rate:.1f}%</div>
            <div class="stat-label">Success Rate</div>
        </div>
    </div>

    <div class="section">
        <h2>Assembly Statistics</h2>
        <table>
            <thead>
                <tr>
                    <th>Sample</th>
                    <th>Status</th>
                    <th>Contigs</th>
                    <th>Total Length</th>
                    <th>N50</th>
                    <th>L50</th>
                    <th>%N</th>
                </tr>
            </thead>
            <tbody>
''')

        # Sort: failed first, then warned, then passed
        sorted_results = sorted(results, key=lambda x: {'FAILED': 0, 'WARN': 1, 'PASS': 2}[x['qc_status']])

        for r in sorted_results:
            sample = r['sample']
            status = r['qc_status']
            status_class = f"status-{'pass' if status == 'PASS' else 'warn' if status == 'WARN' else 'fail'}"

            stats = r.get('stats')
            if stats:
                f.write(f'''
                <tr>
                    <td>{sample}</td>
                    <td class="{status_class}">{status}</td>
                    <td>{stats['num_contigs']:,}</td>
                    <td>{stats['total_length']:,}</td>
                    <td>{stats['n50']:,}</td>
                    <td>{stats['l50']}</td>
                    <td>{stats['n_content_pct']}</td>
                </tr>
''')
            else:
                reason = r.get('reason', 'Unknown')
                f.write(f'''
                <tr>
                    <td>{sample}</td>
                    <td class="{status_class}">{status}</td>
                    <td colspan="5">{reason}</td>
                </tr>
''')

        f.write('''
            </tbody>
        </table>
    </div>
</body>
</html>
''')

    # Print summary to stdout
    print("\\n" + "="*80)
    print("ASSEMBLY QC SUMMARY")
    print("="*80)
    print(f"Total samples: {total}")
    print(f"  ✅ Passed QC: {len(passed)} ({len(passed)/total*100:.1f}%)")
    print(f"  ⚠️  Warnings: {len(warned)} ({len(warned)/total*100:.1f}%)")
    print(f"  ❌ Failed: {len(failed)} ({len(failed)/total*100:.1f}%)")
    print("="*80 + "\\n")
    """
}
