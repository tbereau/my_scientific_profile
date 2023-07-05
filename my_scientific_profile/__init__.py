"""Top-level package for My Scientific Profile."""

__author__ = """Tristan Bereau"""
__email__ = "bereau@thphys.uni-heidelberg.de"
__version__ = "0.1.0"

import confuse


__all__ = ["CONFIG"]

CONFIG = confuse.Configuration('my_scientific_profile', __name__)

