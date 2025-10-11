#!/usr/bin/env python3
"""
COMPASS Pipeline Summary Report Generator
Aggregates results from all pipeline modules into a comprehensive summary
"""

import argparse
import pandas as pd
import json
from pathlib import Path
import sys

def parse_args():
    parser = argparse.ArgumentParser(description='Generate COMPASS summary report')
    parser.add_argument('--outdir', required=True, help='Pipeline output directory')
    parser.add_argument('--output', default='compass_summary.tsv', help='Output summary file')
    return parser.parse_args()

def parse_mlst(mlst_dir):
    """Parse MLST results"""
    mlst_data = {}
    mlst_path = Path(mlst_dir)
    if mlst_path.exists():
        for mlst_file in mlst_path.glob('*_mlst.tsv'):
            sample_id = mlst_file.stem.replace('_mlst', '')
            try:
                df = pd.read_csv(mlst_file, sep='\t')
                if not df.empty:
                    mlst_data[sample_id] = {
                        'mlst_scheme': df.iloc[0]['SCHEME'] if 'SCHEME' in df.columns else '-',
                        'mlst_st': df.iloc[0]['ST'] if 'ST' in df.columns else '-'
                    }
            except:
                pass
    return mlst_data

def parse_sistr(sistr_dir):
    """Parse SISTR results"""
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
                        'serogroup': df.iloc[0].get('serogroup', '-')
                    }
            except:
                pass
    return sistr_data

def parse_amrfinder(amr_dir):
    """Parse AMRFinder results"""
    amr_data = {}
    amr_path = Path(amr_dir)
    if amr_path.exists():
        for amr_file in amr_path.glob('*_amr.tsv'):
            sample_id = amr_file.stem.replace('_amr', '')
            try:
                df = pd.read_csv(amr_file, sep='\t')
                amr_data[sample_id] = {
                    'amr_genes': len(df) if not df.empty else 0,
                    'amr_classes': ','.join(df['Class'].unique()) if not df.empty and 'Class' in df.columns else '-'
                }
            except:
                amr_data[sample_id] = {'amr_genes': 0, 'amr_classes': '-'}
    return amr_data

def parse_quast(quast_dir):
    """Parse QUAST assembly statistics"""
    quast_data = {}
    quast_path = Path(quast_dir)
    if quast_path.exists():
        for report_file in quast_path.glob('*/report.tsv'):
            try:
                df = pd.read_csv(report_file, sep='\t', index_col=0)
                sample_id = df.columns[0]
                quast_data[sample_id] = {
                    'assembly_length': df.loc['Total length', sample_id] if 'Total length' in df.index else '-',
                    'n50': df.loc['N50', sample_id] if 'N50' in df.index else '-',
                    'num_contigs': df.loc['# contigs', sample_id] if '# contigs' in df.index else '-',
                    'gc_percent': df.loc['GC (%)', sample_id] if 'GC (%)' in df.index else '-'
                }
            except:
                pass
    return quast_data

def parse_busco(busco_dir):
    """Parse BUSCO completeness"""
    busco_data = {}
    busco_path = Path(busco_dir)
    if busco_path.exists():
        for summary_file in busco_path.glob('*/short_summary.*.txt'):
            sample_id = summary_file.parent.name.replace('_busco', '')
            try:
                with open(summary_file) as f:
                    for line in f:
                        if 'C:' in line:
                            # Extract BUSCO percentages
                            parts = line.split('[')[1].split(']')[0]
                            busco_data[sample_id] = {'busco_completeness': parts}
                            break
            except:
                pass
    return busco_data

def parse_mobsuite(mobsuite_dir):
    """Parse MOB-suite plasmid results"""
    mobsuite_data = {}
    mobsuite_path = Path(mobsuite_dir)
    if mobsuite_path.exists():
        for result_dir in mobsuite_path.glob('*_mobsuite'):
            sample_id = result_dir.name.replace('_mobsuite', '')
            plasmid_files = list(result_dir.glob('plasmid_*.fasta'))
            mobsuite_data[sample_id] = {
                'num_plasmids': len(plasmid_files)
            }
    return mobsuite_data

def main():
    args = parse_args()
    outdir = Path(args.outdir)

    print(f"Generating COMPASS summary from {outdir}")

    # Parse all result files
    mlst_data = parse_mlst(outdir / 'mlst')
    sistr_data = parse_sistr(outdir / 'sistr')
    amr_data = parse_amrfinder(outdir / 'amrfinder')
    quast_data = parse_quast(outdir / 'quast')
    busco_data = parse_busco(outdir / 'busco')
    mobsuite_data = parse_mobsuite(outdir / 'mobsuite')

    # Combine all data
    all_samples = set()
    for data_dict in [mlst_data, sistr_data, amr_data, quast_data, busco_data, mobsuite_data]:
        all_samples.update(data_dict.keys())

    summary_data = []
    for sample in sorted(all_samples):
        row = {'sample_id': sample}

        # Add MLST data
        row.update(mlst_data.get(sample, {'mlst_scheme': '-', 'mlst_st': '-'}))

        # Add SISTR data
        row.update(sistr_data.get(sample, {'serovar': '-', 'serogroup': '-'}))

        # Add AMR data
        row.update(amr_data.get(sample, {'amr_genes': 0, 'amr_classes': '-'}))

        # Add assembly stats
        row.update(quast_data.get(sample, {'assembly_length': '-', 'n50': '-', 'num_contigs': '-', 'gc_percent': '-'}))

        # Add BUSCO
        row.update(busco_data.get(sample, {'busco_completeness': '-'}))

        # Add plasmid data
        row.update(mobsuite_data.get(sample, {'num_plasmids': 0}))

        summary_data.append(row)

    # Create DataFrame and save
    df = pd.DataFrame(summary_data)
    df.to_csv(args.output, sep='\t', index=False)

    print(f"Summary report written to {args.output}")
    print(f"Total samples: {len(summary_data)}")

if __name__ == '__main__':
    main()
