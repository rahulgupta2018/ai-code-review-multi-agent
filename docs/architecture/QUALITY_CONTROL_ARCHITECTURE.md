# Quality Control Architecture

This document clarifies the different quality control mechanisms in the system to avoid confusion.

## Two Distinct Quality Control Systems

### 1. LLM Output Validation (`config/llm/output_validation.yaml`)
**Purpose**: Controls the quality of AI agent responses and analysis outputs
**What it validates**:
- AI-generated analysis accuracy
- Confidence scores and evidence validation
- Bias detection in AI responses
- Hallucination prevention
- Factual consistency of AI outputs

**Example**: "Is the AI's code analysis accurate and unbiased?"

### 2. Code Quality Gates (`config/rules/quality_gates.yaml`)
**Purpose**: Defines quality standards for the code being analyzed
**What it validates**:
- Code complexity thresholds
- Security vulnerability limits
- Test coverage requirements
- Performance benchmarks
- Architecture quality metrics

**Example**: "Does the target code meet our quality standards?"

## Flow Diagram

```
Target Code → [Code Quality Gates] → AI Analysis → [LLM Output Validation] → Final Report
```

## File Responsibilities

| File | Validates | Controls |
|------|-----------|----------|
| `config/llm/output_validation.yaml` | AI responses | LLM behavior |
| `config/rules/quality_gates.yaml` | Target code | Code standards |

## Configuration Integration

Both systems work together:
1. **Code Quality Gates** determine if code meets standards
2. **LLM Output Validation** ensures AI analysis is reliable
3. Combined results provide trustworthy code review

## No Duplication

While both files contain "quality" concepts, they operate on different subjects and serve complementary purposes in the overall quality assurance pipeline.