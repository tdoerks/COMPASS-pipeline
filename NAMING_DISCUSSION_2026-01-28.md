# Pipeline Naming Discussion - January 28, 2026

## Context

### Pipeline Evolution
The pipeline has evolved significantly from its original scope:

**Original Intent (2024)**:
- NARMS-specific data analysis tool
- Focus: NARMS surveillance data processing

**Current Reality (2026)**:
- **Universal bacterial genomics platform**
- Core focus areas:
  1. 🦠 **AMR detection** (Abricate, AMRfinder)
  2. 🧬 **Prophage analysis** (VIBRANT, Phanotate, DIAMOND)
  3. 🔄 **Plasmid detection** (MOB-suite)
- Additional features:
  - Assembly QC (FastQC, FASTP, QUAST, BUSCO)
  - MLST typing / SISTR
  - Temporal/geographic sampling tools
  - HPC/SLURM optimization for large-scale studies (thousands of genomes)

### Why Rename?

The current name "COMPASS" was chosen with NARMS and public health surveillance in mind. However, the pipeline is now:
- Used for veterinary research
- Used for food safety studies
- Used for academic bacterial genomics research
- Not limited to public health applications

We need a name that:
1. ✅ Emphasizes **prophage** detection (our key differentiator)
2. ✅ Reflects the comprehensive nature (assembly + prophage + AMR + plasmid)
3. ✅ Works for any application domain (public health, veterinary, research, food safety)
4. ✅ Follows NASA-style naming: meaningful name first, acronym backfilled
5. ✅ Is memorable and unique in the bioinformatics space

---

## Top Name Candidates

### 🥇 Option 1: PROPHET

**Full Name**: **P**rophage **R**ecognition **O**ptimized **P**ipeline with **H**igh-throughput **E**valuation **T**ools

**Tagline**: *"Revealing hidden mobile elements: prophage, plasmid, and AMR detection for bacterial genomics"*

#### Pros:
- ✅ **Prophage is the star** - makes our key differentiator obvious
- ✅ **Memorable metaphor** - "prophet" reveals hidden things (prophages ARE hidden in genomes!)
- ✅ **Unique** - no major bioinformatics tools called PROPHET
- ✅ **Use-case agnostic** - works for public health, veterinary, research, food safety
- ✅ **Great branding potential** - mystical/discovery theme
- ✅ **"Optimized"** reflects HPC/SLURM work

#### Cons:
- ⚠️ Slightly religious connotation (minor)
- ⚠️ Acronym is a bit forced with "with"

#### Mission Statement:
> "PROPHET reveals the hidden prophages and mobile genetic elements within bacterial genomes, providing comprehensive AMR and plasmid profiling at scale."

---

### 🥈 Option 2: MOSAIC

**Full Name**: **M**obile genetic element, plasmid, and prophage **O**rganization **S**creening for **A**MR **I**dentification & **C**haracterization

**Tagline**: *"Piecing together the bacterial genomic mosaic"*

#### Pros:
- ✅ **Perfect scientific metaphor** - bacterial genomes ARE mosaics of acquired elements
- ✅ **Emphasizes integration** - prophages, plasmids, AMR genes work together
- ✅ **Sophisticated sound** - professional, established
- ✅ **Beautiful imagery** - mosaic = piecing together complex patterns
- ✅ **Covers all major functions** - mobile elements, organization, AMR

#### Cons:
- ⚠️ "MOSAIC" exists in other contexts (though not bacterial genomics)
- ⚠️ Prophage not as prominent in acronym

#### Mission Statement:
> "MOSAIC pieces together the complex architecture of bacterial genomes, revealing how prophages, plasmids, and AMR genes create genomic mosaics."

---

### 🥉 Option 3: MAPPER

**Full Name**: **M**obile genetic element, **A**MR, and **P**rophage **P**rofiling: **E**xtensive bacterial genom**E** **R**esearch

**Tagline**: *"Map bacterial genomes: prophage, plasmid, and AMR detection at scale"*

#### Pros:
- ✅ **Clean, professional acronym** - no forced words
- ✅ **"Mapping" metaphor** - familiar in bioinformatics
- ✅ **All pillars represented** - mobile elements, AMR, prophage
- ✅ **Easy to cite** - "We used MAPPER v1.4 for analysis..."
- ✅ **Covers scale** - "Extensive" reflects large dataset capability

#### Cons:
- ⚠️ Less unique - "mapping" is common in bioinformatics
- ⚠️ Less memorable than PROPHET or MOSAIC

#### Mission Statement:
> "MAPPER provides comprehensive bacterial genome mapping, integrating prophage, plasmid, and AMR detection for large-scale genomic studies."

---

### 🔄 Option 4: COMPASS (Redefined)

**Full Name**: **C**omprehensive **O**utbreak **M**onitoring via **P**rophage, **A**MR, and pla**S**mid **S**urveillance

**Alternative**: **C**omprehensive **O**ne-stop **M**icrobial **P**rofiling: **A**MR, Prophage, Pla**S**mid **S**urveillance

**Tagline**: *"Navigate bacterial threats with integrated prophage and AMR surveillance"*

#### Pros:
- ✅ **Brand continuity** - already invested in this name
- ✅ **Navigation metaphor** - guiding through complex data
- ✅ **Professional sound** - established, credible
- ✅ **Prophage emphasized** in redefined acronym
- ✅ **No learning curve** - people already know the name

#### Cons:
- ⚠️ Still implies public health focus ("Outbreak Monitoring")
- ⚠️ Acronym feels forced to include prophage
- ⚠️ Less distinctive for what makes us unique

#### Mission Statement:
> "COMPASS guides researchers through bacterial genomic surveillance, integrating prophage, AMR, and plasmid detection to navigate complex datasets."

---

## Comparison Matrix

| Criteria | PROPHET | MOSAIC | MAPPER | COMPASS |
|----------|---------|--------|--------|---------|
| **Prophage prominence** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Memorability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Uniqueness** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Use-case flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Acronym quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Brand continuity** | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| **Scientific accuracy** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Additional Considerations

### What Makes This Pipeline Unique?

1. **Prophage-centric approach**: Most bacterial genomics pipelines treat prophages as an afterthought or ignore them entirely. This pipeline makes prophage detection a first-class feature with multiple complementary tools (VIBRANT, Phanotate, DIAMOND).

2. **Integration over isolation**: Rather than separate tools for assembly, AMR, and mobile elements, this pipeline integrates them into a unified workflow with consistent QC and reporting.

3. **Scale optimization**: Built for HPC/SLURM environments, optimized for analyzing thousands of genomes with efficient caching and resumability.

4. **Temporal/geographic sampling**: Custom tools for sophisticated NCBI sampling strategies (monthly, yearly, geographic) that go beyond simple filtering.

### Publication Considerations

When publishing the pipeline (preprint or peer-reviewed), consider:
- **Journal requirements**: Some journals prefer descriptive names over acronyms
- **Searchability**: Unique names are easier to find in literature searches
- **Citation format**: How will "Analyzed with PROPHET v1.4" sound in methods sections?
- **Branding consistency**: Logo, documentation, GitHub repo all need updating

### Timeline for Decision

**Recommendation**: Make final naming decision **before v1.4 release** and before any publication/preprint submission.

**Steps**:
1. Decide on name (this document provides options)
2. Update all documentation (README, wiki, config files)
3. Create new GitHub repo or rename existing
4. Update logo/branding
5. Prepare manuscript with new name
6. Release v1.4 with new branding

---

## Recommendation Summary

**Top pick**: **PROPHET**

**Why**:
- Best balance of prophage prominence, memorability, and uniqueness
- Tells a compelling story ("revealing hidden elements")
- Use-case agnostic (works for any application)
- Strong branding potential

**Runner-up**: **MOSAIC**
- If you want a more scientifically grounded metaphor
- Beautiful imagery for genomic architecture
- Emphasizes the integration of elements

**Safe choice**: Keep **COMPASS** (redefined)
- If brand continuity is most important
- Minimal disruption to existing users/documentation
- Can still emphasize prophage in updated tagline

---

## Next Steps

- [ ] Discuss with lab members / collaborators
- [ ] Check for name conflicts in bioinformatics databases (Bioconda, BioContainers, etc.)
- [ ] Search literature for existing uses of chosen name
- [ ] Mock up logo concepts for top choices
- [ ] Test how name sounds in citation: "We used [NAME] v1.4 (Doerksen et al., 2026) for..."
- [ ] Make final decision before v1.4 release
- [ ] Plan documentation/branding update timeline

---

**Document Created**: January 28, 2026
**Author**: Tyler Doerksen
**Status**: Draft for discussion
**Decision Deadline**: Before v1.4 publication
