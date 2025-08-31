import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from message_manager import MessageManager
from database import get_db
from config import settings

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not provided. Bot will not be initialized.")
            self.application = None
        else:
            self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            self._setup_handlers()
        self.user_states = {}
    
    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("next", self.next_message_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_message = """
🤖 Welcome to the Answering Agent Bot!

Commands:
/next - Process next message in queue

The bot will help you manage and respond to messages from various platforms!
        """
        await update.message.reply_text(welcome_message)
    
    async def next_message_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db = next(get_db())
        message_manager = MessageManager(db)
        
        message = message_manager.get_next_message()
        if not message:
            await update.message.reply_text("✅ No pending messages in queue!")
            return
        
        await self._show_message_for_processing(update, context, message, message_manager)
    
    async def _show_message_for_processing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message, message_manager):
        message_manager.mark_message_processing(message.id)
        
        message_text = f"""
📨 New Message from {message.platform.title()}

👤 From: {message.sender}
📝 Content: {message.content[:200]}...

What would you like to do?
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🤖 Generate Response", callback_data=f"generate_{message.id}"),
                InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{message.id}")
            ],
            [
                InlineKeyboardButton("✍️ Answer Manually", callback_data=f"manual_{message.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        db = next(get_db())
        message_manager = MessageManager(db)
        
        if data.startswith("generate_"):
            message_id = data.split("_")[1]
            await self._handle_generate_response(query, message_id, message_manager)
        elif data.startswith("ignore_"):
            message_id = data.split("_")[1]
            message_manager.mark_message_ignored(message_id)
            await query.edit_message_text("✅ Message ignored. Use /next for next message.")
        elif data.startswith("manual_"):
            message_id = data.split("_")[1]
            self.user_states[query.from_user.id] = {"state": "waiting_manual_response", "message_id": message_id}
            await query.edit_message_text("✍️ Please type your manual response:")
        elif data.startswith("send_"):
            response_id = data.split("_")[1]
            message_manager.mark_response_sent(response_id)
            await query.edit_message_text("✅ Response sent! Use /next for next message.")
        elif data.startswith("edit_"):
            response_id = data.split("_")[1]
            self.user_states[query.from_user.id] = {"state": "waiting_edit_feedback", "response_id": response_id}
            await query.edit_message_text("✏️ Describe how to edit the response:")
    
    async def _handle_generate_response(self, query, message_id: str, message_manager: MessageManager):
        await query.edit_message_text("🤖 Generating AI response...")
        
        response = message_manager.generate_ai_response(message_id)
        if not response:
            await query.edit_message_text("❌ Failed to generate response.")
            return
        
        response_text = f"🤖 Generated Response:\n\n{response.content}\n\nWhat would you like to do?"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Send", callback_data=f"send_{response.id}"),
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{response.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(response_text, reply_markup=reply_markup)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        db = next(get_db())
        message_manager = MessageManager(db)
        
        if state["state"] == "waiting_manual_response":
            message_id = state["message_id"]
            response = message_manager.save_manual_response(message_id, text)
            
            if response:
                response_text = f"✍️ Manual Response:\n\n{response.content}\n\nWhat would you like to do?"
                keyboard = [[InlineKeyboardButton("✅ Send", callback_data=f"send_{response.id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(response_text, reply_markup=reply_markup)
            
            del self.user_states[user_id]
        
        elif state["state"] == "waiting_edit_feedback":
            response_id = state["response_id"]
            improved_response = message_manager.improve_response(response_id, text)
            
            if improved_response:
                response_text = f"✏️ Improved Response:\n\n{improved_response.content}\n\nWhat would you like to do?"
                keyboard = [[InlineKeyboardButton("✅ Send", callback_data=f"send_{improved_response.id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(response_text, reply_markup=reply_markup)
            
            del self.user_states[user_id]
    
    async def notify_new_message(self, platform: str, sender: str, content: str):
        db = next(get_db())
        message_manager = MessageManager(db)
        message_manager.add_message(platform, sender, content)
        
        notification_text = f"🔔 New {platform.title()} message from {sender}: {content[:100]}...\n\nUse /next to process."
        await self.application.bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=notification_text)
    
    def run(self):
        if not self.application:
            logger.warning("Telegram bot not initialized due to missing token.")
            return
        logger.info("Starting Telegram bot...")
        self.application.run_polling()


bot = TelegramBot()
