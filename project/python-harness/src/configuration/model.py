"""Configuration System - Model Layer

This module handles the core data structures and parsing logic for configuration files.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from pydantic import BaseModel, Field, field_validator


class PathGlobPattern(BaseModel):
    """Represents a file path glob pattern"""
    pattern: str
    priority: str = "medium"

    @field_validator('pattern')
    @classmethod
    def validate_glob(cls, v: str) -> str:
        """Validate glob pattern syntax"""
        if not v:
            raise ValueError("Glob pattern cannot be empty")
        # Check for invalid patterns
        if '..' in v and not v.startswith('../'):
            raise ValueError("Invalid .. placement in glob pattern")
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority value"""
        if v not in ['low', 'medium', 'high', 'critical']:
            raise ValueError(f"Invalid priority: {v}. Must be low, medium, high, or critical")
        return v


class RuleFrontmatter(BaseModel):
    """YAML frontmatter for rule files"""
    applies_to: List[str] = Field(default_factory=list)
    priority: str = "medium"
    enabled: bool = True

    @field_validator('applies_to')
    @classmethod
    def validate_applies_to(cls, v: List[str]) -> List[str]:
        """Validate glob patterns in applies_to"""
        for pattern in v:
            if not pattern:
                raise ValueError("Empty glob pattern in applies_to")
        return v


class SkillConfig(BaseModel):
    """Skill configuration with fork context"""
    name: str
    context: str = "fork"
    allowed_tools: List[str] = Field(default_factory=list)
    description: Optional[str] = None

    @field_validator('context')
    @classmethod
    def validate_context(cls, v: str) -> str:
        """Validate context type"""
        if v not in ['fork', 'main', 'isolated']:
            raise ValueError(f"Invalid context: {v}. Must be fork, main, or isolated")
        return v

    @field_validator('allowed_tools')
    @classmethod
    def validate_tools(cls, v: List[str]) -> List[str]:
        """Validate tool names"""
        valid_tools = {'Read', 'Grep', 'Glob', 'Write', 'Edit', 'Bash', 'WebFetch'}
        for tool in v:
            if tool not in valid_tools:
                raise ValueError(f"Invalid tool name: {tool}")
        return v


class ClaudeConfig(BaseModel):
    """Main CLAUDE.md configuration"""
    imports: List[str] = Field(default_factory=list)
    project_name: Optional[str] = None
    version: str = "1.0"

    @field_validator('imports')
    @classmethod
    def validate_imports(cls, v: List[str]) -> List[str]:
        """Validate import paths start with @"""
        for imp in v:
            if not imp.startswith('@'):
                raise ValueError(f"Import path must start with @: {imp}")
        return v


class ConfigModel:
    """Model layer for configuration parsing and validation"""

    @staticmethod
    def parse_yaml_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content

        Returns:
            Tuple of (frontmatter_dict, remaining_content)
        """
        if not content.startswith('---'):
            return {}, content

        # Find end of frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError("Invalid YAML frontmatter: missing closing ---")

        frontmatter_str = parts[1].strip()
        remaining = parts[2].strip()

        try:
            frontmatter = yaml.safe_load(frontmatter_str)
            return frontmatter or {}, remaining
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in frontmatter: {e}")

    @staticmethod
    def validate_rule_frontmatter(frontmatter: Dict[str, Any]) -> RuleFrontmatter:
        """Validate rule file frontmatter"""
        return RuleFrontmatter(**frontmatter)

    @staticmethod
    def validate_skill_config(config: Dict[str, Any]) -> SkillConfig:
        """Validate skill configuration"""
        return SkillConfig(**config)

    @staticmethod
    def parse_claude_md(content: str) -> ClaudeConfig:
        """Parse CLAUDE.md imports"""
        imports = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('@'):
                imports.append(line)

        return ClaudeConfig(imports=imports)


class YAMLParser:
    """Utility for parsing YAML files"""

    @staticmethod
    def load(file_path: Path) -> Dict[str, Any]:
        """Load and parse YAML file"""
        if not file_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        with open(file_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                return data or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {file_path}: {e}")

    @staticmethod
    def dump(data: Dict[str, Any], file_path: Path) -> None:
        """Write data to YAML file"""
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


class PathGlobValidator:
    """Validate file path glob patterns"""

    @staticmethod
    def is_valid_glob(pattern: str) -> bool:
        """Check if glob pattern is syntactically valid"""
        try:
            PathGlobPattern(pattern=pattern)
            return True
        except ValueError:
            return False

    @staticmethod
    def resolve_glob(pattern: str, root: Path) -> List[Path]:
        """Resolve glob pattern to list of matching files"""
        if not PathGlobValidator.is_valid_glob(pattern):
            raise ValueError(f"Invalid glob pattern: {pattern}")

        # Use pathlib glob resolution
        return list(root.glob(pattern))

    @staticmethod
    def validate_import_path(import_path: str, root: Path) -> bool:
        """Validate that an import path exists"""
        if not import_path.startswith('@'):
            return False

        # Remove @ prefix and resolve relative to root
        rel_path = import_path[1:]
        full_path = root / rel_path

        return full_path.exists()
