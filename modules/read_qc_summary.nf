process READ_QC_SUMMARY {
    publishDir "${params.outdir}/pipeline_info", mode: 'copy'
    container = 'quay.io/biocontainers/python:3.9'

    input:
    path qc_files

    output:
    path "read_qc_summary.txt", emit: summary
    path "read_qc_summary.csv", emit: csv
    path "read_qc_summary.html", emit: html

    script:
    """
    #!/usr/bin/env python3
    import json
    import glob
    from pathlib import Path

    # Collect all Read QC JSON files
    qc_files = glob.glob("*.json")

    if not qc_files:
        print("No Read QC files found!")
        # Create empty files
        Path("read_qc_summary.txt").touch()
        Path("read_qc_summary.csv").touch()
        Path("read_qc_summary.html").touch()
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
    with open("read_qc_summary.txt", 'w') as f:
        f.write("="*80 + "\\n")
        f.write("READ QC SUMMARY (Pre-Assembly Filtering)\\n")
        f.write("="*80 + "\\n\\n")

        f.write(f"Total samples processed: {total}\\n")
        f.write(f"  ✅ Passed Read QC: {len(passed)} ({len(passed)/total*100:.1f}%)\\n")
        f.write(f"  ⚠️  QC warnings: {len(warned)} ({len(warned)/total*100:.1f}%)\\n")
        f.write(f"  ❌ Failed (insufficient quality): {len(failed)} ({len(failed)/total*100:.1f}%)\\n")
        f.write("\\n")

        if failed:
            f.write(f"\\nSamples with insufficient read quality ({len(failed)}):\\n")
            f.write("-"*80 + "\\n")
            for r in failed:
                f.write(f"\\n  {r['sample']}:\\n")
                stats = r.get('stats', {})
                if stats:
                    f.write(f"    Reads after filtering: {stats.get('reads_after_filtering', 0):,}\\n")
                    f.write(f"    Bases after filtering: {stats.get('bases_after_filtering', 0):,} bp\\n")
                    f.write(f"    Survival rate: {stats.get('survival_rate', 0):.1%}\\n")
                    f.write(f"    Q30 rate: {stats.get('q30_rate', 0):.1%}\\n")
                f.write(f"    Failures:\\n")
                for failure in r.get('qc_failures', [r.get('reason', 'Unknown')]):
                    f.write(f"      - {failure}\\n")

        f.write("\\n" + "="*80 + "\\n")

    # Generate CSV
    with open("read_qc_summary.csv", 'w') as f:
        f.write("sample,status,reads_before,reads_after,bases_after,q30_rate,survival_rate,mean_length,issues\\n")
        for r in results:
            sample = r['sample']
            status = r['qc_status']
            stats = r.get('stats', {})

            if stats:
                reads_before = stats.get('reads_before_filtering', '')
                reads_after = stats.get('reads_after_filtering', '')
                bases_after = stats.get('bases_after_filtering', '')
                q30 = stats.get('q30_rate', '')
                survival = stats.get('survival_rate', '')
                mean_len = stats.get('read_length_mean', '')
            else:
                reads_before = reads_after = bases_after = q30 = survival = mean_len = ''

            issues = []
            if 'qc_failures' in r:
                issues.extend(r['qc_failures'])
            if 'qc_warnings' in r:
                issues.extend(r['qc_warnings'])
            if not issues and 'reason' in r:
                issues.append(r['reason'])

            issues_str = '; '.join(issues)

            f.write(f"{sample},{status},{reads_before},{reads_after},{bases_after},{q30},{survival},{mean_len},\\\"{issues_str}\\\"\\n")

    # Generate HTML report
    with open("read_qc_summary.html", 'w') as f:
        f.write(f'''<!DOCTYPE html>
<html>
<head>
    <title>Read QC Summary</title>
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
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Read QC Summary</h1>
        <p>Pre-Assembly Quality Filtering</p>
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
            <div class="stat-label">Pass Rate</div>
        </div>
    </div>

    <div class="section">
        <h2>Read Quality Statistics</h2>
        <table>
            <thead>
                <tr>
                    <th>Sample</th>
                    <th>Status</th>
                    <th>Reads After</th>
                    <th>Bases After</th>
                    <th>Q30 Rate</th>
                    <th>Survival</th>
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
                    <td>{stats['reads_after_filtering']:,}</td>
                    <td>{stats['bases_after_filtering']:,}</td>
                    <td>{stats['q30_rate']:.1%}</td>
                    <td>{stats['survival_rate']:.1%}</td>
                </tr>
''')
            else:
                reason = r.get('reason', 'Unknown')
                f.write(f'''
                <tr>
                    <td>{sample}</td>
                    <td class="{status_class}">{status}</td>
                    <td colspan="4">{reason}</td>
                </tr>
''')

        f.write('''
            </tbody>
        </table>
    </div>
</body>
</html>
''')

    # Print summary
    print("\\n" + "="*80)
    print("READ QC SUMMARY")
    print("="*80)
    print(f"Total samples: {total}")
    print(f"  ✅ Passed: {len(passed)} ({len(passed)/total*100:.1f}%)")
    print(f"  ⚠️  Warnings: {len(warned)} ({len(warned)/total*100:.1f}%)")
    print(f"  ❌ Failed: {len(failed)} ({len(failed)/total*100:.1f}%)")
    print("="*80 + "\\n")
    """
}
