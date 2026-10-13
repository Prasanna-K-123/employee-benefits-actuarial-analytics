# Source rights and attribution

This repository is publicly inspectable portfolio research. No project-wide open-source licence has been applied to its original project files. Public visibility does not itself grant a general right to redistribute or relicense them; GitHub's platform terms and any applicable per-file licences remain separate. See [GitHub's licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

This notice records source boundaries. It grants no additional rights and does not replace an upstream licence.

## Public reserving samples

The public RAA, ABC, GenIns, UK Motor and USAA samples are attributed to [casact/chainladder-python at the pinned upstream commit](https://github.com/casact/chainladder-python/tree/856f87b5651004c799cf06704b8a9c3f7dd61d98/chainladder/utils/data). Retain [data/LICENSE-MPL-2.0.txt](data/LICENSE-MPL-2.0.txt), the existing [predictive-reserving notice](data/predictive_reserving/NOTICE.md) and [RAA source notice](data/RAA_SOURCE_NOTICE.md) with the corresponding files. These upstream file notices do not apply a blanket MPL licence to independently implemented portfolio code.

The [source receipt](reference/predictive_reserving/source_receipt.json) identifies the four predictive samples and their original units. The RAA comparison now independently verifies all 55 cells against the pinned upstream CSV; its extra terminal newline is recorded rather than called byte-identical. Different measures from the same insurer are not independent datasets.

## Synthetic benefits and calibration inputs

The employee population, deterministic benefits claims demonstration and registered simulation triangles are generated research inputs. They are not private employee records, insurer/client data, qualified valuations or professional actuarial credentials. Their provenance is separate from the public reserving samples.
