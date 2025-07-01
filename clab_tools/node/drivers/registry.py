"""Driver registry for vendor detection and routing."""

import logging
from typing import Dict, List, Optional, Type

from clab_tools.node.drivers.base import BaseNodeDriver, ConnectionParams

logger = logging.getLogger(__name__)


class DriverRegistry:
    """Registry for managing vendor-specific drivers."""

    _drivers: Dict[str, Type[BaseNodeDriver]] = {}
    _vendor_mappings: Dict[str, str] = {}
    _device_type_mappings: Dict[str, str] = {}

    @classmethod
    def register_driver(
        cls, driver_class: Type[BaseNodeDriver], name: Optional[str] = None
    ) -> None:
        """Register a driver class.

        Args:
            driver_class: Driver class to register
            name: Optional driver name (defaults to class name)
        """
        driver_name = name or driver_class.__name__
        cls._drivers[driver_name] = driver_class

        # Register vendor mappings
        for vendor in driver_class.get_supported_vendors():
            cls._vendor_mappings[vendor.lower()] = driver_name

        # Register device type mappings
        for device_type in driver_class.get_supported_device_types():
            cls._device_type_mappings[device_type.lower()] = driver_name

        logger.debug(f"Registered driver: {driver_name}")
        logger.debug(f"Vendor mappings: {cls._vendor_mappings}")
        logger.debug(f"Device type mappings: {cls._device_type_mappings}")

    @classmethod
    def get_driver_class(cls, name: str) -> Optional[Type[BaseNodeDriver]]:
        """Get driver class by name.

        Args:
            name: Driver name

        Returns:
            Driver class or None if not found
        """
        return cls._drivers.get(name)

    @classmethod
    def get_driver_by_vendor(cls, vendor: str) -> Optional[Type[BaseNodeDriver]]:
        """Get driver class by vendor name.

        Args:
            vendor: Vendor name

        Returns:
            Driver class or None if not found
        """
        driver_name = cls._vendor_mappings.get(vendor.lower())
        if driver_name:
            return cls._drivers.get(driver_name)
        return None

    @classmethod
    def get_driver_by_device_type(
        cls, device_type: str
    ) -> Optional[Type[BaseNodeDriver]]:
        """Get driver class by device type.

        Args:
            device_type: Device type

        Returns:
            Driver class or None if not found
        """
        logger.debug(f"Looking for device_type: {device_type}")
        logger.debug(
            f"Available device types: {list(cls._device_type_mappings.keys())}"
        )
        driver_name = cls._device_type_mappings.get(device_type.lower())
        logger.debug(f"Found driver_name: {driver_name}")
        if driver_name:
            return cls._drivers.get(driver_name)
        return None

    @classmethod
    def create_driver(cls, connection_params: ConnectionParams) -> BaseNodeDriver:
        """Create driver instance based on connection parameters.

        Args:
            connection_params: Connection parameters

        Returns:
            Driver instance

        Raises:
            ValueError: If no suitable driver found
        """
        # Try vendor first
        if connection_params.vendor:
            driver_class = cls.get_driver_by_vendor(connection_params.vendor)
            if driver_class:
                return driver_class(connection_params)

        # Try device type
        if connection_params.device_type:
            driver_class = cls.get_driver_by_device_type(connection_params.device_type)
            if driver_class:
                return driver_class(connection_params)

        # No suitable driver found
        raise ValueError(
            f"No driver found for vendor='{connection_params.vendor}', "
            f"device_type='{connection_params.device_type}'"
        )

    @classmethod
    def list_drivers(cls) -> List[str]:
        """List all registered driver names.

        Returns:
            List of driver names
        """
        return list(cls._drivers.keys())

    @classmethod
    def list_supported_vendors(cls) -> List[str]:
        """List all supported vendors.

        Returns:
            List of vendor names
        """
        return list(cls._vendor_mappings.keys())

    @classmethod
    def list_supported_device_types(cls) -> List[str]:
        """List all supported device types.

        Returns:
            List of device types
        """
        return list(cls._device_type_mappings.keys())

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered drivers."""
        cls._drivers.clear()
        cls._vendor_mappings.clear()
        cls._device_type_mappings.clear()


def register_driver(name: Optional[str] = None):
    """Decorator to register a driver class.

    Args:
        name: Optional driver name

    Returns:
        Decorator function
    """

    def decorator(driver_class: Type[BaseNodeDriver]):
        DriverRegistry.register_driver(driver_class, name)
        return driver_class

    return decorator
