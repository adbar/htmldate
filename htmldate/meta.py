"""
Meta-functions to be applied module-wide.
"""

import logging

from .core import compare_reference
from .extractors import try_date_expr
from .validators import date_validator, filter_ymd_candidate, output_format_validator


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
    compare_reference.cache_clear()
    date_validator.cache_clear()
    filter_ymd_candidate.cache_clear()
    output_format_validator.cache_clear()
    try_date_expr.cache_clear()
    # charset_normalizer
    try:
        encoding_languages.cache_clear()
        is_suspiciously_successive_range.cache_clear()
        is_accentuated.cache_clear()
    # prevent possible changes in function names
    except (AttributeError, NameError) as err:  # pragma: no cover
        LOGGER.error("impossible to clear cache for function: %s", err)
