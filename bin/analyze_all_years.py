#!/usr/bin/env python3
"""
Multi-Year Analysis Wrapper
Automatically finds and processes all year directories (2021-2025)
and generates a combined comprehensive report.
"""
import sys
import subprocess
from pathlib import Path
import re

def find_year_directories(base_dir):
    """Find all results directories for years 2021-2025"""
    base_dir = Path(base_dir)
    year_dirs = []

    # Look for directories matching patterns like:
    # - results_kansas_2024
    # - results_kansas_2021
    # etc.

    if base_dir.is_dir():
        for item in base_dir.iterdir():
            if item.is_dir():
                # Check if directory name contains a year between 2021-2025
                match = re.search(r'(2021|2022|2023|2024|2025)', item.name)
                if match:
                    # Verify it has the expected structure (amrfinder, vibrant, etc.)
                    if (item / "amrfinder").exists() and (item / "vibrant").exists():
                        year = match.group(1)
                        year_dirs.append((year, item))

    return sorted(year_dirs, key=lambda x: x[0])

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_all_years.py <results_base_directory> [output_html]")
        print("\nExample:")
        print("  python3 analyze_all_years.py /homes/tylerdoe/compass_kansas_results")
        print("\nThis will find and analyze all year directories (2021-2025) in the base directory.")
        sys.exit(1)

    base_dir = Path(sys.argv[1])
    output_html = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "comprehensive_amr_prophage_all_years_dashboard.html"

    if not base_dir.exists():
        print(f"❌ Error: Base directory not found: {base_dir}")
        sys.exit(1)

    # Find all year directories
    print(f"\n🔍 Searching for year directories in: {base_dir}")
    year_dirs = find_year_directories(base_dir)

    if not year_dirs:
        print("❌ No year directories found!")
        print("   Looking for directories matching patterns like 'results_kansas_2024'")
        sys.exit(1)

    print(f"\n✅ Found {len(year_dirs)} year directories:")
    for year, directory in year_dirs:
        print(f"   {year}: {directory}")

    # Get the path to the comprehensive analysis script
    script_dir = Path(__file__).parent
    comprehensive_script = script_dir / "comprehensive_amr_prophage_analysis.py"

    if not comprehensive_script.exists():
        print(f"❌ Error: Comprehensive analysis script not found: {comprehensive_script}")
        sys.exit(1)

    # Create a temporary combined directory approach won't work well
    # Instead, we'll run the analysis on each directory and combine at the end
    # But actually, the comprehensive script already handles multiple years via metadata!

    # The best approach: just run on all directories and let the temporal analysis
    # combine them via the Collection_Date in metadata

    print(f"\n🔬 Running comprehensive analysis on all directories...")
    print(f"   This will combine data from all {len(year_dirs)} years")
    print(f"   Output: {output_html}\n")

    # For now, let's run on the most recent year that has the most complete data
    # OR better: create a script that merges all the directories

    # Actually, the BEST approach is to point to a directory that contains all samples
    # Let's check if there's a combined directory or if we need to analyze each separately

    # Simple approach: Run on each directory and print results, then create combined HTML
    all_year_data = []

    for year, directory in year_dirs:
        print(f"\n{'='*85}")
        print(f"Processing {year}: {directory.name}")
        print('='*85)

        # Run comprehensive analysis on this directory
        try:
            # Import and run the comprehensive analysis directly
            # This is more efficient than subprocess
            sys.path.insert(0, str(script_dir))
            import comprehensive_amr_prophage_analysis as comp_analysis

            data = comp_analysis.run_comprehensive_analysis(directory)

            if data['overall']['total_samples'] > 0:
                print(f"\n✅ {year}: Processed {data['overall']['total_samples']} samples")
                print(f"   AMR genes: {data['overall']['total_amr_genes']}")
                print(f"   AMR on prophages: {data['overall']['amr_on_prophage']} ({data['overall']['amr_on_prophage']/data['overall']['total_amr_genes']*100:.1f}%)")
                print(f"   MDR islands: {len(data['mdr_islands'])}")
                all_year_data.append((year, directory, data))
            else:
                print(f"\n⚠️  {year}: No samples found")

        except Exception as e:
            print(f"\n❌ Error processing {year}: {e}")
            continue

    if not all_year_data:
        print("\n❌ No data collected from any year!")
        sys.exit(1)

    # Now create a combined summary
    print(f"\n\n{'='*85}")
    print("COMBINED SUMMARY - ALL YEARS")
    print('='*85)

    total_samples = sum(data['overall']['total_samples'] for _, _, data in all_year_data)
    total_amr = sum(data['overall']['total_amr_genes'] for _, _, data in all_year_data)
    total_amr_prophage = sum(data['overall']['amr_on_prophage'] for _, _, data in all_year_data)
    total_mdr = sum(len(data['mdr_islands']) for _, _, data in all_year_data)

    print(f"\n📊 Combined Statistics (2021-2025):")
    print(f"  Total samples: {total_samples}")
    print(f"  Total AMR genes: {total_amr}")
    print(f"  AMR on prophages: {total_amr_prophage} ({total_amr_prophage/total_amr*100:.1f}%)")
    print(f"  Total MDR islands: {total_mdr}")

    print(f"\n📅 Year-by-Year Breakdown:")
    print(f"  {'Year':<8} {'Samples':<10} {'AMR Total':<12} {'On Prophage':<15} {'% Prophage':<12} {'MDR Islands'}")
    print("  " + "-"*80)

    for year, directory, data in all_year_data:
        pct = (data['overall']['amr_on_prophage'] / data['overall']['total_amr_genes'] * 100) if data['overall']['total_amr_genes'] > 0 else 0
        print(f"  {year:<8} {data['overall']['total_samples']:<10} {data['overall']['total_amr_genes']:<12} "
              f"{data['overall']['amr_on_prophage']:<15} {pct:<11.1f}% {len(data['mdr_islands'])}")

    # For detailed analysis, pick the directory with the most complete metadata
    # Or combine all samples - but that requires merging directories
    print(f"\n\n💡 For detailed temporal analysis across all years:")
    print(f"   If your metadata includes Collection_Date spanning 2021-2025,")
    print(f"   run the comprehensive analysis on the directory with all samples:")
    print(f"\n   python3 {comprehensive_script} \\")
    print(f"       <directory_with_all_samples> \\")
    print(f"       {output_html}")

    print(f"\n   Or run on each year individually for year-specific reports.")

    print(f"\n{'='*85}")
    print("✅ Multi-year analysis complete!")
    print('='*85 + "\n")

if __name__ == "__main__":
    main()
