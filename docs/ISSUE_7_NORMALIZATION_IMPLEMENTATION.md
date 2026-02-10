# Issue #7: Normalization in GUI - Implementation Guide

## Overview

Add interactive toggle to switch between different count display modes in HTML dashboards:
- **Total counts** (raw sum - current default)
- **Counts per genome** (normalized by number of genomes)
- **Unique counts per genome** (deduplicated hits per genome)

## Status: In Progress

### ✅ Completed
1. Updated `analyze_prophage_types()` function to calculate all 3 metrics
2. Updated `analyze_prophage_quality()` function to calculate all 3 metrics

### 🔄 In Progress
3. Add HTML/CSS for normalization toggle control
4. Add JavaScript to switch between display modes
5. Update HTML tables to support dynamic switching

### ⏳ Pending
6. Apply same changes to other visualization scripts:
   - `visualize_amr_classes.py`
   - `visualize_prophages.py`
   - `visualize_plasmids.py`
   - `visualize_amr_on_plasmids.py`

---

## What We Changed So Far

### 1. `analyze_prophage_types()` Function

**Before:**
```python
def analyze_prophage_types(df):
    type_counts = df['type'].value_counts()
    type_stats = {
        'counts': type_counts.to_dict(),
        'percentages': (type_counts / len(df) * 100).to_dict()
    }
    return type_stats
```

**After:**
```python
def analyze_prophage_types(df):
    num_samples = df['sample_id'].nunique()

    # Total counts (raw sum)
    type_counts = df['type'].value_counts()

    # Per-genome counts (normalized by number of samples)
    type_per_genome = {ptype: count / num_samples for ptype, count in type_counts.items()}

    # Unique counts per genome (deduplicated)
    type_unique = df.groupby('type')['sample_id'].nunique().to_dict()
    type_unique_per_genome = {ptype: count / num_samples for ptype, count in type_unique.items()}

    type_stats = {
        'counts': type_counts.to_dict(),
        'percentages': (type_counts / len(df) * 100).to_dict(),
        'per_genome': type_per_genome,
        'unique_per_genome': type_unique_per_genome,
        'num_samples': num_samples
    }
    return type_stats
```

### 2. `analyze_prophage_quality()` Function

Same pattern - now calculates:
- `counts`: Total raw counts
- `percentages`: Percentage of total
- `per_genome`: Count divided by number of samples
- `unique_per_genome`: Unique samples with feature / total samples
- `num_samples`: Number of samples analyzed

---

## What We Still Need to Add

### 3. HTML Toggle Control

Add this CSS to the `<style>` section (around line 571):

```css
.normalization-toggle {
    background: #f0f4ff;
    border: 2px solid #667eea;
    border-radius: 10px;
    padding: 20px;
    margin: 30px 0;
    text-align: center;
}
.normalization-toggle h3 {
    color: #667eea;
    margin: 0 0 15px 0;
    font-size: 1.3em;
}
.toggle-options {
    display: flex;
    justify-content: center;
    gap: 30px;
    flex-wrap: wrap;
}
.toggle-option {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
}
.toggle-option input[type="radio"] {
    width: 20px;
    height: 20px;
    cursor: pointer;
}
.toggle-option label {
    font-size: 1.1em;
    font-weight: 500;
    cursor: pointer;
}
```

### 4. HTML Toggle Control (HTML)

Add this right after the "Key Statistics" section (around line 605):

```html
<section class="section">
    <div class="normalization-toggle">
        <h3>📊 Display Mode</h3>
        <div class="toggle-options">
            <div class="toggle-option">
                <input type="radio" id="mode-total" name="display-mode" value="total" checked>
                <label for="mode-total">Total Counts</label>
            </div>
            <div class="toggle-option">
                <input type="radio" id="mode-pergenome" name="display-mode" value="pergenome">
                <label for="mode-pergenome">Per-Genome</label>
            </div>
            <div class="toggle-option">
                <input type="radio" id="mode-unique" name="display-mode" value="unique">
                <label for="mode-unique">Unique per Genome</label>
            </div>
        </div>
        <div class="info-box" style="margin-top: 15px; text-align: left;">
            <strong>Display Modes:</strong>
            <ul>
                <li><strong>Total Counts:</strong> Raw sum of all features across all samples</li>
                <li><strong>Per-Genome:</strong> Average number of features per sample (total / {stats['types']['num_samples']} samples)</li>
                <li><strong>Unique per Genome:</strong> Percentage of samples containing each feature type</li>
            </ul>
        </div>
    </div>
</section>
```

### 5. JavaScript for Dynamic Switching

Add this JavaScript right before `</body>` tag:

```javascript
<script>
// Data for all display modes
const prophageTypeData = {
    total: {stats['types']['counts']},
    pergenome: {stats['types']['per_genome']},
    unique: {stats['types']['unique_per_genome']}
};

const prophageQualityData = {
    total: {stats['quality']['counts']},
    pergenome: {stats['quality']['per_genome']},
    unique: {stats['quality']['unique_per_genome']}
};

const numSamples = {stats['types']['num_samples']};

// Update tables when mode changes
document.querySelectorAll('input[name="display-mode"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const mode = this.value;
        updateTables(mode);
    });
});

function updateTables(mode) {
    // Update Prophage Type table
    updateTable('prophage-type-table', prophageTypeData[mode], mode);

    // Update Quality table
    updateTable('prophage-quality-table', prophageQualityData[mode], mode);
}

function updateTable(tableId, data, mode) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr');

    rows.forEach(row => {
        const typeCell = row.cells[0];
        const countCell = row.cells[1];
        const pctCell = row.cells[2];

        const type = typeCell.textContent.trim();
        const value = data[type];

        if (value !== undefined) {
            if (mode === 'total') {
                countCell.textContent = Math.round(value).toLocaleString();
                // Percentage stays the same
            } else if (mode === 'pergenome') {
                countCell.textContent = value.toFixed(2);
                pctCell.textContent = ((value / numSamples) * 100).toFixed(1) + '%';
            } else if (mode === 'unique') {
                countCell.textContent = (value * 100).toFixed(1) + '%';
                pctCell.textContent = Math.round(value * numSamples).toLocaleString() + ' samples';
            }
        }
    });
}
</script>
```

### 6. Update Table HTML with IDs

Change the Prophage Type table (around line 613):

```html
<table id="prophage-type-table">
    <thead>
        <tr>
            <th>Type</th>
            <th class="count-column">Count</th>
            <th>Percentage</th>
        </tr>
    </thead>
    <tbody>
```

Change the Quality table (around line 649):

```html
<table id="prophage-quality-table">
    <thead>
        <tr>
            <th>Quality</th>
            <th class="count-column">Count</th>
            <th>Percentage</th>
        </tr>
    </thead>
    <tbody>
```

---

## Example: How It Works

### Example Data
- **163 samples**
- **Lytic prophages**: 5000 total hits

### Display Mode: Total Counts
```
Type    | Count | Percentage
Lytic   | 5,000 | 60.0%
```

### Display Mode: Per-Genome
```
Type    | Count | Percentage
Lytic   | 30.67 | 18.8%
```
*Calculation: 5000 / 163 = 30.67 prophages per sample*

### Display Mode: Unique per Genome
```
Type    | Count      | Percentage
Lytic   | 92.6%      | 151 samples
```
*Calculation: 151 samples have lytic prophages / 163 total = 92.6%*

---

## Testing Plan

1. **Generate test HTML report**:
   ```bash
   python3 comprehensive_prophage_dashboard.py data/validation/results/
   ```

2. **Open in browser and verify**:
   - Default mode shows total counts
   - Switching to "Per-Genome" recalculates values
   - Switching to "Unique per Genome" shows percentages
   - All three modes show different but accurate data

3. **Verify calculations**:
   - Total mode: Sum all hits
   - Per-genome: Total / 163 samples
   - Unique: Count unique samples with feature

---

## Next Steps

1. **Finish comprehensive_prophage_dashboard.py** (this file)
   - Add HTML toggle
   - Add JavaScript
   - Add table IDs
   - Test with validation data

2. **Apply to other scripts**:
   - `visualize_amr_classes.py` - AMR gene classes
   - `visualize_prophages.py` - Prophage families
   - `visualize_plasmids.py` - Plasmid types
   - `visualize_amr_on_plasmids.py` - AMR on plasmids

3. **Comment on GitHub Issue #7**:
   - Demo screenshot
   - Explain implementation
   - Link to updated scripts

---

## Files Modified

- ✅ `/tmp/COMPASS-pipeline/comprehensive_prophage_dashboard.py` (partial)
- ⏳ Add HTML/JavaScript to same file
- ⏳ Apply to other visualization scripts

---

**Last Updated**: February 10, 2026
**Assigned To**: Issue #7 - Normalization in GUI for Feature Counts
**Status**: 40% complete
