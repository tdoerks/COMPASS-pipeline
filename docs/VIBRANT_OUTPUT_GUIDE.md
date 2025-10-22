# Understanding VIBRANT Phage Analysis Results

## What is VIBRANT?

**VIBRANT** (Virus Identification By iteRative ANnoTation) identifies bacterial viruses (phages) and prophages in bacterial genomes using machine learning based on protein annotations.

## Key Columns in VIBRANT Summary Results

When you see phage results in the COMPASS report, here's what the main columns mean:

### Core Identity Columns

- **scaffold**: The name/ID of the viral sequence detected (e.g., "contig_1", "NODE_42")
  - This identifies which part of your bacterial genome contains a phage
  - Each row = one detected phage or prophage region

### Classification Columns

- **type**: Phage lifecycle prediction
  - **lytic**: Phages that kill the host cell upon reproduction
  - **lysogenic**: Prophages integrated into bacterial chromosome (can activate later)
  - This helps understand if the phage is dormant or actively replicating

- **quality**: Completeness assessment
  - **complete circular**: Full phage genome, high confidence
  - **high quality draft**: Nearly complete
  - **medium quality draft**: Partial phage
  - **low quality draft**: Fragment or uncertain

### Annotation Metrics

The remaining columns are normalized scores (0-1 range) used by VIBRANT's neural network for classification:

- **KEGG/Pfam/VOG columns**: Percentage of phage genes matching different protein databases
  - Higher values = more confident phage identification
  - "v-score" columns = virus-specific weighted scores

- **Check columns**: Validation metrics for specific features:
  - int-rep: integrase/recombinase genes (indicates lysogenic capability)
  - restriction check: restriction enzyme genes
  - toxin check: toxin-related genes
  - Various metabolic and structural gene categories

## What Does This Mean for Your Analysis?

### AMR-Phage Connection

When a sample has **both AMR genes and phages**, several scenarios are possible:

1. **Phage-mediated horizontal gene transfer**: Phages can carry AMR genes between bacteria
2. **Prophage activation**: Stress (like antibiotics) can activate dormant prophages
3. **Co-occurrence**: Simply present in the same isolate without direct connection

### Key Things to Look For

- **Lysogenic phages** (type="lysogenic") are more likely to carry extra genes like AMR
- **Complete circular** phages are higher confidence detections
- Multiple phages in one isolate suggests a complex mobile genome
- Check if the AMR genes and phage sequences are on the same contig (scaffold)

## Example Interpretation

```
Sample: SRR12345678
AMR Genes: 5 (including blaCTX-M)
Phages: 2
  - scaffold: NODE_1, type: lysogenic, quality: high quality draft
  - scaffold: NODE_12, type: lytic, quality: complete circular
```

**Interpretation**: This isolate has 5 AMR genes and 2 detected phages. The lysogenic phage on NODE_1 is integrated into the bacterial chromosome and could potentially carry or mobilize AMR genes. The lytic phage on NODE_12 is a complete, actively replicating phage.

**Action**: Investigate if NODE_1 contains any of the AMR genes (check AMRFinder scaffold column).

## Further Investigation

To determine if phages are actually carrying AMR genes, you would need to:

1. Check if AMR genes and phage regions are on the same scaffold/contig
2. Look at the detailed VIBRANT annotation files for gene content
3. Use specialized tools like PHASTER or MOB-suite to map gene locations

## References

- VIBRANT paper: [Kieft et al. 2020, Microbiome](https://microbiomejournal.biomedcentral.com/articles/10.1186/s40168-020-00867-0)
- VIBRANT GitHub: https://github.com/AnantharamanLab/VIBRANT
