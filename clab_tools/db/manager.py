"""
Database Manager

Handles SQLAlchemy database operations for storing topology data including
nodes, connections, and topology configurations with multi-lab support.
"""

from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from ..config.settings import DatabaseSettings
from ..errors.exceptions import DatabaseError
from ..errors.handlers import handle_database_errors
from ..log_config.logger import LoggerMixin, log_function_call
from .models import Base, Connection, Lab, Node, TopologyConfig


class DatabaseManager(LoggerMixin):
    """
    Manages SQLAlchemy database operations for topology data with
    multi-lab support.
    """

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
    def get_session(self):
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

    def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            self.logger.debug("Database health check passed")
            return True
        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return False

    # Lab Management Methods

    @handle_database_errors
    @log_function_call
    def get_or_create_lab(
        self, lab_name: str, description: Optional[str] = None
    ) -> Lab:
        """Get existing lab or create new one if it doesn't exist."""
        with self.get_session() as session:
            lab = session.query(Lab).filter_by(name=lab_name).first()

            if not lab:
                lab = Lab(name=lab_name, description=description)
                session.add(lab)
                session.flush()  # Get the lab ID
                self.logger.info("Created new lab", name=lab_name, id=lab.id)
            else:
                self.logger.debug("Using existing lab", name=lab_name, id=lab.id)

            # Return a detached instance but ensure attributes are loaded
            session.expunge(lab)
            return lab

    @handle_database_errors
    @log_function_call
    def list_labs(self) -> List[Lab]:
        """Get all labs from the database."""
        with self.get_session() as session:
            labs = session.query(Lab).order_by(Lab.name).all()

            # Access attributes while session is active to avoid DetachedInstanceError
            for lab in labs:
                # Force loading of attributes
                _ = lab.id, lab.name, lab.description, lab.created_at, lab.updated_at
                # Detach from session to avoid future lazy loading issues
                session.expunge(lab)

            self.logger.debug("Retrieved labs", count=len(labs))
            return labs

    @handle_database_errors
    @log_function_call
    def delete_lab(self, lab_name: str) -> bool:
        """Delete a lab and all its associated data."""
        with self.get_session() as session:
            lab = session.query(Lab).filter_by(name=lab_name).first()
            if lab:
                session.delete(lab)
                self.logger.info("Deleted lab and all associated data", name=lab_name)
                return True
            else:
                self.logger.warning("Lab not found for deletion", name=lab_name)
                return False

    @handle_database_errors
    @log_function_call
    def get_lab_stats(self, lab_name: str) -> Dict[str, int]:
        """Get statistics for a specific lab."""
        with self.get_session() as session:
            lab = session.query(Lab).filter_by(name=lab_name).first()
            if not lab:
                return {"error": "Lab not found"}

            nodes_count = session.query(Node).filter_by(lab_id=lab.id).count()
            connections_count = (
                session.query(Connection).filter_by(lab_id=lab.id).count()
            )
            topologies_count = (
                session.query(TopologyConfig).filter_by(lab_id=lab.id).count()
            )

            return {
                "nodes": nodes_count,
                "connections": connections_count,
                "topologies": topologies_count,
            }

    # Multi-Lab First Data Operations (all operations require lab context)

    @handle_database_errors
    @log_function_call
    def clear_nodes(self, lab_name: str) -> bool:
        """Clear all nodes from the specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            deleted_count = session.query(Node).filter_by(lab_id=lab.id).delete()
            self.logger.info(
                "Cleared nodes from lab", lab=lab_name, count=deleted_count
            )
            return True

    @handle_database_errors
    @log_function_call
    def clear_connections(self, lab_name: str) -> bool:
        """Clear all connections from the specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            deleted_count = session.query(Connection).filter_by(lab_id=lab.id).delete()
            self.logger.info(
                "Cleared connections from lab", lab=lab_name, count=deleted_count
            )
            return True

    @handle_database_errors
    @log_function_call
    def insert_node(self, name: str, kind: str, mgmt_ip: str, lab_name: str) -> bool:
        """Insert or update a node in the specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)

            # Check if node exists in this lab
            existing_node = (
                session.query(Node).filter_by(name=name, lab_id=lab.id).first()
            )

            if existing_node:
                # Update existing node
                existing_node.kind = kind
                existing_node.mgmt_ip = mgmt_ip
                self.logger.info(
                    "Updated existing node",
                    name=name,
                    kind=kind,
                    mgmt_ip=mgmt_ip,
                    lab=lab_name,
                )
            else:
                # Create new node
                new_node = Node(name=name, kind=kind, mgmt_ip=mgmt_ip, lab_id=lab.id)
                session.add(new_node)
                self.logger.info(
                    "Inserted new node",
                    name=name,
                    kind=kind,
                    mgmt_ip=mgmt_ip,
                    lab=lab_name,
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
        lab_name: str,
    ) -> bool:
        """Insert a connection into the specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)

            # Verify both nodes exist in this lab
            node1_exists = (
                session.query(Node).filter_by(name=node1, lab_id=lab.id).first()
            )
            node2_exists = (
                session.query(Node).filter_by(name=node2, lab_id=lab.id).first()
            )

            if not node1_exists:
                raise DatabaseError(
                    f"Node '{node1}' does not exist in lab '{lab_name}'",
                    operation="insert_connection",
                )
            if not node2_exists:
                raise DatabaseError(
                    f"Node '{node2}' does not exist in lab '{lab_name}'",
                    operation="insert_connection",
                )

            new_connection = Connection(
                node1_name=node1,
                node2_name=node2,
                type=conn_type,
                node1_interface=node1_interface,
                node2_interface=node2_interface,
                lab_id=lab.id,
            )
            session.add(new_connection)

            self.logger.info(
                "Inserted connection",
                node1=node1,
                node2=node2,
                type=conn_type,
                node1_interface=node1_interface,
                node2_interface=node2_interface,
                lab=lab_name,
            )
            return True

    @handle_database_errors
    @log_function_call
    def get_all_nodes(self, lab_name: str) -> List[Tuple[str, str, str]]:
        """Retrieve all nodes from the specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            nodes = (
                session.query(Node.name, Node.kind, Node.mgmt_ip)
                .filter(Node.lab_id == lab.id)
                .order_by(Node.name)
                .all()
            )
            self.logger.debug(
                "Retrieved nodes from lab", lab=lab_name, count=len(nodes)
            )
            return nodes

    @handle_database_errors
    @log_function_call
    def get_all_connections(
        self, lab_name: str
    ) -> List[Tuple[str, str, str, str, str]]:
        """Retrieve all connections from the specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            connections = (
                session.query(
                    Connection.node1_name,
                    Connection.node2_name,
                    Connection.type,
                    Connection.node1_interface,
                    Connection.node2_interface,
                )
                .filter(Connection.lab_id == lab.id)
                .order_by(Connection.node1_name, Connection.node2_name)
                .all()
            )
            self.logger.debug(
                "Retrieved connections from lab", lab=lab_name, count=len(connections)
            )
            return connections

    @handle_database_errors
    @log_function_call
    def save_topology_config(
        self, name: str, prefix: str, mgmt_network: str, mgmt_subnet: str, lab_name: str
    ) -> bool:
        """Save topology configuration to specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)

            # Check if config exists in this lab
            existing_config = (
                session.query(TopologyConfig)
                .filter_by(name=name, lab_id=lab.id)
                .first()
            )

            if existing_config:
                # Update existing config
                existing_config.prefix = prefix
                existing_config.mgmt_network = mgmt_network
                existing_config.mgmt_subnet = mgmt_subnet
                self.logger.info("Updated topology config", name=name, lab=lab_name)
            else:
                # Create new config
                new_config = TopologyConfig(
                    name=name,
                    prefix=prefix,
                    mgmt_network=mgmt_network,
                    mgmt_subnet=mgmt_subnet,
                    lab_id=lab.id,
                )
                session.add(new_config)
                self.logger.info("Created topology config", name=name, lab=lab_name)

            return True

    @handle_database_errors
    @log_function_call
    def get_topology_config(
        self, name: str, lab_name: str
    ) -> Optional[Tuple[str, str, str]]:
        """Retrieve topology configuration from specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            config = (
                session.query(
                    TopologyConfig.prefix,
                    TopologyConfig.mgmt_network,
                    TopologyConfig.mgmt_subnet,
                )
                .filter_by(name=name, lab_id=lab.id)
                .first()
            )

            if config:
                self.logger.debug("Retrieved topology config", name=name, lab=lab_name)
            else:
                self.logger.debug("Topology config not found", name=name, lab=lab_name)

            return config

    @handle_database_errors
    @log_function_call
    def get_node_by_name(self, name: str, lab_name: str) -> Optional[Node]:
        """Get a node by name from specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            node = session.query(Node).filter_by(name=name, lab_id=lab.id).first()
            if node:
                # Ensure all attributes are loaded before session closes
                _ = node.name, node.kind, node.mgmt_ip, node.created_at
                session.expunge(node)  # Detach from session
            return node

    @handle_database_errors
    @log_function_call
    def delete_node(self, name: str, lab_name: str) -> bool:
        """Delete a node and its connections from specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            node = session.query(Node).filter_by(name=name, lab_id=lab.id).first()
            if node:
                session.delete(node)
                self.logger.info("Deleted node", name=name, lab=lab_name)
                return True
            else:
                self.logger.warning(
                    "Node not found for deletion", name=name, lab=lab_name
                )
                return False

    @handle_database_errors
    @log_function_call
    def get_nodes_by_kind(self, kind: str, lab_name: str) -> List[Node]:
        """Get all nodes of a specific kind from specified lab."""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            nodes = (
                session.query(Node)
                .filter_by(kind=kind, lab_id=lab.id)
                .order_by(Node.name)
                .all()
            )
            # Ensure all attributes are loaded before session closes
            for node in nodes:
                _ = node.name, node.kind, node.mgmt_ip, node.created_at
                session.expunge(node)  # Detach from session
            self.logger.debug(
                "Retrieved nodes by kind", kind=kind, lab=lab_name, count=len(nodes)
            )
            return nodes

    @handle_database_errors
    @log_function_call
    def get_stats(self, lab_name: str = None) -> Dict[str, int]:
        """Get database statistics, optionally for a specific lab."""
        with self.get_session() as session:
            if lab_name:
                # Get stats for specific lab
                lab = self.get_or_create_lab(lab_name)
                node_count = session.query(Node).filter(Node.lab_id == lab.id).count()
                connection_count = (
                    session.query(Connection)
                    .filter(Connection.lab_id == lab.id)
                    .count()
                )
                config_count = (
                    session.query(TopologyConfig)
                    .filter(TopologyConfig.lab_id == lab.id)
                    .count()
                )

                stats = {
                    "nodes": node_count,
                    "connections": connection_count,
                    "configs": config_count,
                }
                self.logger.debug("Retrieved lab stats", lab=lab_name, **stats)
            else:
                # Get global stats across all labs
                lab_count = session.query(Lab).count()
                node_count = session.query(Node).count()
                connection_count = session.query(Connection).count()
                config_count = session.query(TopologyConfig).count()

                stats = {
                    "labs": lab_count,
                    "nodes": node_count,
                    "connections": connection_count,
                    "configs": config_count,
                }
                self.logger.debug("Retrieved database stats", **stats)

            return stats
