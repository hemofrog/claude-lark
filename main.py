import json
import asyncio
import threading
from lark_oapi.ws.client import Client
from lark_oapi.event.dispatcher_handler import EventDispatcherHandlerBuilder

from config import FEISHU_APP_ID, FEISHU_APP_SECRET
from claude_client import generate_response
from feishu_client import reply_message

# 简易会话历史存储 (chat_id -> list of messages)
chat_histories: dict[str, list[dict]] = {}


def handle_message_receive(event):
    """处理飞书消息事件"""
    if not event or not event.Message:
        return

    message = event.Message
    chat_id = message.ChatID or ""
    message_id = message.MessageID or ""
    msg_type = message.MessageType or ""

    # 只处理文本消息
    if msg_type != "text":
        return

    # 忽略机器人自己的消息
    sender = message.Sender or {}
    sender_type = sender.get("sender_id_type", "")
    if sender_type == "app":
        return

    # 解析文本内容
    content = message.Content or "{}"
    if isinstance(content, str):
        content = json.loads(content)
    user_message = content.get("text", "").strip()
    # 去除 @机器人 前缀
    user_message = user_message.lstrip("@").strip()

    if not user_message:
        return

    # 读取会话历史（最近10轮）
    history = chat_histories.get(chat_id, [])[-10:]

    # 调用 Claude 生成回复
    loop = asyncio.new_event_loop()
    try:
        reply_text = loop.run_until_complete(
            generate_response(user_message, history)
        )
    finally:
        loop.close()

    # 更新会话历史
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply_text})
    chat_histories[chat_id] = history

    # 回复消息
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            reply_message(message_id, reply_text)
        )
    finally:
        loop.close()


async def run():
    # 构建事件处理器
    handler = EventDispatcherHandlerBuilder(
        FEISHU_APP_ID, FEISHU_APP_SECRET
    )
    handler.register_p2_im_message_receive_v1(handle_message_receive)

    # 创建 WebSocket 长连接客户端
    ws_client = Client(
        app_id=FEISHU_APP_ID,
        app_secret=FEISHU_APP_SECRET,
        event_handler=handler.build(),
    )

    print("正在连接飞书长连接服务...")
    ws_client.start()
    print("已连接，等待消息...")

    # 保持运行
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    from config import HOST, PORT
    import uvicorn

    # 启动健康检查 HTTP 服务
    from fastapi import FastAPI
    app = FastAPI(title="claude-lark")

    @app.get("/health")
    def health_check():
        return {"status": "ok", "service": "claude-lark"}

    server = uvicorn.Server(
        uvicorn.Config(
            app, host=HOST, port=PORT, log_level="warning"
        )
    )

    async def start_http():
        await server.serve()

    # 在后台线程启动 WebSocket 长连接
    def ws_thread():
        handler = EventDispatcherHandlerBuilder(
            FEISHU_APP_ID, FEISHU_APP_SECRET
        )
        handler.register_p2_im_message_receive_v1(handle_message_receive)
        ws_client = Client(
            app_id=FEISHU_APP_ID,
            app_secret=FEISHU_APP_SECRET,
            event_handler=handler.build(),
        )
        print("正在连接飞书长连接服务...")
        ws_client.start()
        print("已连接，等待消息...")

    thread = threading.Thread(target=ws_thread, daemon=True)
    thread.start()

    # 在主线程启动 HTTP 服务
    asyncio.run(start_http())
