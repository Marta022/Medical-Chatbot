# TODO(remove-shim): remove after P2 stabilization.
from __future__ import annotations

import sys

from run import main as cli_main


def _ensure_default_chat() -> None:
    if len(sys.argv) == 1:
        sys.argv.append("chat")


if __name__ == "__main__":
    _ensure_default_chat()
    cli_main()
