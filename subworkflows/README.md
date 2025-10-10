# COMPASS Subworkflows

This directory contains modular subworkflows that group related processes into logical analysis units.

## Subworkflow Structure

### 1. Data Acquisition (`data_acquisition.nf`)
**Purpose**: Download and filter samples from public databases

**Modules**:
- `DOWNLOAD_NARMS_METADATA` - Download metadata from NARMS BioProjects
- `FILTER_NARMS_SAMPLES` - Filter samples by state, year, source
- `DOWNLOAD_SRA` - Download sequencing reads from SRA

**Inputs**: None (uses params)

**Outputs**:
- `reads` - Downloaded sequencing reads
- `filtered_samples` - Filtered sample metadata
- `versions` - Tool versions

**Usage**:
```groovy
include { DATA_ACQUISITION } from './subworkflows/data_acquisition'

workflow {
    DATA_ACQUISITION()
    DATA_ACQUISITION.out.reads.view()
}
```

### 2. Assembly & QC (`assembly_qc.nf`)
**Purpose**: Genome assembly and quality control

**Modules**:
- `ASSEMBLE_SPADES` - De novo assembly with SPAdes

**Future additions**:
- `QUAST` - Assembly statistics
- `CHECKM` - Completeness/contamination
- `BUSCO` - Gene completeness

**Inputs**:
- `reads` - Sequencing reads channel

**Outputs**:
- `assemblies` - Assembled genomes
- `versions` - Tool versions

**Usage**:
```groovy
include { ASSEMBLY_QC } from './subworkflows/assembly_qc'

workflow {
    Channel.fromPath('reads/*_{1,2}.fastq.gz')
        .map { [it.simpleName, it] }
        .set { reads }

    ASSEMBLY_QC(reads)
}
```

### 3. AMR Analysis (`amr_analysis.nf`)
**Purpose**: Antimicrobial resistance detection

**Modules**:
- `DOWNLOAD_AMRFINDER_DB` - Prepare AMRFinder+ database
- `AMRFINDER` - Detect resistance genes and mutations

**Inputs**:
- `samples` - Channel of [meta, fasta]

**Outputs**:
- `results` - AMR detection results
- `mutations` - Point mutations
- `versions` - Tool versions

**Usage**:
```groovy
include { AMR_ANALYSIS } from './subworkflows/amr_analysis'

workflow {
    Channel.fromPath('assemblies/*.fasta')
        .map { [[id: it.simpleName, organism: 'Salmonella'], it] }
        .set { samples }

    AMR_ANALYSIS(samples)
}
```

### 4. Phage Analysis (`phage_analysis.nf`)
**Purpose**: Comprehensive phage and prophage characterization

**Modules**:
- `DOWNLOAD_PROPHAGE_DB` - Prepare prophage database
- `VIBRANT` - Phage identification and classification
- `DIAMOND_PROPHAGE` - Prophage database comparison
- `CHECKV` - Phage genome quality assessment
- `PHANOTATE` - Phage gene prediction

**Inputs**:
- `samples` - Channel of [meta, fasta] or [sample_id, fasta]

**Outputs**:
- `vibrant_results` - VIBRANT output directories
- `phages` - Identified phage sequences
- `diamond_results` - DIAMOND matches
- `checkv_results` - Quality assessments
- `phanotate_results` - Gene predictions
- `versions` - Tool versions

**Usage**:
```groovy
include { PHAGE_ANALYSIS } from './subworkflows/phage_analysis'

workflow {
    Channel.fromPath('assemblies/*.fasta')
        .map { [it.simpleName, it] }
        .set { samples }

    PHAGE_ANALYSIS(samples)
}
```

## Main Workflows

### COMPASS Workflow (`workflows/compass.nf`)
**Purpose**: Integrated AMR and phage analysis

Combines AMR_ANALYSIS and PHAGE_ANALYSIS subworkflows with results aggregation.

**Inputs**:
- `samples` - Channel of [meta, fasta]

**Outputs**:
- `summary` - Combined TSV summary
- `report` - HTML report
- `amr_results` - AMR detection results
- `phage_results` - Phage sequences
- `versions` - All tool versions

### Full Pipeline (`workflows/full_pipeline_refactored.nf`)
**Purpose**: Complete analysis from NARMS to results

Combines all subworkflows: DATA_ACQUISITION → ASSEMBLY_QC → COMPASS

## Benefits of Subworkflow Structure

### 1. Modularity
- Subworkflows can be mixed and matched
- Easy to create new analysis combinations
- Reusable across different projects

### 2. Clarity
- Logical grouping of related processes
- Clear data flow between analysis stages
- Easier to understand overall pipeline structure

### 3. Maintainability
- Changes isolated to specific subworkflows
- Easier debugging and testing
- Better code organization

### 4. Flexibility
- Run individual subworkflows independently
- Skip unnecessary analysis steps
- Customize workflows for specific needs

## Usage Examples

### Example 1: AMR-only analysis
```groovy
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

include { AMR_ANALYSIS } from './subworkflows/amr_analysis'

workflow {
    Channel.fromPath('assemblies/*.fasta')
        .map { [[id: it.simpleName, organism: 'Salmonella'], it] }
        .set { samples }

    AMR_ANALYSIS(samples)
}
```

### Example 2: Phage-only analysis
```groovy
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

include { PHAGE_ANALYSIS } from './subworkflows/phage_analysis'

workflow {
    Channel.fromPath('assemblies/*.fasta')
        .map { [it.simpleName, it] }
        .set { samples }

    PHAGE_ANALYSIS(samples)
}
```

### Example 3: Custom workflow combining subworkflows
```groovy
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

include { DATA_ACQUISITION } from './subworkflows/data_acquisition'
include { ASSEMBLY_QC } from './subworkflows/assembly_qc'
include { AMR_ANALYSIS } from './subworkflows/amr_analysis'
// Skip phage analysis

workflow {
    DATA_ACQUISITION()
    ASSEMBLY_QC(DATA_ACQUISITION.out.reads)
    AMR_ANALYSIS(ASSEMBLY_QC.out.assemblies)
}
```

## Migration from Old Structure

The old `workflows/integrated_analysis.nf` is now split into:
- AMR components → `subworkflows/amr_analysis.nf`
- Phage components → `subworkflows/phage_analysis.nf`
- Combined → `workflows/compass.nf`

Old workflow files are preserved for backward compatibility but new development should use the subworkflow structure.

## Adding New Subworkflows

To add a new subworkflow:

1. Create a new `.nf` file in `subworkflows/`
2. Group related modules
3. Define clear inputs and outputs
4. Document in this README
5. Add to main workflow if needed

Example template:
```groovy
/*
 * SUBWORKFLOW: Description
 */

include { MODULE1 } from '../modules/module1'
include { MODULE2 } from '../modules/module2'

workflow MY_SUBWORKFLOW {
    take:
    input_channel

    main:
    MODULE1(input_channel)
    MODULE2(MODULE1.out.result)

    emit:
    result = MODULE2.out.result
    versions = MODULE1.out.versions
        .mix(MODULE2.out.versions)
}
```

## Testing Subworkflows

Each subworkflow can be tested independently:

```bash
# Test AMR analysis
nextflow run test_amr_subworkflow.nf -profile test

# Test phage analysis
nextflow run test_phage_subworkflow.nf -profile test
```

## Future Enhancements

Planned subworkflows:
- **Typing & Classification**: MLST, serotyping, phylogroups
- **Mobile Elements**: Plasmid detection, integron finding
- **Virulence Analysis**: Virulence factor detection
- **Phylogenetics**: SNP calling, pan-genome analysis
- **Advanced QC**: CheckM, BUSCO, QUAST integration

## Contributing

When contributing new subworkflows:
1. Follow the existing structure
2. Include comprehensive documentation
3. Add usage examples
4. Test independently before integration
5. Update this README
