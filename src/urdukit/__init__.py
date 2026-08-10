"""urdukit -- a modern, dependency-free NLP toolkit for Urdu.

    >>> import urdukit
    >>> urdukit.normalize("مُحَمَّد علي")
    'محمد علی'

Design note
-----------
This module imports nothing outside the standard library, and every
submodule it touches does the same. That is a deliberate, load-bearing
constraint rather than a stylistic preference.

The previous de-facto Urdu library, ``urduhack``, declared TensorFlow as an
*optional* extra but imported it unconditionally from its package
``__init__``. The result was that ``pip install urduhack; import urduhack``
raised ``ModuleNotFoundError: No module named 'tensorflow'`` -- the package
could not be imported at all without a ~600 MB optional dependency. Six
years of issue reports (#153, #155, #144, #142, #107) trace back to that one
line. Any future model-backed feature here must be lazily imported inside
the function that needs it, never at module scope.
"""

from .characters import is_urdu_character
from .normalization import (
    collapse_whitespace,
    expand_ligatures,
    fold_arabic,
    is_normalized,
    normalize,
    normalize_digits,
    normalize_punctuation,
    normalize_unicode,
    remove_diacritics,
    remove_invisible,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "is_urdu_character",
    "normalize",
    "normalize_unicode",
    "fold_arabic",
    "remove_diacritics",
    "expand_ligatures",
    "normalize_digits",
    "normalize_punctuation",
    "remove_invisible",
    "collapse_whitespace",
    "is_normalized",
]
