"""Run the unchanged registered oracle with NPZ arrays loaded once.

Execution-only performance amendment: NpzFile indexing re-decompressed the
entire artifact inside each interval loop. No forecast, rank, seed, summary,
formula, tolerance or comparison is changed. Study generation is not invoked.
"""
import json
import numpy as np
from verify_conformal_reserving import verify

original_load = np.load

def load_once(*args, **kwargs):
    result = original_load(*args, **kwargs)
    if isinstance(result, np.lib.npyio.NpzFile):
        try:
            return {name: result[name] for name in result.files}
        finally:
            result.close()
    return result

if __name__ == '__main__':
    np.load = load_once
    result = verify(replay_design=True)
    result['execution_amendment'] = 'NPZ arrays loaded once in memory; unchanged registered verifier/formulas/tolerances; no primary study rerun'
    print(json.dumps(result, indent=2))
