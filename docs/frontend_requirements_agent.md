# CineFlow 前端需求说明（开发 Agent 版）

**版本**: v0.1  
**日期**: 2026-01-02  
**目标读者**: 前端项目开发 Agent  

---

## 1. 目标与边界

**目标**：实现完整的前端业务闭环（导入 -> 编辑 -> 配置 -> 运行 -> 监控 -> 结果）。
**边界**：不限定技术栈，不包含后端实现。只需对接 API 契约并完成 UI/交互。

**UI 规范**：
- 默认浅色主题
- 现代、专业、企业级视觉
- 符合 Google 标准的专业 UI 规范（Material Design 3 的色彩、排版、组件规范）
- 界面语言与 i18n：中文为主、英文为辅；必须严格区分中英文，不允许中英混排；支持中/英文切换；所有文案通过 i18n 资源文件管理

### 1.1 i18n 交付要求

- 默认语言：`zh-CN`
- 次语言：`en-US`
- 语言切换入口：全局 Header 右上角（或用户菜单内）
- 文案必须通过资源文件管理，不允许硬编码
- 中英文内容必须严格分离（同一字符串内不得混排）

**资源文件结构示例**
- `locales/zh-CN.json`
- `locales/en-US.json`

**示例键值**
`zh-CN.json`
```json
{
  "app.title": "CineFlow 控制台",
  "nav.dashboard": "概览",
  "action.submit": "提交"
}
```

`en-US.json`
```json
{
  "app.title": "CineFlow Console",
  "nav.dashboard": "Dashboard",
  "action.submit": "Submit"
}
```

### 1.2 i18n Key 命名规范

- 分层命名：`module.section.element`（例：`nav.dashboard`）
- 动作前缀：`action.*`
- 状态前缀：`status.*`
- 提示前缀：`msg.*`
- 错误前缀：`error.*`
- 表单前缀：`form.*`
- 禁止复用不同语义的 key
- 禁止在 key 中使用中文或空格

### 1.3 i18n 运行规范

- 占位符使用命名形式（例：`{count}`）
- 日期/数字必须本地化格式化（Intl 或框架内置）
- 缺失 key：开发环境显式提示，生产环境回退到 `zh-CN`
- 禁用硬编码文案

### 1.4 文案与翻译审核流程

- PR 必须包含 `zh-CN` 与 `en-US` 两套新增 key
- 检查语义一致性与语法错误
- UI 验证：长文本溢出、按钮长度、表格列宽

### 1.5 i18n 测试清单

- 语言切换后全站文案更新
- 缺失 key 在开发环境可见
- 生产环境不得出现未翻译 key
- 占位符渲染正确（如 {count}）
- 日期/数字/货币本地化格式正确
- 双语下布局不溢出
- 表格列宽与按钮尺寸合理
- 刷新后语言偏好保持

### 1.6 i18n 自动化与 CI 建议

- Key 覆盖率检查：`zh-CN` 与 `en-US` 必须 1:1 对齐
- 缺失 Key 检测：构建/CI 阶段自动失败
- 未使用 Key 清理：定期输出报告
- 快照测试：核心页面双语快照
- 伪本地化（可选）：字符拉长测试布局
- Lint 规则：禁止硬编码文案
- 检查脚本：`dev/scripts/check_i18n_keys.py`

---

## 2. 功能与数据流

### 2.1 Storyboard 导入与校验
- 上传 `storyboard*.json`
- 后端返回解析结果与错误信息
- 解析成功后进入分镜列表

**状态**：loading / invalid_json / schema_error / success

### 2.2 Segment 列表与编辑
- 列表字段：segment_index, prompt_text, duration_seconds, resolution, is_pro, image_url
- 支持批量筛选、搜索
- 支持编辑：prompt_text / director_intent / asset / image_url / resolution

**资产编辑**：
- 角色列表（name + id）
- 场景（scene）
- 道具（props）
- 支持 ID 注入的输入提示与保存

### 2.3 参考图上传
- 为分镜上传起始帧图片
- 后端返回 image_url
- 更新到 segment 数据并标记已绑定

### 2.4 执行配置
- gen_count
- concurrency
- range（all 或范围字符串）
- output_mode（centralized / in_place / custom）
- dry_run / force
- duration_seconds 可选值需遵循后端校验规则（4/8/10/12/15/25），且可能因 Provider 能力而变化
- **逻辑模型选择**（用户侧）
  - 逻辑模型下拉选择（来自 `/models`）
  - 路由策略由系统后台配置，用户侧不显示

### 2.5 运行与监控
- 创建 run 后进入监控页
- 状态分级：queued / running / completed / failed / download_failed
- 任务列表支持实时刷新与筛选（status / error_code / retryable）
- 默认筛选：status=failed 且 retryable=true；支持一键清除筛选查看全量任务
- 任务详情需展示错误码 + 处理建议（基于 error_code 映射）
- 重试按钮仅在 `status=failed` 且 `retryable=true` 时可用
- 重试触发后任务进入队列，若筛选条件变化导致不可见，应给出提示或引导清除筛选

### 2.6 结果查看
- 任务详情显示完整元数据（包含 full_prompt / error_code / retryable）
- 提供视频下载与元数据下载
- 失败任务可重试（若后端支持）

### 2.7 管理后台（内部使用，需预留）
- Provider 启用/禁用、优先级配置
- 逻辑模型与 Provider 模型映射维护（不可暴露给普通用户）
- 管理后台可独立页面或独立入口，但需预留导航/权限逻辑

---

## 3. 页面与组件清单

- Dashboard
- Storyboard 导入页
- Project/Storyboard 列表页
- Segment 列表页（可编辑）
- Run 配置页
- Run 监控页
- Task 详情页
- 结果库页

**通用组件**：
- 通知/Toast
- 状态标签（status badge）
- 表单校验提示
- 空状态与错误状态

### 3.1 信息架构与导航结构

**全局导航（左侧主导航）**
- Dashboard
- Storyboards
- Runs
- Results
- Settings（可选）
- Admin Settings（内部使用，可选）

**页面层级（建议路由结构）**
- `/dashboard`
- `/storyboards`
- `/storyboards/import`
- `/storyboards/{id}`
- `/storyboards/{id}/segments`
- `/runs`
- `/runs/{id}`
- `/runs/{id}/tasks/{task_id}`
- `/results`
- `/settings`

**关键页面信息结构**
- Dashboard: 概览卡片 + 最近任务 + 失败提醒
- Storyboards: 列表 / 导入 / 详情（含分镜入口）
- Segments: 表格视图 + 右侧编辑面板或弹窗
- Runs: 运行配置入口 + 运行记录列表
- Run Detail: 进度总览 + 任务列表 + 筛选
- Task Detail: 元数据详情 + 视频/下载 + 错误信息

---

## 4. API 对接（契约草案）

**Base**: `/api/v1`
**OpenAPI 草案**: `docs/openapi_draft.yaml`

### 4.0 认证与安全（JWT/Cookie）

**默认方案: JWT Bearer**
- 请求头：`Authorization: Bearer <token>`
- 401 需返回 `WWW-Authenticate: Bearer`

**模式 B: Cookie Session**
- 请求头：`Cookie: session=<token>`
- 需 CSRF 保护

**错误码规范（建议）**
- `unauthorized` (401)
- `forbidden` (403)
- `not_found` (404)
- `schema_error` (400)
- `validation_error` (400)
- `conflict` (409)
- `rate_limited` (429)
- `dependency_error` (502)
- `quota_exceeded` (402)
- `server_error` (500)

### 4.0.1 前端错误处理策略（执行要求）

- `unauthorized`: 触发登录流程或弹窗
- `forbidden`: 提示无权限并禁用操作按钮
- `not_found`: 提示资源不存在并返回上级
- `schema_error`/`validation_error`: 高亮字段并展示后端原因
- `rate_limited`: 提示限流并延迟重试
- `dependency_error`: 提示外部服务异常，保留重试按钮
- `quota_exceeded`: 提示额度不足，阻断提交
- `server_error`: 通用错误提示并建议反馈

**任务错误字段（Task.error_code）**
可能值：`content_policy`、`validation_error`、`rate_limited`、`timeout`、`quota_exceeded`、`unauthorized`、`forbidden`、`dependency_error`、`server_error`、`unknown_error`、`download_failed`、`no_provider`
`retryable` 为 true 表示可重试或可触发 failover

### 4.0.2 错误展示组件规范（执行要求）

- **Toast**：短期提示（rate_limited / dependency_error / server_error）
- **Banner**：阻断级错误（quota_exceeded / forbidden）
- **Field Error**：表单校验错误（schema_error / validation_error）
- **Empty State**：资源不存在或列表为空

**展示优先级**
1) Banner
2) Field Error
3) Toast
4) Empty State

### Storyboard
- `POST /storyboards`
- `GET /storyboards`
- `GET /storyboards/{id}`
- `GET /storyboards/{id}/segments`

### Segment
- `PATCH /segments/{id}`
- `POST /segments/{id}/assets/start-image`

### Run
- `POST /runs`
- `GET /runs/{id}`
- `GET /runs/{id}/tasks`

### Task
- `GET /tasks/{id}`
- `POST /tasks/{id}/retry`
- `GET /tasks/{id}/download`
- `GET /tasks/{id}/metadata`

### 4.1 请求与响应示例

**通用错误格式**
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

**Storyboard 响应**
```json
{
  "id": "sb_123",
  "name": "storyboard_demo.json",
  "created_at": "2026-01-02T10:00:00Z",
  "segment_count": 2
}
```

**Segment 响应**
```json
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
```

**Run 创建请求**
```json
{
  "storyboard_id": "sb_123",
  "gen_count": 2,
  "concurrency": 5,
  "range": "all",
  "output_mode": "centralized",
  "dry_run": false,
  "force": false
}
```

**Run 详情响应**
```json
{
  "id": "run_456",
  "status": "running",
  "total_tasks": 24,
  "completed": 8,
  "failed": 1,
  "download_failed": 1,
  "created_at": "2026-01-02T10:10:00Z"
}
```

**Task 详情响应**
```json
{
  "id": "task_789",
  "status": "completed",
  "video_url": "https://example.com/video.mp4",
  "metadata_url": "https://example.com/metadata.json",
  "full_prompt": "Alice ... [Scene: ...]",
  "error_msg": null
}
```

**状态枚举**
`queued` | `running` | `completed` | `failed` | `download_failed`

### 4.2 字段级 JSON Schema

**Segment Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["segment_index", "prompt_text", "duration_seconds", "resolution", "is_pro"],
  "properties": {
    "id": { "type": "string", "minLength": 1 },
    "segment_index": { "type": "integer", "minimum": 1 },
    "prompt_text": { "type": "string", "minLength": 1 },
    "director_intent": { "type": ["string", "null"] },
    "image_url": { "type": ["string", "null"], "format": "uri" },
    "duration_seconds": { "type": "integer", "enum": [10, 15, 25] },
    "resolution": { "type": "string", "enum": ["horizontal", "vertical"] },
    "is_pro": { "type": "boolean" },
    "asset": {
      "type": "object",
      "required": ["characters", "props"],
      "properties": {
        "characters": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name"],
            "properties": {
              "name": { "type": "string", "minLength": 1 },
              "id": { "type": ["string", "null"], "pattern": "^@?[a-zA-Z0-9_]+$" }
            }
          }
        },
        "scene": { "type": ["string", "null"] },
        "props": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

**Storyboard Upload Request**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["file"],
  "properties": {
    "file": { "type": "string", "description": "multipart/form-data file upload" }
  }
}
```

**Run Create Request**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["storyboard_id", "model_id", "gen_count", "concurrency", "range", "output_mode", "dry_run", "force"],
  "properties": {
    "storyboard_id": { "type": "string", "minLength": 1 },
    "model_id": { "type": "string", "minLength": 1 },
    "routing_strategy": { "type": "string", "enum": ["manual", "default", "failover", "weighted", "cost", "latency", "quota"] },
    "gen_count": { "type": "integer", "minimum": 1, "maximum": 10 },
    "concurrency": { "type": "integer", "minimum": 1, "maximum": 50 },
    "range": { "type": "string", "minLength": 1 },
    "output_mode": { "type": "string", "enum": ["centralized", "in_place", "custom"] },
    "output_path": { "type": ["string", "null"] },
    "dry_run": { "type": "boolean" },
    "force": { "type": "boolean" }
  }
}
```

**Task Response**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "status"],
  "properties": {
    "id": { "type": "string", "minLength": 1 },
    "status": { "type": "string", "enum": ["queued", "running", "completed", "failed", "download_failed"] },
    "video_url": { "type": ["string", "null"], "format": "uri" },
    "metadata_url": { "type": ["string", "null"], "format": "uri" },
    "full_prompt": { "type": ["string", "null"] },
    "error_msg": { "type": ["string", "null"] }
  }
}
```

### 4.3 端点级 Request/Response Schema（含分页/过滤/排序）

**通用分页参数（Query）**
- `page`: integer, default=1, minimum=1
- `page_size`: integer, default=20, minimum=1, maximum=100
- `sort`: string, 可选字段名（如 `created_at` / `segment_index` / `status`）
- `order`: string, enum=`asc|desc`

**通用分页响应**
```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

**GET /storyboards**
Query: `page, page_size, sort, order, name`
Response:
```json
{
  "items": [
    { "id": "sb_123", "name": "storyboard_demo.json", "created_at": "2026-01-02T10:00:00Z", "segment_count": 2 }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

**GET /storyboards/{id}/segments**
Query: `page, page_size, sort, order, resolution, is_pro`
Response:
```json
{
  "items": [
    { "id": "seg_001", "segment_index": 1, "prompt_text": "Alice ...", "duration_seconds": 10, "resolution": "horizontal", "is_pro": false }
  ],
  "page": 1,
  "page_size": 20,
  "total": 12
}
```

**GET /runs**
Query: `page, page_size, sort, order, status`
Response:
```json
{
  "items": [
    { "id": "run_456", "status": "running", "total_tasks": 24, "created_at": "2026-01-02T10:10:00Z" }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

**GET /runs/{id}/tasks**
Query: `page, page_size, sort, order, status, segment_index, error_code, retryable`
建议排序：`sort=retryable&order=desc`（可重试优先）或 `sort=segment_index&order=asc`
Response:
```json
{
  "items": [
    { "id": "task_789", "status": "completed", "video_url": "https://example.com/video.mp4", "error_code": null, "retryable": null }
  ],
  "page": 1,
  "page_size": 20,
  "total": 24
}
```

**GET /models**
Query: `page, page_size, sort, order, enabled`
Response:
```json
{
  "items": [
    {
      "id": "sora2",
      "display_name": "Sora2",
      "description": "Logical model for standard generation",
      "enabled": true
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

**GET /models/{id}**
Response:
```json
{
  "id": "sora2",
  "display_name": "Sora2",
  "description": "Logical model for standard generation",
  "enabled": true
}
```

**管理后台接口（内部使用，前端需预留但可不实现）**
**GET /admin/providers**
Query: `page, page_size, sort, order, enabled`

**PATCH /admin/providers/{id}**
Request:
```json
{
  "enabled": true,
  "priority": 5,
  "weight": 3
}
```

**GET /admin/models**
Query: `page, page_size, sort, order, enabled`

**PATCH /admin/models/{id}**
Request:
```json
{
  "enabled": false
}
```

**PATCH /admin/models/{id}/providers/{provider_id}**
Request:
```json
{
  "provider_model_ids": ["sora-2", "web-sora-2"]
}
```

**PATCH /segments/{id}**
Request:
```json
{
  "prompt_text": "Updated prompt",
  "director_intent": "Cinematic lighting",
  "image_url": "https://example.com/start.png",
  "resolution": "horizontal",
  "asset": {
    "characters": [{ "name": "Alice", "id": "@char_123" }],
    "scene": "Cyberpunk street",
    "props": ["Neon Umbrella"]
  }
}
```

**POST /runs**
Request:
```json
{
  "storyboard_id": "sb_123",
  "model_id": "sora2",
  "routing_strategy": "default",
  "gen_count": 2,
  "concurrency": 5,
  "range": "all",
  "output_mode": "centralized",
  "output_path": null,
  "dry_run": false,
  "force": false
}
```

---

## 5. 关键交互细节

- 上传 JSON：必须显示校验失败原因与错误行信息
- Segment 编辑：支持即时保存与批量保存（可二选一）
- 运行配置：用户输入范围如 `1-5, 8, 10`，前端只做基础格式校验
- 任务详情：显示原始 prompt、增强 prompt、error_msg、video_url

---

## 6. 交付要求

- 前端工程可运行
- 提供必要的运行说明
- UI 样式符合 Material Design 3 的浅色专业风格
- 桌面端体验优先，移动端兼容
- 联调清单参考 `docs/backend_integration_checklist.md`
