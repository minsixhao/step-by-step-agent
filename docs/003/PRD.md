# AI Chat 应用 – 产品需求文档

## 1. 项目目标

开发一个**响应式 Web 应用**，在手机和电脑浏览器上运行。提供两种交互模式：
- **LLM Chat**：通过 OpenRouter 调用任意供应商的模型进行文本对话。
- **AI 语音电话**：基于豆包端到端实时语音模型（RealtimeAPI）进行语音对话。

**设计风格**：移动端完全参考 DeepSeek – 无底部 Tab，左上角打开历史对话（底部为头像入口），右上角新建对话。  
**主题色**：浅蓝（`#e6f7ff` 背景）+ 白色卡片，强调色 `#1890ff`。

---

## 2. 技术栈（固定）

| 层级 | 技术选型 | 用途 |
|------|----------|------|
| 前端 | React 18 + TypeScript + Vite | 构建 UI，强类型 |
| 样式 | TailwindCSS 3 | 响应式、移动优先 |
| 状态管理 | Zustand | 全局状态（用户、对话、UI） |
| 后端运行时 | Node.js 20 + Express | API 服务、WebSocket 代理 |
| 数据库 | PostgreSQL 15 | 用户、对话、消息存储 |
| ORM | Prisma | 数据库操作 |
| 认证 | JWT（存储于 httpOnly Cookie） | 登录状态管理 |
| 游客存储 | IndexedDB（Dexie.js 封装） | 未登录时本地保存对话 |
| 实时语音代理 | ws 库 + 二进制协议解析 | 连接豆包 API |
| LLM 代理 | Express 路由 + fetch | 调用 OpenRouter REST API |

> 不允许替换上述任何组件。

---

## 3. 用户系统与数据存储

### 3.1 认证要求

- **必须实现**注册、登录、退出登录功能。
- 登录凭证：用户名 + 密码（密码加密使用 bcrypt）。
- JWT 有效期 7 天，存储在 **httpOnly Cookie** 中（防止 XSS）。
- **必须支持游客模式**：未登录时自动生成访客 ID（保存在 localStorage），所有对话写入浏览器 IndexedDB。
- 游客登录后，系统**必须弹窗询问**“是否将本地对话合并到云端？”，合并规则：按 `createdAt` 时间戳去重，同一条消息不重复存储。

### 3.2 数据库模型（Prisma Schema 必须完全一致）

```prisma
model User {
  id            String    @id @default(cuid())
  username      String    @unique
  passwordHash  String
  avatarUrl     String    @default("")   // 默认空，前端生成随机头像
  nickname      String    @default("")
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
  conversations Conversation[]
  settings      UserSettings?
}

model UserSettings {
  id               String   @id @default(cuid())
  userId           String   @unique
  theme            String   @default("light")       // 保留扩展，当前只实现 light
  defaultModelId   String   @default("openrouter/auto") // 默认模型 ID
  ttsSpeaker       String   @default("vv")          // 豆包音色
  user             User     @relation(fields: [userId], references: [id])
}

model Conversation {
  id            String    @id @default(cuid())
  userId        String?            // 游客时为空
  title         String             // 自动生成或用户修改
  mode          String             // "chat" 或 "voice"
  modelId       String?            // chat 模式下使用的模型 ID
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
  messages      Message[]
  user          User?     @relation(fields: [userId], references: [id])
}

model Message {
  id             String   @id @default(cuid())
  conversationId String
  role           String   // "user" 或 "assistant"
  content        String   // 文本内容（语音电话中也是识别出的文本）
  createdAt      DateTime @default(now())
  conversation   Conversation @relation(fields: [conversationId], references: [id])
}
```

### 3.3 游客本地存储（IndexedDB）

- 使用 Dexie.js，库名 `AIChatDB`，表 `conversations` 和 `messages`，结构与云端表相同但无外键约束。
- 游客模式下，所有对话操作（创建、更新、删除）同时修改 IndexedDB。
- 登录后，云端数据优先显示，游客数据隐藏但保留，等待合并请求。

---

## 4. 功能详细要求

### 4.1 全局布局（移动端/桌面）

- **无底部 Tab 栏**。
- **左上角**：菜单按钮（☰），点击打开侧边抽屉。
  - 抽屉宽度占屏幕 80%，背景半透明遮罩，点击遮罩关闭。
  - 抽屉内容：
    - 顶部标题“历史对话”
    - 对话列表按时间分组：今天、昨天、更早。每一行显示对话标题、最后更新时间、模式图标（💬/🎧）。
    - 每个对话支持滑动删除（移动端）或鼠标悬浮显示删除按钮（PC）。
    - 点击对话加载该对话的消息。
    - 抽屉**底部固定**一个区域：显示当前登录用户头像 + 昵称（若未登录则显示“游客”）。点击该区域打开“个人应用”弹窗（底部抽屉或居中模态框）。
- **右上角**：圆形“+”按钮，点击立即创建新对话：
  - 新对话模式沿用当前所选模式（若全局无记忆，则默认 Chat）。
  - 创建后清空消息列表，聚焦输入框。
- **主区域**：消息流 + 底部交互区（根据模式变化）。

### 4.2 LLM Chat 模式

#### 4.2.1 模型选择器
- 位于顶部栏右侧（或底部输入区上方），显示当前模型名称（如 `gpt-4o`）。
- 点击打开模型列表弹窗：
  - 数据来源：调用后端 `/api/models`（后端从 OpenRouter 获取并缓存）。
  - 列表包含模型 ID、名称、供应商 Logo（可使用简单图标）。
  - 支持搜索过滤。
- 切换模型后，后续对话使用该模型（保存在当前 Conversation 的 `modelId` 字段）。

#### 4.2.2 输入与流式回复
- 输入框为多行文本，支持 Enter 发送（Shift+Enter 换行）。
- 发送消息后：
  - 立即显示用户气泡。
  - 调用后端流式接口 `POST /api/chat/stream`，通过 **SSE** 返回增量内容。
  - 助手气泡逐步显示文字（支持 Markdown 渲染，代码高亮使用 `highlight.js`）。
- 每条消息保存到数据库（后端在流结束后保存完整内容）。

#### 4.2.3 历史对话管理
- 自动生成标题：取第一条用户消息前 30 字符，若为空则使用“新对话”。
- 用户可手动修改标题（双击对话列表项或点击编辑图标）。
- 删除对话时，后端删除关联消息，游客模式同时删除 IndexedDB。
- 支持继续已有对话：加载历史消息（分页，每页 50 条，滚动加载）。

### 4.3 AI 语音电话模式

#### 4.3.1 架构与连接
- 前端通过 WebSocket 连接后端代理：`ws://localhost/api/voice/ws`。
- 后端代理**必须**连接豆包地址：`wss://openspeech.bytedance.com/api/v3/realtime/dialogue`，并携带以下固定 Headers：
  ```
  X-Api-App-Id: 从环境变量获取
  X-Api-Access-Key: 从环境变量获取
  X-Api-Resource-Id: volc.speech.dialog
  X-Api-App-Key: PlgvMymc7f3tQnJ6
  ```
- 后端**必须**实现豆包的二进制协议（帧解析与组装），完全按照文档 2.2 节实现。
- 协议版本：v1，Header Size = 4 bytes，序列化使用 JSON，压缩使用无压缩。

#### 4.3.2 前端交互（UI）
- 语音电话界面包含：
  - 一个大的圆形按钮（直径 80px，背景浅蓝色）：显示“按住 说话”。
  - 按钮下方显示实时字幕（用户说的话，服务端返回的 ASRResponse 中的 `results[0].text`）。
  - 助手回复时，字幕区显示模型返回的文本（ChatResponse 的 content）。
- 交互模式：**push_to_talk**（按住说话，松开结束）。
  - 按下按钮时：请求麦克风权限，开始采集音频（20ms 一包 PCM 16000 Hz，int16），发送 `TaskRequest`。
  - 松开按钮时：发送 `EndASR` 事件（JSON `{}`）。
- 若服务端返回 `TTSResponse`（音频数据），前端必须**实时播放**（使用 Web Audio API 队列）。
- 若用户说话过程中助手仍在回复，**必须支持打断**（前端发送 `ClientInterrupt` 事件，并清空播放队列）。

#### 4.3.3 后端代理详细要求
- 接收前端 WebSocket 连接后，立即建立到豆包的连接。
- 转发规则：
  - 前端发送的文本消息（Message Type = 0b0001，event 字段）：解析 JSON 后重新组装为豆包协议的二进制帧，发送给豆包。
  - 前端发送的音频数据（Message Type = 0b0010）：直接作为 `TaskRequest` 的 payload 转发。
  - 豆包返回的二进制帧：解析后转换成简单 JSON 格式转发给前端，格式如下（示例）：
    ```json
    { "type": "TTSResponse", "data": "<base64 of audio>" }
    { "type": "ASRResponse", "data": { "results": [...] } }
    { "type": "ChatResponse", "data": { "content": "..." } }
    ```
- 连接生命周期：
  - 当前端发送 `FinishSession` 后，后端向豆包发送 FinishSession，但不关闭连接，等待下一次 StartSession。
  - 当前端 WebSocket 断开时，后端向豆包发送 FinishConnection 并关闭底层连接。

#### 4.3.4 StartSession 固定参数

后端在接到前端 StartSession 消息后，必须组装如下 JSON 发送给豆包：

```json
{
  "tts": {
    "speaker": "vv",
    "audio_config": {
      "format": "pcm_s16le",
      "sample_rate": 24000,
      "channel": 1
    }
  },
  "asr": {
    "audio_info": {
      "format": "pcm",
      "sample_rate": 16000,
      "channel": 1
    }
  },
  "dialog": {
    "extra": {
      "input_mod": "push_to_talk",
      "model": "2.2.0.0"
    }
  }
}
```

（音色 `speaker` 后续可通过 UpdateConfig 修改）

#### 4.3.5 音色切换
- 在个人应用的设置中，用户可选择默认音色。
- 通话中可通过发送 `UpdateConfig` 事件（Message Type = 0b0001，event=201）动态修改 `tts.speaker`。

#### 4.3.6 历史存储
- 语音电话的每一轮对话（用户语音识别的文本 + 模型回复的文本）**必须**作为两条 Message 存入数据库，`mode='voice'`。

### 4.4 个人应用（点击底部头像）

打开模态框（移动端底部抽屉，PC 端居中卡片），包含以下必须功能：

- **头像**：显示圆形头像，提供上传按钮（文件上传）。上传后存储为 URL（使用 base64 存储到数据库，或集成对象存储）。默认生成随机头像（由 `ui-avatars.com/api` 或相同效果）。
- **昵称**：可编辑文本，保存后更新数据库。
- **设置**：
  - 默认 LLM 模型：下拉选择（从模型列表获取），保存到 `UserSettings.defaultModelId`。
  - 默认语音音色：下拉选择（固定列表：vv, xiaohe, yunzhou, xiaotian 以及官方克隆音色列表），保存到 `UserSettings.ttsSpeaker`。
- **退出登录**：清除 Cookie，跳转到游客模式（不清除游客本地数据）。
- **关于**：显示应用名称、版本号（v1.0.0）、简单使用说明。

---

## 5. 后端 API 详细定义

所有路由前缀 `/api`。

### 5.1 认证

- `POST /auth/register`  
  Body: `{ username, password }`  
  返回: `{ user: { id, username, nickname }, token }`（实际 token 存 cookie）

- `POST /auth/login`  
  Body: `{ username, password }`  
  设置 httpOnly Cookie `token=...`，返回用户信息。

- `POST /auth/logout`  
  清除 Cookie，返回成功。

- `GET /auth/me`  
  返回当前用户信息（根据 Cookie 解析）。

- `PUT /auth/me`  
  Body: `{ nickname, avatarUrl }`  
  更新用户信息。

### 5.2 对话管理（需要登录或游客 ID）

- `GET /conversations?mode=chat|voice&limit=20&offset=0`  
  返回用户对话列表（游客模式需要传递 `x-guest-id` 头）。  
  响应: `{ items: Conversation[], total: number }`

- `POST /conversations`  
  Body: `{ mode, title?, modelId? }`  
  创建新对话，返回 `Conversation`。

- `GET /conversations/:id/messages?limit=50&offset=0`  
  返回消息列表。

- `POST /conversations/:id/messages`  
  Body: `{ role, content }`  
  保存单条消息（用于手动保存）。

- `PUT /conversations/:id`  
  Body: `{ title }`  
  更新对话标题。

- `DELETE /conversations/:id`  
  删除对话及消息。

- `POST /conversations/merge-local`  
  登录后调用，Body: `{ conversations: [...], messages: [...] }`  
  合并本地数据到云端（去重）。

### 5.3 LLM 流式聊天

- `POST /chat/stream`  
  Body: `{ conversationId, modelId, messages: [{role, content}] }`  
  Content-Type: text/event-stream  
  每个事件格式: `data: {"delta": "文字", "done": false}\n\n`，最后发送 `data: {"done": true}\n\n`。  
  后端实时调用 OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`)，携带 API Key（环境变量），使用 `stream: true`。

### 5.4 模型列表

- `GET /models`  
  从 OpenRouter 获取：`https://openrouter.ai/api/v1/models`，缓存 1 小时。  
  返回格式：`{ models: [{ id, name, description }] }`

### 5.5 语音电话 WebSocket

- 端点：`/voice/ws`  
  前端连接此 WebSocket 后，后端进行上述代理逻辑。

---

## 6. UI/UX 强制细节

### 6.1 色彩与字体
- 全局背景：`#e6f7ff`
- 卡片背景：白色 `#ffffff`
- 主按钮：`#1890ff`，悬停加深为 `#0c73c2`
- 文字：主体 `#1f1f1f`，次要 `#8c8c8c`
- 圆角：按钮 `8px`，卡片 `12px`
- 字体：系统默认（SF Pro / Roboto）

### 6.2 聊天界面
- 消息气泡：用户气泡背景 `#1890ff`，白色文字，右对齐；助手气泡背景 `#f0f2f5`，深色文字，左对齐。
- 消息列表自动滚动到底部（新消息时）。
- 加载状态：三点跳动动画（三个灰色圆点依次变亮）。
- 错误提示：使用 toast 通知（位于顶部，3 秒消失）。

### 6.3 语音电话界面
- 大按钮下方显示当前状态：`聆听中...` / `处理中...` / `说话中...`。
- 音量指示器（麦克风输入音量大小，通过 `getUserMedia` 的 `AnalyserNode` 实现）。
- 按住按钮时增加触感反馈（如振动，仅 HTTPS 支持）。

### 6.4 响应式断点
- 手机：`< 768px`，抽屉全宽 80%，按钮圆形直径 80px。
- 平板/PC：`>= 768px`，抽屉宽度 400px，聊天区最大宽度 800px 居中，语音按钮 100px。

---

## 7. 非功能性要求

- **性能**：首次加载时间 < 3s（4G 网络），消息发送到首字延迟 < 500ms（chat 模式）。
- **安全性**：所有 API 需验证 JWT（或游客 ID）；OpenRouter 与豆包密钥仅在后端环境变量；数据库密码使用环境变量。
- **可部署性**：提供 `docker-compose.yml` 文件（PostgreSQL + 应用），附带 README 描述环境变量配置。
- **浏览器支持**：Chrome 90+, Safari 14+, Edge 90+（移动端和桌面端）。

---

## 8. 实现优先级（全部为必须）

所有章节描述的功能必须在最终交付中**完整实现**，不存在“可选”或“P1/P2”优先级区分。特别是语音电话必须完整工作（包括二进制协议、音频采集和播放、打断等）。

---