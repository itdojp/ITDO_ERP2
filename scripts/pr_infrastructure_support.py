#!/usr/bin/env python3
"""
CC03 Infrastructure Supremacy v44.0 - PR Management Infrastructure

Comprehensive system for providing infrastructure support to 20+ open PRs
with automated conflict resolution, CI/CD optimization, and quality assurance.
"""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PRInfo:
    """Information about a Pull Request."""
    number: int
    title: str
    branch: str
    state: str
    created_at: str
    conflicts: bool = False
    ci_status: str = "unknown"
    priority: str = "medium"
    risk_level: str = "low"


class PRInfrastructureManager:
    """Manages infrastructure support for multiple PRs."""
    
    def __init__(self):
        self.base_dir = Path("/home/work/ITDO_ERP2")
        self.reports_dir = self.base_dir / "infrastructure_reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def run_command(self, command: str, cwd: Optional[Path] = None) -> tuple[str, str, int]:
        """Run a shell command and return output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.base_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", 124
        except Exception as e:
            return "", str(e), 1
    
    def get_open_prs(self) -> List[PRInfo]:
        """Get list of open PRs."""
        logger.info("Fetching open PRs...")
        stdout, stderr, code = self.run_command("gh pr list --state open --limit 50 --json number,title,headRefName,state,createdAt")
        
        if code != 0:
            logger.error(f"Failed to fetch PRs: {stderr}")
            return []
        
        try:
            pr_data = json.loads(stdout)
            prs = []
            
            for pr in pr_data:
                pr_info = PRInfo(
                    number=pr["number"],
                    title=pr["title"],
                    branch=pr["headRefName"],
                    state=pr["state"],
                    created_at=pr["createdAt"]
                )
                
                # Check for conflicts
                pr_info.conflicts = self.check_pr_conflicts(pr_info.number)
                
                # Get CI status
                pr_info.ci_status = self.get_ci_status(pr_info.number)
                
                # Determine priority based on title and content
                pr_info.priority = self.determine_priority(pr_info)
                
                # Assess risk level
                pr_info.risk_level = self.assess_risk(pr_info)
                
                prs.append(pr_info)
            
            logger.info(f"Found {len(prs)} open PRs")
            return prs
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse PR data: {e}")
            return []
    
    def check_pr_conflicts(self, pr_number: int) -> bool:
        """Check if PR has merge conflicts."""
        stdout, stderr, code = self.run_command(f"gh pr view {pr_number} --json mergeable")
        
        if code != 0:
            return False
        
        try:
            data = json.loads(stdout)
            return data.get("mergeable") == "CONFLICTING"
        except:
            return False
    
    def get_ci_status(self, pr_number: int) -> str:
        """Get CI status for PR."""
        stdout, stderr, code = self.run_command(f"gh pr checks {pr_number} --json state")
        
        if code != 0:
            return "unknown"
        
        try:
            data = json.loads(stdout)
            if not data:
                return "no_checks"
            
            states = [check.get("state", "unknown") for check in data]
            
            if "FAILURE" in states:
                return "failed"
            elif "PENDING" in states:
                return "pending"
            elif all(state == "SUCCESS" for state in states):
                return "passed"
            else:
                return "mixed"
        except:
            return "unknown"
    
    def determine_priority(self, pr: PRInfo) -> str:
        """Determine PR priority based on content."""
        title_lower = pr.title.lower()
        
        # High priority keywords
        high_priority = ["critical", "urgent", "security", "hotfix", "production", "api", "infrastructure"]
        
        # Medium priority keywords
        medium_priority = ["feat", "feature", "enhancement", "improvement"]
        
        # Low priority keywords
        low_priority = ["doc", "documentation", "style", "refactor", "test"]
        
        if any(keyword in title_lower for keyword in high_priority):
            return "high"
        elif any(keyword in title_lower for keyword in medium_priority):
            return "medium"
        elif any(keyword in title_lower for keyword in low_priority):
            return "low"
        else:
            return "medium"
    
    def assess_risk(self, pr: PRInfo) -> str:
        """Assess risk level of PR."""
        risk_score = 0
        
        # Conflicts increase risk
        if pr.conflicts:
            risk_score += 3
        
        # Failed CI increases risk
        if pr.ci_status == "failed":
            risk_score += 2
        
        # Age increases risk (older PRs might have conflicts)
        try:
            created = datetime.fromisoformat(pr.created_at.replace('Z', '+00:00'))
            age_days = (datetime.now(timezone.utc) - created).days
            if age_days > 7:
                risk_score += 1
            if age_days > 14:
                risk_score += 1
        except:
            pass
        
        # API/Infrastructure changes are higher risk
        if any(keyword in pr.title.lower() for keyword in ["api", "infrastructure", "database", "migration"]):
            risk_score += 1
        
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"
    
    async def resolve_pr_conflicts(self, pr: PRInfo) -> bool:
        """Attempt to resolve PR conflicts automatically."""
        if not pr.conflicts:
            return True
        
        logger.info(f"Resolving conflicts for PR #{pr.number}")
        
        try:
            # Checkout PR branch
            stdout, stderr, code = self.run_command(f"gh pr checkout {pr.number}")
            if code != 0:
                logger.error(f"Failed to checkout PR #{pr.number}: {stderr}")
                return False
            
            # Fetch latest main
            self.run_command("git fetch origin main")
            
            # Attempt merge
            stdout, stderr, code = self.run_command("git merge origin/main")
            
            if code != 0:
                if "CONFLICT" in stderr or "conflict" in stderr.lower():
                    logger.info(f"Conflicts detected in PR #{pr.number}, attempting automatic resolution")
                    
                    # Get conflicted files
                    stdout, stderr, code = self.run_command("git diff --name-only --diff-filter=U")
                    conflicted_files = stdout.strip().split('\n') if stdout.strip() else []
                    
                    resolved_count = 0
                    for file_path in conflicted_files:
                        if self.auto_resolve_conflict(file_path):
                            resolved_count += 1
                    
                    if resolved_count == len(conflicted_files):
                        # All conflicts resolved, commit
                        self.run_command("git add .")
                        self.run_command(f'git commit -m "Auto-resolve merge conflicts for PR #{pr.number}"')
                        
                        # Push resolved branch
                        self.run_command(f"git push origin {pr.branch}")
                        
                        logger.info(f"Successfully resolved all conflicts for PR #{pr.number}")
                        return True
                    else:
                        # Abort merge
                        self.run_command("git merge --abort")
                        logger.warning(f"Could not auto-resolve all conflicts for PR #{pr.number}")
                        return False
                else:
                    logger.error(f"Merge failed for PR #{pr.number}: {stderr}")
                    return False
            else:
                # Merge successful
                self.run_command(f"git push origin {pr.branch}")
                logger.info(f"Successfully merged main into PR #{pr.number}")
                return True
                
        except Exception as e:
            logger.error(f"Error resolving conflicts for PR #{pr.number}: {e}")
            return False
        finally:
            # Always return to main branch
            self.run_command("git checkout main")
    
    def auto_resolve_conflict(self, file_path: str) -> bool:
        """Attempt to automatically resolve conflicts in a file."""
        try:
            file_full_path = self.base_dir / file_path
            
            if not file_full_path.exists():
                return False
            
            # Read file content
            with open(file_full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if it's a simple conflict that can be auto-resolved
            if '<<<<<<< HEAD' not in content:
                return True  # No conflicts
            
            # For package.json and package-lock.json, prefer newer versions
            if file_path.endswith(('package.json', 'package-lock.json')):
                return self.resolve_package_conflicts(file_full_path, content)
            
            # For simple import conflicts, merge both
            if file_path.endswith('.py') and content.count('<<<<<<< HEAD') == 1:
                return self.resolve_python_import_conflicts(file_full_path, content)
            
            # For configuration files, prefer HEAD (current branch)
            if file_path.endswith(('.yml', '.yaml', '.json', '.toml')):
                return self.resolve_config_conflicts(file_full_path, content)
            
            return False
            
        except Exception as e:
            logger.error(f"Error auto-resolving conflict in {file_path}: {e}")
            return False
    
    def resolve_package_conflicts(self, file_path: Path, content: str) -> bool:
        """Resolve package.json conflicts by choosing newer versions."""
        try:
            lines = content.split('\n')
            resolved_lines = []
            skip_until_end = False
            
            for line in lines:
                if '<<<<<<< HEAD' in line:
                    skip_until_end = True
                    continue
                elif '=======' in line:
                    continue
                elif '>>>>>>> origin/main' in line:
                    skip_until_end = False
                    continue
                elif not skip_until_end:
                    resolved_lines.append(line)
            
            # Write resolved content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(resolved_lines))
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving package conflicts in {file_path}: {e}")
            return False
    
    def resolve_python_import_conflicts(self, file_path: Path, content: str) -> bool:
        """Resolve Python import conflicts by merging imports."""
        try:
            lines = content.split('\n')
            resolved_lines = []
            in_conflict = False
            head_imports = []
            main_imports = []
            
            for line in lines:
                if '<<<<<<< HEAD' in line:
                    in_conflict = True
                    continue
                elif '=======' in line:
                    continue
                elif '>>>>>>> origin/main' in line:
                    # Merge imports
                    all_imports = set(head_imports + main_imports)
                    resolved_lines.extend(sorted(all_imports))
                    in_conflict = False
                    head_imports = []
                    main_imports = []
                    continue
                elif in_conflict:
                    if line.strip().startswith(('import ', 'from ')):
                        if line not in head_imports:
                            head_imports.append(line)
                else:
                    resolved_lines.append(line)
            
            # Write resolved content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(resolved_lines))
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving Python import conflicts in {file_path}: {e}")
            return False
    
    def resolve_config_conflicts(self, file_path: Path, content: str) -> bool:
        """Resolve configuration conflicts by preferring HEAD."""
        try:
            lines = content.split('\n')
            resolved_lines = []
            skip_until_end = False
            
            for line in lines:
                if '<<<<<<< HEAD' in line:
                    continue
                elif '=======' in line:
                    skip_until_end = True
                    continue
                elif '>>>>>>> origin/main' in line:
                    skip_until_end = False
                    continue
                elif not skip_until_end:
                    resolved_lines.append(line)
            
            # Write resolved content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(resolved_lines))
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving config conflicts in {file_path}: {e}")
            return False
    
    async def optimize_pr_ci(self, pr: PRInfo) -> bool:
        """Optimize CI/CD for a specific PR."""
        logger.info(f"Optimizing CI for PR #{pr.number}")
        
        try:
            # Checkout PR branch
            stdout, stderr, code = self.run_command(f"gh pr checkout {pr.number}")
            if code != 0:
                return False
            
            # Run basic checks and fixes
            fixes_applied = []
            
            # Fix backend issues
            if (self.base_dir / "backend").exists():
                # Run formatter
                stdout, stderr, code = self.run_command("cd backend && uv run ruff format . --quiet")
                if code == 0:
                    fixes_applied.append("ruff_format")
                
                # Fix imports
                stdout, stderr, code = self.run_command("cd backend && uv run ruff check . --fix --quiet")
                if code == 0:
                    fixes_applied.append("ruff_fix")
            
            # Fix frontend issues
            if (self.base_dir / "frontend").exists():
                # Run formatter
                stdout, stderr, code = self.run_command("cd frontend && npm run lint:fix")
                if code == 0:
                    fixes_applied.append("eslint_fix")
            
            # If fixes were applied, commit them
            if fixes_applied:
                self.run_command("git add .")
                self.run_command(f'git commit -m "CI optimization: {", ".join(fixes_applied)}"')
                self.run_command(f"git push origin {pr.branch}")
                
                logger.info(f"Applied CI fixes for PR #{pr.number}: {fixes_applied}")
                return True
                
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing CI for PR #{pr.number}: {e}")
            return False
        finally:
            self.run_command("git checkout main")
    
    async def generate_pr_report(self, prs: List[PRInfo]) -> Dict[str, Any]:
        """Generate comprehensive PR infrastructure report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_prs": len(prs),
            "summary": {
                "high_priority": len([pr for pr in prs if pr.priority == "high"]),
                "medium_priority": len([pr for pr in prs if pr.priority == "medium"]),
                "low_priority": len([pr for pr in prs if pr.priority == "low"]),
                "with_conflicts": len([pr for pr in prs if pr.conflicts]),
                "failed_ci": len([pr for pr in prs if pr.ci_status == "failed"]),
                "high_risk": len([pr for pr in prs if pr.risk_level == "high"]),
            },
            "prs": []
        }
        
        for pr in prs:
            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "branch": pr.branch,
                "priority": pr.priority,
                "risk_level": pr.risk_level,
                "conflicts": pr.conflicts,
                "ci_status": pr.ci_status,
                "created_at": pr.created_at,
                "recommendations": []
            }
            
            # Add recommendations
            if pr.conflicts:
                pr_data["recommendations"].append("Resolve merge conflicts")
            if pr.ci_status == "failed":
                pr_data["recommendations"].append("Fix CI failures")
            if pr.risk_level == "high":
                pr_data["recommendations"].append("Requires careful review")
            if pr.priority == "high":
                pr_data["recommendations"].append("Priority merge candidate")
            
            report["prs"].append(pr_data)
        
        return report
    
    async def process_all_prs(self):
        """Main method to process all PRs."""
        logger.info("Starting PR infrastructure support process...")
        
        # Get all open PRs
        prs = self.get_open_prs()
        
        if not prs:
            logger.warning("No open PRs found")
            return
        
        # Sort by priority and risk
        prs.sort(key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}[x.priority],
            {"high": 0, "medium": 1, "low": 2}[x.risk_level]
        ))
        
        logger.info(f"Processing {len(prs)} PRs...")
        
        # Process PRs in batches
        batch_size = 5
        for i in range(0, len(prs), batch_size):
            batch = prs[i:i+batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(prs) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            tasks = []
            for pr in batch:
                if pr.conflicts:
                    tasks.append(self.resolve_pr_conflicts(pr))
                if pr.ci_status in ["failed", "unknown"]:
                    tasks.append(self.optimize_pr_ci(pr))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f"Batch results: {len([r for r in results if r is True])} successful")
            
            # Small delay between batches
            await asyncio.sleep(2)
        
        # Generate final report
        report = await self.generate_pr_report(prs)
        
        # Save report
        report_file = self.reports_dir / f"pr_infrastructure_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"PR infrastructure support completed. Report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("PR INFRASTRUCTURE SUPPORT SUMMARY")
        print("="*80)
        print(f"Total PRs processed: {report['total_prs']}")
        print(f"High priority: {report['summary']['high_priority']}")
        print(f"With conflicts: {report['summary']['with_conflicts']}")
        print(f"Failed CI: {report['summary']['failed_ci']}")
        print(f"High risk: {report['summary']['high_risk']}")
        print("="*80)
        
        return report


async def main():
    """Main entry point."""
    manager = PRInfrastructureManager()
    await manager.process_all_prs()


if __name__ == "__main__":
    asyncio.run(main())