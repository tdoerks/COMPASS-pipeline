import csv
compass = {r['sample_id'] for r in csv.DictReader(open('results_mic_ecoli_6k/summary/compass_summary.tsv'), delimiter='\t')}
mic = {r['assembly_accession'].replace('.', '_', 1).replace('.', '_') for r in csv.DictReader(open('mic_ecoli_metadata/mic_metadata.csv'))}
overlap = compass & mic
print(f'COMPASS: {len(compass)}, MIC: {len(mic)}, Overlap: {len(overlap)}')
if overlap:
    print('Example overlapping IDs:')
    for s in list(overlap)[:3]:
        print(f'  {s}')
