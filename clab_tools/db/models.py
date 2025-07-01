"""
Database Models

SQLAlchemy ORM models for the clab-tools database.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Lab(Base):
    """Lab model representing different laboratory environments."""

    __tablename__ = "labs"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = Column(String(1000), nullable=True)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    nodes: Mapped[List["Node"]] = relationship(
        "Node", back_populates="lab", cascade="all, delete-orphan"
    )
    connections: Mapped[List["Connection"]] = relationship(
        "Connection", back_populates="lab", cascade="all, delete-orphan"
    )
    topology_configs: Mapped[List["TopologyConfig"]] = relationship(
        "TopologyConfig", back_populates="lab", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        # Safely access attributes without triggering lazy loading
        name = getattr(self, "name", "<pending>")
        description = getattr(self, "description", "<pending>")
        return f"<Lab(name='{name}', description='{description}')>"

    def to_dict(self) -> dict:
        """Convert lab to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Node(Base):
    """Node model representing network devices."""

    __tablename__ = "nodes"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    lab_id: Mapped[int] = Column(
        Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = Column(String(255), nullable=False, index=True)
    kind: Mapped[str] = Column(String(100), nullable=False)
    mgmt_ip: Mapped[str] = Column(String(45), nullable=False)  # IPv4/IPv6 address

    # New fields for node management
    vendor: Mapped[Optional[str]] = Column(String(100), nullable=True)
    model: Mapped[Optional[str]] = Column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = Column(String(100), nullable=True)
    username: Mapped[Optional[str]] = Column(String(100), nullable=True)
    password: Mapped[Optional[str]] = Column(String(255), nullable=True)
    ssh_port: Mapped[Optional[int]] = Column(Integer, nullable=True, default=22)

    # Configuration management fields
    last_config_load: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True
    )
    last_config_method: Mapped[Optional[str]] = Column(String(50), nullable=True)
    last_config_status: Mapped[Optional[str]] = Column(String(50), nullable=True)
    last_command_exec: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Unique constraint: node name must be unique within a lab
    __table_args__ = (UniqueConstraint("lab_id", "name", name="uq_lab_node_name"),)

    # Relationships
    lab: Mapped["Lab"] = relationship("Lab", back_populates="nodes")
    connections_as_node1: Mapped[List["Connection"]] = relationship(
        "Connection",
        primaryjoin=(
            "and_(Node.name == foreign(Connection.node1_name), "
            "Node.lab_id == foreign(Connection.lab_id))"
        ),
        back_populates="node1_ref",
        viewonly=True,
        overlaps="connections",
    )
    connections_as_node2: Mapped[List["Connection"]] = relationship(
        "Connection",
        primaryjoin=(
            "and_(Node.name == foreign(Connection.node2_name), "
            "Node.lab_id == foreign(Connection.lab_id))"
        ),
        back_populates="node2_ref",
        viewonly=True,
        overlaps="connections,connections_as_node1",
    )

    def __repr__(self) -> str:
        # Safely access attributes without triggering lazy loading
        lab_id = getattr(self, "lab_id", "<pending>")
        name = getattr(self, "name", "<pending>")
        kind = getattr(self, "kind", "<pending>")
        mgmt_ip = getattr(self, "mgmt_ip", "<pending>")
        return (
            f"<Node(lab_id={lab_id}, name='{name}', "
            f"kind='{kind}', mgmt_ip='{mgmt_ip}')>"
        )

    def to_dict(self) -> dict:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "lab_id": self.lab_id,
            "name": self.name,
            "kind": self.kind,
            "mgmt_ip": self.mgmt_ip,
            "vendor": self.vendor,
            "model": self.model,
            "os_version": self.os_version,
            "username": self.username,
            "ssh_port": self.ssh_port,
            "last_config_load": (
                self.last_config_load.isoformat() if self.last_config_load else None
            ),
            "last_config_method": self.last_config_method,
            "last_config_status": self.last_config_status,
            "last_command_exec": (
                self.last_command_exec.isoformat() if self.last_command_exec else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Connection(Base):
    """Connection model representing links between nodes."""

    __tablename__ = "connections"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    lab_id: Mapped[int] = Column(
        Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node1_name: Mapped[str] = Column(String(255), nullable=False)
    node2_name: Mapped[str] = Column(String(255), nullable=False)
    type: Mapped[str] = Column(String(50), nullable=False)
    node1_interface: Mapped[str] = Column(String(100), nullable=False)
    node2_interface: Mapped[str] = Column(String(100), nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    lab: Mapped["Lab"] = relationship(
        "Lab",
        back_populates="connections",
        overlaps="connections_as_node1,connections_as_node2",
    )
    node1_ref: Mapped[Optional["Node"]] = relationship(
        "Node",
        primaryjoin=(
            "and_(foreign(Connection.node1_name) == Node.name, "
            "foreign(Connection.lab_id) == Node.lab_id)"
        ),
        back_populates="connections_as_node1",
        viewonly=True,
    )
    node2_ref: Mapped[Optional["Node"]] = relationship(
        "Node",
        primaryjoin=(
            "and_(foreign(Connection.node2_name) == Node.name, "
            "foreign(Connection.lab_id) == Node.lab_id)"
        ),
        back_populates="connections_as_node2",
        viewonly=True,
    )

    def __repr__(self) -> str:
        # Safely access attributes without triggering lazy loading
        lab_id = getattr(self, "lab_id", "<pending>")
        node1_name = getattr(self, "node1_name", "<pending>")
        node2_name = getattr(self, "node2_name", "<pending>")
        conn_type = getattr(self, "type", "<pending>")
        return (
            f"<Connection(lab_id={lab_id}, node1='{node1_name}', "
            f"node2='{node2_name}', type='{conn_type}')>"
        )

    def to_dict(self) -> dict:
        """Convert connection to dictionary representation."""
        return {
            "id": self.id,
            "lab_id": self.lab_id,
            "node1": self.node1_name,
            "node2": self.node2_name,
            "type": self.type,
            "node1_interface": self.node1_interface,
            "node2_interface": self.node2_interface,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TopologyConfig(Base):
    """Topology configuration model."""

    __tablename__ = "topology_configs"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    lab_id: Mapped[int] = Column(
        Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = Column(String(255), nullable=False, index=True)
    prefix: Mapped[Optional[str]] = Column(String(100))
    mgmt_network: Mapped[Optional[str]] = Column(String(100))
    mgmt_subnet: Mapped[Optional[str]] = Column(String(45))
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Unique constraint: topology config name must be unique within a lab
    __table_args__ = (UniqueConstraint("lab_id", "name", name="uq_lab_topology_name"),)

    # Relationships
    lab: Mapped["Lab"] = relationship("Lab", back_populates="topology_configs")

    def __repr__(self) -> str:
        # Safely access attributes without triggering lazy loading
        lab_id = getattr(self, "lab_id", "<pending>")
        name = getattr(self, "name", "<pending>")
        prefix = getattr(self, "prefix", "<pending>")
        return f"<TopologyConfig(lab_id={lab_id}, name='{name}', prefix='{prefix}')>"

    def to_dict(self) -> dict:
        """Convert topology config to dictionary representation."""
        return {
            "id": self.id,
            "lab_id": self.lab_id,
            "name": self.name,
            "prefix": self.prefix,
            "mgmt_network": self.mgmt_network,
            "mgmt_subnet": self.mgmt_subnet,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
