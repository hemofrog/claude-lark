# claude-lark

将 Claude AI 接入飞书（Lark）的机器人服务。

## 功能

- 飞书长连接模式接收消息（无需公网 IP）
- 调用 Claude API 生成回复
- 多轮对话上下文（保留最近 10 轮）
- 支持群聊 @机器人 交互

## 快速开始

### 1. 飞书开放平台配置

1. 访问 [飞书开放平台](https://open.feishu.cn/app)，创建企业内部应用
2. 获取 **App ID** 和 **App Secret**
3. **事件订阅 → 订阅方式选择"长连接"**
4. 添加事件订阅：`im.message.receive_v1`（接收消息）
5. 将应用添加到目标群聊

### 2. 安装

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
copy .env.example .env
```

编辑 `.env` 文件：

```env
# 飞书应用凭证
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Claude API Key（从 https://console.anthropic.com/ 获取）
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 可选配置
CLAUDE_MODEL=claude-sonnet-4-20250514
SYSTEM_PROMPT=你是一个友好的AI助手。
```

### 4. 启动

```bash
python main.py
```

连接成功后显示：`已连接，等待消息...`

## 使用

在飞书群聊中 @机器人 发送消息即可。

## 变更记录

### 2026-04-22
- 从 IRP 长连接模式切换回 WebSocket 长连接模式，使用 `EventDispatcherHandlerBuilder` 和 `Client`
- 重构消息处理逻辑，使用同步函数在后台线程运行
- 新增 FastAPI `/health` 健康检查接口
- 依赖版本约束从精确 pin 改为范围约束

## 技术栈

- Python + FastAPI
- 飞书长连接（lark-oapi SDK，WebSocket 模式）
- Anthropic Claude API
