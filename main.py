import html
import logging
import re
import asyncio
import time
from random import choice
from interstellar import *
from telegram import Update, Bot
from pyrogram import Client, filters
from pyrogram.types import Message
from telegram.utils.helpers import escape_markdown, mention_html
from telegram.utils.helpers import mention_markdown
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config import LOGGER, MONGO_URI, DB_NAME, TELEGRAM_TOKEN, OWNER_ID, SUDO_ID, BOT_NAME, SUPPORT_ID, API_ID, API_HASH

app = Client("AutoDelete", bot_token=TELEGRAM_TOKEN, api_id=API_ID, api_hash=API_HASH)
print("INFO: ʙɪʟʟᴀ ɢᴜᴀʀᴅɪᴀɴ ɪs ᴏɴ ᴡᴀʏ")
app.start()
bot = app
# Initialize your Pyrogram Client your bot's ID
# Define the text variables
texts = {
    "sudo_5": "Current Sudo Users:\n",
    "sudo_6": "Other Sudo Users:\n",
    "sudo_7": "No sudo users found."
}

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define StartTime at the beginning of the script
StartTime = time.time()

# MongoDB initialization
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db['users']

# Define a list to store sudo user IDs
sudo_users = SUDO_ID.copy()  # Copy initial SUDO_ID list
sudo_users.append(OWNER_ID)  # Add owner to sudo users list initially

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time
def help(update: Update, context: CallbackContext):
    user = update.effective_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
   
    
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_text(
                PM_START_TEXT.format(escape_markdown(first_name), (PM_START_IMG), BOT_NAME),                              
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_photo(
            PM_START_IMG,
            reply_markup=InlineKeyboardMarkup(buttons),
            caption="ʙɪʟʟᴀ ᴇᴅɪᴛ ɢᴜᴀʀᴅɪᴀɴ ɪs ᴀʟɪᴠᴇ ʙᴀʙʏ!\n<b>ᴜᴘᴛɪᴍᴇ :</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )

def get_user_id(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /id <username>")
        return

    username = context.args[0]
    if not username.startswith('@'):
        update.message.reply_text("Please provide a valid username starting with '@'.")
        return
    try:
        user = context.bot.get_chat(username)
        user_id = user.id
        update.message.reply_text(f"User ID of {username} is {user_id}.")
    except Exception as e:
        update.message.reply_text(f"Failed to get user ID: {e}")
        logger.error(f"get_user_id error: {e}")


def check_edit(update: Update, context: CallbackContext):
    bot: Bot = context.bot

    # Check if the update is an edited message
    if update.edited_message:
        edited_message = update.edited_message
        
        # Get the chat ID and message ID
        chat_id = edited_message.chat_id
        message_id = edited_message.message_id
        
        # Get the user who edited the message
        user_id = edited_message.from_user.id
        
        # Create the mention for the user
        user_mention = f"<a href='tg://user?id={user_id}'>{html.escape(edited_message.from_user.first_name)}</a>"
        
        # Delete the message if the editor is not the owner
        if user_id not in sudo_users:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            
            # Send a message notifying about the deletion
            bot.send_message(chat_id=chat_id, text=f"{user_mention} Jᴜsᴛ ᴇᴅɪᴛᴇᴅ ᴀ ᴍᴇssᴀɢᴇ, ɪ ʜᴀᴠᴇ ᴅᴇʟᴇᴛᴇᴅ ʜɪs ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ.", parse_mode='HTML')


def add_sudo(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if the user is the owner
    if user.id != OWNER_ID:
        update.message.reply_text("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return
    
    # Check if a username or user ID is provided
    if len(context.args) != 1:
        update.message.reply_text("ᴜsᴀɢᴇ: /addsudo <username or user ID>")
        return
    
    sudo_user = context.args[0]
    
    # Resolve the user ID from username if provided
    try:
        sudo_user_obj = context.bot.get_chat_member(chat_id=chat_id, user_id=sudo_user)
        sudo_user_id = sudo_user_obj.user.id
    except Exception as e:
        update.message.reply_text(f"ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇsᴏʟᴠᴇ ᴜsᴇʀ: {e}")
        return
    
    # Add sudo user ID to the list if not already present
    if sudo_user_id not in sudo_users:
        sudo_users.append(sudo_user_id)
        update.message.reply_text(f"ᴀᴅᴅᴇᴅ {sudo_user_obj.user.username} ᴀs ᴀ sᴜᴅᴏ ᴜsᴇʀ.")
    else:
        update.message.reply_text(f"{sudo_user_obj.user.username} ɪs ᴀʟʀᴇᴀᴅʏ ᴀ sᴜᴅᴏ ᴜsᴇʀ.")


def sudo_list(update: Update, context: CallbackContext):
    # Check if the user is the owner
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("ʏᴏᴜ ᴅᴏɴ'ᴛ  ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    # Prepare the response message with SUDO_ID users
    text = "ʟɪsᴛ ᴏғ sᴜᴅᴏ ᴜsᴇʀs:\n"
    count = 1
    smex = 0

    # Add the owner
    try:
        owner = context.bot.get_chat(OWNER_ID)
        owner_mention = mention_markdown(OWNER_ID, owner.first_name)
        text += f"{count} {owner_mention}\n"
    except Exception as e:
        update.message.reply_text(f"Failed to get owner details: {e}")

    # Add other sudo users
    for user_id in SUDO_ID:
        if user_id != SUDO_ID:
            try:
                user = context.bot.get_chat(user_id)
                user_mention = mention_markdown(user_id, user.first_name)
                if smex == 0:
                    smex += 1
                count += 1                
                text += f"{count} {user_mention}\n"
            except Exception as e:
                update.message.reply_text(f"Failed to get user details for user_id {user_id}: {e}")

    if not text.strip():
        update.message.reply_text("No sudo users found.")
    else:
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# MongoDB collection for authorized users
authorized_users_collection = db['authorized_users']

# Add the /auth command to authorize a user
def auth(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    reply_message = update.message.reply_to_message
    username = context.args[0] if len(context.args) > 0 else None
    
    if not username and not reply_message:
        update.message.reply_text("Usage: /auth <@username> or reply to a message.")
        return
    
    if reply_message:
        user_to_auth = reply_message.from_user
    elif username:
        try:
            user_to_auth = context.bot.get_chat(username)
        except Exception as e:
            update.message.reply_text(f"Failed to find user {username}: {e}")
            return

    user_id = user_to_auth.id

    # Check if the user is already authorized
    if authorized_users_collection.find_one({"user_id": user_id}):
        update.message.reply_text(f"{user_to_auth.first_name} is already authorized.")
        return

    # Add to the database
    try:
        authorized_users_collection.insert_one({"user_id": user_id, "username": user_to_auth.username, "first_name": user_to_auth.first_name})
        update.message.reply_text(f"{user_to_auth.first_name} has been authorized.")
    except DuplicateKeyError:
        update.message.reply_text(f"{user_to_auth.first_name} is already in the database.")

# Add the /unauth command to unauthorize a user
def unauth(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    reply_message = update.message.reply_to_message
    username = context.args[0] if len(context.args) > 0 else None
    
    if not username and not reply_message:
        update.message.reply_text("Usage: /unauth <@username> or reply to a message.")
        return
    
    if reply_message:
        user_to_unauth = reply_message.from_user
    elif username:
        try:
            user_to_unauth = context.bot.get_chat(username)
        except Exception as e:
            update.message.reply_text(f"Failed to find user {username}: {e}")
            return

    user_id = user_to_unauth.id

    # Check if the user is authorized
    if not authorized_users_collection.find_one({"user_id": user_id}):
        update.message.reply_text(f"{user_to_unauth.first_name} is not authorized.")
        return

    # Remove from the database
    authorized_users_collection.delete_one({"user_id": user_id})
    update.message.reply_text(f"{user_to_unauth.first_name} has been unauthorized.")

# Modify the check_edit function to avoid deleting messages from authorized users or admins
def check_edit(update: Update, context: CallbackContext):
    bot: Bot = context.bot

    # Check if the update is an edited message
    if update.edited_message:
        edited_message = update.edited_message
        
        # Get the chat ID and message ID
        chat_id = edited_message.chat_id
        message_id = edited_message.message_id
        
        # Get the user who edited the message
        user_id = edited_message.from_user.id
        
        # Create the mention for the user
        user_mention = f"<a href='tg://user?id={user_id}'>{html.escape(edited_message.from_user.first_name)}</a>"
        
        # Check if the user is authorized or admin
        if user_id not in sudo_users and not authorized_users_collection.find_one({"user_id": user_id}):
            # Delete the message if the user is neither authorized nor an admin
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            
            # Send a message notifying about the deletion
            bot.send_message(chat_id=chat_id, text=f"{user_mention} Just edited a message, I have deleted his edited message.", parse_mode='HTML')

# Register the sudo_list command hand
def send_stats(update: Update, context: CallbackContext):
    user = update.effective_user
    
    # Check if the user is the owner
    if user.id != OWNER_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    try:
        # Fetch all users who have interacted with the bot
        users_count = users_collection.count_documents({})
        
        # Fetch all unique chat IDs the bot is currently in
        chat_count = chats_collection.count_documents({})
        
        # Prepare the response message
        stats_msg = f"Total Users: {users_count}\n"
        stats_msg += f"Total Chats: {chat_count}\n"
        
        update.message.reply_text(stats_msg)
        
    except Exception as e:
        logger.error(f"Error in send_stats function: {e}")
        update.message.reply_text("Failed to fetch statistics.")
 
def clone(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if the user is the owner
    if user.id != OWNER_ID:
        update.message.reply_text("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴍᴅ.")
        return

    # Get the bot token from the command
    if len(context.args) != 1:
        update.message.reply_text("𝗨𝘀𝗮𝗴𝗲: /clone <Your Bot Token>")
        return

    new_bot_token = context.args[0]

    try:
        # Create a new bot instance
        new_bot = Bot(token=new_bot_token)
        new_bot_info = new_bot.get_me()

        # Clone all handlers from the main bot to the new bot
        clone_updater = Updater(token=new_bot_token, use_context=True)
        clone_dispatcher = clone_updater.dispatcher

        # Add existing handlers to the cloned bot
        clone_dispatcher.add_handler(CommandHandler("start", start))
        clone_dispatcher.add_handler(MessageHandler(Filters.update.edited_message, check_edit))
        clone_dispatcher.add_handler(CommandHandler("addsudo", add_sudo))
        clone_dispatcher.add_handler(CommandHandler("sudolist", sudo_list))
        clone_dispatcher.add_handler(CommandHandler("stats", send_stats))
        clone_dispatcher.add_handler(CommandHandler("clone", clone))

        # Start the cloned bot
        clone_updater.start_polling()

        update.message.reply_text(
            f"sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴏɴᴇᴅ ᴛʜᴇ ʙᴏᴛ {new_bot_info.username} ({new_bot_info.id})."
        )

    except Exception as e:
        update.message.reply_text(f"𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗰𝗹𝗼𝗻𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁: {e}")

# Command handler for /getid
def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:
        if msg.reply_to_message and msg.reply_to_message.forward_from:
            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"<b>ᴛᴇʟᴇɢʀᴀᴍ ɪᴅ:</b>,"
                f"• {html.escape(user2.first_name)} - <code>{user2.id}</code>.\n"
                f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

        else:
            user = bot.get_chat(user_id)
            msg.reply_text(
                f"{html.escape(user.first_name)}'s ɪᴅ ɪs <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

    else:
        if chat.type == "private":
            msg.reply_text(
                f"ʏᴏᴜʀ ᴜsᴇʀ ɪᴅ ɪs <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )

        else:
            msg.reply_text(
                f"ᴛʜɪs ɢʀᴏᴜᴩ's ɪᴅ ɪs <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )

@app.on_message(filters.command("id"))
async def userid(client, message):
    chat = message.chat
    your_id = message.from_user.id
    message_id = message.message_id
    reply = message.reply_to_message

    text = f"**Message ID:** `{message_id}`\n"
    text += f"**Your ID:** `{your_id}`\n"
    
    if not message.command:
        message.command = message.text.split()

    if len(message.command) == 2:
        try:
            split = message.text.split(None, 1)[1].strip()
            user_id = (await client.get_users(split)).id
            text += f"**User ID:** `{user_id}`\n"
        except Exception:
            return await eor(message, text="This user doesn't exist.")

    text += f"**Chat ID:** `{chat.id}`\n\n"
    if not getattr(reply, "empty", True):
        id_ = reply.from_user.id if reply.from_user else reply.sender_chat.id
        text += (
            f"**Replied Message ID:** `{reply.message_id}`\n"
        )
        text += f"**Replied User ID:** `{id_}`"

    await eor(
        message,
        text=text,
        disable_web_page_preview=True,
        parse_mode="md",
            )

# Function to send message to SUPPORT_ID group


def main():

    if SUPPORT_ID is not None and isinstance(SUPPORT_ID, str):
        try:
            dispatcher.bot.sendphoto(
                f"{SUPPORT_ID}",
                photo=PM_START_IMG,               
                caption=f"""
ʜᴇʟʟᴏ ɪ ᴀᴍ sᴛᴀʀᴛᴇᴅ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ𝘀 ! ɪ"ᴍ ᴅᴇᴠʟᴏᴘᴇᴅ ʙʏ @ifeelraam""",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Unauthorized:
            LOGGER.warning(
                f"Bot isn't able to send message to {SUPPORT_ID}, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)    
    # Create the Updater and pass it your bot's token
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.update.edited_message, check_edit))
    dispatcher.add_handler(CommandHandler("addsudo", add_sudo))
    dispatcher.add_handler(CommandHandler("sudolist", sudo_list))
    dispatcher.add_handler(CommandHandler("clone", clone))
    dispatcher.add_handler(CommandHandler("auth", auth))
    dispatcher.add_handler(CommandHandler("unauth", unauth))
    dispatcher.add_handler(CommandHandler("stats", send_stats))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
    # Start the bot



        
