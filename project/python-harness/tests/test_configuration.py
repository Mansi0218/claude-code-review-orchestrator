"""
==================== Configuration System Tests ====================

Test suite for configuration validation system (35 tests)

Tests Model, Harness, and Orchestration layers of the configuration system.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from src.configuration.model import (
    ConfigModel, YAMLParser, PathGlobValidator, PathGlobPattern,
    RuleFrontmatter, SkillConfig, ClaudeConfig
)
from src.configuration.harness import ConfigurationHarness
from src.configuration.orchestrator import ConfigValidator, ValidationResult


# ==================== Model Layer Tests (12 tests) ====================

@pytest.mark.configuration
class TestConfigModel:
    """Test configuration model layer"""

    def test_parse_yaml_frontmatter_valid(self):
        """Test parsing valid YAML frontmatter"""
        content = """---
applies_to:
  - "src/**/*.py"
priority: high
---

# Rule content here"""

        model = ConfigModel()
        frontmatter, remaining = model.parse_yaml_frontmatter(content)

        assert 'applies_to' in frontmatter
        assert frontmatter['priority'] == 'high'
        assert '# Rule content here' in remaining

    def test_parse_yaml_frontmatter_no_frontmatter(self):
        """Test parsing content without frontmatter"""
        content = "# Just content"

        model = ConfigModel()
        frontmatter, remaining = model.parse_yaml_frontmatter(content)

        assert frontmatter == {}
        assert remaining == content

    def test_parse_yaml_frontmatter_invalid_yaml(self):
        """Test parsing invalid YAML syntax"""
        content = """---
invalid: yaml: syntax:
---"""

        model = ConfigModel()
        with pytest.raises(ValueError, match="Invalid YAML syntax"):
            model.parse_yaml_frontmatter(content)

    def test_parse_yaml_frontmatter_missing_closing(self):
        """Test frontmatter without closing ---"""
        content = """---
applies_to: ["src/**/*.py"]
# Missing closing ---"""

        model = ConfigModel()
        with pytest.raises(ValueError, match="missing closing"):
            model.parse_yaml_frontmatter(content)

    def test_validate_glob_pattern_valid(self):
        """Test valid glob pattern"""
        pattern = PathGlobPattern(pattern="src/**/*.py", priority="high")
        assert pattern.pattern == "src/**/*.py"
        assert pattern.priority == "high"

    def test_validate_glob_pattern_empty(self):
        """Test empty glob pattern raises error"""
        with pytest.raises(ValueError, match="cannot be empty"):
            PathGlobPattern(pattern="", priority="medium")

    def test_validate_glob_pattern_invalid_priority(self):
        """Test invalid priority value"""
        with pytest.raises(ValueError, match="Invalid priority"):
            PathGlobPattern(pattern="src/*.py", priority="super-high")

    def test_validate_rule_frontmatter(self):
        """Test rule frontmatter validation"""
        model = ConfigModel()
        frontmatter = {
            'applies_to': ['src/**/*.py', 'tests/**/*.py'],
            'priority': 'high',
            'enabled': True
        }

        rule = model.validate_rule_frontmatter(frontmatter)
        assert rule.priority == 'high'
        assert len(rule.applies_to) == 2

    def test_validate_skill_config_fork_context(self):
        """Test skill config with fork context"""
        model = ConfigModel()
        config = {
            'name': 'code-review',
            'context': 'fork',
            'allowed_tools': ['Read', 'Grep', 'Glob']
        }

        skill = model.validate_skill_config(config)
        assert skill.context == 'fork'
        assert 'Read' in skill.allowed_tools

    def test_validate_skill_config_invalid_tool(self):
        """Test skill config with invalid tool name"""
        model = ConfigModel()
        config = {
            'name': 'test-skill',
            'context': 'fork',
            'allowed_tools': ['Read', 'InvalidTool']
        }

        with pytest.raises(ValueError, match="Invalid tool name"):
            model.validate_skill_config(config)

    def test_parse_claude_md_with_imports(self):
        """Test parsing CLAUDE.md with imports"""
        content = """# Project Configuration

@.claude/standards/api.md
@.claude/standards/testing.md

Some other content
@.claude/standards/security.md
"""

        model = ConfigModel()
        config = model.parse_claude_md(content)

        assert len(config.imports) == 3
        assert '@.claude/standards/api.md' in config.imports

    def test_claude_config_invalid_import(self):
        """Test Claude config with invalid import path"""
        with pytest.raises(ValueError, match="must start with @"):
            ClaudeConfig(imports=['.claude/standards/api.md'])


# ==================== Glob Validator Tests (8 tests) ====================

@pytest.mark.configuration
class TestPathGlobValidator:
    """Test path glob validation"""

    def test_is_valid_glob_simple(self):
        """Test simple glob pattern validation"""
        assert PathGlobValidator.is_valid_glob("src/*.py")

    def test_is_valid_glob_recursive(self):
        """Test recursive glob pattern"""
        assert PathGlobValidator.is_valid_glob("src/**/*.py")

    def test_is_valid_glob_multiple_extensions(self):
        """Test glob with multiple file types"""
        assert PathGlobValidator.is_valid_glob("src/**/*.{py,ts}")

    def test_is_valid_glob_empty(self):
        """Test empty glob pattern is invalid"""
        assert not PathGlobValidator.is_valid_glob("")

    def test_resolve_glob_matches_files(self, tmp_path):
        """Test glob resolution finds matching files"""
        # Create test files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "file1.py").touch()
        (tmp_path / "src" / "file2.py").touch()
        (tmp_path / "src" / "file3.txt").touch()

        matches = PathGlobValidator.resolve_glob("src/*.py", tmp_path)
        assert len(matches) == 2

    def test_resolve_glob_no_matches(self, tmp_path):
        """Test glob resolution with no matches"""
        matches = PathGlobValidator.resolve_glob("nonexistent/*.py", tmp_path)
        assert len(matches) == 0

    def test_validate_import_path_exists(self, tmp_path):
        """Test import path validation when file exists"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "standards").mkdir()
        (claude_dir / "standards" / "api.md").touch()

        assert PathGlobValidator.validate_import_path("@.claude/standards/api.md", tmp_path)

    def test_validate_import_path_not_exists(self, tmp_path):
        """Test import path validation when file doesn't exist"""
        assert not PathGlobValidator.validate_import_path("@.claude/missing.md", tmp_path)


# ==================== Harness Layer Tests (7 tests) ====================

@pytest.mark.configuration
class TestConfigurationHarness:
    """Test configuration harness layer"""

    @pytest.fixture
    def test_project(self, tmp_path):
        """Create test project structure"""
        # Create .claude directory structure
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        (claude_dir / "standards").mkdir()
        (claude_dir / "rules").mkdir()
        (claude_dir / "skills").mkdir()

        # Create CLAUDE.md
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text("""# Project Config
@.claude/standards/api.md
@.claude/standards/testing.md
""")

        # Create standards files
        (claude_dir / "standards" / "api.md").write_text("# API Standards")
        (claude_dir / "standards" / "testing.md").write_text("# Testing Standards")

        # Create rule file
        rule_file = claude_dir / "rules" / "python-style.md"
        rule_file.write_text("""---
applies_to:
  - "src/**/*.py"
priority: high
---

# Python Style Rules
""")

        # Create skill
        skill_dir = claude_dir / "skills" / "code-review"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: code-review
context: fork
allowed_tools:
  - Read
  - Grep
  - Glob
---

# Code Review Skill
""")

        return tmp_path

    def test_load_claude_md(self, test_project):
        """Test loading CLAUDE.md"""
        harness = ConfigurationHarness(test_project)
        config = harness.load_claude_md()

        assert len(config.imports) == 2
        assert '@.claude/standards/api.md' in config.imports

    def test_validate_imports_all_valid(self, test_project):
        """Test import validation with all valid paths"""
        harness = ConfigurationHarness(test_project)
        config = harness.load_claude_md()
        invalid = harness.validate_imports(config)

        assert len(invalid) == 0

    def test_validate_imports_with_invalid(self, test_project):
        """Test import validation with invalid path"""
        harness = ConfigurationHarness(test_project)
        config = ClaudeConfig(imports=['@.claude/missing.md'])
        invalid = harness.validate_imports(config)

        assert len(invalid) == 1
        assert '@.claude/missing.md' in invalid

    def test_find_rule_files(self, test_project):
        """Test finding rule files"""
        harness = ConfigurationHarness(test_project)
        rules = harness.find_rule_files()

        assert len(rules) == 1
        assert rules[0].name == 'python-style.md'

    def test_find_skill_files(self, test_project):
        """Test finding skill files"""
        harness = ConfigurationHarness(test_project)
        skills = harness.find_skill_files()

        assert len(skills) == 1
        assert 'code-review' in str(skills[0])

    def test_load_rule_file(self, test_project):
        """Test loading and parsing rule file"""
        harness = ConfigurationHarness(test_project)
        rule_path = test_project / ".claude" / "rules" / "python-style.md"

        frontmatter, content = harness.load_rule_file(rule_path)

        assert frontmatter.priority == 'high'
        assert 'src/**/*.py' in frontmatter.applies_to
        assert '# Python Style Rules' in content

    def test_check_read_only_tools(self, test_project):
        """Test checking if skill uses only read-only tools"""
        harness = ConfigurationHarness(test_project)
        skill_path = test_project / ".claude" / "skills" / "code-review" / "SKILL.md"

        skill = harness.load_skill_config(skill_path)
        assert harness.check_read_only_tools(skill)

        # Test with non-read-only tool
        skill.allowed_tools.append('Write')
        assert not harness.check_read_only_tools(skill)


# ==================== Orchestration Layer Tests (8 tests) ====================

@pytest.mark.configuration
class TestConfigValidator:
    """Test configuration validator orchestration"""

    @pytest.fixture
    def valid_project(self, tmp_path):
        """Create valid test project"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        (claude_dir / "standards").mkdir()
        (claude_dir / "rules").mkdir()
        (claude_dir / "skills").mkdir()

        # CLAUDE.md
        (claude_dir / "CLAUDE.md").write_text("""
@.claude/standards/api.md
""")

        # Standards
        (claude_dir / "standards" / "api.md").write_text("# API")

        # Rule
        (claude_dir / "rules" / "style.md").write_text("""---
applies_to: ["src/**/*.py"]
priority: medium
---
# Style""")

        # Skill
        skill_dir = claude_dir / "skills" / "review"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: review
context: fork
allowed_tools: [Read, Grep]
---
# Review""")

        return tmp_path

    def test_validate_all_success(self, valid_project):
        """Test successful validation of valid project"""
        validator = ConfigValidator(valid_project)
        result = validator.validate_all()

        assert result.passed
        assert result.get_exit_code() == 0
        assert result.get_status() == "OK"

    def test_validate_missing_claude_dir(self, tmp_path):
        """Test validation with missing .claude directory"""
        validator = ConfigValidator(tmp_path)
        result = validator.validate_all()

        assert not result.passed
        assert result.get_exit_code() == 1
        assert len(result.errors) > 0

    def test_validate_invalid_import(self, tmp_path):
        """Test validation with invalid import path"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        (claude_dir / "CLAUDE.md").write_text("@.claude/missing.md")

        validator = ConfigValidator(tmp_path)
        result = validator.validate_all()

        assert not result.passed
        assert any('Import path not found' in err for err in result.errors)

    def test_validate_invalid_glob_pattern(self, tmp_path):
        """Test validation with invalid glob pattern in rule"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Config")
        (claude_dir / "rules").mkdir()

        # Rule with empty glob pattern (invalid)
        (claude_dir / "rules" / "bad.md").write_text("""---
applies_to: [""]
---
# Bad Rule""")

        validator = ConfigValidator(tmp_path)
        result = validator.validate_all()

        assert not result.passed

    def test_validation_result_add_error(self):
        """Test adding errors to validation result"""
        result = ValidationResult()
        assert result.passed

        result.add_error("Test error")
        assert not result.passed
        assert len(result.errors) == 1

    def test_validation_result_add_warning(self):
        """Test adding warnings to validation result"""
        result = ValidationResult()
        result.add_warning("Test warning")

        assert result.passed  # Warnings don't fail validation
        assert len(result.warnings) == 1

    def test_validation_result_str(self):
        """Test validation result string representation"""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_warning("Warning 1")

        output = str(result)
        assert "Error 1" in output
        assert "Warning 1" in output
        assert "FAILED" in output

    def test_config_validator_run(self, valid_project):
        """Test validator run method returns correct exit code"""
        validator = ConfigValidator(valid_project)

        # Capture exit code
        exit_code = validator.run()
        assert exit_code == 0


# ==================== Summary ====================
# Total tests: 35
# - Model Layer: 12 tests
# - Glob Validator: 8 tests
# - Harness Layer: 7 tests
# - Orchestration Layer: 8 tests
