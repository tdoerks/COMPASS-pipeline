process BUSCO_QC_SUMMARY {
    publishDir "${params.outdir}/pipeline_info", mode: 'copy'
    container = 'quay.io/biocontainers/python:3.9'

    input:
    path qc_files

    output:
    path "busco_qc_summary.txt", emit: summary
    path "busco_qc_summary.csv", emit: csv
    path "busco_qc_summary.html", emit: html

    script:
    """
    #!/usr/bin/env python3
    import json
    import glob
    from pathlib import Path

    # Collect all BUSCO QC JSON files
    qc_files = glob.glob("*.json")

    if not qc_files:
        print("No BUSCO QC files found!")
        # Create empty files
        Path("busco_qc_summary.txt").touch()
        Path("busco_qc_summary.csv").touch()
        Path("busco_qc_summary.html").touch()
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
    with open("busco_qc_summary.txt", 'w') as f:
        f.write("="*80 + "\\n")
        f.write("BUSCO QC SUMMARY (Contamination Detection)\\n")
        f.write("="*80 + "\\n\\n")

        f.write(f"Total samples processed: {total}\\n")
        f.write(f"  ✅ Passed QC: {len(passed)} ({len(passed)/total*100:.1f}%)\\n")
        f.write(f"  ⚠️  QC warnings: {len(warned)} ({len(warned)/total*100:.1f}%)\\n")
        f.write(f"  ❌ Failed (contaminated): {len(failed)} ({len(failed)/total*100:.1f}%)\\n")
        f.write("\\n")

        if failed:
            f.write(f"\\nContaminated/Low-quality samples ({len(failed)}):\\n")
            f.write("-"*80 + "\\n")
            for r in failed:
                f.write(f"\\n  {r['sample']}:\\n")
                stats = r.get('stats', {})
                if stats:
                    f.write(f"    Complete: {stats.get('complete_pct', 'N/A'):.1f}%\\n")
                    f.write(f"    Duplicated: {stats.get('duplicated_pct', 'N/A'):.1f}% ({stats.get('duplicated_count', 'N/A')} BUSCOs)\\n")
                    f.write(f"    Fragmented: {stats.get('fragmented_pct', 'N/A'):.1f}%\\n")
                    f.write(f"    Missing: {stats.get('missing_pct', 'N/A'):.1f}%\\n")
                f.write(f"    Failures:\\n")
                for failure in r.get('qc_failures', [r.get('reason', 'Unknown')]):
                    f.write(f"      - {failure}\\n")

        if warned:
            f.write(f"\\nSamples with BUSCO QC warnings ({len(warned)}):\\n")
            f.write("-"*80 + "\\n")
            for r in warned:
                f.write(f"\\n  {r['sample']}:\\n")
                stats = r.get('stats', {})
                if stats:
                    f.write(f"    Complete: {stats.get('complete_pct', 'N/A'):.1f}%\\n")
                    f.write(f"    Duplicated: {stats.get('duplicated_pct', 'N/A'):.1f}% ({stats.get('duplicated_count', 'N/A')} BUSCOs)\\n")
                    f.write(f"    Fragmented: {stats.get('fragmented_pct', 'N/A'):.1f}%\\n")
                f.write(f"    Warnings:\\n")
                for warn in r.get('qc_warnings', []):
                    f.write(f"      - {warn}\\n")

        f.write("\\n" + "="*80 + "\\n")

    # Generate CSV for easy parsing
    with open("busco_qc_summary.csv", 'w') as f:
        f.write("sample,status,lineage,complete_pct,single_pct,duplicated_pct,duplicated_count,fragmented_pct,missing_pct,total_buscos,issues\\n")
        for r in results:
            sample = r['sample']
            status = r['qc_status']
            stats = r.get('stats', {})

            if stats:
                lineage = stats.get('lineage', '')
                complete = stats.get('complete_pct', '')
                single = stats.get('complete_single_pct', '')
                dup_pct = stats.get('duplicated_pct', '')
                dup_count = stats.get('duplicated_count', '')
                frag = stats.get('fragmented_pct', '')
                miss = stats.get('missing_pct', '')
                total = stats.get('total_buscos', '')
            else:
                lineage = complete = single = dup_pct = dup_count = frag = miss = total = ''

            issues = []
            if 'qc_failures' in r:
                issues.extend(r['qc_failures'])
            if 'qc_warnings' in r:
                issues.extend(r['qc_warnings'])
            if not issues and 'reason' in r:
                issues.append(r['reason'])

            issues_str = '; '.join(issues)

            f.write(f"{sample},{status},{lineage},{complete},{single},{dup_pct},{dup_count},{frag},{miss},{total},\\\"{issues_str}\\\"\\n")

    # Generate HTML report
    with open("busco_qc_summary.html", 'w') as f:
        f.write(f'''<!DOCTYPE html>
<html>
<head>
    <title>BUSCO QC Summary</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1400px;
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
            font-size: 0.9rem;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
            font-size: 0.85rem;
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
        .contamination-alert {{
            background: #fee;
            border-left: 4px solid #ef4444;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .quality-ok {{
            background: #efe;
            border-left: 4px solid #10b981;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧬 BUSCO QC Summary</h1>
        <p>Contamination Detection & Quality Assessment</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Total Samples</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(passed)}</div>
            <div class="stat-label">✅ Clean (Passed)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(warned)}</div>
            <div class="stat-label">⚠️ Warnings</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(failed)}</div>
            <div class="stat-label">❌ Contaminated/Failed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{pass_rate:.1f}%</div>
            <div class="stat-label">Clean Rate</div>
        </div>
    </div>
''')

        if failed:
            avg_dup = sum(r['stats']['duplicated_pct'] for r in failed if 'stats' in r and r['stats']) / len(failed)
            f.write(f'''
    <div class="contamination-alert">
        <h3>⚠️ Contamination Alert</h3>
        <p><strong>{len(failed)} samples</strong> failed BUSCO QC, likely due to contamination or quality issues.</p>
        <p>Average duplication rate in failed samples: <strong>{avg_dup:.1f}%</strong></p>
        <p>These samples should be excluded from downstream analysis or re-sequenced.</p>
    </div>
''')
        else:
            f.write('''
    <div class="quality-ok">
        <h3>✅ All Samples Clean</h3>
        <p>No contamination detected. All samples passed BUSCO quality checks.</p>
    </div>
''')

        f.write('''
    <div class="section">
        <h2>BUSCO Statistics</h2>
        <table>
            <thead>
                <tr>
                    <th>Sample</th>
                    <th>Status</th>
                    <th>Complete</th>
                    <th>Single</th>
                    <th>Duplicated</th>
                    <th>Fragmented</th>
                    <th>Missing</th>
                    <th>Total BUSCOs</th>
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
                dup_color = 'color: #ef4444; font-weight: bold;' if stats['duplicated_pct'] > 5.0 else ''
                f.write(f'''
                <tr>
                    <td>{sample}</td>
                    <td class="{status_class}">{status}</td>
                    <td>{stats['complete_pct']:.1f}%</td>
                    <td>{stats['complete_single_pct']:.1f}%</td>
                    <td style="{dup_color}">{stats['duplicated_pct']:.1f}% ({stats['duplicated_count']})</td>
                    <td>{stats['fragmented_pct']:.1f}%</td>
                    <td>{stats['missing_pct']:.1f}%</td>
                    <td>{stats['total_buscos']}</td>
                </tr>
''')
            else:
                reason = r.get('reason', 'Unknown')
                f.write(f'''
                <tr>
                    <td>{sample}</td>
                    <td class="{status_class}">{status}</td>
                    <td colspan="6">{reason}</td>
                </tr>
''')

        f.write('''
            </tbody>
        </table>
    </div>

    <div class="section">
        <h3>Threshold Information</h3>
        <ul>
            <li><strong>Duplication threshold:</strong> > 5% indicates likely contamination</li>
            <li><strong>Completeness threshold:</strong> < 80% indicates poor assembly or wrong lineage</li>
            <li><strong>Fragmentation threshold:</strong> > 10% warns of assembly fragmentation</li>
            <li><strong>Missing threshold:</strong> > 20% indicates incomplete genome</li>
        </ul>
    </div>
</body>
</html>
''')

    # Print summary to stdout
    print("\\n" + "="*80)
    print("BUSCO QC SUMMARY (Contamination Detection)")
    print("="*80)
    print(f"Total samples: {total}")
    print(f"  ✅ Clean (passed): {len(passed)} ({len(passed)/total*100:.1f}%)")
    print(f"  ⚠️  Warnings: {len(warned)} ({len(warned)/total*100:.1f}%)")
    print(f"  ❌ Contaminated/Failed: {len(failed)} ({len(failed)/total*100:.1f}%)")
    print("="*80 + "\\n")
    """
}
