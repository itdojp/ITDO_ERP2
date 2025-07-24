#!/usr/bin/env python3
"""
CC03 v38.0 - Master Orchestrator System
Central coordination system for all automation components
"""

import asyncio
import json
import logging
import time
import subprocess
import signal
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
from dataclasses import dataclass, asdict
from enum import Enum
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_orchestrator_v38.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemHealth(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"

class ComponentStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    STARTING = "starting"
    STOPPING = "stopping"
    RESTARTING = "restarting"

@dataclass
class Component:
    name: str
    script_path: str
    description: str
    status: ComponentStatus
    pid: Optional[int] = None
    last_health_check: Optional[datetime] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    uptime: timedelta = timedelta()

@dataclass
class SystemMetrics:
    timestamp: datetime
    overall_health: SystemHealth
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_components: int
    failed_components: int
    optimization_score: float
    security_score: float
    performance_score: float

class MasterOrchestrator:
    """Master orchestration system for all automation components"""
    
    def __init__(self):
        self.components = {}
        self.system_metrics_history = []
        self.orchestrator_start_time = datetime.now()
        self.health_check_interval = 300  # 5 minutes
        self.restart_cooldown = 600  # 10 minutes
        self.max_restart_attempts = 3
        self.shutdown_requested = False
        
        # Component definitions
        self.setup_components()
        
        # Performance tracking
        self.performance_baselines = {
            "cpu_threshold": 80.0,
            "memory_threshold": 85.0,
            "disk_threshold": 90.0,
            "optimization_target": 85.0,
            "security_target": 90.0,
            "performance_target": 80.0
        }
        
        # Auto-prevention system
        self.prevention_enabled = True
        self.prevention_rules = []
        self.setup_prevention_rules()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def setup_components(self):
        """Setup all automation components"""
        base_path = Path(__file__).parent
        
        self.components = {
            "infrastructure_optimizer": Component(
                name="Infrastructure Optimizer",
                script_path=str(base_path / "continuous_infrastructure_optimization_v38.py"),
                description="24/7 infrastructure optimization and auto-scaling",
                status=ComponentStatus.STOPPED
            ),
            "observability_automation": Component(
                name="Observability Automation",
                script_path=str(base_path / "observability_automation_v38.py"),
                description="Comprehensive monitoring, alerting, and analysis",
                status=ComponentStatus.STOPPED
            ),
            "security_automation": Component(
                name="Security Automation",
                script_path=str(base_path / "security_automation_v38.py"),
                description="Advanced security monitoring and threat response",
                status=ComponentStatus.STOPPED
            )
        }
    
    def setup_prevention_rules(self):
        """Setup auto-prevention rules"""
        self.prevention_rules = [
            {
                "name": "high_cpu_prevention",
                "condition": lambda metrics: metrics.cpu_usage > 90,
                "action": "scale_infrastructure",
                "cooldown": 600,
                "last_triggered": None
            },
            {
                "name": "memory_exhaustion_prevention",
                "condition": lambda metrics: metrics.memory_usage > 95,
                "action": "restart_components",
                "cooldown": 300,
                "last_triggered": None
            },
            {
                "name": "component_failure_prevention",
                "condition": lambda metrics: metrics.failed_components > 1,
                "action": "emergency_restart",
                "cooldown": 900,
                "last_triggered": None
            },
            {
                "name": "performance_degradation_prevention",
                "condition": lambda metrics: metrics.performance_score < 50,
                "action": "performance_optimization",
                "cooldown": 1200,
                "last_triggered": None
            }
        ]
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    async def start_component(self, component_name: str) -> bool:
        """Start a component"""
        if component_name not in self.components:
            logger.error(f"Unknown component: {component_name}")
            return False
        
        component = self.components[component_name]
        
        if component.status == ComponentStatus.RUNNING:
            logger.info(f"Component {component_name} is already running")
            return True
        
        try:
            logger.info(f"Starting component: {component.name}")
            component.status = ComponentStatus.STARTING
            
            # Start the component process
            process = subprocess.Popen([
                "python3", component.script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            component.pid = process.pid
            component.status = ComponentStatus.RUNNING
            component.last_health_check = datetime.now()
            
            logger.info(f"Component {component.name} started successfully (PID: {component.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start component {component_name}: {e}")
            component.status = ComponentStatus.FAILED
            return False
    
    async def stop_component(self, component_name: str) -> bool:
        """Stop a component"""
        if component_name not in self.components:
            logger.error(f"Unknown component: {component_name}")
            return False
        
        component = self.components[component_name]
        
        if component.status != ComponentStatus.RUNNING or not component.pid:
            logger.info(f"Component {component_name} is not running")
            return True
        
        try:
            logger.info(f"Stopping component: {component.name}")
            component.status = ComponentStatus.STOPPING
            
            # Terminate the process gracefully
            try:
                process = psutil.Process(component.pid)
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=30)
                except psutil.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    process.kill()
                    logger.warning(f"Force killed component {component.name}")
                
            except psutil.NoSuchProcess:
                logger.info(f"Component {component.name} process already terminated")
            
            component.pid = None
            component.status = ComponentStatus.STOPPED
            
            logger.info(f"Component {component.name} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop component {component_name}: {e}")
            component.status = ComponentStatus.FAILED
            return False
    
    async def restart_component(self, component_name: str) -> bool:
        """Restart a component"""
        component = self.components.get(component_name)
        if not component:
            return False
        
        # Check restart cooldown
        if (component.last_restart and 
            datetime.now() - component.last_restart < timedelta(seconds=self.restart_cooldown)):
            logger.info(f"Component {component_name} is in restart cooldown")
            return False
        
        # Check max restart attempts
        if component.restart_count >= self.max_restart_attempts:
            logger.error(f"Component {component_name} exceeded max restart attempts")
            return False
        
        logger.info(f"Restarting component: {component.name}")
        component.status = ComponentStatus.RESTARTING
        
        # Stop and start the component
        await self.stop_component(component_name)
        await asyncio.sleep(5)  # Brief pause between stop and start
        
        success = await self.start_component(component_name)
        
        if success:
            component.restart_count += 1
            component.last_restart = datetime.now()
            logger.info(f"Component {component.name} restarted successfully")
        else:
            logger.error(f"Failed to restart component {component.name}")
        
        return success
    
    async def check_component_health(self, component_name: str) -> bool:
        """Check health of a component"""
        component = self.components.get(component_name)
        if not component or not component.pid:
            return False
        
        try:
            process = psutil.Process(component.pid)
            
            # Check if process is still running
            if not process.is_running():
                logger.warning(f"Component {component.name} process is not running")
                component.status = ComponentStatus.FAILED
                return False
            
            # Update resource usage
            component.cpu_usage = process.cpu_percent()
            component.memory_usage = process.memory_percent()
            component.uptime = datetime.now() - datetime.fromtimestamp(process.create_time())
            component.last_health_check = datetime.now()
            
            # Check for excessive resource usage
            if component.cpu_usage > 95 or component.memory_usage > 95:
                logger.warning(f"Component {component.name} using excessive resources "
                             f"(CPU: {component.cpu_usage:.1f}%, Memory: {component.memory_usage:.1f}%)")
                return False
            
            return True
            
        except psutil.NoSuchProcess:
            logger.warning(f"Component {component.name} process no longer exists")
            component.status = ComponentStatus.FAILED
            component.pid = None
            return False
        except Exception as e:
            logger.error(f"Error checking health of component {component.name}: {e}")
            return False
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""
        try:
            # System resource metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Component status
            active_components = len([c for c in self.components.values() if c.status == ComponentStatus.RUNNING])
            failed_components = len([c for c in self.components.values() if c.status == ComponentStatus.FAILED])
            
            # Calculate scores
            optimization_score = self._calculate_optimization_score()
            security_score = self._calculate_security_score()
            performance_score = self._calculate_performance_score(cpu_usage, memory.percent)
            
            # Determine overall health
            overall_health = self._determine_overall_health(
                cpu_usage, memory.percent, active_components, failed_components, performance_score
            )
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                overall_health=overall_health,
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=(disk.used / disk.total) * 100,
                active_components=active_components,
                failed_components=failed_components,
                optimization_score=optimization_score,
                security_score=security_score,
                performance_score=performance_score
            )
            
            # Add to history
            self.system_metrics_history.append(metrics)
            if len(self.system_metrics_history) > 1000:
                self.system_metrics_history = self.system_metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                overall_health=SystemHealth.FAILED,
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                active_components=0,
                failed_components=len(self.components),
                optimization_score=0.0,
                security_score=0.0,
                performance_score=0.0
            )
    
    def _calculate_optimization_score(self) -> float:
        """Calculate optimization effectiveness score"""
        try:
            # This would integrate with the optimization system to get real metrics
            # For now, we simulate based on component health and resource usage
            
            running_components = len([c for c in self.components.values() if c.status == ComponentStatus.RUNNING])
            total_components = len(self.components)
            
            if total_components == 0:
                return 0.0
            
            component_health_score = (running_components / total_components) * 100
            
            # Factor in recent system performance
            if len(self.system_metrics_history) > 0:
                recent_cpu = sum(m.cpu_usage for m in self.system_metrics_history[-10:]) / min(10, len(self.system_metrics_history))
                recent_memory = sum(m.memory_usage for m in self.system_metrics_history[-10:]) / min(10, len(self.system_metrics_history))
                
                resource_efficiency = 100 - ((recent_cpu + recent_memory) / 2)
                optimization_score = (component_health_score + resource_efficiency) / 2
            else:
                optimization_score = component_health_score
            
            return max(0.0, min(100.0, optimization_score))
            
        except Exception as e:
            logger.error(f"Error calculating optimization score: {e}")
            return 0.0
    
    def _calculate_security_score(self) -> float:
        """Calculate security posture score"""
        try:
            # This would integrate with the security system to get real metrics
            # For now, we simulate based on component availability and basic checks
            
            security_component = self.components.get("security_automation")
            if not security_component or security_component.status != ComponentStatus.RUNNING:
                return 50.0  # Reduced score if security component is down
            
            # Check for security-related processes
            security_processes = ["falco", "trivy", "kube-bench"]
            running_security_processes = 0
            
            for proc in psutil.process_iter(['name']):
                if any(sp in proc.info['name'].lower() for sp in security_processes):
                    running_security_processes += 1
            
            base_score = 80.0
            process_bonus = min(20.0, running_security_processes * 5.0)
            
            return min(100.0, base_score + process_bonus)
            
        except Exception as e:
            logger.error(f"Error calculating security score: {e}")
            return 50.0
    
    def _calculate_performance_score(self, cpu_usage: float, memory_usage: float) -> float:
        """Calculate performance score"""
        try:
            # Performance based on resource utilization and response times
            cpu_score = max(0, 100 - cpu_usage)
            memory_score = max(0, 100 - memory_usage)
            
            # Component availability factor
            running_components = len([c for c in self.components.values() if c.status == ComponentStatus.RUNNING])
            total_components = len(self.components)
            availability_score = (running_components / total_components) * 100 if total_components > 0 else 0
            
            # Weighted average
            performance_score = (cpu_score * 0.3 + memory_score * 0.3 + availability_score * 0.4)
            
            return max(0.0, min(100.0, performance_score))
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
    
    def _determine_overall_health(self, cpu_usage: float, memory_usage: float, 
                                active_components: int, failed_components: int, 
                                performance_score: float) -> SystemHealth:
        """Determine overall system health"""
        try:
            # Critical conditions
            if failed_components > 2 or cpu_usage > 95 or memory_usage > 95:
                return SystemHealth.CRITICAL
            
            if failed_components > 1 or cpu_usage > 90 or memory_usage > 90:
                return SystemHealth.FAILED
            
            # Performance-based assessment
            if performance_score < 50:
                return SystemHealth.CRITICAL
            elif performance_score < 70:
                return SystemHealth.DEGRADED
            elif performance_score < 85:
                return SystemHealth.GOOD
            else:
                return SystemHealth.EXCELLENT
                
        except Exception as e:
            logger.error(f"Error determining overall health: {e}")
            return SystemHealth.FAILED
    
    async def execute_prevention_actions(self, metrics: SystemMetrics):
        """Execute auto-prevention actions based on metrics"""
        if not self.prevention_enabled:
            return
        
        for rule in self.prevention_rules:
            try:
                # Check cooldown
                if (rule["last_triggered"] and 
                    datetime.now() - rule["last_triggered"] < timedelta(seconds=rule["cooldown"])):
                    continue
                
                # Check condition
                if rule["condition"](metrics):
                    logger.warning(f"Prevention rule triggered: {rule['name']}")
                    
                    success = await self._execute_prevention_action(rule["action"], metrics)
                    
                    if success:
                        rule["last_triggered"] = datetime.now()
                        logger.info(f"Prevention action executed: {rule['action']}")
                    else:
                        logger.error(f"Failed to execute prevention action: {rule['action']}")
                        
            except Exception as e:
                logger.error(f"Error executing prevention rule {rule['name']}: {e}")
    
    async def _execute_prevention_action(self, action: str, metrics: SystemMetrics) -> bool:
        """Execute a specific prevention action"""
        try:
            if action == "scale_infrastructure":
                # Scale up infrastructure components
                logger.info("Executing infrastructure scaling...")
                return await self._scale_infrastructure()
                
            elif action == "restart_components":
                # Restart failed or problematic components
                logger.info("Restarting components...")
                return await self._restart_problematic_components()
                
            elif action == "emergency_restart":
                # Emergency restart of all components
                logger.warning("Executing emergency restart...")
                return await self._emergency_restart_all()
                
            elif action == "performance_optimization":
                # Trigger performance optimization
                logger.info("Triggering performance optimization...")
                return await self._trigger_performance_optimization()
                
            else:
                logger.warning(f"Unknown prevention action: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing prevention action {action}: {e}")
            return False
    
    async def _scale_infrastructure(self) -> bool:
        """Scale infrastructure resources"""
        try:
            # Scale backend deployment
            result = subprocess.run([
                "kubectl", "scale", "deployment", "backend",
                "--replicas=6", "-n", "itdo-erp-prod"
            ], capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error scaling infrastructure: {e}")
            return False
    
    async def _restart_problematic_components(self) -> bool:
        """Restart components that are having issues"""
        success = True
        
        for name, component in self.components.items():
            if (component.status == ComponentStatus.FAILED or 
                component.cpu_usage > 90 or 
                component.memory_usage > 90):
                
                logger.info(f"Restarting problematic component: {name}")
                success &= await self.restart_component(name)
        
        return success
    
    async def _emergency_restart_all(self) -> bool:
        """Emergency restart of all components"""
        logger.warning("Performing emergency restart of all components")
        
        # Stop all components first
        for name in self.components.keys():
            await self.stop_component(name)
        
        # Wait a moment
        await asyncio.sleep(10)
        
        # Start all components
        success = True
        for name in self.components.keys():
            success &= await self.start_component(name)
        
        return success
    
    async def _trigger_performance_optimization(self) -> bool:
        """Trigger performance optimization in infrastructure optimizer"""
        try:
            # This would send a signal to the infrastructure optimizer
            # to perform immediate optimization
            
            optimizer = self.components.get("infrastructure_optimizer")
            if optimizer and optimizer.status == ComponentStatus.RUNNING:
                # Send optimization trigger signal
                logger.info("Triggering immediate performance optimization")
                return True
            else:
                logger.warning("Infrastructure optimizer not available for performance optimization")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering performance optimization: {e}")
            return False
    
    async def save_orchestrator_state(self):
        """Save current orchestrator state"""
        try:
            state_data = {
                "timestamp": datetime.now().isoformat(),
                "orchestrator_uptime": str(datetime.now() - self.orchestrator_start_time),
                "components": {
                    name: {
                        "name": comp.name,
                        "status": comp.status.value,
                        "pid": comp.pid,
                        "restart_count": comp.restart_count,
                        "cpu_usage": comp.cpu_usage,
                        "memory_usage": comp.memory_usage,
                        "uptime": str(comp.uptime) if comp.uptime else None,
                        "last_health_check": comp.last_health_check.isoformat() if comp.last_health_check else None
                    }
                    for name, comp in self.components.items()
                },
                "system_metrics": asdict(self.system_metrics_history[-1]) if self.system_metrics_history else None,
                "prevention_rules": [
                    {
                        "name": rule["name"],
                        "last_triggered": rule["last_triggered"].isoformat() if rule["last_triggered"] else None
                    }
                    for rule in self.prevention_rules
                ]
            }
            
            state_file = Path("orchestrator_state_v38.json")
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
            
            # Keep state history
            history_file = Path(f"orchestrator_history_{datetime.now().strftime('%Y%m%d')}.jsonl")
            with open(history_file, 'a') as f:
                json.dump(state_data, f, default=str)
                f.write('\n')
                
        except Exception as e:
            logger.error(f"Error saving orchestrator state: {e}")
    
    def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        current_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "orchestrator_uptime": str(datetime.now() - self.orchestrator_start_time),
            "overall_status": {
                "health": current_metrics.overall_health.value if current_metrics else "unknown",
                "active_components": len([c for c in self.components.values() if c.status == ComponentStatus.RUNNING]),
                "total_components": len(self.components),
                "failed_components": len([c for c in self.components.values() if c.status == ComponentStatus.FAILED]),
                "optimization_score": current_metrics.optimization_score if current_metrics else 0,
                "security_score": current_metrics.security_score if current_metrics else 0,
                "performance_score": current_metrics.performance_score if current_metrics else 0
            },
            "component_status": {
                name: {
                    "status": comp.status.value,
                    "uptime": str(comp.uptime) if comp.uptime else "0:00:00",
                    "cpu_usage": f"{comp.cpu_usage:.1f}%",
                    "memory_usage": f"{comp.memory_usage:.1f}%",
                    "restart_count": comp.restart_count,
                    "last_health_check": comp.last_health_check.strftime("%Y-%m-%d %H:%M:%S") if comp.last_health_check else "Never"
                }
                for name, comp in self.components.items()
            },
            "system_resources": {
                "cpu_usage": f"{current_metrics.cpu_usage:.1f}%" if current_metrics else "Unknown",
                "memory_usage": f"{current_metrics.memory_usage:.1f}%" if current_metrics else "Unknown",
                "disk_usage": f"{current_metrics.disk_usage:.1f}%" if current_metrics else "Unknown"
            },
            "prevention_system": {
                "enabled": self.prevention_enabled,
                "rules_triggered_24h": len([
                    rule for rule in self.prevention_rules
                    if rule["last_triggered"] and 
                    datetime.now() - rule["last_triggered"] < timedelta(hours=24)
                ])
            }
        }
        
        return report
    
    async def orchestration_loop(self):
        """Main orchestration loop"""
        logger.info("Starting Master Orchestrator v38.0")
        logger.info("Initializing all automation components...")
        
        # Start all components
        for name in self.components.keys():
            await self.start_component(name)
            await asyncio.sleep(10)  # Stagger startup
        
        cycle_count = 0
        
        while not self.shutdown_requested:
            try:
                cycle_start = time.time()
                cycle_count += 1
                
                logger.info(f"🔄 Orchestration cycle #{cycle_count}")
                
                # Collect system metrics
                metrics = self.collect_system_metrics()
                
                # Health check all components
                for name in self.components.keys():
                    is_healthy = await self.check_component_health(name)
                    
                    if not is_healthy and self.components[name].status == ComponentStatus.RUNNING:
                        logger.warning(f"Component {name} health check failed, restarting...")
                        await self.restart_component(name)
                
                # Execute prevention actions if needed
                await self.execute_prevention_actions(metrics)
                
                # Save state periodically
                if cycle_count % 6 == 0:  # Every 6 cycles (30 minutes)
                    await self.save_orchestrator_state()
                
                # Generate and display status report
                if cycle_count % 2 == 0:  # Every 2 cycles (10 minutes)
                    report = self.generate_status_report()
                    
                    logger.info(f"📊 System Status: {report['overall_status']['health'].upper()} "
                              f"({report['overall_status']['active_components']}/{report['overall_status']['total_components']} components active)")
                    logger.info(f"📈 Scores - Optimization: {report['overall_status']['optimization_score']:.1f}, "
                              f"Security: {report['overall_status']['security_score']:.1f}, "
                              f"Performance: {report['overall_status']['performance_score']:.1f}")
                
                # Log cycle summary
                cycle_duration = time.time() - cycle_start
                logger.info(f"⏱️  Orchestration cycle #{cycle_count} completed in {cycle_duration:.2f}s "
                          f"(Health: {metrics.overall_health.value})")
                
                # Sleep for next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in orchestration cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        # Graceful shutdown
        logger.info("Shutting down Master Orchestrator...")
        await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all components gracefully"""
        logger.info("Initiating graceful shutdown of all components...")
        
        # Stop all components
        for name in self.components.keys():
            await self.stop_component(name)
        
        # Save final state
        await self.save_orchestrator_state()
        
        logger.info("Master Orchestrator shutdown complete")

async def main():
    """Main function"""
    orchestrator = MasterOrchestrator()
    
    try:
        await orchestrator.orchestration_loop()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error in orchestrator: {e}")
        raise
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())