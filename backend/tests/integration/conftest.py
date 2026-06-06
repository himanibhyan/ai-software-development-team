from __future__ import annotations

import langchain

# Workaround for langchain 1.2.15 incompatibility with langchain-core:
# langchain_core.globals.get_debug() tries to access langchain.debug
# which does not exist in this version.
langchain.debug = False
