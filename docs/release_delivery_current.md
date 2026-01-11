# 版本交付说明（当前迭代）

| 项目 | 内容 |
| --- | --- |
| 版本号 | v0.2-beta |
| 交付日期 | 2026-01-11 |
| 负责人 | 自动化记录 |
| 交付范围 | 后端多 Provider + 前端控制台 + API 对接 + 验收文档 |
| 目标环境 | 本地/内网 |
| 影响面 | 前端与后端整体升级 |
| Release Notes | `docs/release_notes_v0.2-beta.md` |

---

## 1. 本次交付范围
- FastAPI 后端 API 体系与多 Provider 路由（Sora.hk/OpenAI/AIHubMix）
- React/Vite 控制台替换并完成真实 API 对接
- OpenAPI 草案与验收文档补全
- 前端功能规格/交付规范补强

## 2. 功能变更清单
- 多 Provider 逻辑模型映射与路由策略（default/failover/weighted）
- 管理后台接口（Provider/Model 配置）
- 任务重试与下载的闭环流程
- `/client-events` 异常上报接口（后端可接收）
- 前端控制台：分镜、运行、结果、设置页面全面对接

## 3. 破坏性变更
- 无明确破坏性变更（新增 Web 控制台与 API 接口）

## 4. 配置与依赖变更
- 新增/强调环境变量：`OPENAI_API_KEY`、`AIHUBMIX_API_KEY`、`AUTH_TOKEN`
- 前端新增 `VITE_API_BASE`、`VITE_AUTH_TOKEN`

## 5. 数据变更与迁移
- 当前仍为内存存储，无迁移需求（生产化阶段需引入数据库）

## 6. 验证与测试
- 最小闭环联调：上传 → 编辑 → 运行 → 重试 → 元数据/视频下载
- 真实 Provider 下载验证：通过（详见 `docs/backend_integration_acceptance_actual.md`）
- OpenAPI 草案对齐完成：`docs/openapi_draft.yaml`

## 7. 已知问题与风险
- i18n 未完全覆盖（存在硬编码文案）
- 管理后台能力不完整（缺少 priority/weight/mapping 编辑）
- 认证体验不足（需前端登录/Token 管理入口）
- 数据持久化与可观测性不足（仍为内存）
- Tailwind 使用 CDN，离线部署需调整

## 8. 回滚策略
- 回滚至上一标签版本；临时使用 Legacy CLI（`main.py`）继续生产

## 9. 文档更新
- README/README_zh：新版 Web 控制台与后端说明
- OpenAPI 草案、功能规格、验收记录

## 10. 验收结论
- 交付结论：通过（Beta 阶段）
- 交付备注：进入下一阶段需补齐 i18n、后台管理、持久化、权限与可观测性
