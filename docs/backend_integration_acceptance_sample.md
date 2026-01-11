# 后端联调验收记录样例

**版本**: v0.1  
**目标**: 示例记录，仅用于对照填写  

---

## 1. 基本信息

- 项目名称：CineFlow
- 联调版本/分支：feature/provider-routing
- Base URL：http://localhost:8000
- 认证方式：Bearer
- 执行人：示例
- 执行日期：2026-01-05
- 环境备注：本地开发环境
- 请求头示例：`Authorization: Bearer ${AUTH_TOKEN}`

## 2. 依赖配置确认

- `AUTH_TOKEN`：已设置
- Provider Key：Sora.hk / OpenAI / AIHubMix（本次仅 dry_run）
- 是否使用 `dry_run`：是
- 测试数据（Storyboard 文件名）：storyboard_demo.json
- 关键参数：`gen_count=1`、`range=all`、`concurrency=3`

## 3. 联调检查记录

| 步骤 | 接口 | 期望结果 | 实际结果 | 结论(PASS/FAIL) | 备注 |
| --- | --- | --- | --- | --- | --- |
| 1 | POST /api/v1/storyboards | 201 + 返回 id | 201 + sb_6f2a | PASS |  |
| 2 | GET /api/v1/storyboards?page=1&page_size=20&sort=created_at&order=desc | 列表含新 id | 列表含 sb_6f2a | PASS |  |
| 3 | GET /api/v1/storyboards/{id}/segments | segments 可读 | 2 条 segments | PASS |  |
| 4 | PATCH /api/v1/segments/{segment_id} | 更新成功 | 200 + prompt 更新 | PASS |  |
| 5 | GET /api/v1/models?enabled=true | 含 sora2/sora2pro | 返回 sora2/sora2pro | PASS |  |
| 6 | POST /api/v1/runs | 返回 run_id | 201 + run_9c31 | PASS | dry_run |
| 7 | GET /api/v1/runs/{id} | 状态最终完成 | completed | PASS | dry_run |
| 8 | GET /api/v1/runs/{id}/tasks?sort=segment_index&order=asc | tasks 可读 | 返回 2 条 tasks | PASS |  |
| 9 | GET /api/v1/tasks/{task_id} | error_code/详情可读 | error_code 为 null | PASS | dry_run |
| 10 | GET /api/v1/tasks/{task_id}/metadata | 元数据可读 | JSON 返回 | PASS |  |
| 11 | GET /api/v1/tasks/{task_id}/download | 视频或 302 | 404 | PASS | dry_run 预期 |
| 12 | POST /api/v1/tasks/{task_id}/retry | 进入运行态 | running | PASS |  |

## 4. 过滤/排序校验

| 接口 | 条件 | 期望结果 | 实际结果 | 结论(PASS/FAIL) | 备注 |
| --- | --- | --- | --- | --- | --- |
| /api/v1/runs | status=failed | 仅失败 | 0 条 | PASS | dry_run |
| /api/v1/runs/{id}/tasks | status=failed&retryable=true | 仅可重试失败 | 0 条 | PASS |  |
| /api/v1/runs/{id}/tasks | error_code=rate_limited | 仅限流失败 | 0 条 | PASS |  |

## 5. 错误处理校验

- 401 未认证：PASS（code=unauthorized）
- 404 资源不存在：PASS（code=not_found）
- 400 参数校验错误：PASS（code=schema_error 或 validation_error）

## 6. 问题记录与待办

- 问题 1：无
- 问题 2：无
- 待办 1：若需真机生成，请补齐 Provider Key
- 待办 2：前端联调完成后补充截图存档
