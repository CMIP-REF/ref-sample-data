"""
REF sample data
"""

import importlib.metadata

__version__ = importlib.metadata.version("sample_data")


from .data_request.base import DataRequest
from .data_request.cmip6 import CMIP6Request
from .data_request.obs4mips import Obs4MIPsRequest

__all__ = ["DataRequest", "CMIP6Request", "Obs4MIPsRequest"]
