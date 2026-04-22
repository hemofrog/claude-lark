import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    ReplyMessageRequest,
    ReplyMessageRequestBody,
)
from config import FEISHU_APP_ID, FEISHU_APP_SECRET

feishu_client = lark.Client.builder().app_id(FEISHU_APP_ID).app_secret(FEISHU_APP_SECRET).build()


async def send_message(chat_id: str, text: str) -> str | None:
    """发送消息到飞书群/会话，返回 message_id"""
    req = CreateMessageRequest.Builder() \
        .content(CreateMessageRequestBody.ContentBuilder()
                 .text(text)
                 .build()) \
        .receive_id_mode(1) \
        .receive_id(chat_id) \
        .build()

    resp = feishu_client.im.v1.message.create(req)
    if not resp.success():
        print(f"发送消息失败: {resp.code}, {resp.msg}")
        return None
    return resp.data.message_id


async def reply_message(message_id: str, text: str):
    """回复飞书消息"""
    req = ReplyMessageRequest.Builder() \
        .content(ReplyMessageRequestBody.ContentBuilder()
                 .text(text)
                 .build()) \
        .build()

    resp = feishu_client.im.v1.message.reply(message_id, req)
    if not resp.success():
        print(f"回复消息失败: {resp.code}, {resp.msg}")
