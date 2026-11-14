"""Locate a raw field/byte difference after ideal_check reports a mismatch.

This is a diagnostic only: the gameplay verdict uses the reviewed per-view
fingerprints and observer rules. Input dumps must contain every view's bytes.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from portable.tests.acceptance.step_state import split_frame
from portable.tests.acceptance.state_schema import differences


def inspect(schema, dos, native, field=None):
    data=json.loads(schema.read_text())
    items=data.get('state',data)['items']
    if field and field not in {i['name'] for i in items}:raise ValueError('Unknown field: '+field)
    left,right=split_frame(dos,items),split_frame(native,items)
    rows=[]
    for item in items:
        name=item['name']
        if field and name!=field:continue
        delta=differences(left[name],right[name])
        if delta['status']!='EQUAL':rows.append(dict(field=name,**delta))
    return dict(diagnostic='raw bytes; keyboard context and animation identities are not projected here',
                first_difference=rows[0] if rows else None,fields=rows)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('dos',type=Path);ap.add_argument('native',type=Path)
    ap.add_argument('--schema',type=Path,required=True,help='native-views.json from this check, or reference schema.json')
    ap.add_argument('--field',help='The named view from first_difference.views')
    a=ap.parse_args()
    print(json.dumps(inspect(a.schema,a.dos,a.native,a.field),indent=2))
