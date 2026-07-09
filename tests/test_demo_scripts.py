"""
simulation.py / network_demo.py / subnetwork_demo.py / networkx_demo.py are top-level
scripts (no functions, no `if __name__ == '__main__':` guard) that exercise the core API
end-to-end and print results - README categorizes them as demo/utility scripts, not
covered by organflow's 100%-coverage mandate. Importing them directly would run
their side effects at collection time and pollute global state across tests, so each is
smoke-tested as a subprocess instead: does it still run start-to-finish without error.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXECUTE_DIR = REPO_ROOT / 'execute'


def _run_script(name, extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run([sys.executable, str(EXECUTE_DIR / name)],
                          cwd=REPO_ROOT, capture_output=True, text=True,
                          timeout=60, env=env)


def test_simulation_runs_end_to_end_without_error():
    result = _run_script('simulation.py')
    assert result.returncode == 0, result.stderr


def test_network_demo_runs_end_to_end_without_error():
    result = _run_script('network_demo.py')
    assert result.returncode == 0, result.stderr


def test_subnetwork_demo_runs_end_to_end_without_error():
    result = _run_script('subnetwork_demo.py')
    assert result.returncode == 0, result.stderr


def test_networkx_demo_runs_end_to_end_without_error():
    pytest.importorskip('matplotlib')  # demo-only; not a declared project dependency

    # Agg is a non-interactive backend, so plt.show() doesn't try to open a GUI window
    result = _run_script('networkx_demo.py', extra_env={'MPLBACKEND': 'Agg'})
    assert result.returncode == 0, result.stderr
