"""Logging helpers.

Library code in this package logs; it does not print. Notebooks call
:func:`setup_logging` once and then see module output inline.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False
_FORMAT = "%(levelname)-7s %(name)-24s %(message)s"


def setup_logging(level: int | str = logging.INFO, force: bool = False) -> None:
    """Attach a single stdout handler to the ``ml`` logger tree.

    Safe to call repeatedly; the handler is installed only once unless ``force``
    is set. Notebooks get re-run constantly, and without this guard every re-run
    would add another handler and duplicate every log line.
    """
    global _CONFIGURED
    logger = logging.getLogger("ml")
    if _CONFIGURED and not force:
        logger.setLevel(level)
        return

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger inside the ``ml`` namespace."""
    return logging.getLogger(name if name.startswith("ml") else f"ml.{name}")
