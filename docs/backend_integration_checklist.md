# 后端最小闭环接口联调清单

**版本**: v0.1  
**适用范围**: 前后端联调 / 最小闭环验收  

---

## 0. 范围

- 覆盖最小闭环：导入 -> 编辑 -> 配置 -> 运行 -> 监控 -> 结果
- 不覆盖：管理后台、复杂权限、多租户与计费

## 1. 环境准备

- Base URL：`/api/v1`
- 认证：未设置 `AUTH_TOKEN` 时可匿名；设置后需 `Authorization: Bearer <token>`
- 仅联调流程可用 `dry_run=true`（不触发真实调用、无成本）
- 真实生成需配置 Provider Key（Sora.hk / OpenAI / AIHubMix）并确保网络可用
- 上传 Storyboard 使用 `multipart/form-data`，字段名固定为 `file`

## 2. 联调步骤（Happy Path）

1) **上传 Storyboard**  
接口：`POST /api/v1/storyboards`（multipart file）  
期望：201 + `StoryboardSummary(id, name, created_at, segment_count)`

2) **查询 Storyboards 列表**  
接口：`GET /api/v1/storyboards`  
期望：列表包含刚上传的 `id`

3) **拉取 Segments**  
接口：`GET /api/v1/storyboards/{id}/segments`  
期望：Segment 列表包含 `segment_index/duration_seconds/resolution/is_pro`

4) **编辑 Segment**  
接口：`PATCH /api/v1/segments/{segment_id}`  
期望：返回更新后的 `SegmentOut`

5) **查询逻辑模型**  
接口：`GET /api/v1/models?enabled=true`  
期望：至少包含 `sora2` / `sora2pro`

6) **创建 Run**  
接口：`POST /api/v1/runs`  
建议参数：`dry_run=true`、`gen_count=1`、`range=all`  
期望：`RunOut(id, status=queued/running)`

7) **轮询 Run 状态**  
接口：`GET /api/v1/runs/{id}`  
期望：`status` 最终 `completed`（dry_run）或 `failed`

8) **获取 Tasks 列表**  
接口：`GET /api/v1/runs/{id}/tasks?sort=segment_index&order=asc`  
期望：每条 task 含 `status` / `metadata_url`

9) **Task 详情**  
接口：`GET /api/v1/tasks/{task_id}`  
期望：失败任务包含 `error_code` / `retryable`

10) **下载 Metadata**  
接口：`GET /api/v1/tasks/{task_id}/metadata`  
期望：JSON 返回，失败任务含 `error_code` / `retryable`

11) **下载视频**  
接口：`GET /api/v1/tasks/{task_id}/download`  
期望：成功时文件或 302；dry_run 可能 404

12) **失败重试（可选）**  
接口：`POST /api/v1/tasks/{task_id}/retry`  
期望：202 + 任务状态回 `running`，随后 `/runs/{id}` 统计更新

## 2.1 请求/响应示例（精简）

**上传 Storyboard**  
`POST /api/v1/storyboards`（multipart）  
示例响应:
```json
{
  "id": "sb_123",
  "name": "storyboard_demo.json",
  "created_at": "2026-01-02T10:10:10Z",
  "segment_count": 2
}
```

**查询 Storyboards 列表**  
`GET /api/v1/storyboards?page=1&page_size=20&sort=created_at&order=desc&name=demo`  
示例响应:
```json
{
  "items": [
    {
      "id": "sb_123",
      "name": "storyboard_demo.json",
      "created_at": "2026-01-02T10:10:10Z",
      "segment_count": 2
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

**获取 Segments**  
`GET /api/v1/storyboards/sb_123/segments?page=1&page_size=20`  
示例响应:
```json
{
  "items": [
    {
      "id": "seg_001",
      "segment_index": 1,
      "prompt_text": "A futuristic city skyline at night with neon lights reflecting on the river. Cyberpunk style.",
      "image_url": null,
      "asset": {
        "characters": [],
        "scene": "Future City",
        "props": []
      },
      "is_pro": false,
      "duration_seconds": 10,
      "resolution": "horizontal",
      "director_intent": "Establishing shot."
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2
}
```

**更新 Segment**  
`PATCH /api/v1/segments/seg_001`  
请求:
```json
{
  "prompt_text": "City sunrise, wide shot",
  "duration_seconds": 12,
  "resolution": "horizontal",
  "is_pro": false
}
```
示例响应:
```json
{
  "id": "seg_001",
  "segment_index": 1,
  "prompt_text": "City sunrise, wide shot",
  "image_url": null,
  "asset": { "characters": [], "scene": null, "props": [] },
  "is_pro": false,
  "duration_seconds": 12,
  "resolution": "horizontal",
  "director_intent": null
}
```

**创建 Run**  
`POST /api/v1/runs`  
请求:
```json
{
  "storyboard_id": "sb_123",
  "model_id": "sora2",
  "routing_strategy": "default",
  "gen_count": 1,
  "concurrency": 3,
  "range": "all",
  "output_mode": "centralized",
  "output_path": null,
  "dry_run": true,
  "force": false
}
```
示例响应:
```json
{
  "id": "run_123",
  "status": "running",
  "total_tasks": 2,
  "completed": 0,
  "failed": 0,
  "download_failed": 0,
  "created_at": "2026-01-02T10:12:10Z"
}
```

**获取 Run 详情**  
`GET /api/v1/runs/run_123`  
示例响应:
```json
{
  "id": "run_123",
  "status": "completed",
  "total_tasks": 2,
  "completed": 2,
  "failed": 0,
  "download_failed": 0,
  "created_at": "2026-01-02T10:12:10Z"
}
```

**获取 Tasks 列表**  
`GET /api/v1/runs/run_123/tasks?sort=segment_index&order=asc`  
示例响应:
```json
{
  "items": [
    {
      "id": "task_001",
      "status": "completed",
      "video_url": null,
      "metadata_url": "/api/v1/tasks/task_001/metadata",
      "full_prompt": null,
      "error_msg": null,
      "error_code": null,
      "retryable": null,
      "segment_index": 1
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2
}
```

**Tasks 过滤示例**  
`GET /api/v1/runs/run_123/tasks?status=failed&retryable=true`  
示例响应:
```json
{
  "items": [
    {
      "id": "task_002",
      "status": "failed",
      "video_url": null,
      "metadata_url": "/api/v1/tasks/task_002/metadata",
      "full_prompt": null,
      "error_msg": "Rate limit reached",
      "error_code": "rate_limited",
      "retryable": true,
      "segment_index": 2
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

**Task 详情（失败示例）**  
`GET /api/v1/tasks/task_002`  
示例响应:
```json
{
  "id": "task_002",
  "status": "failed",
  "video_url": null,
  "metadata_url": "/api/v1/tasks/task_002/metadata",
  "full_prompt": null,
  "error_msg": "Rate limit reached",
  "error_code": "rate_limited",
  "retryable": true,
  "segment_index": 2
}
```

**失败重试**  
`POST /api/v1/tasks/task_002/retry`  
备注：状态可能为 `queued` 或 `running`（取决于异步线程调度）  
示例响应:
```json
{
  "id": "task_002",
  "status": "running",
  "video_url": null,
  "metadata_url": "/api/v1/tasks/task_002/metadata",
  "full_prompt": null,
  "error_msg": null,
  "error_code": null,
  "retryable": null,
  "segment_index": 2
}
```

**错误响应示例（认证失败）**  
401:
```json
{
  "code": "unauthorized",
  "message": "Authentication required"
}
```

**错误响应示例（Schema 校验）**  
400:
```json
{
  "code": "schema_error",
  "message": "Invalid storyboard schema",
  "details": {
    "errors": [
      {
        "loc": ["segments", 0, "prompt_text"],
        "msg": "Prompt text cannot be empty.",
        "type": "value_error"
      }
    ]
  }
}
```

## 3. 过滤与排序检查

- `/api/v1/runs?status=failed`
- `/api/v1/runs/{id}/tasks?status=failed&retryable=true`
- `/api/v1/runs/{id}/tasks?error_code=rate_limited`
- `page/page_size` + `sort/order`

## 4. 错误处理检查

- 401：未携带/错误 token
- 404：无效 storyboard/segment/task id
- 400：非法 duration/resolution 或 schema 不合法
- 失败任务需返回 `error_code` / `retryable`

## 5. 结果验收标准

- 能从上传 storyboard 到 run 完成（至少 dry_run 闭环）
- 任务列表可筛选、可查看详情、可拉取 metadata
- 失败任务错误码清晰，可映射前端提示
- 验收记录模板参考 `docs/backend_integration_acceptance_template.md`
