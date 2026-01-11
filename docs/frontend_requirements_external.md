# CineFlow 前端需求说明（外部开发者版）

**版本**: v0.1  
**日期**: 2026-01-02  
**目标读者**: 外部前端开发者  

---

## 1. 项目目标

本前端用于将现有 CLI 的视频生成流程产品化为可视化操作台。重点是流程闭环、状态可追踪、结果可验收。

**不限制技术栈**，但请遵循以下 UI 规范：
- **浅色主题**（默认仅浅色）
- **现代、专业、企业级**视觉风格
- **符合 Google 标准的专业 UI 规范**（遵循 Material Design 3 的排版、色彩、组件与交互行为）
- **界面语言与 i18n**：中文为主、英文为辅；必须严格区分中英文，不允许中英混排；支持中/英文切换；所有文案通过 i18n 资源文件管理

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

- 使用分层命名：`module.section.element`（例：`nav.dashboard`、`run.status.completed`）
- 统一动词前缀：`action.*`（例：`action.submit`、`action.cancel`）
- 统一状态前缀：`status.*`（例：`status.running`、`status.failed`）
- 统一提示前缀：`msg.*`（例：`msg.upload_success`）
- 统一错误前缀：`error.*`（例：`error.validation`）
- 统一表单前缀：`form.*`（例：`form.prompt_text.label`）
- 禁止复用不同语义的同一 key
- 禁止在 key 中使用中文或空格

### 1.3 i18n 运行规范

- **占位符**：使用命名占位符（例：`msg.deleted`: "已删除 {count} 项"）
- **日期/数字格式**：必须使用本地化格式化（Intl API 或框架内置）
- **缺失 key**：开发环境必须显式提示缺失 key；生产环境回退到 `zh-CN`
- **禁用硬编码**：UI 文案不得直接写死在组件内

### 1.4 文案与翻译审核流程

- 提交前自检：避免中英文混排、避免语义歧义
- PR 必须包含两种语言的新增 key
- 翻译验收：英文内容需语言校对（基本语法与语义一致）
- UI 验证：检查超长文本、换行与布局溢出（尤其在列表/表格）

### 1.5 i18n 测试清单

- 语言切换后所有页面文案正确更新
- 缺失 key 在开发环境可见（显式警告）
- 未翻译 key 不得在生产环境暴露
- 动态占位符渲染正确（如 {count}）
- 日期/数字/货币格式按语言本地化
- 超长英文/中文不导致布局溢出
- 列表/表格/按钮在双语下宽度合理
- 切换语言后刷新页面保持用户选择

### 1.6 i18n 自动化与 CI 建议

- **Key 覆盖率检查**：`zh-CN` 与 `en-US` 必须 1:1 对齐
- **缺失 Key 检测**：构建或 CI 期间自动失败
- **未使用 Key 清理**：定期检查并输出报告
- **快照测试**：核心页面在中英文下各跑一次快照
- **伪本地化**（可选）：拉长字符测试布局稳定性
- **Lint 规则**：禁止硬编码文案（强制使用 i18n key）
- **检查脚本**：`dev/scripts/check_i18n_keys.py`

---

## 2. 核心功能模块

### 2.1 仪表盘（Dashboard）
- 总览：本日/本周任务数、成功率、失败数、平均耗时
- 最近任务列表（可点击进入详情）

### 2.2 项目与 Storyboard 管理
- 上传/导入 `storyboard*.json`
- 解析并展示分镜列表（Segment Index、Prompt、时长、分辨率、Pro 模式）
- JSON 校验失败时展示错误详情与定位

### 2.3 分镜编辑与资产注入
- 编辑 `prompt_text`、`director_intent`
- 编辑 `asset`（角色列表、场景、道具）
- 角色 ID 注入（对角色名配置 @ID 并保存）
- 参考图上传（Start Frame）并绑定到 `image_url`
- 图片 URL 校验与自动修复提示

### 2.4 执行配置
- 每分镜版本数（gen_count）
- 最大并发数（concurrency）
- 分镜范围选择（all / 1-5,8 等）
- 输出模式（centralized / in_place / custom）
- `dry_run`、`force` 开关
- 时长可选值需遵循后端校验规则（4/8/10/12/15/25），且可能因 Provider 能力而变化
- **逻辑模型选择**（用户侧）
  - 逻辑模型下拉选择（来自 `/models`）
  - 路由策略由系统后台配置，用户侧不显示

### 2.5 任务执行与监控
- 提交生成任务并显示实时进度
- 任务状态：queued / running / completed / failed / download_failed
- 支持手动重试失败任务（可选）
- 失败筛选支持 `error_code` / `retryable`（如仅看可重试失败）
- 默认筛选策略：status=failed 且 retryable=true，并提供“一键清除筛选”以查看全部任务
- 任务详情需展示错误码 + 处理建议（基于 error_code 映射）
- 重试按钮仅在 `status=failed` 且 `retryable=true` 时可用
- 重试触发后任务进入队列，若筛选条件变化导致不可见，应给出提示或引导清除筛选

### 2.6 结果验收
- 任务详情页展示：最终 Prompt、视频 URL、执行耗时、错误信息、错误码（error_code）
- 下载视频、下载元数据 JSON
- 失败任务列表与筛选

### 2.7 管理后台（内部使用，需预留）
- Provider 启用/禁用、优先级配置
- 逻辑模型与 Provider 模型映射维护（不可暴露给普通用户）
- 管理后台可独立页面或独立入口，但需预留导航/权限逻辑

---

## 3. 页面与交互清单

- 登录页（可选，若后端启用鉴权）
- Dashboard
- 项目列表 / 详情
- Storyboard 导入页
- Segment 列表 / 编辑弹窗
- 任务执行配置页
- 运行中任务监控页
- 任务详情页
- 结果库（可按项目/分镜筛选）

**交互要求**
- 明确的状态提示（loading / empty / error）
- 表单校验提示清晰
- 上传、生成、下载操作需有确认与结果反馈
- 桌面优先，移动端可用

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

## 4. 后端接口（建议约定）

> 后端实际实现可能会调整，请以最终 API 文档为准。此处为前端开发对接的功能契约草案。
> OpenAPI 草案见 `docs/openapi_draft.yaml`。

### 4.1 认证与安全（JWT/Cookie）

**推荐默认方案：JWT Bearer**
- `Authorization: Bearer <token>`
- Cookie Session 可选（需 CSRF 保护）

**建议流程**
1) 登录获取 token
2) 前端保存并自动注入到请求头/Cookie
3) 401 触发重新登录

**安全约定**
- 401 未认证
- 403 无权限
- 需要服务端返回 `WWW-Authenticate` 头（JWT 模式）

### 4.2 错误码规范

**统一错误结构**
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

**建议错误码枚举**
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

### 4.3 前端错误处理策略（必做）

- `unauthorized`: 触发登录弹窗或跳转登录页
- `forbidden`: 提示无权限并隐藏相关操作入口
- `not_found`: 提示资源不存在，返回上一级
- `schema_error`/`validation_error`: 表单高亮错误字段，并提示具体原因
- `rate_limited`: 展示限流提示并建议稍后重试
- `dependency_error`: 展示“外部服务异常”提示，保留重试入口
- `quota_exceeded`: 展示额度不足提示，阻断提交入口
- `server_error`: 展示通用错误，建议刷新或联系管理员

**任务错误字段（Task.error_code）**
可能值：`content_policy`、`validation_error`、`rate_limited`、`timeout`、`quota_exceeded`、`unauthorized`、`forbidden`、`dependency_error`、`server_error`、`unknown_error`、`download_failed`、`no_provider`
`retryable` 为 true 表示可重试或可触发 failover

### 4.4 错误展示组件规范（UI 要求）

- **全局 Toast**：用于短期提示（rate_limited / dependency_error / server_error）
- **页面级 Banner**：用于阻断级错误（quota_exceeded / forbidden）
- **表单字段错误**：用于 schema_error / validation_error，必须指向具体字段
- **空状态/404**：统一使用空状态组件，提供返回路径

**展示优先级**
1) Banner（阻断）
2) Field Error（表单）
3) Toast（轻提示）
4) Empty State（无数据）

### 4.1 Storyboard
- `POST /api/v1/storyboards` 上传 JSON，返回解析结果
- `GET /api/v1/storyboards` 获取列表
- `GET /api/v1/storyboards/{id}` 获取详情
- `GET /api/v1/storyboards/{id}/segments` 获取分镜列表

### 4.2 Segment 编辑
- `PATCH /api/v1/segments/{id}` 更新 prompt/asset/image_url/resolution 等
- `POST /api/v1/segments/{id}/assets/start-image` 上传起始帧，返回 image_url

### 4.3 任务运行
- `POST /api/v1/runs` 创建运行任务（参数：storyboard_id, gen_count, concurrency, range, output_mode, dry_run, force）
- `GET /api/v1/runs/{id}` 运行详情（汇总状态）
- `GET /api/v1/runs/{id}/tasks` 任务列表

### 4.4 单任务详情
- `GET /api/v1/tasks/{id}` 任务详情（含元数据、video_url、error_msg）
- `POST /api/v1/tasks/{id}/retry` 重试（可选）

### 4.5 下载
- `GET /api/v1/tasks/{id}/download` 下载视频（可选）
- `GET /api/v1/tasks/{id}/metadata` 下载 JSON 元数据

### 4.6 数据结构与响应示例（草案）

**通用错误格式**（建议统一）：
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

**Storyboard（简化）**
```json
{
  "id": "sb_123",
  "name": "storyboard_demo.json",
  "created_at": "2026-01-02T10:00:00Z",
  "segment_count": 2
}
```

**Segment（简化）**
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

**状态枚举**（前端用于展示与过滤）
`queued` | `running` | `completed` | `failed` | `download_failed`

### 4.7 字段级 JSON Schema（草案）

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

### 4.8 端点级 Request/Response Schema（含分页/过滤/排序）

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

**GET /api/v1/storyboards**
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

**GET /api/v1/storyboards/{id}/segments**
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

**GET /api/v1/runs**
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

**GET /api/v1/runs/{id}/tasks**
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

**GET /api/v1/models**
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

**GET /api/v1/models/{id}**
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
**GET /api/v1/admin/providers**
Query: `page, page_size, sort, order, enabled`

**PATCH /api/v1/admin/providers/{id}**
Request:
```json
{
  "enabled": true,
  "priority": 5,
  "weight": 3
}
```

**GET /api/v1/admin/models**
Query: `page, page_size, sort, order, enabled`

**PATCH /api/v1/admin/models/{id}**
Request:
```json
{
  "enabled": false
}
```

**PATCH /api/v1/admin/models/{id}/providers/{provider_id}**
Request:
```json
{
  "provider_model_ids": ["sora-2", "web-sora-2"]
}
```

**PATCH /api/v1/segments/{id}**
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

**POST /api/v1/runs**
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

## 5. 交付物要求

- 可运行的前端代码
- 清晰的构建/运行说明
- 不依赖特定后端实现细节（只对接 API）
- UI 需满足浅色、专业、Material Design 风格
- 联调清单参考 `docs/backend_integration_checklist.md`

---

## 6. 验收标准

- 基本流程闭环：导入 -> 编辑 -> 配置 -> 运行 -> 监控 -> 结果
- 核心页面功能可用，错误信息可追踪
- UI 风格符合“浅色、现代、专业、Google 标准”
