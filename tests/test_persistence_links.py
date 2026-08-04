import json
from pathlib import Path
def test_persistence_report_is_explicit_and_schema_has_confidence():
 r=json.loads(Path('analysis/scripts/persistence-links.json').read_text()); assert r['links']==[] and r['confidence']=='unknown'
 s=json.loads(Path('schemas/persistence-link.schema.json').read_text()); assert 'confidence' in s['required']
