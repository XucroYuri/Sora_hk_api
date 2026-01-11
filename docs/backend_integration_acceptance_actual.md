# 后端联调验收记录（实际运行）

**版本**: v0.1  
**执行日期**: 2026-01-10  
**执行方式**: FastAPI TestClient（本地进程内）  

---

## 1. 基本信息

- 项目名称：CineFlow
- 联调版本/分支：本地工作区
- Base URL：TestClient（无公网地址）
- 认证方式：Bearer
- 执行人：自动化脚本
- 请求头示例：`Authorization: Bearer test-token`

## 2. 依赖配置确认

- `AUTH_TOKEN`：已设置（test-token）
- Provider Key：未配置（dry_run）
- 是否使用 `dry_run`：是
- 测试数据：`input/storyboard_demo.json`
- 关键参数：`gen_count=1`、`range=all`、`concurrency=2`

## 3. 联调检查记录

| 步骤 | 接口 | 期望结果 | 实际结果 | 结论(PASS/FAIL) | 备注 |
| --- | --- | --- | --- | --- | --- |
| 1 | POST /api/v1/storyboards | 201 + 返回 id | 201 + sb=c5e161735d1648d899dc5cd54de24643 | PASS | segment_count=2 |
| 2 | GET /api/v1/storyboards | 列表含新 id | 列表含 sb=c5e161735d1648d899dc5cd54de24643 | PASS | total=1 |
| 3 | GET /api/v1/storyboards/{id}/segments | segments 可读 | 2 条 segments | PASS | seg=da2b98f5..., dd26958e... |
| 4 | PATCH /api/v1/segments/{segment_id} | 更新成功 | 200 + prompt 更新 | PASS | seg=da2b98f5... |
| 5 | GET /api/v1/models?enabled=true | 含 sora2/sora2pro | 返回 sora2/sora2pro | PASS | total=2 |
| 6 | POST /api/v1/runs | 返回 run_id | 201 + run=242f68951c774f2fb9c44a68740177d1 | PASS | dry_run |
| 7 | GET /api/v1/runs/{id} | 状态最终完成 | completed | PASS | completed=2 |
| 8 | GET /api/v1/runs/{id}/tasks?sort=segment_index&order=asc | tasks 可读 | 2 条 tasks | PASS | task=21a6935b..., 68bdc600... |
| 9 | GET /api/v1/tasks/{task_id} | error_code/详情可读 | error_code=null | PASS | dry_run |
| 10 | GET /api/v1/tasks/{task_id}/metadata | 元数据可读 | JSON 返回 | PASS | 含 output_dir/paths |
| 11 | GET /api/v1/tasks/{task_id}/download | 视频或 302 | 404 | PASS | dry_run 预期 |
| 12 | POST /api/v1/tasks/{task_id}/retry | 进入运行态 | running | PASS | dry_run |

## 4. 过滤/排序校验

| 接口 | 条件 | 期望结果 | 实际结果 | 结论(PASS/FAIL) | 备注 |
| --- | --- | --- | --- | --- | --- |
| /api/v1/runs | status=failed | 仅失败 | 0 条 | PASS | dry_run |
| /api/v1/runs/{id}/tasks | status=failed&retryable=true | 仅可重试失败 | 0 条 | PASS | dry_run |
| /api/v1/runs/{id}/tasks | error_code=rate_limited | 仅限流失败 | 0 条 | PASS | dry_run |

## 5. 错误处理校验

- 401 未认证：PASS（code=unauthorized）
- 404 资源不存在：PASS（code=not_found）
- 400 参数校验错误：PASS（code=validation_error）

## 6. 问题记录与待办

- 问题 1：无
- 问题 2：无
- 待办 1：如需真实生成，请补齐 Provider Key 并关闭 dry_run

## 7. 真实生成联调（进行中）

**执行窗口**: 2026-01-10  
**说明**: 使用真实 Key、`dry_run=false`，仅生成分镜 1  

**摘要**
- storyboard_id: `6eaaf5f674b24757b6833c60b5f83c33`
- run_id: `d706e81b19d74733bb5eb4efd134613f`
- run_status: `running`（采样时仍在执行）
- total_tasks: 1

**任务状态**
- task_id: `39802f75b71847e2bb12d12c933b2f5c`
- status: `running`
- segment_index: 1

**待办**
- 已完成，结果记录如下

**最终结果**
- run_status: `completed`
- total_tasks: 1
- completed: 1
- failed: 0
- download_failed: 0
- task_id: `39802f75b71847e2bb12d12c933b2f5c`
- task_status: `completed`
- video_url: `https://oss-sora-hk.aicook.fun/az/files/00000000-6110-7284-9b86-90defc1e6cf5%2Fraw?se=2026-01-13T00%3A00%3A00Z&sp=r&sv=2024-08-04&sr=b&skoid=8ebb0df1-a278-4e2e-9c20-f2d373479b3a&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-01-10T12%3A12%3A28Z&ske=2026-01-17T12%3A17%3A28Z&sks=b&skv=2024-08-04&sig=wBknLEbSh1aKoseUS50NTXZ2cHXoW4qVILhD5NDhgFk%3D&ac=oaisdsorprcentralus`
- download_status: `200`
- download_content_type: `video/mp4`
- download_size_bytes: 10784340
- download_saved_to: `backend/output_downloads/39802f75b71847e2bb12d12c933b2f5c.mp4`

## 8. AIHubMix 真实生成联调

**执行窗口**: 2026-01-10  
**说明**: 启用 AIHubMix、禁用 Sora.hk/OpenAI 以强制路由；分镜 1、4s  

**摘要**
- storyboard_id: `4ddda62d56904992af4610ebd2ace23b`
- run_id: `5f2ba0fc309141549a89727d75d90b18`
- run_status: `completed`
- total_tasks: 1

**任务结果**
- task_id: `528f19df4e474fefaedd497950102d00`
- task_status: `completed`
- 路由策略：禁用 Sora.hk/OpenAI，强制命中 AIHubMix
- video_url: `https://aihubmix.com/v1/videos/eyJtb2RlbCI6InNvcmEtMiIsImlkIjoidmlkZW9fNjk2MjYxMTdmMDU0ODE5MDlhZTA0M2I5ZWM3MGFjN2IifQchannel2679/content`

**下载校验**
- download_status: `200`
- download_content_type: `video/mp4`
- download_size_bytes: 4814562
- download_saved_to: `backend/output_downloads/aihubmix_528f19df4e474fefaedd497950102d00.mp4`

## 9. 真实下载联调补充（Sora.hk）

**执行窗口**: 2026-01-11  
**说明**: TestClient 真实执行（非 dry_run），分镜 1，`gen_count=1`，`concurrency=1`  

**摘要**
- storyboard_id: `76c94b5b67a7432c838a4720739065f1`
- run_id: `dfae04ea5823487f8f0119bb61a3a476`
- run_status: `completed`
- total_tasks: 1

**任务结果**
- task_id: `4b1605d8e1aa48ab8249f79fd0c4fdcf`
- task_status: `completed`
- video_url: `https://oss-sora-hk.aicook.fun/az/files/00000000-f168-7284-8d1d-1570076b96ac%2Fraw?se=2026-01-13T00%3A00%3A00Z&sp=r&sv=2024-08-04&sr=b&skoid=cfbc986b-d2bc-4088-8b71-4f962129715b&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-01-11T02%3A43%3A29Z&ske=2026-01-18T02%3A48%3A29Z&sks=b&skv=2024-08-04&sig=%2BvIk7k65%2BPf0gW5GjwFu2x6eniqx0TYXif6ARhN5EUw%3D&ac=oaisdsorprcentralus`

**下载校验**
- download_status: `200`
- download_size_bytes: 10658706
- download_saved_to: `backend/output/76c94b5b67a7432c838a4720739065f1/Segment_1/1_v1_20260111150746_nfn7_4b1605d8e1aa48ab8249f79fd0c4fdcf.mp4`
- metadata_path: `backend/output/76c94b5b67a7432c838a4720739065f1/Segment_1/1_v1_20260111150746_nfn7_4b1605d8e1aa48ab8249f79fd0c4fdcf.json`

**元数据快照**
- status: `completed`
- progress: 100
- duration: 10
- resolution: `horizontal`
- quality: `normal`
- provider_task_id: `ec13776f-1872-425e-afa5-4a13c24ca744`

**接口响应快照**
- GET `/api/v1/tasks/{task_id}`
  - status: `200`
  - body: `{"id":"4b1605d8e1aa48ab8249f79fd0c4fdcf","status":"completed","video_url":"https://oss-sora-hk.aicook.fun/az/files/00000000-f168-7284-8d1d-1570076b96ac%2Fraw?se=2026-01-13T00%3A00%3A00Z&sp=r&sv=2024-08-04&sr=b&skoid=cfbc986b-d2bc-4088-8b71-4f962129715b&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-01-11T02%3A43%3A29Z&ske=2026-01-18T02%3A48%3A29Z&sks=b&skv=2024-08-04&sig=%2BvIk7k65%2BPf0gW5GjwFu2x6eniqx0TYXif6ARhN5EUw%3D&ac=oaisdsorprcentralus","metadata_url":"/api/v1/tasks/4b1605d8e1aa48ab8249f79fd0c4fdcf/metadata","full_prompt":"A futuristic city skyline at night with neon lights reflecting on the river. Cyberpunk style. [Scene: Future City] (Director Note: Establishing shot.)","error_msg":"","error_code":null,"retryable":false,"segment_index":1}`
- GET `/api/v1/runs/{run_id}`
  - status: `200`
  - body: `{"id":"dfae04ea5823487f8f0119bb61a3a476","status":"completed","total_tasks":1,"completed":1,"failed":0,"download_failed":0,"created_at":"2026-01-11T15:08:35.407000+08:00"}`
- GET `/api/v1/runs/{run_id}/tasks?page=1&page_size=20&sort=segment_index&order=asc`
  - status: `200`
  - body: `{"items":[{"id":"4b1605d8e1aa48ab8249f79fd0c4fdcf","status":"completed","video_url":"https://oss-sora-hk.aicook.fun/az/files/00000000-f168-7284-8d1d-1570076b96ac%2Fraw?se=2026-01-13T00%3A00%3A00Z&sp=r&sv=2024-08-04&sr=b&skoid=cfbc986b-d2bc-4088-8b71-4f962129715b&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-01-11T02%3A43%3A29Z&ske=2026-01-18T02%3A48%3A29Z&sks=b&skv=2024-08-04&sig=%2BvIk7k65%2BPf0gW5GjwFu2x6eniqx0TYXif6ARhN5EUw%3D&ac=oaisdsorprcentralus","metadata_url":"/api/v1/tasks/4b1605d8e1aa48ab8249f79fd0c4fdcf/metadata","full_prompt":"A futuristic city skyline at night with neon lights reflecting on the river. Cyberpunk style. [Scene: Future City] (Director Note: Establishing shot.)","error_msg":"","error_code":null,"retryable":false,"segment_index":1}],"page":1,"page_size":20,"total":1}`

**下载响应头**
- content-type: `video/mp4`
- accept-ranges: `bytes`
- content-length: `10658706`
- last-modified: `Sun, 11 Jan 2026 07:13:22 GMT`
- etag: `"f8189f08c6f9f0eed30ca6a402b965b6"`

**文件校验**
- video_sha256: `fd5dbea91bfbaac73852b107b7df12efed4ee2271db95b43eace53b38c9774d4`
- video_md5: `7eadf209686dfc7e806285b0cf5965a8`
- metadata_sha256: `ed889f929057bc592e7a4c2f91025518e1b0be1551f15d143e483dd717a40544`
- metadata_size_bytes: 1322

**补充说明**
- 为捕获 `download` 响应头与 `tasks/runs` 快照，使用 TestClient 在进程内复原 `run/task` 记录并指向同一视频文件路径；未修改磁盘数据或真实后端存储。

**元数据完整内容**
```json
{
  "completed_at": "2026-01-11T15:13:06.307+08:00",
  "created_at": "2026-01-11T15:08:35.407+08:00",
  "duration": 10,
  "error_msg": "",
  "image_url": "",
  "is_pro": false,
  "progress": 100,
  "prompt": "A futuristic city skyline at night with neon lights reflecting on the river. Cyberpunk style. [Scene: Future City] (Director Note: Establishing shot.)",
  "quality": "normal",
  "remove_watermark": true,
  "resolution": "horizontal",
  "status": "completed",
  "task_id": "ec13776f-1872-425e-afa5-4a13c24ca744",
  "video_url": "https://oss-sora-hk.aicook.fun/az/files/00000000-f168-7284-8d1d-1570076b96ac%2Fraw?se=2026-01-13T00%3A00%3A00Z&sp=r&sv=2024-08-04&sr=b&skoid=cfbc986b-d2bc-4088-8b71-4f962129715b&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-01-11T02%3A43%3A29Z&ske=2026-01-18T02%3A48%3A29Z&sks=b&skv=2024-08-04&sig=%2BvIk7k65%2BPf0gW5GjwFu2x6eniqx0TYXif6ARhN5EUw%3D&ac=oaisdsorprcentralus",
  "local_status": "completed",
  "full_prompt": "A futuristic city skyline at night with neon lights reflecting on the river. Cyberpunk style. [Scene: Future City] (Director Note: Establishing shot.)",
  "local_task_id": "4b1605d8e1aa48ab8249f79fd0c4fdcf",
  "source_file": "backend/uploads/20260111070746_storyboard_demo.json",
  "segment_index": 1,
  "version_index": 1,
  "download_status": "success"
}
```
