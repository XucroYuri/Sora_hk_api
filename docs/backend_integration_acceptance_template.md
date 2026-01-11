# 后端联调验收记录模板

**版本**: v0.1  
**目标**: 记录最小闭环联调结果，支持回溯与复测  

---

## 1. 基本信息

- 项目名称：
- 联调版本/分支：
- Base URL：
- 认证方式：`Bearer` / `None`
- 执行人：
- 执行日期：
- 环境备注（如本地/测试/预发布）：

## 2. 依赖配置确认

- `AUTH_TOKEN`：已设置 / 未设置
- Provider Key：Sora.hk / OpenAI / AIHubMix（是否已配置）
- 是否使用 `dry_run`：是 / 否
- 测试数据（Storyboard 文件名）：

## 3. 联调检查记录

| 步骤 | 接口 | 期望结果 | 实际结果 | 结论(PASS/FAIL) | 备注 |
| --- | --- | --- | --- | --- | --- |
| 1 | POST /api/v1/storyboards | 201 + 返回 id |  |  |  |
| 2 | GET /api/v1/storyboards | 列表含新 id |  |  |  |
| 3 | GET /api/v1/storyboards/{id}/segments | segments 可读 |  |  |  |
| 4 | PATCH /api/v1/segments/{segment_id} | 更新成功 |  |  |  |
| 5 | GET /api/v1/models?enabled=true | 含 sora2/sora2pro |  |  |  |
| 6 | POST /api/v1/runs | 返回 run_id |  |  |  |
| 7 | GET /api/v1/runs/{id} | 状态最终完成 |  |  |  |
| 8 | GET /api/v1/runs/{id}/tasks | tasks 可读 |  |  |  |
| 9 | GET /api/v1/tasks/{task_id} | error_code/详情可读 |  |  |  |
| 10 | GET /api/v1/tasks/{task_id}/metadata | 元数据可读 |  |  |  |
| 11 | GET /api/v1/tasks/{task_id}/download | 视频或 302 |  |  |  |
| 12 | POST /api/v1/tasks/{task_id}/retry | 进入运行态 |  |  |  |

## 4. 过滤/排序校验

| 接口 | 条件 | 期望结果 | 实际结果 | 结论(PASS/FAIL) | 备注 |
| --- | --- | --- | --- | --- | --- |
| /api/v1/runs | status=failed | 仅失败 |  |  |  |
| /api/v1/runs/{id}/tasks | status=failed&retryable=true | 仅可重试失败 |  |  |  |
| /api/v1/runs/{id}/tasks | error_code=rate_limited | 仅限流失败 |  |  |  |

## 5. 错误处理校验

- 401 未认证：PASS / FAIL
- 404 资源不存在：PASS / FAIL
- 400 参数校验错误：PASS / FAIL

## 6. 问题记录与待办

- 问题 1：
- 问题 2：
- 待办 1：
- 待办 2：
