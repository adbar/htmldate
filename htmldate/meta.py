"""
Meta-functions to be applied module-wide.
"""

import logging

from .extractors import try_date_expr
from .validators import reset_validator_caches

LOGGER = logging.getLogger(__name__)


try:
    from charset_normalizer.cd import encoding_languages
    from charset_normalizer.md import is_suspiciously_successive_range
    from charset_normalizer.utils import is_accentuated
# prevent possible changes in function names
except ImportError:
    LOGGER.error("impossible to import charset function name")


def reset_caches() -> None:
    """Reset all known LRU caches used to speed-up processing.
    This may release some memory."""
    # htmldate
    reset_validator_caches()
    try_date_expr.cache_clear()
    # charset_normalizer internals: cache_clear may be absent depending on version
    # (getattr keeps mypy happy; the except still guards missing names/attrs)
    try:
        getattr(encoding_languages, "cache_clear")()
        getattr(is_suspiciously_successive_range, "cache_clear")()
        getattr(is_accentuated, "cache_clear")()
    except (AttributeError, NameError) as err:  # pragma: no cover
        LOGGER.error("impossible to clear cache for function: %s", err)
