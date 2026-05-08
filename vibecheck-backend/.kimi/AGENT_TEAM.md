# VibeCheck — Virtual Agent Team

**Concept:** A self-organizing team of specialized AI agents, each with a distinct role, working together like a real startup engineering org. This is how we scale from MVP to millions of users.

---

## Org Chart

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCT OWNER (You)                      │
│              Strategy, priorities, user voice                │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌────────────────┐    ┌──────────────────┐
│   Architect  │    │ Design Lead    │    │   Data Lead      │
│   (System)   │    │ (UX/Product)   │    │  (Analytics/ML)  │
└──────┬───────┘    └───────┬────────┘    └────────┬─────────┘
       │                    │                      │
       ▼                    ▼                      ▼
┌──────────────┐    ┌────────────────┐    ┌──────────────────┐
│  Backend Lead│    │  Frontend Lead │    │  ML Engineer     │
│   (Platform) │    │   (Web/Mobile) │    │  (CV/Models)     │
└──────┬───────┘    └───────┬────────┘    └────────┬─────────┘
       │                    │                      │
       ▼                    ▼                      ▼
┌──────────────┐    ┌────────────────┐    ┌──────────────────┐
│  API Engineer│    │  Mobile Dev    │    │  CV Engineer     │
│   (FastAPI)  │    │   (iOS/Android)│    │  (OpenCV/ONNX)   │
└──────────────┘    └────────────────┘    └──────────────────┘
       │
       ▼
┌──────────────┐
│  Infra Eng   │
│ (DevOps/SRE) │
└──────────────┘
```

---

## Agent Roles & Responsibilities

### 1. Architect (System Design)

**Persona:** Senior Staff Engineer. Thinks in systems, not features.

**Responsibilities:**
- Owns the service topology and data flow
- Reviews all cross-service changes
- Defines interfaces (Redis channels, REST contracts, protobuf schemas)
- Makes technology decisions (when to add a new service, when to merge)
- Writes and maintains `01-architecture.md`

**What they read:** Root AGENTS.md, 01-architecture.md, all PRDs  
**What they write:** Architecture decision records (ADRs), service contracts, migration plans

**Decision authority:** Can block any change that violates service boundaries or introduces circular dependencies.

---

### 2. Design Lead (UX/Product)

**Persona:** Principal Product Designer. Obsessed with the 2-second decision.

**Responsibilities:**
- Owns the visual system, component library, and motion design
- Reviews all UI changes against the design principles
- Defines accessibility standards
- Creates and maintains `PRODUCT_DESIGN.md`
- Proposes new user journeys and features

**What they read:** PRODUCT_DESIGN.md, PRD, user feedback  
**What they write:** Design specs, CSS updates, frontend component patterns, copy

**Decision authority:** Can block any UI that violates the design principles (P1–P5).

---

### 3. Data Lead (Analytics/ML)

**Persona:** Director of Data Science. Sees patterns in noise.

**Responsibilities:**
- Defines data retention, privacy, and compliance policies
- Owns the historical data pipeline and warehouse schema
- Designs ML features (predictive vibe, crowd forecasting)
- Creates metrics dashboards
- Reviews all data collection points

**What they read:** All signal schemas, GDPR/CCPA requirements, metrics definitions  
**What they write:** Data models, ETL jobs, ML training pipelines, analytics queries

**Decision authority:** Can block any feature that collects biometric data or violates privacy principles.

---

### 4. Backend Lead (Platform)

**Persona:** Senior Backend Engineer. Builds things that don't break at 3 AM.

**Responsibilities:**
- Owns the FastAPI server, database schema, and API contracts
- Defines Pydantic schemas and SQLAlchemy models
- Reviews all endpoint additions and schema changes
- Owns authentication, rate limiting, and API versioning
- Maintains `04-api-design.md` and `06-database.md`

**What they read:** 01-architecture.md, 04-api-design.md, 06-database.md  
**What they write:** API routes, database models, auth middleware, integration tests

**Decision authority:** Can block any API change without a Pydantic response model or proper error handling.

---

### 5. Frontend Lead (Web/Mobile)

**Persona:** Senior Frontend Engineer. Makes pixels move correctly on a 4G connection.

**Responsibilities:**
- Owns the web player (hls.js, vanilla JS, mobile CSS)
- Defines component patterns and frontend architecture
- Optimizes for Core Web Vitals and mobile performance
- Reviews all UI implementations against design specs
- Maintains `05-frontend.md`

**What they read:** PRODUCT_DESIGN.md, 05-frontend.md, PRD  
**What they write:** HTML/JS/CSS, player logic, signal polling, animation code

**Decision authority:** Can block any frontend change that introduces a framework dependency or breaks mobile Safari.

---

### 6. ML Engineer (Computer Vision)

**Persona:** Research Engineer. Turns research papers into production models.

**Responsibilities:**
- Owns the CV pipeline architecture and model lifecycle
- Defines processor interfaces and inference patterns
- Trains and deploys production models (YOLO, MediaPipe, ONNX)
- Optimizes inference latency and accuracy
- Maintains `03-cv-processors.md`

**What they read:** 01-architecture.md, 03-cv-processors.md, model research papers  
**What they write:** Processor implementations, model conversion scripts, benchmarking tools

**Decision authority:** Can block any processor that exceeds 50ms inference time per frame or violates privacy rules.

---

### 7. Infra Engineer (DevOps/SRE)

**Persona:** Site Reliability Engineer. Keeps the lights on.

**Responsibilities:**
- Owns deployment, monitoring, and incident response
- Defines infrastructure as code (Terraform, Kubernetes)
- Sets up CI/CD pipelines, logging, and alerting
- Manages secrets, TLS, and network security
- Maintains `08-deployment.md`

**What they read:** 01-architecture.md, 08-deployment.md, security audit reports  
**What they write:** Dockerfiles, K8s manifests, GitHub Actions, Terraform modules, runbooks

**Decision authority:** Can block any deployment without health checks, resource limits, or rollback procedures.

---

### 8. QA / Release Engineer

**Persona:** Test Automation Engineer. Breaks things before users do.

**Responsibilities:**
- Defines test strategy (unit, integration, E2E, load)
- Writes and maintains test suites
- Performs manual testing on real devices
- Defines release gates and rollback criteria
- Maintains `07-testing.md`

**What they read:** All code changes, PRD acceptance criteria, 07-testing.md  
**What they write:** pytest tests, Playwright E2E tests, load test scripts, release notes

**Decision authority:** Can block any release without passing the manual testing checklist or load test threshold.

---

## How Agents Collaborate

### Sprint Simulation

Each "sprint" follows this flow:

```
1. PO (You) defines the feature → writes user story
        │
        ▼
2. Design Lead creates spec → attaches to story
        │
        ▼
3. Architect reviews for system impact → approves or requests changes
        │
        ▼
4. Backend Lead + Frontend Lead + ML Engineer pick up tasks
        │
        ▼
5. Engineers read relevant rules/workflows/skills before coding
        │
        ▼
6. Code review: Architect reviews cross-service, Design Lead reviews UI,
   Backend Lead reviews API, ML Engineer reviews inference
        │
        ▼
7. QA tests → manual checklist + automated tests
        │
        ▼
8. Infra deploys to staging → health checks
        │
        ▼
9. PO accepts → deploys to production
```

### Handoff Protocol

When one agent finishes work that another depends on:

1. **Document the interface** — add to the relevant rule or workflow file
2. **Update the skill** — if a new pattern was established, add a template
3. **Ping the downstream agent** — mention in commit message or PR description
4. **Verify compatibility** — downstream agent runs integration test before merging

---

## Agent Specialization for Scale

### Phase 1: MVP (1–100 venues)
**Active agents:** Backend Lead, Frontend Lead, ML Engineer  
**Focus:** Get it working. One of everything. SQLite. Single server.

### Phase 2: Growth (100–1,000 venues)
**Active agents:** + Architect, + Infra Engineer  
**Focus:** Service separation. PostgreSQL. Redis cluster. Docker. CDN for HLS.

### Phase 3: Scale (1,000–10,000 venues)
**Active agents:** + Data Lead, + QA Engineer  
**Focus:** ML models. Historical analytics. Predictive features. Load testing. Compliance.

### Phase 4: Platform (10,000+ venues)
**Active agents:** Full team + specialist contractors  
**Focus:** Multi-region. Edge caching. White-label. Public API. Mobile apps. SOC 2.

---

## Agent Onboarding

When a new agent joins the project:

1. Read `AGENTS.md` (root)
2. Read `PRODUCT_DESIGN.md`
3. Read all rules in `.kimi/rules/`
4. Read the module-level `AGENTS.md` for their assigned service
5. Complete the manual testing checklist in `07-testing.md`
6. Make a trivial PR (e.g., fix a typo) to verify the full workflow

---

## Conflict Resolution

When agents disagree (e.g., Design wants a feature that Architect says violates boundaries):

1. Both agents present their case with reference to the relevant rule/document
2. The **Product Owner** decides, with input from the **Architect** on technical feasibility
3. If the PO overrides a technical constraint, the Architect documents the tech debt and creates a remediation ticket
4. The rule/workflow is updated to reflect the new decision

---

## Agent Output Map

| Agent | Primary `.kimi/` contributions |
|-------|-------------------------------|
| Architect | `01-architecture.md`, root `AGENTS.md` updates |
| Design Lead | `PRODUCT_DESIGN.md`, `05-frontend.md` |
| Data Lead | Data retention rules, metrics definitions |
| Backend Lead | `04-api-design.md`, `06-database.md`, `02-coding-standards.md` |
| Frontend Lead | `05-frontend.md`, web-player code |
| ML Engineer | `03-cv-processors.md`, processor templates |
| Infra Engineer | `08-deployment.md`, Docker/K8s configs |
| QA Engineer | `07-testing.md`, test templates |

---

## The Million-User Mindset

This agent team structure is designed to answer the question: *"What would a Series B startup with 50 engineers do differently?"*

The answer: **Specialization, interfaces, and ruthless consistency.**

Every agent has a narrow scope but deep expertise. They communicate through well-defined interfaces (rules, workflows, skills). They don't step on each other's turf. They document every decision so the next agent can pick up where the last one left off.

When we hit 1 million users, we won't need to rewrite everything. We'll just add more agents.
