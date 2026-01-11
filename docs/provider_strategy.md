# CineFlow Provider Strategy (Draft)

Version: v0.1
Date: 2026-01-02
Status: Draft

## 1. Purpose

Decouple hard-coded `sora.hk` integration into a pluggable Provider layer that can support multiple Sora-compatible vendors (OpenAI official and third parties). The goal is to enable feature coverage, quota management, cost control, and reliability through configurable routing and scheduling. Also introduce logical model IDs (`Sora2`, `Sora2Pro`) that are mapped to provider-specific model IDs.

## 2. Scope

- Backend Provider abstraction and adapters
- Capability and limit normalization
- Provider registry and configuration
- Scheduling strategies (manual, primary/secondary, load balancing)
- Error taxonomy and mapping
- Frontend selection and visibility

## 3. Provider Interface (Backend)

All providers implement a common interface. Example (Python-ish):

```
class Provider:
    def id(self) -> str: ...
    def display_name(self) -> str: ...

    def capabilities(self) -> ProviderCapabilities: ...
    def limits(self) -> ProviderLimits: ...

    def create_task(self, req: GenerationRequest) -> ProviderTaskRef: ...
    def get_task(self, task_id: str) -> ProviderTaskStatus: ...
```

## 3.1 Logical Model Registry

Logical models are user-facing IDs that remain stable across providers.\n

```
LogicalModel:
  id: sora2 | sora2pro
  display_name: Sora2 | Sora2 Pro
  description: string
  enabled: boolean
```

Provider mappings are maintained in the registry and not exposed to end users.\n

```
ModelProviderMap:
  logical_model_id: sora2
  provider_id: sora_hk | openai | aihubmix
  provider_model_ids: [provider-specific variants]
```

### Initial Provider Model Mapping (Draft)

```
sora2:
  sora_hk: [sora2]
  openai: [sora-2, sora-2-2025-12-08, sora-2-2025-10-06]
  aihubmix: [sora-2, web-sora-2]

sora2pro:
  sora_hk: [sora2-pro]
  openai: [sora-2-pro, sora-2-pro-2025-10-06]
  aihubmix: [sora-2-pro, web-sora-2-pro]
```

Notes:
- AIHubMix model IDs confirmed via `GET https://aihubmix.com/v1/models`.
- OpenAI/Sora.hk model IDs are placeholders until official docs confirm naming.
- AIHubMix video API: `POST https://aihubmix.com/v1/videos`, download via `GET /v1/videos/{video_id}/content` (Authorization required).
- Duration differences: Sora.hk uses 10/15/25s; AIHubMix Sora uses 4/8/12s. Provider capabilities must gate routing.
- OpenAI video API (from official SDK sources): `POST https://api.openai.com/v1/videos`, `GET /v1/videos/{video_id}`, `GET /v1/videos/{video_id}/content` (Authorization required).

### Normalized Request Model

```
GenerationRequest:
  prompt: string
  image_url: string | null
  duration_seconds: 10|15|25
  resolution: horizontal|vertical
  is_pro: boolean
  metadata: object
```

### Normalized Response Model

```
ProviderTaskStatus:
  status: queued|running|completed|failed
  progress: 0-100
  video_url: string | null
  error_code: string | null
  error_message: string | null
  raw: object
```

## 4. Capabilities and Limits

### Capability Model

```
ProviderCapabilities:
  supports_image_to_video: boolean
  supported_durations: [10,15,25]
  supported_resolutions: [horizontal, vertical]
  supports_pro: boolean
```

### Limits Model

```
ProviderLimits:
  max_concurrency: integer
  rate_limit_per_minute: integer
  quota_remaining: number | null
  cost_per_second: number | null
```

## 5. Provider Registry

Providers are registered with configuration and credentials:

```
ProviderConfig:
  id: sora_hk | openai | vendor_x
  enabled: true|false
  priority: integer
  weight: integer (1-100)
  credentials: { ... }
  endpoint: string
```

Registry can be loaded from env, config file, or database.

Validation rules (admin):
- priority: 1-100
- weight: 1-100
- supported_durations: subset of [4, 8, 10, 12, 15, 25]
- supported_resolutions: horizontal | vertical

## 6. Scheduling and Routing

### Supported Strategies

1) Manual selection (front-end chooses provider)
2) Default provider (system config)
3) Primary/secondary failover
4) Weighted round-robin (load balance)
5) Cost-aware routing (lowest cost that meets capability)
6) Latency-aware routing (best recent p95)
7) Quota-aware routing (avoid providers with low quota)

### Decision Flow

1) Resolve provider list by strategy
2) Filter by capability and limit (duration, resolution, pro, image-to-video)
3) Resolve provider-specific model ID from logical model registry
4) Apply routing strategy
5) Attempt `create_task`
6) On error, apply fallback rules if enabled

Notes:
- Weighted routing uses `provider.weight` (default 1) to bias selection.
- Failover retries the next eligible provider only on retryable errors (rate limit, timeout, 5xx, quota, auth). Content/policy/validation errors do not fail over.
- If a run includes mixed durations/resolutions, selection must be evaluated per task (not per run).
- Run-level provider metadata may be empty when multiple providers are used.

## 7. Error Taxonomy and Mapping

Map provider-specific errors to internal codes:

- unauthorized
- forbidden
- validation_error
- content_policy
- rate_limited
- timeout
- quota_exceeded
- dependency_error
- server_error
- unknown_error
- download_failed
- no_provider

Providers should return raw error payloads for debugging in metadata.

Task metadata and API responses include:
- `error_code`: normalized error taxonomy
- `retryable`: whether failover/retry is allowed

Optional overrides (environment):
- `FAILOVER_RETRYABLE_TOKENS` (comma-separated)
- `FAILOVER_NON_RETRYABLE_TOKENS` (comma-separated)

## 8. Observability

- Per-provider metrics: success rate, error rate, latency, queue time
- Provider health checks and circuit breaker
- Audit logs for routing decisions (who/why/when)

## 9. Frontend Integration

### New Endpoints (Recommended)

- `GET /api/v1/providers`
- `GET /api/v1/providers/{id}`
- `GET /api/v1/providers/{id}/capabilities`

### Admin Configuration Endpoints (Internal)

- `GET /api/v1/admin/providers`
- `PATCH /api/v1/admin/providers/{id}`
- `GET /api/v1/admin/models`
- `PATCH /api/v1/admin/models/{id}`
- `PATCH /api/v1/admin/models/{id}/providers/{provider_id}`

Admin UI is the only place where provider/model mapping is edited. End-user UI only sees logical model IDs.

### Run Create Extension

```
RunCreate:
  model_id: string
  routing_strategy: manual|default|failover|weighted|cost|latency|quota
```

User-facing UI only exposes `model_id`. Provider routing remains backend-managed or admin-configured.

## 10. Migration Plan

1) Implement Provider interface and SoraHK adapter
2) Add registry and capability models
3) Refactor worker/service layer to call Provider
4) Add OpenAI adapter and one third-party adapter
5) Add routing strategy and fallback
6) Expose provider list to frontend
