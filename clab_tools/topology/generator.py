"""
Topology Generator

Handles the generation of containerlab topology files from database data
using Jinja2 templating.
"""

import sys
from collections import defaultdict
from pathlib import Path

import click
import yaml
from jinja2 import Environment, FileSystemLoader


class TopologyGenerator:
    """Generates containerlab topology files from database data."""

    def __init__(
        self,
        db_manager,
        template_file="topology_template.j2",
        kinds_file="supported_kinds.yaml",
    ):
        self.db = db_manager
        self.template_file = Path(template_file)
        self.kinds_file = Path(kinds_file)

    def load_supported_kinds(self):
        """Load supported device kinds from YAML configuration file."""
        try:
            with open(self.kinds_file, "r") as f:
                content = f.read()
                yaml_content = yaml.safe_load(content)
                if yaml_content is None:
                    return {
                        "juniper_vjunosrouter": "vrnetlab/vr-vjunosrouter:23.2R1.15"
                    }
                return yaml_content
        except FileNotFoundError:
            click.echo(
                f"Warning: Kinds file {self.kinds_file} not found, using defaults",
                err=True,
            )
            return {"juniper_vjunosrouter": "vrnetlab/vr-vjunosrouter:23.2R1.15"}
        except Exception as e:
            click.echo(f"Error loading kinds file {self.kinds_file}: {e}", err=True)
            return {"juniper_vjunosrouter": "vrnetlab/vr-vjunosrouter:23.2R1.15"}

    def generate_topology_data(self):
        """Generate topology data structure from database."""
        nodes = {}
        links = []
        bridges = set()
        bridge_counter = defaultdict(int)

        # Load nodes from database
        db_nodes = self.db.get_all_nodes()
        for name, kind, mgmt_ip in db_nodes:
            nodes[name] = {"kind": kind, "mgmt_ip": mgmt_ip}

        # Load connections from database and generate links
        db_connections = self.db.get_all_connections()
        for node1, node2, conn_type, node1_interface, node2_interface in db_connections:
            if conn_type == "direct":
                # Create direct connection
                link = {
                    "endpoints": [
                        {"node": node1, "interface": node1_interface},
                        {"node": node2, "interface": node2_interface},
                    ]
                }
                links.append(link)

            elif conn_type == "bridge":
                # Create bridge connection with unique name per connection
                bridge_counter[(node1, node2)] += 1

                # Create unique bridge name including interface identifiers
                node1_int_clean = node1_interface.replace("/", "").replace("-", "")
                node2_int_clean = node2_interface.replace("/", "").replace("-", "")
                bridge_name = f"br-{node1}-{node1_int_clean}-{node2}-{node2_int_clean}"

                bridges.add(bridge_name)

                # Add bridge to nodes if not already present
                if bridge_name not in nodes:
                    nodes[bridge_name] = {"kind": "bridge"}

                # Create connections to bridge
                bridge_int1 = f"eth{node1}-{node1_int_clean}"
                bridge_int2 = f"eth{node2}-{node2_int_clean}"

                link1 = {
                    "endpoints": [
                        {"node": node1, "interface": node1_interface},
                        {"node": bridge_name, "interface": bridge_int1},
                    ]
                }
                links.append(link1)

                link2 = {
                    "endpoints": [
                        {"node": node2, "interface": node2_interface},
                        {"node": bridge_name, "interface": bridge_int2},
                    ]
                }
                links.append(link2)

        return nodes, links, bridges

    def generate_topology_file(
        self, topology_name, prefix, mgmt_network, mgmt_subnet, output_file
    ):
        """
        Generate the containerlab topology YAML file using external Jinja2
        template.
        """

        # Generate topology data from database
        nodes, links, bridges = self.generate_topology_data()

        if not nodes:
            click.echo(
                "Warning: No nodes found in database. Generate an empty "
                "topology or import data first.",
                err=True,
            )

        # Load the Jinja2 template from file
        try:
            template_dir = self.template_file.parent
            template_name = self.template_file.name

            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template(template_name)

        except Exception as e:
            click.echo(f"Error loading template {self.template_file}: {e}", err=True)
            sys.exit(1)

        # Get unique kinds (excluding bridges)
        unique_kinds = set()
        for node_data in nodes.values():
            if node_data["kind"] != "bridge":
                unique_kinds.add(node_data["kind"])

        # Load supported kinds from configuration file
        kind_images = self.load_supported_kinds()

        # Create template and render
        rendered = template.render(
            topology_name=topology_name,
            prefix=prefix,
            mgmt_network=mgmt_network,
            mgmt_subnet=mgmt_subnet,
            nodes=nodes,
            links=links,
            unique_kinds=sorted(unique_kinds),
            kind_images=kind_images,
        )

        # Write to file
        try:
            output_path = Path(output_file)
            with open(output_path, "w") as f:
                f.write(rendered)
            click.echo(f"Successfully generated topology file: {output_path}")

            # Save topology config to database
            self.db.save_topology_config(
                topology_name, prefix, mgmt_network, mgmt_subnet
            )

            return True

        except Exception as e:
            click.echo(f"Error writing to {output_file}: {e}", err=True)
            return False

    def validate_yaml(self, yaml_file):
        """Validate YAML file syntax."""
        try:
            with open(yaml_file, "r") as f:
                yaml.safe_load(f)
            return True, "YAML file is valid"
        except yaml.YAMLError as e:
            return False, f"YAML syntax error: {e}"
        except Exception as e:
            return False, f"Error validating YAML: {e}"
