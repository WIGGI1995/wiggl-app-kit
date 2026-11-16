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
  - Services relying on file bind mounts (e.g. tenant apps, config mounts) must be deployed with `--force-recreate` when configuration or mount namespaces change. Docker Compose does not detect host file inode replacements without recreation.
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
- **Per-App Encrypted Secrets & Authentication Contract**:
  - Each tenant app repository owns an isolated `.env.secrets.enc` containing app credentials and `LOG_LEVEL`.
  - Tenant backend endpoints require Keycloak JWT Bearer tokens or `wiggl_session_token` / `wiggl_access_token` cookies; ONLY `/apps/<slug>/health` and `/apps/<slug>/api/health` bypass authentication.

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
  - Grafana MUST provide immediately available pre-provisioned dashboards with Keycloak Generic OAuth SSO (`auth.generic_oauth`).
  - **7 Pre-Configured Thematic Dashboard Areas (Zero Manual Config Needed)**:
    1. **Host & Pi Hardware (`server-overview.json`)**: Real-time Raspberry Pi hardware metrics collected via `node-exporter` (SoC temperature, CPU load, RAM usage, storage volume disk space, network I/O, system load).
    2. **Scrapers Breakdown (`server-overview.json`)**: Prometheus scrape targets status table, scrape duration/latency, and scrape sample rates.
    3. **Thematic & Unified Logs (`app-logs-otel.json`)**: 5 thematic log streams (Security & Auth Events, Errors & Exceptions, HTTP/API Requests, Storage & Quotas, Live Log Stream) with sorting and dynamic filters for App, Service, Level (`DEBUG` to `CRITICAL`), and search query.
    4. **Tenant Applications (`apps-overview.json`, `tenant-app-observability.json`)**: Ecosystem view of all tenant workloads (latency percentiles P50/P95/P99, throughput RPS, error tracking, MinIO storage quotas).
    5. **Platform Core & Service Metrics (`platform-metrics.json`)**: Edge gateway throughput (Traefik web/websecure RPS), P50/P95/P99 latencies, 2xx/3xx/4xx/5xx status distribution, and active upstream health.
    6. **Platform Security, IAM & Audit (`security-and-audit.json`)**: Keycloak authentication rate, 401 Unauthorized & 403 Access Denied rejection monitoring, and tamper-evident audit streams.
    7. **Storage, PostgreSQL & MinIO Observability (`storage-and-databases.json`)**: PostgreSQL active connections and transaction commit rates (TPS), MinIO S3 API request rates, and real-time tenant bucket quota gauges.
  - **1-Click Persistent Navigation Links**:
    - Every provisioned dashboard MUST include top-level `"links": [...]` enabling instant 1-click cross-dashboard navigation directly from the dashboard header without navigating through folders or menus.
  - **Loki LogQL Query Rules**:
    - Loki LogQL does NOT support PromQL `vector(0)`. Queries using `vector(0)` fail with syntax error. Use `"noValue": "0"` in `fieldConfig.defaults` instead.
    - OTLP log bodies are formatted with `[LEVEL] logger: message` for deterministic line filtering (`|~ "$level"`).
    - Multi-level logging active across all 5 levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) with verification test endpoints at `/api/v1/telemetry/test-log-levels` and `/apps/<slug>/api/test-log-levels`.
  - **Token-Based RBAC & SSO**:
    - Central Keycloak SSO via `auth.generic_oauth` (`grafana` client).
    - Role mapping: `platform-admin` and `admin` -> Grafana Admin; all other authenticated users -> Viewer.
    - Anonymous access is strictly disabled (`auth.anonymous enabled = false`).

---

## 10. Official Tenant App SDK Contract (`wiggl-app-kit`)
All Python/FastAPI tenant apps targeting the WIGGLIFICATION platform MUST install and standardise on `wiggl-app-kit`:
- **Repository & Distribution**: `https://github.com/WIGGI1995/wiggl-app-kit` (Package: `wiggl-app-kit`).
- **Turnkey 1-Line Bootstrap (`setup_wiggl_app`)**:
  - `wiggl-app-kit` provides universal 1-line onboarding for any FastAPI application:
    ```python
    from fastapi import FastAPI
    from wiggl_app_kit import setup_wiggl_app

    app = FastAPI(title="MyApp")
    setup_wiggl_app(app, service_name="my-app")
    ```
  - Automatically initializes:
    1. Multi-level structured logging and OTLP / Loki telemetry shipping.
    2. Keycloak RS256 token verification with support for Bearer headers and cookies (`wiggl_session_token`, `wiggl_access_token`).
    3. Health-check and OpenAPI documentation public bypass whitelist (`/health`, `/readyz`, `/apps/<slug>/health`, `/docs`, `/openapi.json`).
  - Supports custom verifier injection (`setup_wiggl_app(app, service_name="my-app", verifier=custom_verifier, public_prefixes=(...))`).
- **Zero-Boilerplate Mandate**:
  - Tenant repositories and templates (`templates/app-template`) MUST NOT duplicate SDK logic. Local decorator, verifier, sanitizer, and telemetry boilerplate must be removed and consumed strictly from `wiggl-app-kit`.
- **`auth_kit.authentication` (Authentication)**:
  - `KeycloakAuthMiddleware`: Standard Starlette/FastAPI middleware validating Bearer tokens against Keycloak JWKS, supporting HttpOnly/SameSite cookies (`wiggl_session_token` / `wiggl_access_token`), providing public route bypass, and injecting `KeycloakUser` into `request.state.user`.
  - `KeycloakTokenVerifier`: Cryptographic JWT verifier with dual RS256 JWKS caching and HS256 secret support.
  - `extract_bearer_token`: Header & cookie extraction helper.
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

---

## 11. Central Keycloak SSO, Security Model & Per-App Secrets Contract
- **Official Test Accounts**:
  - `admin` (`admin:admin`, Superuser: `platform-admin`, `vault-admin`)
  - `test-developer` (`developer@wiggl.local` / `test-dev-2026`, Roles: `app-developer`, `vault-editor`, `vault-viewer`)
  - `test-editor` (`editor@wiggl.local` / `test-edit-2026`, Roles: `platform-editor`, `vault-editor`, `vault-viewer`)
  - `test-viewer` (`viewer@wiggl.local` / `test-view-2026`, Roles: `platform-viewer`, `vault-viewer`)
- **Central Keycloak SSO & RBAC Authentication**:
  - All platform routes and tenant apps require authenticated Keycloak credentials via either:
    1. HTTP Authorization Header: `Authorization: Bearer <jwt_token>`
    2. HttpOnly / SameSite Cookies: `wiggl_session_token` (HttpOnly, Secure, SameSite=Lax, path=/) or `wiggl_access_token` (Secure, SameSite=Lax, path=/).
  - **Strict Authentication Bypass Whitelist**:
    - ONLY the following health endpoints bypass authentication:
      - `/health`
      - `/healthz`
      - `/readyz`
      - `/api/health`
      - `/apps/<slug>/health`
      - `/apps/<slug>/api/health`
    - All other endpoints, administrative APIs, and tenant routes strictly require valid authentication.
- **Single Superuser & Security Model**:
  - Single superuser `admin` defined in `.env` before encryption (`ADMIN_USERNAME=admin`, `ADMIN_PASSWORD=...`).
  - Random/dummy/test users are strictly prohibited in production and committed configurations.
  - 2FA/TOTP is disabled for now (`totp_required: false`, no mandatory `CONFIGURE_TOTP` action) to streamline automated operations.
  - Admin email is decoupled from personal addresses (configured as decoupled system identifier e.g. `admin@wiggl.local` or omitted).
  - The `admin` superuser has exclusive authority to provision and manage new platform users via the Platform API / Keycloak.
- **Per-App Encrypted Environments (`.env.secrets.enc`)**:
  - Each tenant application repository owns an isolated `.env.secrets.enc` containing app-specific credentials, database secrets, and runtime configuration including `LOG_LEVEL` (e.g. `LOG_LEVEL=DEBUG`).
  - Zero Plaintext Secrets in version control: secrets are encrypted with AES-256-GCM / Fernet using platform encryption tooling before git commit.
  - Runtime decryption occurs strictly during container startup/deployment without persisting decrypted files to disk.

---

## 12. Dynamic Tenant App Embedding, Design Bridge & Core Auth Governance
All tenant applications and platform host interfaces MUST strictly adhere to the automated embedding and styling contract:
- **Zero-Overhead Styling Mandate**:
  - Tenant applications MUST NOT manually duplicate platform navigation, portal headers, user management menus, or corporate CSS styles.
  - The Platform Core frontend provides a unified host shell via `AppHostComponent` mounted under `/app/:slug`.
  - The host toolbar provides breadcrumb navigation, return to Launchpad (`← Launchpad`), app metadata, current Keycloak client role badge, iframe reload, and fullscreen toggle.
- **Platform Bridge & CSS Theme Token Contract**:
  - Central platform assets are served directly from Traefik / Platform Frontend:
    - `/assets/platform-theme.css`: Corporate emerald tokens (`--wiggl-primary`, `--wiggl-surface`, etc.) and responsive resets.
    - `/assets/platform-bridge.js`: Bi-directional bridge connecting the embedded app with the host shell.
  - Every tenant app frontend `index.html` MUST include:
    ```html
    <link rel="stylesheet" href="/assets/platform-theme.css" />
    <script src="/assets/platform-bridge.js" defer></script>
    ```
  - **Bridge Auto-Detection & Message Protocol**:
    - `platform-bridge.js` detects embedding (`window.parent !== window`) and sets class `wiggl-embedded` on `document.documentElement`.
    - Redundant local headers, footers, and standalone nav bars (`.app-header`, `.app-footer`, `.portal-nav`) are automatically hidden.
    - Listens for `WIGGL_THEME_APPLY` postMessage events dispatched by `AppHostComponent` on iframe load, updating theme tokens dynamically.
- **Platform Core Route Authentication Middleware (`PlatformAuthMiddleware`)**:
  - All Platform Core routes (`/`, `/api/*`, `/app/*`) are guarded by `PlatformAuthMiddleware`.
  - Authenticates RS256 Keycloak JWT tokens from both:
    1. HTTP `Authorization: Bearer <jwt_token>` header.
    2. HttpOnly / SameSite cookies: `wiggl_session_token` and `wiggl_access_token`.
  - Strict Public Whitelist: ONLY `/health`, `/healthz`, `/readyz`, `/api/health`, `/apps/<slug>/health`, and `/apps/<slug>/api/health` bypass auth.
- **Strict Version Synchronization Contract**:
  - Whenever a tenant app is released, all platform references MUST be updated synchronously:
    1. Tenant App repository: `VERSION`, `app-manifest.yaml`, `pyproject.toml`, `settings.py`, `docker-compose.yml`.
    2. Platform Core pre-populated manifests (e.g. `backend/src/platform_api/main.py:build_default_vault_manifest()`).
    3. Platform Launchpad catalog (`frontend/src/app/features/launchpad/apps.service.ts`).
    4. Platform Catalog service (`frontend/src/app/features/catalog/catalog.service.ts`).
    5. Platform release version bump in `VERSION`, `CHANGELOG.md`, and `.release-please-manifest.json`.

---

## 13. Raspberry Pi Resource Guard, Memory Optimization & Pruning Contract
To prevent host memory exhaustion and runner disconnections on the self-hosted Raspberry Pi (8GB RAM):
- **Explicit Container Memory Limits (`mem_limit`)**:
  - All services in `docker-compose.yml` MUST declare strict `mem_limit` attributes:
    - Traefik: `256m`, PostgreSQL: `512m`, Keycloak: `768m`, MinIO: `384m`, Mailpit: `128m`
    - OTel-Collector: `256m`, Loki: `384m`, Tempo: `384m`, Node-Exporter: `64m`, Prometheus: `512m`, Grafana: `384m`
    - Docs-Portal: `128m`, Platform-Backend: `384m`, Platform-Frontend: `128m`, Portainer: `128m`
    - Tenant Apps (`App-Example`): Backend `384m`, Frontend `128m`
    - Total capped at ~4.8GB, guaranteeing >3GB headroom for Linux kernel, I/O page caches, and background tasks.
- **JVM & Node.js Memory Caps**:
  - Keycloak: Enforce `JAVA_OPTS_APPEND: "-Xms128m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=100"` to prevent unbounded JVM heap expansion.
  - Angular Frontend Build: Enforce `NODE_OPTIONS="--max-old-space-size=1024"` in `frontend/Dockerfile` to prevent Node.js V8 heap blowup during `ng build`.
- **Sequential Container Builds in CI/CD**:
  - Never execute concurrent multi-container builds (`docker compose build backend frontend`).
  - Always build sequentially (`docker compose build platform-backend` followed by `docker compose build platform-frontend`) to avoid simultaneous CPU saturation and RAM spikes.
- **Automated Memory & Container Pruning**:
  - Deployment pipelines MUST execute pre- and post-deployment pruning:
    1. `docker builder prune -f --filter "until=24h"` (remove stale buildkit layers)
    2. `docker image prune -af --filter "until=24h"` (clean dangling & untagged images)
    3. `docker container prune -f` (clean stopped containers)
    4. `docker network prune -f` (clean orphaned networks)
    5. `sync && echo 3 > /proc/sys/vm/drop_caches` (flush dirty pages, free dentries/inodes)
  - Dedicated script: `scripts/prune_memory_and_containers.sh` available for on-demand host maintenance.

---

## 14. Comprehensive Repository Architecture & File Location Map ("Where is What?")
To eliminate redundant file exploration and accelerate agent navigation across repositories:

### 14.1 Platform Core Repository (`Platform`)
- **Root & Orchestration**:
  - `docker-compose.yml`: Multi-container stack (Traefik, Postgres, Keycloak, Observability, Core Backend/Frontend, Portainer).
  - `.env` / `.env.example`: Central platform environment and credentials configuration.
  - `VERSION`: Canonical Semantic Version string (`1.1.0`).
  - `CHANGELOG.md`: Release notes, feature updates, and historical bugfixes.
  - `.github/workflows/ci.yml`: Unified CI/CD pipeline (Lint, Typecheck, Test, Release, Pi Deployment, Pruning).
- **Platform Backend (`backend/`)**:
  - `src/platform_api/main.py`: FastAPI entrypoint, lifespan lifecycle, middleware registration, health endpoints.
  - `src/platform_api/settings.py`: Pydantic BaseSettings, database URLs, Keycloak realm & OTel endpoints.
  - `src/platform_api/apps/`: Tenant App management, registration, manifest validation, and dynamic proxy routing.
  - `src/platform_api/auth/`: Keycloak authentication middleware, token verification, roles extraction (`PlatformAuthMiddleware`).
  - `src/platform_api/database.py` & `models/`: SQLAlchemy async session engine, PostgreSQL connection pool.
  - `src/platform_api/telemetry.py`: OpenTelemetry TracerProvider, MeterProvider, and OTLP log shipping setup.
  - `tests/`: 47 unit and integration tests (`conftest.py`, `test_main.py`, `test_apps.py`, `test_auth.py`).
- **Platform Frontend (`frontend/`)**:
  - `src/main.ts` & `src/app/app.routes.ts`: Angular 19 bootstrap and client-side routing.
  - `src/app/features/app-host/`: Unified tenant app iframe host shell (`app-host.component.ts`), breadcrumbs, theme sync (`WIGGL_THEME_APPLY`).
  - `src/app/features/launchpad/`: Central dashboard & tenant app launcher grid (`launchpad.component.ts`).
  - `src/app/features/catalog/`: Available and installed app catalog view (`catalog.component.ts`).
  - `src/app/features/admin/`: System management, user provisioning, service statuses.
  - `src/app/core/auth/`: Keycloak JS authentication service, silent token refresh, user state.
  - `public/assets/platform-theme.css`: Corporate emerald CSS variables, typography, and theme styling tokens.
  - `public/assets/platform-bridge.js`: Bi-directional iframe bridge script loaded by tenant apps.
- **Infrastructure & Provisioning (`infra/`)**:
  - `infra/traefik/dynamic.yml`: Edge routing rules, security headers middleware (`wiggl-sec-headers`), path prefixes.
  - `infra/keycloak/realm-export.json`: Keycloak realm configuration, clients (`platform-portal`, `grafana`), roles, users.
  - `infra/grafana/provisioning/`: Datasources (`datasources.yml`: Prometheus, Loki, Tempo) and dashboard providers (`dashboards.yml`).
  - `infra/grafana/dashboards/`: 7 pre-provisioned thematic JSON dashboards:
    1. `server-overview.json`: Pi hardware metrics (SoC temp, CPU, RAM, Disk) & scrapers breakdown.
    2. `app-logs-otel.json`: Multi-level thematic Loki log streams (Security, Errors, HTTP, Storage, Live).
    3. `apps-overview.json`: Ecosystem view of tenant workloads (RPS, latency, errors).
    4. `tenant-app-observability.json`: Dedicated drill-down dashboard for individual tenant apps.
    5. `platform-metrics.json`: Traefik edge throughput, HTTP status codes, service latencies.
    6. `security-and-audit.json`: Keycloak auth rates, 401/403 rejections, audit logs.
    7. `storage-and-databases.json`: PostgreSQL connections & TPS, MinIO S3 operations & tenant quotas.
  - `infra/prometheus/prometheus.yml`: Prometheus scrape configs for Traefik, Node-Exporter, OTel, Postgres, Keycloak.
  - `infra/otel/otel-collector-config.yaml`: Central OTLP receivers (4317/4318), processors (batch, memory_limiter), exporters (Prometheus, Loki, Tempo).
  - `infra/loki/loki-config.yaml`: Loki log engine with 14-day retention compactor (`retention_period: 336h`).
  - `infra/tempo/tempo-config.yaml`: Distributed tracing storage engine.
  - `infra/postgres/init-platform.sql`: PostgreSQL bootstrap script for platform and tenant roles/databases.
- **Documentation Portal (`docs/`)**:
  - `docs/index.html` & `docs/html/*.html`: Static documentation portal served on `/docs-portal`.
  - `schemas/app-manifest.schema.json`: JSON Schema specification for tenant `app-manifest.yaml`.
- **Maintenance & Tooling (`scripts/`)**:
  - `scripts/prune_memory_and_containers.sh`: Standalone RAM, container, image, and cache pruning tool.
  - `scripts/encrypt_env.py`: CLI tool for encrypting per-app `.env.secrets.enc`.

### 14.2 Tenant Application Repository (`App-Example` / `WigglVault`)
- **Root Configuration**:
  - `app-manifest.yaml`: App capabilities, metadata, navigation, roles, and observability settings.
  - `docker-compose.yml`: Standalone container configuration with `mem_limit` and network attachments.
  - `VERSION`: SemVer release tag (`1.1.8`).
  - `.env.secrets.enc`: AES-256-GCM / Fernet encrypted runtime secrets and `LOG_LEVEL`.
  - `.github/workflows/ci.yml`: CI linting, testing, multi-arch GHCR image publishing, and platform dispatch.
- **Tenant Backend (`backend/`)**:
  - `src/wiggl_vault/main.py`: FastAPI application initialized via `wiggl-app-kit`'s `setup_wiggl_app()`.
  - `src/wiggl_vault/settings.py`: Pydantic Settings using `VAULT_` prefix (`VAULT_APP_VERSION`, etc.).
  - `src/wiggl_vault/api/`: Domain endpoints (`health.py`, `items.py`, `test_levels.py`).
  - `pyproject.toml`: Poetry/pip packaging specification.
- **Tenant Frontend (`frontend/`)**:
  - `src/index.html`: Contains links to `/assets/platform-theme.css` and `/assets/platform-bridge.js`.
  - `src/app/`: Angular/Vue/Vanilla UI consuming tenant backend APIs under `/apps/<slug>/api`.

### 14.3 Official Tenant App SDK (`wiggl-app-kit`)
- **Package Root (`src/wiggl_app_kit/`)**:
  - `__init__.py`: Public API exports (`setup_wiggl_app`, auth & otel decorator exports).
  - `bootstrap.py`: `setup_wiggl_app(app, service_name, ...)` 1-line FastAPI onboarding bootstrap.
- **Authentication Kit (`src/wiggl_app_kit/auth_kit/`)**:
  - `authentication.py`: `KeycloakAuthMiddleware`, `KeycloakTokenVerifier` (RS256/JWKS/HS256), `extract_bearer_token`, `get_authenticated_user`.
  - `authorization.py`: RBAC guards (`require_roles`, `require_all_roles`, `require_realm_role`, `require_permissions`, `require_scope`).
- **Observability Kit (`src/wiggl_app_kit/otel_kit/`)**:
  - `telemetry.py`: `configure_telemetry(service_name, otlp_endpoint)` initializing Tracer, Meter, and OTLP logging.
  - `decorators.py`: Unified `@observe` and fine-grained decorators (`@log_endpoint`, `@track_metrics`, `@trace_span`, `@audit_event`, `@error_tracker`, `@quota_guard`).
  - `sanitizer.py`: Automated scrubbing of sensitive fields (`password`, `token`, `secret`, `cookie`, `key`, `authorization`).
- **Project Configuration**:
  - `pyproject.toml`: Build dependencies, packaging metadata, release configuration.




