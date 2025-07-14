
import asyncio
import urllib.parse
import requests
import io
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from config import *
from helper_func import admin
from database.database import *
from database.db_super_prime import *

# Super Prime Plans
SUPER_PRIME_PLANS = {
    "1month_sp": {"price": 250, "duration": "1 Month", "days": 30},
    "3months_sp": {"price": 600, "duration": "3 Months", "days": 90}
}

# UPI IDs for super prime payments
SP_UPI_1 = "singhzerotwo@fam"
SP_UPI_2 = "7348433876@mbk"

# Store pending super prime payments
pending_sp_payments = {}
waiting_for_sp_screenshot = {}

async def generate_sp_upi_qr(upi_id, amount, plan_name="Super Prime"):
    """Generate UPI QR code for super prime payments"""
    try:
        note = f"{plan_name} Plan"
        upi_url = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(note)}&am={amount}&cu=INR&tn={urllib.parse.quote('Super Prime Payment')}"
        
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"
        
        response = requests.get(qr_api_url, timeout=10)
        if response.status_code == 200:
            qr_image = io.BytesIO(response.content)
            qr_image.seek(0)
            return qr_image
        else:
            return None
    except Exception as e:
        print(f"Error generating super prime QR code: {e}")
        return None

# Handle super prime callback
async def handle_super_prime_callback(client: Bot, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    if data == "super_prime":
        await query.message.edit_text(
            f"🌟 <b>Super Prime Plans</b> 🌟\n\n"
            f"Choose your Super Prime plan:\n\n"
            f"✨ <b>Super Prime Benefits:</b>\n"
            f"• Forward and save all content\n"
            f"• No token verification required\n"
            f"• Priority support\n"
            f"• No ads interruption\n\n"
            f"Select a plan below:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1 Month - ₹250", callback_data="sp_plan_1month_sp"),
                    InlineKeyboardButton("3 Months - ₹600", callback_data="sp_plan_3months_sp")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_token")]
            ])
        )

    elif data.startswith("sp_plan_"):
        plan_key = data.replace("sp_plan_", "")
        plan = SUPER_PRIME_PLANS.get(plan_key)
        
        if plan:
            await query.message.edit_text(
                f"🌟 <b>Super Prime - {plan['duration']}</b>\n\n"
                f"💰 <b>Price:</b> ₹{plan['price']}\n"
                f"⏰ <b>Duration:</b> {plan['duration']}\n\n"
                f"✨ <b>Benefits:</b>\n"
                f"• Forward and save all content\n"
                f"• No token verification\n"
                f"• Priority support\n"
                f"• Ad-free experience\n\n"
                f"Choose payment method:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 UPI Payment", callback_data=f"sp_upi_{plan_key}")],
                    [InlineKeyboardButton("🎁 Gift Card", callback_data=f"sp_gift_{plan_key}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="super_prime")]
                ])
            )

    elif data.startswith("sp_upi_"):
        plan_key = data.replace("sp_upi_", "")
        plan = SUPER_PRIME_PLANS.get(plan_key)
        
        if plan:
            # Store payment info
            pending_sp_payments[user_id] = {
                'plan': plan_key,
                'amount': plan['price'],
                'duration': plan['duration'],
                'days': plan['days']
            }
            
            # Generate QR code
            qr_image = await generate_sp_upi_qr(SP_UPI_1, plan['price'], f"Super Prime {plan['duration']}")
            
            if qr_image:
                await query.message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=qr_image,
                    caption=(
                        f"🌟 <b>Super Prime Payment</b>\n\n"
                        f"💰 <b>Amount:</b> ₹{plan['price']}\n"
                        f"⏰ <b>Duration:</b> {plan['duration']}\n"
                        f"💳 <b>UPI ID:</b> <code>{SP_UPI_1}</code>\n\n"
                        f"📱 <b>Steps:</b>\n"
                        f"1. Scan QR code or copy UPI ID\n"
                        f"2. Pay exactly ₹{plan['price']}\n"
                        f"3. Take screenshot of payment\n"
                        f"4. Send screenshot here\n\n"
                        f"⚠️ <b>Important:</b> Payment amount must be exact!"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Payment Done", callback_data=f"sp_payment_done_{plan_key}")],
                        [InlineKeyboardButton("❌ Cancel", callback_data="sp_cancel_payment")]
                    ])
                )
                
                waiting_for_sp_screenshot[user_id] = True
            else:
                await query.answer("❌ Failed to generate QR code. Please try again.", show_alert=True)

    elif data.startswith("sp_payment_done_"):
        plan_key = data.replace("sp_payment_done_", "")
        plan = SUPER_PRIME_PLANS.get(plan_key)
        
        await query.message.edit_caption(
            f"🌟 <b>Super Prime Payment Confirmation</b>\n\n"
            f"💰 <b>Amount:</b> ₹{plan['price']}\n"
            f"⏰ <b>Duration:</b> {plan['duration']}\n\n"
            f"📸 <b>Please send your payment screenshot now</b>\n\n"
            f"⚠️ Your Super Prime will be activated after verification.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="sp_cancel_payment")]
            ])
        )

    elif data == "sp_cancel_payment":
        if user_id in pending_sp_payments:
            del pending_sp_payments[user_id]
        if user_id in waiting_for_sp_screenshot:
            del waiting_for_sp_screenshot[user_id]
        
        await query.message.edit_text(
            "❌ <b>Payment cancelled</b>\n\n"
            "You can try again anytime by clicking the Super Prime button.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="super_prime")]
            ])
        )

    elif data == "back_to_token":
        # Redirect back to token verification message
        await query.answer("Please use /start to get your token verification link again.")

# Handle super prime screenshot
@Bot.on_message(filters.private & filters.photo)
async def handle_sp_screenshot(client: Bot, message: Message):
    user_id = message.from_user.id
    
    if user_id in waiting_for_sp_screenshot and user_id in pending_sp_payments:
        payment_info = pending_sp_payments[user_id]
        
        # Forward screenshot to owner
        await client.send_photo(
            chat_id=OWNER_ID,
            photo=message.photo.file_id,
            caption=(
                f"🌟 <b>Super Prime Payment Screenshot</b>\n\n"
                f"👤 <b>User:</b> {message.from_user.first_name}\n"
                f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                f"💰 <b>Amount:</b> ₹{payment_info['amount']}\n"
                f"⏰ <b>Duration:</b> {payment_info['duration']}\n"
                f"📅 <b>Days:</b> {payment_info['days']}\n\n"
                f"✅ Use: <code>/prime {user_id} {payment_info['days']}</code>"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"sp_approve_{user_id}_{payment_info['days']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"sp_reject_{user_id}")
                ]
            ])
        )
        
        # Confirm to user
        await message.reply(
            f"✅ <b>Screenshot received!</b>\n\n"
            f"📝 Your Super Prime payment is under review.\n"
            f"💰 Amount: ₹{payment_info['amount']}\n"
            f"⏰ Duration: {payment_info['duration']}\n\n"
            f"🕐 You'll be notified once verified (usually within 24 hours)."
        )
        
        # Clean up
        del waiting_for_sp_screenshot[user_id]

# Admin commands for super prime
@Bot.on_message(filters.private & filters.command('prime') & admin)
async def add_super_prime_user(client: Bot, message: Message):
    try:
        args = message.text.split()
        if len(args) != 3:
            return await message.reply(
                "<b>❌ Invalid format!</b>\n\n"
                "<b>Usage:</b> <code>/prime user_id duration_days</code>\n\n"
                "<b>Example:</b> <code>/prime 123456789 30</code>"
            )
        
        user_id = int(args[1])
        duration = int(args[2])
        
        if duration <= 0:
            return await message.reply("❌ Duration must be positive!")
        
        success = await add_super_prime(user_id, duration)
        
        if success:
            # Notify user
            try:
                await client.send_message(
                    user_id,
                    f"🌟 <b>Congratulations!</b>\n\n"
                    f"✅ Your Super Prime has been activated!\n"
                    f"⏰ <b>Duration:</b> {duration} days\n\n"
                    f"🎉 <b>Benefits unlocked:</b>\n"
                    f"• Forward and save all content\n"
                    f"• No token verification\n"
                    f"• Priority support\n"
                    f"• Ad-free experience\n\n"
                    f"Thank you for choosing Super Prime! 🌟"
                )
            except:
                pass
            
            await message.reply(
                f"✅ <b>Super Prime activated!</b>\n\n"
                f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
                f"⏰ <b>Duration:</b> {duration} days"
            )
            
            # Clean up pending payment if exists
            if user_id in pending_sp_payments:
                del pending_sp_payments[user_id]
        else:
            await message.reply("❌ Failed to add Super Prime user!")
            
    except ValueError:
        await message.reply("❌ Invalid user ID or duration!")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@Bot.on_message(filters.private & filters.command('sp_users') & admin)
async def list_sp_users(client: Bot, message: Message):
    users = await list_super_prime_users()
    
    if not users:
        return await message.reply("📝 No Super Prime users found.")
    
    text = "🌟 <b>Super Prime Users:</b>\n\n"
    
    for user in users[:20]:  # Limit to 20 users
        status = "🟢 Active" if user['is_active'] else "🔴 Expired"
        text += (
            f"👤 <code>{user['user_id']}</code>\n"
            f"📅 Days left: {user['days_left']}\n"
            f"📊 Status: {status}\n\n"
        )
    
    if len(users) > 20:
        text += f"... and {len(users) - 20} more users"
    
    await message.reply(text)

@Bot.on_message(filters.private & filters.command('remove_sp') & admin)
async def remove_sp_user(client: Bot, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply(
                "<b>Usage:</b> <code>/remove_sp user_id</code>"
            )
        
        user_id = int(args[1])
        success = await remove_super_prime(user_id)
        
        if success:
            # Notify user
            try:
                await client.send_message(
                    user_id,
                    "⚠️ <b>Super Prime Removed</b>\n\n"
                    "Your Super Prime subscription has been removed.\n"
                    "Contact support if this was done in error."
                )
            except:
                pass
            
            await message.reply(f"✅ Super Prime removed for user: <code>{user_id}</code>")
        else:
            await message.reply("❌ User not found in Super Prime list!")
            
    except ValueError:
        await message.reply("❌ Invalid user ID!")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# Handle admin approval/rejection callbacks
async def handle_sp_admin_callback(client: Bot, query: CallbackQuery):
    data = query.data
    
    if data.startswith("sp_approve_"):
        parts = data.split("_")
        user_id = int(parts[2])
        days = int(parts[3])
        
        success = await add_super_prime(user_id, days)
        
        if success:
            # Notify user
            try:
                await client.send_message(
                    user_id,
                    f"🌟 <b>Super Prime Activated!</b>\n\n"
                    f"✅ Your payment has been verified!\n"
                    f"⏰ <b>Duration:</b> {days} days\n\n"
                    f"🎉 <b>Benefits unlocked:</b>\n"
                    f"• Forward and save all content\n"
                    f"• No token verification\n"
                    f"• Priority support\n"
                    f"• Ad-free experience\n\n"
                    f"Thank you for choosing Super Prime! 🌟"
                )
            except:
                pass
            
            await query.message.edit_caption(
                query.message.caption + f"\n\n✅ <b>APPROVED by {query.from_user.first_name}</b>"
            )
            
            # Clean up
            if user_id in pending_sp_payments:
                del pending_sp_payments[user_id]
        else:
            await query.answer("❌ Failed to activate Super Prime!", show_alert=True)
    
    elif data.startswith("sp_reject_"):
        user_id = int(data.split("_")[2])
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                "❌ <b>Payment Rejected</b>\n\n"
                "Your Super Prime payment was not approved.\n"
                "Please contact support for assistance.\n\n"
                "Possible reasons:\n"
                "• Incorrect payment amount\n"
                "• Invalid screenshot\n"
                "• Payment not received"
            )
        except:
            pass
        
        await query.message.edit_caption(
            query.message.caption + f"\n\n❌ <b>REJECTED by {query.from_user.first_name}</b>"
        )
        
        # Clean up
        if user_id in pending_sp_payments:
            del pending_sp_payments[user_id]
