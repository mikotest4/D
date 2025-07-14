from pyrogram import Client, filters
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *
from plugins.super_prime import handle_super_prime_callback, handle_sp_admin_callback
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

    # Handle Super Prime callbacks first
    if data == "super_prime" or data.startswith("sp_"):
        return await handle_super_prime_callback(client, query)
    
    # Handle Super Prime admin callbacks
    if data.startswith("sp_approve_") or data.startswith("sp_reject_"):
        return await handle_sp_admin_callback(client, query)

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
        plan_key = data.replace("plan_", "")
        plan = PLANS.get(plan_key)
        
        if plan:
            await query.message.edit_text(
                f"💎 <b>Premium Plan - {plan['duration']}</b>\n\n"
                f"💰 <b>Price:</b> ₹{plan['price']}\n"
                f"⏰ <b>Duration:</b> {plan['duration']}\n\n"
                f"Choose your payment method:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 UPI Payment", callback_data=f"upi_{plan_key}")],
                    [InlineKeyboardButton("🎁 Gift Card", callback_data=f"gift_{plan_key}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="premium")]
                ])
            )

    # Handle UPI payment selection
    elif data.startswith("upi_"):
        plan_key = data.replace("upi_", "")
        plan = PLANS.get(plan_key)
        
        if plan:
            # Store payment info
            pending_payments[query.from_user.id] = {
                'plan': plan_key,
                'amount': plan['price'],
                'duration': plan['duration'],
                'days': plan['days']
            }
            
            # Generate QR code
            qr_image = await generate_upi_qr_external(UPI_1, plan['price'], f"Premium {plan['duration']}")
            
            if qr_image:
                await query.message.delete()
                await client.send_photo(
                    chat_id=query.from_user.id,
                    photo=qr_image,
                    caption=(
                        f"💎 <b>Premium Payment</b>\n\n"
                        f"💰 <b>Amount:</b> ₹{plan['price']}\n"
                        f"⏰ <b>Duration:</b> {plan['duration']}\n"
                        f"💳 <b>UPI ID:</b> <code>{UPI_1}</code>\n\n"
                        f"📱 <b>Steps:</b>\n"
                        f"1. Scan QR code or copy UPI ID\n"
                        f"2. Pay exactly ₹{plan['price']}\n"
                        f"3. Take screenshot of payment\n"
                        f"4. Send screenshot here\n\n"
                        f"⚠️ <b>Important:</b> Payment amount must be exact!"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Payment Done", callback_data=f"payment_done_{plan_key}")],
                        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
                    ])
                )
                
                waiting_for_screenshot[query.from_user.id] = True
            else:
                await query.answer("❌ Failed to generate QR code. Please try again.", show_alert=True)

    elif data.startswith("payment_done_"):
        plan_key = data.replace("payment_done_", "")
        plan = PLANS.get(plan_key)
        
        await query.message.edit_caption(
            f"💎 <b>Premium Payment Confirmation</b>\n\n"
            f"💰 <b>Amount:</b> ₹{plan['price']}\n"
            f"⏰ <b>Duration:</b> {plan['duration']}\n\n"
            f"📸 <b>Please send your payment screenshot now</b>\n\n"
            f"⚠️ Your premium will be activated after verification.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
            ])
        )

    elif data == "cancel_payment":
        user_id = query.from_user.id
        if user_id in pending_payments:
            del pending_payments[user_id]
        if user_id in waiting_for_screenshot:
            del waiting_for_screenshot[user_id]
        
        await query.message.edit_text(
            "❌ <b>Payment cancelled</b>\n\n"
            "You can try again anytime by using the premium option.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="premium")]
            ])
        )

    # Handle gift card payment
    elif data.startswith("gift_"):
        plan_key = data.replace("gift_", "")
        plan = PLANS.get(plan_key)
        
        if plan:
            # Store gift card info
            pending_gift_cards[query.from_user.id] = {
                'plan': plan_key,
                'amount': plan['price'],
                'duration': plan['duration'],
                'days': plan['days']
            }
            
            await query.message.edit_text(
                f"🎁 <b>Gift Card Payment - {plan['duration']}</b>\n\n"
                f"💰 <b>Amount:</b> ₹{plan['price']}\n"
                f"⏰ <b>Duration:</b> {plan['duration']}\n\n"
                f"📝 <b>Instructions:</b>\n"
                f"1. Buy a gift card of ₹{plan['price']}\n"
                f"2. Send the gift card details here\n"
                f"3. Include card number and PIN\n\n"
                f"⚠️ <b>Supported cards:</b> Amazon, Flipkart, Google Play",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Send Gift Card", callback_data=f"send_gift_{plan_key}")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_gift")]
                ])
            )

    elif data.startswith("send_gift_"):
        plan_key = data.replace("send_gift_", "")
        plan = PLANS.get(plan_key)
        
        waiting_for_gift_card[query.from_user.id] = True
        
        await query.message.edit_text(
            f"🎁 <b>Gift Card Submission</b>\n\n"
            f"💰 <b>Amount:</b> ₹{plan['price']}\n"
            f"⏰ <b>Duration:</b> {plan['duration']}\n\n"
            f"📝 <b>Please send your gift card details in this format:</b>\n\n"
            f"<code>Card Type: Amazon/Flipkart/Google Play\n"
            f"Card Number: XXXX-XXXX-XXXX\n"
            f"PIN: XXXX\n"
            f"Amount: ₹{plan['price']}</code>\n\n"
            f"⚠️ Make sure all details are correct!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_gift")]
            ])
        )

    elif data == "cancel_gift":
        user_id = query.from_user.id
        if user_id in pending_gift_cards:
            del pending_gift_cards[user_id]
        if user_id in waiting_for_gift_card:
            del waiting_for_gift_card[user_id]
        
        await query.message.edit_text(
            "❌ <b>Gift card payment cancelled</b>\n\n"
            "You can try again anytime by using the premium option.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="premium")]
            ])
        )

    # Handle force sub reload
    elif data == "reload":
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply("/start")

    # Handle force sub request callbacks
    elif data.startswith("rfs_ch_"):
        channel_id = int(data.replace("rfs_ch_", ""))
        current_mode = await db.get_channel_mode(channel_id)
        
        if current_mode == "on":
            await db.set_channel_mode(channel_id, "off")
            new_status = "🔴 OFF"
        else:
            await db.set_channel_mode(channel_id, "on")
            new_status = "🟢 ON"
        
        try:
            chat = await client.get_chat(channel_id)
            await query.answer(f"Force-Sub for {chat.title} is now {new_status}", show_alert=True)
        except:
            await query.answer(f"Force-Sub for {channel_id} is now {new_status}", show_alert=True)
        
        # Refresh the buttons
        temp = await query.message.edit_text("<b><i>ᴜᴘᴅᴀᴛɪɴɢ...</i></b>")
        channels = await db.show_channels()
        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                status = "🟢" if mode == "on" else "🔴"
                title = f"{status} {chat.title}"
                buttons.append([InlineKeyboardButton(title, callback_data=f"rfs_ch_{ch_id}")])
            except:
                buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"rfs_ch_{ch_id}")])
        
        buttons.append([InlineKeyboardButton("Close ✖️", callback_data="close")])
        
        await temp.edit(
            "<b>⚡ Select a channel to toggle Force-Sub Mode:</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "close":
        await query.message.delete()

    # Handle admin approval/rejection for regular premium
    elif data.startswith("approve_"):
        user_id = int(data.split("_")[1])
        days = int(data.split("_")[2])
        
        from database.db_premium import add_premium_user
        success = await add_premium_user(user_id, days)
        
        if success:
            # Notify user
            try:
                await client.send_message(
                    user_id,
                    f"🎉 <b>Premium Activated!</b>\n\n"
                    f"✅ Your payment has been verified!\n"
                    f"⏰ <b>Duration:</b> {days} days\n\n"
                    f"Thank you for choosing premium! 💎"
                )
            except:
                pass
            
            await query.message.edit_caption(
                query.message.caption + f"\n\n✅ <b>APPROVED by {query.from_user.first_name}</b>"
            )
            
            # Clean up
            if user_id in pending_payments:
                del pending_payments[user_id]
        else:
            await query.answer("❌ Failed to activate premium!", show_alert=True)

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                "❌ <b>Payment Rejected</b>\n\n"
                "Your premium payment was not approved.\n"
                "Please contact support for assistance."
            )
        except:
            pass
        
        await query.message.edit_caption(
            query.message.caption + f"\n\n❌ <b>REJECTED by {query.from_user.first_name}</b>"
        )
        
        # Clean up
        if user_id in pending_payments:
            del pending_payments[user_id]

    # Handle gift card admin approval/rejection
    elif data.startswith("gift_approve_"):
        user_id = int(data.split("_")[2])
        days = int(data.split("_")[3])
        
        from database.db_premium import add_premium_user
        success = await add_premium_user(user_id, days)
        
        if success:
            # Notify user
            try:
                await client.send_message(
                    user_id,
                    f"🎉 <b>Premium Activated!</b>\n\n"
                    f"✅ Your gift card has been verified!\n"
                    f"⏰ <b>Duration:</b> {days} days\n\n"
                    f"Thank you for choosing premium! 💎"
                )
            except:
                pass
            
            await query.message.edit_text(
                query.message.text + f"\n\n✅ <b>APPROVED by {query.from_user.first_name}</b>"
            )
            
            # Clean up
            if user_id in pending_gift_cards:
                del pending_gift_cards[user_id]
        else:
            await query.answer("❌ Failed to activate premium!", show_alert=True)

    elif data.startswith("gift_reject_"):
        user_id = int(data.split("_")[2])
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                "❌ <b>Gift Card Rejected</b>\n\n"
                "Your gift card was not approved.\n"
                "Please contact support for assistance."
            )
        except:
            pass
        
        await query.message.edit_text(
            query.message.text + f"\n\n❌ <b>REJECTED by {query.from_user.first_name}</b>"
        )
        
        # Clean up
        if user_id in pending_gift_cards:
            del pending_gift_cards[user_id]

# Handle screenshot submissions for regular premium
@Bot.on_message(filters.private & filters.photo)
async def handle_screenshot(client: Bot, message: Message):
    user_id = message.from_user.id
    
    # Check if user is waiting to send screenshot for regular premium
    if user_id in waiting_for_screenshot and user_id in pending_payments:
        payment_info = pending_payments[user_id]
        
        # Forward screenshot to owner
        await client.send_photo(
            chat_id=OWNER_ID,
            photo=message.photo.file_id,
            caption=(
                f"💎 <b>Premium Payment Screenshot</b>\n\n"
                f"👤 <b>User:</b> {message.from_user.first_name}\n"
                f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                f"💰 <b>Amount:</b> ₹{payment_info['amount']}\n"
                f"⏰ <b>Duration:</b> {payment_info['duration']}\n"
                f"📅 <b>Days:</b> {payment_info['days']}\n\n"
                f"✅ Use: <code>/addpremium {user_id} {payment_info['days']}</code>"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{payment_info['days']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                ]
            ])
        )
        
        # Confirm to user
        await message.reply(
            f"✅ <b>Screenshot received!</b>\n\n"
            f"📝 Your premium payment is under review.\n"
            f"💰 Amount: ₹{payment_info['amount']}\n"
            f"⏰ Duration: {payment_info['duration']}\n\n"
            f"🕐 You'll be notified once verified (usually within 24 hours)."
        )
        
        # Clean up
        del waiting_for_screenshot[user_id]

# Handle gift card submissions
@Bot.on_message(filters.private & filters.text & ~filters.command(['start', 'help']))
async def handle_gift_card(client: Bot, message: Message):
    user_id = message.from_user.id
    
    # Check if user is waiting to send gift card details
    if user_id in waiting_for_gift_card and user_id in pending_gift_cards:
        gift_info = pending_gift_cards[user_id]
        
        # Forward gift card details to owner
        await client.send_message(
            chat_id=OWNER_ID,
            text=(
                f"🎁 <b>Gift Card Payment Details</b>\n\n"
                f"👤 <b>User:</b> {message.from_user.first_name}\n"
                f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                f"💰 <b>Amount:</b> ₹{gift_info['amount']}\n"
                f"⏰ <b>Duration:</b> {gift_info['duration']}\n"
                f"📅 <b>Days:</b> {gift_info['days']}\n\n"
                f"🎁 <b>Gift Card Details:</b>\n"
                f"<code>{message.text}</code>\n\n"
                f"✅ Use: <code>/addpremium {user_id} {gift_info['days']}</code>"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"gift_approve_{user_id}_{gift_info['days']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"gift_reject_{user_id}")
                ]
            ])
        )
        
        # Confirm to user
        await message.reply(
            f"✅ <b>Gift card details received!</b>\n\n"
            f"📝 Your premium payment is under review.\n"
            f"💰 Amount: ₹{gift_info['amount']}\n"
            f"⏰ Duration: {gift_info['duration']}\n\n"
            f"🕐 You'll be notified once verified (usually within 24 hours)."
        )
        
        # Clean up
        del waiting_for_gift_card[user_id]
