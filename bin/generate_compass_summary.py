#!/usr/bin/env python3
"""
COMPASS Pipeline Comprehensive Summary Report Generator (Enhanced Version)
Aggregates results from all pipeline modules into comprehensive summary with visualizations
"""

import argparse
import pandas as pd
import json
from pathlib import Path
import sys
from collections import Counter, defaultdict
import re
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='Generate comprehensive COMPASS summary report with visualizations')
    parser.add_argument('--outdir', required=True, help='Pipeline output directory')
    parser.add_argument('--metadata', help='Optional metadata CSV with organism/source info')
    parser.add_argument('--output_tsv', default='compass_summary.tsv', help='Output TSV summary file')
    parser.add_argument('--output_html', default='compass_summary.html', help='Output HTML report')
    return parser.parse_args()

def parse_metadata(metadata_file):
    """Parse metadata CSV if provided"""
    metadata = {}
    if metadata_file and Path(metadata_file).exists():
        try:
            df = pd.read_csv(metadata_file)
            for _, row in df.iterrows():
                sample_id = row.get('Run', row.get('sample_id', row.get('sample', '')))
                metadata[sample_id] = {
                    'organism': row.get('Organism', row.get('organism', '-')),
                    'state': row.get('geo_loc_name_state_province', row.get('state', '-')),
                    'year': row.get('Collection_Date', row.get('year', '-')),
                    'source': row.get('Isolation_source', row.get('source', '-'))
                }
        except Exception as e:
            print(f"Warning: Could not parse metadata file: {e}", file=sys.stderr)
    return metadata

def parse_quast(quast_dir):
    """Parse QUAST assembly statistics"""
    quast_data = {}
    quast_path = Path(quast_dir)
    if quast_path.exists():
        for report_file in quast_path.glob('*/report.tsv'):
            try:
                df = pd.read_csv(report_file, sep='\t', index_col=0)
                sample_id = df.columns[0]

                # Extract key metrics
                total_length = df.loc['Total length', sample_id] if 'Total length' in df.index else 0
                n50 = df.loc['N50', sample_id] if 'N50' in df.index else 0
                num_contigs = df.loc['# contigs', sample_id] if '# contigs' in df.index else 0

                # Determine assembly quality status based on thresholds
                quality_pass = True
                quality_issues = []

                if isinstance(num_contigs, (int, float)) and num_contigs > 500:
                    quality_pass = False
                    quality_issues.append(f"high_contigs({num_contigs})")

                if isinstance(total_length, (int, float)) and total_length < 1000000:
                    quality_pass = False
                    quality_issues.append(f"small_assembly({total_length})")

                if isinstance(n50, (int, float)) and n50 < 10000:
                    quality_pass = False
                    quality_issues.append(f"low_N50({n50})")

                quast_data[sample_id] = {
                    'num_contigs': num_contigs,
                    'assembly_length': total_length,
                    'n50': n50,
                    'gc_percent': df.loc['GC (%)', sample_id] if 'GC (%)' in df.index else '-',
                    'assembly_quality': 'Pass' if quality_pass else f"Fail: {', '.join(quality_issues)}"
                }
            except Exception as e:
                print(f"Warning: Could not parse QUAST results for {report_file}: {e}", file=sys.stderr)
    return quast_data

def parse_busco(busco_dir):
    """Parse BUSCO completeness and contamination metrics"""
    busco_data = {}
    busco_path = Path(busco_dir)
    if busco_path.exists():
        for summary_file in busco_path.glob('*/short_summary.*.txt'):
            sample_id = summary_file.parent.name.replace('_busco', '')
            try:
                with open(summary_file) as f:
                    content = f.read()

                    # Parse BUSCO percentages from summary line
                    # Format: C:98.5%[S:97.0%,D:1.5%],F:0.5%,M:1.0%,n:124
                    match = re.search(r'C:([0-9.]+)%\[S:([0-9.]+)%,D:([0-9.]+)%\],F:([0-9.]+)%,M:([0-9.]+)%', content)

                    if match:
                        complete_pct = float(match.group(1))
                        single_pct = float(match.group(2))
                        duplicated_pct = float(match.group(3))
                        fragmented_pct = float(match.group(4))
                        missing_pct = float(match.group(5))

                        busco_data[sample_id] = {
                            'busco_complete_pct': complete_pct,
                            'busco_duplicated_pct': duplicated_pct,
                            'busco_fragmented_pct': fragmented_pct,
                            'busco_missing_pct': missing_pct,
                            'busco_summary': f"C:{complete_pct}%[S:{single_pct}%,D:{duplicated_pct}%],F:{fragmented_pct}%,M:{missing_pct}%"
                        }
            except Exception as e:
                print(f"Warning: Could not parse BUSCO results for {summary_file}: {e}", file=sys.stderr)
    return busco_data

def parse_mlst(mlst_dir):
    """Parse MLST sequence typing results"""
    mlst_data = {}
    mlst_path = Path(mlst_dir)
    if mlst_path.exists():
        for mlst_file in mlst_path.glob('*_mlst.tsv'):
            sample_id = mlst_file.stem.replace('_mlst', '')
            try:
                df = pd.read_csv(mlst_file, sep='\t')
                if not df.empty:
                    # MLST format: FILE SCHEME ST gene1 gene2 ...
                    mlst_data[sample_id] = {
                        'mlst_scheme': str(df.iloc[0]['SCHEME']) if 'SCHEME' in df.columns else '-',
                        'mlst_st': str(df.iloc[0]['ST']) if 'ST' in df.columns else '-'
                    }
            except Exception as e:
                print(f"Warning: Could not parse MLST results for {mlst_file}: {e}", file=sys.stderr)
    return mlst_data

def parse_sistr(sistr_dir):
    """Parse SISTR Salmonella serovar predictions"""
    sistr_data = {}
    sistr_path = Path(sistr_dir)
    if sistr_path.exists():
        for sistr_file in sistr_path.glob('*_sistr.tsv'):
            sample_id = sistr_file.stem.replace('_sistr', '')
            try:
                df = pd.read_csv(sistr_file, sep='\t')
                if not df.empty:
                    sistr_data[sample_id] = {
                        'serovar': df.iloc[0].get('serovar', '-'),
                        'serogroup': df.iloc[0].get('serogroup', '-'),
                        'h1': df.iloc[0].get('h1', '-'),
                        'h2': df.iloc[0].get('h2', '-')
                    }
            except Exception as e:
                print(f"Warning: Could not parse SISTR results for {sistr_file}: {e}", file=sys.stderr)
    return sistr_data

def parse_amrfinder(amr_dir):
    """Parse AMRFinder+ AMR gene and point mutation results"""
    amr_data = {}
    amr_path = Path(amr_dir)
    if amr_path.exists():
        for amr_file in amr_path.glob('*_amr.tsv'):
            sample_id = amr_file.stem.replace('_amr', '')
            try:
                df = pd.read_csv(amr_file, sep='\t')

                if df.empty:
                    amr_data[sample_id] = {
                        'num_amr_genes': 0,
                        'num_point_mutations': 0,
                        'amr_classes': '-',
                        'mdr_status': 'No',
                        'top_amr_genes': '-'
                    }
                else:
                    # Count genes vs point mutations
                    genes = df[df['Element type'] == 'AMR'] if 'Element type' in df.columns else df
                    mutations = df[df['Element type'] == 'POINT'] if 'Element type' in df.columns else pd.DataFrame()

                    # Get AMR classes
                    classes = []
                    if 'Class' in df.columns:
                        classes = [c for c in df['Class'].dropna().unique() if str(c) != 'nan']

                    # Determine MDR status (≥3 classes)
                    mdr_status = 'Yes' if len(classes) >= 3 else 'No'

                    # Get top genes
                    top_genes = []
                    if 'Gene symbol' in df.columns:
                        gene_counts = Counter(df['Gene symbol'].dropna())
                        top_genes = [gene for gene, count in gene_counts.most_common(5)]

                    amr_data[sample_id] = {
                        'num_amr_genes': len(genes),
                        'num_point_mutations': len(mutations),
                        'amr_classes': ', '.join(sorted(classes)) if classes else '-',
                        'mdr_status': mdr_status,
                        'top_amr_genes': ', '.join(top_genes) if top_genes else '-'
                    }
            except Exception as e:
                print(f"Warning: Could not parse AMRFinder results for {amr_file}: {e}", file=sys.stderr)
    return amr_data

def parse_mobsuite(mobsuite_dir):
    """Parse MOB-suite plasmid detection and typing results"""
    mobsuite_data = {}
    mobsuite_path = Path(mobsuite_dir)
    if mobsuite_path.exists():
        for result_file in mobsuite_path.glob('*/mobtyper_results.txt'):
            sample_id = result_file.parent.name.replace('_mobsuite', '')
            try:
                df = pd.read_csv(result_file, sep='\t')

                if df.empty:
                    mobsuite_data[sample_id] = {
                        'num_plasmids': 0,
                        'inc_groups': '-',
                        'mob_types': '-'
                    }
                else:
                    # Count plasmids
                    num_plasmids = len(df)

                    # Get incompatibility groups
                    inc_groups = []
                    if 'rep_type(s)' in df.columns:
                        for reps in df['rep_type(s)'].dropna():
                            if str(reps) != 'nan' and str(reps) != '-':
                                inc_groups.extend(str(reps).split(','))

                    # Get MOB types
                    mob_types = []
                    if 'predicted_mobility' in df.columns:
                        mob_types = df['predicted_mobility'].dropna().unique().tolist()

                    mobsuite_data[sample_id] = {
                        'num_plasmids': num_plasmids,
                        'inc_groups': ', '.join(sorted(set(inc_groups))) if inc_groups else '-',
                        'mob_types': ', '.join(sorted(set(str(m) for m in mob_types))) if mob_types else '-'
                    }
            except Exception as e:
                print(f"Warning: Could not parse MOBsuite results for {result_file}: {e}", file=sys.stderr)
    return mobsuite_data

def parse_vibrant(vibrant_dir):
    """Parse VIBRANT prophage detection results"""
    vibrant_data = {}
    vibrant_path = Path(vibrant_dir)
    if vibrant_path.exists():
        # VIBRANT creates nested structure: sample_vibrant/VIBRANT_sample_contigs/VIBRANT_results_sample_contigs/VIBRANT_genome_quality_sample_contigs.tsv
        for results_file in vibrant_path.glob('*/VIBRANT_*/VIBRANT_results_*/VIBRANT_genome_quality_*.tsv'):
            # Extract sample_id from directory name (e.g., SRR001_vibrant -> SRR001)
            sample_id = results_file.parents[2].name.replace('_vibrant', '')
            try:
                df = pd.read_csv(results_file, sep='\t')

                if df.empty:
                    vibrant_data[sample_id] = {
                        'num_prophages': 0,
                        'num_lytic': 0,
                        'num_lysogenic': 0
                    }
                else:
                    # Count prophages
                    num_prophages = len(df)

                    # Count lytic vs lysogenic
                    num_lytic = 0
                    num_lysogenic = 0
                    if 'type' in df.columns:
                        num_lytic = len(df[df['type'] == 'lytic'])
                        num_lysogenic = len(df[df['type'] == 'lysogenic'])

                    vibrant_data[sample_id] = {
                        'num_prophages': num_prophages,
                        'num_lytic': num_lytic,
                        'num_lysogenic': num_lysogenic
                    }
            except Exception as e:
                print(f"Warning: Could not parse VIBRANT results for {results_file}: {e}", file=sys.stderr)
    return vibrant_data

def parse_vibrant_annotations(vibrant_dir):
    """Parse VIBRANT annotation files to extract prophage functional categories"""
    functional_data = Counter()
    hypothetical_count = 0
    vibrant_path = Path(vibrant_dir)

    if vibrant_path.exists():
        # Look for annotation files - VIBRANT creates nested structure
        for annot_file in vibrant_path.glob('*_vibrant/VIBRANT_*/VIBRANT_annotations_*.tsv'):
            try:
                df = pd.read_csv(annot_file, sep='\t')

                # VIBRANT uses multi-column format: columns 4 (KO), 9 (Pfam), 14 (VOG)
                # Based on working v1.2-stable code
                for idx, row in df.iterrows():
                    # Extract annotation from multiple columns
                    ko_name = str(row.iloc[4]) if len(row) > 4 else ""
                    pfam_name = str(row.iloc[9]) if len(row) > 9 else ""
                    vog_name = str(row.iloc[14]) if len(row) > 14 else ""

                    combined = f"{ko_name} {pfam_name} {vog_name}".lower()

                    # Skip hypothetical/unknown proteins
                    if any(kw in combined for kw in ['hypothetical', 'duf', 'unknown function', 'uncharacterized', 'nan']):
                        hypothetical_count += 1
                        continue

                    # Categorize using combined annotation (from v1.2-stable logic)
                    categorized = False

                    # DNA Packaging
                    if any(term in combined for term in ['terminase', 'portal', 'packaging protein', 'dna-packaging']):
                        functional_data['DNA Packaging'] += 1
                        categorized = True
                    # Structural
                    elif any(term in combined for term in ['capsid', 'head', 'coat protein', 'tail', 'baseplate', 'fiber']):
                        functional_data['Structural'] += 1
                        categorized = True
                    # Lysis
                    elif any(term in combined for term in ['lyso', 'lysis', 'holin', 'spanin', 'endopeptidase', 'lysin', 'endolysin']):
                        functional_data['Lysis'] += 1
                        categorized = True
                    # DNA Modification
                    elif any(term in combined for term in ['integrase', 'recombinase', 'transposase', 'excisionase', 'replication', 'primase', 'helicase', 'polymerase', 'ligase', 'endonuclease', 'exonuclease', 'nuclease', 'methylase', 'methyltransferase']):
                        functional_data['DNA Modification'] += 1
                        categorized = True
                    # Regulation
                    elif any(term in combined for term in ['repressor', 'regulator', 'antitermination', 'antirepressor', 'anti-repressor']):
                        functional_data['Regulation'] += 1
                        categorized = True

                    # If not categorized and not hypothetical, mark as "Other"
                    if not categorized:
                        functional_data['Other'] += 1

            except Exception as e:
                print(f"Warning: Could not parse VIBRANT annotations for {annot_file}: {e}", file=sys.stderr)

    return dict(functional_data)

def parse_diamond_prophage(diamond_dir):
    """Parse DIAMOND prophage database matches"""
    diamond_data = {}
    diamond_path = Path(diamond_dir)
    if diamond_path.exists():
        for diamond_file in diamond_path.glob('*_diamond_results.tsv'):
            sample_id = diamond_file.stem.replace('_diamond_results', '')
            try:
                # DIAMOND format: qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
                df = pd.read_csv(diamond_file, sep='\t', header=None,
                                names=['qseqid', 'sseqid', 'pident', 'length', 'mismatch',
                                       'gapopen', 'qstart', 'qend', 'sstart', 'send', 'evalue', 'bitscore'])

                if df.empty:
                    diamond_data[sample_id] = {
                        'num_prophage_hits': 0,
                        'top_prophage_matches': '-'
                    }
                else:
                    # Count unique prophage hits
                    num_hits = df['qseqid'].nunique()

                    # Get top 3 matches by identity
                    top_matches = []
                    if not df.empty:
                        df_sorted = df.sort_values('pident', ascending=False).head(3)
                        for _, row in df_sorted.iterrows():
                            match_str = f"{row['sseqid']}({row['pident']:.1f}%)"
                            top_matches.append(match_str)

                    diamond_data[sample_id] = {
                        'num_prophage_hits': num_hits,
                        'top_prophage_matches': ', '.join(top_matches) if top_matches else '-'
                    }
            except Exception as e:
                print(f"Warning: Could not parse DIAMOND results for {diamond_file}: {e}", file=sys.stderr)
    return diamond_data

def generate_html_report(df, output_file, functional_diversity=None, multiqc_path=None, generation_time=None):
    """Generate interactive multi-tab HTML report with visualizations"""

    # Get generation time
    if generation_time is None:
        generation_time = datetime.now()

    # Calculate summary statistics
    total_samples = len(df)
    passed_qc = len(df[df['assembly_quality'] == 'Pass'])
    failed_qc = total_samples - passed_qc

    # Convert numeric columns, replacing '-' with 0 and handling NaN
    avg_contigs = df['num_contigs'].replace('-', 0).astype(float).mean()
    avg_n50 = df['n50'].replace('-', 0).astype(float).mean()

    mdr_samples = len(df[df['mdr_status'] == 'Yes'])
    mdr_pct = (mdr_samples / total_samples * 100) if total_samples > 0 else 0

    # Ensure prophage counts are numeric before summing
    total_prophages = int(df['num_prophages'].replace('-', 0).fillna(0).astype(float).sum())
    avg_prophages = total_prophages / total_samples if total_samples > 0 else 0

    # AMR statistics - ensure numeric values
    total_amr_genes = int(df['num_amr_genes'].replace('-', 0).fillna(0).astype(float).sum())
    samples_with_amr = len(df[df['num_amr_genes'].replace('-', 0).fillna(0).astype(float) > 0])

    # Plasmid statistics - ensure numeric values
    total_plasmids = int(df['num_plasmids'].replace('-', 0).fillna(0).astype(float).sum())
    samples_with_plasmids = len(df[df['num_plasmids'].replace('-', 0).fillna(0).astype(float) > 0])

    # Prepare functional diversity data for chart
    functional_labels = []
    functional_values = []
    if functional_diversity:
        for category, count in functional_diversity.items():
            functional_labels.append(category)
            functional_values.append(count)

    # Prepare AMR data for visualizations
    # Parse top_amr_genes column to get gene frequency
    amr_gene_counter = Counter()
    amr_class_counter = Counter()

    for _, row in df.iterrows():
        # Parse top AMR genes
        genes_str = row.get('top_amr_genes', '-')
        if genes_str and genes_str != '-':
            genes = [g.strip() for g in str(genes_str).split(',')]
            for gene in genes:
                if gene:  # Skip empty strings
                    amr_gene_counter[gene] += 1

        # Parse AMR classes
        classes_str = row.get('amr_classes', '-')
        if classes_str and classes_str != '-':
            classes = [c.strip() for c in str(classes_str).split(',')]
            for cls in classes:
                if cls:  # Skip empty strings
                    amr_class_counter[cls] += 1

    # Get top 15 AMR genes for bar chart
    top_amr_genes = amr_gene_counter.most_common(15)
    amr_gene_labels = [gene for gene, count in top_amr_genes]
    amr_gene_counts = [count for gene, count in top_amr_genes]

    # Get AMR class distribution for pie chart
    amr_class_labels = [cls for cls, count in amr_class_counter.most_common()]
    amr_class_counts = [count for cls, count in amr_class_counter.most_common()]

    # Prepare Plasmid Analysis data for visualizations
    inc_group_counter = Counter()
    mobility_type_counter = Counter()
    plasmid_count_values = []
    plasmid_amr_pairs = []  # For scatter plot: (num_plasmids, num_amr_genes)

    for _, row in df.iterrows():
        # Parse Inc groups
        inc_str = row.get('inc_groups', '-')
        if inc_str and inc_str != '-':
            inc_list = [i.strip() for i in str(inc_str).split(',')]
            for inc in inc_list:
                if inc:
                    inc_group_counter[inc] += 1

        # Parse mobility types
        mob_str = row.get('mob_types', '-')
        if mob_str and mob_str != '-':
            mob_list = [m.strip() for m in str(mob_str).split(',')]
            for mob in mob_list:
                if mob:
                    mobility_type_counter[mob] += 1

        # Plasmid counts
        num_plas = row.get('num_plasmids', 0)
        if num_plas != '-' and str(num_plas) != 'nan':
            try:
                plasmid_count_values.append(int(num_plas))
            except (ValueError, TypeError):
                plasmid_count_values.append(0)

        # Plasmid-AMR correlation data
        num_amr = row.get('num_amr_genes', 0)
        if num_plas != '-' and num_amr != '-':
            try:
                plas_int = int(num_plas) if num_plas != '-' else 0
                amr_int = int(num_amr) if num_amr != '-' else 0
                plasmid_amr_pairs.append((plas_int, amr_int))
            except (ValueError, TypeError):
                pass

    # Get top 15 Inc groups for bar chart
    top_inc_groups = inc_group_counter.most_common(15)
    inc_group_labels = [inc for inc, count in top_inc_groups]
    inc_group_counts = [count for inc, count in top_inc_groups]

    # Get mobility type distribution
    mob_type_labels = [mob for mob, count in mobility_type_counter.most_common()]
    mob_type_counts = [count for mob, count in mobility_type_counter.most_common()]

    # Create plasmid count histogram (0-10 plasmids)
    plasmid_bins = list(range(0, 11))
    if plasmid_count_values:
        plasmid_hist, _ = pd.cut(plasmid_count_values, bins=plasmid_bins, retbins=True)
        plasmid_hist_counts = plasmid_hist.value_counts().sort_index().tolist()
    else:
        plasmid_hist_counts = []
    plasmid_hist_labels = [f"{i}-{i+1}" for i in range(0, 10)]

    # Prepare scatter plot data (plasmid count vs AMR gene count)
    scatter_plasmid_x = [pair[0] for pair in plasmid_amr_pairs]
    scatter_amr_y = [pair[1] for pair in plasmid_amr_pairs]

    # Prepare Temporal Analysis data for visualizations
    # Group data by year
    temporal_data = defaultdict(lambda: {
        'total_samples': 0,
        'amr_positive': 0,
        'mdr_samples': 0,
        'prophages': 0,
        'plasmids': 0
    })

    for _, row in df.iterrows():
        year = row.get('year', '-')
        # Try to parse year as integer
        if year and year != '-' and year != 'Unknown':
            try:
                year_int = int(float(year))
                temporal_data[year_int]['total_samples'] += 1

                # Count AMR positive samples
                num_amr = row.get('num_amr_genes', 0)
                if num_amr and num_amr != '-':
                    try:
                        if int(num_amr) > 0:
                            temporal_data[year_int]['amr_positive'] += 1
                    except (ValueError, TypeError):
                        pass

                # Count MDR samples
                if row.get('mdr_status') == 'Yes':
                    temporal_data[year_int]['mdr_samples'] += 1

                # Sum prophages
                num_prophages = row.get('num_prophages', 0)
                if num_prophages and num_prophages != '-':
                    try:
                        temporal_data[year_int]['prophages'] += int(num_prophages)
                    except (ValueError, TypeError):
                        pass

                # Sum plasmids
                num_plasmids = row.get('num_plasmids', 0)
                if num_plasmids and num_plasmids != '-':
                    try:
                        temporal_data[year_int]['plasmids'] += int(num_plasmids)
                    except (ValueError, TypeError):
                        pass
            except (ValueError, TypeError):
                pass

    # Sort years and prepare chart data
    sorted_years = sorted(temporal_data.keys())
    temporal_years = [str(year) for year in sorted_years]
    temporal_sample_counts = [temporal_data[year]['total_samples'] for year in sorted_years]
    temporal_amr_counts = [temporal_data[year]['amr_positive'] for year in sorted_years]
    temporal_mdr_counts = [temporal_data[year]['mdr_samples'] for year in sorted_years]
    temporal_prophage_counts = [temporal_data[year]['prophages'] for year in sorted_years]
    temporal_plasmid_counts = [temporal_data[year]['plasmids'] for year in sorted_years]

    # Calculate percentages for AMR/MDR trends
    temporal_amr_pct = []
    temporal_mdr_pct = []
    for year in sorted_years:
        total = temporal_data[year]['total_samples']
        if total > 0:
            temporal_amr_pct.append(round(temporal_data[year]['amr_positive'] / total * 100, 1))
            temporal_mdr_pct.append(round(temporal_data[year]['mdr_samples'] / total * 100, 1))
        else:
            temporal_amr_pct.append(0)
            temporal_mdr_pct.append(0)

    # Prepare Assembly Quality data for visualizations
    # Extract numeric values for histograms
    n50_values = []
    assembly_length_values = []
    contig_count_values = []
    busco_completeness_values = []

    for _, row in df.iterrows():
        # N50 values
        n50 = row.get('n50', '-')
        if n50 != '-' and str(n50) != 'nan':
            try:
                n50_values.append(float(n50))
            except (ValueError, TypeError):
                pass

        # Assembly length values
        length = row.get('assembly_length', '-')
        if length != '-' and str(length) != 'nan':
            try:
                assembly_length_values.append(float(length))
            except (ValueError, TypeError):
                pass

        # Contig counts
        contigs = row.get('num_contigs', '-')
        if contigs != '-' and str(contigs) != 'nan':
            try:
                contig_count_values.append(float(contigs))
            except (ValueError, TypeError):
                pass

        # BUSCO completeness
        busco = row.get('busco_complete_pct', '-')
        if busco != '-' and str(busco) != 'nan':
            try:
                busco_completeness_values.append(float(busco))
            except (ValueError, TypeError):
                pass

    # Create bins for histograms
    # N50 histogram bins (0-200kb in 10kb increments)
    n50_bins = list(range(0, 210000, 10000))
    n50_hist, _ = pd.cut(n50_values, bins=n50_bins, retbins=True) if n50_values else ([], n50_bins)
    n50_counts = n50_hist.value_counts().sort_index().tolist() if len(n50_values) > 0 else []
    n50_labels = [f"{i//1000}-{(i+10000)//1000}kb" for i in range(0, 200000, 10000)]

    # Assembly length bins (0-8Mb in 0.5Mb increments)
    length_bins = list(range(0, 8500000, 500000))
    length_hist, _ = pd.cut(assembly_length_values, bins=length_bins, retbins=True) if assembly_length_values else ([], length_bins)
    length_counts = length_hist.value_counts().sort_index().tolist() if len(assembly_length_values) > 0 else []
    length_labels = [f"{i//1000000:.1f}-{(i+500000)//1000000:.1f}Mb" for i in range(0, 8000000, 500000)]

    # Contig count bins (0-500 in bins of 50)
    contig_bins = list(range(0, 550, 50))
    contig_hist, _ = pd.cut(contig_count_values, bins=contig_bins, retbins=True) if contig_count_values else ([], contig_bins)
    contig_counts = contig_hist.value_counts().sort_index().tolist() if len(contig_count_values) > 0 else []
    contig_labels = [f"{i}-{i+50}" for i in range(0, 500, 50)]

    # BUSCO completeness bins (0-100% in 5% increments)
    busco_bins = list(range(0, 105, 5))
    busco_hist, _ = pd.cut(busco_completeness_values, bins=busco_bins, retbins=True) if busco_completeness_values else ([], busco_bins)
    busco_counts = busco_hist.value_counts().sort_index().tolist() if len(busco_completeness_values) > 0 else []
    busco_labels = [f"{i}-{i+5}%" for i in range(0, 100, 5)]

    # Geographic Analysis data preparation
    state_counter = Counter()
    state_mdr_counts = {}  # state -> MDR count
    state_total_counts = {}  # state -> total samples
    state_amr_totals = {}  # state -> total AMR genes

    for _, row in df.iterrows():
        state = row.get('state', '-')
        if state and state != '-':
            # Count samples per state
            state_counter[state] += 1

            # Track MDR by state
            if state not in state_mdr_counts:
                state_mdr_counts[state] = 0
                state_total_counts[state] = 0
                state_amr_totals[state] = 0

            state_total_counts[state] += 1

            # Count MDR samples
            if row.get('mdr_status') == 'Yes':
                state_mdr_counts[state] += 1

            # Sum AMR genes
            num_amr = row.get('num_amr_genes', 0)
            if num_amr != '-':
                try:
                    state_amr_totals[state] += int(num_amr)
                except (ValueError, TypeError):
                    pass

    # Calculate MDR rates by state
    state_mdr_rates = {}
    for state in state_counter.keys():
        if state_total_counts.get(state, 0) > 0:
            state_mdr_rates[state] = (state_mdr_counts.get(state, 0) / state_total_counts[state]) * 100
        else:
            state_mdr_rates[state] = 0

    # Get top 15 states by sample count
    top_states = state_counter.most_common(15)
    state_labels = [state for state, count in top_states]
    state_counts = [count for state, count in top_states]

    # MDR rates for top states
    state_mdr_rate_values = [state_mdr_rates.get(state, 0) for state in state_labels]

    # Total states with samples
    num_states = len(state_counter)

    # State with highest MDR rate
    max_mdr_state = max(state_mdr_rates.items(), key=lambda x: x[1]) if state_mdr_rates else ('-', 0)
    max_mdr_state_name = max_mdr_state[0]
    max_mdr_state_rate = max_mdr_state[1]

    # Strain Typing Analysis data preparation
    mlst_st_counter = Counter()
    serovar_counter = Counter()
    mlst_scheme_counter = Counter()

    for _, row in df.iterrows():
        # Count MLST sequence types
        mlst_st = row.get('mlst_st', '-')
        if mlst_st and mlst_st != '-':
            mlst_st_counter[mlst_st] += 1

        # Count MLST schemes
        mlst_scheme = row.get('mlst_scheme', '-')
        if mlst_scheme and mlst_scheme != '-':
            mlst_scheme_counter[mlst_scheme] += 1

        # Count serovars (Salmonella)
        serovar = row.get('serovar', '-')
        if serovar and serovar != '-':
            serovar_counter[serovar] += 1

    # Get top 15 MLST STs for bar chart
    top_mlst_sts = mlst_st_counter.most_common(15)
    mlst_st_labels = [str(st) for st, count in top_mlst_sts]
    mlst_st_counts = [count for st, count in top_mlst_sts]

    # Get top 15 serovars for bar chart
    top_serovars = serovar_counter.most_common(15)
    serovar_labels = [serovar for serovar, count in top_serovars]
    serovar_counts = [count for serovar, count in top_serovars]

    # MLST scheme distribution
    mlst_scheme_labels = [scheme for scheme, count in mlst_scheme_counter.most_common()]
    mlst_scheme_counts = [count for scheme, count in mlst_scheme_counter.most_common()]

    # Total unique types
    num_unique_sts = len(mlst_st_counter)
    num_unique_serovars = len(serovar_counter)
    num_mlst_schemes = len(mlst_scheme_counter)

    # Samples with typing data
    samples_with_mlst = len([s for s in df['mlst_st'] if s and s != '-'])
    samples_with_sistr = len([s for s in df['serovar'] if s and s != '-'])

    # Check if MultiQC report exists
    has_multiqc = multiqc_path and Path(multiqc_path).exists()

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COMPASS Pipeline Summary Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}

        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}

        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}

        .tabs {{
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .tab-buttons {{
            display: flex;
            overflow-x: auto;
            border-bottom: 2px solid #e0e0e0;
        }}

        .tab-button {{
            padding: 15px 25px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            color: #666;
            white-space: nowrap;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }}

        .tab-button:hover {{
            color: #667eea;
            background: #f8f9ff;
        }}

        .tab-button.active {{
            color: #667eea;
            border-bottom-color: #667eea;
            background: #f8f9ff;
        }}

        .tab-content {{
            display: none;
            padding: 30px;
            animation: fadeIn 0.3s ease-in;
        }}

        .tab-content.active {{
            display: block;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
            transition: transform 0.2s ease;
        }}

        .summary-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}

        .summary-card.card-success {{
            border-left-color: #22c55e;
        }}

        .summary-card.card-warning {{
            border-left-color: #f59e0b;
        }}

        .summary-card.card-danger {{
            border-left-color: #ef4444;
        }}

        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .summary-card.card-success h3 {{
            color: #22c55e;
        }}

        .summary-card.card-warning h3 {{
            color: #f59e0b;
        }}

        .summary-card.card-danger h3 {{
            color: #ef4444;
        }}

        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}

        .summary-card .subtext {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}

        .summary-card .indicator {{
            display: inline-block;
            margin-left: 8px;
            font-size: 0.5em;
        }}

        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}

        .chart-container h2 {{
            margin: 0 0 20px 0;
            color: #333;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
        }}

        .table-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}

        .search-box {{
            margin-bottom: 20px;
            padding: 12px;
            width: 100%;
            max-width: 400px;
            border: 2px solid #667eea;
            border-radius: 6px;
            font-size: 1em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th:hover {{
            background: #5568d3;
        }}

        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background-color: #f8f9ff;
        }}

        .status-pass {{
            color: #22c55e;
            font-weight: 600;
        }}

        .status-fail {{
            color: #ef4444;
            font-weight: 600;
        }}

        .mdr-yes {{
            background: #fee2e2;
            color: #991b1b;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}

        .footer {{
            background: white;
            padding: 30px;
            margin-top: 40px;
            border-top: 3px solid #667eea;
            box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
        }}

        .footer h3 {{
            color: #333;
            margin-bottom: 15px;
        }}

        .footer-content {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}

        .footer-section {{
            padding: 15px;
            background: #f8f9ff;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }}

        .footer-section h4 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .footer-section p {{
            margin: 5px 0;
            color: #666;
            font-size: 0.9em;
        }}

        .footer-section strong {{
            color: #333;
        }}

        .footer-links {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .footer-links a {{
            color: #667eea;
            text-decoration: none;
            margin: 0 10px;
        }}

        .footer-links a:hover {{
            text-decoration: underline;
        }}

        .export-toolbar {{
            background: #f8f9ff;
            padding: 12px 20px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }}

        .export-btn {{
            padding: 8px 16px;
            background: white;
            color: #667eea;
            border: 1px solid #667eea;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .export-btn:hover {{
            background: #667eea;
            color: white;
        }}

        .export-btn:active {{
            transform: scale(0.98);
        }}

        .export-label {{
            color: #666;
            font-size: 0.9em;
            font-weight: 600;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧬 COMPASS Pipeline Summary Report</h1>
        <p>Comprehensive Overview of AMR, Phage, and Assembly Quality Metrics</p>
    </div>

    <div class="tabs">
        <div class="tab-buttons">
            <button class="tab-button active" onclick="switchTab(event, 'overview')">Overview</button>
            <button class="tab-button" onclick="switchTab(event, 'amr-analysis')">AMR Analysis</button>
            <button class="tab-button" onclick="switchTab(event, 'plasmid-analysis')">Plasmid Analysis</button>
            <button class="tab-button" onclick="switchTab(event, 'temporal-analysis')">Temporal Analysis</button>
            <button class="tab-button" onclick="switchTab(event, 'geographic-analysis')">Geographic Analysis</button>
            <button class="tab-button" onclick="switchTab(event, 'strain-typing')">Strain Typing</button>
            <button class="tab-button" onclick="switchTab(event, 'assembly-quality')">Assembly Quality</button>
            <button class="tab-button" onclick="switchTab(event, 'data-table')">Data Table</button>
            <button class="tab-button" onclick="switchTab(event, 'prophage-functional')">Prophage Functional Diversity</button>"""

    if has_multiqc:
        html += """
            <button class="tab-button" onclick="switchTab(event, 'multiqc')">MultiQC Report</button>"""

    html += f"""
        </div>

        <!-- Export Toolbar -->
        <div class="export-toolbar">
            <span class="export-label">Export:</span>
            <button class="export-btn" onclick="downloadSummaryJSON()">
                📊 Summary JSON
            </button>
            <button class="export-btn" onclick="downloadAllChartsPNG()">
                📈 All Charts (PNG)
            </button>
            <button class="export-btn" onclick="generatePDFReport()">
                📄 PDF Report
            </button>
        </div>
    </div>

    <!-- Overview Tab -->
    <div id="overview" class="tab-content active">
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Samples</h3>
                <div class="value">__TOTAL_SAMPLES__</div>
            </div>
            <div class="summary-card {'card-success' if passed_qc/total_samples >= 0.9 else 'card-warning' if passed_qc/total_samples >= 0.7 else 'card-danger'}">
                <h3>Assembly QC <span class="indicator">{'✓' if passed_qc/total_samples >= 0.9 else '⚠' if passed_qc/total_samples >= 0.7 else '✗'}</span></h3>
                <div class="value">__PASSED_QC__</div>
                <div class="subtext">Passed (__FAILED_QC__ failed) - {passed_qc/total_samples*100:.1f}%</div>
            </div>
            <div class="summary-card {'card-success' if avg_contigs <= 100 and avg_n50 >= 50000 else 'card-warning' if avg_contigs <= 300 else 'card-danger'}">
                <h3>Average Assembly <span class="indicator">{'✓' if avg_contigs <= 100 and avg_n50 >= 50000 else '⚠' if avg_contigs <= 300 else '✗'}</span></h3>
                <div class="value">__AVG_CONTIGS_INT__</div>
                <div class="subtext">Contigs (N50: __AVG_N50_KB__kb)</div>
            </div>
            <div class="summary-card {'card-success' if mdr_pct < 10 else 'card-warning' if mdr_pct < 25 else 'card-danger'}">
                <h3>MDR Samples <span class="indicator">{'✓' if mdr_pct < 10 else '⚠' if mdr_pct < 25 else '!'}</span></h3>
                <div class="value">__MDR_SAMPLES__</div>
                <div class="subtext">__MDR_PCT_1F__% of samples</div>
            </div>
            <div class="summary-card">
                <h3>Total Prophages</h3>
                <div class="value">__TOTAL_PROPHAGES__</div>
                <div class="subtext">Avg: __AVG_PROPHAGES_1F__ per sample</div>
            </div>
            <div class="summary-card {'card-warning' if samples_with_amr/total_samples >= 0.5 else 'card-success'}">
                <h3>AMR Genes <span class="indicator">{'!' if samples_with_amr/total_samples >= 0.5 else 'ⓘ'}</span></h3>
                <div class="value">__TOTAL_AMR_GENES__</div>
                <div class="subtext">__SAMPLES_WITH_AMR__ samples with AMR (__AMR_PREVALENCE_1F__%)</div>
            </div>
            <div class="summary-card">
                <h3>Plasmids</h3>
                <div class="value">__TOTAL_PLASMIDS__</div>
                <div class="subtext">__SAMPLES_WITH_PLASMIDS__ samples with plasmids</div>
            </div>
        </div>
    </div>

    <!-- AMR Analysis Tab -->
    <div id="amr-analysis" class="tab-content">
        <div class="summary-grid" style="margin-bottom: 30px;">
            <div class="summary-card">
                <h3>Total AMR Genes</h3>
                <div class="value">__TOTAL_AMR_GENES__</div>
                <div class="subtext">Across __SAMPLES_WITH_AMR__ samples</div>
            </div>
            <div class="summary-card">
                <h3>MDR Samples</h3>
                <div class="value">__MDR_SAMPLES__</div>
                <div class="subtext">__MDR_PCT_1F__% of total</div>
            </div>
            <div class="summary-card">
                <h3>Unique AMR Genes</h3>
                <div class="value">__UNIQUE_AMR_GENES__</div>
                <div class="subtext">Detected across dataset</div>
            </div>
            <div class="summary-card">
                <h3>AMR Classes</h3>
                <div class="value">__UNIQUE_AMR_CLASSES__</div>
                <div class="subtext">Resistance classes found</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px;">
            <div class="chart-container">
                <h2>Top 15 AMR Genes</h2>
                <p style="color: #666; margin-bottom: 20px;">Most frequently detected AMR genes across all samples</p>
                <div class="chart-wrapper">
                    <canvas id="amrGenesBarChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>AMR Class Distribution</h2>
                <p style="color: #666; margin-bottom: 20px;">Distribution of antimicrobial resistance classes</p>
                <div class="chart-wrapper">
                    <canvas id="amrClassPieChart"></canvas>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h2>MDR vs Non-MDR Comparison</h2>
            <p style="color: #666; margin-bottom: 20px;">Samples with multidrug resistance (≥3 resistance classes) vs susceptible samples</p>
            <div class="chart-wrapper" style="height: 300px;">
                <canvas id="mdrComparisonChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Plasmid Analysis Tab -->
    <div id="plasmid-analysis" class="tab-content">
        <div class="summary-grid" style="margin-bottom: 30px;">
            <div class="summary-card">
                <h3>Total Plasmids</h3>
                <div class="value">__TOTAL_PLASMIDS__</div>
                <div class="subtext">Across __SAMPLES_WITH_PLASMIDS__ samples</div>
            </div>
            <div class="summary-card">
                <h3>Samples with Plasmids</h3>
                <div class="value">__SAMPLES_WITH_PLASMIDS__</div>
                <div class="subtext">__PLASMID_PREVALENCE_1F__% of total</div>
            </div>
            <div class="summary-card">
                <h3>Inc Groups Detected</h3>
                <div class="value">__UNIQUE_INC_GROUPS__</div>
                <div class="subtext">Incompatibility groups</div>
            </div>
            <div class="summary-card">
                <h3>Mobility Types</h3>
                <div class="value">__UNIQUE_MOBILITY_TYPES__</div>
                <div class="subtext">Different mobility classes</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px;">
            <div class="chart-container">
                <h2>Top 15 Incompatibility Groups</h2>
                <p style="color: #666; margin-bottom: 20px;">Most common plasmid Inc groups detected across samples</p>
                <div class="chart-wrapper">
                    <canvas id="incGroupsBarChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Plasmid Mobility Types</h2>
                <p style="color: #666; margin-bottom: 20px;">Distribution of predicted plasmid mobility mechanisms</p>
                <div class="chart-wrapper">
                    <canvas id="mobilityPieChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Plasmid Count Distribution</h2>
                <p style="color: #666; margin-bottom: 20px;">Number of plasmids detected per sample</p>
                <div class="chart-wrapper">
                    <canvas id="plasmidCountHistChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Plasmid-AMR Correlation</h2>
                <p style="color: #666; margin-bottom: 20px;">Relationship between plasmid count and AMR gene count</p>
                <div class="chart-wrapper">
                    <canvas id="plasmidAmrScatterChart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Temporal Analysis Tab -->
    <div id="temporal-analysis" class="tab-content">
        <div class="summary-grid" style="margin-bottom: 30px;">
            <div class="summary-card">
                <h3>Years Analyzed</h3>
                <div class="value">{len(sorted_years)}</div>
                <div class="subtext">{'From ' + str(min(sorted_years)) + ' to ' + str(max(sorted_years)) if sorted_years else 'No temporal data'}</div>
            </div>
            <div class="summary-card">
                <h3>Total Samples</h3>
                <div class="value">{sum(temporal_sample_counts) if temporal_sample_counts else 0}</div>
                <div class="subtext">Across all years</div>
            </div>
            <div class="summary-card {'card-danger' if temporal_mdr_pct and max(temporal_mdr_pct) > 25 else 'card-warning' if temporal_mdr_pct and max(temporal_mdr_pct) > 10 else 'card-success'}">
                <h3>Peak MDR Rate</h3>
                <div class="value">{max(temporal_mdr_pct) if temporal_mdr_pct else 0:.1f}%</div>
                <div class="subtext">{'In ' + str(sorted_years[temporal_mdr_pct.index(max(temporal_mdr_pct))]) if temporal_mdr_pct and max(temporal_mdr_pct) > 0 else 'No MDR detected'}</div>
            </div>
            <div class="summary-card">
                <h3>Trend Direction</h3>
                <div class="value">{'↑' if len(temporal_mdr_pct) >= 2 and temporal_mdr_pct[-1] > temporal_mdr_pct[0] else '↓' if len(temporal_mdr_pct) >= 2 and temporal_mdr_pct[-1] < temporal_mdr_pct[0] else '→'}</div>
                <div class="subtext">{'MDR increasing' if len(temporal_mdr_pct) >= 2 and temporal_mdr_pct[-1] > temporal_mdr_pct[0] else 'MDR decreasing' if len(temporal_mdr_pct) >= 2 and temporal_mdr_pct[-1] < temporal_mdr_pct[0] else 'MDR stable'}</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px;">
            <div class="chart-container">
                <h2>Sample Collection Over Time</h2>
                <p style="color: #666; margin-bottom: 20px;">Number of samples collected per year</p>
                <div class="chart-wrapper">
                    <canvas id="temporalSamplesChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>AMR/MDR Trends</h2>
                <p style="color: #666; margin-bottom: 20px;">Percentage of samples with AMR genes and MDR over time</p>
                <div class="chart-wrapper">
                    <canvas id="temporalAmrMdrChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Prophage Detection Over Time</h2>
                <p style="color: #666; margin-bottom: 20px;">Total prophages detected per year</p>
                <div class="chart-wrapper">
                    <canvas id="temporalProphagesChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Plasmid Detection Over Time</h2>
                <p style="color: #666; margin-bottom: 20px;">Total plasmids detected per year</p>
                <div class="chart-wrapper">
                    <canvas id="temporalPlasmidsChart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Geographic Analysis Tab -->
    <div id="geographic-analysis" class="tab-content">
        <div class="summary-grid" style="margin-bottom: 30px;">
            <div class="summary-card">
                <h3>States Analyzed</h3>
                <div class="value">{num_states}</div>
                <div class="subtext">Geographic regions with data</div>
            </div>
            <div class="summary-card {'card-success' if num_states > 10 else 'card-warning' if num_states > 5 else ''}">
                <h3>Top State</h3>
                <div class="value">{state_labels[0] if state_labels else '-'}</div>
                <div class="subtext">{state_counts[0] if state_counts else 0} samples</div>
            </div>
            <div class="summary-card {'card-danger' if max_mdr_state_rate > 30 else 'card-warning' if max_mdr_state_rate > 20 else 'card-success'}">
                <h3>Highest MDR Rate</h3>
                <div class="value">{max_mdr_state_rate:.1f}%</div>
                <div class="subtext">{max_mdr_state_name}</div>
            </div>
            <div class="summary-card">
                <h3>Coverage</h3>
                <div class="value">__TOTAL_SAMPLES__</div>
                <div class="subtext">Samples across {num_states} states</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; margin-bottom: 20px;">
            <div class="chart-container">
                <h2>Samples by State</h2>
                <p style="color: #666; margin-bottom: 20px;">Top 15 states by sample count</p>
                <div class="chart-wrapper">
                    <canvas id="stateSamplesChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>MDR Rates by State</h2>
                <p style="color: #666; margin-bottom: 20px;">Multidrug resistance prevalence across states</p>
                <div class="chart-wrapper">
                    <canvas id="stateMDRChart"></canvas>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h2>Regional Comparison</h2>
            <p style="color: #666; margin-bottom: 20px;">Sample counts vs MDR rates by state</p>
            <div class="chart-wrapper" style="height: 400px;">
                <canvas id="regionalComparisonChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Strain Typing Tab -->
    <div id="strain-typing" class="tab-content">
        <div class="summary-grid" style="margin-bottom: 30px;">
            <div class="summary-card">
                <h3>Samples with MLST</h3>
                <div class="value">{samples_with_mlst}</div>
                <div class="subtext">{samples_with_mlst/total_samples*100:.1f}% of total samples</div>
            </div>
            <div class="summary-card {'card-success' if num_unique_sts > 10 else 'card-warning' if num_unique_sts > 5 else ''}">
                <h3>Unique Sequence Types</h3>
                <div class="value">{num_unique_sts}</div>
                <div class="subtext">MLST STs detected</div>
            </div>
            <div class="summary-card">
                <h3>Samples with Serovars</h3>
                <div class="value">{samples_with_sistr}</div>
                <div class="subtext">{samples_with_sistr/total_samples*100:.1f}% (Salmonella only)</div>
            </div>
            <div class="summary-card {'card-success' if num_unique_serovars > 5 else ''}">
                <h3>Unique Serovars</h3>
                <div class="value">{num_unique_serovars}</div>
                <div class="subtext">SISTR serovar predictions</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; margin-bottom: 20px;">
            <div class="chart-container">
                <h2>Top MLST Sequence Types</h2>
                <p style="color: #666; margin-bottom: 20px;">Most common ST types across samples</p>
                <div class="chart-wrapper">
                    <canvas id="mlstSTChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>MLST Scheme Distribution</h2>
                <p style="color: #666; margin-bottom: 20px;">Typing schemes used for strain classification</p>
                <div class="chart-wrapper">
                    <canvas id="mlstSchemeChart"></canvas>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h2>Top Serovars (Salmonella)</h2>
            <p style="color: #666; margin-bottom: 20px;">Most common Salmonella serovars detected by SISTR</p>
            <div class="chart-wrapper" style="height: 400px;">
                <canvas id="serovarChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Assembly Quality Tab -->
    <div id="assembly-quality" class="tab-content">
        <div class="summary-grid" style="margin-bottom: 30px;">
            <div class="summary-card">
                <h3>Assemblies Analyzed</h3>
                <div class="value">{len(n50_values)}</div>
                <div class="subtext">With quality metrics</div>
            </div>
            <div class="summary-card">
                <h3>Average N50</h3>
                <div class="value">__AVG_N50_KB__kb</div>
                <div class="subtext">Assembly contiguity</div>
            </div>
            <div class="summary-card">
                <h3>Average Length</h3>
                <div class="value">{sum(assembly_length_values)/len(assembly_length_values)/1000000:.2f}Mb</div>
                <div class="subtext">Genome size</div>
            </div>
            <div class="summary-card">
                <h3>QC Pass Rate</h3>
                <div class="value">{passed_qc/total_samples*100:.1f}%</div>
                <div class="subtext">__PASSED_QC__/__TOTAL_SAMPLES__ samples</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px;">
            <div class="chart-container">
                <h2>N50 Distribution</h2>
                <p style="color: #666; margin-bottom: 20px;">Assembly contiguity across samples (higher is better)</p>
                <div class="chart-wrapper">
                    <canvas id="n50HistChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Assembly Length Distribution</h2>
                <p style="color: #666; margin-bottom: 20px;">Total assembly size distribution</p>
                <div class="chart-wrapper">
                    <canvas id="lengthHistChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Contig Count Distribution</h2>
                <p style="color: #666; margin-bottom: 20px;">Number of contigs per assembly (lower is better)</p>
                <div class="chart-wrapper">
                    <canvas id="contigHistChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>BUSCO Completeness</h2>
                <p style="color: #666; margin-bottom: 20px;">Genome completeness assessment (higher is better)</p>
                <div class="chart-wrapper">
                    <canvas id="buscoHistChart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Data Table Tab -->
    <div id="data-table" class="tab-content">
        <div class="table-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0;">Sample Details</h2>
                <button onclick="exportTableToCSV('compass_summary_export.csv')"
                        style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1em; transition: background 0.2s;">
                    📥 Export to CSV
                </button>
            </div>
            <input type="text" class="search-box" id="searchBox" placeholder="Search samples..." onkeyup="filterTable()">
            <div style="margin-bottom: 15px; color: #666; font-size: 0.9em;" id="tableStats">
                Showing <span id="visibleRows">0</span> of <span id="totalRows">0</span> samples
            </div>

            <!-- Pagination Controls -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding: 10px; background: #f8f9ff; border-radius: 6px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <label style="color: #666;">Rows per page:</label>
                    <select id="pageSizeSelect" onchange="changePageSize()" style="padding: 5px 10px; border: 1px solid #ddd; border-radius: 4px;">
                        <option value="50">50</option>
                        <option value="100" selected>100</option>
                        <option value="500">500</option>
                        <option value="999999">All</option>
                    </select>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span id="pageInfo" style="color: #666; font-size: 0.9em;">Page 1 of 1</span>
                    <button onclick="firstPage()" id="firstPage" style="padding: 5px 10px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;">⏮ First</button>
                    <button onclick="prevPage()" id="prevPage" style="padding: 5px 10px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;">◀ Prev</button>
                    <button onclick="nextPage()" id="nextPage" style="padding: 5px 10px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;">Next ▶</button>
                    <button onclick="lastPage()" id="lastPage" style="padding: 5px 10px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;">Last ⏭</button>
                </div>
            </div>

            <table id="dataTable">
                <thead>
                    <tr>
"""

    # Add table headers
    for col in df.columns:
        html += f"                        <th onclick=\"sortTable('{col}')\">{col}</th>\n"

    html += """                    </tr>
                </thead>
                <tbody>
"""

    # Add table rows
    for _, row in df.iterrows():
        html += "                    <tr>\n"
        for col in df.columns:
            value = row[col]

            # Apply special formatting
            if col == 'assembly_quality':
                css_class = 'status-pass' if value == 'Pass' else 'status-fail'
                html += f"                        <td class='{css_class}'>{value}</td>\n"
            elif col == 'mdr_status' and value == 'Yes':
                html += f"                        <td><span class='mdr-yes'>{value}</span></td>\n"
            else:
                html += f"                        <td>{value}</td>\n"

        html += "                    </tr>\n"

    html += """                </tbody>
            </table>
        </div>
    </div>

    <!-- Prophage Functional Diversity Tab -->
    <div id="prophage-functional" class="tab-content">
        <div class="chart-container">
            <h2>Prophage Functional Diversity</h2>
            <p style="color: #666; margin-bottom: 20px;">Distribution of prophage gene functions across all samples</p>
            <div class="chart-wrapper">
                <canvas id="functionalPieChart"></canvas>
            </div>
        </div>
    </div>"""

    if has_multiqc:
        html += """
    <!-- MultiQC Report Tab -->
    <div id="multiqc" class="tab-content">
        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="margin-bottom: 15px;">Quality Control Report</h2>
            <p style="color: #666; margin-bottom: 20px;">
                Comprehensive QC metrics from FastQC, fastp, QUAST, and BUSCO aggregated by MultiQC.
            </p>
            <iframe src="../multiqc/multiqc_report.html"
                    style="width: 100%; height: 1200px; border: none; border-radius: 4px;">
            </iframe>
        </div>
    </div>"""

    # Build JavaScript section as regular string, will format with .format() at end
    js_code = """

    <script>
        // Tab switching - simplified to avoid any escaping issues
        // Track which tabs have been rendered (for lazy loading)
        var renderedTabs = {
            'overview': true  // Overview is visible on load
        };

        function switchTab(evt, tabName) {
            // Hide all tab contents
            var tabContents = document.getElementsByClassName('tab-content');
            for (var i = 0; i < tabContents.length; i++) {
                tabContents[i].style.display = 'none';
                tabContents[i].classList.remove('active');
            }

            // Deactivate all buttons
            var tabButtons = document.getElementsByClassName('tab-button');
            for (var i = 0; i < tabButtons.length; i++) {
                tabButtons[i].classList.remove('active');
            }

            // Show the selected tab and activate button
            document.getElementById(tabName).style.display = 'block';
            document.getElementById(tabName).classList.add('active');
            evt.currentTarget.classList.add('active');

            // Lazy load charts for this tab if not already rendered
            if (!renderedTabs[tabName]) {
                renderTabCharts(tabName);
                renderedTabs[tabName] = true;
            }
        }

        // Table sorting
        function sortTable(column) {
            const table = document.getElementById('dataTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const headerRow = table.querySelector('thead tr');
            const headers = Array.from(headerRow.querySelectorAll('th'));
            const colIndex = headers.findIndex(h => h.textContent === column);

            const currentSort = table.dataset.sortColumn;
            const currentDir = table.dataset.sortDir || 'asc';
            const newDir = (currentSort === column && currentDir === 'asc') ? 'desc' : 'asc';

            rows.sort((a, b) => {
                const aVal = a.cells[colIndex].textContent.trim();
                const bVal = b.cells[colIndex].textContent.trim();

                const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newDir === 'asc' ? aNum - bNum : bNum - aNum;
                }

                return newDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            });

            rows.forEach(row => tbody.appendChild(row));

            table.dataset.sortColumn = column;
            table.dataset.sortDir = newDir;
        }

        // Table filtering with count
        function filterTable() {
            const input = document.getElementById('searchBox');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('dataTable');
            const rows = table.querySelectorAll('tbody tr');

            var visibleCount = 0;
            rows.forEach(row => {
                const text = row.textContent.toUpperCase();
                if (text.includes(filter)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Update count display
            document.getElementById('visibleRows').textContent = visibleCount;
            document.getElementById('totalRows').textContent = rows.length;
        }

        // Export table to CSV
        function exportTableToCSV(filename) {
            const table = document.getElementById('dataTable');
            const rows = table.querySelectorAll('tr');
            const csv = [];

            // Process all rows (including header)
            for (var i = 0; i < rows.length; i++) {
                const row = rows[i];
                const cols = row.querySelectorAll('td, th');
                const csvRow = [];

                for (var j = 0; j < cols.length; j++) {
                    // Get cell text and escape quotes
                    var cellText = cols[j].textContent.replace(/"/g, '""');
                    // Wrap in quotes if contains comma, quote, or newline
                    if (cellText.includes(',') || cellText.includes('"') || cellText.includes('\\n')) {
                        cellText = '"' + cellText + '"';
                    }
                    csvRow.push(cellText);
                }
                csv.push(csvRow.join(','));
            }

            // Create download link
            const csvContent = csv.join('\\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);

            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        // Export summary statistics as JSON
        function downloadSummaryJSON() {
            const summary = {
                report_metadata: {
                    generated_at: '__GENERATION_TIMESTAMP__',
                    pipeline_version: 'COMPASS v1.2-mod',
                    total_samples: __TOTAL_SAMPLES__
                },
                overview: {
                    total_samples: __TOTAL_SAMPLES__,
                    assembly_qc_passed: __PASSED_QC__,
                    assembly_qc_failed: __FAILED_QC__,
                    assembly_qc_pass_rate: __QC_PASS_RATE__,
                    average_contigs: __AVG_CONTIGS__,
                    average_n50: __AVG_N50__,
                    average_assembly_length: __AVG_LENGTH__,
                    average_gc_percent: __AVG_GC__
                },
                amr_analysis: {
                    total_amr_genes: __TOTAL_AMR_GENES__,
                    samples_with_amr: __SAMPLES_WITH_AMR__,
                    amr_prevalence: __AMR_PREVALENCE__,
                    mdr_samples: __MDR_SAMPLES__,
                    mdr_percentage: __MDR_PCT__,
                    unique_amr_genes: __UNIQUE_AMR_GENES__,
                    unique_amr_classes: __UNIQUE_AMR_CLASSES__
                },
                plasmid_analysis: {
                    total_plasmids: __TOTAL_PLASMIDS__,
                    samples_with_plasmids: __SAMPLES_WITH_PLASMIDS__,
                    plasmid_prevalence: __PLASMID_PREVALENCE__,
                    unique_inc_groups: __UNIQUE_INC_GROUPS__,
                    unique_mobility_types: __UNIQUE_MOBILITY_TYPES__
                },
                prophage_analysis: {
                    total_prophages: __TOTAL_PROPHAGES__,
                    samples_with_prophages: __SAMPLES_WITH_PROPHAGES__,
                    prophage_prevalence: __PROPHAGE_PREVALENCE__,
                    average_prophages_per_sample: __AVG_PROPHAGES__
                }
            };

            const jsonStr = JSON.stringify(summary, null, 2);
            const blob = new Blob([jsonStr], { type: 'application/json' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);

            link.setAttribute('href', url);
            link.setAttribute('download', 'compass_summary.json');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        // Download all charts as PNG files
        function downloadAllChartsPNG() {
            const chartIds = [
                'amrGenesBarChart',
                'amrClassPieChart',
                'mdrComparisonChart',
                'incGroupsBarChart',
                'mobilityPieChart',
                'plasmidCountHist',
                'plasmidAmrScatter',
                'samplesOverTimeChart',
                'amrTrendsChart',
                'prophageTrendChart',
                'plasmidTrendChart',
                'stateSamplesChart',
                'stateMDRChart',
                'regionalComparisonChart',
                'mlstSTChart',
                'mlstSchemeChart',
                'serovarChart',
                'n50HistChart',
                'lengthHistChart',
                'contigHistChart',
                'buscoHistChart',
                'functionalPieChart'
            ];

            var downloaded = 0;
            chartIds.forEach(function(chartId, index) {
                setTimeout(function() {
                    downloadChartPNG(chartId);
                    downloaded++;
                    if (downloaded === chartIds.length) {
                        alert('Downloaded ' + downloaded + ' charts as PNG files!');
                    }
                }, index * 300);  // Stagger downloads by 300ms
            });
        }

        // Download individual chart as PNG
        function downloadChartPNG(chartId) {
            const canvas = document.getElementById(chartId);
            if (!canvas) {
                console.warn('Chart not found: ' + chartId);
                return;
            }

            // Get the chart instance
            const chartInstance = Chart.getChart(canvas);
            if (!chartInstance) {
                console.warn('Chart instance not found: ' + chartId);
                return;
            }

            // Convert to base64 PNG
            const url = canvas.toDataURL('image/png');

            // Create download link
            const link = document.createElement('a');
            link.href = url;
            link.download = chartId + '.png';
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        // Generate PDF report (basic version)
        function generatePDFReport() {
            // Check if jsPDF is loaded
            if (typeof window.jspdf === 'undefined') {
                alert('PDF library not loaded. Please refresh the page and try again.');
                return;
            }

            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();

            var yPos = 20;
            const lineHeight = 7;
            const pageHeight = doc.internal.pageSize.height;

            // Helper to check if new page needed
            function checkPageBreak() {
                if (yPos > pageHeight - 20) {
                    doc.addPage();
                    yPos = 20;
                }
            }

            // Title
            doc.setFontSize(20);
            doc.setTextColor(102, 126, 234);
            doc.text('COMPASS Pipeline Summary Report', 105, yPos, { align: 'center' });
            yPos += 15;

            // Generated timestamp
            doc.setFontSize(10);
            doc.setTextColor(100, 100, 100);
            doc.text('Generated: __GENERATION_DATETIME__', 105, yPos, { align: 'center' });
            yPos += 15;

            // Overview section
            doc.setFontSize(14);
            doc.setTextColor(0, 0, 0);
            doc.text('Overview', 20, yPos);
            yPos += 10;

            doc.setFontSize(10);
            const overviewStats = [
                'Total Samples: __TOTAL_SAMPLES__',
                'Assembly QC Passed: __PASSED_QC__ ({passed_qc/total_samples*100:.1f}%)',
                'Average Contigs: __AVG_CONTIGS_INT__',
                'Average N50: __AVG_N50_KB__ kb',
                '',
                'AMR Analysis',
                'Total AMR Genes: __TOTAL_AMR_GENES__',
                'Samples with AMR: __SAMPLES_WITH_AMR__ (__AMR_PREVALENCE_1F__%)',
                'MDR Samples: __MDR_SAMPLES__ (__MDR_PCT_1F__%)',
                '',
                'Plasmid Analysis',
                'Total Plasmids: __TOTAL_PLASMIDS__',
                'Samples with Plasmids: __SAMPLES_WITH_PLASMIDS__ (__PLASMID_PREVALENCE_1F__%)',
                '',
                'Prophage Analysis',
                'Total Prophages: __TOTAL_PROPHAGES__',
                'Samples with Prophages: __SAMPLES_WITH_PROPHAGES__ (__PROPHAGE_PREVALENCE_1F__%)',
                'Average per Sample: __AVG_PROPHAGES_1F__'
            ];

            overviewStats.forEach(function(stat) {
                checkPageBreak();
                if (stat === '') {
                    yPos += 3;
                } else if (stat.includes('Analysis')) {
                    doc.setFontSize(12);
                    doc.setTextColor(102, 126, 234);
                    doc.text(stat, 20, yPos);
                    doc.setFontSize(10);
                    doc.setTextColor(0, 0, 0);
                    yPos += lineHeight;
                } else {
                    doc.text(stat, 25, yPos);
                    yPos += lineHeight;
                }
            });

            // Footer
            const pageCount = doc.internal.getNumberOfPages();
            for (var i = 1; i <= pageCount; i++) {
                doc.setPage(i);
                doc.setFontSize(8);
                doc.setTextColor(150, 150, 150);
                doc.text('Page ' + i + ' of ' + pageCount, 105, pageHeight - 10, { align: 'center' });
                doc.text('Generated by COMPASS Pipeline v1.2-mod', 105, pageHeight - 5, { align: 'center' });
            }

            // Save PDF
            doc.save('compass_summary_report.pdf');
            alert('PDF report generated successfully!');
        }

        // Initialize table stats and pagination on page load
        window.addEventListener('load', function() {
            filterTable();  // Initialize counts
            updatePagination();  // Initialize pagination
        });

        // Pagination variables
        var currentPage = 1;
        var rowsPerPage = 100;

        // Update table pagination
        function updatePagination() {
            const table = document.getElementById('dataTable');
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            const totalRows = rows.length;
            const totalPages = Math.ceil(totalRows / rowsPerPage);

            // Hide all rows first
            rows.forEach(row => row.style.display = 'none');

            // Show only rows for current page
            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            for (var i = start; i < end && i < totalRows; i++) {
                rows[i].style.display = '';
            }

            // Update pagination info
            document.getElementById('pageInfo').textContent =
                'Page ' + currentPage + ' of ' + totalPages + ' (' + totalRows + ' total rows)';

            // Update button states
            document.getElementById('prevPage').disabled = currentPage === 1;
            document.getElementById('nextPage').disabled = currentPage === totalPages;
            document.getElementById('firstPage').disabled = currentPage === 1;
            document.getElementById('lastPage').disabled = currentPage === totalPages;
        }

        // Pagination controls
        function firstPage() {
            currentPage = 1;
            updatePagination();
        }

        function prevPage() {
            if (currentPage > 1) {
                currentPage--;
                updatePagination();
            }
        }

        function nextPage() {
            const table = document.getElementById('dataTable');
            const rows = table.querySelectorAll('tbody tr');
            const totalPages = Math.ceil(rows.length / rowsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                updatePagination();
            }
        }

        function lastPage() {
            const table = document.getElementById('dataTable');
            const rows = table.querySelectorAll('tbody tr');
            const totalPages = Math.ceil(rows.length / rowsPerPage);
            currentPage = totalPages;
            updatePagination();
        }

        function changePageSize() {
            const select = document.getElementById('pageSizeSelect');
            rowsPerPage = parseInt(select.value);
            currentPage = 1;  // Reset to first page
            updatePagination();
        }

        // Master function to render charts for a specific tab (lazy loading)
        function renderTabCharts(tabName) {
            switch(tabName) {
                case 'amr-analysis':
                    renderAMRCharts();
                    break;
                case 'plasmid-analysis':
                    renderPlasmidCharts();
                    break;
                case 'temporal-analysis':
                    renderTemporalCharts();
                    break;
                case 'assembly-quality':
                    renderAssemblyCharts();
                    break;
                case 'prophage-functional':
                    renderProphageCharts();
                    break;
            }
        }

        // AMR Genes Bar Chart
        const amrGeneLabels = AMR_GENE_LABELS_PLACEHOLDER;
        const amrGeneCounts = AMR_GENE_COUNTS_PLACEHOLDER;

        const amrGenesCtx = document.getElementById('amrGenesBarChart').getContext('2d');
        const amrGenesBar = new Chart(amrGenesCtx, {
            type: 'bar',
            data: {
                labels: amrGeneLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: amrGeneCounts,
                    backgroundColor: '#667eea',
                    borderColor: '#5568d3',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'AMR Gene'
                        }
                    }
                }
            }
        });

        // AMR Class Pie Chart
        const amrClassLabels = AMR_CLASS_LABELS_PLACEHOLDER;
        const amrClassCounts = AMR_CLASS_COUNTS_PLACEHOLDER;

        const amrClassCtx = document.getElementById('amrClassPieChart').getContext('2d');
        const amrClassPie = new Chart(amrClassCtx, {
            type: 'pie',
            data: {
                labels: amrClassLabels,
                datasets: [{
                    data: amrClassCounts,
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384',
                        '#36A2EB', '#FFCE56', '#9966FF', '#FF9F40', '#C9CBCF'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: {
                                size: 12
                            },
                            padding: 10
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });

        // MDR Comparison Bar Chart
        const mdrLabels = ['MDR (≥3 classes)', 'Non-MDR'];
        const mdrCounts = [MDR_SAMPLES_PLACEHOLDER, NON_MDR_SAMPLES_PLACEHOLDER];

        const mdrCtx = document.getElementById('mdrComparisonChart').getContext('2d');
        const mdrBar = new Chart(mdrCtx, {
            type: 'bar',
            data: {
                labels: mdrLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: mdrCounts,
                    backgroundColor: ['#ef4444', '#22c55e'],
                    borderColor: ['#dc2626', '#16a34a'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Resistance Status'
                        }
                    }
                }
            }
        });

        // Plasmid Inc Groups Bar Chart
        const incGroupLabels = INC_GROUP_LABELS_PLACEHOLDER;
        const incGroupCounts = INC_GROUP_COUNTS_PLACEHOLDER;

        const incGroupCtx = document.getElementById('incGroupsBarChart').getContext('2d');
        const incGroupBar = new Chart(incGroupCtx, {
            type: 'bar',
            data: {
                labels: incGroupLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: incGroupCounts,
                    backgroundColor: '#9966FF',
                    borderColor: '#8855ee',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Inc Group'
                        }
                    }
                }
            }
        });

        // Plasmid Mobility Types Pie Chart
        const mobTypeLabels = MOB_TYPE_LABELS_PLACEHOLDER;
        const mobTypeCounts = MOB_TYPE_COUNTS_PLACEHOLDER;

        const mobTypeCtx = document.getElementById('mobilityPieChart').getContext('2d');
        const mobTypePie = new Chart(mobTypeCtx, {
            type: 'pie',
            data: {
                labels: mobTypeLabels,
                datasets: [{
                    data: mobTypeCounts,
                    backgroundColor: [
                        '#FF9F40',  // Conjugative
                        '#4BC0C0',  // Mobilizable
                        '#9966FF',  // Non-mobilizable
                        '#FFCE56',  // Other
                        '#FF6384'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: {
                                size: 12
                            },
                            padding: 10
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });

        // Plasmid Count Histogram
        const plasmidHistLabels = PLASMID_HIST_LABELS_PLACEHOLDER;
        const plasmidHistCounts = PLASMID_HIST_COUNTS_PLACEHOLDER;

        const plasmidHistCtx = document.getElementById('plasmidCountHistChart').getContext('2d');
        const plasmidHist = new Chart(plasmidHistCtx, {
            type: 'bar',
            data: {
                labels: plasmidHistLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: plasmidHistCounts,
                    backgroundColor: '#FF9F40',
                    borderColor: '#e68f39',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Number of Plasmids'
                        }
                    }
                }
            }
        });

        // Plasmid-AMR Correlation Scatter Plot
        const scatterPlasmidX = SCATTER_PLASMID_X_PLACEHOLDER;
        const scatterAmrY = SCATTER_AMR_Y_PLACEHOLDER;

        // Create scatter data array
        const scatterData = scatterPlasmidX.map((x, i) => ({ x: x, y: scatterAmrY[i] }));

        const scatterCtx = document.getElementById('plasmidAmrScatterChart').getContext('2d');
        const scatterChart = new Chart(scatterCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Samples',
                    data: scatterData,
                    backgroundColor: 'rgba(102, 126, 234, 0.5)',
                    borderColor: '#667eea',
                    borderWidth: 1,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Plasmids: ' + context.parsed.x + ', AMR genes: ' + context.parsed.y;
                            }
                        }
                    },
                    decimation: {
                        enabled: true,
                        algorithm: 'lttb',  // Largest-Triangle-Three-Buckets algorithm
                        samples: 500,  // Display max 500 points for large datasets
                        threshold: 1000  // Only decimate if dataset > 1000 points
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Plasmids'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of AMR Genes'
                        }
                    }
                }
            }
        });

        // Temporal Analysis: Sample Collection Over Time
        const temporalYears = TEMPORAL_YEARS_PLACEHOLDER;
        const temporalSampleCounts = TEMPORAL_SAMPLE_COUNTS_PLACEHOLDER;

        const temporalSamplesCtx = document.getElementById('temporalSamplesChart').getContext('2d');
        const temporalSamplesChart = new Chart(temporalSamplesCtx, {
            type: 'line',
            data: {
                labels: temporalYears,
                datasets: [{
                    label: 'Number of Samples',
                    data: temporalSampleCounts,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#667eea'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    }
                }
            }
        });

        // Temporal Analysis: AMR/MDR Percentage Trends
        const temporalAmrPct = TEMPORAL_AMR_PCT_PLACEHOLDER;
        const temporalMdrPct = TEMPORAL_MDR_PCT_PLACEHOLDER;

        const temporalAmrMdrCtx = document.getElementById('temporalAmrMdrChart').getContext('2d');
        const temporalAmrMdrChart = new Chart(temporalAmrMdrCtx, {
            type: 'line',
            data: {
                labels: temporalYears,
                datasets: [{
                    label: 'AMR Positive (%)',
                    data: temporalAmrPct,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }, {
                    label: 'MDR (%)',
                    data: temporalMdrPct,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Percentage (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    }
                }
            }
        });

        // Temporal Analysis: Prophage Detection Over Time
        const temporalProphageCounts = TEMPORAL_PROPHAGE_COUNTS_PLACEHOLDER;

        const temporalProphagesCtx = document.getElementById('temporalProphagesChart').getContext('2d');
        const temporalProphagesChart = new Chart(temporalProphagesCtx, {
            type: 'bar',
            data: {
                labels: temporalYears,
                datasets: [{
                    label: 'Total Prophages',
                    data: temporalProphageCounts,
                    backgroundColor: '#36A2EB',
                    borderColor: '#2e8bc0',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Total Prophages Detected'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    }
                }
            }
        });

        // Temporal Analysis: Plasmid Detection Over Time
        const temporalPlasmidCounts = TEMPORAL_PLASMID_COUNTS_PLACEHOLDER;

        const temporalPlasmidsCtx = document.getElementById('temporalPlasmidsChart').getContext('2d');
        const temporalPlasmidsChart = new Chart(temporalPlasmidsCtx, {
            type: 'bar',
            data: {
                labels: temporalYears,
                datasets: [{
                    label: 'Total Plasmids',
                    data: temporalPlasmidCounts,
                    backgroundColor: '#9966FF',
                    borderColor: '#8855ee',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Total Plasmids Detected'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    }
                }
            }
        });

        // Geographic Analysis: Samples by State
        const stateLabels = {json.dumps(state_labels)};
        const stateCounts = {json.dumps(state_counts)};

        const stateSamplesCtx = document.getElementById('stateSamplesChart').getContext('2d');
        const stateSamplesChart = new Chart(stateSamplesCtx, {
            type: 'bar',
            data: {
                labels: stateLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: stateCounts,
                    backgroundColor: '#36A2EB',
                    borderColor: '#2a8fcc',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',  // Horizontal bar chart
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    }
                }
            }
        });

        // Geographic Analysis: MDR Rates by State
        const stateMDRRates = {json.dumps(state_mdr_rate_values)};

        const stateMDRCtx = document.getElementById('stateMDRChart').getContext('2d');
        const stateMDRChart = new Chart(stateMDRCtx, {
            type: 'bar',
            data: {
                labels: stateLabels,
                datasets: [{
                    label: 'MDR Rate (%)',
                    data: stateMDRRates,
                    backgroundColor: '#ef4444',
                    borderColor: '#dc2626',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',  // Horizontal bar chart
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'MDR Rate (%)'
                        }
                    }
                }
            }
        });

        // Geographic Analysis: Regional Comparison (Scatter Plot)
        const regionalData = stateLabels.map(function(state, i) {
            return {
                x: stateCounts[i],
                y: stateMDRRates[i],
                label: state
            };
        });

        const regionalComparisonCtx = document.getElementById('regionalComparisonChart').getContext('2d');
        const regionalComparisonChart = new Chart(regionalComparisonCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'States',
                    data: regionalData,
                    backgroundColor: '#9966FF',
                    borderColor: '#7744cc',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                var point = context.raw;
                                return point.label + ': ' + point.x + ' samples, ' + point.y.toFixed(1) + '% MDR';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'MDR Rate (%)'
                        }
                    }
                }
            }
        });

        // Strain Typing: MLST Sequence Types
        const mlstSTLabels = {json.dumps(mlst_st_labels)};
        const mlstSTCounts = {json.dumps(mlst_st_counts)};

        const mlstSTCtx = document.getElementById('mlstSTChart').getContext('2d');
        const mlstSTChart = new Chart(mlstSTCtx, {
            type: 'bar',
            data: {
                labels: mlstSTLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: mlstSTCounts,
                    backgroundColor: '#22c55e',
                    borderColor: '#16a34a',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',  // Horizontal bar chart
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    }
                }
            }
        });

        // Strain Typing: MLST Scheme Distribution
        const mlstSchemeLabels = {json.dumps(mlst_scheme_labels)};
        const mlstSchemeCounts = {json.dumps(mlst_scheme_counts)};

        const mlstSchemeCtx = document.getElementById('mlstSchemeChart').getContext('2d');
        const mlstSchemeChart = new Chart(mlstSchemeCtx, {
            type: 'pie',
            data: {
                labels: mlstSchemeLabels,
                datasets: [{
                    data: mlstSchemeCounts,
                    backgroundColor: [
                        '#22c55e',
                        '#10b981',
                        '#14b8a6',
                        '#06b6d4',
                        '#0ea5e9',
                        '#3b82f6'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });

        // Strain Typing: Serovar Distribution (Salmonella)
        const serovarLabels = {json.dumps(serovar_labels)};
        const serovarCounts = {json.dumps(serovar_counts)};

        const serovarCtx = document.getElementById('serovarChart').getContext('2d');
        const serovarChart = new Chart(serovarCtx, {
            type: 'bar',
            data: {
                labels: serovarLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: serovarCounts,
                    backgroundColor: '#f59e0b',
                    borderColor: '#d97706',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',  // Horizontal bar chart
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    }
                }
            }
        });

        // N50 Distribution Histogram
        const n50Labels = N50_LABELS_PLACEHOLDER;
        const n50Counts = N50_COUNTS_PLACEHOLDER;

        const n50Ctx = document.getElementById('n50HistChart').getContext('2d');
        const n50Hist = new Chart(n50Ctx, {
            type: 'bar',
            data: {
                labels: n50Labels,
                datasets: [{
                    label: 'Number of Samples',
                    data: n50Counts,
                    backgroundColor: '#667eea',
                    borderColor: '#5568d3',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'N50 (kb)'
                        }
                    }
                }
            }
        });

        // Assembly Length Distribution Histogram
        const lengthLabels = LENGTH_LABELS_PLACEHOLDER;
        const lengthCounts = LENGTH_COUNTS_PLACEHOLDER;

        const lengthCtx = document.getElementById('lengthHistChart').getContext('2d');
        const lengthHist = new Chart(lengthCtx, {
            type: 'bar',
            data: {
                labels: lengthLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: lengthCounts,
                    backgroundColor: '#36A2EB',
                    borderColor: '#2e8bc0',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Assembly Length (Mb)'
                        }
                    }
                }
            }
        });

        // Contig Count Distribution Histogram
        const contigLabels = CONTIG_LABELS_PLACEHOLDER;
        const contigCounts = CONTIG_COUNTS_PLACEHOLDER;

        const contigCtx = document.getElementById('contigHistChart').getContext('2d');
        const contigHist = new Chart(contigCtx, {
            type: 'bar',
            data: {
                labels: contigLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: contigCounts,
                    backgroundColor: '#FFCE56',
                    borderColor: '#e6b84f',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Number of Contigs'
                        }
                    }
                }
            }
        });

        // BUSCO Completeness Histogram
        const buscoLabels = BUSCO_LABELS_PLACEHOLDER;
        const buscoCounts = BUSCO_COUNTS_PLACEHOLDER;

        const buscoCtx = document.getElementById('buscoHistChart').getContext('2d');
        const buscoHist = new Chart(buscoCtx, {
            type: 'bar',
            data: {
                labels: buscoLabels,
                datasets: [{
                    label: 'Number of Samples',
                    data: buscoCounts,
                    backgroundColor: '#4BC0C0',
                    borderColor: '#3da8a8',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Samples'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'BUSCO Completeness (%)'
                        }
                    }
                }
            }
        });

        // Prophage Functional Diversity Pie Chart
        const functionalLabels = FUNCTIONAL_LABELS_PLACEHOLDER;
        const functionalData = FUNCTIONAL_DATA_PLACEHOLDER;

        const functionalCtx = document.getElementById('functionalPieChart').getContext('2d');
        const functionalPieChart = new Chart(functionalCtx, {
            type: 'pie',
            data: {
                labels: functionalLabels,
                datasets: [{
                    data: functionalData,
                    backgroundColor: [
                        '#FF6384',  // DNA Packaging
                        '#36A2EB',  // Structural
                        '#FFCE56',  // Lysis
                        '#4BC0C0',  // Regulation
                        '#9966FF',  // DNA Modification
                        '#C9CBCF'   // Other
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: {
                                size: 14
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    </script>

    <!-- Footer with Report Metadata -->
    <div class="footer">
        <h3>Report Information</h3>
        <div class="footer-content">
            <div class="footer-section">
                <h4>Generation Details</h4>
                <p><strong>Generated:</strong> GENERATION_TIME_PLACEHOLDER</p>
                <p><strong>Pipeline:</strong> COMPASS v1.2-mod</p>
                <p><strong>Report Version:</strong> Enhanced Interactive v2.0</p>
            </div>
            <div class="footer-section">
                <h4>Dataset Summary</h4>
                <p><strong>Total Samples:</strong> TOTAL_SAMPLES_PLACEHOLDER</p>
                <p><strong>Date Range:</strong> YEAR_RANGE_PLACEHOLDER</p>
                <p><strong>Organisms:</strong> ORGANISMS_PLACEHOLDER</p>
            </div>
            <div class="footer-section">
                <h4>Analysis Modules</h4>
                <p>✓ Assembly QC (QUAST + BUSCO)</p>
                <p>✓ AMR Detection (AMRFinderPlus)</p>
                <p>✓ Prophage Identification (VIBRANT)</p>
                <p>✓ Plasmid Analysis (MOB-suite)</p>
                <p>✓ Strain Typing (MLST + SISTR)</p>
            </div>
        </div>
        <div class="footer-links">
            <span>COMPASS Pipeline - Comprehensive Mobile element & Pathogen ASsessment Suite</span>
            <span>|</span>
            <a href="https://github.com/tylerdougan/COMPASS-pipeline" target="_blank">GitHub</a>
            <span>|</span>
            <span>Generated with Python {sys.version.split()[0]}, pandas {pd.__version__}, Chart.js 4.4.0</span>
        </div>
    </div>
</body>
</html>
"""

    # Replace placeholders in JavaScript with actual data
    # AMR data
    js_code = js_code.replace('AMR_GENE_LABELS_PLACEHOLDER', json.dumps(amr_gene_labels))
    js_code = js_code.replace('AMR_GENE_COUNTS_PLACEHOLDER', json.dumps(amr_gene_counts))
    js_code = js_code.replace('AMR_CLASS_LABELS_PLACEHOLDER', json.dumps(amr_class_labels))
    js_code = js_code.replace('AMR_CLASS_COUNTS_PLACEHOLDER', json.dumps(amr_class_counts))
    js_code = js_code.replace('MDR_SAMPLES_PLACEHOLDER', str(mdr_samples))
    js_code = js_code.replace('NON_MDR_SAMPLES_PLACEHOLDER', str(total_samples - mdr_samples))

    # Plasmid data
    js_code = js_code.replace('INC_GROUP_LABELS_PLACEHOLDER', json.dumps(inc_group_labels))
    js_code = js_code.replace('INC_GROUP_COUNTS_PLACEHOLDER', json.dumps(inc_group_counts))
    js_code = js_code.replace('MOB_TYPE_LABELS_PLACEHOLDER', json.dumps(mob_type_labels))
    js_code = js_code.replace('MOB_TYPE_COUNTS_PLACEHOLDER', json.dumps(mob_type_counts))
    js_code = js_code.replace('PLASMID_HIST_LABELS_PLACEHOLDER', json.dumps(plasmid_hist_labels))
    js_code = js_code.replace('PLASMID_HIST_COUNTS_PLACEHOLDER', json.dumps(plasmid_hist_counts))
    js_code = js_code.replace('SCATTER_PLASMID_X_PLACEHOLDER', json.dumps(scatter_plasmid_x))
    js_code = js_code.replace('SCATTER_AMR_Y_PLACEHOLDER', json.dumps(scatter_amr_y))

    # Temporal analysis data
    js_code = js_code.replace('TEMPORAL_YEARS_PLACEHOLDER', json.dumps(temporal_years))
    js_code = js_code.replace('TEMPORAL_SAMPLE_COUNTS_PLACEHOLDER', json.dumps(temporal_sample_counts))
    js_code = js_code.replace('TEMPORAL_AMR_PCT_PLACEHOLDER', json.dumps(temporal_amr_pct))
    js_code = js_code.replace('TEMPORAL_MDR_PCT_PLACEHOLDER', json.dumps(temporal_mdr_pct))
    js_code = js_code.replace('TEMPORAL_PROPHAGE_COUNTS_PLACEHOLDER', json.dumps(temporal_prophage_counts))
    js_code = js_code.replace('TEMPORAL_PLASMID_COUNTS_PLACEHOLDER', json.dumps(temporal_plasmid_counts))

    # Assembly quality data
    js_code = js_code.replace('N50_LABELS_PLACEHOLDER', json.dumps(n50_labels))
    js_code = js_code.replace('N50_COUNTS_PLACEHOLDER', json.dumps(n50_counts))
    js_code = js_code.replace('LENGTH_LABELS_PLACEHOLDER', json.dumps(length_labels))
    js_code = js_code.replace('LENGTH_COUNTS_PLACEHOLDER', json.dumps(length_counts))
    js_code = js_code.replace('CONTIG_LABELS_PLACEHOLDER', json.dumps(contig_labels))
    js_code = js_code.replace('CONTIG_COUNTS_PLACEHOLDER', json.dumps(contig_counts))
    js_code = js_code.replace('BUSCO_LABELS_PLACEHOLDER', json.dumps(busco_labels))
    js_code = js_code.replace('BUSCO_COUNTS_PLACEHOLDER', json.dumps(busco_counts))

    # Prophage functional diversity data
    js_code = js_code.replace('FUNCTIONAL_LABELS_PLACEHOLDER', json.dumps(functional_labels))
    js_code = js_code.replace('FUNCTIONAL_DATA_PLACEHOLDER', json.dumps(functional_values))

    # Replace summary statistics placeholders
    from datetime import datetime
    js_code = js_code.replace('__GENERATION_TIMESTAMP__', datetime.now().isoformat())
    js_code = js_code.replace('__GENERATION_DATETIME__', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    js_code = js_code.replace('__TOTAL_SAMPLES__', str(total_samples))
    js_code = js_code.replace('__PASSED_QC__', str(passed_qc))
    js_code = js_code.replace('__FAILED_QC__', str(failed_qc))
    js_code = js_code.replace('__QC_PASS_RATE__', f'{passed_qc/total_samples*100:.2f}')
    js_code = js_code.replace('__AVG_CONTIGS__', f'{avg_contigs:.2f}')
    js_code = js_code.replace('__AVG_CONTIGS_INT__', f'{avg_contigs:.0f}')
    js_code = js_code.replace('__AVG_N50__', f'{avg_n50:.2f}')
    js_code = js_code.replace('__AVG_N50_KB__', f'{avg_n50/1000:.1f}')
    js_code = js_code.replace('__AVG_LENGTH__', f'{avg_length:.2f}')
    js_code = js_code.replace('__AVG_GC__', f'{avg_gc:.2f}')
    js_code = js_code.replace('__TOTAL_AMR_GENES__', str(total_amr_genes))
    js_code = js_code.replace('__SAMPLES_WITH_AMR__', str(samples_with_amr))
    js_code = js_code.replace('__AMR_PREVALENCE__', f'{samples_with_amr/total_samples*100:.2f}')
    js_code = js_code.replace('__AMR_PREVALENCE_1F__', f'{samples_with_amr/total_samples*100:.1f}')
    js_code = js_code.replace('__MDR_SAMPLES__', str(mdr_samples))
    js_code = js_code.replace('__MDR_PCT__', f'{mdr_pct:.2f}')
    js_code = js_code.replace('__MDR_PCT_1F__', f'{mdr_pct:.1f}')
    js_code = js_code.replace('__UNIQUE_AMR_GENES__', str(len(amr_gene_counter)))
    js_code = js_code.replace('__UNIQUE_AMR_CLASSES__', str(len(amr_class_counter)))
    js_code = js_code.replace('__TOTAL_PLASMIDS__', str(total_plasmids))
    js_code = js_code.replace('__SAMPLES_WITH_PLASMIDS__', str(samples_with_plasmids))
    js_code = js_code.replace('__PLASMID_PREVALENCE__', f'{samples_with_plasmids/total_samples*100:.2f}')
    js_code = js_code.replace('__PLASMID_PREVALENCE_1F__', f'{samples_with_plasmids/total_samples*100:.1f}')
    js_code = js_code.replace('__UNIQUE_INC_GROUPS__', str(len(inc_group_counter)))
    js_code = js_code.replace('__UNIQUE_MOBILITY_TYPES__', str(len(mobility_type_counter)))
    js_code = js_code.replace('__TOTAL_PROPHAGES__', str(total_prophages))
    js_code = js_code.replace('__SAMPLES_WITH_PROPHAGES__', str(samples_with_prophages))
    js_code = js_code.replace('__PROPHAGE_PREVALENCE__', f'{samples_with_prophages/total_samples*100:.2f}')
    js_code = js_code.replace('__PROPHAGE_PREVALENCE_1F__', f'{samples_with_prophages/total_samples*100:.1f}')
    js_code = js_code.replace('__AVG_PROPHAGES__', f'{avg_prophages:.2f}')
    js_code = js_code.replace('__AVG_PROPHAGES_1F__', f'{avg_prophages:.1f}')

    # Append JavaScript to HTML
    html += js_code

    # Prepare footer metadata
    generation_time_str = generation_time.strftime("%Y-%m-%d %H:%M:%S")

    # Calculate year range
    year_range = "Unknown"
    if 'year' in df.columns:
        years = []
        for year_val in df['year']:
            if year_val and year_val != '-' and year_val != 'Unknown':
                try:
                    years.append(int(float(year_val)))
                except (ValueError, TypeError):
                    pass
        if years:
            year_range = f"{min(years)}-{max(years)}" if min(years) != max(years) else str(min(years))

    # Get organisms summary
    organisms_str = "Unknown"
    if 'organism' in df.columns:
        organism_counts = df['organism'].value_counts()
        organisms_list = [f"{org} ({count})" for org, count in organism_counts.head(3).items()]
        if len(organism_counts) > 3:
            organisms_list.append(f"+{len(organism_counts) - 3} more")
        organisms_str = ", ".join(organisms_list)

    # Replace footer placeholders
    html = html.replace('GENERATION_TIME_PLACEHOLDER', generation_time_str)
    html = html.replace('TOTAL_SAMPLES_PLACEHOLDER', str(total_samples))
    html = html.replace('YEAR_RANGE_PLACEHOLDER', year_range)
    html = html.replace('ORGANISMS_PLACEHOLDER', organisms_str)

    # Write HTML file
    with open(output_file, 'w') as f:
        f.write(html)

def main():
    args = parse_args()
    outdir = Path(args.outdir)

    print(f"Generating comprehensive COMPASS summary from {outdir}")

    # Parse optional metadata
    metadata = parse_metadata(args.metadata)

    # Parse all result files
    print("Parsing QUAST assembly statistics...")
    quast_data = parse_quast(outdir / 'quast')

    print("Parsing BUSCO completeness metrics...")
    busco_data = parse_busco(outdir / 'busco')

    print("Parsing MLST typing results...")
    mlst_data = parse_mlst(outdir / 'mlst')

    print("Parsing SISTR serovar predictions...")
    sistr_data = parse_sistr(outdir / 'sistr')

    print("Parsing AMRFinder results...")
    amr_data = parse_amrfinder(outdir / 'amrfinder')

    print("Parsing MOB-suite plasmid results...")
    mobsuite_data = parse_mobsuite(outdir / 'mobsuite')

    print("Parsing VIBRANT prophage results...")
    vibrant_data = parse_vibrant(outdir / 'vibrant')

    print("Parsing VIBRANT functional annotations...")
    functional_diversity = parse_vibrant_annotations(outdir / 'vibrant')
    if functional_diversity:
        print(f"  Found {sum(functional_diversity.values())} categorized prophage genes")
        for category, count in functional_diversity.items():
            print(f"    {category}: {count}")

    print("Parsing DIAMOND prophage matches...")
    diamond_data = parse_diamond_prophage(outdir / 'diamond_prophage')

    # Combine all data
    all_samples = set()
    for data_dict in [quast_data, busco_data, mlst_data, sistr_data, amr_data,
                     mobsuite_data, vibrant_data, diamond_data, metadata]:
        all_samples.update(data_dict.keys())

    print(f"Found {len(all_samples)} total samples")

    # Build comprehensive summary table
    summary_data = []
    for sample in sorted(all_samples):
        row = {'sample_id': sample}

        # Sample metadata (if available)
        if sample in metadata:
            row['organism'] = metadata[sample].get('organism', '-')
            row['state'] = metadata[sample].get('state', '-')
            row['year'] = metadata[sample].get('year', '-')
            row['source'] = metadata[sample].get('source', '-')

        # Assembly quality metrics
        if sample in quast_data:
            row.update(quast_data[sample])
        else:
            row.update({
                'num_contigs': '-',
                'assembly_length': '-',
                'n50': '-',
                'gc_percent': '-',
                'assembly_quality': 'No data'
            })

        # BUSCO completeness/contamination
        if sample in busco_data:
            row.update(busco_data[sample])
        else:
            row.update({
                'busco_complete_pct': '-',
                'busco_duplicated_pct': '-',
                'busco_summary': '-'
            })

        # Strain typing
        if sample in mlst_data:
            row.update(mlst_data[sample])
        else:
            row.update({'mlst_scheme': '-', 'mlst_st': '-'})

        if sample in sistr_data:
            row['serovar'] = sistr_data[sample]['serovar']
        else:
            row['serovar'] = '-'

        # AMR summary
        if sample in amr_data:
            row.update(amr_data[sample])
        else:
            row.update({
                'num_amr_genes': 0,
                'num_point_mutations': 0,
                'amr_classes': '-',
                'mdr_status': 'No',
                'top_amr_genes': '-'
            })

        # Mobile elements
        if sample in mobsuite_data:
            row.update(mobsuite_data[sample])
        else:
            row.update({
                'num_plasmids': 0,
                'inc_groups': '-',
                'mob_types': '-'
            })

        # Phage summary
        if sample in vibrant_data:
            row.update(vibrant_data[sample])
        else:
            row.update({
                'num_prophages': 0,
                'num_lytic': 0,
                'num_lysogenic': 0
            })

        if sample in diamond_data:
            row.update(diamond_data[sample])
        else:
            row.update({
                'num_prophage_hits': 0,
                'top_prophage_matches': '-'
            })

        summary_data.append(row)

    # Create DataFrame
    df = pd.DataFrame(summary_data)

    # Reorder columns for better readability
    column_order = ['sample_id']
    if 'organism' in df.columns:
        column_order.extend(['organism', 'state', 'year', 'source'])

    column_order.extend([
        # Assembly metrics
        'num_contigs', 'assembly_length', 'n50', 'assembly_quality',
        # BUSCO
        'busco_complete_pct', 'busco_duplicated_pct', 'busco_summary',
        # Typing
        'mlst_st', 'mlst_scheme', 'serovar',
        # AMR
        'num_amr_genes', 'num_point_mutations', 'amr_classes', 'mdr_status', 'top_amr_genes',
        # Plasmids
        'num_plasmids', 'inc_groups', 'mob_types',
        # Phages
        'num_prophages', 'num_lytic', 'num_lysogenic', 'num_prophage_hits', 'top_prophage_matches'
    ])

    # Only include columns that exist
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]

    # Create output directories if they don't exist
    import os
    tsv_dir = os.path.dirname(args.output_tsv)
    if tsv_dir and not os.path.exists(tsv_dir):
        os.makedirs(tsv_dir, exist_ok=True)
        print(f"Created output directory: {tsv_dir}")

    html_dir = os.path.dirname(args.output_html)
    if html_dir and not os.path.exists(html_dir):
        os.makedirs(html_dir, exist_ok=True)
        print(f"Created output directory: {html_dir}")

    # Save TSV
    df.to_csv(args.output_tsv, sep='\t', index=False)
    print(f"✓ TSV summary written to {args.output_tsv}")

    # Check for MultiQC report
    multiqc_report = outdir / 'multiqc' / 'multiqc_report.html'
    if multiqc_report.exists():
        print(f"✓ Found MultiQC report at {multiqc_report}")
    else:
        print(f"⚠️  MultiQC report not found at {multiqc_report}")
        multiqc_report = None

    # Generate HTML report with functional diversity data and MultiQC
    generation_time = datetime.now()
    generate_html_report(df, args.output_html,
                        functional_diversity=functional_diversity,
                        multiqc_path=multiqc_report,
                        generation_time=generation_time)
    print(f"✓ HTML report written to {args.output_html}")

    print(f"\n=== Summary Statistics ===")
    print(f"Total samples: {len(summary_data)}")
    print(f"Samples with assembly data: {len(quast_data)}")
    print(f"Samples with AMR genes: {len([s for s in summary_data if s.get('num_amr_genes', 0) > 0])}")
    print(f"Samples with prophages: {len([s for s in summary_data if s.get('num_prophages', 0) > 0])}")
    print(f"MDR samples: {len([s for s in summary_data if s.get('mdr_status') == 'Yes'])}")

if __name__ == '__main__':
    main()
