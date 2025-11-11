# Tree-sitter Configuration Files

This directory contains two complementary configuration files for the Tree-sitter multi-language analysis system:

## File Purposes

### 📋 `languages.yaml` - Language Support & High-Level Configuration
**Purpose**: Language definitions, framework detection, and analysis configuration
**Content**:
- ✅ **Language support definitions** (12+ languages)
- ✅ **AST node mappings** for each language
- ✅ **Framework detection patterns** (React, Spring, Django, etc.)
- ✅ **File processing rules** (include/exclude patterns)
- ✅ **Analysis thresholds** and complexity limits
- ✅ **Legacy pattern compatibility** for existing tools
- ✅ **Performance optimization settings**

**Example**: Framework detection using string patterns
```yaml
frameworks:
  - name: "React"
    patterns: ["import React", "useState", "useEffect"]
```

### 🔍 `patterns.yaml` - Tree-sitter Query Patterns
**Purpose**: Low-level AST query patterns using Tree-sitter S-expression syntax
**Content**:
- ✅ **Tree-sitter specific queries** using `@identifiers` and `#match?` syntax
- ✅ **Security vulnerability patterns** (SQL injection, XSS, etc.)
- ✅ **Code quality patterns** (complexity, magic numbers, etc.)
- ✅ **Performance analysis patterns** (inefficient loops, memory leaks)
- ✅ **Language-specific AST queries** for precise code analysis

**Example**: Tree-sitter query for detecting dangerous functions
```yaml
dangerous_functions:
  - "(call (identifier) @func (#match? @func \"^(eval|exec|compile)$\"))"
```

## Key Differences

| Aspect | `languages.yaml` | `patterns.yaml` |
|--------|------------------|-----------------|
| **Level** | High-level configuration | Low-level AST queries |
| **Syntax** | YAML + Regex patterns | YAML + Tree-sitter S-expressions |
| **Purpose** | Language support & framework detection | Precise code analysis queries |
| **Usage** | Configuration and setup | Runtime AST pattern matching |
| **Examples** | `"@SpringBootApplication"` | `"(annotation (identifier) @annotation)"` |

## Why Both Are Needed

### 🔧 `languages.yaml` provides:
1. **Language Configuration** - Which languages to support and how
2. **Framework Detection** - High-level pattern matching for frameworks
3. **File Processing** - What files to include/exclude
4. **Analysis Settings** - Thresholds, limits, and optimization settings

### 🎯 `patterns.yaml` provides:
1. **Precise AST Queries** - Exact syntax tree pattern matching
2. **Security Analysis** - Vulnerability detection using AST structure
3. **Code Quality** - Detailed analysis using parsed syntax trees
4. **Performance Patterns** - Runtime analysis of code structures

## File Sizes & Complexity

- **`languages.yaml`**: 1,090 lines, 32KB - Comprehensive language support
- **`patterns.yaml`**: 267 lines, 8KB - Focused AST query patterns

## Configuration Flow

```
1. languages.yaml → Configures which languages and frameworks to support
2. patterns.yaml → Defines how to analyze the parsed code using AST queries
3. Runtime → Tree-sitter parses code and applies patterns for analysis
```

## Usage Examples

### Framework Detection (languages.yaml)
```yaml
# Detects React components by string patterns
frameworks:
  - name: "React"
    patterns: ["import React", "useState", "useEffect"]
```

### Security Analysis (patterns.yaml)
```yaml
# Detects SQL injection using AST structure
sql_injection:
  - "(string) @sql (#match? @sql \"SELECT.*FROM.*WHERE.*\\+\")"
```

Both files work together to provide comprehensive multi-language code analysis with both high-level framework detection and precise AST-based pattern matching.