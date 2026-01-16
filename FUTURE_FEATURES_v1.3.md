# COMPASS Pipeline v1.3 - Future Features Roadmap

This document tracks feature ideas and enhancements planned for future versions of the COMPASS pipeline.

---

## 🤖 AI Assistant Integration (Priority: Medium)

### Overview
Add an AI-powered assistant to help users analyze their COMPASS results through natural language questions and automated insights.

### Three Implementation Options

#### Option A: Cloud-Based AI Chatbot (Medium Complexity)
**Description**: Embed a live chatbot widget (Claude API) directly in the HTML report

**How it works**:
- User opens COMPASS HTML report in browser
- Clicks floating chat icon in corner
- Types questions like "Which samples have the most AMR genes?" or "Show me plasmid distribution by host"
- Claude API analyzes the data and generates responses/charts

**Pros**:
- ✅ Full AI capabilities (Claude Sonnet 4.5)
- ✅ Natural language understanding
- ✅ Can generate custom visualizations on demand
- ✅ Interactive conversation

**Cons**:
- ❌ Requires active internet connection
- ❌ Costs per API call (~$3-15 per million tokens)
- ❌ Data privacy concerns (genomic data sent to Anthropic servers)
- ❌ Users need to provide own API key OR lab provides shared key

**Implementation Effort**: 2-3 days
- JavaScript chatbot UI widget (~100 lines)
- Claude API integration (~200 lines)
- Data context preparation (~100 lines)
- TSV → JSON converter for AI context
- Rate limiting and error handling

---

#### Option B: Local AI Model (High Complexity)
**Description**: Embed a smaller AI model that runs entirely in the user's browser

**How it works**:
- User downloads COMPASS HTML report
- Report includes embedded WebAssembly AI model (e.g., Llama 3.1 8B)
- AI runs locally in browser - no internet needed
- Fully private - data never leaves user's computer

**Pros**:
- ✅ Completely offline and private
- ✅ No API costs
- ✅ Works without internet
- ✅ No data sharing concerns

**Cons**:
- ❌ Very large download (1-5 GB for model files)
- ❌ Slow performance (runs in browser, not optimized hardware)
- ❌ Limited capabilities vs. Claude
- ❌ Requires modern browser with WebGPU support
- ❌ May not work on older computers

**Implementation Effort**: 1-2 weeks
- Complex WebAssembly integration
- Model quantization and optimization
- Browser compatibility testing
- Significant performance tuning

**Technologies**: Transformers.js, ONNX Runtime, or WebLLM

---

#### Option C: Pre-Generated AI Insights (Low Complexity) ⭐ **RECOMMENDED**
**Description**: Run Claude API during pipeline execution to generate insights, then embed static text/charts in HTML

**How it works**:
- COMPASS pipeline calls Claude API while generating summary
- Claude analyzes the dataset and generates insights:
  - "This dataset shows high MDR prevalence (65%) with frequent blaKPC genes"
  - "Plasmid Inc group IncF is dominant in 12/15 samples"
  - "Quality concern: 3 samples have low N50 (<50kb)"
- Insights embedded as static HTML sections
- No runtime AI needed - report is fully self-contained

**Pros**:
- ✅ Best of both worlds - AI insights without runtime complexity
- ✅ No internet needed for viewing report
- ✅ No privacy concerns - data stays on HPC
- ✅ Only researcher running pipeline needs API access
- ✅ Fast - insights pre-computed
- ✅ Easy to implement

**Cons**:
- ❌ Not interactive - can't ask follow-up questions
- ❌ Insights fixed at report generation time
- ❌ Still requires API key (but only for researcher, not end users)

**Implementation Effort**: 2-3 days
- Claude API integration in `generate_compass_summary.py` (~150 lines)
- Prompt engineering for useful insights
- HTML template for insight sections
- Cost estimation and rate limiting

---

## Implementation Recommendation

**Start with Option C (Pre-Generated Insights)** for v1.3:

### Phase 1: Basic AI Insights (v1.3.0)
- Add Claude API call during summary generation
- Generate 3-5 key insights per dataset:
  1. **AMR Summary**: "15/20 samples (75%) show MDR phenotype..."
  2. **Quality Alert**: "3 samples failed QC due to low N50..."
  3. **Plasmid Trends**: "IncFII plasmids found in 80% of samples..."
  4. **Geographic/Temporal Patterns**: "Resistance increasing over time..."
  5. **Prophage Insights**: "High lysogenic prophage count in clinical isolates..."

### Phase 2: Interactive Charts (v1.3.1)
- Let Claude suggest interesting data visualizations
- Generate custom chart configurations based on data patterns
- Add to HTML as Chart.js configurations

### Phase 3: Sample-Level Insights (v1.3.2)
- Per-sample AI analysis
- Highlight unusual patterns
- Flag potential quality issues

### Future: Add Interactive AI (v2.0)
- If users request it, add Option A (Cloud Chatbot) in v2.0
- By then, browser-based AI may be more mature (Option B)

---

## Cost Estimation (Option C)

**Claude API Pricing** (as of 2025):
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

**Per-Report Cost**:
- Typical COMPASS summary: ~5,000 tokens (TSV data + sample info)
- AI response: ~500 tokens (insights text)
- Cost per report: ~$0.02-0.03 (negligible!)

**Annual Cost** (assuming 500 reports/year):
- ~$10-15/year total
- Very affordable for most labs

---

## Configuration

Add to `nextflow.config`:

```groovy
params {
    // AI Insights (Optional - requires Claude API key)
    enable_ai_insights = false  // Set to true to enable
    claude_api_key = null       // Or set via environment: ANTHROPIC_API_KEY
    ai_insight_level = 'standard'  // 'basic', 'standard', or 'detailed'
}
```

Users can enable by:
```bash
nextflow run main.nf --enable_ai_insights --claude_api_key sk-ant-xxx
```

Or set environment variable:
```bash
export ANTHROPIC_API_KEY=sk-ant-xxx
nextflow run main.nf --enable_ai_insights
```

---

## Other v1.3 Feature Ideas

### 1. Interactive Data Filtering
- Add filter controls to charts
- "Show only MDR samples"
- "Filter by date range"
- "Compare clinical vs. environmental isolates"

### 2. Report Comparison Mode
- Compare two COMPASS runs side-by-side
- Highlight differences in AMR trends
- Useful for longitudinal studies

### 3. Export Enhancements
- Export filtered data subsets
- Generate publication-ready figures
- PDF report generation

### 4. Enhanced Metadata Integration
- Better handling of custom metadata
- Automatic detection of metadata types
- Smart suggestions for grouping variables

### 5. Performance Optimizations
- Faster summary generation for large datasets (1000+ samples)
- Incremental updates (add new samples without re-processing all)
- Parallel processing for summary scripts

---

## Timeline (Tentative)

- **v1.2**: Current focus - UI improvements, bug fixes, metadata handling
- **v1.3**: AI insights (Option C), interactive filtering, comparison mode
- **v2.0**: Major refactor, interactive AI chatbot (Option A), advanced analytics

---

## Contributing Ideas

Have ideas for v1.3 or beyond? Add them here or open a GitHub issue!

**Last Updated**: January 2026
