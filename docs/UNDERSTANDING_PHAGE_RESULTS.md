# Understanding Your Phage Results - Simple Explanation

## The Big Picture

Think of phage detection like identifying bacteria:
1. **Step 1**: "There's a bacteria here" (detection)
2. **Step 2**: "It's *E. coli*" (identification)

For phages:
1. **VIBRANT**: "There's a phage on contig_5" (detection)
2. **DIAMOND**: "It matches *Salmonella phage P22*" (identification)

---

## Reading the Phage Detection Section (VIBRANT)

When you see VIBRANT results, you're looking at a table with these important columns:

### scaffold
- **What it is**: The name of the contig/piece of your genome assembly where the phage was found
- **Example**: `NODE_5`, `contig_42`, `scaffold_123`
- **Think of it as**: The "address" where the phage lives in your genome

### type
- **What it is**: The phage's lifestyle
- **Options**:
  - `lytic`: Active virus that kills the bacteria when it reproduces
  - `lysogenic`: Dormant prophage integrated into the bacterial chromosome (like a sleeper virus)
- **Why it matters**: Lysogenic phages are more likely to carry extra genes like AMR genes

### quality
- **What it is**: How complete the phage sequence is
- **Options** (from best to worst):
  - `complete circular`: Full phage genome, highest confidence
  - `high quality draft`: Nearly complete
  - `medium quality draft`: Partial
  - `low quality draft`: Fragment or uncertain
- **Think of it as**: Confidence level in the detection

### Other columns
- These are technical scoring metrics used by VIBRANT's AI
- You can generally ignore these unless doing deep analysis
- Higher numbers usually = more confident detection

---

## Reading the Phage Identification Section (DIAMOND)

This is where you find out **WHAT phage it is** - this is what you were asking for!

### query
- **What it is**: The name of your contig (from VIBRANT)
- **Example**: `NODE_5_fragment_1`
- **Matches**: The `scaffold` column in VIBRANT results

### subject ⭐ **THIS IS THE PHAGE NAME!**
- **What it is**: The name of the known phage it matches in the database
- **Examples**:
  - `Salmonella_phage_P22_complete_genome`
  - `Escherichia_phage_lambda`
  - `Enterobacteria_phage_T4`
- **This tells you**: "Your phage looks like this known phage"
- **Think of it as**: The species/strain name (like saying "it's E. coli O157:H7")

### pident (Percent Identity)
- **What it is**: How similar your phage is to the known phage (percentage)
- **Example**: `85.3` means 85.3% of the amino acids match
- **Guidelines**:
  - `>90%`: Very closely related, probably the same phage
  - `70-90%`: Related phage, same family
  - `50-70%`: Distantly related
  - `<50%`: Very different, may not be meaningful
- **Think of it as**: DNA similarity (like human vs chimp = 98%)

### evalue (Expect Value)
- **What it is**: Statistical significance - how likely this match is by random chance
- **Example**: `2e-89` means 2 × 10⁻⁸⁹ (incredibly tiny number)
- **Guidelines**:
  - `<1e-10`: Excellent match, definitely real
  - `1e-10 to 1e-5`: Good match, likely real
  - `>1e-5`: Weak match, might be noise
- **Think of it as**: p-value in statistics (lower = better)
- **Rule of thumb**: If you see scientific notation with a big negative number, it's a good match!

### length
- **What it is**: How many amino acids aligned between your phage and the database phage
- **Example**: `256` means 256 amino acids matched
- **Think of it as**: How much of the phage sequence was compared

### bitscore
- **What it is**: Overall alignment quality score
- **Example**: `450.5`
- **Guidelines**:
  - Higher = better
  - `>200`: Excellent alignment
  - `100-200`: Good alignment
  - `<100`: Weak alignment
- **Think of it as**: Combined score of length and quality

---

## Real-World Example

Let's say you have these results:

**VIBRANT (Detection):**
```
scaffold: NODE_5
type: lysogenic
quality: high quality draft
```

**DIAMOND (Identification):**
```
query: NODE_5
subject: Salmonella_phage_P22_complete_genome
pident: 87.5
evalue: 3e-145
bitscore: 485.2
```

### What This Means:

1. **There's a phage on NODE_5** (VIBRANT found it)
2. **It's a lysogenic (dormant) phage** (integrated into the bacterial chromosome)
3. **The detection is high quality** (we're confident it's really a phage)
4. **It's 87.5% identical to Salmonella phage P22** (closely related)
5. **The match is extremely significant** (evalue of 3e-145 is excellent)
6. **The alignment score is high** (bitscore of 485)

**Plain English**: Your isolate has a dormant P22-like phage integrated into its chromosome on contig NODE_5.

---

## Connecting to AMR Results

Now let's say your AMR results show:

```
Gene: blaCTX-M-15
Contig: NODE_5
```

**AHA!** The AMR gene `blaCTX-M-15` is on the **same contig** (NODE_5) as the **P22-like phage**!

**This means**: The phage might be carrying the resistance gene, which is a big deal because phages can transfer genes between bacteria.

---

## Common Patterns You Might See

### Pattern 1: Multiple Hits to Same Phage
```
query: NODE_5_fragment_1, subject: Salmonella_phage_P22, pident: 90%
query: NODE_5_fragment_2, subject: Salmonella_phage_P22, pident: 88%
query: NODE_5_fragment_3, subject: Salmonella_phage_P22, pident: 92%
```
**Meaning**: Different parts of NODE_5 all match P22 - strong evidence it's a P22-like phage

### Pattern 2: No Good Matches
```
query: NODE_12
subject: various phages with pident: 30-40%, evalue: 0.01
```
**Meaning**: This might be a novel/unknown phage not in the database

### Pattern 3: Matches Multiple Phages
```
query: NODE_8, subject: Escherichia_phage_lambda, pident: 85%
query: NODE_8, subject: Enterobacteria_phage_HK97, pident: 83%
```
**Meaning**: Your phage is related to multiple known phages (they're all in the same family)

---

## Quick Reference Guide

| Column | What You Want to See |
|--------|---------------------|
| **subject** | Recognizable phage name |
| **pident** | >70% (higher = better) |
| **evalue** | <1e-10 (smaller = better) |
| **bitscore** | >100 (higher = better) |

**Red flags:**
- pident <50%: Probably not a good match
- evalue >0.001: Might be random noise
- Very short length (<50): Too small to trust

---

## What If I Don't See DIAMOND Results?

Possible reasons:
1. VIBRANT didn't detect any phages (check VIBRANT section)
2. VIBRANT found phages but they're too small/incomplete for DIAMOND
3. The detected phages don't match anything in the prophage database (novel phages)
4. DIAMOND process failed (check pipeline logs)

---

## Summary

**VIBRANT tells you:**
- ✅ Where the phage is (which contig)
- ✅ What type (lytic/lysogenic)
- ✅ Quality of detection

**DIAMOND tells you:**
- ✅ **What phage it is** (the name/species)
- ✅ How similar it is to known phages
- ✅ How confident we are in the match

**Together they answer:**
"Your isolate has a **P22-like lysogenic phage** on **contig NODE_5** with **87% similarity** to the reference."

Just like AMRFinder says: "Your isolate has **blaCTX-M-15** (an ESBL gene) on **contig NODE_5** with **99% similarity** to the reference."
