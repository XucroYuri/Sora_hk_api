# Release Notes - v0.2-beta

**Release Date**: 2026-01-11  
**Status**: Beta  
**Scope**: Backend + Frontend + Docs  

---

## Highlights

- Web console + FastAPI backend shipped as the new primary workflow.
- Multi-provider routing (Sora.hk / OpenAI / AIHubMix) with logical model mapping.
- End-to-end run lifecycle validated with real provider download.

---

## What's New

### Backend
- FastAPI API set for storyboards, segments, runs, tasks, providers, models.
- Provider routing with failover/weighted strategy.
- Task retry and metadata download endpoints.
- Client event ingestion endpoint (`/client-events`).

### Frontend
- New React/Vite admin console integrated with backend APIs.
- Storyboard upload/edit, run creation, task tracking, result download.
- Admin panels for provider/model enablement.
- i18n baseline (zh-CN / en-US).

### Documentation
- OpenAPI draft updated (`docs/openapi_draft.yaml`).
- Frontend functional spec and integration guides expanded.
- Acceptance logs updated with real provider download validation.
- Delivery documentation added (template + current release).

---

## Breaking Changes

- None declared for this beta release.

---

## Migration Notes

- Use `.env.example` to configure provider keys.
- If backend auth is enabled, set `VITE_AUTH_TOKEN` for frontend.

---

## Known Issues / Gaps

- i18n coverage is incomplete (hard-coded strings exist).
- Admin console lacks priority/weight/mapping edits.
- No persistence layer (in-memory only).
- No observability dashboard.
- Tailwind uses CDN; offline deployments need local build.

---

## Validation

- Real provider download verified (see `docs/backend_integration_acceptance_actual.md`).

---

## 中文摘要

- Web 控制台 + FastAPI 后端成为主要工作流，CLI 仍可用。
- 多 Provider 路由已完成，真实下载验证通过。
- i18n、权限、持久化与可观测性仍需补齐，详见交付清单。

---

## GitHub Release Notes (Copy/Paste)

### CineFlow v0.2-beta

**Highlights**
- Web console + FastAPI backend shipped as the primary workflow
- Multi-provider routing (Sora.hk / OpenAI / AIHubMix) with logical models
- Real provider download verified

**New**
- Storyboard/run/task/provider/model APIs (FastAPI)
- React/Vite admin console wired to backend APIs
- `/client-events` ingestion endpoint
- OpenAPI draft + acceptance records updated

**Known Gaps**
- i18n coverage incomplete
- Admin console lacks priority/weight/mapping edits
- In-memory storage only (no persistence yet)
- No observability dashboard

**Docs**
- `docs/release_delivery_current.md`
- `docs/backend_integration_acceptance_actual.md`
- `docs/openapi_draft.yaml`
