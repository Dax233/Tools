# SPDX-License-Identifier: AGPL-3.0-or-later
"""让测试在未安装包的情况下也能 import formulacalc（把仓库根目录加入 sys.path）。"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
