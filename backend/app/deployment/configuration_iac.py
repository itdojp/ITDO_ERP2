"""
CC02 v78.0 Day 23: Enterprise Integrated Deployment & Operations Automation
Module 6: Configuration Management & Infrastructure as Code (IaC)

Advanced infrastructure automation with declarative configuration management,
multi-cloud resource provisioning, and GitOps-driven infrastructure deployment.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List

import jinja2
import yaml

from ..core.mobile_erp_sdk import MobileERPSDK


class CloudProvider(Enum):
    """Supported cloud providers"""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    TERRAFORM = "terraform"


class ResourceType(Enum):
    """Infrastructure resource types"""

    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    LOAD_BALANCER = "load_balancer"
    SECURITY_GROUP = "security_group"
    DNS = "dns"
    MONITORING = "monitoring"
    BACKUP = "backup"


class DeploymentState(Enum):
    """Deployment state tracking"""

    PLANNED = "planned"
    APPLYING = "applying"
    APPLIED = "applied"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    FAILED = "failed"
    DRIFTED = "drifted"


class ConfigurationSource(Enum):
    """Configuration source types"""

    GIT = "git"
    FILE = "file"
    DATABASE = "database"
    ENVIRONMENT = "environment"
    VAULT = "vault"
    CONFIG_MAP = "config_map"


@dataclass
class InfrastructureTemplate:
    """Infrastructure template definition"""

    id: str
    name: str
    provider: CloudProvider
    template_path: str
    variables: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class ConfigurationItem:
    """Configuration item definition"""

    id: str
    name: str
    source: ConfigurationSource
    path: str
    environment: str
    sensitive: bool = False
    encrypted: bool = False
    version: str = "latest"
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeploymentPlan:
    """Infrastructure deployment plan"""

    id: str
    name: str
    templates: List[str]
    target_environment: str
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    state: DeploymentState = DeploymentState.PLANNED
    resources_created: List[Dict[str, Any]] = field(default_factory=list)
    resources_updated: List[Dict[str, Any]] = field(default_factory=list)
    resources_destroyed: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DriftDetectionResult:
    """Infrastructure drift detection result"""

    template_id: str
    resource_id: str
    resource_type: str
    expected_state: Dict[str, Any]
    actual_state: Dict[str, Any]
    drift_detected: bool
    timestamp: datetime
    severity: str


class TemplateEngine:
    """Infrastructure template processing engine"""

    def __init__(self) -> dict:
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("."), undefined=jinja2.StrictUndefined
        )
        self.template_cache: Dict[str, str] = {}

    def render_template(self, template_path: str, variables: Dict[str, Any]) -> str:
        """Render infrastructure template with variables"""
        try:
            if template_path not in self.template_cache:
                with open(template_path, "r") as f:
                    self.template_cache[template_path] = f.read()

            template = self.jinja_env.from_string(self.template_cache[template_path])

            # Add built-in variables
            built_in_vars = {
                "timestamp": datetime.now().isoformat(),
                "environment": variables.get("environment", "default"),
                "region": variables.get("region", "us-east-1"),
            }

            all_variables = {**built_in_vars, **variables}

            rendered = template.render(**all_variables)
            return rendered

        except Exception as e:
            logging.error(f"Template rendering failed: {template_path} - {e}")
            raise

    def validate_template(self, template_path: str, variables: Dict[str, Any]) -> bool:
        """Validate template syntax and variables"""
        try:
            self.render_template(template_path, variables)
            return True
        except Exception as e:
            logging.error(f"Template validation failed: {e}")
            return False

    def extract_variables(self, template_path: str) -> List[str]:
        """Extract required variables from template"""
        try:
            with open(template_path, "r") as f:
                content = f.read()

            template = self.jinja_env.from_string(content)

            # Get undefined variables (this is a simplified approach)
            variables = []
            for node in template.environment.parse(content).find_all(jinja2.nodes.Name):
                if node.name not in ["timestamp", "environment", "region"]:
                    variables.append(node.name)

            return list(set(variables))

        except Exception as e:
            logging.error(f"Variable extraction failed: {e}")
            return []


class ConfigurationManager:
    """Advanced configuration management system"""

    def __init__(self) -> dict:
        self.configurations: Dict[str, ConfigurationItem] = {}
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.config_watchers: Dict[str, Callable] = {}
        self.encryption_key = self._generate_encryption_key()

    def _generate_encryption_key(self) -> str:
        """Generate encryption key for sensitive configurations"""
        return hashlib.sha256(b"itdo_erp_config_key").hexdigest()

    def add_configuration(self, config_item: ConfigurationItem) -> dict:
        """Add configuration item"""
        self.configurations[config_item.id] = config_item
        logging.info(f"Added configuration: {config_item.name}")

    def remove_configuration(self, config_id: str) -> dict:
        """Remove configuration item"""
        if config_id in self.configurations:
            del self.configurations[config_id]
            if config_id in self.config_cache:
                del self.config_cache[config_id]
            logging.info(f"Removed configuration: {config_id}")

    async def load_configuration(self, config_id: str) -> Dict[str, Any]:
        """Load configuration from source"""
        if config_id not in self.configurations:
            raise ValueError(f"Configuration not found: {config_id}")

        config_item = self.configurations[config_id]

        try:
            if config_item.source == ConfigurationSource.FILE:
                return await self._load_file_config(config_item)
            elif config_item.source == ConfigurationSource.GIT:
                return await self._load_git_config(config_item)
            elif config_item.source == ConfigurationSource.ENVIRONMENT:
                return await self._load_env_config(config_item)
            elif config_item.source == ConfigurationSource.VAULT:
                return await self._load_vault_config(config_item)
            else:
                raise ValueError(
                    f"Unsupported configuration source: {config_item.source}"
                )

        except Exception as e:
            logging.error(f"Configuration loading failed: {config_id} - {e}")
            raise

    async def _load_file_config(self, config_item: ConfigurationItem) -> Dict[str, Any]:
        """Load configuration from file"""
        file_path = Path(config_item.path)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_item.path}")

        with open(file_path, "r") as f:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                config_data = yaml.safe_load(f)
            elif file_path.suffix.lower() == ".json":
                config_data = json.load(f)
            else:
                config_data = {"content": f.read()}

        if config_item.encrypted:
            config_data = self._decrypt_config(config_data)

        self.config_cache[config_item.id] = config_data
        return config_data

    async def _load_git_config(self, config_item: ConfigurationItem) -> Dict[str, Any]:
        """Load configuration from Git repository"""
        # Simplified Git config loading
        # In production, this would clone/pull from actual Git repos

        config_data = {
            "git_url": config_item.path,
            "version": config_item.version,
            "environment": config_item.environment,
            "loaded_at": datetime.now().isoformat(),
        }

        self.config_cache[config_item.id] = config_data
        return config_data

    async def _load_env_config(self, config_item: ConfigurationItem) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        import os

        env_prefix = config_item.path
        config_data = {}

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix) :].lower()
                config_data[config_key] = value

        self.config_cache[config_item.id] = config_data
        return config_data

    async def _load_vault_config(
        self, config_item: ConfigurationItem
    ) -> Dict[str, Any]:
        """Load configuration from HashiCorp Vault"""
        # Simplified Vault config loading
        # In production, this would integrate with actual Vault

        config_data = {
            "vault_path": config_item.path,
            "secret_data": "encrypted_secret_value",
            "loaded_at": datetime.now().isoformat(),
        }

        if config_item.encrypted:
            config_data = self._decrypt_config(config_data)

        self.config_cache[config_item.id] = config_data
        return config_data

    def _decrypt_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive configuration data"""
        # Simplified decryption - in production use proper encryption
        decrypted_data = {}

        for key, value in config_data.items():
            if isinstance(value, str) and value.startswith("encrypted:"):
                # Simulate decryption
                decrypted_data[key] = value.replace("encrypted:", "decrypted:")
            else:
                decrypted_data[key] = value

        return decrypted_data

    async def watch_configuration(self, config_id: str, callback: Callable) -> dict:
        """Watch configuration for changes"""
        self.config_watchers[config_id] = callback

        # Start watching (simplified implementation)
        asyncio.create_task(self._watch_config_changes(config_id))

    async def _watch_config_changes(self, config_id: str) -> dict:
        """Monitor configuration changes"""
        while config_id in self.config_watchers:
            try:
                # Check for configuration changes
                current_config = await self.load_configuration(config_id)

                # Compare with cached version
                if config_id in self.config_cache:
                    cached_config = self.config_cache[config_id]

                    if current_config != cached_config:
                        # Configuration changed - notify callback
                        callback = self.config_watchers[config_id]
                        await callback(config_id, current_config, cached_config)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logging.error(f"Configuration watching error: {config_id} - {e}")
                await asyncio.sleep(30)

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration management summary"""
        total_configs = len(self.configurations)
        cached_configs = len(self.config_cache)
        watched_configs = len(self.config_watchers)

        by_source = {}
        for config in self.configurations.values():
            source = config.source.value
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total_configurations": total_configs,
            "cached_configurations": cached_configs,
            "watched_configurations": watched_configs,
            "configurations_by_source": by_source,
            "last_updated": datetime.now(),
        }


class InfrastructureProvisioner:
    """Multi-cloud infrastructure provisioning system"""

    def __init__(
        self, template_engine: TemplateEngine, config_manager: ConfigurationManager
    ):
        self.template_engine = template_engine
        self.config_manager = config_manager
        self.templates: Dict[str, InfrastructureTemplate] = {}
        self.deployment_plans: Dict[str, DeploymentPlan] = {}
        self.provisioning_history: List[Dict[str, Any]] = []

    def add_template(self, template: InfrastructureTemplate) -> dict:
        """Add infrastructure template"""
        self.templates[template.id] = template
        logging.info(f"Added infrastructure template: {template.name}")

    def remove_template(self, template_id: str) -> dict:
        """Remove infrastructure template"""
        if template_id in self.templates:
            del self.templates[template_id]
            logging.info(f"Removed infrastructure template: {template_id}")

    async def create_deployment_plan(
        self,
        plan_name: str,
        template_ids: List[str],
        target_environment: str,
        variables: Dict[str, Any],
    ) -> str:
        """Create infrastructure deployment plan"""
        plan_id = f"plan_{int(datetime.now().timestamp())}"

        # Validate templates exist
        for template_id in template_ids:
            if template_id not in self.templates:
                raise ValueError(f"Template not found: {template_id}")

        plan = DeploymentPlan(
            id=plan_id,
            name=plan_name,
            templates=template_ids,
            target_environment=target_environment,
            variables=variables,
        )

        self.deployment_plans[plan_id] = plan

        # Generate plan details
        await self._generate_plan_details(plan)

        logging.info(f"Created deployment plan: {plan_name} ({plan_id})")
        return plan_id

    async def _generate_plan_details(self, plan: DeploymentPlan) -> dict:
        """Generate detailed deployment plan"""
        for template_id in plan.templates:
            template = self.templates[template_id]

            try:
                # Render template with variables
                rendered_content = self.template_engine.render_template(
                    template.template_path, {**template.variables, **plan.variables}
                )

                # Parse rendered content to identify resources
                resources = await self._parse_template_resources(
                    template, rendered_content
                )

                plan.resources_created.extend(resources)

            except Exception as e:
                logging.error(f"Plan generation failed for template {template_id}: {e}")
                plan.state = DeploymentState.FAILED

    async def _parse_template_resources(
        self, template: InfrastructureTemplate, rendered_content: str
    ) -> List[Dict[str, Any]]:
        """Parse template to identify resources to be created"""
        resources = []

        if template.provider == CloudProvider.TERRAFORM:
            resources = await self._parse_terraform_resources(rendered_content)
        elif template.provider == CloudProvider.KUBERNETES:
            resources = await self._parse_kubernetes_resources(rendered_content)
        elif template.provider == CloudProvider.AWS:
            resources = await self._parse_aws_resources(rendered_content)
        # Add more provider parsers as needed

        return resources

    async def _parse_terraform_resources(self, content: str) -> List[Dict[str, Any]]:
        """Parse Terraform template resources"""
        # Simplified Terraform parsing
        resources = []

        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("resource "):
                parts = line.strip().split()
                if len(parts) >= 3:
                    resource_type = parts[1].strip('"')
                    resource_name = parts[2].strip('"')

                    resources.append(
                        {
                            "type": resource_type,
                            "name": resource_name,
                            "provider": "terraform",
                            "action": "create",
                        }
                    )

        return resources

    async def _parse_kubernetes_resources(self, content: str) -> List[Dict[str, Any]]:
        """Parse Kubernetes manifest resources"""
        resources = []

        try:
            # Parse YAML content
            docs = yaml.safe_load_all(content)

            for doc in docs:
                if doc and isinstance(doc, dict):
                    kind = doc.get("kind", "Unknown")
                    metadata = doc.get("metadata", {})
                    name = metadata.get("name", "unnamed")

                    resources.append(
                        {
                            "type": kind,
                            "name": name,
                            "provider": "kubernetes",
                            "action": "create",
                            "namespace": metadata.get("namespace", "default"),
                        }
                    )

        except Exception as e:
            logging.error(f"Kubernetes resource parsing failed: {e}")

        return resources

    async def _parse_aws_resources(self, content: str) -> List[Dict[str, Any]]:
        """Parse AWS CloudFormation template resources"""
        resources = []

        try:
            # Parse JSON/YAML CloudFormation template
            if content.strip().startswith("{"):
                template_data = json.loads(content)
            else:
                template_data = yaml.safe_load(content)

            cf_resources = template_data.get("Resources", {})

            for resource_name, resource_def in cf_resources.items():
                resource_type = resource_def.get("Type", "Unknown")

                resources.append(
                    {
                        "type": resource_type,
                        "name": resource_name,
                        "provider": "aws",
                        "action": "create",
                    }
                )

        except Exception as e:
            logging.error(f"AWS resource parsing failed: {e}")

        return resources

    async def apply_deployment_plan(self, plan_id: str) -> bool:
        """Apply infrastructure deployment plan"""
        if plan_id not in self.deployment_plans:
            raise ValueError(f"Deployment plan not found: {plan_id}")

        plan = self.deployment_plans[plan_id]
        plan.state = DeploymentState.APPLYING

        try:
            logging.info(f"Applying deployment plan: {plan.name}")

            for template_id in plan.templates:
                template = self.templates[template_id]

                success = await self._provision_template(template, plan)

                if not success:
                    plan.state = DeploymentState.FAILED
                    return False

            plan.state = DeploymentState.APPLIED

            # Record deployment history
            self.provisioning_history.append(
                {
                    "plan_id": plan_id,
                    "plan_name": plan.name,
                    "environment": plan.target_environment,
                    "timestamp": datetime.now(),
                    "status": "success",
                    "resources_count": len(plan.resources_created),
                }
            )

            logging.info(f"Deployment plan applied successfully: {plan.name}")
            return True

        except Exception as e:
            plan.state = DeploymentState.FAILED
            logging.error(f"Deployment plan application failed: {e}")

            # Record failure
            self.provisioning_history.append(
                {
                    "plan_id": plan_id,
                    "plan_name": plan.name,
                    "environment": plan.target_environment,
                    "timestamp": datetime.now(),
                    "status": "failed",
                    "error": str(e),
                }
            )

            return False

    async def _provision_template(
        self, template: InfrastructureTemplate, plan: DeploymentPlan
    ) -> bool:
        """Provision infrastructure from template"""
        try:
            # Render template
            rendered_content = self.template_engine.render_template(
                template.template_path, {**template.variables, **plan.variables}
            )

            # Execute provisioning based on provider
            if template.provider == CloudProvider.TERRAFORM:
                return await self._provision_terraform(template, rendered_content)
            elif template.provider == CloudProvider.KUBERNETES:
                return await self._provision_kubernetes(template, rendered_content)
            elif template.provider == CloudProvider.AWS:
                return await self._provision_aws(template, rendered_content)
            else:
                logging.error(f"Unsupported provider: {template.provider}")
                return False

        except Exception as e:
            logging.error(f"Template provisioning failed: {template.name} - {e}")
            return False

    async def _provision_terraform(
        self, template: InfrastructureTemplate, content: str
    ) -> bool:
        """Provision infrastructure using Terraform"""
        try:
            # Create temporary directory for Terraform files
            with tempfile.TemporaryDirectory() as temp_dir:
                tf_file = Path(temp_dir) / "main.tf"

                with open(tf_file, "w") as f:
                    f.write(content)

                # Initialize Terraform
                init_result = subprocess.run(
                    ["terraform", "init"], cwd=temp_dir, capture_output=True, text=True
                )

                if init_result.returncode != 0:
                    logging.error(f"Terraform init failed: {init_result.stderr}")
                    return False

                # Plan Terraform
                plan_result = subprocess.run(
                    ["terraform", "plan", "-out=tfplan"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                )

                if plan_result.returncode != 0:
                    logging.error(f"Terraform plan failed: {plan_result.stderr}")
                    return False

                # Apply Terraform
                apply_result = subprocess.run(
                    ["terraform", "apply", "-auto-approve", "tfplan"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                )

                if apply_result.returncode != 0:
                    logging.error(f"Terraform apply failed: {apply_result.stderr}")
                    return False

                logging.info(f"Terraform provisioning completed: {template.name}")
                return True

        except Exception as e:
            logging.error(f"Terraform provisioning error: {e}")
            return False

    async def _provision_kubernetes(
        self, template: InfrastructureTemplate, content: str
    ) -> bool:
        """Provision infrastructure using Kubernetes"""
        try:
            # Create temporary file for Kubernetes manifest
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write(content)
                manifest_file = f.name

            try:
                # Apply Kubernetes manifest
                apply_result = subprocess.run(
                    ["kubectl", "apply", "-f", manifest_file],
                    capture_output=True,
                    text=True,
                )

                if apply_result.returncode != 0:
                    logging.error(f"Kubernetes apply failed: {apply_result.stderr}")
                    return False

                logging.info(f"Kubernetes provisioning completed: {template.name}")
                return True

            finally:
                # Clean up temporary file
                Path(manifest_file).unlink(missing_ok=True)

        except Exception as e:
            logging.error(f"Kubernetes provisioning error: {e}")
            return False

    async def _provision_aws(
        self, template: InfrastructureTemplate, content: str
    ) -> bool:
        """Provision infrastructure using AWS CloudFormation"""
        try:
            # This would integrate with AWS CloudFormation API
            # Simplified implementation for demonstration

            stack_name = f"{template.name}-{int(datetime.now().timestamp())}"

            # Simulate CloudFormation stack creation
            await asyncio.sleep(2)  # Simulate deployment time

            logging.info(f"AWS CloudFormation stack created: {stack_name}")
            return True

        except Exception as e:
            logging.error(f"AWS provisioning error: {e}")
            return False

    async def destroy_deployment(self, plan_id: str) -> bool:
        """Destroy infrastructure deployment"""
        if plan_id not in self.deployment_plans:
            raise ValueError(f"Deployment plan not found: {plan_id}")

        plan = self.deployment_plans[plan_id]
        plan.state = DeploymentState.DESTROYING

        try:
            logging.info(f"Destroying deployment: {plan.name}")

            # Destroy resources in reverse order
            for template_id in reversed(plan.templates):
                template = self.templates[template_id]

                success = await self._destroy_template(template, plan)

                if not success:
                    logging.warning(f"Failed to destroy template: {template.name}")

            plan.state = DeploymentState.DESTROYED

            logging.info(f"Deployment destroyed: {plan.name}")
            return True

        except Exception as e:
            plan.state = DeploymentState.FAILED
            logging.error(f"Deployment destruction failed: {e}")
            return False

    async def _destroy_template(
        self, template: InfrastructureTemplate, plan: DeploymentPlan
    ) -> bool:
        """Destroy infrastructure from template"""
        # Implementation would depend on provider
        # This is a simplified version

        try:
            logging.info(f"Destroying template resources: {template.name}")

            # Simulate destruction
            await asyncio.sleep(1)

            return True

        except Exception as e:
            logging.error(f"Template destruction failed: {template.name} - {e}")
            return False

    def get_provisioning_status(self) -> Dict[str, Any]:
        """Get infrastructure provisioning status"""
        total_plans = len(self.deployment_plans)
        applied_plans = len(
            [
                p
                for p in self.deployment_plans.values()
                if p.state == DeploymentState.APPLIED
            ]
        )

        failed_plans = len(
            [
                p
                for p in self.deployment_plans.values()
                if p.state == DeploymentState.FAILED
            ]
        )

        return {
            "total_plans": total_plans,
            "applied_plans": applied_plans,
            "failed_plans": failed_plans,
            "success_rate": applied_plans / total_plans if total_plans > 0 else 0,
            "total_templates": len(self.templates),
            "deployment_history": len(self.provisioning_history),
        }


class DriftDetector:
    """Infrastructure drift detection system"""

    def __init__(self, provisioner: InfrastructureProvisioner) -> dict:
        self.provisioner = provisioner
        self.drift_results: List[DriftDetectionResult] = []
        self.detection_enabled = True

    async def start_drift_monitoring(self) -> dict:
        """Start infrastructure drift monitoring"""
        logging.info("Starting infrastructure drift monitoring")

        while self.detection_enabled:
            try:
                for plan_id, plan in self.provisioner.deployment_plans.items():
                    if plan.state == DeploymentState.APPLIED:
                        await self._detect_plan_drift(plan)

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logging.error(f"Drift monitoring error: {e}")
                await asyncio.sleep(300)

    async def _detect_plan_drift(self, plan: DeploymentPlan) -> dict:
        """Detect drift for deployment plan"""
        for template_id in plan.templates:
            template = self.provisioner.templates[template_id]

            drift_results = await self._check_template_drift(template, plan)
            self.drift_results.extend(drift_results)

            # Check if drift exceeds threshold
            critical_drifts = [
                r
                for r in drift_results
                if r.drift_detected and r.severity == "critical"
            ]

            if critical_drifts:
                await self._handle_critical_drift(plan, critical_drifts)

    async def _check_template_drift(
        self, template: InfrastructureTemplate, plan: DeploymentPlan
    ) -> List[DriftDetectionResult]:
        """Check template for configuration drift"""
        drift_results = []

        try:
            # Get expected state from template
            expected_resources = await self.provisioner._parse_template_resources(
                template,
                self.provisioner.template_engine.render_template(
                    template.template_path, {**template.variables, **plan.variables}
                ),
            )

            # Get actual state from provider
            actual_resources = await self._get_actual_resource_state(
                template, expected_resources
            )

            # Compare expected vs actual
            for expected_resource in expected_resources:
                resource_id = expected_resource["name"]

                actual_resource = next(
                    (r for r in actual_resources if r["name"] == resource_id), None
                )

                if actual_resource is None:
                    # Resource missing
                    drift_result = DriftDetectionResult(
                        template_id=template.id,
                        resource_id=resource_id,
                        resource_type=expected_resource["type"],
                        expected_state=expected_resource,
                        actual_state={},
                        drift_detected=True,
                        timestamp=datetime.now(),
                        severity="critical",
                    )
                    drift_results.append(drift_result)

                elif actual_resource != expected_resource:
                    # Resource configuration drift
                    drift_result = DriftDetectionResult(
                        template_id=template.id,
                        resource_id=resource_id,
                        resource_type=expected_resource["type"],
                        expected_state=expected_resource,
                        actual_state=actual_resource,
                        drift_detected=True,
                        timestamp=datetime.now(),
                        severity="medium",
                    )
                    drift_results.append(drift_result)

        except Exception as e:
            logging.error(f"Drift detection failed for template {template.id}: {e}")

        return drift_results

    async def _get_actual_resource_state(
        self, template: InfrastructureTemplate, expected_resources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get actual resource state from provider"""
        # This would query the actual cloud provider APIs
        # Simplified implementation for demonstration

        actual_resources = []

        for resource in expected_resources:
            # Simulate getting actual state
            actual_resource = resource.copy()

            # Simulate some drift (random for demo)
            import random

            if random.random() > 0.8:  # 20% chance of drift
                actual_resource["drifted_property"] = "unexpected_value"

            actual_resources.append(actual_resource)

        return actual_resources

    async def _handle_critical_drift(
        self, plan: DeploymentPlan, critical_drifts: List[DriftDetectionResult]
    ):
        """Handle critical infrastructure drift"""
        logging.critical(f"Critical drift detected in plan: {plan.name}")

        for drift in critical_drifts:
            logging.critical(
                f"Resource {drift.resource_id} ({drift.resource_type}) "
                f"has critical drift in template {drift.template_id}"
            )

        # Update plan state
        plan.state = DeploymentState.DRIFTED

        # Auto-remediation could be implemented here
        # For now, just log and alert

    def get_drift_summary(self) -> Dict[str, Any]:
        """Get drift detection summary"""
        total_checks = len(self.drift_results)
        drift_detected = len([r for r in self.drift_results if r.drift_detected])

        critical_drifts = len(
            [
                r
                for r in self.drift_results
                if r.drift_detected and r.severity == "critical"
            ]
        )

        return {
            "total_drift_checks": total_checks,
            "drifts_detected": drift_detected,
            "critical_drifts": critical_drifts,
            "drift_rate": drift_detected / total_checks if total_checks > 0 else 0,
            "last_check": max([r.timestamp for r in self.drift_results])
            if self.drift_results
            else None,
        }

    def stop_drift_monitoring(self) -> dict:
        """Stop drift monitoring"""
        self.detection_enabled = False
        logging.info("Drift monitoring stopped")


class ConfigurationIaCSystem:
    """Main Configuration Management & Infrastructure as Code system"""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.template_engine = TemplateEngine()
        self.config_manager = ConfigurationManager()
        self.provisioner = InfrastructureProvisioner(
            self.template_engine, self.config_manager
        )
        self.drift_detector = DriftDetector(self.provisioner)

        # System configuration
        self.iac_enabled = True
        self.drift_detection_enabled = True
        self.auto_remediation_enabled = False

        # Initialize default configurations
        self._initialize_default_configs()

        logging.info("Configuration & IaC system initialized")

    def _initialize_default_configs(self) -> dict:
        """Initialize default configurations and templates"""

        # Add sample configuration items
        app_config = ConfigurationItem(
            id="app_config",
            name="Application Configuration",
            source=ConfigurationSource.FILE,
            path="config/app.yaml",
            environment="production",
            sensitive=False,
        )
        self.config_manager.add_configuration(app_config)

        db_config = ConfigurationItem(
            id="database_config",
            name="Database Configuration",
            source=ConfigurationSource.VAULT,
            path="secret/database",
            environment="production",
            sensitive=True,
            encrypted=True,
        )
        self.config_manager.add_configuration(db_config)

        # Add sample infrastructure templates
        k8s_template = InfrastructureTemplate(
            id="k8s_app_template",
            name="Kubernetes Application Template",
            provider=CloudProvider.KUBERNETES,
            template_path="templates/k8s-app.yaml.j2",
            variables={
                "app_name": "itdo-erp",
                "replicas": 3,
                "image": "itdo-erp:latest",
            },
            tags={"environment": "production", "team": "platform"},
        )
        self.provisioner.add_template(k8s_template)

        terraform_template = InfrastructureTemplate(
            id="aws_infrastructure",
            name="AWS Infrastructure Template",
            provider=CloudProvider.TERRAFORM,
            template_path="templates/aws-infra.tf.j2",
            variables={
                "region": "us-east-1",
                "instance_type": "t3.medium",
                "environment": "production",
            },
            tags={"provider": "aws", "managed_by": "terraform"},
        )
        self.provisioner.add_template(terraform_template)

    async def start_iac_monitoring(self) -> dict:
        """Start IaC monitoring and drift detection"""
        if not self.iac_enabled:
            logging.info("IaC monitoring is disabled")
            return

        logging.info("Starting IaC monitoring")

        tasks = []

        if self.drift_detection_enabled:
            tasks.append(
                asyncio.create_task(self.drift_detector.start_drift_monitoring())
            )

        if tasks:
            await asyncio.gather(*tasks)

    async def deploy_infrastructure(
        self,
        plan_name: str,
        template_ids: List[str],
        environment: str,
        variables: Dict[str, Any],
    ) -> str:
        """Deploy infrastructure using templates"""
        # Load configuration for environment
        env_configs = {}
        for config_id, config_item in self.config_manager.configurations.items():
            if config_item.environment == environment:
                try:
                    config_data = await self.config_manager.load_configuration(
                        config_id
                    )
                    env_configs[config_id] = config_data
                except Exception as e:
                    logging.warning(f"Failed to load config {config_id}: {e}")

        # Merge configuration variables
        all_variables = {**env_configs, **variables}

        # Create and apply deployment plan
        plan_id = await self.provisioner.create_deployment_plan(
            plan_name, template_ids, environment, all_variables
        )

        success = await self.provisioner.apply_deployment_plan(plan_id)

        if success:
            logging.info(f"Infrastructure deployed successfully: {plan_name}")
        else:
            logging.error(f"Infrastructure deployment failed: {plan_name}")

        return plan_id

    async def update_infrastructure(
        self, plan_id: str, variables: Dict[str, Any]
    ) -> bool:
        """Update existing infrastructure deployment"""
        if plan_id not in self.provisioner.deployment_plans:
            raise ValueError(f"Deployment plan not found: {plan_id}")

        plan = self.provisioner.deployment_plans[plan_id]

        # Update variables
        plan.variables.update(variables)

        # Re-apply deployment
        success = await self.provisioner.apply_deployment_plan(plan_id)

        if success:
            logging.info(f"Infrastructure updated successfully: {plan.name}")
        else:
            logging.error(f"Infrastructure update failed: {plan.name}")

        return success

    async def destroy_infrastructure(self, plan_id: str) -> bool:
        """Destroy infrastructure deployment"""
        success = await self.provisioner.destroy_deployment(plan_id)

        if success:
            logging.info("Infrastructure destroyed successfully")
        else:
            logging.error("Infrastructure destruction failed")

        return success

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive IaC system status"""
        config_summary = self.config_manager.get_configuration_summary()
        provisioning_status = self.provisioner.get_provisioning_status()
        drift_summary = self.drift_detector.get_drift_summary()

        return {
            "timestamp": datetime.now(),
            "iac_enabled": self.iac_enabled,
            "drift_detection_enabled": self.drift_detection_enabled,
            "auto_remediation_enabled": self.auto_remediation_enabled,
            "configuration_management": config_summary,
            "infrastructure_provisioning": provisioning_status,
            "drift_detection": drift_summary,
        }

    async def stop_iac_monitoring(self) -> dict:
        """Stop IaC monitoring"""
        self.iac_enabled = False
        self.drift_detector.stop_drift_monitoring()
        logging.info("IaC monitoring stopped")


# Example usage and testing
async def main() -> None:
    """Example usage of the Configuration & IaC system"""

    # Initialize SDK (mock)
    class MockMobileERPSDK:
        pass

    sdk = MockMobileERPSDK()

    # Create IaC system
    iac_system = ConfigurationIaCSystem(sdk)

    # Get initial system status
    status = iac_system.get_system_status()
    print(f"Initial IaC Status: {json.dumps(status, indent=2, default=str)}")

    # Deploy infrastructure
    print("Deploying sample infrastructure...")

    plan_id = await iac_system.deploy_infrastructure(
        plan_name="Sample ERP Infrastructure",
        template_ids=["k8s_app_template"],
        environment="production",
        variables={
            "app_version": "v1.0.0",
            "replicas": 5,
            "cpu_limit": "500m",
            "memory_limit": "1Gi",
        },
    )

    print(f"Deployment plan created: {plan_id}")

    # Start monitoring
    print("Starting IaC monitoring...")

    monitoring_task = asyncio.create_task(iac_system.start_iac_monitoring())

    # Let it run for demonstration
    await asyncio.sleep(10)

    # Check for drift
    drift_summary = iac_system.drift_detector.get_drift_summary()
    print(f"Drift Summary: {json.dumps(drift_summary, indent=2, default=str)}")

    # Get final status
    final_status = iac_system.get_system_status()
    print(f"Final IaC Status: {json.dumps(final_status, indent=2, default=str)}")

    # Stop monitoring
    await iac_system.stop_iac_monitoring()
    monitoring_task.cancel()

    print("Configuration & IaC demonstration completed")


if __name__ == "__main__":
    asyncio.run(main())
