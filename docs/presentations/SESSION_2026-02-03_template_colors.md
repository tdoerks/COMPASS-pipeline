# Session Notes: PowerPoint Template Colors & Slide Optimization
## Date: February 3, 2026

## Summary

Fixed presentation to use official COMPASS acronym and prepared template color guide for applying COMPASS color scheme to slides.

## Changes Made

### 1. Fixed COMPASS Acronym
- **Changed FROM**: "Comprehensive Omics Analysis Pipeline for Surveillance and Study"
- **Changed TO**: "COmprehensive Mobile element & Pathogen ASsessment Suite"
- **Files updated**: `slides.md`, `lab_meeting_slides.Rmd`
- **Source**: Official acronym from `README.md`

### 2. Applied PowerPoint Template
- **Changed**: `reference_doc: null` → `reference_doc: COMPASS_title_with_compass_badge_sq.pptx`
- **File**: `lab_meeting_slides.Rmd`
- **Result**: Presentation now uses uploaded COMPASS template

### 3. Optimized Slide Length
Split 3 overly long slides into 7 manageable slides:

**Before**:
- Slide 11 (1,020 chars) → Split into 11A + 11B
- Slide 21 (1,501 chars) → Split into 21A + 21B
- Slide 22 (2,095 chars) → Split into 22A + 22B + 22C

**After**: Each slide ~400-600 chars (fits PowerPoint comfortably)

---

## PowerPoint Template Color Guide

### Problem
The current template (`COMPASS_title_with_compass_badge_sq.pptx`) only applies colors to the title slide. Regular content slides remain plain white.

### Solution: Edit Slide Master

#### Step 1: Open PowerPoint Slide Master
1. Open `COMPASS_title_with_compass_badge_sq.pptx` in PowerPoint (desktop app)
2. Go to: **View** → **Slide Master**
3. Left panel shows all slide layouts

#### Step 2: Locate "Title and Content" Layout
This layout controls all regular content slides. It's usually the 2nd or 3rd layout in the left panel.

#### Step 3: Add COMPASS Colors

Use the official COMPASS color scheme from README:

| Section | Primary Color | Light Background | Use For |
|---------|--------------|------------------|---------|
| Input/Download | Blue | #0066CC / #E8F4F8 | Data acquisition slides |
| QC | Green | #27AE60 / #D5F4E6 | Quality control slides |
| Assembly | Orange | #F39C12 / #FCF3CF | Assembly slides |
| **AMR** | **Red** | **#E74C3C / #FADBD8** | **AMR detection slides** |
| **Prophage** | **Purple** | **#9B59B6 / #E8DAEF** | **Prophage analysis slides** |
| Typing | Light Blue | #3498DB / #D6EAF8 | MLST/serotyping slides |
| Output | Green | #27AE60 / #D5F4E6 | Results/reporting slides |

#### Step 4: Design Options

**Option A: Single Colored Accent Bar (Simplest)**
1. In "Title and Content" layout, insert a rectangle
2. Position at top of slide (above title) or left side (vertical bar)
3. Fill with one color (e.g., purple #9B59B6 for general use)
4. Make it 0.5-1 inch wide/tall
5. Result: All slides have consistent colored accent

**Option B: Colored Title Background**
1. Select the title placeholder box
2. Right-click → Format Shape → Fill
3. Set background color (use light tints like #E8DAEF)
4. Result: Title area colorized, content area remains white

**Option C: Full Colored Background (Use Light Tints!)**
1. Right-click on slide background → Format Background
2. Choose Solid Fill
3. Use LIGHT colors only (#FADBD8, #E8DAEF, #D5F4E6)
4. Result: Entire slide has colored background (ensure text contrast)

**Option D: Multiple Colored Layouts (Advanced)**
1. In Slide Master view, right-click "Title and Content"
2. Select "Duplicate Layout"
3. Rename: "Title and Content - AMR"
4. Add red accent (#E74C3C or light #FADBD8)
5. Repeat for each section:
   - "Title and Content - Prophage" (purple)
   - "Title and Content - QC" (green)
   - "Title and Content - Assembly" (orange)
6. Save template
7. Use custom-style divs in .Rmd to assign slides to layouts

#### Step 5: Save Template
1. Close Slide Master view (click "Close Master View")
2. Delete any example slides
3. **File** → **Save**
4. Template is now updated!

---

## Using Multiple Colored Layouts in R Markdown

If you created Option D (multiple layouts), use them like this:

```markdown
---
title: "COMPASS Pipeline"
output:
  powerpoint_presentation:
    reference_doc: COMPASS_title_with_compass_badge_sq.pptx
---

## Regular Slide
This uses the default layout (neutral color)

---

::: {custom-style="Title and Content - AMR"}
## AMR Detection Results
- This slide will have RED accents
- Color applied automatically from template
:::

---

::: {custom-style="Title and Content - Prophage"}
## Prophage Analysis
- This slide will have PURPLE accents
- Color applied automatically from template
:::

---

## Another Regular Slide
Back to default layout
```

**Layout Names Must Match Exactly**:
- Check layout names in PowerPoint Slide Master view
- Use exact names in `custom-style=""` divs

---

## Recommendation

**For a 45-minute technical presentation:**
- Use **Option A** (single colored accent bar) for consistency
- Choose purple (#9B59B6) since prophage is a key focus
- Or use blue (#0066CC) for neutral/professional look

**For a multi-section presentation:**
- Use **Option D** (multiple colored layouts)
- Manually assign slides to layouts via custom-style divs
- Results in color-coded sections (AMR=red, Prophage=purple, etc.)

---

## Alternative: LibreOffice Impress or Google Slides

**Don't have PowerPoint?**

### LibreOffice Impress (Free, Open Source)
1. Install: `sudo apt install libreoffice-impress` (Linux) or download from libreoffice.org
2. Open `.pptx` template
3. Go to: **View** → **Master Slide**
4. Edit layouts same way as PowerPoint
5. Save as `.pptx`

### Google Slides (Web-based)
1. Upload `.pptx` to Google Drive
2. Open with Google Slides
3. Go to: **Slide** → **Edit Master**
4. Edit layouts (colors, shapes, backgrounds)
5. Download as PowerPoint (`.pptx`)

---

## Files Modified This Session

### Updated Files
- `docs/presentations/lab_meeting/slides.md` - Split long slides, fixed acronym
- `docs/presentations/lab_meeting/lab_meeting_slides.Rmd` - Fixed acronym, applied template

### New Files
- `docs/presentations/SESSION_2026-02-03_template_colors.md` (this file)

---

## Next Steps

1. ✅ Presentation files updated and pushed
2. ⏭️ Edit PowerPoint template to add colors (user task)
3. ⏭️ Regenerate presentation: `rmarkdown::render('lab_meeting_slides.Rmd')`
4. ⏭️ Review generated PowerPoint, adjust template if needed
5. ⏭️ Practice presentation timing (aim for 45-50 minutes)

---

## Slide Count Update

**Before optimization**: 29 slides (some too long)
**After optimization**: 34 slides (all fit comfortably)

| Slide Change | Before | After |
|--------------|--------|-------|
| Dataset Inventory | Slide 11 | Slides 11A, 11B |
| Phylo Datasets | Slide 21 | Slides 21A, 21B |
| iTOL Demo | Slide 22 | Slides 22A, 22B, 22C |

**Total presentation time**: Still ~45-50 minutes (more slides but less dense content per slide)

---

## Git Commit History

```bash
# Commit 1: Fix COMPASS acronym and apply template
git commit -m "Fix presentation title to use official COMPASS acronym and apply template"

# Commit 2: Optimize slide length
git commit -m "Split overly long slides for better PowerPoint formatting"
```

---

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu
Kansas State University College of Veterinary Medicine
Diagnostic Medicine/Pathobiology

---

**Last Updated**: February 3, 2026
**Branch**: `presentation`
**Status**: Ready for template color editing
