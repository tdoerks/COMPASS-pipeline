# COMPASS Presentations

This directory contains presentation materials for the COMPASS pipeline and research findings.

## Contents

### 📊 [Phi Zeta Research Day 2026](./phi_zeta_2026/)
- **Date**: March 3, 2026
- **Venue**: Kansas State University College of Veterinary Medicine
- **Format**: Oral presentation (10-15 minutes)
- **Audience**: Veterinary researchers, students, faculty

**Files**:
- `abstract.md` - Abstract submission (267 words, Applied Science category)
- `slides.md` - Presentation slides (15 slides)

**Deadline**: Abstract due **January 31, 2026, 11:59 PM CST**

### 🔬 [Lab Meeting Presentation](./lab_meeting/)
- **Format**: Technical deep dive (~45-50 minutes)
- **Audience**: Lab members, computational biology focus

**Files**:
- `slides.md` - Detailed technical presentation (28 slides)

## Pipeline Diagram

Both presentations use the COMPASS pipeline diagram located in:
- `../pipeline_diagram/compass_pipeline.mmd` (Mermaid source)
- `../pipeline_diagram/compass_pipeline.svg` (Vector graphic)
- `../pipeline_diagram/compass_pipeline.png` (Raster image)

## Converting Markdown to PowerPoint

### Method 1: Pandoc (Recommended)

```bash
# Install pandoc
sudo apt install pandoc  # Linux
brew install pandoc      # macOS

# Convert to PowerPoint
cd docs/presentations/phi_zeta_2026
pandoc slides.md -o phi_zeta_2026.pptx

# With custom template (for consistent styling)
pandoc slides.md -o phi_zeta_2026.pptx --reference-doc=template.pptx
```

### Method 2: Marp (Markdown Presentation Ecosystem)

```bash
# Install Marp CLI
npm install -g @marp-team/marp-cli

# Convert to PowerPoint
marp slides.md --pptx -o phi_zeta_2026.pptx

# Convert to PDF
marp slides.md --pdf -o phi_zeta_2026.pdf

# Preview in browser
marp slides.md --preview
```

### Method 3: Manual Creation
- Copy slide content from markdown files
- Paste into PowerPoint
- Add images manually:
  - Pipeline diagram: `../pipeline_diagram/compass_pipeline.png`
  - Phylogenetic trees: Download from beocat (see session notes)
  - Data tables: Format in PowerPoint

## Presentation Assets

### Images Needed
1. **Pipeline Diagram** ✅
   - Location: `../pipeline_diagram/compass_pipeline.png`
   - Size: 2400×1800 px
   - Format: PNG (transparent background)

2. **Phylogenetic Trees** (Download from beocat)
   ```bash
   # Kansas AMR-prophage tree
   scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/kansas_2021-2025_amr_prophage_phylogeny_20260122/amr_prophage_tree_cleaned.nwk .

   # E. coli all-prophage tree
   scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/ecoli_all_prophage_phylogeny_20260123/prophage_tree_cleaned.nwk .

   # E. coli AMR-prophage subsample tree (when complete)
   scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/ecoli_amr_prophage_phylogeny_20260120/amr_prophage_subsample_tree_cleaned.nwk .
   ```

3. **Tree Visualization** (Upload to iTOL)
   - Go to https://itol.embl.de/
   - Upload `.nwk` files
   - Export as PNG/SVG (high resolution)
   - Color by year or organism

### Data Tables
- See session notes: `../../SESSION_2026-01-23.md`
- Kansas results summary
- E. coli temporal analysis
- AMR gene distribution

### Logos
- Kansas State University CVM logo
- Phi Zeta logo (for Phi Zeta presentation)
- Any funding source logos

## Presentation Tips

### For Phi Zeta (10-15 min oral)
- **Practice timing**: 1 minute per slide
- **Focus on impact**: Public health, veterinary medicine
- **Simplify jargon**: Broader audience, not all bioinformaticians
- **Visual heavy**: Use diagrams, minimize text
- **Emphasize novelty**: First comprehensive prophage-AMR surveillance

### For Lab Meeting (45-50 min)
- **Deep technical dive**: Methods, parameters, validation
- **Show raw data**: Be ready to display code, files
- **Discuss challenges**: What didn't work, why
- **Invite feedback**: Methods improvements, collaborations
- **Leave time for questions**: 10-15 min discussion

## Slide Design Guidelines

### Color Scheme (Match pipeline diagram)
- **Input/Download**: Blue (#0066CC, #E8F4F8)
- **QC**: Green (#27AE60, #D5F4E6)
- **Assembly**: Yellow/Orange (#F39C12, #FCF3CF)
- **AMR**: Red (#E74C3C, #FADBD8) - KEY FOCUS
- **Prophage**: Purple (#9B59B6, #E8DAEF) - KEY FOCUS
- **Typing**: Light Blue (#3498DB, #D6EAF8)
- **Output**: Green (#27AE60, #D5F4E6)

### Typography
- **Headings**: Sans-serif (Arial, Helvetica), bold, 36-44pt
- **Body text**: Sans-serif, 24-28pt
- **Code**: Monospace (Consolas, Monaco), 18-20pt
- **Maximum**: 5-7 bullet points per slide

### Layout
- Consistent header/footer
- Slide numbers
- KSU CVM branding
- White space (don't overcrowd)

## Timeline

### Immediate (This Week)
- [ ] Submit abstract by **Jan 31, 2026, 11:59 PM CST**
- [ ] Generate pipeline diagram PNG/SVG
- [ ] Download phylogenetic trees from beocat

### February 2026
- [ ] Await acceptance notification (Feb 14)
- [ ] Convert markdown to PowerPoint
- [ ] Add images and format slides
- [ ] Practice presentation (lab members)
- [ ] Refine based on feedback

### March 2026
- [ ] Final practice run (week before)
- [ ] Present at Phi Zeta Day (March 3)
- [ ] Present at lab meeting (TBD)

## Questions?

Contact: Tyler Doerks (tdoerks@vet.k-state.edu)

---

**Last Updated**: January 26, 2026
**Branch**: `presentation`
**Status**: Ready for review
