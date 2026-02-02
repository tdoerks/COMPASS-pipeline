#!/usr/bin/env Rscript

# Install rmarkdown if not already installed
if (!require("rmarkdown", quietly = TRUE)) {
  install.packages("rmarkdown", repos = "https://cloud.r-project.org")
}

# Convert markdown to PowerPoint
rmarkdown::pandoc_convert(
  input = "docs/presentations/lab_meeting/slides_ppt_optimized.md",
  to = "pptx",
  output = "docs/presentations/lab_meeting/lab_meeting_presentation.pptx",
  options = c(
    "--reference-doc=docs/presentations/lab_meeting/COMPASS_title_with_compass_badge_sq.pptx"
  )
)

cat("\n✅ PowerPoint created successfully!\n")
cat("📄 Output: docs/presentations/lab_meeting/lab_meeting_presentation.pptx\n\n")
