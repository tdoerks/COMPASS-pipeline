# COMPASS HTML Report - Final Tab Structure

## Overview

After tonight's implementation, here's what the tab structure looks like:

## Tab Navigation (in order):

1. **📊 Overview**
   - Total samples, organisms, AMR genes
   - Sample distribution pie chart
   - Key statistics cards

2. **💊 AMR Analysis**  
   - Top AMR genes bar chart
   - AMR classes distribution
   - MDR vs Non-MDR donut chart
   - Sample distribution by AMR gene count

3. **🧬 Plasmid Analysis**
   - Top 15 Inc groups (horizontal bar)
   - Mobility types (conjugative/mobilizable/non-mobilizable)
   - Plasmid count distribution histogram
   - Plasmid vs AMR scatter plot

4. **🦠 Prophage Functional Diversity**
   - Functional category pie chart
   - DNA Packaging, Structural, Lysis, DNA Modification, Regulation, Other

5. **🔍 Metadata Explorer** ⭐ NEW!
   - Dynamic field selection dropdown
   - Metric selection (count, MDR rate, avg AMR/prophage/plasmid)
   - Chart type selection (bar/line/pie)
   - Live statistics panel
   - **Replaces old Temporal Analysis and Geographic Analysis tabs**

6. **🧪 Strain Typing**
   - Top MLST sequence types
   - MLST scheme distribution
   - Serovar distribution (Salmonella only)

7. **📈 Assembly Quality**
   - N50 distribution histogram
   - Assembly length distribution
   - Contig count distribution
   - BUSCO completeness distribution

8. **📋 Data Table**
   - Sortable, filterable table of all samples
   - Pagination controls
   - Export-friendly view

## What Changed?

### Removed:
- ❌ **Temporal Analysis** tab (hardcoded to Year field)
- ❌ **Geographic Analysis** tab (hardcoded to State field)

### Added:
- ✅ **Metadata Explorer** tab (works with ANY metadata field!)

### Moved:
- **Prophage Functional Diversity** moved from position 9 → position 4
  - Rationale: Core microbiology analyses (AMR/Plasmid/Prophage) grouped together

## Benefits of New Structure

1. **More Flexible**: Metadata Explorer adapts to any dataset
2. **More Compact**: 8 tabs instead of 9
3. **Better Organization**: Core analyses together
4. **User-Driven**: Explorer lets users choose what to visualize
5. **Future-Proof**: Auto-detects new metadata columns

## Metadata Explorer - How It Works

### Available Metadata Fields:
The dropdown will show ALL metadata columns from your dataset, excluding technical fields like:
- sample_id, assembly_path
- num_amr_genes, num_prophages, num_plasmids (these are metrics)
- AMR-specific columns (amr_genes, mdr_status)
- Assembly QC columns (n50, assembly_length, etc.)

### Typical Fields for NARMS Data:
- `organism` → E. coli, Salmonella, Campylobacter
- `year` → Collection year
- `state` → State abbreviation
- `source` → Clinical, chicken, retail meat, etc.
- `isolation_type` → Environmental, clinical, etc.
- Any other NARMS metadata columns

### Available Metrics:
- **Sample Count** - How many samples in each group
- **MDR Rate (%)** - Percentage with MDR in each group
- **Avg AMR Genes** - Average number of AMR genes per sample
- **Avg Prophages** - Average prophages per sample
- **Avg Plasmids** - Average plasmids per sample

### Chart Types:
- **Bar Chart** - Best for comparing categories
- **Line Chart** - Best for trends (especially with year)
- **Pie Chart** - Best for proportions (shows legend)

## Example Explorations

### 1. Samples by Organism
- Field: `organism`
- Metric: Sample Count
- Chart: Bar
- **Result**: See distribution of E. coli vs Salmonella vs Campylobacter

### 2. MDR Trend Over Time
- Field: `year`
- Metric: MDR Rate (%)
- Chart: Line
- **Result**: Track MDR percentage changes year-over-year

### 3. Source Breakdown
- Field: `source`
- Metric: Sample Count
- Chart: Pie
- **Result**: Proportion from clinical vs food sources

### 4. AMR by State (if multi-state)
- Field: `state`
- Metric: Avg AMR Genes
- Chart: Bar
- **Result**: Compare average AMR burden across states

## Testing Workflow

```bash
# On Beocat
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull
./test_kansas_2021-2025_summary_bulk.sh

# Download compass_summary_FIXED.html
# Open in browser
# Navigate to each tab
# Try Metadata Explorer with different combinations
```

## Known Limitations

- Top 15 values per field (for performance)
- Requires metadata fields to be present in dataframe
- Empty/missing values filtered out ('-', 'Unknown', NaN)

## Future Enhancements (Ideas)

- Multi-field grouping (e.g., organism + year)
- Downloadable chart images
- Custom color schemes
- Filter by value ranges
- Save/bookmark favorite combinations

---

**Last Updated**: December 20, 2025
**Version**: Post-Metadata-Explorer Implementation
