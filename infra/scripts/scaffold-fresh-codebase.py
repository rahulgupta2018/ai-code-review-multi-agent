#!/usr/bin/env python3
"""
Project Scaffolding Script for AI Code Review Multi-Agent System
Based on the latest ADK Multi-Agent System Design Document

This script generates a fresh codebase implementing the design document architecture:
- Master Orchestrator with cross-domain synthesis
- 9 Specialized Agents (Code Quality, Security, Architecture, Performance, Cloud Native, 
  Engineering Practices, Sustainability, Microservices, API Design)
- Flexible Agent Configuration & Plugin Framework
- LLM Guardrails & Quality Control
- Redis Session Management & Neo4j Knowledge Graph
- Multi-Format Report Generation
- Tree-sitter Multi-Language Analysis

Usage:
    python infra/scripts/scaffold-fresh-codebase.py [--dry-run] [--force] [--minimal]
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class FileTemplate:
    """Represents a file template to be generated"""
    path: str
    content: str
    executable: bool = False
    description: str = ""

@dataclass
class DirectoryStructure:
    """Represents the project directory structure"""
    directories: List[str] = field(default_factory=list)
    files: List[FileTemplate] = field(default_factory=list)

class ProjectScaffolder:
    """Main class for scaffolding the fresh codebase"""
    
    def __init__(self, project_root: Path, dry_run: bool = False, force: bool = False, minimal: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.force = force
        self.minimal = minimal
        self.src_dir = project_root / "src"
        self.config_dir = project_root / "config"
        self.tests_dir = project_root / "tests"
        
        # Remove old src if it exists and we're not in dry-run mode
        if not dry_run and (self.src_dir / "agents").exists():
            if not force:
                response = input(f"Directory {self.src_dir} already exists. Remove it? (y/N): ")
                if response.lower() != 'y':
                    print("Aborting scaffolding.")
                    sys.exit(1)
            
            import shutil
            if self.src_dir.exists():
                shutil.rmtree(self.src_dir)
                print(f"Removed existing {self.src_dir}")
    
    def generate_structure(self) -> DirectoryStructure:
        """Generate the complete project structure based on design document"""
        
        directories = [
            # Core source structure
            "src",
            "src/agents",
            "src/agents/orchestrator",
            "src/agents/base",
            "src/agents/base/tools",
            "src/agents/specialized",
            "src/agents/specialized/code_quality",
            "src/agents/specialized/code_quality/tools",
            "src/agents/specialized/security",
            "src/agents/specialized/security/tools", 
            "src/agents/specialized/architecture",
            "src/agents/specialized/architecture/tools",
            "src/agents/specialized/performance",
            "src/agents/specialized/performance/tools",
            "src/agents/specialized/cloud_native",
            "src/agents/specialized/cloud_native/tools",
            "src/agents/specialized/engineering_practices",
            "src/agents/specialized/engineering_practices/tools",
            "src/agents/specialized/sustainability",
            "src/agents/specialized/sustainability/tools",
            "src/agents/specialized/microservices", 
            "src/agents/specialized/microservices/tools",
            "src/agents/specialized/api_design",
            "src/agents/specialized/api_design/tools",
            "src/agents/plugins",
            
            # Core modules
            "src/core",
            "src/core/session",
            "src/core/knowledge_graph",
            "src/core/llm",
            "src/core/llm/providers",
            "src/core/llm/guardrails",
            "src/core/security", 
            "src/core/validation",
            "src/core/reporting",
            "src/core/tree_sitter",
            
            # Integration layers
            "src/integrations",
            "src/integrations/adk",
            "src/integrations/redis",
            "src/integrations/neo4j",
            
            # API layer
            "src/api",
            "src/api/v1",
            "src/api/middleware",
            
            # Configuration
            "config",
            "config/agents",
            "config/environments",
            "config/llm",
            "config/rules",
            "config/tree_sitter",
            
            # Tests
            "tests",
            "tests/unit",
            "tests/unit/agents", 
            "tests/unit/core",
            "tests/integration",
            "tests/e2e",
            "tests/fixtures",
            "tests/test_files",
            
            # Documentation
            "docs/agents",
            "docs/architecture",
            "docs/api",
            "docs/deployment",
        ]
        
        files = []
        
        # Generate core files
        files.extend(self._generate_core_files())
        
        # Generate agent files
        files.extend(self._generate_agent_files())
        
        # Generate configuration files
        files.extend(self._generate_config_files())
        
        # Generate test files
        files.extend(self._generate_test_files())
        
        # Generate integration files
        files.extend(self._generate_integration_files())
        
        # Generate API files
        files.extend(self._generate_api_files())
        
        # Generate documentation
        files.extend(self._generate_documentation_files())
        
        return DirectoryStructure(directories=directories, files=files)
    
    def _generate_core_files(self) -> List[FileTemplate]:
        """Generate core module files"""
        files = []
        
        # Main package init
        files.append(FileTemplate(
            path="src/__init__.py",
            content='"""AI Code Review Multi-Agent System with Google ADK Integration"""\n\n__version__ = "1.0.0"\n',
            description="Main package initialization"
        ))
        
        # Core module files
        files.extend([
            # Session management
            FileTemplate(
                path="src/core/__init__.py",
                content="",
                description="Core module initialization"
            ),
            
            FileTemplate(
                path="src/core/session/__init__.py", 
                content="",
                description="Session management module"
            ),
            
            FileTemplate(
                path="src/core/session/session_manager.py",
                content=self._get_session_manager_template(),
                description="ADK + Redis session management implementation"
            ),
            
            # Knowledge Graph
            FileTemplate(
                path="src/core/knowledge_graph/__init__.py",
                content="",
                description="Knowledge graph module"
            ),
            
            FileTemplate(
                path="src/core/knowledge_graph/neo4j_client.py",
                content=self._get_neo4j_client_template(),
                description="Neo4j knowledge graph client"
            ),
            
            FileTemplate(
                path="src/core/knowledge_graph/schema.py", 
                content=self._get_knowledge_graph_schema_template(),
                description="Knowledge graph schema definitions"
            ),
            
            # LLM and Guardrails
            FileTemplate(
                path="src/core/llm/__init__.py",
                content="",
                description="LLM module initialization"
            ),
            
            FileTemplate(
                path="src/core/llm/providers/__init__.py",
                content="",
                description="LLM providers module"
            ),
            
            FileTemplate(
                path="src/core/llm/providers/gemini.py",
                content=self._get_gemini_provider_template(),
                description="Google Gemini LLM provider"
            ),
            
            FileTemplate(
                path="src/core/llm/guardrails/__init__.py",
                content="",
                description="LLM guardrails module"
            ),
            
            FileTemplate(
                path="src/core/llm/guardrails/security.py",
                content=self._get_llm_security_template(),
                description="LLM input/output security controls"
            ),
            
            FileTemplate(
                path="src/core/llm/guardrails/bias_prevention.py",
                content=self._get_bias_prevention_template(),
                description="Bias prevention and output validation"
            ),
            
            # Tree-sitter integration
            FileTemplate(
                path="src/core/tree_sitter/__init__.py",
                content="",
                description="Tree-sitter module"
            ),
            
            FileTemplate(
                path="src/core/tree_sitter/parser.py",
                content=self._get_tree_sitter_parser_template(),
                description="Universal AST parser implementation"
            ),
            
            # Reporting
            FileTemplate(
                path="src/core/reporting/__init__.py",
                content="",
                description="Reporting module"
            ),
            
            FileTemplate(
                path="src/core/reporting/report_generator.py",
                content=self._get_report_generator_template(),
                description="Multi-format report generator"
            ),
        ])
        
        return files
    
    def _generate_agent_files(self) -> List[FileTemplate]:
        """Generate agent-related files"""
        files = []
        
        # Base agent framework
        files.extend([
            FileTemplate(
                path="src/agents/__init__.py",
                content="",
                description="Agents module initialization"
            ),
            
            FileTemplate(
                path="src/agents/base/__init__.py",
                content="",
                description="Base agents module"
            ),
            
            FileTemplate(
                path="src/agents/base/specialized_agent.py",
                content=self._get_base_specialized_agent_template(),
                description="Base class for all specialized agents"
            ),
            
            FileTemplate(
                path="src/agents/base/agent_registry.py",
                content=self._get_agent_registry_template(),
                description="Dynamic agent registry with plugin support"
            ),
            
            FileTemplate(
                path="src/agents/base/tools/__init__.py",
                content="",
                description="Base tools module"
            ),
            
            FileTemplate(
                path="src/agents/base/tools/deterministic_tool.py",
                content=self._get_deterministic_tool_template(),
                description="Base interface for deterministic tools"
            ),
            
            # Orchestrator
            FileTemplate(
                path="src/agents/orchestrator/__init__.py",
                content="",
                description="Orchestrator module"
            ),
            
            FileTemplate(
                path="src/agents/orchestrator/orchestrator.py",
                content=self._get_orchestrator_template(),
                description="Master orchestrator implementation"
            ),
            
            FileTemplate(
                path="src/agents/orchestrator/synthesis.py",
                content=self._get_synthesis_template(),
                description="Cross-domain synthesis engine"
            ),
        ])
        
        # Specialized agents
        agent_types = [
            ("code_quality", "Code Quality Agent", "General code quality, complexity, maintainability"),
            ("security", "Security Standards Agent", "Security vulnerabilities, OWASP compliance"),
            ("architecture", "Architecture Agent", "Design patterns, SOLID principles, modularity"),
            ("performance", "Performance Agent", "Performance bottlenecks, algorithmic complexity"),
            ("cloud_native", "Cloud Native Agent", "12-factor app compliance, containerization"),
            ("engineering_practices", "Engineering Practices Agent", "Code style, documentation, testing"),
            ("sustainability", "Sustainability Agent", "Carbon efficiency, green software practices"),
            ("microservices", "Microservices Agent", "Service decomposition, distributed systems"),
            ("api_design", "API Design Agent", "REST/GraphQL design, API documentation"),
        ]
        
        for agent_dir, agent_name, description in agent_types:
            files.extend([
                FileTemplate(
                    path=f"src/agents/specialized/{agent_dir}/__init__.py",
                    content="",
                    description=f"{agent_name} module"
                ),
                
                FileTemplate(
                    path=f"src/agents/specialized/{agent_dir}/agent.py",
                    content=self._get_specialized_agent_template(agent_dir, agent_name, description),
                    description=f"{agent_name} implementation"
                ),
                
                FileTemplate(
                    path=f"src/agents/specialized/{agent_dir}/tools/__init__.py",
                    content="",
                    description=f"{agent_name} tools module"
                ),
                
                FileTemplate(
                    path=f"src/agents/specialized/{agent_dir}/tools/analyzer.py",
                    content=self._get_agent_analyzer_template(agent_dir, agent_name),
                    description=f"{agent_name} analyzer tool"
                ),
            ])
        
        # Plugin framework
        files.extend([
            FileTemplate(
                path="src/agents/plugins/__init__.py",
                content="",
                description="Plugins module"
            ),
            
            FileTemplate(
                path="src/agents/plugins/plugin_interface.py",
                content=self._get_plugin_interface_template(),
                description="Plugin interface definition"
            ),
            
            FileTemplate(
                path="src/agents/plugins/example_plugin.py",
                content=self._get_example_plugin_template(),
                description="Example custom agent plugin"
            ),
        ])
        
        return files
    
    def _generate_config_files(self) -> List[FileTemplate]:
        """Generate configuration files"""
        files = []
        
        # Agent configuration
        files.extend([
            FileTemplate(
                path="config/agents/agent_registry.yaml",
                content=self._get_agent_registry_config(),
                description="Agent registry configuration"
            ),
            
            # Individual agent configurations
            FileTemplate(
                path="config/agents/code_quality.yaml",
                content=self._get_code_quality_agent_config(),
                description="Code Quality Agent configuration"
            ),
            
            FileTemplate(
                path="config/agents/security_standards.yaml",
                content=self._get_security_agent_config(),
                description="Security Standards Agent configuration"
            ),
            
            FileTemplate(
                path="config/agents/architecture.yaml",
                content=self._get_architecture_agent_config(),
                description="Architecture Agent configuration"
            ),
            
            FileTemplate(
                path="config/agents/performance.yaml",
                content=self._get_performance_agent_config(),
                description="Performance Agent configuration"
            ),
            
            FileTemplate(
                path="config/agents/cloud_native.yaml",
                content=self._get_cloud_native_agent_config(),
                description="Cloud Native Agent configuration"
            ),
            
            FileTemplate(
                path="config/agents/engineering_practices.yaml",
                content=self._get_engineering_practices_agent_config(),
                description="Engineering Practices Agent configuration"
            ),
            
            FileTemplate(
                path="config/agents/sustainability.yaml",
                content=self._get_sustainability_agent_config(),
                description="Sustainability Agent configuration"
            ),
            
            FileTemplate(
                path="config/agents/microservices.yaml",
                content=self._get_microservices_agent_config(),
                description="Microservices Agent configuration"
            ),
            
            FileTemplate(
                path="config/agents/api_design.yaml",
                content=self._get_api_design_agent_config(),
                description="API Design Agent configuration"
            ),
            
            # Environment configurations
            FileTemplate(
                path="config/environments/development.yaml",
                content=self._get_development_config(),
                description="Development environment configuration"
            ),
            
            FileTemplate(
                path="config/environments/staging.yaml",
                content=self._get_staging_config(),
                description="Staging environment configuration"
            ),
            
            FileTemplate(
                path="config/environments/production.yaml",
                content=self._get_production_config(),
                description="Production environment configuration"
            ),
            
            # LLM configurations
            FileTemplate(
                path="config/llm/security_controls.yaml",
                content=self._get_llm_security_config(),
                description="LLM security controls configuration"
            ),
            
            FileTemplate(
                path="config/llm/quality_control.yaml",
                content=self._get_quality_control_config(),
                description="Quality control configuration"
            ),
            
            FileTemplate(
                path="config/llm/models.yaml",
                content=self._get_llm_models_config(),
                description="LLM models configuration"
            ),
            
            FileTemplate(
                path="config/llm/cost_optimization.yaml",
                content=self._get_cost_optimization_config(),
                description="LLM cost optimization configuration"
            ),
            
            # Rules and guidelines
            FileTemplate(
                path="config/rules/bias_prevention.yaml",
                content=self._get_bias_prevention_config(),
                description="Bias prevention rules"
            ),
            
            FileTemplate(
                path="config/rules/quality_gates.yaml",
                content=self._get_quality_gates_config(),
                description="Quality gates configuration"
            ),
            
            FileTemplate(
                path="config/rules/security_rules.yaml",
                content=self._get_security_rules_config(),
                description="Security analysis rules"
            ),
            
            # Tree-sitter configuration
            FileTemplate(
                path="config/tree_sitter/languages.yaml",
                content=self._get_tree_sitter_config(),
                description="Tree-sitter language configuration"
            ),
            
            FileTemplate(
                path="config/tree_sitter/patterns.yaml",
                content=self._get_tree_sitter_patterns_config(),
                description="Tree-sitter analysis patterns"
            ),
            
            # Integration configurations
            FileTemplate(
                path="config/integrations/redis.yaml",
                content=self._get_redis_config(),
                description="Redis integration configuration"
            ),
            
            FileTemplate(
                path="config/integrations/neo4j.yaml",
                content=self._get_neo4j_config(),
                description="Neo4j integration configuration"
            ),
            
            FileTemplate(
                path="config/integrations/adk.yaml",
                content=self._get_adk_config(),
                description="ADK integration configuration"
            ),
            
            # Reporting configuration
            FileTemplate(
                path="config/reporting/formats.yaml",
                content=self._get_reporting_formats_config(),
                description="Report format configurations"
            ),
            
            FileTemplate(
                path="config/reporting/templates.yaml",
                content=self._get_reporting_templates_config(),
                description="Report template configurations"
            ),
        ])
        
        return files
    
    def _generate_integration_files(self) -> List[FileTemplate]:
        """Generate integration layer files"""
        files = []
        
        files.extend([
            # ADK Integration
            FileTemplate(
                path="src/integrations/__init__.py",
                content="",
                description="Integrations module"
            ),
            
            FileTemplate(
                path="src/integrations/adk/__init__.py",
                content="",
                description="ADK integration module"
            ),
            
            FileTemplate(
                path="src/integrations/adk/agent_discovery.py",
                content=self._get_adk_discovery_template(),
                description="ADK agent discovery implementation"
            ),
            
            # Redis Integration
            FileTemplate(
                path="src/integrations/redis/__init__.py",
                content="",
                description="Redis integration module"
            ),
            
            FileTemplate(
                path="src/integrations/redis/client.py",
                content=self._get_redis_client_template(),
                description="Redis client implementation"
            ),
            
            # Neo4j Integration
            FileTemplate(
                path="src/integrations/neo4j/__init__.py",
                content="",
                description="Neo4j integration module"
            ),
            
            FileTemplate(
                path="src/integrations/neo4j/client.py",
                content=self._get_neo4j_integration_template(),
                description="Neo4j integration client"
            ),
        ])
        
        return files
    
    def _generate_api_files(self) -> List[FileTemplate]:
        """Generate API layer files"""
        files = []
        
        files.extend([
            FileTemplate(
                path="src/api/__init__.py",
                content="",
                description="API module"
            ),
            
            FileTemplate(
                path="src/api/main.py",
                content=self._get_api_main_template(),
                description="FastAPI application main file"
            ),
            
            FileTemplate(
                path="src/api/v1/__init__.py",
                content="",
                description="API v1 module"
            ),
            
            FileTemplate(
                path="src/api/v1/analysis.py",
                content=self._get_analysis_api_template(),
                description="Analysis API endpoints"
            ),
            
            FileTemplate(
                path="src/api/middleware/__init__.py",
                content="",
                description="API middleware module"
            ),
            
            FileTemplate(
                path="src/api/middleware/security.py",
                content=self._get_api_security_template(),
                description="API security middleware"
            ),
        ])
        
        return files
    
    def _generate_test_files(self) -> List[FileTemplate]:
        """Generate test files"""
        files = []
        
        files.extend([
            FileTemplate(
                path="tests/__init__.py",
                content="",
                description="Tests module"
            ),
            
            FileTemplate(
                path="tests/conftest.py",
                content=self._get_test_conftest_template(),
                description="Pytest configuration and fixtures"
            ),
            
            FileTemplate(
                path="tests/unit/__init__.py",
                content="",
                description="Unit tests module"
            ),
            
            FileTemplate(
                path="tests/unit/agents/__init__.py",
                content="",
                description="Agent unit tests module"
            ),
            
            FileTemplate(
                path="tests/unit/agents/test_orchestrator.py",
                content=self._get_orchestrator_test_template(),
                description="Orchestrator unit tests"
            ),
            
            FileTemplate(
                path="tests/unit/core/__init__.py",
                content="",
                description="Core unit tests module"
            ),
            
            FileTemplate(
                path="tests/unit/core/test_session_manager.py",
                content=self._get_session_manager_test_template(),
                description="Session manager unit tests"
            ),
            
            FileTemplate(
                path="tests/integration/__init__.py",
                content="",
                description="Integration tests module"
            ),
            
            FileTemplate(
                path="tests/integration/test_adk_integration.py",
                content=self._get_adk_integration_test_template(),
                description="ADK integration tests"
            ),
            
            FileTemplate(
                path="tests/e2e/__init__.py",
                content="",
                description="End-to-end tests module"
            ),
            
            FileTemplate(
                path="tests/e2e/test_full_analysis.py",
                content=self._get_e2e_test_template(),
                description="End-to-end analysis tests"
            ),
        ])
        
        return files
    
    def _generate_documentation_files(self) -> List[FileTemplate]:
        """Generate documentation files"""
        files = []
        
        files.extend([
            FileTemplate(
                path="docs/agents/README.md",
                content=self._get_agents_docs_template(),
                description="Agent documentation"
            ),
            
            FileTemplate(
                path="docs/architecture/README.md",
                content=self._get_architecture_docs_template(),
                description="Architecture documentation"
            ),
            
            FileTemplate(
                path="docs/api/README.md",
                content=self._get_api_docs_template(),
                description="API documentation"
            ),
        ])
        
        return files
    
    def scaffold(self):
        """Execute the scaffolding process"""
        print("🏗️  AI Code Review Multi-Agent System - Project Scaffolding")
        print("=" * 60)
        print(f"📁 Project Root: {self.project_root}")
        print(f"🔧 Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"⚡ Minimal: {self.minimal}")
        print()
        
        # Generate structure
        structure = self.generate_structure()
        
        print(f"📂 Directories to create: {len(structure.directories)}")
        print(f"📄 Files to generate: {len(structure.files)}")
        print()
        
        if self.dry_run:
            print("👀 DRY RUN - showing what would be created:")
            print()
            
            print("📂 Directories:")
            for directory in structure.directories:
                print(f"  📁 {directory}")
            
            print()
            print("📄 Files:")
            for file_template in structure.files:
                print(f"  📄 {file_template.path} - {file_template.description}")
            
            print()
            print("🔍 To actually create the files, run without --dry-run")
            return
        
        # Create directories
        print("📂 Creating directories...")
        for directory in structure.directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created: {directory}")
        
        print()
        
        # Create files
        print("📄 Creating files...")
        for file_template in structure.files:
            file_path = self.project_root / file_template.path
            
            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_template.content)
            
            # Make executable if needed
            if file_template.executable:
                os.chmod(file_path, 0o755)
            
            print(f"  ✅ Created: {file_template.path} - {file_template.description}")
        
        print()
        print("🎉 Project scaffolding completed successfully!")
        print()
        print("Next steps:")
        print("1. Review the generated configuration files in config/")
        print("2. Update environment variables in .env")
        print("3. Run the development setup: ./infra/scripts/dev-setup.sh up")
        print("4. Run tests: pytest tests/")
        print("5. Start implementing the specific analysis tools for each agent")
    
    # Template methods - these would contain the actual file content templates
    # For brevity, I'm including just a few key examples
    
    def _get_session_manager_template(self) -> str:
        return '''"""
ADK + Redis Session Management Implementation
Enhanced session management with Redis backend for persistence and pub/sub
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from google.adk.core.session import InMemorySessionService, Session
from google.adk.core import types

from ..integrations.redis.client import get_redis_client


class CodeReviewSessionManager:
    """Enhanced session management with Redis backend following ADK patterns"""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.redis_client: Optional[aioredis.Redis] = None
        self.app_name = "ai_code_review_multi_agent"
        self.session_ttl = 3600  # 1 hour default
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = await get_redis_client()
    
    async def create_analysis_session(self, 
                                    user_id: str, 
                                    session_id: str,
                                    files: List[str], 
                                    options: Dict[str, Any] = None) -> Session:
        """Create a new analysis session with Redis persistence"""
        
        # Create ADK session
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        # Initialize session state
        session_state = {
            'analysis_request': {
                'files': files,
                'analysis_domains': options.get('agents', []) if options else [],
                'options': options or {},
                'user_preferences': {
                    'detail_level': 'standard',
                    'priority_focus': 'security',
                    'output_format': 'json'
                }
            },
            'analysis_progress': {
                'current_phase': 'initialization',
                'completed_agents': [],
                'failed_agents': [],
                'progress_percentage': 0
            },
            'agent_results': {},
            'session_metadata': {
                'start_time': datetime.now().isoformat(),
                'created_by': user_id,
                'session_version': '1.0'
            }
        }
        
        # Store in Redis for persistence
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_state)
            )
        
        # Store in ADK session
        await session.store_data("session_state", session_state)
        
        return session
    
    async def update_session_progress(self, 
                                    user_id: str, 
                                    session_id: str,
                                    phase: str, 
                                    agent: str, 
                                    status: str):
        """Update session progress with Redis sync"""
        
        # Get current session
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id, 
            session_id=session_id
        )
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Update progress
        session_state = await session.get_data("session_state") or {}
        
        if 'analysis_progress' not in session_state:
            session_state['analysis_progress'] = {
                'current_phase': phase,
                'completed_agents': [],
                'failed_agents': []
            }
        
        session_state['analysis_progress']['current_phase'] = phase
        
        if status == 'completed':
            if agent not in session_state['analysis_progress']['completed_agents']:
                session_state['analysis_progress']['completed_agents'].append(agent)
        elif status == 'failed':
            if agent not in session_state['analysis_progress']['failed_agents']:
                session_state['analysis_progress']['failed_agents'].append(agent)
        
        # Calculate progress percentage
        total_agents = 9  # Based on our 9 specialized agents
        completed = len(session_state['analysis_progress']['completed_agents'])
        session_state['analysis_progress']['progress_percentage'] = (completed / total_agents) * 100
        
        # Update both ADK session and Redis
        await session.store_data("session_state", session_state)
        
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_state)
            )
            
            # Publish progress update
            await self.redis_client.publish(
                f"session:progress:{session_id}",
                json.dumps({
                    'phase': phase,
                    'agent': agent,
                    'status': status,
                    'progress': session_state['analysis_progress']['progress_percentage'],
                    'timestamp': datetime.now().isoformat()
                })
            )
    
    async def store_agent_results(self, 
                                user_id: str, 
                                session_id: str,
                                agent_name: str, 
                                results: Dict[str, Any]):
        """Store agent analysis results"""
        
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session_state = await session.get_data("session_state") or {}
        
        if 'agent_results' not in session_state:
            session_state['agent_results'] = {}
        
        session_state['agent_results'][agent_name] = results
        
        # Update both stores
        await session.store_data("session_state", session_state)
        
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_state)
            )
    
    async def get_session_state(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete session state"""
        
        # Try Redis first for persistence
        if self.redis_client:
            redis_data = await self.redis_client.get(f"session:{session_id}")
            if redis_data:
                return json.loads(redis_data)
        
        # Fallback to ADK session
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if session:
            return await session.get_data("session_state")
        
        return None
    
    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions (background task)"""
        
        if not self.redis_client:
            return
        
        # Redis handles TTL automatically, but we can cleanup ADK sessions
        # This would be run as a background task
        pass
'''
    
    def _get_orchestrator_template(self) -> str:
        return '''"""
Master Orchestrator Implementation
Central coordinator for multi-agent code analysis with cross-domain synthesis
"""

import asyncio
import json
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime

from google.adk.core import BaseAgent, InvocationContext, Event, types
from google.adk.core.agents import Agent, Runner

from ..base.agent_registry import DynamicAgentRegistry
from ..base.specialized_agent import BaseSpecializedAgent
from ...core.session.session_manager import CodeReviewSessionManager
from ...core.llm.guardrails.security import SecureLLMContextManager
from ...core.llm.guardrails.bias_prevention import LLMOutputValidator
from ...core.reporting.report_generator import MasterOrchestratorReportGenerator


class CodeReviewOrchestrator(BaseAgent):
    """Master orchestrator for AI code review with intelligent sub-agent delegation"""
    
    def __init__(self):
        super().__init__(
            name="code_review_orchestrator",
            description="Master orchestrator for AI code review with intelligent sub-agent delegation"
        )
        
        # Session management (ADK pattern)
        self.session_manager = CodeReviewSessionManager()
        
        # Comprehensive LLM for cross-domain synthesis
        self.synthesis_model = "gemini-1.5-pro"
        
        # Security and validation
        self.security_manager = SecureLLMContextManager()
        self.output_validator = LLMOutputValidator()
        
        # Report generation
        self.report_generator = MasterOrchestratorReportGenerator()
        
        # Dynamic agent registry
        self.agent_registry = DynamicAgentRegistry()
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Main orchestration workflow with sub-agent delegation"""
        
        try:
            # Phase 1: Initialize Session and Parse Request
            request = self._parse_request(ctx)
            
            session = await self.session_manager.create_analysis_session(
                user_id=ctx.user_id,
                session_id=ctx.session_id,
                files=request.get('files', []),
                options=request.get('options', {})
            )
            
            yield self._create_status_event("Analysis session initialized")
            
            # Phase 2: Delegate to Specialized Sub-Agents
            yield self._create_status_event("Delegating to specialized agents")
            
            agent_results = {}
            active_agents = self.agent_registry.get_active_agents()
            
            for agent_name, sub_agent in active_agents.items():
                try:
                    # Update session progress
                    await self.session_manager.update_session_progress(
                        ctx.user_id, ctx.session_id, 
                        'agent_analysis', agent_name, 'started'
                    )
                    
                    # Delegate to sub-agent (ADK delegation pattern)
                    sub_agent_results = await self._delegate_to_sub_agent(sub_agent, request, ctx)
                    agent_results[agent_name] = sub_agent_results
                    
                    # Store results in session
                    await self.session_manager.store_agent_results(
                        ctx.user_id, ctx.session_id, 
                        agent_name, sub_agent_results
                    )
                    
                    # Update progress
                    await self.session_manager.update_session_progress(
                        ctx.user_id, ctx.session_id, 
                        'agent_analysis', agent_name, 'completed'
                    )
                    
                    yield self._create_progress_event(f"{agent_name} analysis complete")
                    
                except Exception as e:
                    # Handle agent failure gracefully
                    await self.session_manager.update_session_progress(
                        ctx.user_id, ctx.session_id, 
                        'agent_analysis', agent_name, 'failed'
                    )
                    
                    agent_results[agent_name] = {
                        'error': str(e),
                        'status': 'failed',
                        'fallback_summary': f"{agent_name} analysis failed but system continues"
                    }
                    
                    yield self._create_status_event(f"{agent_name} failed, continuing with other agents")
            
            # Phase 3: Cross-Domain Synthesis
            yield self._create_status_event("Performing cross-domain synthesis")
            
            await self.session_manager.update_session_progress(
                ctx.user_id, ctx.session_id, 'synthesis', 'orchestrator', 'started'
            )
            
            final_report = await self._perform_cross_domain_synthesis(agent_results, ctx)
            
            # Phase 4: Generate Comprehensive Report
            yield self._create_status_event("Generating comprehensive report")
            
            comprehensive_report = await self.report_generator.generate_comprehensive_report(
                orchestrator_results=final_report,
                agent_outputs=agent_results,
                analysis_metadata={
                    'user_id': ctx.user_id,
                    'session_id': ctx.session_id,
                    'files_analyzed': len(request.get('files', [])),
                    'agents_used': list(agent_results.keys()),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            )
            
            # Phase 5: Finalize Session
            await self._finalize_session(ctx.user_id, ctx.session_id, comprehensive_report)
            
            yield self._create_final_event(comprehensive_report)
            
        except Exception as e:
            error_report = {
                'error': str(e),
                'status': 'orchestration_failed',
                'partial_results': agent_results if 'agent_results' in locals() else {}
            }
            yield self._create_error_event(error_report)
    
    async def _delegate_to_sub_agent(self, 
                                   sub_agent: BaseSpecializedAgent, 
                                   request: Dict, 
                                   ctx: InvocationContext) -> Dict:
        """Delegate analysis to a specialized sub-agent (ADK delegation pattern)"""
        
        # Create sub-context for the specialized agent
        sub_context = self._create_sub_context(ctx, request['files'])
        
        # Execute sub-agent using ADK delegation
        agent_events = []
        async for event in sub_agent._run_async_impl(sub_context):
            agent_events.append(event)
        
        # Extract final results from sub-agent events
        return self._extract_results_from_agent_events(agent_events)
    
    async def _perform_cross_domain_synthesis(self, 
                                            agent_results: Dict, 
                                            ctx: InvocationContext) -> Dict:
        """Perform comprehensive cross-domain synthesis using powerful LLM"""
        
        try:
            # Create synthesis prompt with security controls
            synthesis_prompt = await self._create_secure_synthesis_prompt(agent_results)
            
            # Use comprehensive model for synthesis
            synthesis_agent = Agent(
                name="cross_domain_synthesizer",
                model=self.synthesis_model,
                description="Cross-domain code review synthesizer",
                instruction="""You are a senior technical architect performing cross-domain 
                analysis synthesis. Analyze results from multiple specialized agents and provide:
                1. Executive summary of overall code quality
                2. Critical issues requiring immediate attention  
                3. Cross-domain patterns and relationships
                4. Prioritized recommendations
                5. Overall risk assessment
                Be comprehensive but concise. Focus on actionable insights."""
            )
            
            # Execute synthesis with validation
            content = types.Content(
                role='user',
                parts=[types.Part(text=synthesis_prompt)]
            )
            
            temp_runner = Runner(
                agent=synthesis_agent,
                app_name=self.session_manager.app_name,
                session_service=self.session_manager.session_service
            )
            
            synthesis_result = ""
            async for event in temp_runner.run_async(
                user_id=ctx.user_id,
                session_id=f"{ctx.session_id}_synthesis",
                new_message=content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    synthesis_result = event.content.parts[0].text
                    break
            
            # Validate synthesis output
            validation_result = await self.output_validator.validate_agent_output(
                synthesis_result,
                agent_results,
                "orchestrator"
            )
            
            if not validation_result.is_valid:
                # Use fallback synthesis if validation fails
                synthesis_result = self._create_fallback_synthesis(agent_results)
            
            return {
                'executive_summary': self._extract_executive_summary(synthesis_result),
                'critical_issues': self._extract_critical_issues(synthesis_result),
                'cross_domain_patterns': self._identify_cross_patterns(agent_results),
                'prioritized_recommendations': self._prioritize_recommendations(synthesis_result),
                'overall_risk_score': self._calculate_risk_score(agent_results),
                'agent_results': agent_results,
                'synthesis_text': synthesis_result,
                'validation_metadata': validation_result.metadata,
                'metadata': {
                    'synthesis_model': self.synthesis_model,
                    'successful_agents': len([r for r in agent_results.values() if 'error' not in r]),
                    'total_agents': len(agent_results),
                    'synthesis_timestamp': datetime.now().isoformat(),
                    'confidence_score': validation_result.confidence_score
                }
            }
            
        except Exception as e:
            # Fallback synthesis without LLM
            return {
                'agent_results': agent_results,
                'structured_summary': self._create_structured_summary(agent_results),
                'error': f"Cross-domain synthesis failed: {str(e)}",
                'fallback_mode': True
            }
    
    def _parse_request(self, ctx: InvocationContext) -> Dict[str, Any]:
        """Parse analysis request from context"""
        # Implementation would extract files and options from context
        return {
            'files': [],  # Extract from context
            'options': {}  # Extract from context
        }
    
    def _create_status_event(self, message: str) -> Event:
        """Create status event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=message)]),
            actions=types.EventActions(
                state_delta={'status': message}
            )
        )
    
    def _create_progress_event(self, message: str) -> Event:
        """Create progress event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=message)]),
            actions=types.EventActions(
                state_delta={'progress': message}
            )
        )
    
    def _create_final_event(self, report: Dict[str, Any]) -> Event:
        """Create final event with comprehensive report"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Analysis complete")]),
            actions=types.EventActions(
                state_delta={'final_report': report},
                artifact_delta={'comprehensive_report': json.dumps(report)}
            )
        )
    
    def _create_error_event(self, error_info: Dict[str, Any]) -> Event:
        """Create error event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Error: {error_info.get('error', 'Unknown error')}")]),
            actions=types.EventActions(
                state_delta={'error': error_info}
            )
        )
'''
    
    def _get_base_specialized_agent_template(self) -> str:
        return '''"""
Base Specialized Agent Implementation
Base class for all specialized analysis agents with lightweight LLM integration
"""

import asyncio
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime
from abc import ABC, abstractmethod

from google.adk.core import BaseAgent, InvocationContext, Event, types
from google.adk.core.agents import Agent, Runner
from google.adk.core.session import InMemorySessionService

from .tools.deterministic_tool import BaseDeterministicTool
from ..core.llm.guardrails.security import SecureLLMContextManager
from ..core.llm.guardrails.bias_prevention import LLMOutputValidator


class BaseSpecializedAgent(BaseAgent, ABC):
    """Base class for all specialized analysis agents with lightweight LLM integration"""
    
    def __init__(self, name: str, description: str, tools: List[BaseDeterministicTool], 
                 lightweight_model: str = "gemini-2.0-flash"):
        super().__init__(name=name, description=description)
        self.tools = tools
        self.supported_languages = []
        # Lightweight LLM for domain-specific insights
        self.lightweight_model = lightweight_model
        self.domain_expertise = self._define_domain_expertise()
        
        # Security and validation
        self.security_manager = SecureLLMContextManager()
        self.output_validator = LLMOutputValidator()
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Standard specialized agent workflow with lightweight LLM synthesis"""
        
        files = self._extract_files_from_context(ctx)
        yield self._create_status_event(f"Starting {self.name} analysis")
        
        # Phase 1: Deterministic Analysis
        raw_results = []
        for file_path in files:
            if self._is_language_supported(file_path):
                file_results = await self._analyze_file_deterministic(file_path)
                raw_results.append(file_results)
        
        yield self._create_progress_event("Deterministic analysis complete, generating domain insights")
        
        # Phase 2: Lightweight LLM Domain Insights (following Google ADK pattern)
        if raw_results:
            domain_insights = await self._generate_domain_insights(raw_results, ctx)
            yield self._create_progress_event("Domain insights generated")
        else:
            domain_insights = {"insights": "No files to analyze in this domain", "status": "no_input"}
        
        # Phase 3: Package Results
        final_results = {
            'agent': self.name,
            'raw_analysis': raw_results,
            'domain_insights': domain_insights,
            'timestamp': datetime.now().isoformat(),
            'file_count': len(raw_results)
        }
        
        yield self._create_results_event(final_results)
    
    async def _analyze_file_deterministic(self, file_path: str) -> Dict:
        """Analyze a single file using deterministic tools"""
        
        results = {}
        for tool in self.tools:
            try:
                tool_result = await tool.analyze(file_path)
                results[tool.name] = tool_result
            except Exception as e:
                results[tool.name] = {'error': str(e), 'status': 'failed'}
        
        return {
            'file': file_path,
            'analysis_domain': self.name,
            'deterministic_results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _generate_domain_insights(self, raw_results: List[Dict], ctx: InvocationContext) -> Dict:
        """Generate lightweight domain-specific insights using LLM (ADK pattern)"""
        
        try:
            # Create domain-specific analysis prompt with security controls
            analysis_prompt = await self._create_secure_domain_prompt(raw_results)
            
            # Use ADK's Runner pattern for lightweight LLM call
            domain_analyzer = Agent(
                name=f"{self.name}_analyzer",
                model=self.lightweight_model,
                description=f"Domain expert for {self.name} analysis",
                instruction=f"""You are a {self.name} domain expert. 
                Analyze the provided deterministic data and generate focused insights.
                {self.domain_expertise}
                Be concise, factual, and focus only on {self.name} aspects.
                Provide actionable recommendations."""
            )
            
            # Create content for the domain analyzer
            content = types.Content(
                role='user', 
                parts=[types.Part(text=analysis_prompt)]
            )
            
            # Use InMemorySessionService for lightweight session
            temp_session_service = InMemorySessionService()
            temp_session = await temp_session_service.create_session(
                app_name=f"{self.name}_analysis",
                user_id="system",
                session_id=f"analysis_{datetime.now().timestamp()}"
            )
            
            # Create runner for domain analysis
            temp_runner = Runner(
                agent=domain_analyzer,
                app_name=f"{self.name}_analysis",
                session_service=temp_session_service
            )
            
            # Execute domain analysis
            final_response = ""
            async for event in temp_runner.run_async(
                user_id="system",
                session_id=temp_session.session_id,
                new_message=content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                    break
            
            # Validate output
            validation_result = await self.output_validator.validate_agent_output(
                final_response,
                raw_results,
                self.name
            )
            
            if not validation_result.is_valid:
                # Fallback to deterministic summary
                final_response = self._create_deterministic_summary(raw_results)
            
            return {
                'insights': final_response,
                'model_used': self.lightweight_model,
                'confidence': validation_result.confidence_score,
                'key_findings': self._extract_key_findings(final_response),
                'recommendations': self._extract_recommendations(final_response),
                'validation_metadata': validation_result.metadata,
                'status': 'success'
            }
            
        except Exception as e:
            # Fallback to deterministic summary
            return {
                'insights': self._create_deterministic_summary(raw_results),
                'error': str(e),
                'model_used': 'deterministic_fallback',
                'status': 'fallback'
            }
    
    @abstractmethod
    def _define_domain_expertise(self) -> str:
        """Define domain-specific expertise - must be implemented by subclasses"""
        pass
    
    def _extract_files_from_context(self, ctx: InvocationContext) -> List[str]:
        """Extract file list from invocation context"""
        # Implementation would extract files from context
        return []
    
    def _is_language_supported(self, file_path: str) -> bool:
        """Check if file language is supported by this agent"""
        # Implementation would check file extension against supported languages
        return True
    
    def _create_status_event(self, message: str) -> Event:
        """Create status event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=message)]),
            actions=types.EventActions(
                state_delta={'status': message}
            )
        )
    
    def _create_progress_event(self, message: str) -> Event:
        """Create progress event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=message)]),
            actions=types.EventActions(
                state_delta={'progress': message}
            )
        )
    
    def _create_results_event(self, results: Dict) -> Event:
        """Create results event"""
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Analysis complete")]),
            actions=types.EventActions(
                state_delta={'results': results},
                artifact_delta={'analysis_data': json.dumps(results)}
            )
        )
'''
    
    # Additional template methods would follow similar patterns...
    # For brevity, I'm including placeholders for the remaining templates
    
    def _get_agent_registry_template(self) -> str:
        return "# Agent Registry Implementation\n# TODO: Implement dynamic agent registry"
    
    def _get_deterministic_tool_template(self) -> str:
        return "# Base Deterministic Tool Interface\n# TODO: Implement base tool interface"
    
    def _get_specialized_agent_template(self, agent_dir: str, agent_name: str, description: str) -> str:
        return f"# {agent_name} Implementation\n# Domain: {description}\n# TODO: Implement {agent_name}"
    
    def _get_agent_analyzer_template(self, agent_dir: str, agent_name: str) -> str:
        return f"# {agent_name} Analyzer Tool\n# TODO: Implement domain-specific analyzer"
    
    # Configuration templates
    def _get_agent_registry_config(self) -> str:
        return """# Agent Registry Configuration
# Controls which agents are enabled and their execution parameters
agents:
  enabled_agents:
    - code_quality
    - security_standards  
    - architecture
    - performance
    - cloud_native
    - engineering_practices
    - sustainability
    - microservices
    - api_design
  
  agent_priorities:
    security_standards: 1.0    # Critical for production systems
    code_quality: 0.9         # High importance for maintainability
    performance: 0.8          # Important for user experience
    architecture: 0.7         # Important for long-term success
    sustainability: 0.6       # Moderate importance, growing
    microservices: 0.5        # Context-dependent
    api_design: 0.5           # Context-dependent
    cloud_native: 0.4         # Lower priority for non-cloud projects
    engineering_practices: 0.3 # Basic hygiene, always enabled

  execution_strategy:
    parallel_execution: true   # Run agents in parallel for speed
    fail_fast: false         # Continue analysis if some agents fail
    timeout_seconds: 300     # Max time per agent
    retry_count: 2           # Retry failed agents
    
  # Agent-specific configurations
  agent_configs:
    code_quality:
      complexity_threshold: 15
      maintainability_min_score: 60
      enable_refactoring_suggestions: true
      
    security_standards:
      compliance_frameworks: ["OWASP", "NIST"]
      vulnerability_severity_threshold: "medium"
      enable_dependency_scanning: true
      
    architecture:
      pattern_detection: true
      coupling_analysis: true
      solid_principles_check: true
      
    performance:
      algorithm_analysis: true
      resource_optimization: true
      benchmark_comparisons: true
      
    cloud_native:
      twelve_factor_compliance: true
      container_best_practices: true
      kubernetes_patterns: true
      
    engineering_practices:
      style_enforcement: true
      documentation_coverage: true
      test_pattern_analysis: true
      
    sustainability:
      energy_efficiency_analysis: true
      carbon_footprint_estimation: true
      green_coding_patterns: true
      
    microservices:
      service_boundary_analysis: true
      communication_pattern_detection: true
      distributed_system_patterns: true
      
    api_design:
      rest_design_principles: true
      graphql_schema_analysis: true
      documentation_quality: true
"""
    
    def _get_development_config(self) -> str:
        return """# Development Environment Configuration
# Optimized for learning and rapid development
environment: development

agents:
  enabled_agents:
    - code_quality           # Focus on code learning
    - engineering_practices  # Build good habits
    - architecture           # Design patterns
    - sustainability         # Optional: Learn green practices
  
  agent_configs:
    code_quality:
      learning_mode: true
      detailed_explanations: true
      severity_adjustment: lenient
      provide_examples: true
      
    engineering_practices:
      style_enforcement: relaxed
      documentation_requirements: basic
      test_coverage_threshold: 50
      
    architecture:
      pattern_suggestions: true
      design_alternatives: true
      educational_mode: true
      
    sustainability:
      educational_insights: true
      optimization_suggestions: basic

llm:
  models:
    orchestrator: "ollama/llama3.1:8b"  # Local model for dev
    agents: "ollama/llama3.1:8b"        # Local model for dev
  
  cost_optimization:
    use_cache_aggressively: true
    limit_context_size: true
    fallback_to_deterministic: true

session:
  ttl_seconds: 1800  # 30 minutes
  cleanup_frequency: 300  # 5 minutes

quality_control:
  confidence_threshold: 0.5  # Lower threshold for learning
  human_review_trigger: 0.2
  enable_fallbacks: true
"""
    
    def _get_production_config(self) -> str:
        return """# Production Environment Configuration  
# Optimized for reliability, security, and comprehensive analysis
environment: production

agents:
  enabled_agents:
    - security_standards      # Critical in production
    - performance            # User experience matters
    - sustainability         # Cost/environmental optimization
    - architecture           # Long-term maintainability
    - api_design            # Production API quality
    - cloud_native          # Production deployment patterns
    - code_quality          # Overall quality assurance
    - microservices         # If using microservices architecture
  
  agent_configs:
    security_standards:
      strict_mode: true
      compliance_frameworks: ["OWASP", "NIST", "CWE"]
      fail_on_critical: true
      vulnerability_database_updates: "daily"
      
    performance:
      benchmark_mode: production
      latency_thresholds: strict
      memory_optimization: true
      algorithm_complexity_analysis: true
      
    sustainability:
      carbon_tracking: true
      cost_optimization: true
      energy_monitoring: true
      green_metrics_reporting: true
      
    architecture:
      enterprise_patterns: true
      scalability_analysis: true
      maintainability_focus: true
      technical_debt_tracking: true
      
    api_design:
      production_readiness: true
      versioning_compliance: true
      documentation_completeness: true
      security_integration: true
      
    cloud_native:
      production_patterns: true
      observability_requirements: true
      reliability_patterns: true
      cost_optimization: true

llm:
  models:
    orchestrator: "gemini-1.5-pro"     # Comprehensive model
    agents: "gemini-2.0-flash"         # Efficient model
  
  cost_optimization:
    intelligent_batching: true
    cache_results: true
    progressive_analysis: true

session:
  ttl_seconds: 3600  # 1 hour
  cleanup_frequency: 600  # 10 minutes
  persistence: redis

quality_control:
  confidence_threshold: 0.8  # High threshold for production
  human_review_trigger: 0.5
  validation_required: true
  bias_prevention: strict

monitoring:
  enable_metrics: true
  track_performance: true
  alert_on_failures: true
"""

    def _get_llm_security_config(self) -> str:
        return """# LLM Security Controls Configuration
# Comprehensive security measures for LLM interactions

input_security:
  prompt_injection_detection:
    enabled: true
    confidence_threshold: 0.8
    patterns:
      - "ignore previous instructions"
      - "act as if you are"
      - "pretend to be"  
      - "override your instructions"
      - "system prompt"
      - "developer mode"
    
  data_leakage_prevention:
    enabled: true
    pii_detection: true
    sensitive_patterns:
      - credit_card_numbers
      - social_security_numbers
      - api_keys
      - passwords
      - private_keys
      - email_addresses
      - phone_numbers
    
  content_filtering:
    enabled: true
    max_input_length: 50000
    allowed_file_types: 
      - .py
      - .js
      - .ts
      - .java
      - .go
      - .rs
      - .cpp
      - .cs
      - .php
      - .rb
      - .kt
      - .swift
    blocked_content:
      - malicious_code_patterns
      - obfuscated_scripts
      - binary_data
      - executable_code

output_security:
  content_validation:
    enabled: true
    check_for_secrets: true
    validate_code_examples: true
    
  response_filtering:
    enabled: true
    remove_sensitive_info: true
    sanitize_recommendations: true

rate_limiting:
  requests_per_minute: 60
  requests_per_hour: 500
  burst_allowance: 10

authentication:
  require_api_key: true
  session_validation: true
  user_context_isolation: true
"""

    def _get_quality_control_config(self) -> str:
        return """# Quality Control Configuration
# Multi-layer quality assurance for agent outputs

quality_control:
  validation_pipeline:
    enabled: true
    stages:
      - input_security_check
      - bias_prevention_injection
      - llm_generation
      - output_fact_checking
      - domain_expertise_validation
      - final_quality_gate
  
  quality_gates:
    minimum_confidence: 0.7
    minimum_domain_expertise: 0.8
    max_bias_indicators: 2
    require_factual_consistency: true
    allow_hallucination_threshold: 0.1
    
  validation_rules:
    factual_consistency:
      enabled: true
      check_quantitative_claims: true
      verify_code_examples: true
      cross_reference_deterministic_data: true
      
    domain_expertise:
      enabled: true
      specialized_validation: true
      knowledge_base_verification: true
      
    bias_detection:
      enabled: true
      language_bias: true
      framework_bias: true
      experience_level_bias: true
      cultural_bias: true
    
  fallback_strategies:
    low_confidence_threshold: 0.5
    fallback_to_deterministic: true
    human_review_trigger: 0.3
    partial_results_acceptable: true
    
  monitoring:
    track_validation_failures: true
    alert_on_repeated_failures: true
    quality_metrics_reporting: true
    confidence_score_distribution: true

human_review:
  triggers:
    low_confidence: 0.3
    critical_domain: ["security", "performance"]
    novel_patterns: true
    high_stakes_analysis: true
    
  review_types:
    quick_validation: 5  # minutes
    detailed_review: 30  # minutes
    expert_consultation: 120  # minutes
    
  escalation:
    repeated_failures: 3
    confidence_degradation: true
    user_complaints: true
"""

    def _get_bias_prevention_config(self) -> str:
        return """# Bias Prevention Configuration
# Rules and guidelines to prevent bias in agent analysis

bias_prevention:
  general_guidelines:
    - "Focus on objective, measurable code characteristics"
    - "Avoid assumptions about programming languages, frameworks, or developer experience"
    - "Present findings based on established software engineering principles"
    - "Consider multiple valid approaches rather than favoring specific technologies"
    - "Provide evidence-based recommendations with clear reasoning"
    - "Acknowledge when multiple solutions are equally valid"
  
  domain_specific:
    security:
      - "Assess vulnerabilities based on OWASP/NIST standards, not personal preferences"
      - "Consider context-appropriate security measures"
      - "Avoid over-engineering security for low-risk applications"
      - "Present balanced view of security vs usability tradeoffs"
      
    performance:
      - "Base recommendations on actual performance metrics, not assumptions"
      - "Consider premature optimization vs necessary optimization"
      - "Account for different performance requirements"
      - "Avoid favoring specific optimization techniques without context"
      
    architecture:
      - "Evaluate patterns based on project context and team size"
      - "Avoid architectural dogma - consider multiple valid approaches"
      - "Balance ideal architecture vs practical constraints"
      - "Present tradeoffs clearly rather than absolute recommendations"
      
    sustainability:
      - "Focus on measurable environmental impact"
      - "Consider cost-benefit analysis of green practices"
      - "Avoid green-washing - be honest about trade-offs"
      - "Present practical sustainability improvements"
      
    microservices:
      - "Evaluate appropriateness based on team size and complexity"
      - "Avoid microservices dogma - monoliths can be appropriate"
      - "Consider operational complexity vs benefits"
      - "Focus on business value over architectural trends"
      
    api_design:
      - "Evaluate based on use case and consumer needs"
      - "Avoid REST vs GraphQL bias - both have appropriate uses"
      - "Consider developer experience and maintenance burden"
      - "Focus on consistency and predictability"

detection_patterns:
  language_bias:
    - "X language is better than Y"
    - "Always use language X"
    - "Language Y is outdated"
    
  framework_bias:
    - "Framework X is the best choice"
    - "Never use framework Y"
    - "Modern applications should use X"
    
  experience_bias:
    - "Junior developers can't handle X"
    - "Only senior developers should use Y"
    - "This is too complex for beginners"
    
  complexity_bias:
    - "This solution is too simple"
    - "Enterprise applications require X"
    - "Microservices are always better"

correction_strategies:
  reframe_absolute_statements: true
  provide_context_considerations: true
  offer_multiple_perspectives: true
  acknowledge_trade_offs: true
  use_evidence_based_language: true
"""

    def _get_tree_sitter_config(self) -> str:
        return """# Tree-sitter Language Configuration
# Multi-language support configuration for AST parsing

supported_languages:
  python:
    grammar: "tree-sitter-python"
    version: "0.25.2"
    file_extensions: [".py", ".pyx", ".pyi"]
    complexity_patterns:
      - function_definition
      - class_definition
      - if_statement
      - for_statement
      - while_statement
      - try_statement
    security_patterns:
      - import_statement
      - call
      - attribute
    maintainability_patterns:
      - docstring
      - comment
      - function_definition
      
  javascript:
    grammar: "tree-sitter-javascript"
    version: "0.25.2"
    file_extensions: [".js", ".jsx", ".mjs"]
    complexity_patterns:
      - function_declaration
      - arrow_function
      - if_statement
      - while_statement
      - for_statement
    security_patterns:
      - call_expression
      - member_expression
      - import_statement
    maintainability_patterns:
      - comment
      - function_declaration
      - class_declaration
      
  typescript:
    grammar: "tree-sitter-typescript"
    version: "0.25.2"
    file_extensions: [".ts", ".tsx"]
    complexity_patterns:
      - function_declaration
      - arrow_function
      - if_statement
      - for_statement
      - interface_declaration
    security_patterns:
      - call_expression
      - member_expression
      - import_declaration
    maintainability_patterns:
      - comment
      - interface_declaration
      - type_alias_declaration
      
  java:
    grammar: "tree-sitter-java"
    version: "0.25.2"
    file_extensions: [".java"]
    complexity_patterns:
      - method_declaration
      - class_declaration
      - if_statement
      - for_statement
      - while_statement
    security_patterns:
      - method_invocation
      - object_creation_expression
      - import_declaration
    maintainability_patterns:
      - block_comment
      - line_comment
      - method_declaration
      
  go:
    grammar: "tree-sitter-go"
    version: "0.25.2"
    file_extensions: [".go"]
    complexity_patterns:
      - function_declaration
      - method_declaration
      - if_statement
      - for_statement
      - switch_statement
    security_patterns:
      - call_expression
      - import_spec
    maintainability_patterns:
      - comment
      - function_declaration
      
  rust:
    grammar: "tree-sitter-rust"
    version: "0.25.2"
    file_extensions: [".rs"]
    complexity_patterns:
      - function_item
      - impl_item
      - if_expression
      - loop_expression
      - match_expression
    security_patterns:
      - call_expression
      - use_declaration
    maintainability_patterns:
      - line_comment
      - block_comment
      - function_item
      
  cpp:
    grammar: "tree-sitter-cpp"
    version: "0.25.2"
    file_extensions: [".cpp", ".cxx", ".cc", ".hpp", ".h"]
    complexity_patterns:
      - function_definition
      - class_specifier
      - if_statement
      - for_statement
      - while_statement
    security_patterns:
      - call_expression
      - preproc_include
    maintainability_patterns:
      - comment
      - function_definition
      
  csharp:
    grammar: "tree-sitter-c-sharp"
    version: "0.25.2"
    file_extensions: [".cs"]
    complexity_patterns:
      - method_declaration
      - class_declaration
      - if_statement
      - for_statement
      - while_statement
    security_patterns:
      - invocation_expression
      - using_directive
    maintainability_patterns:
      - comment
      - method_declaration
      
  php:
    grammar: "tree-sitter-php"
    version: "0.25.2"
    file_extensions: [".php"]
    complexity_patterns:
      - function_definition
      - method_declaration
      - if_statement
      - for_statement
      - while_statement
    security_patterns:
      - function_call_expression
      - include_expression
    maintainability_patterns:
      - comment
      - function_definition
      
  ruby:
    grammar: "tree-sitter-ruby"
    version: "0.25.2"
    file_extensions: [".rb"]
    complexity_patterns:
      - method
      - class
      - if
      - for
      - while
    security_patterns:
      - call
      - constant
    maintainability_patterns:
      - comment
      - method
      
  kotlin:
    grammar: "tree-sitter-kotlin"
    version: "0.25.2"
    file_extensions: [".kt", ".kts"]
    complexity_patterns:
      - function_declaration
      - class_declaration
      - if_expression
      - for_statement
      - while_statement
    security_patterns:
      - call_expression
      - import_header
    maintainability_patterns:
      - comment
      - function_declaration
      
  swift:
    grammar: "tree-sitter-swift"
    version: "0.25.2"
    file_extensions: [".swift"]
    complexity_patterns:
      - function_declaration
      - class_declaration
      - if_statement
      - for_statement
      - while_statement
    security_patterns:
      - call_expression
      - import_declaration
    maintainability_patterns:
      - comment
      - function_declaration

parsing_configuration:
  cache_parse_trees: true
  incremental_parsing: true
  max_file_size: 1048576  # 1MB
  timeout_seconds: 30
  memory_limit_mb: 100
  
performance_optimization:
  parallel_parsing: true
  lazy_loading: true
  tree_reuse: true
  memory_cleanup_interval: 300  # 5 minutes
"""
    
    def _get_code_quality_agent_config(self) -> str:
        """Get Code Quality Agent configuration"""
        return """# Code Quality Agent Configuration
agent_id: "code_quality"
name: "Code Quality Agent"
version: "1.0.0"
priority: 1

analysis_scope:
  - complexity_analysis
  - maintainability_scoring
  - code_smells_detection
  - documentation_quality
  - test_coverage_analysis
  - naming_conventions

complexity_metrics:
  cyclomatic_complexity:
    enabled: true
    thresholds:
      low: 5
      medium: 10
      high: 15
      critical: 20
    
  cognitive_complexity:
    enabled: true
    thresholds:
      low: 7
      medium: 15
      high: 25
      critical: 35

maintainability_scoring:
  factors:
    complexity_weight: 0.25
    documentation_weight: 0.20
    test_coverage_weight: 0.20
    naming_weight: 0.15
    duplication_weight: 0.20
    
  thresholds:
    excellent: 90
    good: 75
    acceptable: 60
    poor: 40

code_smell_detection:
  rules:
    long_method:
      enabled: true
      max_lines: 50
    
    large_class:
      enabled: true
      max_lines: 500
      max_methods: 20
    
    too_many_parameters:
      enabled: true
      max_parameters: 5

naming_conventions:
  check_consistency: true
  patterns:
    class_names: "PascalCase"
    function_names: "snake_case"
    variable_names: "snake_case"
    constant_names: "UPPER_SNAKE_CASE"
"""

    def _get_security_agent_config(self) -> str:
        """Get Security Standards Agent configuration"""
        return """# Security Standards Agent Configuration
agent_id: "security_standards"
name: "Security Standards Agent"
version: "1.0.0"
priority: 2

analysis_scope:
  - vulnerability_scanning
  - secrets_detection
  - dependency_analysis
  - input_validation
  - authentication_analysis

vulnerability_scanning:
  enabled_scanners:
    - "bandit"      # Python security linter
    - "semgrep"     # Multi-language static analysis
    - "safety"      # Python dependency vulnerability scanner
  
  severity_levels:
    critical: 
      fail_build: true
      require_immediate_fix: true
    high:
      fail_build: true
      max_allowed: 0
    medium:
      fail_build: false
      max_allowed: 5

secrets_detection:
  patterns:
    api_keys:
      - "api[_-]?key"
      - "apikey"
      - "access[_-]?key"
    
    passwords:
      - "password"
      - "passwd"
      - "pwd"
    
    tokens:
      - "token"
      - "auth[_-]?token"

dependency_analysis:
  check_known_vulnerabilities: true
  check_license_compatibility: true
  check_outdated_packages: true
  
  allowed_licenses:
    - "MIT"
    - "Apache-2.0"
    - "BSD-3-Clause"
    - "ISC"
"""

    def _get_architecture_agent_config(self) -> str:
        """Get Architecture Agent configuration"""
        return """# Architecture Agent Configuration
agent_id: "architecture"
name: "Architecture Agent"
version: "1.0.0"
priority: 3

analysis_scope:
  - design_patterns_analysis
  - dependency_analysis
  - layered_architecture_validation
  - coupling_cohesion_metrics

design_patterns:
  detect_patterns:
    creational:
      - "singleton"
      - "factory"
      - "builder"
    
    structural:
      - "adapter"
      - "decorator"
      - "facade"
    
    behavioral:
      - "observer"
      - "strategy"
      - "command"
  
  anti_patterns:
    - "god_object"
    - "spaghetti_code"
    - "copy_paste_programming"

dependency_analysis:
  metrics:
    afferent_coupling: true
    efferent_coupling: true
    instability: true
  
  thresholds:
    max_dependencies: 10
    max_dependents: 15
    max_cycle_length: 5

coupling_cohesion:
  thresholds:
    max_coupling_factor: 0.3
    min_cohesion_factor: 0.7
"""

    def _get_performance_agent_config(self) -> str:
        """Get Performance Agent configuration"""
        return """# Performance Agent Configuration
agent_id: "performance"
name: "Performance Agent"
version: "1.0.0"
priority: 4

analysis_scope:
  - performance_profiling
  - bottleneck_detection
  - memory_usage_analysis
  - database_query_optimization

performance_profiling:
  metrics_to_collect:
    - "execution_time"
    - "memory_usage"
    - "cpu_usage"
    - "io_operations"
  
  profiling_tools:
    python:
      - "cProfile"
      - "line_profiler"
      - "memory_profiler"

bottleneck_detection:
  threshold_rules:
    execution_time:
      warning: 1000  # milliseconds
      critical: 5000
    
    memory_usage:
      warning: 100   # MB
      critical: 500

database_optimization:
  query_analysis:
    - "missing_indexes"
    - "slow_queries"
    - "n_plus_one_queries"
  
  optimization_patterns:
    - "query_optimization"
    - "connection_pooling"
    - "result_caching"
"""

    def _get_cloud_native_agent_config(self) -> str:
        """Get Cloud Native Agent configuration"""
        return """# Cloud Native Agent Configuration
agent_id: "cloud_native"
name: "Cloud Native Agent"
version: "1.0.0"
priority: 5

analysis_scope:
  - containerization_review
  - kubernetes_best_practices
  - service_mesh_patterns
  - observability_analysis

containerization:
  docker_best_practices:
    - "multi_stage_builds"
    - "minimal_base_images"
    - "security_scanning"
    - "layer_optimization"
  
  security_checks:
    - "non_root_user"
    - "read_only_filesystem"
    - "resource_limits"

kubernetes_patterns:
  deployment_strategies:
    - "rolling_updates"
    - "blue_green"
    - "canary"
  
  resource_management:
    - "resource_requests"
    - "resource_limits"
    - "horizontal_pod_autoscaling"

observability:
  monitoring_patterns:
    - "health_checks"
    - "metrics_collection"
    - "distributed_tracing"
    - "structured_logging"
"""

    def _get_engineering_practices_agent_config(self) -> str:
        """Get Engineering Practices Agent configuration"""
        return """# Engineering Practices Agent Configuration
agent_id: "engineering_practices"
name: "Engineering Practices Agent"
version: "1.0.0"
priority: 6

analysis_scope:
  - testing_practices
  - ci_cd_pipeline_review
  - documentation_quality
  - version_control_practices

testing_practices:
  test_types:
    - "unit_tests"
    - "integration_tests"
    - "end_to_end_tests"
  
  quality_metrics:
    coverage_threshold: 80
    test_naming_conventions: true
    test_isolation: true

ci_cd_practices:
  pipeline_stages:
    - "build"
    - "test"
    - "security_scan"
    - "deploy"
  
  quality_gates:
    - "test_coverage"
    - "security_vulnerabilities"
    - "code_quality_metrics"

documentation:
  required_docs:
    - "README"
    - "API_documentation"
    - "deployment_guide"
    - "troubleshooting_guide"
"""

    def _get_sustainability_agent_config(self) -> str:
        """Get Sustainability Agent configuration"""
        return """# Sustainability Agent Configuration
agent_id: "sustainability"
name: "Sustainability Agent"
version: "1.0.0"
priority: 7

analysis_scope:
  - carbon_footprint_analysis
  - energy_efficiency_review
  - resource_optimization
  - green_coding_practices

carbon_footprint:
  metrics:
    - "compute_resource_usage"
    - "data_transfer_volume"
    - "storage_efficiency"
    - "algorithm_efficiency"
  
  optimization_suggestions:
    - "efficient_algorithms"
    - "resource_pooling"
    - "lazy_loading"
    - "caching_strategies"

energy_efficiency:
  code_patterns:
    - "loop_optimization"
    - "memory_efficient_structures"
    - "database_query_optimization"
    - "async_processing"

green_coding:
  best_practices:
    - "minimize_data_transfer"
    - "optimize_database_queries"
    - "use_efficient_data_structures"
    - "implement_caching"
"""

    def _get_microservices_agent_config(self) -> str:
        """Get Microservices Agent configuration"""
        return """# Microservices Agent Configuration
agent_id: "microservices"
name: "Microservices Agent"
version: "1.0.0"
priority: 8

analysis_scope:
  - service_boundary_analysis
  - inter_service_communication
  - data_consistency_patterns
  - resilience_patterns

service_boundaries:
  domain_driven_design:
    - "bounded_contexts"
    - "domain_entities"
    - "aggregates"
  
  coupling_analysis:
    - "data_coupling"
    - "behavioral_coupling"
    - "temporal_coupling"

communication_patterns:
  synchronous:
    - "REST_APIs"
    - "GraphQL"
    - "gRPC"
  
  asynchronous:
    - "message_queues"
    - "event_streaming"
    - "publish_subscribe"

resilience_patterns:
  fault_tolerance:
    - "circuit_breaker"
    - "retry_with_backoff"
    - "timeout_handling"
    - "bulkhead_isolation"
"""

    def _get_api_design_agent_config(self) -> str:
        """Get API Design Agent configuration"""
        return """# API Design Agent Configuration
agent_id: "api_design"
name: "API Design Agent"
version: "1.0.0"
priority: 9

analysis_scope:
  - rest_api_design
  - graphql_schema_analysis
  - api_security_review
  - api_documentation_quality

rest_api_design:
  best_practices:
    - "resource_naming"
    - "http_methods_usage"
    - "status_codes"
    - "versioning_strategy"
  
  security_checks:
    - "authentication"
    - "authorization"
    - "input_validation"
    - "rate_limiting"

graphql_analysis:
  schema_design:
    - "type_definitions"
    - "resolver_patterns"
    - "query_complexity"
    - "n_plus_one_prevention"

api_documentation:
  requirements:
    - "endpoint_documentation"
    - "request_examples"
    - "response_schemas"
    - "error_handling"
"""

    def _get_staging_config(self) -> str:
        """Get staging environment configuration"""
        return """# Staging Environment Configuration
environment: "staging"
debug: false
log_level: "INFO"

# Staging-specific agent configuration
agents:
  enabled_agents:
    - code_quality
    - security_standards
    - architecture
    - performance
    - cloud_native
    - engineering_practices
    - sustainability
    - microservices
    - api_design
  
  parallel_execution: true
  max_concurrent_agents: 6
  timeout_per_agent: 600  # 10 minutes

# LLM Configuration for staging
llm_providers:
  primary:
    provider: "google_gemini"
    model: "gemini-pro"
    temperature: 0.3
    max_tokens: 4000
  
  fallback:
    provider: "openai"
    model: "gpt-4"

# Quality thresholds for staging
quality_thresholds:
  code_quality:
    complexity_threshold: 15
    maintainability_threshold: 70
  
  security:
    fail_on_high_severity: true
    fail_on_secrets: true
  
  performance:
    max_execution_time: 2000  # milliseconds

# Integration settings
integrations:
  redis:
    host: "staging-redis.internal"
    port: 6379
    db: 1
  
  neo4j:
    uri: "bolt://staging-neo4j.internal:7687"
    database: "staging_knowledge"
"""

    def _get_llm_models_config(self) -> str:
        """Get LLM models configuration"""
        return """# LLM Models Configuration
default_provider: "google_gemini"

providers:
  google_gemini:
    models:
      gemini_pro:
        name: "gemini-pro"
        max_tokens: 8192
        temperature: 0.3
        top_p: 0.9
        cost_per_1k_tokens:
          input: 0.00025
          output: 0.0005
        
      gemini_pro_vision:
        name: "gemini-pro-vision"
        max_tokens: 4096
        supports_images: true
        cost_per_1k_tokens:
          input: 0.00025
          output: 0.0005
    
    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 100000
    
    endpoints:
      generate: "https://generativelanguage.googleapis.com/v1beta/models"
    
  openai:
    models:
      gpt_4:
        name: "gpt-4"
        max_tokens: 8192
        temperature: 0.3
        cost_per_1k_tokens:
          input: 0.03
          output: 0.06
      
      gpt_3_5_turbo:
        name: "gpt-3.5-turbo"
        max_tokens: 4096
        temperature: 0.3
        cost_per_1k_tokens:
          input: 0.0015
          output: 0.002
    
    rate_limits:
      requests_per_minute: 20
      tokens_per_minute: 40000

# Model selection strategy
model_selection:
  strategy: "cost_optimized"  # options: cost_optimized, performance_optimized, balanced
  
  routing_rules:
    - condition: "analysis_type == 'security'"
      model: "gemini_pro"
      reason: "Better security analysis capabilities"
    
    - condition: "file_size > 1000"
      model: "gpt_4"
      reason: "Better handling of large files"
    
    - condition: "complexity_score > 80"
      model: "gemini_pro"
      reason: "Better complex code analysis"

# Fallback configuration
fallback_strategy:
  enable: true
  max_retries: 3
  fallback_sequence:
    - "google_gemini"
    - "openai"
"""

    def _get_cost_optimization_config(self) -> str:
        """Get cost optimization configuration"""
        return """# Cost Optimization Configuration
budget_management:
  daily_budget: 100.00  # USD
  monthly_budget: 2000.00  # USD
  alert_thresholds:
    warning: 80  # percentage of budget
    critical: 95  # percentage of budget

cost_tracking:
  track_by:
    - "agent_type"
    - "user_id"
    - "project_id"
    - "analysis_type"
  
  reporting:
    generate_daily_reports: true
    generate_weekly_reports: true
    export_formats: ["csv", "json"]

optimization_strategies:
  token_optimization:
    enable_prompt_compression: true
    remove_redundant_context: true
    optimize_response_length: true
  
  model_selection:
    prefer_cost_effective: true
    use_smaller_models_for_simple_tasks: true
    cache_similar_requests: true
  
  request_batching:
    enable: true
    max_batch_size: 10
    batch_timeout: 5  # seconds

caching_strategy:
  cache_responses: true
  cache_ttl: 3600  # 1 hour
  cache_similar_threshold: 0.9  # similarity score
  
  cache_levels:
    - "exact_match"
    - "semantic_similarity"
    - "partial_results"

rate_limiting:
  adaptive_rate_limiting: true
  reduce_rate_on_budget_warning: true
  pause_on_budget_exceeded: true

cost_alerts:
  email_notifications: true
  webhook_notifications: true
  slack_integration: true
"""

    def _get_quality_gates_config(self) -> str:
        """Get quality gates configuration"""
        return """# Quality Gates Configuration
quality_gates:
  code_quality:
    enabled: true
    thresholds:
      cyclomatic_complexity: 15
      cognitive_complexity: 25
      maintainability_index: 60
      test_coverage: 80
    
    blocking: true
    failure_action: "block_merge"
  
  security:
    enabled: true
    thresholds:
      critical_vulnerabilities: 0
      high_vulnerabilities: 0
      secrets_detected: 0
    
    blocking: true
    failure_action: "block_merge"
  
  performance:
    enabled: true
    thresholds:
      max_execution_time: 5000  # milliseconds
      memory_usage_mb: 500
      database_queries_per_request: 50
    
    blocking: false
    failure_action: "warning"
  
  architecture:
    enabled: true
    thresholds:
      coupling_factor: 0.3
      cohesion_factor: 0.7
      circular_dependencies: 0
    
    blocking: false
    failure_action: "warning"

gate_execution:
  parallel_execution: true
  timeout_per_gate: 300  # 5 minutes
  retry_on_failure: true
  max_retries: 2

reporting:
  generate_gate_reports: true
  include_recommendations: true
  export_formats: ["json", "html", "pdf"]

notifications:
  on_gate_failure:
    email: true
    slack: true
    webhook: true
  
  on_gate_success:
    email: false
    slack: false
    webhook: true
"""

    def _get_security_rules_config(self) -> str:
        """Get security rules configuration"""
        return """# Security Rules Configuration
security_rules:
  vulnerability_detection:
    sql_injection:
      enabled: true
      severity: "critical"
      patterns:
        - "SELECT.*FROM.*WHERE.*\\$\\{.*\\}"
        - "INSERT.*INTO.*VALUES.*\\$\\{.*\\}"
        - "UPDATE.*SET.*\\$\\{.*\\}"
    
    xss_prevention:
      enabled: true
      severity: "high"
      patterns:
        - "innerHTML.*\\+.*"
        - "document\\.write\\(.*\\+.*\\)"
        - "eval\\(.*user.*\\)"
    
    command_injection:
      enabled: true
      severity: "critical"
      patterns:
        - "exec\\(.*user.*\\)"
        - "system\\(.*user.*\\)"
        - "subprocess\\..*shell=True"

secrets_detection:
  enabled: true
  entropy_threshold: 4.0
  
  patterns:
    aws_access_key:
      pattern: "AKIA[0-9A-Z]{16}"
      severity: "critical"
    
    api_key:
      pattern: "[aA][pP][iI][_-]?[kK][eE][yY].*"
      severity: "high"
    
    password:
      pattern: "[pP][aA][sS][sS][wW][oO][rR][dD].*"
      severity: "medium"

dependency_security:
  check_vulnerabilities: true
  check_licenses: true
  
  vulnerability_sources:
    - "nvd"
    - "snyk"
    - "ossindex"
  
  license_compliance:
    allowed_licenses:
      - "MIT"
      - "Apache-2.0"
      - "BSD-3-Clause"
    
    forbidden_licenses:
      - "GPL-3.0"
      - "AGPL-3.0"

authentication_patterns:
  password_complexity:
    min_length: 12
    require_uppercase: true
    require_lowercase: true
    require_numbers: true
    require_special_chars: true
  
  session_management:
    session_timeout: 1800  # 30 minutes
    secure_cookies: true
    httponly_cookies: true

encryption_standards:
  symmetric_algorithms:
    recommended:
      - "AES-256-GCM"
      - "ChaCha20-Poly1305"
    
    deprecated:
      - "DES"
      - "3DES"
      - "RC4"
  
  asymmetric_algorithms:
    recommended:
      - "RSA-2048"
      - "RSA-4096"
      - "ECDSA-P256"
    
    deprecated:
      - "RSA-1024"
      - "DSA"
"""

    def _get_tree_sitter_patterns_config(self) -> str:
        """Get tree-sitter patterns configuration"""
        return """# Tree-sitter Analysis Patterns Configuration
analysis_patterns:
  complexity_patterns:
    cyclomatic_complexity:
      - "(if_statement) @conditional"
      - "(while_statement) @loop"
      - "(for_statement) @loop"
      - "(case_clause) @case"
      - "(except_clause) @exception"
    
    cognitive_complexity:
      - "(nested_statement) @nesting"
      - "(logical_operator) @logical"
      - "(conditional_expression) @ternary"
  
  security_patterns:
    dangerous_functions:
      - "(call (identifier) @func (#match? @func \"^(eval|exec|compile)$\"))"
      - "(call (identifier) @func (#match? @func \"^(system|popen)$\"))"
    
    sql_injection:
      - "(string) @sql (#match? @sql \"SELECT.*FROM.*WHERE\")"
      - "(string) @sql (#match? @sql \"INSERT.*INTO.*VALUES\")"
  
  code_quality_patterns:
    long_parameter_lists:
      - "(parameters (identifier) @param)"
    
    magic_numbers:
      - "(integer) @number (#not-match? @number \"^[01]$\")"
    
    duplicate_code:
      - "(block) @code_block"

language_specific_patterns:
  python:
    imports:
      - "(import_statement (dotted_name) @import)"
      - "(import_from_statement (dotted_name) @import)"
    
    functions:
      - "(function_definition (identifier) @function_name)"
    
    classes:
      - "(class_definition (identifier) @class_name)"
  
  javascript:
    functions:
      - "(function_declaration (identifier) @function_name)"
      - "(arrow_function) @arrow_function"
    
    promises:
      - "(call_expression (member_expression (identifier) @promise (#eq? @promise \"Promise\")))"
  
  java:
    annotations:
      - "(annotation (identifier) @annotation)"
    
    generics:
      - "(type_parameters (type_parameter) @type_param)"

query_optimization:
  cache_queries: true
  parallel_execution: true
  max_depth: 100
  timeout_ms: 5000
"""

    def _get_redis_config(self) -> str:
        """Get Redis integration configuration"""
        return """# Redis Integration Configuration
connection:
  host: "${REDIS_HOST:-localhost}"
  port: "${REDIS_PORT:-6379}"
  db: "${REDIS_DB:-0}"
  password: "${REDIS_PASSWORD:-}"
  ssl: "${REDIS_SSL:-false}"
  
connection_pool:
  max_connections: 20
  retry_on_timeout: true
  socket_timeout: 5
  socket_connect_timeout: 5

session_management:
  session_prefix: "adk_session:"
  session_ttl: 3600  # 1 hour
  cleanup_interval: 300  # 5 minutes
  
  serialization:
    format: "json"
    compression: true

caching:
  cache_prefix: "adk_cache:"
  default_ttl: 1800  # 30 minutes
  max_key_length: 250
  
  cache_levels:
    analysis_results:
      ttl: 3600
      compression: true
    
    agent_outputs:
      ttl: 1800
      compression: false
    
    user_preferences:
      ttl: 86400  # 24 hours
      compression: false

pub_sub:
  channels:
    progress_updates: "adk:progress"
    status_changes: "adk:status"
    notifications: "adk:notifications"
  
  message_format: "json"
  max_message_size: 1048576  # 1MB

monitoring:
  health_check_interval: 30  # seconds
  metrics_collection: true
  slow_query_threshold: 100  # milliseconds
"""

    def _get_neo4j_config(self) -> str:
        """Get Neo4j integration configuration"""
        return """# Neo4j Integration Configuration
connection:
  uri: "${NEO4J_URI:-bolt://localhost:7687}"
  username: "${NEO4J_USERNAME:-neo4j}"
  password: "${NEO4J_PASSWORD:-}"
  database: "${NEO4J_DATABASE:-adk_knowledge}"
  
  driver_config:
    max_connection_lifetime: 3600  # 1 hour
    max_connection_pool_size: 50
    connection_acquisition_timeout: 60
    encrypted: false

knowledge_graph:
  schema:
    nodes:
      - label: "CodeFile"
        properties: ["path", "language", "size", "hash"]
      
      - label: "Function"
        properties: ["name", "complexity", "lines_of_code"]
      
      - label: "Class"
        properties: ["name", "methods_count", "inheritance_depth"]
      
      - label: "Agent"
        properties: ["name", "version", "analysis_type"]
      
      - label: "Analysis"
        properties: ["timestamp", "confidence", "recommendations"]
    
    relationships:
      - type: "CONTAINS"
        from: "CodeFile"
        to: "Function"
      
      - type: "DEFINES"
        from: "CodeFile"
        to: "Class"
      
      - type: "CALLS"
        from: "Function"
        to: "Function"
      
      - type: "ANALYZED_BY"
        from: "CodeFile"
        to: "Agent"

indexing:
  auto_index: true
  indexes:
    - label: "CodeFile"
      properties: ["path", "hash"]
    
    - label: "Function"
      properties: ["name"]
    
    - label: "Analysis"
      properties: ["timestamp"]

queries:
  optimization:
    use_explain: true
    query_timeout: 30  # seconds
    max_result_size: 10000
  
  caching:
    enable_query_cache: true
    cache_ttl: 1800  # 30 minutes

learning:
  pattern_detection:
    enable: true
    min_pattern_frequency: 3
    confidence_threshold: 0.8
  
  recommendation_engine:
    enable: true
    similarity_threshold: 0.7
    max_recommendations: 10
"""

    def _get_adk_config(self) -> str:
        """Get ADK integration configuration"""
        return """# Google Agent Development Kit (ADK) Configuration
adk:
  version: "1.0.0"
  project_id: "${GOOGLE_CLOUD_PROJECT}"
  region: "${GOOGLE_CLOUD_REGION:-us-central1}"
  
agent_discovery:
  discovery_endpoint: "https://agentbuilder.googleapis.com/v1/projects/${GOOGLE_CLOUD_PROJECT}/agents"
  refresh_interval: 3600  # 1 hour
  
  available_agents:
    - name: "code-quality-analyzer"
      type: "analysis"
      capabilities: ["complexity", "maintainability", "documentation"]
    
    - name: "security-scanner"
      type: "security"
      capabilities: ["vulnerability", "secrets", "dependencies"]
    
    - name: "performance-profiler"
      type: "performance"
      capabilities: ["profiling", "bottlenecks", "optimization"]

integration:
  authentication:
    service_account_path: "${GOOGLE_APPLICATION_CREDENTIALS}"
    scopes:
      - "https://www.googleapis.com/auth/cloud-platform"
      - "https://www.googleapis.com/auth/agentbuilder"
  
  api_configuration:
    timeout: 60  # seconds
    retry_attempts: 3
    backoff_multiplier: 2

agent_orchestration:
  parallel_execution: true
  max_concurrent_agents: 5
  execution_timeout: 600  # 10 minutes
  
  failure_handling:
    retry_failed_agents: true
    continue_on_agent_failure: true
    fallback_to_local_agents: true

data_exchange:
  input_format: "structured_json"
  output_format: "structured_json"
  
  serialization:
    use_compression: true
    max_payload_size: 10485760  # 10MB

monitoring:
  metrics_collection: true
  performance_tracking: true
  cost_tracking: true
  
  alerts:
    on_failure: true
    on_timeout: true
    on_cost_threshold: true
"""

    def _get_reporting_formats_config(self) -> str:
        """Get reporting formats configuration"""
        return """# Reporting Formats Configuration
output_formats:
  json:
    enabled: true
    pretty_print: true
    include_metadata: true
    file_extension: ".json"
  
  html:
    enabled: true
    template: "comprehensive_report.html"
    include_charts: true
    include_recommendations: true
    file_extension: ".html"
  
  pdf:
    enabled: true
    template: "executive_summary.pdf"
    include_executive_summary: true
    include_detailed_analysis: true
    file_extension: ".pdf"
  
  markdown:
    enabled: true
    template: "github_report.md"
    include_code_snippets: true
    file_extension: ".md"
  
  csv:
    enabled: true
    include_metrics_only: true
    delimiter: ","
    file_extension: ".csv"

report_sections:
  executive_summary:
    enabled: true
    max_length: 500
    include_recommendations: true
  
  detailed_analysis:
    enabled: true
    include_code_examples: true
    include_metrics: true
  
  agent_findings:
    enabled: true
    group_by_agent: true
    include_confidence_scores: true
  
  recommendations:
    enabled: true
    prioritize_by_impact: true
    include_implementation_guides: true
  
  metrics_dashboard:
    enabled: true
    include_trends: true
    include_comparisons: true

customization:
  branding:
    company_logo: true
    custom_colors: true
    footer_text: true
  
  filtering:
    by_severity: true
    by_agent: true
    by_file_type: true
  
  export_options:
    compress_outputs: true
    batch_reports: true
    email_delivery: true
"""

    def _get_reporting_templates_config(self) -> str:
        """Get reporting templates configuration"""
        return """# Reporting Templates Configuration
templates:
  executive_summary:
    name: "Executive Summary Report"
    description: "High-level overview for management"
    sections:
      - "overview"
      - "key_findings"
      - "recommendations"
      - "risk_assessment"
    
    format_options:
      - "pdf"
      - "html"
      - "markdown"
  
  technical_detailed:
    name: "Technical Detailed Report"
    description: "Comprehensive technical analysis"
    sections:
      - "code_quality_analysis"
      - "security_assessment"
      - "performance_analysis"
      - "architecture_review"
      - "detailed_recommendations"
    
    format_options:
      - "html"
      - "pdf"
      - "json"
  
  agent_specific:
    name: "Agent-Specific Report"
    description: "Focused report per agent"
    sections:
      - "agent_overview"
      - "findings"
      - "metrics"
      - "recommendations"
    
    format_options:
      - "json"
      - "html"
      - "markdown"

template_customization:
  variables:
    - name: "project_name"
      type: "string"
      required: true
    
    - name: "analysis_date"
      type: "datetime"
      required: true
    
    - name: "analyst_name"
      type: "string"
      required: false
  
  styling:
    css_customization: true
    logo_placement: true
    color_schemes:
      - "default"
      - "corporate"
      - "dark_mode"

chart_templates:
  complexity_trends:
    type: "line_chart"
    data_source: "complexity_metrics"
    x_axis: "file_path"
    y_axis: "complexity_score"
  
  security_severity:
    type: "pie_chart"
    data_source: "security_findings"
    category: "severity"
  
  agent_performance:
    type: "bar_chart"
    data_source: "agent_metrics"
    x_axis: "agent_name"
    y_axis: "execution_time"

export_settings:
  include_raw_data: false
  compress_attachments: true
  watermark: false
  
  delivery_options:
    email_notification: true
    webhook_notification: true
    file_storage: true
"""
    
    # Add placeholder methods for other templates...
    def _get_neo4j_client_template(self) -> str:
        return "# Neo4j Client Implementation\n# TODO: Implement Neo4j knowledge graph client"
    
    def _get_knowledge_graph_schema_template(self) -> str:
        return "# Knowledge Graph Schema\n# TODO: Implement Neo4j schema definitions"
    
    def _get_gemini_provider_template(self) -> str:
        return "# Google Gemini LLM Provider\n# TODO: Implement Gemini provider with guardrails"
    
    def _get_llm_security_template(self) -> str:
        return "# LLM Security Controls\n# TODO: Implement input/output security validation"
    
    def _get_bias_prevention_template(self) -> str:
        return "# Bias Prevention Framework\n# TODO: Implement bias detection and prevention"
    
    def _get_tree_sitter_parser_template(self) -> str:
        return "# Tree-sitter Universal Parser\n# TODO: Implement multi-language AST parsing"
    
    def _get_report_generator_template(self) -> str:
        return "# Multi-Format Report Generator\n# TODO: Implement comprehensive reporting"
    
    def _get_synthesis_template(self) -> str:
        return "# Cross-Domain Synthesis Engine\n# TODO: Implement synthesis logic"
    
    def _get_plugin_interface_template(self) -> str:
        return "# Plugin Interface Definition\n# TODO: Implement plugin framework"
    
    def _get_example_plugin_template(self) -> str:
        return "# Example Custom Agent Plugin\n# TODO: Implement example plugin"
    
    def _get_adk_discovery_template(self) -> str:
        return "# ADK Agent Discovery\n# TODO: Implement ADK integration"
    
    def _get_redis_client_template(self) -> str:
        return "# Redis Client Implementation\n# TODO: Implement Redis integration"
    
    def _get_neo4j_integration_template(self) -> str:
        return "# Neo4j Integration Client\n# TODO: Implement Neo4j integration"
    
    def _get_api_main_template(self) -> str:
        return "# FastAPI Main Application\n# TODO: Implement API layer"
    
    def _get_analysis_api_template(self) -> str:
        return "# Analysis API Endpoints\n# TODO: Implement analysis endpoints"
    
    def _get_api_security_template(self) -> str:
        return "# API Security Middleware\n# TODO: Implement API security"
    
    def _get_test_conftest_template(self) -> str:
        return "# Pytest Configuration\n# TODO: Implement test fixtures"
    
    def _get_orchestrator_test_template(self) -> str:
        return "# Orchestrator Tests\n# TODO: Implement orchestrator tests"
    
    def _get_session_manager_test_template(self) -> str:
        return "# Session Manager Tests\n# TODO: Implement session manager tests"
    
    def _get_adk_integration_test_template(self) -> str:
        return "# ADK Integration Tests\n# TODO: Implement integration tests"
    
    def _get_e2e_test_template(self) -> str:
        return "# End-to-End Tests\n# TODO: Implement e2e tests"
    
    def _get_agents_docs_template(self) -> str:
        return "# Agent Documentation\n# TODO: Document agent architecture"
    
    def _get_architecture_docs_template(self) -> str:
        return "# Architecture Documentation\n# TODO: Document system architecture"
    
    def _get_api_docs_template(self) -> str:
        return "# API Documentation\n# TODO: Document API endpoints"


def main():
    """Main scaffolding function"""
    parser = argparse.ArgumentParser(description="Scaffold fresh codebase for AI Code Review Multi-Agent System")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without creating files")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files")
    parser.add_argument("--minimal", action="store_true", help="Create minimal structure only")
    
    args = parser.parse_args()
    
    # Get project root (parent of infra/scripts)
    project_root = Path(__file__).parent.parent.parent
    
    # Create scaffolder and run
    scaffolder = ProjectScaffolder(
        project_root=project_root,
        dry_run=args.dry_run,
        force=args.force,
        minimal=args.minimal
    )
    
    scaffolder.scaffold()


if __name__ == "__main__":
    main()