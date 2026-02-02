# Phylogenetic Trees for Lab Meeting Presentation

This directory contains phylogenetic tree files and instructions for interactive visualization.

## Available Trees

### 1. Kansas All-Prophage Tree (READY ✅)

**Location on Beocat**:
```bash
/homes/tylerdoe/kansas_2021-2025_all_prophage_phylogeny_20260126/
```

**Download**:
```bash
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/kansas_2021-2025_all_prophage_phylogeny_20260126/prophage_tree_cleaned.nwk .
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/kansas_2021-2025_all_prophage_phylogeny_20260126/prophage_metadata_cleaned.tsv .
```

**Details**:
- 7,097 prophage sequences from 825 samples
- Multi-organism: Campylobacter, Salmonella, E. coli
- Subsampled to 500 for phylogeny
- Tree has colons cleaned (ready for iTOL!)

### 2. E. coli AMR-Prophage Tree (PENDING ⏳)

**Status**: Needs to be restarted (previous run timed out at 24h)

**When complete**:
```bash
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/ecoli_amr_prophage_phylogeny_*/amr_prophage_subsample_tree_cleaned.nwk .
```

---

## How to Upload Trees to This Directory

After downloading from Beocat, upload to GitHub:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git checkout presentation
git pull origin presentation

# Copy your downloaded tree files
cp ~/prophage_tree_cleaned.nwk docs/presentations/lab_meeting/trees/kansas_all_prophage_tree_cleaned.nwk
cp ~/prophage_metadata_cleaned.tsv docs/presentations/lab_meeting/trees/kansas_prophage_metadata_cleaned.tsv

git add docs/presentations/lab_meeting/trees/
git commit -m "Add Kansas prophage phylogeny tree files"
git push origin presentation
```

---

## Visualizing Trees with iTOL

### Step 1: Generate iTOL Annotation Files

The metadata TSV needs to be converted to iTOL-compatible format:

```bash
# Make sure you're in the COMPASS-pipeline directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Run the annotation generator
python3 bin/generate_itol_annotations.py \\
    docs/presentations/lab_meeting/trees/kansas_prophage_metadata_cleaned.tsv \\
    itol_annotations/

# Output:
# itol_annotations/
#   organism_colorstrip.txt  - Color strip by organism
#   length_barchart.txt      - Bar chart showing prophage sizes
#   labels.txt               - Sample ID labels
```

### Step 2: Upload to iTOL

1. Go to: https://itol.embl.de/upload.cgi
2. Upload `kansas_all_prophage_tree_cleaned.nwk`
3. Once tree loads, **drag-and-drop** the annotation files onto the tree:
   - `organism_colorstrip.txt` (adds organism colors)
   - `length_barchart.txt` (adds size bar chart)
   - `labels.txt` (optional, adds sample labels)

### Step 3: Customize & Export

**In iTOL**:
- Adjust color strip width
- Change label sizes
- Collapse/expand clades
- Get shareable link: "Export" → "Project" → Copy URL
- Export PNG: "Export" → "Image" → PNG (3000x3000px for high-res)

---

## Offline Viewing with FigTree

**Install**:
```bash
# macOS
brew install --cask figtree

# Linux
sudo apt install figtree
```

**Usage**:
```bash
figtree kansas_all_prophage_tree_cleaned.nwk
```

**Controls**:
- Mouse wheel: Zoom in/out
- Click-drag: Pan around tree
- Right-click branches: Collapse/expand

---

## Tree Files in This Directory

After you upload them, this directory will contain:

```
trees/
├── README.md (this file)
├── kansas_all_prophage_tree_cleaned.nwk
├── kansas_prophage_metadata_cleaned.tsv
├── ecoli_amr_prophage_tree_cleaned.nwk (when ready)
└── ecoli_amr_prophage_metadata.tsv (when ready)
```

---

## During Lab Meeting Presentation

### Option 1: Live iTOL Demo (Recommended)
- Open iTOL link in browser during talk
- Demonstrate zoom/pan interactively
- Point out interesting clades on-the-fly

### Option 2: Static Images
- Export high-res PNG from iTOL beforehand
- Insert into PowerPoint as backup
- Use if internet connection fails

### Option 3: FigTree Live
- Open tree in FigTree before presentation
- Alt-tab to FigTree during tree discussion
- Full offline control

---

## Troubleshooting

### "Unknown template type" error in iTOL
Use the `generate_itol_annotations.py` script to convert metadata to proper iTOL format.

### Tree has colons in IDs
Make sure you're using the `*_cleaned.nwk` files, not the original `.nwk` files.

### Can't find tree files on Beocat
```bash
# List all phylogeny directories
ls -ld /homes/tylerdoe/*phylogeny*20260*
ls -ld /homes/tylerdoe/*prophage*20260*
```

---

## Resources

- **iTOL**: https://itol.embl.de/
- **iTOL Help**: https://itol.embl.de/help.cgi
- **FigTree**: http://tree.bio.ed.ac.uk/software/figtree/
- **Analysis Branch**: See `analysis/prophage_phylogeny_kansas_2021-2025/` for source scripts

---

**Last Updated**: February 2, 2026
**Branch**: `presentation`
