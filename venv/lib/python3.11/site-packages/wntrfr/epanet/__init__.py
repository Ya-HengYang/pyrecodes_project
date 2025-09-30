"""
The wntrfr.epanet package provides EPANET2 compatibility functions for wntrfr.
"""
from .io import InpFile  #, BinFile, HydFile, RptFile
from .util import FlowUnits, MassUnits, HydParam, QualParam, EN
from . import toolkit, io, util, exceptions
