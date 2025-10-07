process COMBINE_RESULTS {
    publishDir "${params.outdir}/reports", mode: 'copy'
    
    label 'process_low'
    
    input:
    path amr_files, stageAs: 'amr/*'
    path vibrant_results, stageAs: 'vibrant/*'
    path diamond_results, stageAs: 'diamond/*'
    path phanotate_results, stageAs: 'phanotate/*'
    path report_script
    
    output:
    path "compass_integrated_summary.tsv", emit: summary
    path "compass_report.html", emit: report
    path "phage_analysis_summary.tsv", emit: phage_summary, optional: true
    path "versions.yml", emit: versions
    
    script:
    """
    #!/bin/bash
    set -euo pipefail
    
    # Create output directory
    mkdir -p results
    
    # Process VIBRANT results for phage data
    python3 << 'EOFPYTHON'
import pandas as pd
import glob
import os
from pathlib import Path

# Initialize summary data
summary_data = []

# Process VIBRANT results
vibrant_dirs = glob.glob("vibrant/*_vibrant")
for vdir in vibrant_dirs:
    sample_id = Path(vdir).name.replace('_vibrant', '')
    
    quality_files = glob.glob(f"{vdir}/VIBRANT_*/VIBRANT_results_*/VIBRANT_genome_quality_*.tsv")
    
    phage_count = 0
    lytic_count = 0
    lysogenic_count = 0
    quality_list = []
    
    if quality_files and os.path.exists(quality_files[0]):
        df = pd.read_csv(quality_files[0], sep='\\t')
        phage_count = len(df)
        
        if 'type' in df.columns:
            lytic_count = len(df[df['type'] == 'lytic'])
            lysogenic_count = len(df[df['type'] == 'lysogenic'])
        
        if 'Quality' in df.columns:
            for qual in df['Quality'].dropna():
                if 'complete' in str(qual).lower():
                    quality_list.append('Complete')
                elif 'high' in str(qual).lower():
                    quality_list.append('High-quality')
                elif 'medium' in str(qual).lower():
                    quality_list.append('Medium-quality')
                elif 'low' in str(qual).lower():
                    quality_list.append('Low-quality')
    
    quality_summary = ', '.join(set(quality_list)) if quality_list else 'N/A'
    
    summary_data.append({
        'sample_id': sample_id,
        'phage_count': phage_count,
        'lytic_count': lytic_count,
        'lysogenic_count': lysogenic_count,
        'quality_summary': quality_summary
    })

# Process DIAMOND results for prophage hits
diamond_data = {}
diamond_files = glob.glob("diamond/*_diamond_results.tsv")
for df_file in diamond_files:
    sample_id = Path(df_file).stem.replace('_diamond_results', '')
    
    if os.path.exists(df_file) and os.path.getsize(df_file) > 0:
        df = pd.read_csv(df_file, sep='\\t', header=None)
        diamond_data[sample_id] = len(df)
    else:
        diamond_data[sample_id] = 0

# Process PHANOTATE results for gene predictions
phanotate_data = {}
phanotate_files = glob.glob("phanotate/*_phanotate.gff")
for gff_file in phanotate_files:
    sample_id = Path(gff_file).stem.replace('_phanotate', '')
    
    gene_count = 0
    if os.path.exists(gff_file) and os.path.getsize(gff_file) > 0:
        with open(gff_file, 'r') as f:
            for line in f:
                if not line.startswith('>') and not line.startswith('#') and 'CDS' in line:
                    gene_count += 1
    
    phanotate_data[sample_id] = gene_count

# Combine phage data
for item in summary_data:
    sample = item['sample_id']
    item['prophage_hits'] = diamond_data.get(sample, 0)
    item['predicted_genes'] = phanotate_data.get(sample, 0)

# Save phage summary
phage_df = pd.DataFrame(summary_data)
phage_df.to_csv('results/phage_summary.tsv', sep='\\t', index=False)

EOFPYTHON
    
    # Process AMR data
    python3 << 'EOFAMR'
import pandas as pd
import glob
from pathlib import Path

amr_data = []
mutation_data = []

# Process AMRFinderPlus results
amr_files = glob.glob("amr/*.tsv")
for amr_file in amr_files:
    sample_id = Path(amr_file).stem.replace('_amrfinder', '')
    
    if Path(amr_file).stat().st_size > 0:
        df = pd.read_csv(amr_file, sep='\\t')
        
        # AMR genes
        if not df.empty:
            df['sample_id'] = sample_id
            
            # Rename columns to match expected format
            column_mapping = {
                'Gene symbol': 'gene',
                'Sequence name': 'contig',
                'Start': 'start',
                'Stop': 'end',
                '% Coverage of reference sequence': 'coverage',
                '% Identity to reference sequence': 'identity',
                'Class': 'resistance_class',
                'Subclass': 'subclass'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Separate genes and mutations
            if 'Element type' in df.columns:
                genes = df[df['Element type'].isin(['AMR', 'STRESS'])].copy()
                mutations = df[df['Element type'] == 'POINT'].copy()
                
                if not genes.empty:
                    genes_subset = genes[['sample_id', 'gene', 'resistance_class', 
                                         'identity', 'coverage', 'contig', 'start', 'end']].copy()
                    amr_data.append(genes_subset)
                
                if not mutations.empty:
                    mutations_subset = mutations[['sample_id', 'gene', 'resistance_class']].copy()
                    mutations_subset['mutation'] = mutations.get('Protein identifier', 'Unknown')
                    mutation_data.append(mutations_subset)
            else:
                # If no Element type column, treat all as genes
                genes_subset = df[['sample_id', 'gene', 'resistance_class', 
                                  'identity', 'coverage', 'contig', 'start', 'end']].copy()
                amr_data.append(genes_subset)

# Combine and save
if amr_data:
    amr_df = pd.concat(amr_data, ignore_index=True)
    amr_df.to_csv('results/amr_genes.tsv', sep='\\t', index=False)
else:
    # Create empty file with headers
    pd.DataFrame(columns=['sample_id', 'gene', 'resistance_class', 'identity', 
                         'coverage', 'contig', 'start', 'end']).to_csv('results/amr_genes.tsv', sep='\\t', index=False)

if mutation_data:
    mut_df = pd.concat(mutation_data, ignore_index=True)
    mut_df.to_csv('results/amr_mutations.tsv', sep='\\t', index=False)
else:
    # Create empty file with headers
    pd.DataFrame(columns=['sample_id', 'gene', 'mutation', 'resistance_class']).to_csv('results/amr_mutations.tsv', sep='\\t', index=False)

EOFAMR
    
    # Run the enhanced report generator
    python3 ${report_script} results results/amr_genes.tsv results/amr_mutations.tsv results/phage_summary.tsv
    
    # Move outputs to expected locations
    mv results/compass_integrated_summary.tsv . || touch compass_integrated_summary.tsv
    mv results/compass_report.html . || touch compass_report.html
    mv results/phage_summary.tsv phage_analysis_summary.tsv || touch phage_analysis_summary.tsv
    
    # Create versions file
    cat > versions.yml << VERSION
    "COMBINE_RESULTS":
      python: "\$(python3 --version | cut -d' ' -f2)"
      pandas: "\$(python3 -c 'import pandas; print(pandas.__version__)')"
    VERSION
    """
}