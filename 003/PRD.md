# AI Chat 应用 – 产品需求文档

## 1. 项目目标

开发一个**响应式 Web 应用**，在手机和电脑浏览器上均可流畅运行，提供两种交互模式：
- **LLM Chat**：通过 OpenRouter 调用任意供应商的模型进行文本对话。
- **AI 语音电话**：基于豆包端到端实时语音模型（RealtimeAPI）进行语音对话。

**设计风格**：现代风格，参照 **DeepSeek Web 端/移动端** 的布局与交互方式 – 界面极简，无底部 Tab 栏，左上角呼出历史对话，右上角新建对话，对话框（输入区）始终固定在页面底部。  
**主题色**：紫色系主题 - 背景（`#f5f0ff`）+ 白色卡片，强调色 `#8b5cf6`（紫色）。

---

## 2. 技术栈（固定）

| 层级 | 技术选型 | 用途 |
|------|----------|------|
| 前端 | React 18 + TypeScript + Vite | 构建 UI，强类型 |
| 样式 | TailwindCSS 3 | 响应式、移动优先 |
| 状态管理 | Zustand | 全局状态（用户、对话、UI） |
| 后端运行时 | Python 3.11 + FastAPI | API 服务、WebSocket 代理 |
| 数据库 | PostgreSQL 15 | 用户、对话、消息存储 |
| ORM | SQLAlchemy 2.0 (async) + Alembic | 数据库操作与迁移 |
| 认证 | JWT（存储于 httpOnly Cookie） | 登录状态管理 |
| 游客存储 | IndexedDB（Dexie.js 封装） | 未登录时本地保存对话 |
| 实时语音代理 | FastAPI WebSocket + `websockets` 库 + 二进制协议解析 | 连接豆包 API |
| LLM 代理 | FastAPI 路由 + `httpx` | 调用 OpenRouter REST API |

> **不允许替换上述任何组件**，技术方案以此表为准。

---

## 3. 用户系统与数据存储

### 3.1 认证要求

- **必须实现**注册、登录、退出登录。
- 登录凭证：用户名 + 密码（密码用 `bcrypt` 加密）。
- JWT 有效期 7 天，存入 **httpOnly Secure SameSite Cookie**。
- **必须支持游客模式**：未登录时自动生成访客 ID（保存在 `localStorage`），所有对话写入浏览器 IndexedDB。
- 游客登录后，系统**弹窗询问**“是否将本地对话合并到云端？”，合并规则：依据 `createdAt` 时间戳去重，同一条消息不重复存储。

### 3.2 数据库模型（SQLAlchemy ORM）

以下为 Python 端的模型定义，与最终数据库表结构完全一致：

```python
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func,
    Integer, Boolean, JSON, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship
import uuid

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id            = Column(String, primary_key=True, default=lambda: "u_" + uuid.uuid4().hex[:12])
    username      = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    avatar_url    = Column(String, default="")
    nickname      = Column(String, default="")
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, onupdate=func.now())
    deleted_at    = Column(DateTime, nullable=True)
    conversations = relationship("Conversation", back_populates="user")
    settings      = relationship("UserSettings", back_populates="user", uselist=False)

class UserSettings(Base):
    __tablename__ = "user_settings"
    id               = Column(String, primary_key=True, default=lambda: "us_" + uuid.uuid4().hex[:12])
    user_id          = Column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    theme            = Column(String, default="light")
    default_model_id = Column(String, default="openrouter/auto")
    tts_speaker      = Column(String, default="vv")
    extra_settings   = Column(JSON, default=dict)
    created_at       = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, onupdate=func.now())
    user             = relationship("User", back_populates="settings")

class Conversation(Base):
    __tablename__ = "conversations"
    id              = Column(String, primary_key=True, default=lambda: "c_" + uuid.uuid4().hex[:12])
    user_id         = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    title           = Column(String, nullable=False)
    mode            = Column(String, nullable=False, index=True)  # "chat" 或 "voice"
    model_id        = Column(String, nullable=True)
    summary         = Column(Text, nullable=True)
    is_archived     = Column(Boolean, default=False, index=True)
    created_at      = Column(DateTime, server_default=func.now(), index=True)
    updated_at      = Column(DateTime, onupdate=func.now())
    last_message_at = Column(DateTime, server_default=func.now(), index=True)
    deleted_at      = Column(DateTime, nullable=True)
    messages        = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user            = relationship("User", back_populates="conversations")

    __table_args__ = (
        Index('idx_conv_user_lastmsg', 'user_id', 'last_message_at'),
    )

class Message(Base):
    __tablename__ = "messages"
    id              = Column(String, primary_key=True, default=lambda: "m_" + uuid.uuid4().hex[:12])
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role            = Column(String, nullable=False, index=True)  # "user" 或 "assistant"
    content         = Column(Text, nullable=False)
    model_id        = Column(String, nullable=True)
    tokens_used     = Column(Integer, nullable=True)
    status          = Column(String, default="completed", index=True)  # "sending", "completed", "failed"
    error_message   = Column(Text, nullable=True)
    created_at      = Column(DateTime, server_default=func.now(), index=True)
    deleted_at      = Column(DateTime, nullable=True)
    conversation    = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index('idx_msg_conv_created', 'conversation_id', 'created_at'),
    )
```

### 3.3 游客本地存储（IndexedDB）

- 使用 Dexie.js，数据库名 `AIChatDB`，含 `conversations` 和 `messages` 两张表，字段结构与云端一致但不设外键。
- 游客模式下所有操作直接读写 IndexedDB。
- 登录后云端数据优先显示，本地数据保留待合并。

---

## 4. 功能详细要求

### 4.1 全局布局（参考 DeepSeek 设计）

- **无底部 Tab 栏**，页面纯净。
- **左上角**：菜单按钮（☰），点击打开侧边抽屉。
  - 抽屉宽度占屏幕 80%（移动端）/ 400px（桌面端），背景半透明遮罩，点遮罩关闭。
  - 内容：标题“历史对话”，列表按时间分组（今天/昨天/更早），每项显示对话标题、时间、模式图标（💬/🎧）。
  - 支持滑动删除（移动端）或悬浮删除按钮（PC）。
  - 抽屉底部固定用户信息栏：头像 + 昵称（游客显示“游客”），点击打开“个人应用”弹窗。
- **右上角**：“+”按钮/图标，点击按当前模式创建新对话，立即清空消息区域并将焦点移至输入框。
- **主区域**：上下结构 — 中间消息流区域可滚动，**底部固定对话输入区**（Chat 模式）或语音交互区（Voice 模式）。消息列表自动滚动至最新消息。
- 桌面端：内容最大宽度设为 800px 居中；移动端：全宽，输入框与按钮尺寸适配手指操作。

### 4.2 LLM Chat 模式

#### 4.2.1 模型选择器
- 位于底部输入区上方（或顶部栏右侧），显示当前模型别称。
- 弹窗列出可用模型，支持搜索过滤，数据来自 `GET /api/models`。

#### 4.2.2 输入与流式回复
- 输入框采用多行文本区域，固定于页面底部，样式借鉴 DeepSeek 输入框：圆角大卡片、阴影、发送按钮置于框内右侧。
- **多媒体输入支持**：
  - 支持从相册选择图片上传。
  - 支持相机拍摄图片上传。
  - 图片显示在消息气泡中，支持点击放大查看。
- 发送逻辑：
  - 立即显示用户气泡（紫色背景 `#8b5cf6`，右对齐）。
  - **必须使用流式回复**：通过 SSE (`POST /api/chat/stream`) 发送消息，逐字渲染回复。
  - **流式中断机制**：用户可随时点击"停止"按钮中断模型生成，已生成内容保留。
  - **必须支持渲染 Markdown 格式**：
    - 支持完整 CommonMark/GitHub Flavored Markdown 语法。
    - 支持元素：标题、列表、链接、代码块、表格、引用、任务列表、删除线、图片。
    - 数学公式：支持 KaTeX 行内公式（`$...$`）和块级公式（`$$...$$`）。
    - 图表：支持 Mermaid 流程图、时序图、甘特图等。
    - 代码高亮：使用 `highlight.js`，支持常见编程语言（Python、JavaScript、TypeScript、Java、Go、Rust、C++、SQL、Shell 等）。
    - 代码块操作：每个代码块右上角显示"复制"按钮，点击一键复制代码到剪贴板。
- 流结束后保存完整消息到数据库/IndexedDB。

#### 4.2.3 消息操作
- **悬停/长按菜单**：桌面端鼠标悬停、移动端长按消息时显示操作菜单。
- **重新生成**（仅助手消息）：使用相同上下文重新请求模型生成回复，替换原消息。
- **复制**：复制消息文本内容到剪贴板。
- **删除**：删除单条消息，支持确认提示。
- **引用/回复**：引用某条消息进行回复，被引用消息显示在新消息上方（样式：灰色背景，内容截断，点击跳转）。
- **点赞/收藏**（可选）：消息旁显示心形图标，点击标记收藏，收藏消息可在个人中心查看。

#### 4.2.4 搜索功能
- **全局搜索**：
  - 在侧边栏顶部添加搜索框。
  - 支持搜索对话标题和消息内容。
  - 搜索结果按时间倒序排列，高亮匹配关键词。
  - 点击搜索结果直接跳转到对应对话位置。
- **对话内搜索**：
  - 在聊天界面右上角添加搜索按钮。
  - 点击后在消息流上方显示搜索框。
  - 支持实时搜索当前对话内的消息。
  - 显示匹配数量，支持上一条/下一条导航。

#### 4.2.5 历史对话管理
- 自动将第一条用户消息截取前 30 字符作为标题，可后续修改。
- 支持分页加载历史消息（每页 50 条），滚动顶部触发加载更早记录。
- 删除对话同步清除关联消息。

#### 4.2.6 触摸手势（移动端）
- **下拉刷新**：在消息列表顶部下拉触发刷新，显示最新消息。
- **长按菜单**：长按消息气泡显示操作菜单（重新生成、复制、删除等）。
- **侧滑返回**：从屏幕左侧边缘向右滑动关闭侧边抽屉或返回上一级。
- **点击空白处**：点击消息区域空白处关闭键盘和菜单。

### 4.3 AI 语音电话模式

#### 4.3.1 架构与连接
- 前端 WebSocket 连接至 `ws://<domain>/api/voice/ws`。
- 后端通过 `websockets` 库连接豆包服务 `wss://openspeech.bytedance.com/api/v3/realtime/dialogue`，并携带固定 Headers：
  ```
  X-Api-App-Id: <环境变量>
  X-Api-Access-Key: <环境变量>
  X-Api-Resource-Id: volc.speech.dialog
  X-Api-App-Key: PlgvMymc7f3tQnJ6
  ```
- 后端**必须完整实现**豆包二进制协议（帧头4字节，版本1，无压缩，JSON 序列化），按文档 2.2 节解析和封装。

#### 4.3.2 前端交互（UI）
- 底部固定区域：一个大圆形按钮（直径80px 移动端/100px 桌面端），显示“按住 说话”。
- 按钮下方展示实时字幕（ASR 识别文本与模型回答文本）。
- 交互模式 `push_to_talk`：按住录音，松开结束并发送 `EndASR`。
- 音频播放采用 Web Audio API 队列，支持打断（发送 `ClientInterrupt` 并清空队列）。
- 状态提示：聆听中… / 处理中… / 说话中…，同时显示麦克风音量指示条。

#### 4.3.3 后端代理详细要求
- 前端发来的消息分为文本控制消息（type=0b0001）和音频数据（type=0b0010），需按照豆包协议重新打包发送。
- 豆包返回的二进制帧解析后，以精简 JSON 格式推送给前端：
  ```json
  {"type": "TTSResponse", "data": "<base64 audio>"}
  {"type": "ASRResponse", "data": {"results": [...]}}
  {"type": "ChatResponse", "data": {"content": "..."}}
  ```
- 会话管理：前端发送 `FinishSession` 后不关闭连接，可复用；前端 WebSocket 断开则发送 `FinishConnection` 并关闭豆包连接。

#### 4.3.4 StartSession 固定参数
后端代理在收到前端 StartSession 消息后，向豆包发送的 JSON 配置仍按原要求，默认音色 `speaker: "vv"`。

#### 4.3.5 音色切换
- 用户可通过个人设置更换默认音色，或在通话中动态发送 `UpdateConfig` 消息修改 `tts.speaker`。

#### 4.3.6 历史存储
每一轮完整交互（用户语音识别文本 + 助手回复文本）作为两条 Message 存入数据库，`mode='voice'`。

### 4.4 个人应用（点击头像区域）

弹窗（移动端底部抽屉，PC 端居中卡片）含：
- 头像上传（Base64 存入数据库或对象存储），默认生成渐变头像。
- 昵称编辑。
- 默认 LLM 模型选择。
- 默认 TTS 音色选择（vv, xiaohe, yunzhou, xiaotian 及官方克隆音色）。
- 退出登录（清除 Cookie 并回到游客模式）。
- 关于信息（版本 v1.0.0）。

---

## 5. 后端 API 详细定义（FastAPI）

所有接口前缀 `/api`，采用 Pydantic 模型进行请求/响应校验。

### 5.1 认证
- `POST /auth/register` – 注册，设置 Cookie。
- `POST /auth/login` – 登录，设置 httpOnly Cookie。
- `POST /auth/logout` – 清除 Cookie。
- `GET /auth/me` – 获取当前用户信息。
- `PUT /auth/me` – 更新昵称、头像。

### 5.2 对话管理
- `GET /conversations` – 支持游客（通过 Header `x-guest-id`）。
- `POST /conversations` – 创建新对话。
- `GET /conversations/{id}/messages` – 分页获取消息。
- `POST /conversations/{id}/messages` – 手动保存消息（一般由流结束后调用）。
- `PUT /conversations/{id}` – 修改标题。
- `DELETE /conversations/{id}` – 删除对话及关联消息（软删除）。
- `POST /conversations/merge-local` – 合并本地数据到云端。
- `GET /conversations/search` – 全局搜索对话和消息。

### 5.3 消息管理
- `POST /messages/{id}/regenerate` – 重新生成助手消息。
- `DELETE /messages/{id}` – 删除单条消息（软删除）。

### 5.4 LLM 流式聊天
- `POST /chat/stream` – SSE 响应，后端使用 `httpx` 流式请求 OpenRouter，将增量 token 推送至前端。
- 支持流式中断：前端关闭连接时，后端终止请求。

### 5.5 文件上传
- `POST /upload/image` – 上传图片，返回图片 URL。

### 5.6 模型列表
- `GET /models` – 从 OpenRouter 获取并缓存 1 小时。

### 5.5 语音电话 WebSocket
- `WS /voice/ws` – FastAPI WebSocket 端点，实现前述代理与二进制协议解析。

---

## 6. UI/UX 强制细节（强化版）

### 6.1 色彩与字体
- 背景：`#f5f0ff`（浅紫背景）；卡片：`#ffffff`；主按钮：`#8b5cf6`（紫色，hover `#7c3aed`）；文字主色 `#1f1f1f`，次要 `#8c8c8c`。
- 圆角：按钮 8px，卡片 12px；字体：系统默认。

### 6.2 聊天界面
- 用户气泡：紫底（`#8b5cf6`）白字右对齐；助手气泡：灰底深字左对齐。
- **对话输入区固定于页面底部**，样式为一悬浮圆角大卡片，内部包含多行文本域和发送按钮，模仿 DeepSeek 的输入设计。
- **消息滚动区域**：
  - 支持自然流畅的滑动查看历史记录，滚动性能平滑无卡顿。
  - 新消息自动滚动到底。
  - 加载历史消息时不跳动（保持当前滚动位置）。
- **快捷回底按钮**：
  - 当用户向上滚动查看历史消息时，在右下角显示一个悬浮圆形按钮（带有向下箭头图标 ↓）。
  - 点击该按钮立即平滑滚动到最新消息处，按钮随之隐藏。
  - 按钮样式：紫色背景（`#8b5cf6`），白色图标，圆角 50%，带轻微阴影。
- 加载状态用三点跳动动画，错误用顶部 toast 提示（3秒消失）。
- **Markdown 渲染**：助手消息区域使用专门的 Markdown 渲染组件，支持代码高亮、数学公式（可选）等。

### 6.3 语音电话界面
- 大按钮固定于底部，附带状态文字和音量指示。
- 按住按钮有触感反馈（支持振动）。

### 6.4 响应式断点
- 移动设备（< 768px）：抽屉宽 80%，语音按钮 80px，输入框全宽。
- 桌面（≥ 768px）：抽屉宽 400px，聊天容器最大宽 800px 居中，语音按钮 100px。

---

## 7. 非功能性要求

- **性能**：首次加载 < 3s，Chat 首字延迟 < 500ms。
- **安全性**：JWT 鉴权（或游客ID）；密钥仅存于后端环境变量；数据库密码环境变量。
- **可部署性**：提供 `Dockerfile` 及 `docker-compose.yml`（含 PostgreSQL 和应用服务），与详细环境变量说明。
- **浏览器支持**：Chrome 90+，Safari 14+，Edge 90+。

---

## 8. 实现优先级

所有章节描述的功能**必须全部完整实现**，语音电话的二进制协议、音频采集播放、打断机制等均须正常工作，不可裁剪。