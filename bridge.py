"""Browser transport adapter; algorithm modules are unchanged."""
import sys
sys.path.insert(0, '/project/source')
import json
import io
import base64
import zipfile
from pathlib import Path
from controller import Directory
from data_io import write_csv
from benchmark import run_benchmark

directory = Directory()


def dispatch(request_json):
    request = json.loads(request_json)
    path, data = request['path'], request.get('data') or {}
    if path == 'status':
        result = directory.status()
    elif path == 'load':
        result = directory.load(**data)
    elif path == 'query':
        result = directory.query(**data)
    elif path == 'mutate':
        result = directory.mutate(**data)
    elif path == 'benchmark':
        result = run_benchmark()
        result['metadata']['edition'] = 'Pyodide browser; visitor device'
    elif path == 'export':
        if not directory.engines:
            raise ValueError('Build the indexes first.')
        csv_path = Path('/project/results/directory_export.csv')
        write_csv(csv_path, directory.records)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('directory_export.csv', csv_path.read_bytes())
            archive.writestr('index_snapshot.json', json.dumps(directory.status(), indent=2))
        result = {'zip': base64.b64encode(buffer.getvalue()).decode('ascii')}
    else:
        raise ValueError('Unknown action.')
    return json.dumps(result)
