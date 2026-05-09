# Meta-Prompt: Generate Agent Framework for Any Project

Copy this entire block and paste it into a new chat with Kimi (or any LLM). It will instruct the model to scaffold a `.kimi/` rules infrastructure identical to what VibeCheck uses, adapted to your new project.

---

## BEGIN META-PROMPT

You are an expert software architect and agent-system designer. You have been hired to set up the AI-agent infrastructure for a new software project.

I want you to create a `.kimi/` directory at the project root that contains:
1. **Rules** (numbered, priority-ordered constraints)
2. **Workflows** (step-by-step guides for common tasks)
3. **Skills** (copy-paste code templates)
4. **Root AGENTS.md** (golden rules + project overview)
5. **Module-level AGENTS.md** files in each service/module directory

This infrastructure ensures that every subsequent AI agent (including you) that works on this codebase follows consistent patterns, respects boundaries, and knows the architecture before writing a single line of code.

---

### CONTEXT TO EXTRACT FROM THE PROJECT

Before writing any files, you MUST first explore the codebase and extract:

#### 1. Architecture
- [ ] List every service/module and its responsibility
- [ ] Map data flow between services (what calls what, via what protocol)
- [ ] List all ports, environment variables, and their defaults
- [ ] Identify the entry point of each service
- [ ] Note any standalone binaries or external dependencies (Redis, MediaMTX, etc.)

#### 2. Technology Stack
- [ ] Programming languages and versions
- [ ] Frameworks (FastAPI, React, etc.)
- [ ] Databases and cache layers
- [ ] Message buses or event systems
- [ ] Build tools and package managers

#### 3. Coding Patterns
- [ ] Import ordering (stdlib → third-party → local)
- [ ] Error handling style (exceptions vs returns)
- [ ] Async vs sync conventions
- [ ] Logging format and level conventions
- [ ] Configuration strategy (env vars, YAML, JSON)

#### 4. Boundaries & Constraints
- [ ] What are the "forbidden patterns"? (e.g., no cross-service imports)
- [ ] What is non-negotiable? (e.g., privacy, security rules)
- [ ] What is out of scope for MVP?
- [ ] Performance targets (latency, throughput)

#### 5. Extension Points
- [ ] How do you add a new module/service?
- [ ] How do you add a new feature end-to-end?
- [ ] What is the plugin/extension interface?

#### 6. Testing Strategy
- [ ] Unit test conventions
- [ ] Integration test approach
- [ ] Manual testing checklist

#### 7. Deployment
- [ ] Local dev setup
- [ ] Production target architecture
- [ ] Environment-specific configs

---

### OUTPUT STRUCTURE

After exploring, create these files:

```
.kimi/
├── AGENTS.md                  # Root: 10 golden rules, project overview, how to use this dir
├── rules/
│   ├── 01-architecture.md     # Service map, data flow, ports, boundaries
│   ├── 02-coding-standards.md # Language-specific patterns, style, imports, errors
│   ├── 03-[domain].md         # Domain-specific rules (e.g., CV processors, API design)
│   ├── 04-[domain].md         # Additional domain rules as needed
│   ├── 05-frontend.md         # If applicable
│   ├── 06-database.md         # ORM, migrations, seeding
│   ├── 07-testing.md          # Test patterns, coverage, manual checklist
│   └── 08-deployment.md       # Local setup, prod path, scaling, secrets
├── workflows/
│   ├── add-[module].md        # How to add a new X (processor, endpoint, model, etc.)
│   ├── add-[feature].md       # End-to-end feature addition
│   ├── connect-[external].md  # How to integrate external systems
│   ├── debug-[system].md      # Diagnostic steps for common failures
│   └── test-[environment].md  # How to test on mobile/staging/etc.
└── skills/
    ├── [domain]-template.md   # Copy-paste code templates
    ├── [domain]-template.md
    ├── debug-[topic].md       # Diagnostic skill
    └── [domain]-advanced.md   # Advanced patterns
```

For each service/module directory (e.g., `api-server/`, `cv-pipeline/`), create:
```
api-server/
├── AGENTS.md                  # Module-specific constraints, key files, env vars, testing
```

---

### RULE FILE FORMAT

Each rule file MUST contain:
- **What this governs** — 1 sentence
- **Constraints** — numbered, "must" language
- **Examples** — correct vs incorrect code snippets
- **Environment variables** — table of vars, defaults, descriptions
- **References** — links to related rules/workflows/skills

### WORKFLOW FORMAT

Each workflow MUST contain:
- **Goal** — what you achieve
- **Prerequisites** — what to read first
- **Steps** — numbered, with file paths and code snippets
- **Verification** — how to confirm it worked
- **Rollback** — how to undo if broken

### SKILL FORMAT

Each skill MUST contain:
- **When to use** — context
- **Copy-paste template** — complete, working code
- **How to customize** — what to change
- **Registration checklist** — what files to update

### AGENTS.md FORMAT

Root AGENTS.md MUST contain:
- Project name and one-line description
- Architecture diagram (ASCII or reference to docs)
- 10 golden rules (numbered, "never"/"always" language)
- How to use the `.kimi/` directory
- Module directory references
- Quick commands (start, stop, test)

Module AGENTS.md MUST contain:
- What this service does (1 paragraph)
- Entry point command
- Key files table (file → purpose)
- Constraints specific to this module
- Quick testing command
- Common issues and fixes

---

### GOLDEN RULES (adapt to project)

The root AGENTS.md must include golden rules like these (adapted to the actual project):

1. **Privacy/Security is non-negotiable.** [Specific rule]
2. **Minimal changes.** Touch only what you need.
3. **Follow existing patterns.** If a pattern exists, use it.
4. **Service boundaries are sacred.** No cross-service imports.
5. **Environment variables over hardcoded values.**
6. **All inter-service communication via [protocol].** [e.g., Redis pub/sub, gRPC, REST]
7. **The [component] is [technology].** No other frameworks.
8. **Every [module] must inherit [base class].**
9. **Test before claiming done.** Run the full stack.
10. **Keep it stupidly simple.** Stay in PRD scope.

---

### ADAPTATION GUIDELINES

- If the project is a monolith (not microservices), rules 01 and 04 should reflect module boundaries, not service boundaries.
- If the project uses React/Vue, create `05-frontend.md` with component patterns.
- If the project is Go/Rust, adapt `02-coding-standards.md` accordingly.
- If there is no database, skip `06-database.md`.
- Create as many domain-specific rule files as needed (03, 04, etc.).
- Create as many workflows as there are common tasks.

---

### FINAL CHECKLIST

Before finishing, verify:
- [ ] Every file has a clear purpose stated in the first line
- [ ] No placeholder text like "TODO" or "fill this in"
- [ ] All file paths are relative to project root
- [ ] All commands are copy-pasteable
- [ ] The root AGENTS.md references every rule, workflow, and skill
- [ ] Module AGENTS.md files reference the root AGENTS.md
- [ ] No contradictions between rules

---

## END META-PROMPT
