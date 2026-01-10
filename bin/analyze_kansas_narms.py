#!/usr/bin/env python3
"""
Kansas NARMS Comprehensive Analysis Script
==========================================

Performs publication-worthy analyses on Kansas NARMS 2021-2025 data including:
1. Phage phylogeny and evolution
2. Temporal AMR trends
3. Phage-AMR-plasmid correlations
4. Geographic and host patterns
5. Comparative genomics

Usage:
    # Run all analyses
    ./bin/analyze_kansas_narms.py --all --compass-results /path/to/results --outdir analysis_output/

    # Run specific analysis
    ./bin/analyze_kansas_narms.py --phage --compass-results /path/to/results --outdir analysis_output/

    # Multiple analyses
    ./bin/analyze_kansas_narms.py --amr --correlations --compass-results /path/to/results --outdir analysis_output/

Author: Tyler Doerksen & Claude
Date: January 2026
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Data manipulation
import pandas as pd
import numpy as np

# Visualization
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    print("Warning: seaborn not available. Using matplotlib defaults.")

# Statistics
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

# Optional dependencies (check availability)
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not available. Some interactive plots will be skipped.")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("Warning: networkx not available. Network analysis will be skipped.")

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. PCA analysis will be skipped.")

try:
    from Bio import SeqIO, AlignIO, Phylo
    from Bio.Seq import Seq
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    print("Warning: Biopython not available. Phylogeny features will be limited.")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA LOADING MODULE
# ============================================================================

class DataLoader:
    """Load and preprocess COMPASS pipeline results"""

    def __init__(self, compass_results_dir: Path):
        self.results_dir = Path(compass_results_dir)
        self.summary_file = self.results_dir / "summary" / "compass_summary.tsv"

    def load_compass_summary(self) -> pd.DataFrame:
        """Load the main COMPASS summary TSV with all results"""
        logger.info("Loading COMPASS summary data...")

        if not self.summary_file.exists():
            raise FileNotFoundError(f"COMPASS summary not found: {self.summary_file}")

        df = pd.read_csv(self.summary_file, sep='\t')
        logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")

        # Add year column if not present (extract from releasedate or other date fields)
        if 'Year' not in df.columns and 'releasedate' in df.columns:
            df['Year'] = pd.to_datetime(df['releasedate'], errors='coerce').dt.year

        return df

    def load_vibrant_results(self) -> Dict[str, pd.DataFrame]:
        """Load VIBRANT prophage detection results for each sample"""
        logger.info("Loading VIBRANT prophage results...")

        vibrant_dir = self.results_dir / "vibrant"
        if not vibrant_dir.exists():
            logger.warning(f"VIBRANT directory not found: {vibrant_dir}")
            return {}

        results = {}
        for sample_dir in vibrant_dir.glob("*_vibrant"):
            sample_id = sample_dir.name.replace("_vibrant", "")

            # Load phage predictions table
            predictions_file = sample_dir / "VIBRANT_phages_{}/VIBRANT_results_{}/VIBRANT_genome_quality_{}.tsv".format(
                sample_id, sample_id, sample_id
            )

            if predictions_file.exists():
                results[sample_id] = pd.read_csv(predictions_file, sep='\t')

        logger.info(f"Loaded VIBRANT results for {len(results)} samples")
        return results

    def load_amr_results(self) -> Dict[str, pd.DataFrame]:
        """Load AMRFinder+ results for each sample"""
        logger.info("Loading AMRFinder+ results...")

        amr_dir = self.results_dir / "amrfinder"
        if not amr_dir.exists():
            logger.warning(f"AMRFinder directory not found: {amr_dir}")
            return {}

        results = {}
        for amr_file in amr_dir.glob("*_amr.tsv"):
            sample_id = amr_file.stem.replace("_amr", "")
            results[sample_id] = pd.read_csv(amr_file, sep='\t')

        logger.info(f"Loaded AMR results for {len(results)} samples")
        return results

    def load_mobsuite_results(self) -> Dict[str, pd.DataFrame]:
        """Load MOB-suite plasmid analysis results"""
        logger.info("Loading MOB-suite plasmid results...")

        mob_dir = self.results_dir / "mobsuite"
        if not mob_dir.exists():
            logger.warning(f"MOB-suite directory not found: {mob_dir}")
            return {}

        results = {}
        for sample_dir in mob_dir.glob("*_mobsuite"):
            sample_id = sample_dir.name.replace("_mobsuite", "")

            mobtyper_file = sample_dir / "mobtyper_results.txt"
            if mobtyper_file.exists():
                results[sample_id] = pd.read_csv(mobtyper_file, sep='\t')

        logger.info(f"Loaded MOB-suite results for {len(results)} samples")
        return results


# ============================================================================
# ANALYSIS MODULE 1: PHAGE PHYLOGENY & EVOLUTION
# ============================================================================

class PhageAnalyzer:
    """Analyze prophage phylogeny and temporal evolution"""

    def __init__(self, df: pd.DataFrame, vibrant_results: Dict, output_dir: Path):
        self.df = df
        self.vibrant_results = vibrant_results
        self.output_dir = output_dir / "phage_phylogeny"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self):
        """Run all phage analyses"""
        logger.info("="*70)
        logger.info("ANALYSIS 1: PHAGE PHYLOGENY & EVOLUTION")
        logger.info("="*70)

        # Extract prophage statistics from COMPASS summary
        phage_stats = self.extract_phage_statistics()

        # Temporal trends
        self.plot_temporal_phage_diversity(phage_stats)

        # Phage quality distribution
        self.plot_phage_quality_distribution(phage_stats)

        # Organism-specific patterns
        self.plot_phage_by_organism(phage_stats)

        # Export data
        phage_stats.to_csv(self.output_dir / "phage_statistics.csv", index=False)

        logger.info(f"Phage analysis complete. Results in: {self.output_dir}")

    def extract_phage_statistics(self) -> pd.DataFrame:
        """Extract prophage statistics from COMPASS summary"""
        logger.info("Extracting prophage statistics...")

        # Get phage-related columns from summary
        phage_cols = [col for col in self.df.columns if 'phage' in col.lower() or 'vibrant' in col.lower()]

        stats_df = self.df[['sample_id', 'organism', 'Year'] + phage_cols].copy()

        # Parse num_phages if exists
        if 'num_phages' in stats_df.columns:
            stats_df['num_phages'] = pd.to_numeric(stats_df['num_phages'], errors='coerce').fillna(0)

        return stats_df

    def plot_temporal_phage_diversity(self, phage_stats: pd.DataFrame):
        """Plot prophage counts over time"""
        logger.info("Plotting temporal phage diversity...")

        if 'Year' not in phage_stats.columns or 'num_phages' not in phage_stats.columns:
            logger.warning("Missing Year or num_phages column. Skipping temporal plot.")
            return

        # Group by year and organism
        temporal = phage_stats.groupby(['Year', 'organism'])['num_phages'].agg(['mean', 'std', 'count']).reset_index()

        fig, ax = plt.subplots(figsize=(12, 6))

        for organism in temporal['organism'].unique():
            org_data = temporal[temporal['organism'] == organism]
            ax.plot(org_data['Year'], org_data['mean'], marker='o', label=organism, linewidth=2)
            ax.fill_between(org_data['Year'],
                           org_data['mean'] - org_data['std'],
                           org_data['mean'] + org_data['std'],
                           alpha=0.2)

        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Average Number of Prophages', fontsize=12)
        ax.set_title('Temporal Trend in Prophage Abundance (Kansas NARMS 2021-2025)', fontsize=14, fontweight='bold')
        ax.legend(title='Organism')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / "temporal_phage_diversity.png", dpi=300, bbox_inches='tight')
        plt.close()

        logger.info("✓ Temporal diversity plot saved")

    def plot_phage_quality_distribution(self, phage_stats: pd.DataFrame):
        """Plot distribution of prophage quality scores"""
        logger.info("Plotting phage quality distribution...")

        # Look for quality-related columns
        quality_cols = [col for col in phage_stats.columns if 'quality' in col.lower()]

        if not quality_cols:
            logger.warning("No quality columns found. Skipping quality plot.")
            return

        fig, axes = plt.subplots(1, len(quality_cols), figsize=(6*len(quality_cols), 5))
        if len(quality_cols) == 1:
            axes = [axes]

        for idx, col in enumerate(quality_cols):
            quality_data = phage_stats[col].value_counts()
            axes[idx].bar(quality_data.index, quality_data.values, color='steelblue', alpha=0.7)
            axes[idx].set_xlabel('Quality Category', fontsize=12)
            axes[idx].set_ylabel('Number of Prophages', fontsize=12)
            axes[idx].set_title(f'{col.replace("_", " ").title()}', fontsize=12, fontweight='bold')
            axes[idx].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(self.output_dir / "phage_quality_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()

        logger.info("✓ Quality distribution plot saved")

    def plot_phage_by_organism(self, phage_stats: pd.DataFrame):
        """Plot prophage distribution by organism"""
        logger.info("Plotting phage distribution by organism...")

        if 'num_phages' not in phage_stats.columns or 'organism' not in phage_stats.columns:
            logger.warning("Missing required columns. Skipping organism plot.")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        organism_data = phage_stats.groupby('organism')['num_phages'].apply(list)

        ax.boxplot(organism_data.values, labels=organism_data.index, patch_artist=True)
        ax.set_xlabel('Organism', fontsize=12)
        ax.set_ylabel('Number of Prophages', fontsize=12)
        ax.set_title('Prophage Distribution by Organism', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(self.output_dir / "phage_by_organism.png", dpi=300, bbox_inches='tight')
        plt.close()

        logger.info("✓ Organism distribution plot saved")


# ============================================================================
# ANALYSIS MODULE 2: TEMPORAL AMR TRENDS
# ============================================================================

class AMRAnalyzer:
    """Analyze antimicrobial resistance trends over time"""

    def __init__(self, df: pd.DataFrame, amr_results: Dict, output_dir: Path):
        self.df = df
        self.amr_results = amr_results
        self.output_dir = output_dir / "temporal_amr"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self):
        """Run all AMR temporal analyses"""
        logger.info("="*70)
        logger.info("ANALYSIS 2: TEMPORAL AMR TRENDS")
        logger.info("="*70)

        # Aggregate AMR genes across samples
        amr_matrix = self.build_amr_gene_matrix()

        # Plot temporal trends
        self.plot_amr_prevalence_over_time(amr_matrix)

        # Plot resistance class trends
        self.plot_resistance_class_trends(amr_matrix)

        # MDR trends
        self.plot_mdr_trends()

        # Export data
        amr_matrix.to_csv(self.output_dir / "amr_gene_matrix.csv")

        logger.info(f"AMR analysis complete. Results in: {self.output_dir}")

    def build_amr_gene_matrix(self) -> pd.DataFrame:
        """Build matrix of AMR gene presence/absence by sample"""
        logger.info("Building AMR gene presence/absence matrix...")

        # Extract all unique AMR genes
        all_genes = set()
        for sample_id, amr_df in self.amr_results.items():
            if 'Gene symbol' in amr_df.columns:
                all_genes.update(amr_df['Gene symbol'].unique())

        # Build matrix
        matrix_data = []
        for sample_id in self.df['sample_id']:
            row = {'sample_id': sample_id}

            if sample_id in self.amr_results:
                amr_df = self.amr_results[sample_id]
                if 'Gene symbol' in amr_df.columns:
                    present_genes = set(amr_df['Gene symbol'].unique())
                    for gene in all_genes:
                        row[gene] = 1 if gene in present_genes else 0
                else:
                    for gene in all_genes:
                        row[gene] = 0
            else:
                for gene in all_genes:
                    row[gene] = 0

            matrix_data.append(row)

        matrix_df = pd.DataFrame(matrix_data)

        # Merge with metadata
        matrix_df = matrix_df.merge(self.df[['sample_id', 'organism', 'Year']], on='sample_id', how='left')

        logger.info(f"AMR matrix: {len(matrix_df)} samples x {len(all_genes)} genes")
        return matrix_df

    def plot_amr_prevalence_over_time(self, amr_matrix: pd.DataFrame):
        """Plot prevalence of top AMR genes over time"""
        logger.info("Plotting AMR gene prevalence trends...")

        if 'Year' not in amr_matrix.columns:
            logger.warning("No Year column found. Skipping temporal AMR plot.")
            return

        # Get top 10 most prevalent genes
        gene_cols = [col for col in amr_matrix.columns if col not in ['sample_id', 'organism', 'Year']]
        gene_prevalence = amr_matrix[gene_cols].sum().sort_values(ascending=False)
        top_genes = gene_prevalence.head(10).index.tolist()

        # Calculate prevalence by year
        fig, ax = plt.subplots(figsize=(14, 8))

        for gene in top_genes:
            yearly_prev = amr_matrix.groupby('Year')[gene].mean() * 100
            ax.plot(yearly_prev.index, yearly_prev.values, marker='o', label=gene, linewidth=2)

        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Prevalence (%)', fontsize=12)
        ax.set_title('Temporal Trends in Top 10 AMR Genes (Kansas NARMS 2021-2025)',
                    fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / "amr_prevalence_trends.png", dpi=300, bbox_inches='tight')
        plt.close()

        logger.info("✓ AMR prevalence plot saved")

    def plot_resistance_class_trends(self, amr_matrix: pd.DataFrame):
        """Plot trends by antibiotic class"""
        logger.info("Plotting resistance class trends...")

        # This would require AMRFinder class annotations
        # For now, create a placeholder
        logger.info("Resistance class analysis requires detailed AMR annotations")

    def plot_mdr_trends(self):
        """Plot multi-drug resistance trends over time"""
        logger.info("Plotting MDR trends...")

        if 'mdr_status' not in self.df.columns or 'Year' not in self.df.columns:
            logger.warning("Missing MDR or Year data. Skipping MDR plot.")
            return

        mdr_by_year = self.df.groupby(['Year', 'organism'])['mdr_status'].apply(
            lambda x: (x == 'MDR').sum() / len(x) * 100
        ).reset_index(name='mdr_percentage')

        fig, ax = plt.subplots(figsize=(12, 6))

        for organism in mdr_by_year['organism'].unique():
            org_data = mdr_by_year[mdr_by_year['organism'] == organism]
            ax.plot(org_data['Year'], org_data['mdr_percentage'],
                   marker='o', label=organism, linewidth=2)

        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('MDR Percentage (%)', fontsize=12)
        ax.set_title('Multi-Drug Resistance Trends (Kansas NARMS 2021-2025)',
                    fontsize=14, fontweight='bold')
        ax.legend(title='Organism')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / "mdr_trends.png", dpi=300, bbox_inches='tight')
        plt.close()

        logger.info("✓ MDR trends plot saved")


# ============================================================================
# ANALYSIS MODULE 3: PHAGE-AMR CORRELATIONS
# ============================================================================

class CorrelationAnalyzer:
    """Analyze correlations between prophages, AMR genes, and plasmids"""

    def __init__(self, df: pd.DataFrame, vibrant_results: Dict, amr_results: Dict,
                 mob_results: Dict, output_dir: Path):
        self.df = df
        self.vibrant_results = vibrant_results
        self.amr_results = amr_results
        self.mob_results = mob_results
        self.output_dir = output_dir / "correlations"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self):
        """Run all correlation analyses"""
        logger.info("="*70)
        logger.info("ANALYSIS 3: PHAGE-AMR-PLASMID CORRELATIONS")
        logger.info("="*70)

        # Build combined feature matrix
        feature_matrix = self.build_feature_matrix()

        # Correlation heatmap
        self.plot_correlation_heatmap(feature_matrix)

        # Co-occurrence analysis
        self.analyze_cooccurrence(feature_matrix)

        # Network analysis if available
        if NETWORKX_AVAILABLE:
            self.plot_feature_network(feature_matrix)

        # Export data
        feature_matrix.to_csv(self.output_dir / "feature_matrix.csv")

        logger.info(f"Correlation analysis complete. Results in: {self.output_dir}")

    def build_feature_matrix(self) -> pd.DataFrame:
        """Build combined matrix of phages, AMR genes, and plasmids"""
        logger.info("Building combined feature matrix...")

        # Start with sample IDs
        matrix = self.df[['sample_id', 'organism']].copy()

        # Add phage counts
        if 'num_phages' in self.df.columns:
            matrix['has_prophages'] = (self.df['num_phages'] > 0).astype(int)

        # Add AMR gene counts
        if 'num_amr_genes' in self.df.columns:
            matrix['num_amr_genes'] = self.df['num_amr_genes']

        # Add plasmid presence
        if 'num_plasmids' in self.df.columns:
            matrix['has_plasmids'] = (self.df['num_plasmids'] > 0).astype(int)

        # Add MDR status
        if 'mdr_status' in self.df.columns:
            matrix['is_mdr'] = (self.df['mdr_status'] == 'MDR').astype(int)

        logger.info(f"Feature matrix: {len(matrix)} samples x {len(matrix.columns)} features")
        return matrix

    def plot_correlation_heatmap(self, feature_matrix: pd.DataFrame):
        """Plot correlation heatmap of features"""
        logger.info("Plotting correlation heatmap...")

        # Select numeric columns
        numeric_cols = feature_matrix.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col != 'sample_id']

        if len(numeric_cols) < 2:
            logger.warning("Not enough numeric features for correlation. Skipping heatmap.")
            return

        # Calculate correlations
        corr_matrix = feature_matrix[numeric_cols].corr()

        # Plot heatmap
        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')

        # Set ticks
        ax.set_xticks(np.arange(len(numeric_cols)))
        ax.set_yticks(np.arange(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
        ax.set_yticklabels(numeric_cols)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Correlation Coefficient', fontsize=12)

        # Add correlation values
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=8)

        ax.set_title('Feature Correlation Heatmap', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(self.output_dir / "correlation_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()

        logger.info("✓ Correlation heatmap saved")

    def analyze_cooccurrence(self, feature_matrix: pd.DataFrame):
        """Analyze co-occurrence patterns"""
        logger.info("Analyzing feature co-occurrence...")

        # Calculate co-occurrence statistics
        cooccur_data = []

        if 'has_prophages' in feature_matrix.columns and 'is_mdr' in feature_matrix.columns:
            # Prophages + MDR
            both = ((feature_matrix['has_prophages'] == 1) & (feature_matrix['is_mdr'] == 1)).sum()
            phage_only = ((feature_matrix['has_prophages'] == 1) & (feature_matrix['is_mdr'] == 0)).sum()
            mdr_only = ((feature_matrix['has_prophages'] == 0) & (feature_matrix['is_mdr'] == 1)).sum()
            neither = ((feature_matrix['has_prophages'] == 0) & (feature_matrix['is_mdr'] == 0)).sum()

            # Fisher's exact test
            from scipy.stats import fisher_exact
            odds_ratio, p_value = fisher_exact([[both, phage_only], [mdr_only, neither]])

            cooccur_data.append({
                'Feature1': 'Prophages',
                'Feature2': 'MDR',
                'Both': both,
                'Feature1_only': phage_only,
                'Feature2_only': mdr_only,
                'Neither': neither,
                'Odds_Ratio': odds_ratio,
                'P_value': p_value
            })

        if cooccur_data:
            cooccur_df = pd.DataFrame(cooccur_data)
            cooccur_df.to_csv(self.output_dir / "cooccurrence_analysis.csv", index=False)
            logger.info("✓ Co-occurrence analysis saved")

    def plot_feature_network(self, feature_matrix: pd.DataFrame):
        """Plot network of feature associations"""
        logger.info("Plotting feature network...")

        # Calculate correlations
        numeric_cols = feature_matrix.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col not in ['sample_id']]

        if len(numeric_cols) < 2:
            return

        corr_matrix = feature_matrix[numeric_cols].corr()

        # Create network
        G = nx.Graph()

        # Add edges for significant correlations
        threshold = 0.3
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) > threshold:
                    G.add_edge(numeric_cols[i], numeric_cols[j], weight=abs(corr))

        # Plot network
        fig, ax = plt.subplots(figsize=(12, 10))

        pos = nx.spring_layout(G, k=2, iterations=50)

        # Draw edges
        edges = G.edges()
        weights = [G[u][v]['weight'] for u, v in edges]
        nx.draw_networkx_edges(G, pos, width=weights, alpha=0.6, edge_color='gray', ax=ax)

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=1000, node_color='steelblue',
                              alpha=0.8, ax=ax)

        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)

        ax.set_title('Feature Association Network (|correlation| > 0.3)',
                    fontsize=14, fontweight='bold')
        ax.axis('off')

        plt.tight_layout()
        plt.savefig(self.output_dir / "feature_network.png", dpi=300, bbox_inches='tight')
        plt.close()

        logger.info("✓ Feature network plot saved")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Kansas NARMS Comprehensive Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all analyses
  %(prog)s --all --compass-results results/ --outdir analysis/

  # Run specific analyses
  %(prog)s --phage --amr --compass-results results/ --outdir analysis/

  # Run correlations only
  %(prog)s --correlations --compass-results results/ --outdir analysis/
        """
    )

    parser.add_argument('--compass-results', required=True, type=Path,
                       help='Path to COMPASS pipeline results directory')
    parser.add_argument('--outdir', required=True, type=Path,
                       help='Output directory for analysis results')

    # Analysis selection
    parser.add_argument('--all', action='store_true',
                       help='Run all analyses')
    parser.add_argument('--phage', action='store_true',
                       help='Run phage phylogeny analysis')
    parser.add_argument('--amr', action='store_true',
                       help='Run temporal AMR trends analysis')
    parser.add_argument('--correlations', action='store_true',
                       help='Run phage-AMR-plasmid correlation analysis')
    parser.add_argument('--geography', action='store_true',
                       help='Run geographic patterns analysis (TODO)')
    parser.add_argument('--pangenome', action='store_true',
                       help='Run pan-genome analysis (TODO)')

    return parser.parse_args()


def main():
    """Main execution function"""
    args = parse_arguments()

    # Create output directory
    args.outdir.mkdir(parents=True, exist_ok=True)

    # Add file logging
    log_file = args.outdir / "analysis.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    logger.info("="*70)
    logger.info("KANSAS NARMS COMPREHENSIVE ANALYSIS")
    logger.info("="*70)
    logger.info(f"COMPASS results: {args.compass_results}")
    logger.info(f"Output directory: {args.outdir}")
    logger.info("")

    # Load data
    logger.info("Loading data...")
    loader = DataLoader(args.compass_results)

    try:
        df = loader.load_compass_summary()
        vibrant_results = loader.load_vibrant_results()
        amr_results = loader.load_amr_results()
        mob_results = loader.load_mobsuite_results()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        sys.exit(1)

    logger.info(f"✓ Data loaded: {len(df)} samples")
    logger.info("")

    # Determine which analyses to run
    run_all = args.all
    run_phage = args.phage or run_all
    run_amr = args.amr or run_all
    run_corr = args.correlations or run_all
    run_geo = args.geography or run_all
    run_pan = args.pangenome or run_all

    # Run analyses
    if run_phage:
        try:
            analyzer = PhageAnalyzer(df, vibrant_results, args.outdir)
            analyzer.analyze()
        except Exception as e:
            logger.error(f"Error in phage analysis: {e}", exc_info=True)

    if run_amr:
        try:
            analyzer = AMRAnalyzer(df, amr_results, args.outdir)
            analyzer.analyze()
        except Exception as e:
            logger.error(f"Error in AMR analysis: {e}", exc_info=True)

    if run_corr:
        try:
            analyzer = CorrelationAnalyzer(df, vibrant_results, amr_results, mob_results, args.outdir)
            analyzer.analyze()
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}", exc_info=True)

    if run_geo:
        logger.info("Geographic analysis not yet implemented")

    if run_pan:
        logger.info("Pan-genome analysis not yet implemented")

    logger.info("")
    logger.info("="*70)
    logger.info("ANALYSIS COMPLETE!")
    logger.info("="*70)
    logger.info(f"Results saved to: {args.outdir}")
    logger.info(f"Log file: {log_file}")


if __name__ == "__main__":
    main()
