#!/usr/bin/env python3
"""
Comprehensive AMR-Prophage Analysis Suite
Combines all analyses into one tool with terminal output and HTML dashboard:
1. Physical co-location analysis
2. Multi-drug resistance islands
3. Species comparison
4. Temporal and source stratification
"""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import csv
import json

# ============================================================================
# SHARED PARSING FUNCTIONS
# ============================================================================

def parse_metadata(metadata_file):
    """Parse full metadata from filtered_samples.csv"""
    metadata = {}
    organism_map = {}

    if not Path(metadata_file).exists():
        return metadata, organism_map

    with open(metadata_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row['Run']

            # Handle both 'organism' and 'Organism' column names
            organism = row.get('organism', row.get('Organism', 'Unknown'))

            # Handle both 'Year' and 'Collection_Date'
            year = row.get('Year', '')
            if not year and 'Collection_Date' in row:
                year = row['Collection_Date'][:4] if row['Collection_Date'] else 'Unknown'
            if not year:
                year = 'Unknown'

            # Handle various source column names
            source = row.get('Isolation_source', row.get('source', 'Unknown'))
            sample_name = row.get('SampleName', '')

            organism_map[sample_id] = organism
            metadata[sample_id] = {
                'organism': organism,
                'year': year,
                'source': source,
                'sample_name': sample_name,
                'state': row.get('geo_loc_name_state_province', 'Unknown'),
                'bioproject': row.get('BioProject', '')
            }

    return metadata, organism_map

def parse_amr_by_contig(amr_file):
    """Extract AMR genes grouped by contig"""
    contig_amr = defaultdict(list)

    if not Path(amr_file).exists():
        return contig_amr

    with open(amr_file) as f:
        header = next(f, None)
        if not header:
            return contig_amr

        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 11:
                contig = parts[1]
                element_type = parts[8]
                gene_symbol = parts[5]
                gene_class = parts[10]

                if element_type == 'AMR' and gene_symbol != 'NA':
                    contig_amr[contig].append({
                        'gene': gene_symbol,
                        'class': gene_class,
                        'start': int(parts[2]),
                        'end': int(parts[3])
                    })

    return contig_amr

def parse_prophage_contigs(vibrant_phages_file):
    """Extract prophage-containing contigs"""
    prophage_contigs = set()

    if not Path(vibrant_phages_file).exists():
        return prophage_contigs

    with open(vibrant_phages_file) as f:
        for line in f:
            if line.startswith('>'):
                contig = '_'.join(line.strip()[1:].split('_')[:-2])
                prophage_contigs.add(contig)

    return prophage_contigs

def parse_mlst(mlst_file):
    """Parse MLST sequence type"""
    if not Path(mlst_file).exists():
        return None

    with open(mlst_file) as f:
        line = f.readline().strip()
        parts = line.split('\t')
        if len(parts) >= 3:
            st = parts[2]
            return st if st != '-' else None

    return None

def parse_prophage_functions(vibrant_annotations_file):
    """Extract prophage gene functional annotations"""
    functions = []
    if not Path(vibrant_annotations_file).exists():
        return functions

    with open(vibrant_annotations_file) as f:
        header = next(f, None)
        if not header:
            return functions

        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue

            ko_name = parts[4] if len(parts) > 4 else ""
            pfam_name = parts[9] if len(parts) > 9 else ""
            vog_name = parts[14] if len(parts) > 14 else ""

            function_category = categorize_prophage_function(ko_name, pfam_name, vog_name)
            if function_category:
                functions.append(function_category)

    return functions

def categorize_prophage_function(ko_name, pfam_name, vog_name):
    """Categorize prophage genes into functional classes"""
    combined = f"{ko_name} {pfam_name} {vog_name}".lower()

    if any(term in combined for term in ['integrase', 'recombinase', 'transposase']):
        return 'Integrase/Recombinase'
    elif any(term in combined for term in ['terminase', 'portal']):
        return 'DNA_Packaging'
    elif any(term in combined for term in ['tail', 'baseplate', 'fiber']):
        return 'Tail_Assembly'
    elif any(term in combined for term in ['capsid', 'head', 'coat']):
        return 'Head/Capsid'
    elif any(term in combined for term in ['lyso', 'lysis', 'holin', 'spanin', 'endopeptidase']):
        return 'Lysis'
    elif any(term in combined for term in ['replication', 'primase', 'helicase', 'polymerase']):
        return 'DNA_Replication'
    elif any(term in combined for term in ['repressor', 'regulator', 'antitermination']):
        return 'Regulation'
    elif any(term in combined for term in ['recombinase', 'excisionase']):
        return 'Recombination'
    elif any(term in combined for term in ['antirepressor', 'anti-repressor']):
        return 'Antirepressor'
    elif any(term in combined for term in ['methylase', 'methyltransferase']):
        return 'DNA_Modification'
    elif any(term in combined for term in ['endonuclease', 'nuclease']):
        return 'Nuclease'
    else:
        return None

def get_contig_length(contig_name):
    """Extract contig length from name (format: NODE_X_length_12345_cov_Y)"""
    try:
        parts = contig_name.split('_')
        for i, part in enumerate(parts):
            if part == 'length' and i + 1 < len(parts):
                return int(parts[i + 1])
    except (ValueError, IndexError):
        pass
    return None

def categorize_source(source_text, sample_name=''):
    """Categorize isolation source into broad categories

    NARMS sample naming convention from SampleName column:
    [Year][State][Number][ProductCode][Number]-[Organism]

    Product codes:
    - GB = Ground Beef
    - CB = Chicken/Poultry (Chicken Breast, legs, etc.)
    - GT = Ground Turkey
    - PC = Pork Products
    - CL = Chicken Liver
    - CG = Chicken Gizzards
    - CH = Chicken Hearts
    """
    import re

    # First try to extract product code from SampleName
    if sample_name:
        # Extract product code pattern (e.g., GB, CB, GT, PC, CL, CG, CH)
        # Pattern: digits followed by 2 capital letters followed by digits
        # Use findall to get all matches, then take the second one (first is state code)
        matches = re.findall(r'\d([A-Z]{2})\d', sample_name)
        if len(matches) >= 2:
            product_code = matches[1]  # Second match is the product code

            if product_code == 'GB':
                return 'Ground Beef'
            elif product_code == 'CB':
                return 'Chicken/Poultry'
            elif product_code == 'GT':
                return 'Ground Turkey'
            elif product_code == 'PC':
                return 'Pork Products'
            elif product_code == 'CL':
                return 'Chicken Liver'
            elif product_code == 'CG':
                return 'Chicken Gizzards'
            elif product_code == 'CH':
                return 'Chicken Hearts'

    # Fallback to text-based categorization
    source_lower = source_text.lower()

    if any(term in source_lower for term in ['clinical', 'patient', 'blood', 'urine', 'fecal', 'feces', 'stool']):
        return 'Clinical'
    elif any(term in source_lower for term in ['food', 'meat', 'poultry', 'beef', 'pork', 'chicken', 'turkey']):
        return 'Food'
    elif any(term in source_lower for term in ['environment', 'water', 'soil', 'sediment']):
        return 'Environmental'
    elif any(term in source_lower for term in ['animal', 'livestock', 'cattle', 'swine', 'farm']):
        return 'Animal'
    else:
        return 'Other'

# ============================================================================
# COMPREHENSIVE ANALYSIS
# ============================================================================

def run_comprehensive_analysis(results_dir):
    """Run all analyses and collect data"""
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"
    mlst_dir = results_dir / "mlst"
    metadata_file = results_dir / "filtered_samples" / "filtered_samples.csv"

    # Get metadata
    sample_metadata, organism_map = parse_metadata(metadata_file)

    # Data structures
    overall_stats = {
        'total_samples': 0,
        'samples_with_amr': 0,
        'samples_with_prophage': 0,
        'samples_with_colocation': 0,
        'total_amr_genes': 0,
        'amr_on_prophage': 0
    }

    # Co-location data
    colocation_data = {
        'amr_gene_locations': Counter(),
        'amr_classes_on_prophages': Counter(),
        'st_distribution': Counter(),
        'st_with_colocation': Counter(),
        'colocated_samples': []
    }

    # MDR islands
    mdr_islands = []
    drug_class_combinations = Counter()

    # Species comparison
    species_data = defaultdict(lambda: {
        'samples': 0,
        'samples_with_amr': 0,
        'samples_with_prophage': 0,
        'samples_with_colocation': 0,
        'total_amr_genes': 0,
        'amr_on_prophage': 0,
        'amr_genes': Counter(),
        'amr_classes': Counter(),
        'amr_genes_on_prophage': Counter(),
        'amr_classes_on_prophage': Counter()
    })

    # Temporal/source stratification
    temporal_data = defaultdict(lambda: {
        'samples': 0,
        'samples_with_colocation': 0,
        'total_amr': 0,
        'amr_on_prophage': 0,
        'top_genes_on_prophage': Counter()
    })

    source_data = defaultdict(lambda: {
        'samples': 0,
        'samples_with_colocation': 0,
        'total_amr': 0,
        'amr_on_prophage': 0,
        'top_genes_on_prophage': Counter()
    })

    # Prophage functional diversity
    prophage_functions = Counter()

    # Process all samples
    for amr_file in sorted(amr_dir.glob("*_amr.tsv")):
        sample_id = amr_file.stem.replace('_amr', '')

        # Get metadata
        meta = sample_metadata.get(sample_id, {})
        organism = meta.get('organism', 'Unknown')
        year = meta.get('year', 'Unknown')
        source_raw = meta.get('source', 'Unknown')
        sample_name = meta.get('sample_name', '')
        source_category = categorize_source(source_raw, sample_name)

        overall_stats['total_samples'] += 1

        # Parse data
        contig_amr = parse_amr_by_contig(amr_file)
        vibrant_phages_file = vibrant_dir / f"{sample_id}_phages.fna"
        prophage_contigs = parse_prophage_contigs(vibrant_phages_file)
        mlst_file = mlst_dir / f"{sample_id}_mlst.tsv"
        st = parse_mlst(mlst_file)

        # Parse prophage functional annotations
        vibrant_sample_dir = vibrant_dir / f"{sample_id}_vibrant"
        vibrant_annotations = vibrant_sample_dir / f"VIBRANT_{sample_id}_scaffolds" / f"VIBRANT_results_{sample_id}_scaffolds" / f"VIBRANT_annotations_{sample_id}_scaffolds.tsv"
        sample_prophage_functions = parse_prophage_functions(vibrant_annotations)
        prophage_functions.update(sample_prophage_functions)

        if st:
            colocation_data['st_distribution'][st] += 1

        # Track presence
        has_prophage = len(prophage_contigs) > 0
        has_amr = len(contig_amr) > 0
        has_colocation = False

        if has_prophage:
            overall_stats['samples_with_prophage'] += 1
            if organism != 'Unknown':
                species_data[organism]['samples_with_prophage'] += 1

        if organism != 'Unknown':
            species_data[organism]['samples'] += 1

        if year != 'Unknown':
            temporal_data[year]['samples'] += 1

        source_data[source_category]['samples'] += 1

        sample_amr_on_prophage = []
        sample_amr_on_other = []

        # Track MDR islands for this sample
        for contig, amr_genes in contig_amr.items():
            is_prophage = any(contig.startswith(pc) for pc in prophage_contigs)

            # MDR island detection
            if is_prophage:
                drug_classes = set(gene['class'] for gene in amr_genes)
                if len(drug_classes) >= 2:
                    contig_length = get_contig_length(contig)
                    combo = tuple(sorted(drug_classes))
                    drug_class_combinations[combo] += 1

                    mdr_islands.append({
                        'sample': sample_id,
                        'organism': organism,
                        'contig': contig,
                        'length': contig_length,
                        'num_amr_genes': len(amr_genes),
                        'num_drug_classes': len(drug_classes),
                        'drug_classes': drug_classes,
                        'amr_genes': amr_genes
                    })

            # Process each AMR gene
            for amr in amr_genes:
                gene = amr['gene']
                gene_class = amr['class']

                overall_stats['total_amr_genes'] += 1

                if organism != 'Unknown':
                    species_data[organism]['total_amr_genes'] += 1
                    species_data[organism]['amr_genes'][gene] += 1
                    species_data[organism]['amr_classes'][gene_class] += 1

                if year != 'Unknown':
                    temporal_data[year]['total_amr'] += 1

                source_data[source_category]['total_amr'] += 1

                if is_prophage:
                    has_colocation = True
                    overall_stats['amr_on_prophage'] += 1
                    colocation_data['amr_gene_locations'][f"{gene}_prophage"] += 1
                    colocation_data['amr_classes_on_prophages'][gene_class] += 1

                    if organism != 'Unknown':
                        species_data[organism]['amr_on_prophage'] += 1
                        species_data[organism]['amr_genes_on_prophage'][gene] += 1
                        species_data[organism]['amr_classes_on_prophage'][gene_class] += 1

                    if year != 'Unknown':
                        temporal_data[year]['amr_on_prophage'] += 1
                        temporal_data[year]['top_genes_on_prophage'][gene] += 1

                    source_data[source_category]['amr_on_prophage'] += 1
                    source_data[source_category]['top_genes_on_prophage'][gene] += 1

                    sample_amr_on_prophage.append({
                        'gene': gene,
                        'class': gene_class,
                        'contig': contig
                    })
                else:
                    colocation_data['amr_gene_locations'][f"{gene}_other"] += 1
                    sample_amr_on_other.append({
                        'gene': gene,
                        'class': gene_class,
                        'contig': contig
                    })

        if has_amr:
            overall_stats['samples_with_amr'] += 1
            if organism != 'Unknown':
                species_data[organism]['samples_with_amr'] += 1

        if has_colocation:
            overall_stats['samples_with_colocation'] += 1
            if st:
                colocation_data['st_with_colocation'][st] += 1
            if organism != 'Unknown':
                species_data[organism]['samples_with_colocation'] += 1
            if year != 'Unknown':
                temporal_data[year]['samples_with_colocation'] += 1
            source_data[source_category]['samples_with_colocation'] += 1

            colocation_data['colocated_samples'].append({
                'sample': sample_id,
                'st': st,
                'organism': organism,
                'amr_on_prophage': len(sample_amr_on_prophage),
                'amr_on_other': len(sample_amr_on_other),
                'prophage_amr_genes': sample_amr_on_prophage,
                'other_amr_genes': sample_amr_on_other
            })

    return {
        'overall': overall_stats,
        'colocation': colocation_data,
        'mdr_islands': mdr_islands,
        'drug_class_combinations': drug_class_combinations,
        'species': species_data,
        'temporal': temporal_data,
        'source': source_data,
        'prophage_functions': prophage_functions
    }

# ============================================================================
# TERMINAL OUTPUT
# ============================================================================

def print_comprehensive_report(data, results_dir):
    """Print comprehensive terminal report"""

    print("\n" + "="*85)
    print("COMPREHENSIVE AMR-PROPHAGE ANALYSIS REPORT")
    print(f"Results: {results_dir}")
    print("="*85)

    # Section 1: Overall Statistics
    print("\n" + "="*85)
    print("1. OVERALL STATISTICS")
    print("="*85)

    overall = data['overall']
    print(f"\n📊 Dataset Overview:")
    print(f"  Total samples analyzed: {overall['total_samples']}")
    print(f"  Samples with AMR genes: {overall['samples_with_amr']} ({overall['samples_with_amr']/overall['total_samples']*100:.1f}%)")
    print(f"  Samples with prophages: {overall['samples_with_prophage']} ({overall['samples_with_prophage']/overall['total_samples']*100:.1f}%)")
    print(f"  Samples with AMR-prophage co-location: {overall['samples_with_colocation']} ({overall['samples_with_colocation']/overall['total_samples']*100:.1f}%)")

    print(f"\n💊 AMR Gene Statistics:")
    print(f"  Total AMR genes detected: {overall['total_amr_genes']}")
    print(f"  AMR genes on PROPHAGE contigs: {overall['amr_on_prophage']} ({overall['amr_on_prophage']/overall['total_amr_genes']*100:.1f}%)")
    print(f"  AMR genes on NON-PROPHAGE contigs: {overall['total_amr_genes'] - overall['amr_on_prophage']} ({(overall['total_amr_genes'] - overall['amr_on_prophage'])/overall['total_amr_genes']*100:.1f}%)")

    # Section 2: Physical Co-location
    print("\n" + "="*85)
    print("2. PHYSICAL CO-LOCATION ANALYSIS")
    print("="*85)

    coloc = data['colocation']
    print(f"\n💊 Top 10 AMR Drug Classes on Prophage Contigs:")
    print(f"  {'Drug Class':<40} {'Count'}")
    print("  " + "-"*55)
    for drug_class, count in coloc['amr_classes_on_prophages'].most_common(10):
        print(f"  {drug_class:<40} {count}")

    print(f"\n🧬 Top 15 AMR Genes on Prophages:")
    print(f"  {'Gene':<25} {'On Prophage':<15} {'On Other':<15} {'% Prophage'}")
    print("  " + "-"*75)

    genes = set()
    for key in coloc['amr_gene_locations'].keys():
        gene = key.replace('_prophage', '').replace('_other', '')
        genes.add(gene)

    gene_data = []
    for gene in genes:
        prophage_count = coloc['amr_gene_locations'].get(f"{gene}_prophage", 0)
        other_count = coloc['amr_gene_locations'].get(f"{gene}_other", 0)
        total = prophage_count + other_count
        if total > 0:
            pct = (prophage_count / total) * 100
            gene_data.append((gene, prophage_count, other_count, pct))

    gene_data.sort(key=lambda x: x[1], reverse=True)
    for gene, prophage_count, other_count, pct in gene_data[:15]:
        print(f"  {gene:<25} {prophage_count:<15} {other_count:<15} {pct:>6.1f}%")

    # Section 3: MDR Islands
    print("\n" + "="*85)
    print("3. MULTI-DRUG RESISTANCE ISLANDS")
    print("="*85)

    print(f"\n🔥 MDR Islands Found: {len(data['mdr_islands'])}")
    print(f"   (Prophage contigs with AMR from ≥2 drug classes)")

    if data['mdr_islands']:
        # Group by organism
        islands_by_organism = defaultdict(list)
        for island in data['mdr_islands']:
            islands_by_organism[island['organism']].append(island)

        print(f"\n🦠 MDR Islands by Organism:")
        for organism, islands in sorted(islands_by_organism.items()):
            print(f"  {organism:<20} {len(islands)} MDR islands")

        print(f"\n💊 Top 10 Drug Class Combinations:")
        print(f"  {'Drug Classes':<60} {'Count'}")
        print("  " + "-"*70)
        for combo, count in data['drug_class_combinations'].most_common(10):
            classes_str = ', '.join(sorted(combo))[:55]
            print(f"  {classes_str:<60} {count}")

        print(f"\n🔥 Top 10 MDR Islands (by drug class diversity):")
        print(f"  {'Sample':<20} {'Organism':<15} {'Length':<12} {'Genes':<8} {'Classes'}")
        print("  " + "-"*75)

        sorted_islands = sorted(data['mdr_islands'],
                              key=lambda x: (x['num_drug_classes'], x['num_amr_genes']),
                              reverse=True)

        for island in sorted_islands[:10]:
            length_str = f"{island['length']/1000:.1f}kb" if island['length'] else "Unknown"
            classes_str = ', '.join(sorted(list(island['drug_classes']))[:2])
            if len(island['drug_classes']) > 2:
                classes_str += f", +{len(island['drug_classes'])-2}"

            print(f"  {island['sample']:<20} {island['organism']:<15} {length_str:<12} "
                  f"{island['num_amr_genes']:<8} {classes_str}")

    # Section 4: Species Comparison
    print("\n" + "="*85)
    print("4. SPECIES COMPARISON")
    print("="*85)

    print(f"\n📊 AMR-Prophage Statistics by Species:")
    print(f"  {'Species':<25} {'Samples':<10} {'AMR Total':<12} {'On Prophage':<15} {'% on Prophage'}")
    print("  " + "-"*75)

    for organism in sorted(data['species'].keys()):
        sp_data = data['species'][organism]
        pct = (sp_data['amr_on_prophage'] / sp_data['total_amr_genes'] * 100) if sp_data['total_amr_genes'] > 0 else 0
        print(f"  {organism:<25} {sp_data['samples']:<10} {sp_data['total_amr_genes']:<12} "
              f"{sp_data['amr_on_prophage']:<15} {pct:.1f}%")

    print(f"\n🧬 Top 5 AMR Genes per Species (on prophages):")
    for organism in sorted(data['species'].keys()):
        sp_data = data['species'][organism]
        if sp_data['samples'] < 5:
            continue
        print(f"\n  {organism}:")
        for gene, count in sp_data['amr_genes_on_prophage'].most_common(5):
            print(f"    {gene:<25} {count}")

    # Section 5: Temporal Trends
    print("\n" + "="*85)
    print("5. TEMPORAL TRENDS")
    print("="*85)

    print(f"\n📅 Year-by-Year Trends:")
    print(f"  {'Year':<8} {'Samples':<10} {'AMR Total':<12} {'On Prophage':<15} {'% on Prophage'}")
    print("  " + "-"*65)

    for year in sorted(data['temporal'].keys()):
        temp_data = data['temporal'][year]
        pct = (temp_data['amr_on_prophage'] / temp_data['total_amr'] * 100) if temp_data['total_amr'] > 0 else 0
        print(f"  {year:<8} {temp_data['samples']:<10} {temp_data['total_amr']:<12} "
              f"{temp_data['amr_on_prophage']:<15} {pct:.1f}%")

    # Section 6: Source Stratification
    print("\n" + "="*85)
    print("6. SOURCE STRATIFICATION")
    print("="*85)

    print(f"\n🏥 AMR-Prophage by Isolation Source:")
    print(f"  {'Source':<20} {'Samples':<10} {'AMR Total':<12} {'On Prophage':<15} {'% on Prophage'}")
    print("  " + "-"*70)

    for source in sorted(data['source'].keys()):
        src_data = data['source'][source]
        pct = (src_data['amr_on_prophage'] / src_data['total_amr'] * 100) if src_data['total_amr'] > 0 else 0
        print(f"  {source:<20} {src_data['samples']:<10} {src_data['total_amr']:<12} "
              f"{src_data['amr_on_prophage']:<15} {pct:.1f}%")

    print("\n" + "="*85)
    print("✅ Analysis complete!")
    print("="*85 + "\n")

# ============================================================================
# HTML DASHBOARD GENERATION
# ============================================================================

def generate_html_dashboard(data, results_dir, output_file):
    """Generate comprehensive interactive HTML dashboard"""

    overall = data['overall']

    # Prepare data for charts
    # Temporal trend - two percentage lines
    years = sorted(data['temporal'].keys())
    temporal_pct_samples = [(data['temporal'][y]['samples_with_colocation'] / data['temporal'][y]['samples'] * 100)
                            if data['temporal'][y]['samples'] > 0 else 0 for y in years]
    temporal_pct_genes = [(data['temporal'][y]['amr_on_prophage'] / data['temporal'][y]['total_amr'] * 100)
                          if data['temporal'][y]['total_amr'] > 0 else 0 for y in years]

    # Species comparison
    species_names = sorted(data['species'].keys())
    species_samples = [data['species'][s]['samples'] for s in species_names]
    species_coloc = [data['species'][s]['samples_with_colocation'] for s in species_names]

    # Top genes on prophages
    genes = set()
    for key in data['colocation']['amr_gene_locations'].keys():
        gene = key.replace('_prophage', '').replace('_other', '')
        genes.add(gene)

    gene_prophage_counts = []
    for gene in genes:
        count = data['colocation']['amr_gene_locations'].get(f"{gene}_prophage", 0)
        if count > 0:
            gene_prophage_counts.append((gene, count))

    gene_prophage_counts.sort(key=lambda x: x[1], reverse=True)
    top_genes = [g[0] for g in gene_prophage_counts[:15]]
    top_gene_counts = [g[1] for g in gene_prophage_counts[:15]]

    # Gene data for table (prophage vs non-prophage)
    gene_data = []
    for gene in genes:
        prophage_count = data['colocation']['amr_gene_locations'].get(f"{gene}_prophage", 0)
        other_count = data['colocation']['amr_gene_locations'].get(f"{gene}_other", 0)
        total = prophage_count + other_count
        if total > 0:
            pct = (prophage_count / total) * 100
            gene_data.append((gene, prophage_count, other_count, pct))
    gene_data.sort(key=lambda x: x[1], reverse=True)

    # MDR islands by organism
    mdr_by_organism = defaultdict(int)
    for island in data['mdr_islands']:
        mdr_by_organism[island['organism']] += 1

    mdr_organisms = sorted(mdr_by_organism.keys())
    mdr_counts = [mdr_by_organism[org] for org in mdr_organisms]

    # Prophage functional diversity
    function_categories = sorted(data['prophage_functions'].keys())
    function_counts = [data['prophage_functions'][cat] for cat in function_categories]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive AMR-Prophage Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .header h1 {{
            color: #2d3748;
            font-size: 2.8rem;
            margin-bottom: 10px;
        }}

        .header p {{
            color: #718096;
            font-size: 1.2rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-value {{
            font-size: 3rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .stat-label {{
            color: #718096;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}

        .section h2 {{
            color: #2d3748;
            margin-bottom: 25px;
            font-size: 1.8rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }}

        .two-col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}

        .three-col {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }}

        tr:hover {{
            background: #f7fafc;
        }}

        .highlight {{
            background: #fef3c7;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }}

        .badge-success {{
            background: #d1fae5;
            color: #065f46;
        }}

        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge-info {{
            background: #dbeafe;
            color: #1e40af;
        }}

        @media (max-width: 768px) {{
            .two-col, .three-col {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 Comprehensive AMR-Prophage Analysis</h1>
            <p>Complete analysis of antimicrobial resistance genes and prophage associations</p>
            <p style="margin-top: 10px;"><strong>Dataset:</strong> {results_dir}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{overall['total_samples']}</div>
                <div class="stat-label">Total Samples</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{overall['samples_with_colocation']}</div>
                <div class="stat-label">Samples with Co-location</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{overall['total_amr_genes']}</div>
                <div class="stat-label">Total AMR Genes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{overall['amr_on_prophage']}</div>
                <div class="stat-label">AMR on Prophages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(data['mdr_islands'])}</div>
                <div class="stat-label">MDR Islands Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{overall['amr_on_prophage']/overall['total_amr_genes']*100:.1f}%</div>
                <div class="stat-label">% AMR on Prophages</div>
            </div>
        </div>

        <div class="section">
            <h2>📅 AMR-Prophage Co-location by Year</h2>
            <div class="chart-wrapper">
                <canvas id="temporalChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2>🦠 Prophage Functional Diversity</h2>
            <div class="chart-wrapper">
                <canvas id="prophageFunctionsChart"></canvas>
            </div>
        </div>

        <div class="two-col">
            <div class="section">
                <h2>🦠 Species Comparison</h2>
                <div class="chart-wrapper">
                    <canvas id="speciesChart"></canvas>
                </div>
            </div>

            <div class="section">
                <h2>🧬 Top AMR Genes on Prophages</h2>
                <div class="chart-wrapper">
                    <canvas id="topGenesChart"></canvas>
                </div>
            </div>
        </div>

        <div class="two-col">
            <div class="section">
                <h2>🔥 MDR Islands by Organism</h2>
                <div class="chart-wrapper">
                    <canvas id="mdrChart"></canvas>
                </div>
            </div>

            <div class="section">
                <h2>🏥 Source Stratification</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Source</th>
                            <th>Samples</th>
                            <th>% with Co-location</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for source in sorted(data['source'].keys()):
        src_data = data['source'][source]
        pct = (src_data['samples_with_colocation'] / src_data['samples'] * 100) if src_data['samples'] > 0 else 0
        html_content += f"""
                        <tr>
                            <td><strong>{source}</strong></td>
                            <td>{src_data['samples']}</td>
                            <td><span class="highlight">{pct:.1f}%</span></td>
                        </tr>
"""

    html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <h2>💊 Top Drug Class Combinations in MDR Islands</h2>
            <table>
                <thead>
                    <tr>
                        <th>Drug Classes</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
"""

    for combo, count in data['drug_class_combinations'].most_common(10):
        classes_str = ', '.join(sorted(combo))
        html_content += f"""
                    <tr>
                        <td>{classes_str}</td>
                        <td><span class="badge badge-warning">{count}</span></td>
                    </tr>
"""

    html_content += f"""
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>🔍 Top AMR Genes: Prophage vs Non-Prophage</h2>
            <table>
                <thead>
                    <tr>
                        <th>Gene</th>
                        <th>On Prophage</th>
                        <th>On Other</th>
                        <th>% Prophage</th>
                    </tr>
                </thead>
                <tbody>
"""

    for gene, prophage_count, other_count, pct in gene_data[:20]:
        badge_class = "badge-success" if pct > 50 else "badge-info"
        html_content += f"""
                    <tr>
                        <td><strong>{gene}</strong></td>
                        <td>{prophage_count}</td>
                        <td>{other_count}</td>
                        <td><span class="badge {badge_class}">{pct:.1f}%</span></td>
                    </tr>
"""

    html_content += f"""
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Temporal trend chart - AMR-Prophage Co-location by Year
        const temporalCtx = document.getElementById('temporalChart').getContext('2d');
        new Chart(temporalCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(years)},
                datasets: [
                    {{
                        label: '% Samples with Prophage-AMR',
                        data: {json.dumps(temporal_pct_samples)},
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }},
                    {{
                        label: '% AMR Genes on Prophages',
                        data: {json.dumps(temporal_pct_genes)},
                        borderColor: '#f56565',
                        backgroundColor: 'rgba(245, 101, 101, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false,
                }},
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    title: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Percentage (%)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Species comparison chart
        const speciesCtx = document.getElementById('speciesChart').getContext('2d');
        new Chart(speciesCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(species_names)},
                datasets: [
                    {{
                        label: 'Total Samples',
                        data: {json.dumps(species_samples)},
                        backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    }},
                    {{
                        label: 'With Co-location',
                        data: {json.dumps(species_coloc)},
                        backgroundColor: 'rgba(245, 101, 101, 0.6)',
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Top genes chart
        const genesCtx = document.getElementById('topGenesChart').getContext('2d');
        new Chart(genesCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_genes)},
                datasets: [{{
                    label: 'Count on Prophages',
                    data: {json.dumps(top_gene_counts)},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // MDR islands chart
        const mdrCtx = document.getElementById('mdrChart').getContext('2d');
        new Chart(mdrCtx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(mdr_organisms)},
                datasets: [{{
                    data: {json.dumps(mdr_counts)},
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(245, 101, 101, 0.8)',
                        'rgba(72, 187, 120, 0.8)',
                        'rgba(246, 173, 85, 0.8)',
                    ],
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                    }}
                }}
            }}
        }});

        // Prophage functional diversity chart
        const prophageFunctionsCtx = document.getElementById('prophageFunctionsChart').getContext('2d');
        new Chart(prophageFunctionsCtx, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(function_categories)},
                datasets: [{{
                    data: {json.dumps(function_counts)},
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(245, 101, 101, 0.8)',
                        'rgba(72, 187, 120, 0.8)',
                        'rgba(246, 173, 85, 0.8)',
                        'rgba(237, 100, 166, 0.8)',
                        'rgba(155, 81, 224, 0.8)',
                        'rgba(52, 211, 153, 0.8)',
                        'rgba(251, 146, 60, 0.8)',
                        'rgba(96, 165, 250, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(147, 197, 253, 0.8)',
                    ],
                    borderColor: 'white',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            boxWidth: 15,
                            padding: 10
                        }}
                    }},
                    title: {{
                        display: false
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html_content)

# ============================================================================
# MAIN
# ============================================================================

def find_year_directories(base_dir):
    """Find all results directories matching year patterns (2021-2025)"""
    import re
    base_dir = Path(base_dir)
    year_dirs = []

    if base_dir.is_dir():
        for item in base_dir.iterdir():
            if item.is_dir():
                # Check if directory name contains a year between 2021-2025
                match = re.search(r'(2021|2022|2023|2024|2025)', item.name)
                if match:
                    # Verify it has the expected structure
                    if (item / "amrfinder").exists() and (item / "vibrant").exists():
                        year_dirs.append(item)

    return year_dirs

def merge_analysis_data(all_data_list):
    """Merge data from multiple directories into one combined dataset"""
    from collections import defaultdict, Counter

    merged = {
        'overall': {
            'total_samples': 0,
            'samples_with_amr': 0,
            'samples_with_prophage': 0,
            'samples_with_colocation': 0,
            'total_amr_genes': 0,
            'amr_on_prophage': 0
        },
        'colocation': {
            'amr_gene_locations': Counter(),
            'amr_classes_on_prophages': Counter(),
            'st_distribution': Counter(),
            'st_with_colocation': Counter(),
            'colocated_samples': []
        },
        'mdr_islands': [],
        'drug_class_combinations': Counter(),
        'species': defaultdict(lambda: {
            'samples': 0,
            'samples_with_amr': 0,
            'samples_with_prophage': 0,
            'samples_with_colocation': 0,
            'total_amr_genes': 0,
            'amr_on_prophage': 0,
            'amr_genes': Counter(),
            'amr_classes': Counter(),
            'amr_genes_on_prophage': Counter(),
            'amr_classes_on_prophage': Counter()
        }),
        'temporal': defaultdict(lambda: {
            'samples': 0,
            'samples_with_colocation': 0,
            'total_amr': 0,
            'amr_on_prophage': 0,
            'top_genes_on_prophage': Counter()
        }),
        'source': defaultdict(lambda: {
            'samples': 0,
            'samples_with_colocation': 0,
            'total_amr': 0,
            'amr_on_prophage': 0,
            'top_genes_on_prophage': Counter()
        }),
        'prophage_functions': Counter()
    }

    for data in all_data_list:
        # Merge overall stats
        for key in merged['overall']:
            merged['overall'][key] += data['overall'][key]

        # Merge colocation data
        merged['colocation']['amr_gene_locations'].update(data['colocation']['amr_gene_locations'])
        merged['colocation']['amr_classes_on_prophages'].update(data['colocation']['amr_classes_on_prophages'])
        merged['colocation']['st_distribution'].update(data['colocation']['st_distribution'])
        merged['colocation']['st_with_colocation'].update(data['colocation']['st_with_colocation'])
        merged['colocation']['colocated_samples'].extend(data['colocation']['colocated_samples'])

        # Merge MDR islands
        merged['mdr_islands'].extend(data['mdr_islands'])
        merged['drug_class_combinations'].update(data['drug_class_combinations'])

        # Merge species data
        for organism, sp_data in data['species'].items():
            for key in ['samples', 'samples_with_amr', 'samples_with_prophage', 'samples_with_colocation', 'total_amr_genes', 'amr_on_prophage']:
                merged['species'][organism][key] += sp_data[key]
            merged['species'][organism]['amr_genes'].update(sp_data['amr_genes'])
            merged['species'][organism]['amr_classes'].update(sp_data['amr_classes'])
            merged['species'][organism]['amr_genes_on_prophage'].update(sp_data['amr_genes_on_prophage'])
            merged['species'][organism]['amr_classes_on_prophage'].update(sp_data['amr_classes_on_prophage'])

        # Merge temporal data
        for year, temp_data in data['temporal'].items():
            for key in ['samples', 'samples_with_colocation', 'total_amr', 'amr_on_prophage']:
                merged['temporal'][year][key] += temp_data[key]
            merged['temporal'][year]['top_genes_on_prophage'].update(temp_data['top_genes_on_prophage'])

        # Merge source data
        for source, src_data in data['source'].items():
            for key in ['samples', 'samples_with_colocation', 'total_amr', 'amr_on_prophage']:
                merged['source'][source][key] += src_data[key]
            merged['source'][source]['top_genes_on_prophage'].update(src_data['top_genes_on_prophage'])

        # Merge prophage functions
        merged['prophage_functions'].update(data['prophage_functions'])

    return merged

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 comprehensive_amr_prophage_analysis.py <results_dir_or_parent> [output_html]")
        print("\nExamples:")
        print("  # Single year:")
        print("  python3 comprehensive_amr_prophage_analysis.py /homes/tylerdoe/compass_kansas_results/results_kansas_2024")
        print()
        print("  # All years (auto-detect 2021-2025 subdirectories):")
        print("  python3 comprehensive_amr_prophage_analysis.py /homes/tylerdoe/compass_kansas_results")
        sys.exit(1)

    results_path = Path(sys.argv[1])
    output_html = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "comprehensive_amr_prophage_dashboard.html"

    if not results_path.exists():
        print(f"❌ Error: Path not found: {results_path}")
        sys.exit(1)

    # Check if this is a single results directory or a parent containing multiple years
    is_single_dir = (results_path / "amrfinder").exists() and (results_path / "vibrant").exists()

    if is_single_dir:
        # Single directory mode
        print(f"\n🔬 Running comprehensive AMR-prophage analysis...")
        print(f"   Results directory: {results_path}")

        data = run_comprehensive_analysis(results_path)

        if data['overall']['total_samples'] == 0:
            print("❌ No samples found!")
            sys.exit(1)

        print_comprehensive_report(data, results_path)

        print(f"\n📊 Generating HTML dashboard...")
        generate_html_dashboard(data, results_path, output_html)

        print(f"\n✅ HTML dashboard created: {output_html}")
        print(f"   Open in browser: file://{output_html.absolute()}\n")

    else:
        # Multi-directory mode - search for year directories
        print(f"\n🔍 Searching for year directories in: {results_path}")
        year_dirs = find_year_directories(results_path)

        if not year_dirs:
            print("❌ No year directories found and not a valid single results directory!")
            print("   Looking for subdirectories with 'amrfinder' and 'vibrant' folders")
            sys.exit(1)

        print(f"\n✅ Found {len(year_dirs)} year directories:")
        for d in sorted(year_dirs):
            print(f"   - {d.name}")

        print(f"\n🔬 Processing all directories...")

        all_data = []
        for directory in sorted(year_dirs):
            print(f"\n   Processing {directory.name}...")
            try:
                data = run_comprehensive_analysis(directory)
                if data['overall']['total_samples'] > 0:
                    all_data.append(data)
                    print(f"   ✅ {directory.name}: {data['overall']['total_samples']} samples, "
                          f"{data['overall']['total_amr_genes']} AMR genes, "
                          f"{len(data['mdr_islands'])} MDR islands")
                else:
                    print(f"   ⚠️  {directory.name}: No samples found")
            except Exception as e:
                print(f"   ❌ {directory.name}: Error - {e}")

        if not all_data:
            print("\n❌ No data collected from any directory!")
            sys.exit(1)

        # Merge all data
        print(f"\n🔄 Merging data from {len(all_data)} directories...")
        merged_data = merge_analysis_data(all_data)

        # Print combined report
        print_comprehensive_report(merged_data, f"{results_path} (2021-2025)")

        # Generate HTML dashboard
        print(f"\n📊 Generating HTML dashboard...")
        generate_html_dashboard(merged_data, f"{results_path} (All Years)", output_html)

        print(f"\n✅ HTML dashboard created: {output_html}")
        print(f"   Open in browser: file://{output_html.absolute()}\n")

if __name__ == "__main__":
    main()
