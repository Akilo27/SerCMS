from .core_settings import *

# Импорт списка языков
from .language import LANGUAGES

try:
    from .local_settings import *
except ImportError:
    from .logging_settings import *
