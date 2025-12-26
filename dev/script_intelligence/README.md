# 🧠 CineFlow Script Intelligence (CSI) - 前置处理模块开发计划

## 1. 项目愿景 (Vision)
构建一个智能化的前置处理模块，能够接收非结构化的长文本（剧本、小说），通过 LLM（如 Gemini 1.5/2.0 Flash）的长窗口能力，自动进行角色对齐、剧情切分、视觉转化，最终输出 `CineFlow` 可直接执行的高质量标准化 JSON 数据。

## 2. 核心痛点解决 (Problem Solving)
*   **角色一致性**: 解决 "小美"、"她"、"老师" 指代同一人的问题。通过建立 `Character Bible` (角色圣经) 进行统一管理。
*   **上下文丢失**: 解决切片后的分镜不知道前文发生了什么的问题。通过注入 `Global Summary` (全剧概括) 和 `Beat Context` (节拍上下文)。
*   **视觉转化**: 将文学语言（"心中五味杂陈"）转化为视觉语言（"面部特写，眉头紧锁，眼神游离"）。
*   **格式混乱**: 兼容 Final Draft、Markdown、纯文本等多种输入格式。

## 3. 架构设计 (Architecture)

### Phase 1: 宏观分析 (The "Brain")
*   **输入**: 完整剧本/小说文件。
*   **处理**: LLM 阅读全文。
*   **输出**: 
    *   `Global Summary`: 故事核心梗概。
    *   `Character Bible`: 角色列表，包含 ID、标准名、所有别名 (Aliases)、外貌描述。
    *   `Beat Sheet`: 剧情节拍表，包含 [节拍摘要, 原文起始句, 原文结束句]。

### Phase 2: 精细切分 (The "Knife")
*   **逻辑**: 基于 `Beat Sheet` 的锚点，或者基于场景头 (Scene Header) 的正则特征，将长文本物理切分为 `Chunks`。
*   **策略**: 
    *   剧本模式: 按 `EXT.` / `INT.` 切分。
    *   小说模式: 按章节或语义节拍切分。

### Phase 3: 分镜生成 (The "Refiner")
*   **输入**: `Chunk Text` + `Global Summary` + `Character Bible`。
*   **处理**: LLM 逐个 Chunk 处理。
*   **指令**: 
    *   将文本转化为视觉画面 `prompt_text`。
    *   **关键**: 使用 `((角色名))` 符号在 Prompt 中框出角色，且必须使用 Bible 中的标准名。
    *   **保护**: 台词 (Dialogue) 保持原样，不进行 ID 替换。
*   **输出**: 标准化 JSON Segments。

## 4. 数据结构升级 (Schema V2)
见 `schema_v2.json`。引入 `metadata` 全局信息和更丰富的 `character` 定义。

## 5. 路线图 (Roadmap)
1.  [x] 设计 JSON V2 结构。
2.  [x] 设计 Prompt Framework (.md)。
3.  [ ] 开发 Python 原型代码 (Splitter & Context Injector)。
4.  [ ] 接入 LLM API 进行实测。
5.  [ ] 集成至 `CineFlow` 主流程 (作为可选的前置步骤)。
