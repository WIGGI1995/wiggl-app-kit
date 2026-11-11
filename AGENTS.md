# AGENTS.md — WIGGLIFICATION (Die totale Verwiggelung)

> "Die totale Verwiggelung" – Platform Automation, Governance & Agentic Architecture.
> Corporate Brand Color: `#10B981` / `#22C55E` / `#064E3B` (Emerald / Green Spectrum).

---

## 1. Obligatory Skills & Modes
All agents operating within the **WIGGLIFICATION** repository MUST strictly load and abide by:
- **`/caveman`**: Ultra-compressed communication and execution mode for maximum token efficiency and zero fluff.
- **`/clean-code`**: Strict adherence to software craftsmanship principles (SRP, immutability, fail fast, guard clauses).
- **`/caveman-commit`**: Conventional Commits generator producing terse, intent-preserving commit messages.

---

## 2. Multi-Tier Model Routing Matrix
Task complexity determines the exact model tier deployed:
- **`flash_lite`**: Configuration files, JSON schemas, static assets, Markdown documentation, icon definitions.
- **`flash`**: Standard feature modules, unit tests, integration tests, infrastructure definitions, Docker compose files.
- **`pro` / `inherit` / `claude`**: Core architecture, security boundaries, cryptographic modules, authorization subsystems, security code reviews.

---

## 3. Clean Code Rules & Craftsmanship
- **Single Responsibility Principle (SRP)**: Each function, class, and module performs exactly one well-defined task.
- **Function Length & Complexity**: Maximum **20–30 lines** per function. Maximum **3 parameters** per function (if more data is required, pass a typed frozen dataclass, Pydantic model, or TypeScript interface).
- **Control Flow**: Guard clauses (early returns) instead of deep `if` nesting.
- **Immutability**: Enforce `frozen=True` in Python dataclasses/Pydantic models and `readonly` / `readonly` modifiers in TypeScript.
- **Fail Fast & Fail Loud**: No silent fallbacks, no empty `except`/`catch` blocks, no returning `None` or default fallback values upon error conditions.
- **Anti-Patterns Prohibited**: No pass-through wrappers, no boolean flag parameters (`is_active: bool`) for control flow branching, no magic numbers.
- **Strict Typing**: Full compatibility with `mypy --strict` in Python and `strict: true` in TypeScript.
- **Precise Domain Naming**: Generic, utility naming is strictly forbidden. No `utils.py`, `helpers.py`, `manager.py`, `common.ts`. Use explicit domain names (e.g., `crypto_hasher.py`, `jwt_verifier.py`).

---

## 4. Git Workflow & Branching Strategy
- **`main`**: Production-ready releases tied strictly to Semantic Versioning (`vX.Y.Z`). Protected branch requiring passing CI and peer review.
- **`dev`**: Default integration branch for ongoing development. All feature and bugfix PRs merge into `dev`.
- **`feature/<issue-id>-<slug>`**: Dedicated branch per GitHub issue. Pull requests into `dev` must include `Closes #<id>` in their description.
- **Branch Inspection & Merge Order Governance**:
  - Before merging any feature branch, agents MUST inspect active branches and open PRs across all repositories (`gh pr list`, `git branch -a`).
  - Merge order follows dependency hierarchy: SDK (`wiggl-app-kit`) -> Platform Core (`Platform`) -> Tenant Apps (`App-Example`).
  - Sequence merges to eliminate cross-repo divergence: merge feature into `dev`, verify CI, merge `dev` into `main` (auto-tagging release and deploying to Raspberry Pi), and immediately merge `origin/main` back into `dev` (`git merge origin/main`) before subsequent feature releases.
  - Releases on `main` MUST trigger live automated deployments to the self-hosted Raspberry Pi runner across all repositories.

---

## 5. Architecture & Single-Port Traefik Path Routing
The platform operates locally and via DynDNS through a **single Traefik edge router port**, routing requests via clean path prefixes:
- `/` -> Unified Portal / Frontend Gateway
- `/api` -> Platform Core Backend API
- `/auth` -> Keycloak IAM Authentication Gateway
- `/grafana` -> Observability & Metrics Dashboard
- `/apps/<slug>` -> Isolated Tenant App Frontend
- `/apps/<slug>/api` -> Isolated Tenant App Backend API
- `/mail` -> Mailpit Local SMTP Testing UI
- `/docs-portal` -> Platform Documentation & Schema Portal

---

## 6. Deployment Architecture & Operations
Deployments execute automatically via GitHub Actions runner (`[self-hosted, pi]`) on Raspberry Pi:
- **Two-Stage Git Flow Release**:
  - `feature/*` -> `dev`: Code quality, tests, linting, security scans.
  - `dev` -> `main`: Auto-tags SemVer release (`vX.Y.Z`) and executes live deployment.
  - **Divergence Prevention**: When `dev` merges into `main`, GitHub creates a merge commit on `main`. Always merge `origin/main` back into `dev` (`git merge origin/main`) before opening new release PRs to ensure full commit lineage preservation (e.g. merge commits like `d7f61e5`).
- **Database Persistence Contract**:
  - `wiggl-postgres` is marked `restart: always` and MUST NEVER be pulled or recreated during platform deployments (`docker compose up -d --no-recreate postgres`).
  - Container recreate on Postgres is strictly prohibited; volume persistence (`./data/postgres`) and container ID must be preserved across updates.
- **Force-Recreate Guard for Config Mounts**:
  - Services relying on file bind mounts (e.g. `ddns-updater`, tenant apps) must be deployed with `--force-recreate` when configuration or mount namespaces change. Docker Compose does not detect host file inode replacements without recreation.
- **Keycloak 26 Hostname v2 & Proxy Routing**:
  - Keycloak requires `KC_HOSTNAME: "${PUBLIC_BASE_URL:-https://wiggi.ddns.net}/auth"` and `KC_HTTP_RELATIVE_PATH: "/auth"`.
  - Traefik must pass `X-Forwarded-Proto=https` and `X-Forwarded-Port=443` via headers middleware.
  - Health checks against Keycloak must include `-H "Host: ${DOMAIN}"` to prevent HTTP 500 rejection.
- **Zero Platform Downtime Tenant App Hot Updates**:
  - Tenant apps deploy independently without platform downtime via `repository_dispatch` (types: `[deploy-app, update-tenant-app]`) or `workflow_dispatch` (`action: update-app-only`).

---

## 7. Tenant App Governance Contract (App-Example / WigglVault)
Tenant apps (e.g. `WIGGI1995/App-Example`) integrate into WIGGLIFICATION under strict architectural contracts:
- **Host-Tenant Demarcation**:
  - Platform provides Edge Routing (Traefik), IAM (Keycloak), Observability (OTel/Loki/Tempo/Prometheus/Grafana), Database (Postgres), and Object Storage (MinIO).
  - Tenant apps execute as isolated services mounted under `/apps/<slug>` (Frontend) and `/apps/<slug>/api` (Backend).
- **Branch Synchronization Contract**:
  - Platform deployment pipelines strictly check out the `main` branch (`ref: main`) of tenant repositories via `APP_DEPLOY_KEY`.
  - Feature branches and `dev` in tenant repositories must be merged into `main` before triggering production rollouts.
- **Version & Manifest Consistency**:
  - Every tenant app release must keep the following files synchronized to the exact SemVer tag (`vX.Y.Z`):
    - `VERSION` file (raw SemVer string)
    - `app-manifest.yaml`: `metadata.version`, `deployment.frontend.image`, `deployment.backend.image`
    - Backend packaging: `pyproject.toml` (`version`), `__version__`, and runtime settings
    - `docker-compose.yml`: `APP_VERSION` and framework-specific settings
- **Pydantic Settings & Environment Prefix Rule**:
  - If a tenant backend uses Pydantic Settings with a prefix (e.g. `env_prefix="VAULT_"`), environment variables in `docker-compose.yml` MUST use that prefix (e.g. `VAULT_APP_VERSION`), or settings must use `SettingsConfigDict(extra="ignore")` with aliases to prevent silent fallback to default values.
- **Container Build & Force-Recreate Contract**:
  - Tenant container updates MUST execute with `docker compose up -d --build --force-recreate --remove-orphans`. Omission of `--force-recreate` causes Docker Compose to leave older container instances running.
- **Isolated Tenant Resources**:
  - Dedicated PostgreSQL role and database per tenant app (e.g. `vault_user` / `app_wiggl_vault`), initialized idempotently on startup.
  - Dedicated MinIO S3 bucket (e.g. `app-wiggl-vault`).
  - Integration into the shared platform network `wiggl_net`.
  - Traefik labels must specify entrypoints `web,websecure` and middleware `wiggl-sec-headers@file`.

---

## 8. Branch Protection & Quality Gates
- **Protected Branch Mandate**: Both `main` and `dev` branches in Platform and all tenant repositories (`App-Example`) must be protected against direct unreviewed pushes.
- **PR Enforcement via CI Guard**: Because GitHub Free personal plans restrict classic API branch protection for private repositories, the CI pipeline enforces direct-push guards and strictly validates all commits through pull requests.
- **GitHub Pro / Enterprise Setup**: If the organization upgrades or sets repositories to public, enforce GitHub Branch Protection with:
  - Required pull request reviews before merging.
  - Required status checks to pass before merging (`1. Gitleaks, License, Ruff, Mypy Strict & Pytest`).
  - Strict branch up-to-date enforcement before merge.

---

## 9. Observability & Telemetry Governance Contract (OTel, Loki, Tempo, Prometheus, Grafana)
All platform services and tenant apps (`App-Example`) MUST adhere to the standardized observability architecture:
- **OTLP Ingestion Standard**:
  - OpenTelemetry endpoints run centrally on `http://otel-collector:4318` (HTTP OTLP) and `otel-collector:4317` (gRPC OTLP).
  - Logs, metrics, and traces are transmitted via standard OTLP protocols without ad-hoc sidecars or proprietary agents.
- **Tenant App Decorator Suite**:
  - Endpoints in tenant apps must be instrumented using clean, typed decorators:
    - `@log_endpoint` (`@logging`): Logs entry, execution checkpoints, duration, response code, and trace context.
    - `@track_metrics` (`@metrics`): Records request counters and latency histograms (`p50`, `p95`, `p99`).
    - `@trace_span` (`@tracing`): Emits named OpenTelemetry child spans for fine-grained Tempo waterfall visualization.
    - `@audit_event` (`@audit`): Emits structured tamper-evident audit records (actor, action, target) for security operations.
    - `@error_tracker` (`@errors`): Intercepts, categorizes, and logs exceptions with structured severity and clean stack traces.
    - `@quota_guard` (`@quota`): Measures tenant payload byte sizes and updates real-time quota gauges.
    - `@observe`: Unified composite decorator combining logging, metrics, and tracing in one line.
- **Secret & PII Sanitization Mandate**:
  - Logging decorators MUST scrub sensitive keys (`authorization`, `token`, `password`, `key`, `cookie`, `secret`, base64 payloads) before emitting records. Credential leakage in logs is strictly prohibited.
- **Bi-Directional Trace-to-Log Correlation**:
  - Every log entry emitted MUST carry `trace_id` and `span_id`. In Grafana, clicking a log line jumps directly to the Tempo trace waterfall, and inspecting a Tempo trace provides a direct drill-down into Loki logs.
- **Loki Stream Labeling & Log Level Standard**:
  - Standardized levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
  - Loki stream labels: `{app="<slug>", level="<LEVEL>", job="<service>"}` for sub-second indexed querying.
- **Raspberry Pi Disk Guard & Retention Compactor**:
  - Loki compactor enforces 14-day retention (`retention_period: 336h`) to permanently protect the Raspberry Pi SD card / storage volume from exhaustion.
- **Manifest-Driven Observability**:
  - Tenant apps configure observability via `observability` in `app-manifest.yaml` (`platformLogging`, `otelTracing`, `logLevel`, `metricsEnabled`, `customMetrics`, `dashboardEnabled`). Grafana provides a dedicated dynamic dashboard for each tenant app automatically without manual dashboard configuration.
- **Pre-Configured Default Dashboards & Admin Authority**:
  - Grafana MUST provide immediately available pre-provisioned dashboards for the platform administrator (`admin:admin` / `wiggi1995@gmail.com`) with unrestricted root privileges.
  - Essential pre-configured dashboards:
    1. **Raspberry Pi Host & Server Overview**: Hardware metrics collected via `node-exporter` (CPU load, RAM usage, storage volume disk space, temperature, network I/O).
    2. **Platform & Tenant Logs Viewer**: Real-time LogQL streaming from Loki for all connected container services and application workloads with severity filtering (`DEBUG` to `CRITICAL`).
    3. **Tenant App Ecosystem**: Latency percentiles (P50/P95/P99), request throughput, error tracking, and storage quota gauges.

---

## 10. Official Tenant App SDK Contract (`wiggl-app-kit`)
All Python/FastAPI tenant apps targeting the WIGGLIFICATION platform MUST install and standardise on `wiggl-app-kit`:
- **Repository & Distribution**: `https://github.com/WIGGI1995/wiggl-app-kit` (Package: `wiggl-app-kit`).
- **Zero-Boilerplate Mandate**:
  - Tenant repositories and templates (`templates/app-template`) MUST NOT duplicate SDK logic. Local decorator, verifier, sanitizer, and telemetry boilerplate must be removed and consumed strictly from `wiggl-app-kit`.
- **`auth_kit.authentication` (Authentication)**:
  - `KeycloakAuthMiddleware`: Standard Starlette/FastAPI middleware validating Bearer tokens against Keycloak JWKS, providing public route bypass (`/health`, `/info`, `/docs`, `/openapi.json`), and injecting `KeycloakUser` into `request.state.user`.
  - `KeycloakTokenVerifier`: Cryptographic JWT verifier with dual RS256 JWKS caching and HS256 secret support.
  - `extract_bearer_token`: Header extraction helper.
  - `get_authenticated_user` (`get_current_user`): Request user dependency.
- **`auth_kit.authorization` (Authorization)**:
  - Role-Based Access Control (RBAC):
    - `require_roles(*roles)`: At least one role required (raises `AccessDeniedError` / `403 Forbidden`).
    - `require_all_roles(*roles)`: Every specified role strictly required.
    - `require_realm_role(role)` & `require_client_role(role)`: Strict scope boundaries.
  - Fine-Grained Permissions & Scopes:
    - `require_permissions(*permissions)` & `require_all_permissions(*permissions)`.
    - `require_scope(scope)`: OAuth2 / OIDC token scope validation.
- **`otel_kit` (Observability)**:
  - `configure_telemetry(service_name, otlp_endpoint)`: Automated setup for TracerProvider (`OTLPSpanExporter`), MeterProvider (`OTLPMetricExporter`), and OTLP log shipping (`HttpOtlpLogHandler`).
  - Decorator suite: `@observe`, `@log_endpoint`, `@track_metrics`, `@trace_span`, `@audit_event`, `@error_tracker`, `@quota_guard`.
  - Automated Secret & PII Sanitization.


