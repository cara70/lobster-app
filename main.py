import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
import os

# 配置（云端自动读取，不用手动改）
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_LIST = [-1001863386261, -1002077212634]
ADMIN_ID = 5799847245

# 定时群发公告
async def auto_send(context: ContextTypes.DEFAULT_TYPE):
    text = "👋 本群为IT海外求职招聘群，禁止广告、刷单、无关外链，违规将被禁言/踢出，请大家遵守群规！"
    for chat_id in GROUP_LIST:
        await context.bot.send_message(chat_id=chat_id, text=text)

# 新人欢迎
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for user in update.message.new_chat_members:
        name = user.full_name
        await context.bot.send_message(
            chat_id,
            f"🎉 欢迎 {name} 加入本群！\n交流求职招聘相关内容，请勿发布违规信息~"
        )

# 违规词拦截+禁言1小时
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    msg = update.message.text.lower()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    ban_words = ["广告", "刷单", "赌博", "微信", "vx", "兼职", "博彩"]
    if any(word in msg for word in ban_words):
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            until_date=datetime.now().timestamp() + 3600
        )
        await update.message.delete()
        await context.bot.send_message(chat_id, f"⚠️ @{update.effective_user.username} 发布违规内容，已禁言1小时！")

# 踢人命令 /ban
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        await context.bot.ban_chat_member(update.effective_chat.id, target_id)
        await update.message.reply_text("✅ 已移出群聊")

# 解禁命令 /unban
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        await context.bot.unban_chat_member(update.effective_chat.id, target_id)
        await update.message.reply_text("✅ 已解除封禁")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = app.job_queue
    # 每日10点定时发消息
    job_queue.run_daily(auto_send, time=datetime.strptime("10:00", "%H:%M").time())

    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())