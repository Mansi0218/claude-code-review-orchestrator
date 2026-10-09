"""Configuration System - Harness Layer

This module provides the execution context and file system operations for configuration validation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .model import ConfigModel, YAMLParser, PathGlobValidator, RuleFrontmatter, SkillConfig, ClaudeConfig


class ConfigurationHarness:
    """
    Harness layer for configuration file operations

    Provides file I/O, path resolution, and validation orchestration.
    Located at: src/configuration/harness.py
    """

    def __init__(self, root_path: Path):
        """Initialize harness with project root"""
        self.root_path = Path(root_path)
        self.claude_dir = self.root_path / '.claude'
        self.model = ConfigModel()
        self.parser = YAMLParser()
        self.glob_validator = PathGlobValidator()

    def load_rule_file(self, rule_path: Path) -> tuple[RuleFrontmatter, str]:
        """
        Load and parse a rule file with YAML frontmatter

        Returns:
            Tuple of (validated_frontmatter, rule_content)
        """
        if not rule_path.exists():
            raise FileNotFoundError(f"Rule file not found: {rule_path}")

        with open(rule_path, 'r') as f:
            content = f.read()

        frontmatter_dict, remaining = self.model.parse_yaml_frontmatter(content)
        frontmatter = self.model.validate_rule_frontmatter(frontmatter_dict)

        return frontmatter, remaining

    def load_skill_config(self, skill_path: Path) -> SkillConfig:
        """Load and validate skill configuration"""
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")

        with open(skill_path, 'r') as f:
            content = f.read()

        frontmatter_dict, _ = self.model.parse_yaml_frontmatter(content)
        return self.model.validate_skill_config(frontmatter_dict)

    def load_claude_md(self) -> ClaudeConfig:
        """Load main CLAUDE.md configuration"""
        claude_md_path = self.claude_dir / 'CLAUDE.md'

        if not claude_md_path.exists():
            raise FileNotFoundError(f"CLAUDE.md not found at {claude_md_path}")

        with open(claude_md_path, 'r') as f:
            content = f.read()

        return self.model.parse_claude_md(content)

    def validate_imports(self, config: ClaudeConfig) -> List[str]:
        """
        Validate all import paths exist

        Returns:
            List of invalid import paths (empty if all valid)
        """
        invalid = []

        for import_path in config.imports:
            if not self.glob_validator.validate_import_path(import_path, self.claude_dir):
                invalid.append(import_path)

        return invalid

    def find_rule_files(self) -> List[Path]:
        """Find all rule files in .claude/rules/"""
        rules_dir = self.claude_dir / 'rules'

        if not rules_dir.exists():
            return []

        return list(rules_dir.glob('*.md'))

    def find_skill_files(self) -> List[Path]:
        """Find all skill SKILL.md files"""
        skills_dir = self.claude_dir / 'skills'

        if not skills_dir.exists():
            return []

        return list(skills_dir.glob('*/SKILL.md'))

    def validate_glob_patterns(self, patterns: List[str]) -> Dict[str, bool]:
        """
        Validate multiple glob patterns

        Returns:
            Dict mapping pattern to validity (True/False)
        """
        results = {}

        for pattern in patterns:
            results[pattern] = self.glob_validator.is_valid_glob(pattern)

        return results

    def check_read_only_tools(self, skill: SkillConfig) -> bool:
        """
        Check if skill uses only read-only tools

        Read-only tools: Read, Grep, Glob
        """
        read_only = {'Read', 'Grep', 'Glob'}
        return all(tool in read_only for tool in skill.allowed_tools)

    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of configuration state"""
        summary = {
            'root_path': str(self.root_path),
            'claude_dir_exists': self.claude_dir.exists(),
            'rule_files': len(self.find_rule_files()),
            'skill_files': len(self.find_skill_files()),
        }

        try:
            claude_config = self.load_claude_md()
            summary['imports'] = len(claude_config.imports)
            summary['invalid_imports'] = len(self.validate_imports(claude_config))
        except FileNotFoundError:
            summary['imports'] = 0
            summary['invalid_imports'] = 0

        return summary
