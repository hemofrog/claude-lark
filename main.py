import time
import hashlib
import json
import asyncio
import lark_oapi as lark
from lark_oapi.adapter.fastapi import FastAPIAdapter
from fastapi import FastAPI, Request
from lark_oapi.api.im.v1 import P2ImMessageResource

from config import (
    FEISHU_VERIFICATION_TOKEN,
    FEISHU_ENCRYPT_KEY,
    HOST,
    PORT,
)
from claude_client import generate_response
from feishu_client import send_message, reply_message

app = FastAPI(title="claude-lark")
adapter = FastAPIAdapter(
    token=FEISHU_VERIFICATION_TOKEN,
    encrypt_key=FEISHU_ENCRYPT_KEY,
    handler=FastAppHandler(app),
)

# 简易会话历史存储 (chat_id -> list of messages)
chat_histories: dict[str, list[dict]] = {}


class FastAppHandler:
    """处理飞书事件"""

    async def event_handler(
        self, ctx: lark.ctx.EventContext, request: lark.irp.SubscribeEventReq
    ):
        """事件分发"""
        event = request.event
        event_type = request.header.event_type

        if event_type == "im.message.receive_v1":
            await self._handle_message(ctx, event)

        return ctx.next()

    async def _handle_message(self, ctx, event):
        """处理收到的消息"""
        message = event.get("message", {})
        chat_id = message.get("chat_id", "")
        msg_type = message.get("type", "")
        message_id = message.get("message_id", "")

        # 只处理文本消息，且忽略机器人自己的消息
        sender = message.get("sender", {}).get("sender_id", {})
        if msg_type != "text" or sender.get("user_id") or sender.get("app_id"):
            return

        text = message.get("content", "{}")
        if isinstance(text, str):
            text = json.loads(text)
        user_message = text.get("text", "").strip().lstrip("@Claude").strip()

        if not user_message:
            return

        # 读取会话历史
        history = chat_histories.get(chat_id, [])[-10:]  # 保留最近10轮

        # 调用 Claude 生成回复
        reply_text = await generate_response(user_message, history)

        # 更新会话历史
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply_text})
        chat_histories[chat_id] = history

        # 回复消息
        await reply_message(message_id, reply_text)


# 飞书事件订阅路由
@app.api_route("/event", methods=["GET", "POST"])
async def feishu_event(request: Request):
    return await adapter.handle(request)


# 健康检查
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "claude-lark"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
