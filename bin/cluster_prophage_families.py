#!/usr/bin/env python3
"""
Cluster Prophages into Families by Sequence Similarity

Instead of exact matching, clusters prophages at 90%, 95%, and 99% identity
to identify "prophage families" that are shared across samples.

Uses CD-HIT-EST for clustering, then analyzes:
1. How many prophage families exist?
2. Which families are shared across multiple samples?
3. Do families show temporal/food/species patterns?

Methods:
- 99% identity: Nearly identical prophages (same prophage, minor variants)
- 95% identity: Close relatives (same prophage type)
- 90% identity: Prophage family (related prophages)
- 80% identity: Broader prophage group

Outputs:
- Clustered FASTA files at different thresholds
- Family membership tables
- Shared family analysis
- Updated movement tracking based on families
"""

import csv
import os
import subprocess
from collections import defaultdict, Counter
from pathlib import Path
from Bio import SeqIO


def check_cdhit_installed():
    """Check if CD-HIT is installed"""
    try:
        result = subprocess.run(['cd-hit-est', '-h'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def cluster_prophages_cdhit(input_fasta, output_prefix, identity=0.95, threads=8):
    """
    Cluster prophages using CD-HIT-EST

    Parameters:
    - identity: 0.90, 0.95, 0.99 (90%, 95%, 99% nucleotide identity)
    - threads: number of CPU threads
    """
    print(f"\nClustering prophages at {identity*100:.0f}% identity...")

    output_fasta = f"{output_prefix}_{int(identity*100)}.fasta"
    output_clstr = f"{output_prefix}_{int(identity*100)}.fasta.clstr"

    # Choose word size based on identity threshold
    # CD-HIT recommendation:
    if identity >= 0.95:
        word_size = 10
    elif identity >= 0.90:
        word_size = 8
    elif identity >= 0.85:
        word_size = 7
    else:
        word_size = 6

    cmd = [
        'cd-hit-est',
        '-i', input_fasta,
        '-o', output_fasta,
        '-c', str(identity),      # Identity threshold
        '-n', str(word_size),     # Word size
        '-M', '8000',             # Memory limit (MB)
        '-T', str(threads),       # Threads
        '-d', '0',                # Full sequence name in output
        '-aS', '0.8',             # Alignment coverage for shorter sequence (80%)
        '-g', '1',                # Accurate but slower mode
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if result.returncode == 0:
            print(f"  ✅ Clustering complete: {output_fasta}")
            return output_fasta, output_clstr
        else:
            print(f"  ❌ CD-HIT failed: {result.stderr}")
            return None, None

    except subprocess.TimeoutExpired:
        print(f"  ❌ CD-HIT timed out after 1 hour")
        return None, None
    except Exception as e:
        print(f"  ❌ Error running CD-HIT: {e}")
        return None, None


def parse_cdhit_clusters(clstr_file):
    """
    Parse CD-HIT .clstr file to get cluster membership

    Returns:
    - cluster_dict: {prophage_id: cluster_id}
    - cluster_members: {cluster_id: [list of prophage_ids]}
    - representatives: {cluster_id: representative_prophage_id}
    """
    print(f"\nParsing clusters from {clstr_file}...")

    cluster_dict = {}
    cluster_members = defaultdict(list)
    representatives = {}

    current_cluster = None

    with open(clstr_file) as f:
        for line in f:
            line = line.strip()

            # New cluster
            if line.startswith('>Cluster'):
                current_cluster = int(line.split()[1])

            # Cluster member
            elif line.startswith('>'):
                # Extract sequence ID
                # Format: >0	25567nt, >SRR123_prophage_1... at 95.2%
                parts = line.split('>')
                if len(parts) >= 2:
                    seq_info = parts[1].split('...')[0]
                    prophage_id = seq_info.strip()

                    # Check if representative (marked with *)
                    is_representative = '*' in line

                    cluster_dict[prophage_id] = current_cluster
                    cluster_members[current_cluster].append(prophage_id)

                    if is_representative:
                        representatives[current_cluster] = prophage_id

    print(f"  Found {len(cluster_members)} clusters")
    print(f"  Average cluster size: {sum(len(m) for m in cluster_members.values()) / len(cluster_members):.1f}")

    return cluster_dict, cluster_members, representatives


def extract_sample_from_prophage_id(prophage_id):
    """
    Extract sample ID from prophage ID
    Assumes format: SampleID_something or SampleID_prophage_N
    """
    # Try to extract sample ID (first part before underscore)
    if '_' in prophage_id:
        return prophage_id.split('_')[0]
    return prophage_id


def analyze_cluster_sharing(cluster_members, metadata):
    """
    Analyze which clusters are shared across samples, years, organisms
    """
    print("\nAnalyzing cluster sharing patterns...")

    shared_clusters = []

    for cluster_id, members in cluster_members.items():
        # Extract sample IDs
        samples = set()
        for prophage_id in members:
            sample = extract_sample_from_prophage_id(prophage_id)
            samples.add(sample)

        if len(samples) < 2:
            continue  # Skip clusters in only 1 sample

        # Get metadata for samples in this cluster
        years = set()
        organisms = set()

        for sample in samples:
            if sample in metadata:
                years.add(metadata[sample].get('year', 'Unknown'))
                organisms.add(metadata[sample].get('organism', 'Unknown'))

        shared_clusters.append({
            'cluster_id': cluster_id,
            'n_prophages': len(members),
            'n_samples': len(samples),
            'years': sorted(years),
            'organisms': sorted(organisms),
            'crosses_years': len(years) > 1,
            'crosses_species': len(organisms) > 1,
            'members': members[:10]  # First 10 members
        })

    # Sort by number of samples
    shared_clusters.sort(key=lambda x: x['n_samples'], reverse=True)

    print(f"  Found {len(shared_clusters)} clusters shared across multiple samples")

    if shared_clusters:
        top = shared_clusters[0]
        print(f"  Most widespread cluster: {top['n_samples']} samples, {top['n_prophages']} prophages")

    return shared_clusters


def load_metadata(base_dir):
    """Load sample metadata"""
    print("Loading metadata...")

    metadata = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        metadata_file = base_path / f"results_kansas_{year}" / "filtered_samples" / "filtered_samples.csv"

        if not metadata_file.exists():
            continue

        with open(metadata_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                srr_id = row['Run']
                metadata[srr_id] = {
                    'year': year,
                    'organism': row.get('organism', 'Unknown'),
                    'sample_name': row.get('SampleName', '')
                }

    print(f"  Loaded {len(metadata)} samples")
    return metadata


def generate_cluster_report(shared_clusters, identity, output_file):
    """Generate HTML report for cluster analysis"""
    print(f"\nGenerating cluster report: {output_file}")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Prophage Family Analysis ({int(identity*100)}% identity)</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            border-radius: 15px 15px 0 0;
        }}
        .content {{ padding: 40px; }}
        h2 {{
            color: #667eea;
            font-size: 2em;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-card .value {{ font-size: 3em; font-weight: bold; margin: 10px 0; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        tbody tr:hover {{ background: #f7fafc; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            margin: 2px;
        }}
        .badge-year {{ background: #dbeafe; color: #1e40af; }}
        .badge-species {{ background: #fef3c7; color: #92400e; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 Prophage Family Analysis</h1>
            <p>Clustered at {int(identity*100)}% Nucleotide Identity</p>
        </header>

        <div class="content">
            <h2>📊 Summary Statistics</h2>

            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Shared Families</h4>
                    <div class="value">{len(shared_clusters)}</div>
                    <p>Found in 2+ samples</p>
                </div>
                <div class="stat-card">
                    <h4>Cross-Year Families</h4>
                    <div class="value">{sum(1 for c in shared_clusters if c['crosses_years'])}</div>
                    <p>Spanning multiple years</p>
                </div>
                <div class="stat-card">
                    <h4>Cross-Species Families</h4>
                    <div class="value">{sum(1 for c in shared_clusters if c['crosses_species'])}</div>
                    <p>Across different organisms</p>
                </div>
                <div class="stat-card">
                    <h4>Most Widespread</h4>
                    <div class="value">{max((c['n_samples'] for c in shared_clusters), default=0)}</div>
                    <p>Samples in largest family</p>
                </div>
            </div>

            <h2>🔍 Top 50 Most Widespread Prophage Families</h2>
            <table>
                <thead>
                    <tr>
                        <th>Family ID</th>
                        <th>Prophages</th>
                        <th>Samples</th>
                        <th>Years</th>
                        <th>Organisms</th>
                        <th>Movement</th>
                    </tr>
                </thead>
                <tbody>
"""

    for cluster in shared_clusters[:50]:
        years_str = ', '.join(str(y) for y in cluster['years'])
        organisms_str = ', '.join(cluster['organisms'])[:50]

        badges = []
        if cluster['crosses_years']:
            badges.append('<span class="badge badge-year">Cross-Year</span>')
        if cluster['crosses_species']:
            badges.append('<span class="badge badge-species">Cross-Species</span>')
        badges_html = ' '.join(badges) if badges else '-'

        html += f"""
                    <tr>
                        <td><strong>Family_{cluster['cluster_id']}</strong></td>
                        <td>{cluster['n_prophages']}</td>
                        <td><strong>{cluster['n_samples']}</strong></td>
                        <td>{years_str}</td>
                        <td>{organisms_str}</td>
                        <td>{badges_html}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"  ✅ Saved: {output_file}")


def save_cluster_table(cluster_dict, cluster_members, shared_clusters, output_file):
    """Save cluster membership to CSV"""
    print(f"\nSaving cluster table: {output_file}")

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Prophage_ID', 'Sample_ID', 'Cluster_ID', 'Cluster_Size', 'Is_Shared'])

        for prophage_id, cluster_id in cluster_dict.items():
            sample = extract_sample_from_prophage_id(prophage_id)
            cluster_size = len(cluster_members[cluster_id])
            is_shared = any(c['cluster_id'] == cluster_id for c in shared_clusters)

            writer.writerow([prophage_id, sample, cluster_id, cluster_size, is_shared])

    print(f"  ✅ Saved: {output_file}")


def main():
    # Paths
    base_dir = os.path.expanduser('~/compass_kansas_results')
    phylogeny_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/phylogeny')
    input_fasta = os.path.join(phylogeny_dir, 'complete_prophages.fasta')
    output_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/prophage_families')

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Prophage Family Clustering Analysis")
    print("=" * 70)

    # Check if CD-HIT is installed
    if not check_cdhit_installed():
        print("\n❌ ERROR: CD-HIT not found!")
        print("\nPlease install CD-HIT:")
        print("  module load CD-HIT")
        print("  # or")
        print("  conda install -c bioconda cd-hit")
        print("  # or")
        print("  # Download from: https://github.com/weizhongli/cdhit/releases")
        return

    print("✅ CD-HIT found")

    # Check if input exists
    if not Path(input_fasta).exists():
        print(f"\n❌ ERROR: {input_fasta} not found!")
        print("Please run prepare_prophage_phylogeny.py first")
        return

    # Load metadata
    metadata = load_metadata(base_dir)

    # Cluster at different identity thresholds
    identity_thresholds = [0.99, 0.95, 0.90]

    for identity in identity_thresholds:
        print(f"\n{'='*70}")
        print(f"Clustering at {int(identity*100)}% identity")
        print(f"{'='*70}")

        output_prefix = os.path.join(output_dir, 'prophage_clusters')

        # Run CD-HIT
        clustered_fasta, clstr_file = cluster_prophages_cdhit(
            input_fasta,
            output_prefix,
            identity=identity,
            threads=8
        )

        if not clstr_file:
            print(f"⚠️  Skipping {int(identity*100)}% analysis due to clustering failure")
            continue

        # Parse clusters
        cluster_dict, cluster_members, representatives = parse_cdhit_clusters(clstr_file)

        # Analyze sharing
        shared_clusters = analyze_cluster_sharing(cluster_members, metadata)

        # Generate reports
        report_html = os.path.join(output_dir, f'PROPHAGE_FAMILIES_{int(identity*100)}.html')
        generate_cluster_report(shared_clusters, identity, report_html)

        # Save tables
        table_csv = os.path.join(output_dir, f'prophage_clusters_{int(identity*100)}.csv')
        save_cluster_table(cluster_dict, cluster_members, shared_clusters, table_csv)

        print(f"\n✅ Analysis at {int(identity*100)}% complete!")
        print(f"   - {len(cluster_members)} total families")
        print(f"   - {len(shared_clusters)} families shared across samples")

    print("\n" + "=" * 70)
    print("✅ Prophage family clustering complete!")
    print("=" * 70)
    print(f"\nOutput directory: {output_dir}")
    print(f"\nKey files:")
    print(f"  - PROPHAGE_FAMILIES_99.html (nearly identical prophages)")
    print(f"  - PROPHAGE_FAMILIES_95.html (same prophage type)")
    print(f"  - PROPHAGE_FAMILIES_90.html (prophage family)")
    print("=" * 70)


if __name__ == '__main__':
    main()
