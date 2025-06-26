"""
Database Manager

Handles SQLAlchemy database operations for storing topology data including
nodes, connections, and topology configurations.
"""

from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ..config.settings import DatabaseSettings
from ..errors.exceptions import DatabaseError
from ..errors.handlers import handle_database_errors
from ..log_config.logger import LoggerMixin, log_function_call
from .models import Base, Connection, Node, TopologyConfig


class DatabaseManager(LoggerMixin):
    """Manages SQLAlchemy database operations for topology data."""

    def __init__(
        self, settings: Optional[DatabaseSettings] = None, db_url: Optional[str] = None
    ):
        """
        Initialize database manager.

        Args:
            settings: Database settings object
            db_url: Direct database URL (overrides settings)
        """
        if db_url:
            self.db_url = db_url
        elif settings:
            self.db_url = settings.url
        else:
            # Fallback to default SQLite
            self.db_url = "sqlite:///clab_topology.db"

        self.settings = settings
        self.engine = create_engine(
            self.db_url,
            echo=settings.echo if settings else False,
            pool_pre_ping=settings.pool_pre_ping if settings else True,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Initialize database
        self.init_database()

    @log_function_call
    def init_database(self):
        """Initialize the database with required tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database initialized successfully")
        except SQLAlchemyError as e:
            raise DatabaseError(
                "Failed to initialize database",
                operation="init_database",
                original_error=e,
            )

    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @handle_database_errors
    @log_function_call
    def clear_nodes(self) -> bool:
        """Clear all nodes from the database."""
        with self.get_session() as session:
            deleted_count = session.query(Node).delete()
            self.logger.info("Cleared nodes from database", count=deleted_count)
            return True

    @handle_database_errors
    @log_function_call
    def clear_connections(self) -> bool:
        """Clear all connections from the database."""
        with self.get_session() as session:
            deleted_count = session.query(Connection).delete()
            self.logger.info("Cleared connections from database", count=deleted_count)
            return True

    @handle_database_errors
    @log_function_call
    def insert_node(self, name: str, kind: str, mgmt_ip: str) -> bool:
        """Insert or update a node in the database."""
        with self.get_session() as session:
            # Check if node exists
            existing_node = session.query(Node).filter_by(name=name).first()

            if existing_node:
                # Update existing node
                existing_node.kind = kind
                existing_node.mgmt_ip = mgmt_ip
                self.logger.info(
                    "Updated existing node", name=name, kind=kind, mgmt_ip=mgmt_ip
                )
            else:
                # Create new node
                new_node = Node(name=name, kind=kind, mgmt_ip=mgmt_ip)
                session.add(new_node)
                self.logger.info(
                    "Inserted new node", name=name, kind=kind, mgmt_ip=mgmt_ip
                )

            return True

    @handle_database_errors
    @log_function_call
    def insert_connection(
        self,
        node1: str,
        node2: str,
        conn_type: str,
        node1_interface: str,
        node2_interface: str,
    ) -> bool:
        """Insert a connection into the database."""
        with self.get_session() as session:
            # Verify both nodes exist
            node1_exists = session.query(Node).filter_by(name=node1).first()
            node2_exists = session.query(Node).filter_by(name=node2).first()

            if not node1_exists:
                raise DatabaseError(
                    f"Node '{node1}' does not exist", operation="insert_connection"
                )
            if not node2_exists:
                raise DatabaseError(
                    f"Node '{node2}' does not exist", operation="insert_connection"
                )

            new_connection = Connection(
                node1_name=node1,
                node2_name=node2,
                type=conn_type,
                node1_interface=node1_interface,
                node2_interface=node2_interface,
            )
            session.add(new_connection)

            self.logger.info(
                "Inserted connection",
                node1=node1,
                node2=node2,
                type=conn_type,
                node1_interface=node1_interface,
                node2_interface=node2_interface,
            )
            return True

    @handle_database_errors
    @log_function_call
    def get_all_nodes(self) -> List[Tuple[str, str, str]]:
        """Retrieve all nodes from the database."""
        with self.get_session() as session:
            nodes = (
                session.query(Node.name, Node.kind, Node.mgmt_ip)
                .order_by(Node.name)
                .all()
            )
            self.logger.debug("Retrieved nodes from database", count=len(nodes))
            return nodes

    @handle_database_errors
    @log_function_call
    def get_all_connections(self) -> List[Tuple[str, str, str, str, str]]:
        """Retrieve all connections from the database."""
        with self.get_session() as session:
            connections = (
                session.query(
                    Connection.node1_name,
                    Connection.node2_name,
                    Connection.type,
                    Connection.node1_interface,
                    Connection.node2_interface,
                )
                .order_by(Connection.node1_name, Connection.node2_name)
                .all()
            )
            self.logger.debug(
                "Retrieved connections from database", count=len(connections)
            )
            return connections

    @handle_database_errors
    @log_function_call
    def save_topology_config(
        self, name: str, prefix: str, mgmt_network: str, mgmt_subnet: str
    ) -> bool:
        """Save topology configuration to database."""
        with self.get_session() as session:
            # Check if config exists
            existing_config = session.query(TopologyConfig).filter_by(name=name).first()

            if existing_config:
                # Update existing config
                existing_config.prefix = prefix
                existing_config.mgmt_network = mgmt_network
                existing_config.mgmt_subnet = mgmt_subnet
                self.logger.info("Updated topology config", name=name)
            else:
                # Create new config
                new_config = TopologyConfig(
                    name=name,
                    prefix=prefix,
                    mgmt_network=mgmt_network,
                    mgmt_subnet=mgmt_subnet,
                )
                session.add(new_config)
                self.logger.info("Created topology config", name=name)

            return True

    @handle_database_errors
    @log_function_call
    def get_topology_config(self, name: str) -> Optional[Tuple[str, str, str]]:
        """Retrieve topology configuration from database."""
        with self.get_session() as session:
            config = (
                session.query(
                    TopologyConfig.prefix,
                    TopologyConfig.mgmt_network,
                    TopologyConfig.mgmt_subnet,
                )
                .filter_by(name=name)
                .first()
            )

            if config:
                self.logger.debug("Retrieved topology config", name=name)
            else:
                self.logger.debug("Topology config not found", name=name)

            return config

    @handle_database_errors
    @log_function_call
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.get_session() as session:
            node_count = session.query(Node).count()
            connection_count = session.query(Connection).count()
            config_count = session.query(TopologyConfig).count()

            stats = {
                "nodes": node_count,
                "connections": connection_count,
                "configs": config_count,
            }

            self.logger.debug("Retrieved database stats", **stats)
            return stats

    @handle_database_errors
    @log_function_call
    def get_node_by_name(self, name: str) -> Optional[Node]:
        """Get a node by name."""
        with self.get_session() as session:
            node = session.query(Node).filter_by(name=name).first()
            if node:
                # Ensure all attributes are loaded before session closes
                _ = node.name, node.kind, node.mgmt_ip, node.created_at
                session.expunge(node)  # Detach from session
            return node

    @handle_database_errors
    @log_function_call
    def delete_node(self, name: str) -> bool:
        """Delete a node and its connections."""
        with self.get_session() as session:
            node = session.query(Node).filter_by(name=name).first()
            if node:
                session.delete(node)
                self.logger.info("Deleted node", name=name)
                return True
            else:
                self.logger.warning("Node not found for deletion", name=name)
                return False

    @handle_database_errors
    @log_function_call
    def get_nodes_by_kind(self, kind: str) -> List[Node]:
        """Get all nodes of a specific kind."""
        with self.get_session() as session:
            nodes = session.query(Node).filter_by(kind=kind).order_by(Node.name).all()
            # Ensure all attributes are loaded before session closes
            for node in nodes:
                _ = node.name, node.kind, node.mgmt_ip, node.created_at
                session.expunge(node)  # Detach from session
            self.logger.debug("Retrieved nodes by kind", kind=kind, count=len(nodes))
            return nodes

    @handle_database_errors
    @log_function_call
    def health_check(self) -> bool:
        """Perform a database health check."""
        try:
            with self.get_session() as session:
                # Simple query to test connection
                session.execute(text("SELECT 1"))
                self.logger.info("Database health check passed")
                return True
        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return False
