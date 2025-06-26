"""
Database Models

SQLAlchemy ORM models for the clab-tools database.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Node(Base):
    """Node model representing network devices."""

    __tablename__ = "nodes"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    kind: Mapped[str] = Column(String(100), nullable=False)
    mgmt_ip: Mapped[str] = Column(String(45), nullable=False)  # IPv4/IPv6 address
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    connections_as_node1: Mapped[List["Connection"]] = relationship(
        "Connection",
        foreign_keys="Connection.node1_name",
        back_populates="node1_ref",
        cascade="all, delete-orphan",
    )
    connections_as_node2: Mapped[List["Connection"]] = relationship(
        "Connection",
        foreign_keys="Connection.node2_name",
        back_populates="node2_ref",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Node(name='{self.name}', kind='{self.kind}', mgmt_ip='{self.mgmt_ip}')>"
        )

    def to_dict(self) -> dict:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "mgmt_ip": self.mgmt_ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Connection(Base):
    """Connection model representing links between nodes."""

    __tablename__ = "connections"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    node1_name: Mapped[str] = Column(
        String(255), ForeignKey("nodes.name", ondelete="CASCADE"), nullable=False
    )
    node2_name: Mapped[str] = Column(
        String(255), ForeignKey("nodes.name", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = Column(String(50), nullable=False)
    node1_interface: Mapped[str] = Column(String(100), nullable=False)
    node2_interface: Mapped[str] = Column(String(100), nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    node1_ref: Mapped["Node"] = relationship(
        "Node", foreign_keys=[node1_name], back_populates="connections_as_node1"
    )
    node2_ref: Mapped["Node"] = relationship(
        "Node", foreign_keys=[node2_name], back_populates="connections_as_node2"
    )

    def __repr__(self) -> str:
        return (
            f"<Connection(node1='{self.node1_name}', "
            f"node2='{self.node2_name}', type='{self.type}')>"
        )

    def to_dict(self) -> dict:
        """Convert connection to dictionary representation."""
        return {
            "id": self.id,
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
    name: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    prefix: Mapped[Optional[str]] = Column(String(100))
    mgmt_network: Mapped[Optional[str]] = Column(String(100))
    mgmt_subnet: Mapped[Optional[str]] = Column(String(45))
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<TopologyConfig(name='{self.name}', prefix='{self.prefix}')>"

    def to_dict(self) -> dict:
        """Convert topology config to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix,
            "mgmt_network": self.mgmt_network,
            "mgmt_subnet": self.mgmt_subnet,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
