"""Node drivers for vendor-specific operations."""

from clab_tools.node.drivers.base import (
    BaseNodeDriver,
    CommandResult,
    ConfigFormat,
    ConfigLoadMethod,
    ConfigResult,
    ConnectionParams,
)
from clab_tools.node.drivers.registry import DriverRegistry, register_driver

# Import drivers to register them
try:
    from clab_tools.node.drivers.juniper import JuniperPyEZDriver  # noqa: F401
except ImportError:
    # PyEZ not installed, skip registration
    pass

__all__ = [
    "BaseNodeDriver",
    "CommandResult",
    "ConfigFormat",
    "ConfigLoadMethod",
    "ConfigResult",
    "ConnectionParams",
    "DriverRegistry",
    "register_driver",
]
