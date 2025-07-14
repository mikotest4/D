from pyrogram import Client, filters
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *
import urllib.parse
import requests
import io

# UPI IDs for payment
UPI_1 = "singhzerotwo@fam"
UPI_2 = "7348433876@mbk"

# Plan details
PLANS = {
    "7days": {"price": 50, "duration": "7 Days", "days": 7},
    "1month": {"price": 130, "duration": "1 Month", "days": 30},
    "3months": {"price": 299, "duration": "3 Months", "days": 90},
    "6months": {"price": 599, "duration": "6 Months", "days": 180},
    "1year": {"price": 999, "duration": "1 Year", "days": 365}
}

# Store pending gift card payments (in production, use proper database)
pending_gift_cards = {}
pending_payments = {}
waiting_for_screenshot = {}  # Track users waiting to send screenshots
waiting_for_gift_card = {}  # Track users waiting to send gift card details

async def generate_upi_qr_external(upi_id, amount, plan_name="Premium"):
    """Generate UPI QR code using external API"""
    try:
        # Create UPI payment URL
        note = f"{plan_name} Premium Plan"
        upi_url = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(note)}&am={amount}&cu=INR&tn={urllib.parse.quote('Premium Payment')}"
        
        # Generate QR Code using external API
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"
        
        print(f"Generated UPI URL: {upi_url}")
        print(f"QR API URL: {qr_api_url}")
        
        # Download QR code image
        response = requests.get(qr_api_url, timeout=10)
        if response.status_code == 200:
            qr_image = io.BytesIO(response.content)
            qr_image.seek(0)
            return qr_image
        else:
            print(f"Failed to generate QR code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data

    if data == "help":
        await query.message.edit_text(
            text=HELP_TXT.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                 InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data='close')]
            ])
        )

    elif data == "about":
        await query.message.edit_text(
            text=ABOUT_TXT.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                 InlineKeyboardButton('ᴄʟᴏꜱᴇ', callback_data='close')]
            ])
        )

    elif data == "start":
        await query.message.edit_text(
            text=START_MSG.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʜᴇʟᴘ", callback_data='help'),
                 InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data='about')]
            ])
        )

    elif data == "premium":
        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo="https://graph.org/file/608d82ad34a92e32d37ce-25e6e6bf08e194f088.jpg",
            caption=(
                f"ʜᴇʟʟᴏ 『{query.from_user.first_name}』❋𝄗⃝🦋 👋\n\n"
                f"ʜᴇʀᴇ ʏᴏᴜ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀꜱʜɪᴘ ᴏꜰ ᴛʜɪꜱ ʙᴏᴛ.\n"
                f"ꜱᴏᴍᴇ ᴘʟᴀɴ ᴀʀᴇ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇᴍ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ.\n"
                f"ɪꜰ ʏᴏᴜ ᴍᴀᴅᴇ ᴛʜᴇ ᴘᴀʏᴍᴇɴᴛ ᴀꜰᴛᴇʀ 11:00 ᴘᴍ, ɪғ ᴛʜᴇ ᴏᴡɴᴇʀ ɪs ᴀᴄᴛɪᴠᴇ ᴛʜᴀɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ᴀᴄᴛɪᴠᴇ sᴏᴏɴ ᴏᴛʜᴇʀᴡɪꜱᴇ, ɪᴛ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ɪɴ ᴛʜᴇ ᴍᴏʀɴɪɴɢ."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("7 Days 50 Rs", callback_data="plan_7days"),
                    InlineKeyboardButton("1 Month 130 Rs", callback_data="plan_1month")
                ],
                [
                    InlineKeyboardButton("3 Month 299 Rs", callback_data="plan_3months"),
                    InlineKeyboardButton("6 Month 599 Rs", callback_data="plan_6months")
                ],
                [
                    InlineKeyboardButton("1 Year 999 Rs", callback_data="plan_1year")
                ],
                [
                    InlineKeyboardButton("🔒 Close", callback_data="close")
                ]
            ])
        )

    # Handle plan selection callbacks
    elif data.startswith("plan_"):
        plan_key = data.split("_")[1]
        plan = PLANS.get(plan_key)
        
        if plan:
            await query.message.edit_caption(
                caption=(
                    f"📋 Selected Plan: {plan['duration']} - ₹{plan['price']}\n\n"
                    f"💳 Please select your payment method:"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("UPI 1", callback_data=f"payment_upi1_{plan_key}"),
                        InlineKeyboardButton("UPI 2", callback_data=f"payment_upi2_{plan_key}")
                    ],
                    [
                        InlineKeyboardButton("Amazon Gift Card", callback_data=f"payment_gift_{plan_key}")
                    ],
                    [
                        InlineKeyboardButton("‹ Back to Plans", callback_data="premium"),
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ])
            )

    # Handle UPI payment method selection
    elif data.startswith("payment_upi1_") or data.startswith("payment_upi2_"):
        parts = data.split("_")
        payment_method = parts[1]
        plan_key = parts[2]
        plan = PLANS.get(plan_key)
        
        if plan:
            upi_id = UPI_1 if payment_method == "upi1" else UPI_2
            
            # Store payment info for screenshot handling
            user_id = query.from_user.id
            pending_payments[user_id] = {
                "plan": plan_key,
                "amount": plan['price'],
                "duration": plan['duration'],
                "upi_method": payment_method,
                "upi_id": upi_id
            }
            
            # Generate QR code
            qr_image = await generate_upi_qr_external(upi_id, plan['price'], plan['duration'])
            
            if qr_image:
                await query.message.delete()
                await client.send_photo(
                    chat_id=query.message.chat.id,
                    photo=qr_image,
                    caption=(
                        f"📝 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:\n"
                        f"1. sᴄᴀɴ ᴛʜᴇ Qʀ ᴄᴏᴅᴇ ᴀʙᴏᴠᴇ ᴏʀ ᴘᴀʏ ᴛᴏ Uᴘɪ ɪᴅ\n"
                        f"2. ᴘᴀʏ ᴇxᴀᴄᴛʟʏ ₹{plan['price']}.\n"
                        f"3. ᴄʟɪᴄᴋ ᴏɴ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ.\n\n"
                        f"ɴᴏᴛᴇ: ɪꜰ ʏᴏᴜ ᴍᴀᴋᴇ ᴘᴀʏᴍᴇɴᴛ ᴀᴛ ɴɪɢʜᴛ ᴀꜰᴛᴇʀ 11 ᴘᴍ ᴛʜᴀɴ ʏᴏᴜ ʜᴀᴠᴇ ᴛᴏ ᴡᴀɪᴛ ꜰᴏʀ ᴍᴏʀɴɪɴɢ ʙᴇᴄᴀᴜsᴇ ᴏᴡɴᴇʀ ɪs sʟᴇᴇᴘɪɴɢ ᴛʜᴀᴛ's ᴡʜʏ ʜᴇ ᴄᴀɴ'ᴛ ᴀᴄᴛɪᴠᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ. ɪꜰ ᴏᴡɴᴇʀ ɪs ᴏɴʟɪɴᴇ ᴛʜᴀɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ᴀᴄᴛɪᴠᴇ ɪɴ ᴀɴ ʜᴏᴜʀ. sᴏ ᴘᴀʏ ᴀᴛ ʏᴏᴜʀ ᴏᴡɴ ʀɪsᴋ ᴀꜰᴛᴇʀ ɴɪɢʜᴛ 11 ᴘᴍ. ᴅᴏɴ'ᴛ ʙʟᴀᴍᴇ ᴏᴡɴᴇʀ."
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid_{user_id}")
                        ],
                        [
                            InlineKeyboardButton("‹ Back to Plans", callback_data="premium"),
                            InlineKeyboardButton("🔒 Close", callback_data="close")
                        ]
                    ])
                )
            else:
                await query.answer("Failed to generate QR code. Please try again.", show_alert=True)

    # Handle "I Have Paid" button
    elif data.startswith("paid_"):
        user_id = int(data.split("_")[1])
        
        if user_id == query.from_user.id and user_id in pending_payments:
            payment_info = pending_payments[user_id]
            
            # Mark user as waiting for screenshot
            waiting_for_screenshot[user_id] = True
            
            await query.message.edit_caption(
                caption=(
                    f"📸 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ\n\n"
                    f"📋 ᴘʟᴀɴ: {payment_info['duration']} - ₹{payment_info['amount']}\n\n"
                    f"📤 sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ɴᴏᴡ.\n"
                    f"🔄 sᴄʀᴇᴇɴsʜᴏᴛ ᴡɪʟʟ ʙᴇ ꜰᴏʀᴡᴀʀᴅᴇᴅ ᴛᴏ ᴏᴡɴᴇʀ ꜰᴏʀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ.\n"
                    f"⚡ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴀꜰᴛᴇʀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("‹ Back to Payment", callback_data=f"payment_{payment_info['upi_method']}_{payment_info['plan']}"),
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ])
            )
        else:
            await query.answer("Invalid payment session. Please start again.", show_alert=True)

    # Handle Amazon Gift Card payment
    elif data.startswith("payment_gift_"):
        plan_key = data.split("_")[2]
        plan = PLANS.get(plan_key)
        
        if plan:
            user_id = query.from_user.id
            pending_gift_cards[user_id] = {
                "plan": plan_key,
                "amount": plan['price'],
                "duration": plan['duration']
            }
            
            # Send text message instead of photo to avoid URL error
            await query.message.edit_caption(
                caption=(
                    f"🎁 ᴀᴍᴀᴢᴏɴ ɢɪꜰᴛ ᴄᴀʀᴅ ᴘᴀʏᴍᴇɴᴛ\n\n"
                    f"📋 ᴘʟᴀɴ: {plan['duration']} - ₹{plan['price']}\n\n"
                    f"📝 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:\n"
                    f"1. ᴘᴜʀᴄʜᴀsᴇ ᴀᴍᴀᴢᴏɴ ɢɪꜰᴛ ᴄᴀʀᴅ ᴡᴏʀᴛʜ ₹{plan['price']}\n"
                    f"2. sᴇɴᴅ ᴛʜᴇ ɢɪꜰᴛ ᴄᴀʀᴅ ᴄᴏᴅᴇ ᴛᴏ ᴀᴅᴍɪɴ\n"
                    f"3. ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴀꜰᴛᴇʀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ\n"
                    f"4. ʏᴏᴜ ʜᴀᴠᴇ ᴛᴏ ʙᴜʏ ᴇxᴀᴄᴛʟʏ ᴀᴍᴀᴢᴏɴ ɢɪꜰᴛ ᴄᴀʀᴅ ᴠᴏᴜᴄʜᴇʀ. ᴏᴛʜᴇʀ ᴄᴀʀᴅs ɴᴏᴛ ᴀᴄᴄᴇᴘᴛᴇᴅ ᴏɴʟʏ ᴀᴍᴀᴢᴏɴ ɢɪꜰᴛ ᴄᴀʀᴅ.\n\n"
                    f"⚠️ ᴍᴀᴋᴇ sᴜʀᴇ ᴛʜᴇ ɢɪꜰᴛ ᴄᴀʀᴅ ᴀᴍᴏᴜɴᴛ ᴍᴀᴛᴄʜᴇs ᴇxᴀᴄᴛʟʏ: ₹{plan['price']}\n"
                    f"‼️ ɢɪꜰᴛ ᴄᴀʀᴅs ᴀʀᴇ ɴᴏɴ-ʀᴇꜰᴜɴᴅᴀʙʟᴇ"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🎁 Send Gift Card", callback_data=f"send_gift_{user_id}")
                    ],
                    [
                        InlineKeyboardButton("‹ Back to Plans", callback_data="premium"),
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ])
            )

    # Handle "Send Gift Card" button
    elif data.startswith("send_gift_"):
        user_id = int(data.split("_")[2])
        
        if user_id == query.from_user.id and user_id in pending_gift_cards:
            gift_card_info = pending_gift_cards[user_id]
            
            # Mark user as waiting for gift card details
            waiting_for_gift_card[user_id] = True
            
            await query.message.edit_caption(
                caption=(
                    f"🎁 sᴇɴᴅ ɢɪꜰᴛ ᴄᴀʀᴅ ᴅᴇᴛᴀɪʟs\n\n"
                    f"📋 ᴘʟᴀɴ: {gift_card_info['duration']} - ₹{gift_card_info['amount']}\n\n"
                    f"📤 ɴᴏᴡ sᴇɴᴅ ᴅɪʀᴇᴄᴛ ʟɪɴᴋ ᴛᴏ ᴄʟᴀɪᴍ ɢɪꜰᴛ ᴄᴀʀᴅ.\n"
                    f"🎫 ɢɪꜰᴛ ᴄᴀʀᴅ ɪᴅ. ᴏʀ ʏᴏᴜ ᴄᴀɴ sᴇɴᴅ sᴄʀᴇᴇɴsʜᴏᴛ\n"
                    f"📸 ᴍᴀᴋᴇ sᴜʀᴇ sᴄʀᴇᴇɴsʜᴏᴛ ɪɴᴄʟᴜᴅᴇᴅ ɢɪꜰᴛ ᴄᴀʀᴅ ʀᴇᴅᴇᴇᴍ ɪᴅ\n\n"
                    f"⚡ ɢɪꜰᴛ ᴄᴀʀᴅ ᴡɪʟʟ ʙᴇ ꜰᴏʀᴡᴀʀᴅᴇᴅ ᴛᴏ ᴏᴡɴᴇʀ ꜰᴏʀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("‹ Back to Payment", callback_data=f"payment_gift_{gift_card_info['plan']}"),
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ])
            )
        else:
            await query.answer("Invalid gift card session. Please start again.", show_alert=True)

    elif data == "close":
        # Remove user from waiting states when closing
        user_id = query.from_user.id
        if user_id in waiting_for_screenshot:
            del waiting_for_screenshot[user_id]
        if user_id in pending_payments:
            del pending_payments[user_id]
        if user_id in waiting_for_gift_card:
            del waiting_for_gift_card[user_id]
        if user_id in pending_gift_cards:
            del pending_gift_cards[user_id]
            
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

    elif data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
            new_mode = "ᴏғғ" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
                [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
            ]
            await query.message.edit_text(
                f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            await query.answer("Failed to fetch channel info", show_alert=True)

    elif data.startswith("rfs_toggle_"):
        cid, action = data.split("_")[2:]
        cid = int(cid)
        mode = "on" if action == "on" else "off"

        await db.set_channel_mode(cid, mode)
        await query.answer(f"Force-Sub set to {'ON' if mode == 'on' else 'OFF'}")

        # Refresh the same channel's mode view
        chat = await client.get_chat(cid)
        status = "🟢 ON" if mode == "on" else "🔴 OFF"
        new_mode = "off" if mode == "on" else "on"
        buttons = [
            [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
            [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
        ]
        await query.message.edit_text(
            f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "fsub_back":
        channels = await db.show_channels()
        buttons = []
        for cid in channels:
            try:
                chat = await client.get_chat(cid)
                mode = await db.get_channel_mode(cid)
                status = "🟢" if mode == "on" else "🔴"
                buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"rfs_ch_{cid}")])
            except:
                continue

        await query.message.edit_text(
            "sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ɪᴛs ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# Custom filter function to check if user is waiting for screenshot
def screenshot_filter(_, __, message):
    user_id = message.from_user.id
    return user_id in waiting_for_screenshot and user_id in pending_payments

# Create the custom filter
waiting_screenshot_filter = filters.create(screenshot_filter)

# Handle payment screenshots ONLY when user is specifically waiting
@Bot.on_message(filters.photo & filters.private & waiting_screenshot_filter)
async def handle_payment_screenshot(client: Bot, message: Message):
    user_id = message.from_user.id
    payment_info = pending_payments[user_id]
    
    # Forward screenshot to owner
    try:
        owner_caption = (
            f"💳 Payment Screenshot Received\n\n"
            f"👤 User: {message.from_user.first_name} (@{message.from_user.username})\n"
            f"🆔 User ID: {user_id}\n"
            f"📋 Plan: {payment_info['duration']} - ₹{payment_info['amount']}\n\n"
            f"⚡ Please verify and activate premium"
        )
        
        await client.send_photo(
            chat_id=OWNER_ID,
            photo=message.photo.file_id,
            caption=owner_caption
        )
        
        # Confirm to user
        await message.reply_text(
            f"✅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ᴛʜᴇ ᴏᴡɴᴇʀ ꜰᴏʀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ.\n\n"
            f"⏳ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ꜰᴏʀ ᴀᴘᴘʀᴏᴠᴀʟ. ʏᴏᴜ ᴡɪʟʟ ʙᴇ ɴᴏᴛɪꜰɪᴇᴅ ᴏɴᴄᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪs ᴀᴄᴛɪᴠᴀᴛᴇᴅ.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🏠 Home", callback_data="start"),
                    InlineKeyboardButton("📢 Channel", url="https://t.me/+f4n8nwqVzFhiMmUx")
                ]
            ])
        )
        
        # Remove user from waiting state after screenshot is processed
        del waiting_for_screenshot[user_id]
        
    except Exception as e:
        await message.reply_text("❌ Failed to forward screenshot. Please contact admin directly.")
        print(f"Error forwarding screenshot: {e}")

# Custom filter function to check if user is waiting for gift card
def gift_card_filter(_, __, message):
    user_id = message.from_user.id
    return user_id in waiting_for_gift_card and user_id in pending_gift_cards

# Create the custom filter for gift cards
waiting_gift_card_filter = filters.create(gift_card_filter)

# Handle gift card submissions (text or photo)
@Bot.on_message((filters.text | filters.photo) & filters.private & waiting_gift_card_filter)
async def handle_gift_card_submission(client: Bot, message: Message):
    user_id = message.from_user.id
    gift_card_info = pending_gift_cards[user_id]
    
    try:
        # Prepare owner message based on message type
        if message.photo:
            # Forward gift card screenshot to owner
            owner_caption = (
                f"🎁 Gift Card Screenshot Received\n\n"
                f"👤 User: {message.from_user.first_name} (@{message.from_user.username})\n"
                f"🆔 User ID: {user_id}\n"
                f"📋 Plan: {gift_card_info['duration']} - ₹{gift_card_info['amount']}\n\n"
                f"⚡ Please verify gift card and activate premium"
            )
            
            await client.send_photo(
                chat_id=OWNER_ID,
                photo=message.photo.file_id,
                caption=owner_caption
            )
        else:
            # Forward gift card text/code to owner
            owner_message = (
                f"🎁 Gift Card Code/Link Received\n\n"
                f"👤 User: {message.from_user.first_name} (@{message.from_user.username})\n"
                f"🆔 User ID: {user_id}\n"
                f"📋 Plan: {gift_card_info['duration']} - ₹{gift_card_info['amount']}\n\n"
                f"🎫 Gift Card Details:\n{message.text}\n\n"
                f"⚡ Please verify gift card and activate premium"
            )
            
            await client.send_message(
                chat_id=OWNER_ID,
                text=owner_message
            )
        
        # Confirm to user
        await message.reply_text(
            f"✅ ʏᴏᴜʀ ɢɪꜰᴛ ᴄᴀʀᴅ ᴅᴇᴛᴀɪʟs ʜᴀᴠᴇ ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ᴛʜᴇ ᴏᴡɴᴇʀ ꜰᴏʀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ.\n\n"
            f"⏳ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ꜰᴏʀ ᴀᴘᴘʀᴏᴠᴀʟ. ʏᴏᴜ ᴡɪʟʟ ʙᴇ ɴᴏᴛɪꜰɪᴇᴅ ᴏɴᴄᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪs ᴀᴄᴛɪᴠᴀᴛᴇᴅ.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🏠 Home", callback_data="start"),
                    InlineKeyboardButton("📢 Channel", url="https://t.me/+f4n8nwqVzFhiMmUx")
                ]
            ])
        )
        
        # Remove user from waiting state after gift card is processed
        del waiting_for_gift_card[user_id]
        
    except Exception as e:
        await message.reply_text("❌ Failed to forward gift card details. Please contact admin directly.")
        print(f"Error forwarding gift card: {e}")
