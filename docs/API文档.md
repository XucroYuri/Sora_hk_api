# API 文档

了解如何使用 Sora API

## 快速开始

1. 在"API密钥"页面创建您的 API Key

2. 确保账户有足够的余额

3. 使用以下代码开始调用 API

## 认证

所有 API 请求需要在 Header 中包含您的 API Key：

```
Authorization: Bearer sora-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Base URL

```
https://api.sora.hk/v1
```

## API 接口

### 1. 创建视频生成任务

本站格式OpenAI官方格式（兼容NewAPI）

POST`/create`

创建一个新的视频生成任务，支持文本生成和图片生成两种模式

#### 请求参数

|参数|类型|必填|说明|
|---|---|---|---|
|prompt|string|是|视频描述文本|
|image_url|string|否|附加图片|
|is_pro|boolean|否|是否使用Pro模型（默认false）|
|duration|number|否|视频时长（秒）。普通模式：10/15（默认10）；Pro模式：10/15/25（默认10）|
|resolution|string|否|分辨率：horizontal/vertical|
|quality|string|否|清晰度：normal/high（Pro模式自动高清，该参数为兼容性保留）|
|remove_watermark|boolean|否|是否去水印（默认true）。设为true时生成无水印视频，设为false时视频会带水印|

#### 请求示例

```
curl -X POST https://api.sora.hk/v1/create \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "is_pro": false,
    "duration": 10,
    "resolution": "horizontal",
    "remove_watermark": true
  }'
```

#### 响应示例

```
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "cost": 10
  }
}
```

### 2. 查询任务状态

本站格式OpenAI官方格式（兼容NewAPI）

GET`/tasks/:task_id`

查询指定任务的状态和结果

#### 请求示例

```
curl -X GET https://api.sora.hk/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### 成功响应示例

```
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": 100,
    "prompt": "A beautiful sunset over the ocean",
    "video_url": "https://example.com/video.mp4",
    "is_pro": false,
    "created_at": "2025-10-19T12:00:00Z",
    "completed_at": "2025-10-19T12:05:00Z"
  }
}
```

#### 失败响应示例

```
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "failed",
    "progress": 97,
    "prompt": "A beautiful sunset over the ocean",
    "error_msg": "此内容可能违反关于裸露、性内容或色情内容的相关规定。",
    "is_pro": false,
    "created_at": "2025-10-19T12:00:00Z"
  }
}
```

### 3. 获取任务列表

GET`/tasks`

获取您的任务列表，支持分页和筛选

#### 查询参数

- page - 页码（默认1）
- page_size - 每页数量（默认20）
- status - 状态筛选（pending/processing/completed/failed）

#### 请求示例

```
curl -X GET "https://api.sora.hk/v1/tasks?page=1&page_size=20&status=completed" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 4. 查询余额

GET`/balance`

#### 请求示例

```
curl -X GET https://api.sora.hk/v1/balance \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### 响应示例

```
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "balance": 5000
  }
}
```

注：余额单位为分（cents），5000 = $50.00

### 5. 查询价格

GET`/pricing`

#### 请求示例

```
curl -X GET https://api.sora.hk/v1/pricing \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### 响应示例

```
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "normal_price": 3,
    "pro_price": 30,
    "currency": "USD",
    "unit": "cents"
  }
}
```

## 任务状态

pending等待处理

processing生成中

completed已完成

failed失败

## 错误码

200操作成功

401未授权（API Key 无效或已禁用）

1001参数错误

1012余额不足

500服务器内部错误

## 最佳实践

- 妥善保管 API Key，不要在客户端代码中暴露
- 为不同环境使用不同的 API Key
- 定期轮换 API Key 以提高安全性
- 使用额度限制功能防止意外消耗
- 实现错误重试机制（建议指数退避）
- 任务生成通常需要3-30分钟（Pro任务耗时较长），建议使用轮询或 Webhook