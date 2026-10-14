# Licence scope, source rights and attribution

This project's original software and original documentation are licensed under
the [MIT licence](LICENSE), Copyright (c) 2026 Prasanna K. This includes original
Python source, tests, notebooks, workflows and dependency specification files.

The original-code grant does not relicense third-party libraries, model weights,
source reports, datasets, benchmark records or quoted source material. Existing
per-file copyright notices, upstream licences and source-provider conditions
continue to apply to that material. In a mixed file, the grant covers only the
project's original contribution. Public accessibility is not a substitute for
the applicable upstream terms, and no source-provider endorsement is implied.

The source-specific boundaries below remain separate from the MIT code licence.

## Public reserving samples

The public RAA, ABC, GenIns, UK Motor and USAA samples are attributed to [casact/chainladder-python at the pinned upstream commit](https://github.com/casact/chainladder-python/tree/856f87b5651004c799cf06704b8a9c3f7dd61d98/chainladder/utils/data). Retain [data/LICENSE-MPL-2.0.txt](data/LICENSE-MPL-2.0.txt), the existing [predictive-reserving notice](data/predictive_reserving/NOTICE.md) and [RAA source notice](data/RAA_SOURCE_NOTICE.md) with the corresponding files. These upstream file notices do not apply a blanket MPL licence to independently implemented portfolio code.

The [source receipt](reference/predictive_reserving/source_receipt.json) identifies the four predictive samples and their original units. The RAA comparison now independently verifies all 55 cells against the pinned upstream CSV; its extra terminal newline is recorded rather than called byte-identical. Different measures from the same insurer are not independent datasets.

## Synthetic benefits and calibration inputs

The employee population, deterministic benefits claims demonstration and registered simulation triangles are generated research inputs. They are not private employee records, insurer/client data, qualified valuations or professional actuarial credentials. Their provenance is separate from the public reserving samples.

The project-created synthetic benefits input files and formula-driven benefits
workbook are included in the original-project MIT grant. The attributed public
reserving samples and their upstream notices remain under their existing terms.
