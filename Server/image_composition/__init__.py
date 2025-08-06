"""
Image composition package for Smart Dashboard Server.

This package contains modules for creating and manipulating images:
- overlay: Information overlay creation and positioning
- fonts: Font management and cross-platform compatibility
- utils: Image utilities and transformations
"""

from .overlay import OverlayComposer
from .fonts import FontManager

__all__ = ['OverlayComposer', 'FontManager']
