# 前端功能说明与后端通信规范

**版本**: v0.1  
**目标**: 面向前端设计/开发团队，说明需要实现的功能与后端通信方式  
**范围**: 不包含 UI 设计逻辑，仅描述功能与接口  

---

## 1. 基础通信

**Base URL**
- `/api/v1`

**认证**
- 若后端设置 `AUTH_TOKEN`，前端请求必须带 `Authorization: Bearer <token>`
- 401 返回需要提示用户并引导重新配置/登录

**错误结构**
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

**常见错误码**
- `unauthorized` (401)
- `not_found` (404)
- `schema_error` / `validation_error` (400)
- `server_error` (500)

---

## 2. Storyboard（分镜脚本）

### 2.1 上传
**接口**: `POST /storyboards`  
**请求**: `multipart/form-data`，字段名 `file`  
**响应**: `StoryboardSummary`
```json
{
  "id": "sb_123",
  "name": "storyboard_demo.json",
  "created_at": "2026-01-02T10:00:00Z",
  "segment_count": 2
}
```

### 2.2 列表
**接口**: `GET /storyboards`  
**Query**: `page, page_size, sort, order, name`  

### 2.3 详情
**接口**: `GET /storyboards/{id}`  

### 2.4 分镜列表
**接口**: `GET /storyboards/{id}/segments`  
**Query**: `page, page_size, sort, order, resolution, is_pro`  

---

## 3. Segment（分镜编辑）

### 3.1 修改分镜
**接口**: `PATCH /segments/{id}`  
**请求字段**: `prompt_text, director_intent, image_url, duration_seconds, resolution, is_pro, asset`  
**备注**:
- `duration_seconds` 可选值：`4/8/10/12/15/25`（且与 is_pro 组合满足后端校验）

### 3.2 上传起始帧
**接口**: `POST /segments/{id}/assets/start-image`  
**请求**: `multipart/form-data`，字段名 `file`  
**响应**:
```json
{ "image_url": "https://..." }
```

---

## 4. Models（逻辑模型）

### 4.1 模型列表
**接口**: `GET /models`  
**Query**: `page, page_size, sort, order, enabled`  
**用途**: 运行配置时提供逻辑模型下拉

### 4.2 模型详情
**接口**: `GET /models/{id}`

---

## 5. Runs（运行）

### 5.1 创建运行
**接口**: `POST /runs`  
**请求字段**:
```json
{
  "storyboard_id": "sb_123",
  "model_id": "sora2",
  "routing_strategy": "default",
  "gen_count": 1,
  "concurrency": 2,
  "range": "all",
  "output_mode": "centralized",
  "output_path": null,
  "dry_run": false,
  "force": false
}
```
**校验规则**:
- `model_id` 必须存在且启用
- `output_mode=custom` 时 `output_path` 必填

### 5.2 运行列表
**接口**: `GET /runs`  
**Query**: `page, page_size, sort, order, status`

### 5.3 运行详情
**接口**: `GET /runs/{id}`  
**用途**: 轮询运行状态与统计字段  

---

## 6. Tasks（任务）

### 6.1 任务列表（按 Run）
**接口**: `GET /runs/{id}/tasks`  
**Query**: `page, page_size, sort, order, status, segment_index, error_code, retryable`  
**用途**: 任务表格、筛选与排序

### 6.2 任务详情
**接口**: `GET /tasks/{id}`

### 6.3 任务重试
**接口**: `POST /tasks/{id}/retry`  
**返回**: 202，任务进入 `queued` 或 `running`  
**可用条件**: `status=failed` 且 `retryable=true`

### 6.4 下载
**接口**: `GET /tasks/{id}/download`  
**返回**: 视频文件或 302 跳转到远程 URL

### 6.5 元数据
**接口**: `GET /tasks/{id}/metadata`

---

## 7. Admin（服务商与模型映射）

> 用于内部配置与调度，普通用户不可见

### 7.1 服务商列表
**接口**: `GET /admin/providers`  
**Query**: `page, page_size, sort, order, enabled`

### 7.2 更新服务商配置
**接口**: `PATCH /admin/providers/{id}`  
**请求字段**: `enabled, priority, weight`

### 7.3 模型映射列表
**接口**: `GET /admin/models`

### 7.4 更新模型映射
**接口**: `PATCH /admin/models/{id}/providers/{provider_id}`  
**请求字段**:
```json
{ "provider_model_ids": ["sora-2", "web-sora-2"] }
```

---

## 8. 轮询与状态策略（功能要求）

- Run 状态需要轮询（默认 3-5 秒）  
- 任务列表随 Run 轮询刷新  
- 任务失败需展示 `error_code`、`retryable`，并提供重试入口  

---

## 9. i18n（功能要求）

- UI 文案必须通过 i18n 资源文件管理  
- 仅中文或仅英文，不允许中英混排  
- 必须支持 `zh-CN` 与 `en-US` 切换  

---

## 10. 字段级 JSON Schema（严格类型与校验）

> 仅展示关键字段与校验规则，便于前端对齐表单与校验提示。

### 10.1 Storyboard 文件结构
```json
{
  "type": "object",
  "required": ["segments"],
  "properties": {
    "segments": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/definitions/Segment" }
    },
    "metadata": { "type": "object" },
    "character_bible": { "type": "array" },
    "_comment": { "type": "string" }
  },
  "definitions": {
    "Segment": {
      "type": "object",
      "required": ["segment_index", "prompt_text", "duration_seconds", "resolution", "is_pro"],
      "properties": {
        "segment_index": { "type": "integer", "minimum": 1 },
        "prompt_text": { "type": "string", "minLength": 1 },
        "director_intent": { "type": "string", "nullable": true },
        "image_url": { "type": "string", "format": "uri", "nullable": true },
        "duration_seconds": { "type": "integer", "enum": [4, 8, 10, 12, 15, 25] },
        "resolution": { "type": "string", "enum": ["horizontal", "vertical"] },
        "is_pro": { "type": "boolean" },
        "asset": { "$ref": "#/definitions/Asset" }
      }
    },
    "Asset": {
      "type": "object",
      "required": ["characters", "props"],
      "properties": {
        "characters": {
          "type": "array",
          "items": { "$ref": "#/definitions/CharacterItem" }
        },
        "scene": { "type": "string", "nullable": true },
        "props": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "CharacterItem": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "id": { "type": "string", "nullable": true, "pattern": "^@?[a-zA-Z0-9_]+$" }
      }
    }
  }
}
```

### 10.2 SegmentUpdate（PATCH /segments/{id}）
```json
{
  "type": "object",
  "properties": {
    "prompt_text": { "type": "string", "minLength": 1 },
    "director_intent": { "type": "string", "nullable": true },
    "image_url": { "type": "string", "format": "uri", "nullable": true },
    "duration_seconds": { "type": "integer", "enum": [4, 8, 10, 12, 15, 25] },
    "resolution": { "type": "string", "enum": ["horizontal", "vertical"] },
    "is_pro": { "type": "boolean" },
    "asset": { "$ref": "#/definitions/Asset" }
  }
}
```

### 10.3 RunCreate（POST /runs）
```json
{
  "type": "object",
  "required": ["storyboard_id", "model_id", "gen_count", "concurrency", "range", "output_mode"],
  "properties": {
    "storyboard_id": { "type": "string", "minLength": 1 },
    "model_id": { "type": "string", "minLength": 1 },
    "routing_strategy": {
      "type": "string",
      "enum": ["manual", "default", "failover", "weighted", "cost", "latency", "quota"]
    },
    "gen_count": { "type": "integer", "minimum": 1, "maximum": 10 },
    "concurrency": { "type": "integer", "minimum": 1, "maximum": 50 },
    "range": { "type": "string", "minLength": 1 },
    "output_mode": { "type": "string", "enum": ["centralized", "in_place", "custom"] },
    "output_path": { "type": "string", "nullable": true },
    "dry_run": { "type": "boolean" },
    "force": { "type": "boolean" }
  }
}
```

### 10.4 Run（GET /runs/{id}）
```json
{
  "type": "object",
  "required": ["id", "status", "total_tasks", "created_at"],
  "properties": {
    "id": { "type": "string" },
    "status": { "type": "string", "enum": ["queued", "running", "completed", "failed", "download_failed"] },
    "total_tasks": { "type": "integer", "minimum": 0 },
    "completed": { "type": "integer", "minimum": 0 },
    "failed": { "type": "integer", "minimum": 0 },
    "download_failed": { "type": "integer", "minimum": 0 },
    "created_at": { "type": "string", "format": "date-time" }
  }
}
```

### 10.5 Task（GET /tasks/{id}）
```json
{
  "type": "object",
  "required": ["id", "status"],
  "properties": {
    "id": { "type": "string" },
    "status": { "type": "string", "enum": ["queued", "running", "completed", "failed", "download_failed"] },
    "segment_index": { "type": "integer", "minimum": 1, "nullable": true },
    "video_url": { "type": "string", "format": "uri", "nullable": true },
    "metadata_url": { "type": "string", "format": "uri", "nullable": true },
    "full_prompt": { "type": "string", "nullable": true },
    "error_msg": { "type": "string", "nullable": true },
    "error_code": {
      "type": "string",
      "nullable": true,
      "enum": [
        "content_policy",
        "validation_error",
        "rate_limited",
        "timeout",
        "quota_exceeded",
        "unauthorized",
        "forbidden",
        "dependency_error",
        "server_error",
        "unknown_error",
        "download_failed",
        "no_provider"
      ]
    },
    "retryable": { "type": "boolean", "nullable": true }
  }
}
```

### 10.6 ProviderUpdate（PATCH /admin/providers/{id}）
```json
{
  "type": "object",
  "properties": {
    "display_name": { "type": "string", "minLength": 1 },
    "enabled": { "type": "boolean" },
    "priority": { "type": "integer", "minimum": 1, "maximum": 100 },
    "weight": { "type": "integer", "minimum": 1, "maximum": 100 }
  }
}
```

### 10.7 ModelProviderMapUpdate（PATCH /admin/models/{id}/providers/{provider_id}）
```json
{
  "type": "object",
  "required": ["provider_model_ids"],
  "properties": {
    "provider_model_ids": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "minLength": 1 },
      "uniqueItems": true
    }
  }
}
```

### 10.8 PaginatedResponse（通用）
```json
{
  "type": "object",
  "required": ["items", "page", "page_size", "total"],
  "properties": {
    "items": { "type": "array" },
    "page": { "type": "integer", "minimum": 1 },
    "page_size": { "type": "integer", "minimum": 1, "maximum": 100 },
    "total": { "type": "integer", "minimum": 0 }
  }
}
```

---

## 11. 端点级 Request/Response Schema（摘要）

### 11.1 POST /storyboards
- Request: `multipart/form-data` with `file`
- Response: `StoryboardSummary`

### 11.2 GET /storyboards
- Response: `PaginatedResponse<StoryboardSummary>`

### 11.3 GET /storyboards/{id}/segments
- Response: `PaginatedResponse<Segment>`

### 11.4 PATCH /segments/{id}
- Request: `SegmentUpdate`
- Response: `Segment`

### 11.5 POST /runs
- Request: `RunCreate`
- Response: `Run`

### 11.6 GET /runs
- Response: `PaginatedResponse<Run>`

### 11.7 GET /runs/{id}/tasks
- Response: `PaginatedResponse<Task>`

### 11.8 GET /tasks/{id}
- Response: `Task`

### 11.9 POST /tasks/{id}/retry
- Response: `Task` (status becomes `queued` or `running`)

### 11.10 GET /tasks/{id}/download
- Response: `200 video/mp4` or `302 Location`

### 11.11 GET /tasks/{id}/metadata
- Response: `object` (任务元数据，包含 provider_id/provider_model_id/video_url 等)

### 11.12 Admin endpoints
- `GET /admin/providers` -> `PaginatedResponse<Provider>`
- `PATCH /admin/providers/{id}` -> `Provider`
- `GET /admin/models` -> `PaginatedResponse<ModelAdmin>`
- `PATCH /admin/models/{id}/providers/{provider_id}` -> `ModelAdmin`

---

## 12. 分页 / 过滤 / 排序示例（可直接调用）

### 12.1 Storyboards
```
GET /storyboards?page=1&page_size=20&sort=created_at&order=desc&name=demo
```

### 12.2 Segments
```
GET /storyboards/{id}/segments?page=1&page_size=20&sort=segment_index&order=asc&resolution=horizontal&is_pro=false
```

### 12.3 Runs
```
GET /runs?page=1&page_size=20&sort=created_at&order=desc&status=running
```

### 12.4 Tasks（按 Run）
```
GET /runs/{id}/tasks?page=1&page_size=20&sort=segment_index&order=asc&status=failed&retryable=true
GET /runs/{id}/tasks?page=1&page_size=20&sort=segment_index&order=asc&error_code=rate_limited
```

### 12.5 Models
```
GET /models?page=1&page_size=20&sort=id&order=asc&enabled=true
```

### 12.6 Admin Providers / Models
```
GET /admin/providers?page=1&page_size=20&sort=priority&order=asc&enabled=true
GET /admin/models?page=1&page_size=20&sort=id&order=asc&enabled=true
```

---

## 13. 端点完整请求/响应示例（精选）

### 13.1 POST /storyboards
Request: `multipart/form-data` with `file`

Response:
```json
{
  "id": "sb_123",
  "name": "storyboard_demo.json",
  "created_at": "2026-01-02T10:00:00Z",
  "segment_count": 2
}
```

### 13.2 GET /storyboards
```json
{
  "items": [
    {
      "id": "sb_123",
      "name": "storyboard_demo.json",
      "created_at": "2026-01-02T10:00:00Z",
      "segment_count": 2
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### 13.3 GET /storyboards/{id}/segments
```json
{
  "items": [
    {
      "id": "seg_001",
      "segment_index": 1,
      "prompt_text": "A futuristic city skyline at night with neon lights reflecting on the river. Cyberpunk style.",
      "director_intent": "Establishing shot.",
      "image_url": null,
      "duration_seconds": 10,
      "resolution": "horizontal",
      "is_pro": false,
      "asset": {
        "characters": [],
        "scene": "Future City",
        "props": []
      }
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2
}
```

### 13.4 PATCH /segments/{id}
Request:
```json
{
  "prompt_text": "Updated prompt for integration check.",
  "duration_seconds": 12,
  "resolution": "horizontal",
  "is_pro": false
}
```
Response:
```json
{
  "id": "seg_001",
  "segment_index": 1,
  "prompt_text": "Updated prompt for integration check.",
  "director_intent": "Establishing shot.",
  "image_url": null,
  "duration_seconds": 12,
  "resolution": "horizontal",
  "is_pro": false,
  "asset": {
    "characters": [],
    "scene": "Future City",
    "props": []
  }
}
```

### 13.5 POST /runs
Request:
```json
{
  "storyboard_id": "sb_123",
  "model_id": "sora2",
  "routing_strategy": "default",
  "gen_count": 1,
  "concurrency": 2,
  "range": "all",
  "output_mode": "centralized",
  "output_path": null,
  "dry_run": false,
  "force": false
}
```
Response:
```json
{
  "id": "run_123",
  "status": "running",
  "total_tasks": 2,
  "completed": 0,
  "failed": 0,
  "download_failed": 0,
  "created_at": "2026-01-02T10:10:00Z"
}
```

### 13.6 GET /runs/{id}
```json
{
  "id": "run_123",
  "status": "completed",
  "total_tasks": 2,
  "completed": 2,
  "failed": 0,
  "download_failed": 0,
  "created_at": "2026-01-02T10:10:00Z"
}
```

### 13.7 GET /runs/{id}/tasks
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

### 13.8 GET /tasks/{id}
```json
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
```

### 13.9 POST /tasks/{id}/retry
Response:
```json
{
  "id": "task_001",
  "status": "running",
  "video_url": null,
  "metadata_url": "/api/v1/tasks/task_001/metadata",
  "full_prompt": null,
  "error_msg": null,
  "error_code": null,
  "retryable": null,
  "segment_index": 1
}
```

### 13.10 GET /tasks/{id}/download
- `200 video/mp4` 或 `302 Location` 跳转到远程 URL

### 13.11 GET /tasks/{id}/metadata
```json
{
  "id": "task_001",
  "run_id": "run_123",
  "segment_id": "seg_001",
  "segment_index": 1,
  "version_index": 1,
  "output_dir": "backend/output/sb_123/Segment_1",
  "status": "completed",
  "video_url": null,
  "metadata_url": "/api/v1/tasks/task_001/metadata",
  "full_prompt": null,
  "error_msg": null,
  "error_code": null,
  "retryable": null,
  "provider_id": "sora_hk",
  "provider_model_id": "sora2"
}
```

### 13.12 GET /admin/providers
```json
{
  "items": [
    {
      "id": "sora_hk",
      "display_name": "Sora.hk",
      "enabled": true,
      "priority": 10,
      "weight": 1,
      "supports_image_to_video": true,
      "supported_durations": [10, 15, 25],
      "supported_resolutions": ["horizontal", "vertical"],
      "supports_pro": true
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### 13.13 PATCH /admin/providers/{id}
Request:
```json
{ "enabled": true, "priority": 5, "weight": 2 }
```
Response: `Provider`

### 13.14 GET /admin/models
```json
{
  "items": [
    {
      "id": "sora2",
      "display_name": "Sora2",
      "description": "Logical model for standard generation",
      "enabled": true,
      "provider_map": {
        "sora_hk": ["sora2"],
        "aihubmix": ["sora-2", "web-sora-2"]
      }
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### 13.15 PATCH /admin/models/{id}/providers/{provider_id}
Request:
```json
{ "provider_model_ids": ["sora-2", "web-sora-2"] }
```
Response: `ModelAdmin`

---

## 14. 前端状态机与页面状态（功能要求）

> 目的是统一“加载/空态/错误/完成”的交互行为，便于前端设计团队落地。

### 14.1 全局状态
- **idle**：未发起请求
- **loading**：请求中（禁用重复提交）
- **success**：请求成功并渲染
- **empty**：请求成功但无数据
- **error**：请求失败（展示错误码与说明）

### 14.2 连接设置
- **已配置**：保存 `Base URL` 与 `AUTH_TOKEN`，显示“已配置”
- **未配置**：提示填写；尝试请求时若 401 触发提示

### 14.3 Storyboard 上传
- **loading**：上传中，禁用按钮
- **success**：上传成功后自动刷新列表并选中该 storyboard
- **error**：显示 `schema_error` 或 `validation_error` 的字段路径

### 14.4 分镜编辑
- **empty**：未选择 storyboard / segment
- **loading**：加载 segments 或保存中
- **error**：字段校验失败时提示到对应字段
- **success**：保存成功后刷新列表

### 14.5 运行与任务
- **running**：Run 状态为 running 时启动轮询
- **completed/failed**：停止轮询，展示统计数据
- **tasks empty**：任务为空时提示“清除筛选/调整筛选”

### 14.6 Admin 配置
- **loading**：获取 providers/models 时显示加载态
- **success**：保存后刷新数据
- **error**：提示 `validation_error`（priority/weight/映射为空）

---

## 15. 与 OpenAPI 草案的差异说明（对齐建议）

> 以 `docs/openapi_draft.yaml` 为准补充说明。

| 项目 | 当前功能文档 | OpenAPI 草案 |
| --- | --- | --- |
| Provider 公共接口 | 未强制要求 | `/providers`、`/providers/{id}`、`/providers/{id}/capabilities` 可选 |
| Admin 模型更新 | 未强制要求 | `PATCH /admin/models/{id}` 支持更新 display_name/description/enabled |
| Provider 更新字段 | 仅说明 enabled/priority/weight | 可选字段包含 `supports_image_to_video`/`supported_durations`/`supported_resolutions`/`supports_pro` |
| 认证模式 | Bearer 为主 | 草案中也包含 Cookie 方案（可选） |

---

## 16. 字段校验规则与错误提示映射（建议）

### 16.1 前端输入校验（建议与后端一致）
- `storyboard_id` / `model_id`：必填，非空字符串
- `gen_count`：整数 1-10
- `concurrency`：整数 1-50
- `range`：必填字符串（如 `all` 或 `1-5,8`）
- `output_mode=custom` 时 `output_path` 必填
- `duration_seconds`：`4/8/10/12/15/25`（且 `is_pro=false` 时不得选择 `25`）
- `resolution`：`horizontal` / `vertical`
- `prompt_text`：非空
- `asset.characters[*].id`：`^@?[a-zA-Z0-9_]+$`
- 管理后台：
  - `priority` / `weight`：整数 `1-100`
  - `provider_model_ids`：非空、去重

### 16.2 错误提示映射（前端展示）
| error_code | 建议提示 |
| --- | --- |
| content_policy | 提示词包含违规内容，建议调整 |
| validation_error | 参数校验错误，检查分镜/配置 |
| rate_limited | 服务商限流，建议稍后重试 |
| timeout | 任务超时，建议降低并发或重试 |
| quota_exceeded | 额度不足，需更换服务商或充值 |
| unauthorized | 未授权，检查 token 或 API Key |
| forbidden | 权限不足，联系管理员 |
| dependency_error | 外部服务异常，建议稍后重试 |
| server_error | 服务异常，请稍后重试 |
| unknown_error | 未知错误，查看详情并重试 |
| download_failed | 视频生成成功但下载失败，可手动下载或重试 |
| no_provider | 无可用服务商，请调整参数或启用服务商 |

---

## 17. 轮询与重试策略（建议）

### 17.1 Run 轮询
- 默认 3-5 秒轮询 `/runs/{id}` 与 `/runs/{id}/tasks`
- `status != running` 时停止轮询
- 若接口连续失败（如 3 次），提示用户网络异常并暂停

### 17.2 Task 重试
- 仅当 `status=failed` 且 `retryable=true` 时展示重试入口
- 重试后任务可变为 `queued` 或 `running`
- 若当前开启“失败筛选”，重试后任务可能从列表消失，需提示“可清除筛选查看全部”

### 17.3 下载
- `GET /tasks/{id}/download` 可能返回 302 跳转
- 前端若需要显示直链，可优先使用 `video_url`

---

## 18. 管理后台安全与权限（建议）

- 管理后台仅供内部使用，生产环境建议通过独立域名或 VPN 访问
- 不在前端页面明文展示 Provider Key
- 建议开启 `AUTH_TOKEN` 并限制 Admin 接口访问
- 建议为 Admin 页面增加“二次确认”或“保存提示”

---

## 19. 前端日志与埋点建议（可选）

**目的**: 便于定位失败、统计成功率、分析耗时

建议记录的事件：
- `storyboard_upload`：上传开始/成功/失败（含错误码）
- `segment_update`：保存成功/失败（含字段与错误码）
- `run_create`：创建运行成功/失败（含 model_id、routing_strategy）
- `task_retry`：重试成功/失败（含 error_code）
- `download_video`：下载成功/失败（含耗时与大小）

建议记录的字段：
- `request_id`（若后端提供）
- `error_code` / `status`
- `latency_ms`
- `provider_id` / `provider_model_id`（从 metadata 获取）

---

## 20. 前端权限分级建议

**角色划分**
- **普通用户**：只能上传 storyboard、编辑分镜、创建运行、查看任务结果
- **管理员**：可访问 Admin 接口与管理后台页面

**实现建议**
- 前端根据登录态或配置标记隐藏 Admin 页面入口
- 后端以 `AUTH_TOKEN` 或更严格方式控制 Admin 权限

---

## 21. 统一错误提示组件规范（建议）

**使用场景**
- **Toast**：短暂提示（网络错误、临时失败、轻提示）
- **Banner**：阻断级错误（权限/额度不足）
- **Modal**：破坏性操作确认（清除筛选、批量操作）
- **Inline Field Error**：表单字段校验错误（schema_error / validation_error）

**展示优先级**
1) Banner  
2) Field Error  
3) Toast  
4) Empty State

---

## 22. 前端数据缓存策略（建议）

- **短缓存**：Storyboards/Models/Providers 建议 1-3 分钟内复用，避免重复请求
- **强制刷新**：用户点击 Refresh 时必须绕过缓存
- **本地状态**：选中项（storyboard/run/task）可存于内存，不需持久化
- **轮询一致性**：Run/Tasks 轮询结果优先覆盖缓存

---

## 23. 大文件上传与失败重试交互（建议）

**上传流程**
- 显示进度（若浏览器支持上传进度）
- 上传中禁用按钮，防止重复提交
- 上传失败提示错误码 + 重试按钮

**重试策略**
- 网络错误：允许用户点击“重试上传”
- schema_error：提示具体字段错误（不自动重试）

**用户引导**
- 上传成功后自动选中该 storyboard 并提示下一步（编辑/运行）

---

## 24. 任务详情信息层级（建议）

**优先级 1：关键信息**
- 任务状态（status）
- 关联分镜（segment_index / storyboard_id）
- 生成结果（video_url / 下载按钮）

**优先级 2：可诊断信息**
- error_code / retryable
- error_msg
- provider_id / provider_model_id（如 metadata 可用）

**优先级 3：可复现信息**
- full_prompt
- metadata_url（下载元数据）

---

## 25. 下载失败的 UI 引导文案（示例）

当 `download_failed` 或下载接口返回 404 时：
- 中文：`视频已生成，但下载失败。请稍后重试或使用直链下载。`
- 英文：`Video generated, but download failed. Please retry or use the direct link.`

当 `video_url` 为空且仍未生成：
- 中文：`视频尚未生成完成，请稍后刷新。`
- 英文：`Video is not ready. Please refresh later.`

---

## 26. 多语言翻译验收清单（建议）

- 中英文文案严格分离，不允许同句混排  
- 所有 UI 文案通过 i18n 资源文件管理  
- 新增 key 必须双语对齐（zh-CN / en-US）  
- 切换语言后全站文本即时更新  
- 日期/数字格式使用本地化格式（Intl）  
- 超长中英文不会造成布局溢出  
- 缺失 key 在开发环境可见、生产环境回退 zh-CN  

---

## 27. 状态枚举与展示要点

**Run.status**
- `queued` / `running` / `completed` / `failed` / `download_failed`

**Task.status**
- `queued` / `running` / `completed` / `failed` / `download_failed`

**Task.error_code**
- `content_policy` / `validation_error` / `rate_limited` / `timeout` / `quota_exceeded`
- `unauthorized` / `forbidden` / `dependency_error` / `server_error`
- `unknown_error` / `download_failed` / `no_provider`

**Task.retryable**
- `true`：显示“重试”入口
- `false` 或 `null`：不可重试

---

## 28. 空态文案（建议）

- Storyboards 为空：`暂无分镜脚本，请先上传` / `No storyboards. Upload first.`
- Segments 为空：`暂无分镜，请选择脚本` / `No segments. Select a storyboard.`
- Runs 为空：`暂无运行记录` / `No runs.`
- Tasks 为空（无筛选）：`暂无任务` / `No tasks.`
- Tasks 为空（有筛选）：`当前筛选无任务，可清除筛选` / `No tasks match filters. Clear filters.`
- Admin Providers 为空：`暂无服务商配置` / `No provider settings.`
- Admin Models 为空：`暂无模型映射` / `No model mappings.`

---

## 29. 任务详情页动作（功能要求）

- **下载视频**：调用 `GET /tasks/{id}/download` 或使用 `video_url`
- **下载元数据**：调用 `GET /tasks/{id}/metadata`
- **复制提示词**：复制 `full_prompt`（若存在）
- **重试**：仅当 `retryable=true` 且 `status=failed`

---

## 30. 数据格式与展示（建议）

- 日期/时间：使用本地化格式（Intl），显示 `created_at`
- 分辨率：`horizontal/vertical` 显示为“横/竖”
- 时长：秒级显示，如 `10s`
- 布尔值：统一用 `是/否` 或 `Yes/No`

---

## 31. 分页/排序体验（建议）

- 列表默认排序：storyboards 按 `created_at desc`，runs 按 `created_at desc`
- tasks 默认按 `segment_index asc`
- 切换分页时保持当前筛选条件

---

## 32. 性能与交互（建议）

- 列表超过 200 条时建议分页或虚拟滚动
- 输入型筛选建议 debounce（300-500ms）
- 轮询期间避免全量刷新 UI，仅更新必要区域

---

## 33. 逻辑模型与 Provider 的 UI 约束

- 用户侧只选择**逻辑模型**（`/models`）
- Provider 选择与路由策略由后台/管理员配置
- Admin 页面用于调整 provider 启用/优先级/权重/映射

---

## 34. 下载与分享交互（建议）

- **下载入口**：任务详情页提供“下载视频”按钮（调用 `/tasks/{id}/download`）
- **直链显示**：若 `video_url` 可用，提供“复制直链”
- **失败处理**：下载失败时提示 `download_failed` 文案，并提供重试/直链

---

## 35. 任务历史导出（可选）

- 导出格式：CSV 或 JSON
- 导出字段：`task_id, status, error_code, retryable, segment_index, created_at`
- 使用场景：离线汇总、供应商对账、异常回溯

---

## 36. 管理操作审计（可选）

- 建议记录 Admin 操作历史（时间/操作者/变更前后）
- UI 可在 Admin 页面提供最近变更列表（如后端支持）

---

## 37. 运行配置校验交互（建议）

- `gen_count` / `concurrency` 非法时立即提示（1-10 / 1-50）
- `output_mode=custom` 且缺失 `output_path` 时阻止提交
- `range` 输入无效（如空、全非法）时提示并阻止提交
- `model_id` 未选择时提示

---

## 38. 失败任务批量重试（可选）

- 前端可提供“批量重试”入口（仅限 `retryable=true`）
- 支持筛选后批量重试（如当前筛选条件）
- 失败重试可能导致任务列表消失，需提示“清除筛选查看全部”

---

## 39. 多语言翻译流程建议

- 新增 key 时必须同时补齐 zh-CN / en-US
- 统一 Key 命名规范（如 `action.*`, `label.*`, `msg.*`)
- 发布前对双语进行抽样审校

---

## 40. 错误码与用户动作推荐（建议）

| error_code | 用户动作 |
| --- | --- |
| content_policy | 修改提示词后重试 |
| validation_error | 修正表单字段 |
| rate_limited | 等待后重试或降低并发 |
| timeout | 降低并发或重试 |
| quota_exceeded | 切换服务商或充值 |
| unauthorized | 重新配置 token / key |
| forbidden | 联系管理员 |
| dependency_error | 稍后重试 |
| server_error | 稍后重试或反馈 |
| unknown_error | 查看详情后重试 |
| download_failed | 点击重试下载 |
| no_provider | 启用服务商或调整参数 |

---

## 41. 任务状态可视化规范（建议）

- `queued`：灰色，显示“排队中”
- `running`：蓝色，显示“运行中”
- `completed`：绿色，显示“已完成”
- `failed`：红色，显示“失败”
- `download_failed`：橙色，显示“下载失败”

---

## 42. 多人协作与权限（可选）

- 普通用户仅可查看与编辑自身运行
- 管理员可查看所有运行与任务
- 若无用户体系，前端可隐藏协作入口

---

## 43. 数据导出/导入格式规范（建议）

**导出**
- CSV 字段：`task_id, status, error_code, retryable, segment_index, created_at`
- JSON 字段：同上，额外可包含 `video_url`

**导入**
- 仅支持 storyboard JSON
- 失败时返回 `schema_error` 并展示字段路径

---

## 44. 调度策略展示规则（建议）

- 用户侧仅展示逻辑模型选择（不展示 provider 列表）
- Admin 侧可展示：
  - 当前启用的 provider
  - priority 与 weight
  - 当前逻辑模型的映射列表

---

## 45. 权限异常处理流程（建议）

- 401：提示重新配置 token 或重新登录
- 403：提示无权限并隐藏 Admin 入口
- 404：提示资源不存在并引导返回列表

---

## 46. 自动重试策略（可选）

- 仅对 `retryable=true` 的任务提供“自动重试开关”
- 自动重试建议：
  - rate_limited / timeout：延迟 30-60 秒后重试
  - dependency_error / server_error：延迟 60 秒后重试
- 自动重试次数上限建议为 1-2 次

---

## 47. 通知与提醒（可选）

- 运行完成后可展示通知（toast/banner）
- 失败任务可提示“查看失败原因”
- 若浏览器支持，可选桌面通知

---

## 48. 移动端适配规则（建议）

- 核心功能需可用：上传、创建运行、查看任务
- 表格在移动端可折叠为卡片列表
- 侧栏可折叠成抽屉菜单

---

## 49. 可访问性与键盘导航（建议）

- 表单输入与按钮可通过 Tab 访问
- 重要按钮提供可识别的 aria-label
- 弹窗/提示支持 Esc 关闭
- 颜色对比度满足可读性

---

## 50. 性能指标与体验目标（建议）

- 首页首屏渲染 < 2s（本地或内网）
- 任务列表刷新 < 1s（不含生成耗时）
- 轮询请求失败率 < 5%

---

## 51. 审计导出格式（可选）

- CSV 字段：`time, operator, action, before, after`
- JSON 字段：同上，结构化字段便于筛选

---

## 52. 安全与隐私合规（建议）

- 不在前端保存或展示真实 Provider Key
- 仅保存 `AUTH_TOKEN`（必要时可选本地存储）
- 若为公网环境，建议开启 HTTPS

---

## 53. 缓存失效策略（建议）

- Storyboards/Models/Admin 数据超过 3 分钟需强制刷新
- 运行与任务状态优先以轮询数据为准

---

## 54. API 变更与回滚流程（建议）

- 前端版本发布前与后端确认 OpenAPI 变更
- 重要接口变更建议提供兼容期
- 回滚时保留旧接口 1-2 个版本

---

## 55. 用户引导与新手流程（建议）

- 首次进入提示填写 Base URL 与 Token
- 上传 storyboard 成功后提示“下一步：编辑分镜或创建运行”
- 未选择 run 时提示“请选择运行以查看任务”

---

## 56. 联调验收步骤（建议）

- 上传 storyboard → 选择分镜 → 创建 run → 轮询 → 查看任务 → 下载
- 失败时记录 `error_code` 与 `retryable`

---

## 57. 运行配置向导（可选）

- 按步骤引导填写：模型 → 范围 → 并发 → 输出模式 → dry_run/force
- 表单校验未通过时禁止下一步

---

## 58. 用户帮助与 FAQ（建议）

- 常见问题：
  - 为什么看不到任务？（未选择 run 或筛选条件限制）
  - 为什么无法重试？（retryable=false）
  - 为什么下载失败？（download_failed 或视频未生成）

---

## 59. 多 Provider 切换策略说明（建议）

- 用户侧只选择逻辑模型，不暴露 Provider
- Admin 侧可通过：
  - 启用/禁用 Provider
  - 调整 priority / weight
  - 更新 provider_model_ids 映射
- 若使用 `failover` 策略，失败会尝试备用 Provider

---

## 60. 任务批量操作规范（可选）

- 批量选择任务（仅当前 run）
- 批量重试：仅作用于 `retryable=true` 的失败任务
- 批量导出：按筛选条件导出

---

## 61. 任务生命周期图（文字版）

```
create -> queued -> running -> completed
                           \-> failed
completed -> download_failed
failed/download_failed --(retry creates new task)--> queued
```

说明：
- `create`：前端发起 RunCreate，后端生成任务并返回 task_id
- `queued`：任务已创建，等待执行
- `running`：已分配 Provider，正在生成
- `completed`：生成完成，可下载
- `failed`：生成失败（含 error_code / retryable）
- `download_failed`：生成成功但下载失败，可手动重试下载

状态与 UI 行为：
- `queued`：显示排队提示和排队时长
- `running`：显示进度条或“生成中”，可刷新/取消轮询
- `completed`：显示下载按钮与预览入口
- `failed`：展示错误码 + 可重试入口（若 retryable=true）
- `download_failed`：提示下载失败原因，引导重试或切换下载方式

前后端数据关联：
- `run_id` 关联多个任务（segment_index 体现分段顺序）
- `task_id` 级别重试会创建新任务，需在 UI 中标注“由任务 X 重试生成”

---

## 62. 异常上报机制（建议）

**目的**: 捕获前端异常与接口失败，便于排查与统计，形成可量化的质量指标

建议事件类型：
- `ui_error`：前端 JS 运行时异常 / 崩溃
- `api_error`：接口请求失败（4xx/5xx/timeout）
- `task_error`：任务失败或 download_failed
- `i18n_error`：缺少翻译 key、语言切换异常

建议上报字段（最小集合）：
- `event_id` / `event_type` / `severity`
- `timestamp` / `timezone` / `user_locale`
- `endpoint` / `method` / `status_code` / `latency_ms`
- `run_id` / `task_id` / `provider_id` / `model_id`
- `error_code` / `message` / `stack`（可截断）

推荐约束：
- 不上传敏感数据（API key、完整 prompt、视频内容）；prompt 可只上报长度或 hash
- 支持本地队列与退避重试（避免短时网络波动导致丢失）
- 采样/去重：相同错误 1 分钟内只上报一次，避免刷屏

建议触发点：
- API 请求失败或超时（4xx/5xx）
- 任务失败（status=failed / download_failed）
- 上传失败（schema_error / validation_error）
- i18n key 缺失或语言切换异常

可选实现：
- 若后端提供事件上报接口，则 POST 到 `/client-events`
- 未提供接口时：开发环境 `console.error` + 本地缓存

---

## 63. UI 状态与动作矩阵（建议）

**任务级状态矩阵**

| 状态 | 主操作 | 次操作 | UI 提示 |
| --- | --- | --- | --- |
| queued | 刷新状态 | 查看分镜详情 | 显示排队时长/提示稍后刷新 |
| running | 刷新状态 | 查看分镜详情 | 显示生成中与预计时长区间 |
| completed | 下载视频 | 查看详情/预览 | 显示完成时间与文件大小 |
| failed | 重试任务（仅 retryable=true） | 查看错误详情 | 展示 error_code + 解决建议 |
| download_failed | 重试下载 | 复制下载链接 | 提示下载失败原因与替代方式 |

**Run 级状态矩阵**

| 状态 | 主操作 | 次操作 | UI 提示 |
| --- | --- | --- | --- |
| running | 查看任务列表 | 刷新统计 | 显示进度（completed/total） |
| completed | 导出任务 | 查看失败列表 | 显示完成时间与失败数 |
| failed | 查看失败原因 | 导出日志 | 显示失败比例与建议重试 |

---

## 64. 错误码分级与 UI 处理规则（建议）

| 级别 | error_code | UI 处理规则 | 允许动作 |
| --- | --- | --- | --- |
| 阻断 | unauthorized, forbidden | 顶部 Banner/弹窗，提示登录或权限不足 | 禁止提交 Run |
| 阻断 | quota_exceeded | Banner + 联系方式/升级说明 | 允许编辑配置，不允许提交 |
| 表单 | validation_error, schema_error | 表单字段内联错误 | 仅允许修正后再次提交 |
| 内容 | content_policy | 弹窗/侧栏解释违规原因 | 允许编辑 prompt 再提交 |
| 可重试 | rate_limited, timeout, dependency_error | Toast + “重试”按钮 | 支持重试任务 |
| 服务端 | server_error, unknown_error | Banner + 重试入口 | 支持重试或稍后再试 |
| 下载 | download_failed | 下载区块内提示 | 允许重试下载 |
| 配置 | no_provider | Banner + 引导联系管理员 | 禁止提交 Run |

补充说明：
- 同时存在 `retryable=true` 时，UI 应优先展示“重试任务”
- 同一任务连续失败 3 次后提示“建议更换模型或稍后再试”
