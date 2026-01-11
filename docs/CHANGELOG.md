# Changelog

All notable changes to this project will be documented in this file.

## [0.2-beta] - 2026-01-11

### Added
- FastAPI backend with storyboard/run/task/provider/model APIs.
- Multi-provider routing (Sora.hk/OpenAI/AIHubMix) with logical models.
- React/Vite admin console wired to backend APIs.
- Client event ingestion endpoint (`/client-events`).
- Updated OpenAPI draft and acceptance records.
- Release delivery template and current delivery notes.

### Changed
- README updated to reflect Web console + API workflow.

### Known Issues
- i18n coverage incomplete.
- Admin console lacks advanced provider/model editing.
- In-memory storage only (no persistence).
