---
inclusion: always
---

# Karpathy-Inspired AI Coding Principles
> Derived from Andrej Karpathy's observations on LLM coding pitfalls.
> These are ACTIVE RULES — not suggestions. Apply them on every task.

---

## The Four Principles

---

### 1. Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before writing a single line of code:
- **State assumptions explicitly** — If uncertain about intent, ask. Never silently pick an interpretation.
- **Present multiple interpretations** — When ambiguity exists, name the options and ask which to pursue.
- **Push back when warranted** — If a simpler approach exists, say so before implementing the complex one.
- **Stop when confused** — Name exactly what is unclear and ask for clarification. Do not guess and proceed.
- **Surface tradeoffs** — If there are meaningful tradeoffs (speed vs. simplicity, flexibility vs. coupling), present them.

❌ BAD: Silently assume what the user meant and implement it.
✅ GOOD: "I see two interpretations: A or B. Which do you want?"

---

### 2. Simplicity First
**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was explicitly asked
- No abstractions for single-use code
- No "flexibility" or "configurability" that wasn't requested
- No error handling for impossible/irrelevant scenarios
- No future-proofing that wasn't asked for
- If 200 lines could be 50, rewrite it to 50

**The test:** Would a senior engineer say this is overcomplicated? If yes, simplify before submitting.

❌ BAD: Adding a plugin system when the user asked for one function.
✅ GOOD: Write the one function. Nothing else.

---

### 3. Surgical Changes
**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Do NOT "improve" adjacent code, comments, or formatting
- Do NOT refactor things that aren't broken
- Match existing style, even if you'd do it differently
- If you notice unrelated dead code, **mention it — don't delete it**

When your changes create orphans:
- Remove imports/variables/functions that **YOUR changes** made unused
- Do NOT remove pre-existing dead code unless explicitly asked

**The test:** Every changed line must trace directly to the user's request. If it can't, revert it.

❌ BAD: Fixing a bug and also "cleaning up" 3 unrelated functions.
✅ GOOD: Fix only the bug. Note the unrelated issues separately.

---

### 4. Goal-Driven Execution
**Define success criteria. Loop until verified.**

Transform imperative tasks into verifiable goals:

| Instead of... | Transform to... |
|---|---|
| "Add validation" | "Write tests for invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces it, then make it pass" |
| "Refactor X" | "Ensure tests pass before and after" |

For multi-step tasks, state a brief plan first:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria = Kiro can loop independently.
Weak criteria ("make it work") = constant back-and-forth.

---

## How to Know These Are Working

These principles are working if you see:
- **Fewer unnecessary changes in diffs** — only requested changes appear
- **Fewer rewrites** — code is simple the first time
- **Clarifying questions come before implementation** — not after mistakes
- **Clean, minimal PRs** — no drive-by refactoring or "improvements"

---

## Tradeoff Note

These principles bias toward **caution over speed**.

For trivial tasks (typo fixes, obvious one-liners), use judgment — not every change needs full rigor.

The goal is reducing costly mistakes on non-trivial work, not slowing down simple tasks.

---

## PurpleOps Application

Apply these principles specifically to this project:

- **Think Before Coding**: PurpleOps has complex agent interactions. Always clarify which agent (Red/Blue/Coordinator) is being modified before touching agent code.
- **Simplicity First**: The Coordinator already handles orchestration. Don't add orchestration logic to Red/Blue agents.
- **Surgical Changes**: The codebase has 13 agents + routes + utils. Only touch the specific file requested.
- **Goal-Driven**: For agent changes, define: "Agent X should do Y when Z" — then verify with a test.
