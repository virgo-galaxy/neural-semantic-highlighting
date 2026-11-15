# INI dataset

Original Git commit/tree/blob captures and upstream licenses remain under
`~/Datasets/neural-semantic-highlighting/ini`. Fixed path-hash bounded selection
covers Fail2ban, Geany, Meson, CPython and setuptools configurations. Known INI
source paths allow their original .conf/filetypes/cross filenames without mapping
every such extension to INI. Test/fixture/vendor/generated roots are excluded;
parser/range/structure validation happens before selection, with rejected
candidates retained in inventory. Source is never executed or loaded as settings.

40 original configuration families have 24 variants each: 960 files separate
from the 40 hand-marked Golden cases, focused teacher regressions and eight
Playground probes. Exact/lexical/structural copy audits run before windowing,
source families freeze before training, and natural/focus evidence stays separate.
Every corpus, Gold, prepared snapshot, prior run and formal model is preserved.

`make dataset-ini-tools` records the existing Python/ConfigParser/teacher hashes,
without downloads or installs. `make dataset-ini` follows the established external
paths and immutable pipeline. Resume full optimizer/RNG checkpoints only under
artifacts/ini; inference .pt/ONNX are never continuation checkpoints.
