"""Execute all notebook code cells in a fresh process, without kernel sockets."""
from pathlib import Path
from unittest.mock import patch
import sys
import nbformat

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path('tests').resolve()))
from test_analysis import fixtures
from IPython.core.interactiveshell import InteractiveShell
import fatigue_prediction.cli as cli

book = nbformat.read('program.ipynb', as_version=4)
nbformat.validate(book)
original_run = cli.run

def synthetic_run(data_dir, output, **kwargs):
    kwargs['bootstrap'] = 20
    with patch('fatigue_prediction.cli.load', return_value=(fixtures(), {'synthetic': True})):
        return original_run(data_dir, output, **kwargs)

shell = InteractiveShell.instance()
with patch.object(cli, 'run', synthetic_run):
    for index, cell in enumerate(book.cells):
        if cell.cell_type != 'code':
            continue
        source = cell.source.replace('Path("results/notebook")', 'Path("work/notebook-synthetic-results")')
        result = shell.run_cell(source)
        if result.error_before_exec or result.error_in_exec:
            raise RuntimeError(f'Notebook cell {index} failed')
print('All notebook code cells passed in process with synthetic data, bootstrap=20.')
