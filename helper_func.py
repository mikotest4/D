#(©)CodeFlix_Bots
#rohit_1888 on Tg #Dont remove this line

import base64
import re
import asyncio
import time
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import *
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from shortzy import Shortzy
from pyrogram.errors import FloodWait
from database.database import *
from database.db_premium import *
from database.db_super_prime import is_super_prime_user
import logging

# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

#used for cheking if a user is admin ~Owner also treated as admin level
async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id       
        return any([user_id == OWNER_ID, await db.admin_exist(user_id)])
    except Exception as e:
        print(f"! Exception in check_admin: {e}")
        return False

# Enhanced premium checking with automatic cleanup
async def is_premium_user_enhanced(user_id):
    """Enhanced premium check with automatic expiry cleanup"""
    try:
        # First check if user exists in premium collection
        user_exists = await is_premium_user(user_id)
        if not user_exists:
            return False
        
        # Check if premium has expired and auto-remove
        user_data = await collection.find_one({"user_id": user_id})
        if user_data:
            from datetime import datetime
            from pytz import timezone
            
            ist = timezone("Asia/Kolkata")
            current_time = datetime.now(ist)
            expiration_time = datetime.fromisoformat(user_data["expiration_timestamp"]).astimezone(ist)
            
            if expiration_time <= current_time:
                # Auto remove expired user
                await remove_premium(user_id)
                logging.info(f"Auto-removed expired premium user: {user_id}")
                return False
        
        return True
    except Exception as e:
        logging.error(f"Error in enhanced premium check for user {user_id}: {e}")
        return False

# Check if content should be protected for this user
async def should_protect_content(user_id):
    """Check if content should be protected for this user"""
    # Super Prime users can forward/save content
    if await is_super_prime_user(user_id):
        return False
    
    # Regular premium users still have protection
    if await is_premium_user(user_id):
        return True
    
    # Non-premium users have protection
    return True

# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

async def is_subscribed(client, user_id):
    channel_ids = await db.show_channels()

    if not channel_ids:
        return True

    if user_id == OWNER_ID:
        return True

    for cid in channel_ids:
        if not await is_sub(client, user_id, cid):
            # Retry once if join request might be processing
            mode = await db.get_channel_mode(cid)
            if mode == "on":
                await asyncio.sleep(2)  # give time for @on_chat_join_request to process
                if await is_sub(client, user_id, cid):
                    continue
            return False

    return True

# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

async def is_sub(client, user_id, channel_id):
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status
        #print(f"[SUB] User {user_id} in {channel_id} with status {status}")
        return status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        }

    except UserNotParticipant:
        mode = await db.get_channel_mode(channel_id)
        if mode == "on":
            exists = await db.req_user_exist(channel_id, user_id)
            #print(f"[REQ] User {user_id} join request for {channel_id}: {exists}")
            return exists
        return False

    except Exception as e:
        print(f"[SUB] Error checking subscription for {user_id} in {channel_id}: {e}")
        return False

# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

async def not_joined(client, message):
    channels = await db.show_channels()
    if not channels:
        return True

    buttons = []
    for channel_id in channels:
        try:
            chat = await client.get_chat(channel_id)
            if chat.username:
                url = f"https://t.me/{chat.username}"
            else:
                url = f"https://t.me/c/{str(channel_id)[4:]}"
            buttons.append([InlineKeyboardButton(text=chat.title, url=url)])
        except:
            buttons.append([InlineKeyboardButton(text=f"Channel {channel_id}", url=f"https://t.me/c/{str(channel_id)[4:]}")])

    try:
        buttons.append([InlineKeyboardButton(text='♻️ Reload', callback_data='reload')])
        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(first=message.from_user.first_name),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except:
        await message.reply_text(
            text=FORCE_MSG.format(first=message.from_user.first_name),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    return False

# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.b64encode(string_bytes)
    base64_string = base64_bytes.decode("ascii")
    return base64_string

async def decode(base64_string):
    base64_bytes = base64_string.encode("ascii")
    string_bytes = base64.b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_from:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*?)/(\\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.username:
                return msg_id
    else:
        return 0

def get_readable_time(seconds):
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result

def get_exp_time(seconds):
    periods = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{period_value}{period_name}'
    return result

# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    try:
        link = await shortzy.convert(link)
        return link
    except Exception as e:
        print(f"Error in get_shortlink: {e}")
        return link

admin = filters.create(check_admin)
