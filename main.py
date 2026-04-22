import json
import asyncio
import lark_oapi as lark
from lark_oapi.im.p2.message_reader import IrpMessageReader
from lark_oapi.im.p2.event_callback import IEventCallback

from config import FEISHU_APP_ID, FEISHU_APP_SECRET
from claude_client import generate_response
from feishu_client import reply_message

# 简易会话历史存储 (chat_id -> list of messages)
chat_histories: dict[str, list[dict]] = {}

# 最小 FastAPI app（保持进程存活 + 健康检查）
from fastapi import FastAPI
app = FastAPI(title="claude-lark")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "claude-lark"}


class MessageHandler(IEventCallback):
    """处理飞书消息事件"""

    async def on_event(self, ctx: lark.ctx.IrpContext, event: bytes):
        event_body = json.loads(event)
        event_type = event_body.get("header", {}).get("event_type", "")

        if event_type == "im.message.receive_v1":
            await self._handle_message(ctx, event_body)

    async def _handle_message(self, ctx, event):
        """处理收到的消息"""
        message = event.get("message", {})
        chat_id = message.get("chat_id", "")
        msg_type = message.get("type", "")
        message_id = message.get("message_id", "")

        # 忽略机器人自己的消息
        sender = message.get("sender", {}).get("sender_id", {})
        if sender.get("user_id") or sender.get("app_id"):
            return

        if msg_type != "text":
            return

        text = message.get("content", "{}")
        if isinstance(text, str):
            text = json.loads(text)
        user_message = text.get("text", "").strip().lstrip("@Claude").strip()

        if not user_message:
            return

        # 读取会话历史
        history = chat_histories.get(chat_id, [])[-10:]

        # 调用 Claude 生成回复
        reply_text = await generate_response(user_message, history)

        # 更新会话历史
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply_text})
        chat_histories[chat_id] = history

        # 回复消息
        await reply_message(message_id, reply_text)


async def run():
    handler = MessageHandler()
    message_reader = IrpMessageReader(
        app_id=FEISHU_APP_ID,
        app_secret=FEISHU_APP_SECRET,
        event_callback=handler,
    )

    print("正在连接飞书长连接服务...")
    await message_reader.start()
    print("已连接，等待消息...")

    # 保持运行
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    from config import HOST, PORT
    import uvicorn

    print("正在连接飞书长连接服务...")

    async def main():
        handler = MessageHandler()
        message_reader = IrpMessageReader(
            app_id=FEISHU_APP_ID,
            app_secret=FEISHU_APP_SECRET,
            event_callback=handler,
        )
        server = uvicorn.Server(
            uvicorn.Config(
                app, host=HOST, port=PORT, log_level="warning"
            )
        )
        server_task = asyncio.create_task(server.serve())
        await message_reader.start()
        await server_task

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n已停止")
