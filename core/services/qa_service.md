# QAService — Specification
<!-- Status: Active -->

## Purpose
6-check quality gate before any external action. Mirrors `core/qa_layer.md`.

## Interface
```
Input:  { agent_output: dict, domain: string, constraints: list }
Output: { passed: bool, checks: dict[str, CheckResult], failures: list, recommendation: string }
```

## Checks
1. **factual_fit** — facts accurate, sources real, tools used when needed
2. **style_fit** — tone/length/language matches target
3. **policy_fit** — complies with loaded constraints
4. **risk_check** — privacy/embarrassment/conflict/accuracy risks
5. **missing_context** — critical info gaps, guessing vs knowing
6. **wrong_action** — correct tool, answers what was asked, within role

## Failure Handling
- Any check fails → action stops
- Recommendation: "fix_and_send" | "retry_agent" | "cancel"
