"""
# Protocol implementation for explicit factor isolation.
"""
import typing
import collections
import itertools
import json

from ..context.types import Cell
from ..route.types import Segment, Selector
from ..system import files

from . import types
