#!/usr/bin/env python3
"""
💎 EarnX Pro Bot - Complete Telegram Earning Bot
WITH PROPER CHANNEL MEMBERSHIP CHECK
FIXED VERSION - ALL ISSUES RESOLVED
"""

import os
import sqlite3
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from dotenv import load_dotenv
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    ChatMember
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# ==================== LOAD ENVIRONMENT ====================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
BOT_USERNAME = os.getenv("BOT_USERNAME", "EEarnX_Pro_Bot")  # ডিফল্ট ভ্যালু
MAIN_CHANNEL = os.getenv("MAIN_CHANNEL", "@DarkRootCrew")  # .env থেকে নিবে
PAYMENT_CHANNEL = os.getenv("PAYMENT_CHANNEL", "@DarkRoot_Official")  # .env থেকে নিবে
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "@TheSagorOfficial")  # .env থেকে নিবে

# Load bonus and fee values from .env
REFERRAL_BONUS = float(os.getenv("REFERRAL_BONUS", "10.00"))
DAILY_BONUS = float(os.getenv("DAILY_BONUS", "5.00"))
WELCOME_BONUS = float(os.getenv("WELCOME_BONUS", "2.00"))
MIN_WITHDRAW = float(os.getenv("MIN_WITHDRAW", "50.00"))
WITHDRAW_FEE = float(os.getenv("WITHDRAW_FEE", "1"))
CURRENCY = os.getenv("CURRENCY", "USDT")

# BOT_USERNAME থেকে @ সরিয়ে ফেলুন (যদি থাকে)
if BOT_USERNAME.startswith('@'):
    BOT_USERNAME = BOT_USERNAME[1:]

# ==================== CHANNEL MEMBERSHIP CHECK ====================
async def check_channel_membership(bot, user_id: int, channel_username: str) -> bool:
    """
    Check if user is member of a channel
    Returns: True if member, False if not
    """
    try:
        # Remove @ if present
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]
        
        # Get chat member status
        chat_id = f"@{channel_username}"
        member = await bot.get_chat_member(
            chat_id=chat_id, 
            user_id=user_id
        )
        
        # Debug information
        print(f"Checking membership for user {user_id} in {chat_id}")
        print(f"Member status: {member.status}")
        
        # Check if user is member, admin or creator
        if member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error checking membership for {channel_username}: {e}")
        return False  # Change to True for testing without admin rights

# ==================== DATABASE SETUP ====================
def init_db():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT NOT NULL,
        balance REAL DEFAULT 0,
        wallet_address TEXT,
        wallet_type TEXT DEFAULT 'USDT',
        mobile_bank TEXT,
        phone_number TEXT,
        has_agreed INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        ban_reason TEXT,
        last_daily_bonus TEXT,
        referral_code TEXT UNIQUE,
        referred_by INTEGER,
        total_earned REAL DEFAULT 0,
        daily_bonus_count INTEGER DEFAULT 0,
        total_daily_bonus REAL DEFAULT 0,
        joined_date TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Withdrawals table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        fee REAL NOT NULL,
        net_amount REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        wallet_address TEXT,
        wallet_type TEXT,
        mobile_bank TEXT,
        phone_number TEXT,
        admin_note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # Settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert default settings if not exists
    default_settings = [
        ('refer_bonus', str(REFERRAL_BONUS)),
        ('min_withdraw', str(MIN_WITHDRAW)),
        ('daily_bonus', str(DAILY_BONUS)),
        ('withdraw_fee', str(WITHDRAW_FEE)),
        ('currency', CURRENCY),
        ('support_chat', SUPPORT_CHAT),
        ('payment_channel', PAYMENT_CHANNEL),
        ('main_channel', MAIN_CHANNEL),
        ('welcome_bonus', str(WELCOME_BONUS))
    ]
    
    for key, value in default_settings:
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()

# ==================== DATABASE HELPER FUNCTIONS ====================
def get_user(user_id: int):
    """Get user from database"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_dict(user_id: int) -> Dict:
    """Get user as dictionary"""
    conn = sqlite3.connect('earnx_bot.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user(user_id: int, **kwargs):
    """Update user fields"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    
    for key, value in kwargs.items():
        cursor.execute(f'UPDATE users SET {key} = ? WHERE user_id = ?', (value, user_id))
    
    conn.commit()
    conn.close()

def create_user(user_id: int, username: str, first_name: str):
    """Create new user with referral code"""
    import random
    import string
    
    # Generate unique referral code
    while True:
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        conn = sqlite3.connect('earnx_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE referral_code = ?', (ref_code,))
        if cursor.fetchone()[0] == 0:
            break
    
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO users 
    (user_id, username, first_name, referral_code, balance, total_earned, daily_bonus_count, total_daily_bonus) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, ref_code, 0, 0, 0, 0))
    
    conn.commit()
    conn.close()
    return ref_code

def get_setting(key: str) -> str:
    """Get setting value"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_setting(key: str, value: str):
    """Update setting value"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?', 
                   (value, key))
    conn.commit()
    conn.close()

def add_balance(user_id: int, amount: float):
    """Add balance to user"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ?, total_earned = total_earned + ? WHERE user_id = ?', 
                   (amount, amount, user_id))
    conn.commit()
    conn.close()

def get_total_users():
    """Get total user count"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_total_withdrawn():
    """Get total withdrawn amount"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(net_amount) FROM withdrawals WHERE status = "approved"')
    result = cursor.fetchone()
    conn.close()
    return result[0] or 0

def get_pending_withdrawals():
    """Get pending withdrawal count"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM withdrawals WHERE status = "pending"')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_user_total_withdrawn(user_id: int):
    """Get user's total withdrawn amount"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(net_amount) FROM withdrawals WHERE user_id = ? AND status = "approved"', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] or 0

def get_user_pending_withdrawn(user_id: int):
    """Get user's pending withdrawn amount"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(amount) FROM withdrawals WHERE user_id = ? AND status = "pending"', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] or 0

def get_banned_users():
    """Get all banned users"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, first_name, ban_reason FROM users WHERE is_banned = 1')
    users = cursor.fetchall()
    conn.close()
    return users

# ==================== CONVERSATION STATES ====================
(
    # User states
    WAITING_FOR_WALLET_TYPE,
    WAITING_FOR_USDT_ADDRESS,
    WAITING_FOR_BANK_PROVIDER,
    WAITING_FOR_PHONE_NUMBER,
    WAITING_FOR_WITHDRAW_AMOUNT,
    WAITING_FOR_CONFIRM_WITHDRAW,
    WAITING_FOR_DENY_REASON,
    
    # Admin states
    ADMIN_ADD_BALANCE_USER,
    ADMIN_ADD_BALANCE_AMOUNT,
    ADMIN_CUT_BALANCE_USER,
    ADMIN_CUT_BALANCE_AMOUNT,
    ADMIN_BAN_USER_ID,
    ADMIN_BAN_REASON,
    ADMIN_UNBAN_USER_ID,
    ADMIN_BROADCAST_MESSAGE,
    
    # Settings states
    SETTING_REF_BONUS,
    SETTING_MIN_WITHDRAW,
    SETTING_DAILY_BONUS,
    SETTING_WITHDRAW_FEE,
    SETTING_SUPPORT_CHAT,
    SETTING_PAYMENT_CHANNEL,
    SETTING_MAIN_CHANNEL,
    SETTING_WELCOME_BONUS
) = range(23)

# ==================== KEYBOARDS ====================
def get_main_keyboard():
    """Main menu reply keyboard"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 Balance"), KeyboardButton("💸 Withdraw"), KeyboardButton("🎁 Daily Bonus")],
        [KeyboardButton("📊 Statistics"), KeyboardButton("👥 Referral"), KeyboardButton("🆘 Help")],
        [KeyboardButton("🔐 Set Wallet"), KeyboardButton("ℹ️ About")]
    ], resize_keyboard=True)

def get_admin_keyboard():
    """Admin menu reply keyboard"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("📈 Bot Stats"), KeyboardButton("👥 All Users")],
        [KeyboardButton("➕ Add Balance"), KeyboardButton("➖ Cut Balance")],
        [KeyboardButton("💸 Withdraw Request"), KeyboardButton("📢 Broadcast")],
        [KeyboardButton("🚫 Ban Manager"), KeyboardButton("⚙️ Bot Settings")],
        [KeyboardButton("🔙 User Panel")]
    ], resize_keyboard=True)

def get_banned_user_keyboard():
    """Keyboard for banned users"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("🆘 Help")]
    ], resize_keyboard=True)

def get_help_keyboard():
    """Help menu keyboard"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("📞 Support Chat"), KeyboardButton("🔙 Back")]
    ], resize_keyboard=True)

def get_ban_manager_keyboard():
    """Ban manager keyboard"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("🚫 Ban User"), KeyboardButton("🔐 UnBan User")],
        [KeyboardButton("👁 View Banned"), KeyboardButton("🔙 Back")]
    ], resize_keyboard=True)

def get_settings_keyboard():
    """Settings keyboard"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎁Set Refer Bonus"), KeyboardButton("💵Set Min Withdraw")],
        [KeyboardButton("🎁Set Daily Bonus"), KeyboardButton("💵Set Withdraw Fee")],
        [KeyboardButton("🎁Set Welcome Bonus"), KeyboardButton("📞Set Support Chat")],
        [KeyboardButton("💬Set Payment Channel"), KeyboardButton("🏠Set Main Channel")],
        [KeyboardButton("🔙 Back")]
    ], resize_keyboard=True)

# ==================== BUTTON CALLBACK HANDLERS ====================
async def join_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Join Channel button click"""
    query = update.callback_query
    await query.answer()
    
    main_channel = get_setting('main_channel')
    
    await query.edit_message_text(
        text=f"🔗 Click below to join our channel:\n\n"
             f"{main_channel}\n\n"
             f"After joining, click '✅ I've Joined'",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{main_channel[1:]}")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ])
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user joined channel"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer("Checking membership...")
    
    main_channel = get_setting('main_channel')
    
    has_joined = await check_channel_membership(
        context.bot, 
        user_id, 
        main_channel
    )
    
    if has_joined:
        await query.edit_message_text(
            text=f"✅ Welcome! You have successfully joined the channel. You can now use all bot features.\n\n"
                 f"Our Terms And Conditions. If you agree, click the 🟢 I Agree 🟢 button.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 I Agree 🟢", callback_data="agree_terms")]
            ])
        )
    else:
        await query.edit_message_text(
            text=f"❌ You haven't joined the channel yet. Please join {main_channel} first.\n\n"
                 f"📢 To use this bot, you must join our channel:\n"
                 f"👉 {main_channel}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{main_channel[1:]}")],
                [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
            ])
        )

async def check_payment_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check payment channel membership callback"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer("Checking payment channel...")
    
    payment_channel = get_setting('payment_channel')
    has_joined = await check_channel_membership(
        context.bot,
        user_id,
        payment_channel
    )
    
    if has_joined:
        await query.edit_message_text(
            text="✅ Great! You've joined the payment channel.\n\n"
                 "You can now proceed with withdrawal."
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=f"💸 Withdrawal Request\n\n"
                 f"Please enter the amount you want to withdraw:",
            reply_markup=ReplyKeyboardRemove()
        )
        return WAITING_FOR_WITHDRAW_AMOUNT
    else:
        await query.edit_message_text(
            text=f"❌ You still haven't joined the payment channel.\n\n"
                 f"Please join: {payment_channel}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Payment Channel", url=f"https://t.me/{payment_channel[1:]}")],
                [InlineKeyboardButton("🔄 Check Again", callback_data="check_payment_channel")]
            ])
        )

async def agree_terms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle terms agreement"""
    query = update.callback_query
    user_id = query.from_user.id
    
    update_user(user_id, has_agreed=1)
    
    welcome_bonus = float(get_setting('welcome_bonus'))
    add_balance(user_id, welcome_bonus)
    
    await query.edit_message_text(
        text=f"✅ Thank you for agreeing to our terms!\n"
             f"🎁 Welcome bonus: ${welcome_bonus:.2f} has been added to your account."
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text="🎉 Welcome to 💎 EarnX Pro Bot!\n\n"
             "Use the menu below to navigate:",
        reply_markup=get_main_keyboard()
    )

async def share_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle share link button"""
    query = update.callback_query
    user = get_user_dict(query.from_user.id)
    
    if user:
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user['referral_code']}"
        
        await query.answer("Share link opened!", show_alert=False)
        
        share_text = f"💰 Earn money with EarnX Pro Bot!\n\n" \
                     f"Use my referral link:\n{ref_link}\n\n" \
                     f"Get ${get_setting('refer_bonus')} bonus!"
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=share_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏩ Share", url=f"https://t.me/share/url?url={ref_link}&text={share_text}")]
            ])
        )

async def wallet_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet type selection"""
    query = update.callback_query
    wallet_type = query.data.split('_')[1]
    
    if wallet_type == 'usdt':
        await query.edit_message_text(
            text="💳 Please enter your USDT (TRC20) wallet address:\n\n"
                 "Format: Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
                 "Example: TJLp... (34 characters starting with T)\n\n"
                 "Type /cancel to cancel",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="wallet_back")]
            ])
        )
        context.user_data['wallet_type'] = 'USDT'
        return WAITING_FOR_USDT_ADDRESS
    elif wallet_type == 'bdt':
        await query.edit_message_text(
            text="💳 Choose your mobile banking provider:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("bKash", callback_data="bank_bkash")],
                [InlineKeyboardButton("Nagad", callback_data="bank_nagad")],
                [InlineKeyboardButton("Rocket", callback_data="bank_rocket")],
                [InlineKeyboardButton("Upay", callback_data="bank_upay")],
                [InlineKeyboardButton("🔙 Back", callback_data="wallet_back")]
            ])
        )
        return WAITING_FOR_BANK_PROVIDER

async def bank_provider_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bank provider selection"""
    query = update.callback_query
    provider = query.data.split('_')[1]
    
    context.user_data['mobile_bank'] = provider.capitalize()
    context.user_data['wallet_type'] = 'BDT'
    
    await query.edit_message_text(
        text=f"📱 Please enter your {provider.capitalize()} phone number:\n\n"
             "Format: 01XXXXXXXXX (11 digits)\n"
             "Example: 01712345678\n\n"
             "Type /cancel to cancel",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="wallet_back")]
        ])
    )
    return WAITING_FOR_PHONE_NUMBER

async def wallet_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet back button"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="💱 Choose your withdrawal currency:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("USDT", callback_data="wallet_usdt")],
            [InlineKeyboardButton("BDT", callback_data="wallet_bdt")]
        ])
    )
    return WAITING_FOR_WALLET_TYPE

async def withdraw_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal confirmation"""
    query = update.callback_query
    action = query.data
    user_id = query.from_user.id
    
    if action == 'withdraw_confirm':
        amount = context.user_data.get('withdraw_amount', 0)
        fee_percent = float(get_setting('withdraw_fee'))
        fee = amount * (fee_percent / 100)
        net_amount = amount - fee
        
        conn = sqlite3.connect('earnx_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT wallet_address, wallet_type, mobile_bank, phone_number FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            await query.edit_message_text("❌ User not found!")
            conn.close()
            return
        
        wallet_address, wallet_type, mobile_bank, phone_number = user_data
        
        cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
        
        cursor.execute('''
        INSERT INTO withdrawals 
        (user_id, amount, fee, net_amount, wallet_address, wallet_type, mobile_bank, phone_number, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            user_id, amount, fee, net_amount, 
            wallet_address, wallet_type,
            mobile_bank, phone_number
        ))
        
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            text=f"✅ Withdrawal request submitted!\n\n"
                 f"💸 Amount: ${amount:.2f}\n"
                 f"💰 Net Amount: ${net_amount:.2f}\n"
                 f"⏳ Status: Pending\n\n"
                 f"You will be notified when it's processed."
        )
        
        await context.bot.send_message(
            chat_id=user_id,
            text="Main Menu:",
            reply_markup=get_main_keyboard()
        )
        
        if ADMIN_ID:
            wallet_info = ""
            if wallet_type == 'USDT' and wallet_address:
                truncated = wallet_address[:6] + "..." + wallet_address[-4:] if wallet_address else "N/A"
                wallet_info = f"💳 Wallet: {truncated} (USDT TRC20)"
            elif wallet_type == 'BDT' and phone_number:
                wallet_info = f"💳 Wallet: {phone_number} ({mobile_bank})"
            else:
                wallet_info = "💳 Wallet: Not set"
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆕 New Withdrawal Request!\n\n"
                     f"👤 User: @{query.from_user.username or 'N/A'} ({user_id})\n"
                     f"💸 Amount: ${amount:.2f}\n"
                     f"💰 Net: ${net_amount:.2f}\n"
                     f"{wallet_info}"
            )
    
    elif action == 'withdraw_cancel':
        await query.edit_message_text(text="❌ Withdrawal cancelled.")
        await context.bot.send_message(
            chat_id=user_id,
            text="Main Menu:",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END

async def admin_approve_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin approve withdrawal"""
    query = update.callback_query
    withdraw_id = int(query.data.split('_')[1])
    
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE withdrawals SET status = "approved" WHERE id = ?', (withdraw_id,))
    
    cursor.execute('SELECT user_id, net_amount, amount FROM withdrawals WHERE id = ?', (withdraw_id,))
    withdraw = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if withdraw:
        user_id, net_amount, amount = withdraw
        
        user = get_user_dict(user_id)
        username = f"@{user['username']}" if user and user['username'] else "N/A"
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Your withdrawal has been approved!\n\n"
                     f"💰 Amount: ${net_amount:.2f} has been approved.\n"
                     f"💸 You will receive the money within 24 hours.\n\n"
                     f"Thank you for using our service!"
            )
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")
        
        await query.edit_message_text(
            text=f"✅ Withdrawal #{withdraw_id} approved!\n\n"
                 f"👤 User: {username} (ID: {user_id})\n"
                 f"💸 Amount: ${amount:.2f}\n"
                 f"💰 Net Amount: ${net_amount:.2f}\n\n"
                 f"User has been notified and will receive payment within 24 hours."
        )

async def admin_deny_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin deny withdrawal"""
    query = update.callback_query
    withdraw_id = int(query.data.split('_')[1])
    
    context.user_data['deny_withdraw_id'] = withdraw_id
    
    await query.edit_message_text(
        text=f"❌ Deny Withdrawal #{withdraw_id}\n\n"
             f"Please enter the reason for denial:"
    )
    
    return WAITING_FOR_DENY_REASON

async def handle_deny_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deny reason input"""
    reason = update.message.text.strip()
    withdraw_id = context.user_data.get('deny_withdraw_id')
    
    if not withdraw_id:
        await update.message.reply_text("❌ Error: Withdrawal ID not found!")
        return ConversationHandler.END
    
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE withdrawals SET status = "denied", admin_note = ? WHERE id = ?', (reason, withdraw_id))
    
    cursor.execute('SELECT user_id, amount FROM withdrawals WHERE id = ?', (withdraw_id,))
    withdraw = cursor.fetchone()
    
    if withdraw:
        user_id, amount = withdraw
        
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        
        user = get_user_dict(user_id)
        username = f"@{user['username']}" if user and user['username'] else "N/A"
    
    conn.commit()
    conn.close()
    
    try:
        support_chat = get_setting('support_chat')
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Your withdrawal request has been denied!\n\n"
                 f"💸 Amount: ${amount:.2f}\n"
                 f"📝 Reason: {reason}\n\n"
                 f"Your balance has been refunded.\n"
                 f"If you have any complaints, please contact our support team:\n"
                 f"{support_chat}"
        )
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")
    
    await update.message.reply_text(
        text=f"❌ Withdrawal #{withdraw_id} denied!\n\n"
             f"👤 User: {username} (ID: {user_id})\n"
             f"💸 Amount: ${amount:.2f}\n"
             f"📝 Reason: {reason}\n\n"
             f"User has been notified and balance has been refunded."
    )
    
    context.user_data.pop('deny_withdraw_id', None)
    
    return ConversationHandler.END

# ==================== COMMAND HANDLERS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    user_data = get_user_dict(user_id)
    if user_data and user_data['is_banned']:
        await update.message.reply_text(
            text=f"🚫 You are banned from using this bot.\n"
                 f"Reason: {user_data.get('ban_reason', 'Violation of terms')}\n\n"
                 f"If you think this is a mistake, please contact support.",
            reply_markup=get_banned_user_keyboard()
        )
        return
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            text=f"👑 Admin Mode Activated\n"
                 f"👋 Welcome back, {user.first_name}!\n\n"
                 f"⚙️ Admin Features:\n"
                 f"• Bot Statistics\n"
                 f"• User Management\n"
                 f"• Withdrawal Processing\n"
                 f"• System Configuration\n\n"
                 f"Use the buttons below to navigate:",
            reply_markup=get_admin_keyboard()
        )
        return
    
    if not user_data:
        ref_code = create_user(user_id, user.username, user.first_name)
        
        if context.args and len(context.args) > 0:
            ref_code_from_args = context.args[0]
            conn = sqlite3.connect('earnx_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (ref_code_from_args,))
            referrer = cursor.fetchone()
            if referrer:
                cursor.execute('UPDATE users SET referred_by = ? WHERE user_id = ?', (referrer[0], user_id))
                refer_bonus = float(get_setting('refer_bonus'))
                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', 
                              (refer_bonus, referrer[0]))
            conn.commit()
            conn.close()
    
    user_data = get_user_dict(user_id)
    
    if user_data and user_data['has_agreed']:
        await update.message.reply_text(
            text=f"👋 Welcome back, {user.first_name}!\n\n"
                 f"Use the menu below to navigate:",
            reply_markup=get_main_keyboard()
        )
    else:
        main_channel = get_setting('main_channel')
        await update.message.reply_text(
            text=f"👋 Welcome {user.first_name}!\n\n"
                 f"📢 To use this bot, you must join our channel:\n"
                 f"👉 {main_channel}\n\n"
                 f"Click the button below to join, then click 'I've Joined'.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{main_channel[1:]}")],
                [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
            ])
        )

# ==================== MESSAGE HANDLERS ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check if user is banned
    user_data = get_user_dict(user_id)
    if user_data and user_data['is_banned']:
        if text == "🆘 Help":
            await update.message.reply_text(
                text=f"📞 Contact support: {get_setting('support_chat')}",
                reply_markup=get_banned_user_keyboard()
            )
        return
    
    # Check if admin and in admin panel
    is_admin = (user_id == ADMIN_ID)
    
    # Handle user panel buttons (for both admin and regular users when in user panel)
    if text == "💰 Balance":
        await show_balance(update, context)
    elif text == "🎁 Daily Bonus":
        await daily_bonus(update, context)
    elif text == "💸 Withdraw":
        await withdraw_start(update, context)
    elif text == "👥 Referral":
        await show_referral(update, context)
    elif text == "🔐 Set Wallet":
        await set_wallet_start(update, context)
    elif text == "🆘 Help":
        await show_help(update, context)
    elif text == "📊 Statistics":
        await show_user_statistics(update, context)
    elif text == "ℹ️ About":
        await show_about(update, context)
    elif text == "🔙 Back":
        if is_admin:
            await update.message.reply_text(
                text="Admin Panel:",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text(
                text="Main Menu:",
                reply_markup=get_main_keyboard()
            )
    elif text == "📞 Support Chat":
        await update.message.reply_text(
            text=f"📞 Contact our support team:\n\n"
                 f"{get_setting('support_chat')}"
        )
    elif text == "🔙 User Panel":
        # Switch from admin to user panel
        if is_admin:
            await update.message.reply_text(
                text="Switched to User Panel",
                reply_markup=get_main_keyboard()
            )
    # Handle admin panel buttons (only for admin)
    elif is_admin and text == "📈 Bot Stats":
        await admin_bot_stats(update, context)
    elif is_admin and text == "👥 All Users":
        await admin_all_users(update, context, page=1)
    elif is_admin and text == "➕ Add Balance":
        await update.message.reply_text("Enter user ID to add balance:\n\nType /cancel to cancel")
        return ADMIN_ADD_BALANCE_USER
    elif is_admin and text == "➖ Cut Balance":
        await update.message.reply_text("Enter user ID to cut balance:\n\nType /cancel to cancel")
        return ADMIN_CUT_BALANCE_USER
    elif is_admin and text == "💸 Withdraw Request":
        await admin_withdraw_requests(update, context)
    elif is_admin and text == "📢 Broadcast":
        await update.message.reply_text(
            "📢 Broadcast Message\n\n"
            "Please enter the message you want to broadcast to all users:\n\n"
            "Type /cancel to cancel",
            reply_markup=ReplyKeyboardRemove()
        )
        return ADMIN_BROADCAST_MESSAGE
    elif is_admin and text == "🚫 Ban Manager":
        await update.message.reply_text(
            text="🚫 Ban Manager",
            reply_markup=get_ban_manager_keyboard()
        )
    elif is_admin and text == "⚙️ Bot Settings":
        await admin_bot_settings_menu(update, context)
    # Handle ban manager buttons (only for admin)
    elif is_admin and text == "🚫 Ban User":
        await update.message.reply_text("Enter user ID to ban:\n\nType /cancel to cancel")
        return ADMIN_BAN_USER_ID
    elif is_admin and text == "🔐 UnBan User":
        await update.message.reply_text("Enter user ID to unban:\n\nType /cancel to cancel")
        return ADMIN_UNBAN_USER_ID
    elif is_admin and text == "👁 View Banned":
        await admin_view_banned(update, context)
    # Handle settings buttons (only for admin)
    elif is_admin and text == "🎁Set Refer Bonus":
        current_value = get_setting('refer_bonus')
        await update.message.reply_text(
            text=f"🎁 Set Referral Bonus\n\n"
                 f"📊 Current Value: ${current_value}\n\n"
                 f"Enter new referral bonus amount:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_REF_BONUS
    elif is_admin and text == "💵Set Min Withdraw":
        current_value = get_setting('min_withdraw')
        await update.message.reply_text(
            text=f"💵 Set Minimum Withdrawal\n\n"
                 f"📊 Current Value: ${current_value}\n\n"
                 f"Enter new minimum withdrawal amount:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_MIN_WITHDRAW
    elif is_admin and text == "🎁Set Daily Bonus":
        current_value = get_setting('daily_bonus')
        await update.message.reply_text(
            text=f"🎁 Set Daily Bonus\n\n"
                 f"📊 Current Value: ${current_value}\n\n"
                 f"Enter new daily bonus amount:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_DAILY_BONUS
    elif is_admin and text == "💵Set Withdraw Fee":
        current_value = get_setting('withdraw_fee')
        await update.message.reply_text(
            text=f"💵 Set Withdrawal Fee\n\n"
                 f"📊 Current Value: {current_value}%\n\n"
                 f"Enter new withdrawal fee percentage (0-100):",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_WITHDRAW_FEE
    elif is_admin and text == "🎁Set Welcome Bonus":
        current_value = get_setting('welcome_bonus')
        await update.message.reply_text(
            text=f"🎁 Set Welcome Bonus\n\n"
                 f"📊 Current Value: ${current_value}\n\n"
                 f"Enter new welcome bonus amount:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_WELCOME_BONUS
    elif is_admin and text == "📞Set Support Chat":
        current_value = get_setting('support_chat')
        await update.message.reply_text(
            text=f"📞 Set Support Chat\n\n"
                 f"📊 Current Value: {current_value}\n\n"
                 f"Enter new support chat username (e.g., @username):",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_SUPPORT_CHAT
    elif is_admin and text == "💬Set Payment Channel":
        current_value = get_setting('payment_channel')
        await update.message.reply_text(
            text=f"💬 Set Payment Channel\n\n"
                 f"📊 Current Value: {current_value}\n\n"
                 f"Enter new payment channel username (e.g., @channel):",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_PAYMENT_CHANNEL
    elif is_admin and text == "🏠Set Main Channel":
        current_value = get_setting('main_channel')
        await update.message.reply_text(
            text=f"🏠 Set Main Channel\n\n"
                 f"📊 Current Value: {current_value}\n\n"
                 f"Enter new main channel username (e.g., @channel):",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_MAIN_CHANNEL

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user balance"""
    user_id = update.effective_user.id
    user = get_user_dict(user_id)
    
    if not user:
        await update.message.reply_text("User not found!")
        return
    
    pending_withdrawals = get_user_pending_withdrawn(user_id)
    
    wallet_info = ""
    if user['wallet_type'] == 'USDT' and user['wallet_address']:
        truncated = user['wallet_address'][:6] + "..." + user['wallet_address'][-4:]
        wallet_info = f"💳 Wallet: {truncated} (USDT TRC20)"
    elif user['wallet_type'] == 'BDT' and user['phone_number']:
        wallet_info = f"💳 Wallet: {user['phone_number']} ({user['mobile_bank']})"
    else:
        wallet_info = "❌ Wallet not set! Use '🔐 Set Wallet' to set up your wallet."
    
    await update.message.reply_text(
        text=f"💰 Your Balance:\n\n"
             f"• Current Balance: ${user['balance']:.2f}\n"
             f"• Pending Withdrawals: ${pending_withdrawals:.2f}\n"
             f"• Total Earned: ${user['total_earned']:.2f}\n\n"
             f"⚙️ Withdrawal Settings:\n"
             f"• Minimum Withdrawal: ${get_setting('min_withdraw')}\n"
             f"• Withdrawal Fee: {get_setting('withdraw_fee')}%\n\n"
             f"{wallet_info}",
        reply_markup=get_main_keyboard()
    )

async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle daily bonus claim"""
    user_id = update.effective_user.id
    user = get_user_dict(user_id)
    
    if not user:
        await update.message.reply_text("User not found!")
        return
    
    daily_bonus_amount = float(get_setting('daily_bonus'))
    
    if user['last_daily_bonus']:
        last_claim = datetime.fromisoformat(user['last_daily_bonus'])
        now = datetime.now()
        
        if (now - last_claim).total_seconds() < 24 * 3600:
            next_claim = last_claim + timedelta(hours=24)
            remaining = next_claim - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            
            await update.message.reply_text(
                text=f"⏰ You can claim your daily bonus in {hours} hours {minutes} minutes.",
                reply_markup=get_main_keyboard()
            )
            return
    
    add_balance(user_id, daily_bonus_amount)
    
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_daily_bonus = ?, daily_bonus_count = daily_bonus_count + 1, total_daily_bonus = total_daily_bonus + ? WHERE user_id = ?', 
                   (datetime.now().isoformat(), daily_bonus_amount, user_id))
    conn.commit()
    conn.close()
    
    user_updated = get_user_dict(user_id)
    
    await update.message.reply_text(
        text=f"🎁 Daily Bonus Claimed!\n\n"
             f"💰 ${daily_bonus_amount:.2f} has been added to your balance.\n"
             f"💵 New Balance: ${user_updated['balance']:.2f}",
        reply_markup=get_main_keyboard()
    )

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start withdrawal process"""
    user_id = update.effective_user.id
    user = get_user_dict(user_id)
    
    if not user['wallet_address'] and not user['phone_number']:
        await update.message.reply_text(
            text="❌ Please set your wallet first using '🔐 Set Wallet'.",
            reply_markup=get_main_keyboard()
        )
        return
    
    min_withdraw = float(get_setting('min_withdraw'))
    if user['balance'] < min_withdraw:
        await update.message.reply_text(
            text=f"❌ Minimum withdrawal amount is ${min_withdraw:.2f}\n"
                 f"💵 Your Balance: ${user['balance']:.2f}",
            reply_markup=get_main_keyboard()
        )
        return
    
    payment_channel = get_setting('payment_channel')
    has_joined_payment = await check_channel_membership(
        context.bot,
        user_id,
        payment_channel
    )
    
    if not has_joined_payment:
        await update.message.reply_text(
            text=f"📢 To withdraw, please join our payment channel:\n"
                 f"👉 {payment_channel}\n\n"
                 f"Join and try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Payment Channel", url=f"https://t.me/{payment_channel[1:]}")],
                [InlineKeyboardButton("🔄 Check Again", callback_data="check_payment_channel")]
            ])
        )
        return
    
    await update.message.reply_text(
        text=f"💸 Withdrawal Request\n\n"
             f"💵 Available Balance: ${user['balance']:.2f}\n"
             f"📈 Minimum Withdrawal: ${min_withdraw:.2f}\n\n"
             f"Please enter the amount you want to withdraw:",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return WAITING_FOR_WITHDRAW_AMOUNT

async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral information"""
    user_id = update.effective_user.id
    user = get_user_dict(user_id)
    
    if not user:
        await update.message.reply_text("User not found!")
        return
    
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*), SUM(total_earned) FROM users WHERE referred_by = ?', (user_id,))
    ref_stats = cursor.fetchone()
    conn.close()
    
    total_refs = ref_stats[0] or 0
    total_ref_earnings = float(ref_stats[1] or 0) * 0.1
    
    bot_username = BOT_USERNAME
    ref_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    
    ref_bonus = get_setting('refer_bonus')
    
    await update.message.reply_text(
        text=f"*👥 Referral System*\n\n"
             f"*🔗 Your Referral Link:*\n"
             f"```\n{ref_link}\n```\n\n"
             f"*🎫 Your Referral Code:*\n"
             f"```\n{user['referral_code']}\n```\n\n"
             f"*💰 Referral Bonus:* `${ref_bonus}` per user\n"
             f"*💵 Total Referral Earnings:* `${total_ref_earnings:.2f}`\n"
             f"*👥 Total Referrals:* {total_refs}\n\n"
             f"_Share your link and earn money!_",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏩ Share Link", callback_data="share_link")]
        ]),
        parse_mode='Markdown'
    )

async def set_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start wallet setup process"""
    await update.message.reply_text(
        text="💱 Choose your withdrawal currency:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("USDT", callback_data="wallet_usdt")],
            [InlineKeyboardButton("BDT", callback_data="wallet_bdt")]
        ])
    )
    
    return WAITING_FOR_WALLET_TYPE

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    await update.message.reply_text(
        text="🆘 Help & Support\n\n"
             "📋 How to use this bot:\n"
             "1. Join our channel to start\n"
             "2. Agree to terms and conditions\n"
             "3. Claim daily bonus every 24 hours\n"
             "4. Refer friends to earn more\n"
             "5. Set your wallet for withdrawal\n"
             "6. Withdraw when you reach minimum amount\n\n"
             "💡 Tips:\n"
             "• Check balance regularly\n"
             "• Join payment channel for withdrawals\n"
             "• Keep your wallet info updated\n\n"
             f"For any issues, contact support:\n{get_setting('support_chat')}",
        reply_markup=get_help_keyboard()
    )

async def show_user_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    user = get_user_dict(user_id)
    
    if not user:
        await update.message.reply_text("User not found!")
        return
    
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
    ref_count = cursor.fetchone()[0] or 0
    
    total_withdrawn = get_user_total_withdrawn(user_id)
    pending_withdrawn = get_user_pending_withdrawn(user_id)
    
    conn.close()
    
    statistics_text = f"📊 Your Statistics\n\n"
    statistics_text += f"👤 Account:\n"
    statistics_text += f"• ID: {user_id}\n"
    statistics_text += f"• Username: @{user['username'] if user['username'] else 'N/A'}\n"
    statistics_text += f"• Member Since: {user['joined_date'][:10]}\n\n"
    
    statistics_text += f"💰 Earnings:\n"
    statistics_text += f"• Balance: ${user['balance']:.2f}\n"
    statistics_text += f"• Total Earned: ${user['total_earned']:.2f}\n"
    statistics_text += f"• Total Withdrawn: ${total_withdrawn:.2f}\n"
    statistics_text += f"• Pending Withdrawn: ${pending_withdrawn:.2f}\n\n"
    
    statistics_text += f"👥 Referrals:\n"
    statistics_text += f"• Total: {ref_count} friends\n\n"
    
    statistics_text += f"🎁 Bonuses:\n"
    statistics_text += f"• Claimed: {user['daily_bonus_count']} times\n"
    statistics_text += f"• Total Bonus: ${user['total_daily_bonus']:.2f}"
    
    await update.message.reply_text(
        text=statistics_text,
        reply_markup=get_main_keyboard()
    )

async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show about information"""
    await update.message.reply_text(
        text="💎 EarnX Pro Bot\n"
             "Version: 1.0.0\n\n"
             "📊 Statistics:\n"
             f"• Total Users: {get_total_users()}\n"
             f"• Total Withdrawn: ${get_total_withdrawn():.2f}\n\n"
             "💎 Features:\n"
             "• Daily Bonuses\n"
             "• Referral System\n"
             "• Secure Withdrawals\n"
             "• 24/7 Support\n\n"
             "Made with ❤️ for Telegram users",
        reply_markup=get_main_keyboard()
    )

# ==================== WALLET SETUP HANDLERS ====================
async def handle_usdt_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle USDT address input"""
    user_id = update.effective_user.id
    address = update.message.text.strip()
    
    if not address.startswith('T') or len(address) != 34:
        await update.message.reply_text(
            text="❌ Invalid USDT (TRC20) address!\n\n"
                 "Format must be:\n"
                 "• Starts with 'T'\n"
                 "• Exactly 34 characters\n\n"
                 "Please enter a valid address:"
        )
        return WAITING_FOR_USDT_ADDRESS
    
    update_user(user_id, 
                wallet_address=address,
                wallet_type='USDT',
                mobile_bank=None,
                phone_number=None)
    
    truncated = address[:6] + "..." + address[-4:]
    
    await update.message.reply_text(
        text=f"✅ USDT wallet set successfully!\n"
             f"Address: {truncated}",
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END

async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input"""
    user_id = update.effective_user.id
    phone = update.message.text.strip()
    
    if not phone.isdigit() or len(phone) != 11 or not phone.startswith('01'):
        await update.message.reply_text(
            text="❌ Invalid phone number!\n\n"
                 "Format must be:\n"
                 "• 11 digits\n"
                 "• Starts with '01'\n\n"
                 "Example: 01712345678\n\n"
                 "Please enter a valid phone number:"
        )
        return WAITING_FOR_PHONE_NUMBER
    
    mobile_bank = context.user_data.get('mobile_bank', '')
    update_user(user_id,
                phone_number=phone,
                mobile_bank=mobile_bank,
                wallet_type='BDT',
                wallet_address=None)
    
    await update.message.reply_text(
        text=f"✅ {mobile_bank} wallet set successfully!\n"
             f"Phone: {phone}",
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END

async def handle_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal amount input"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number:")
        return WAITING_FOR_WITHDRAW_AMOUNT
    
    user = get_user_dict(user_id)
    min_withdraw = float(get_setting('min_withdraw'))
    
    if amount < min_withdraw:
        await update.message.reply_text(
            text=f"❌ Minimum withdrawal is ${min_withdraw:.2f}\n"
                 f"Please enter amount ≥ ${min_withdraw:.2f}:"
        )
        return WAITING_FOR_WITHDRAW_AMOUNT
    
    if amount > user['balance']:
        await update.message.reply_text(
            text=f"❌ Insufficient balance!\n"
                 f"Your balance: ${user['balance']:.2f}\n"
                 f"Please enter a smaller amount:"
        )
        return WAITING_FOR_WITHDRAW_AMOUNT
    
    fee_percent = float(get_setting('withdraw_fee'))
    fee = amount * (fee_percent / 100)
    net_amount = amount - fee
    
    wallet_info = ""
    if user['wallet_type'] == 'USDT':
        truncated = user['wallet_address'][:6] + "..." + user['wallet_address'][-4:]
        wallet_info = f"💳 Wallet: {truncated} (USDT TRC20)"
    else:
        wallet_info = f"💳 Wallet: {user['phone_number']} ({user['mobile_bank']})"
    
    context.user_data['withdraw_amount'] = amount
    
    await update.message.reply_text(
        text=f"📋 Withdrawal Details:\n\n"
             f"💸 Amount: ${amount:.2f}\n"
             f"📉 Fee ({fee_percent}%): ${fee:.2f}\n"
             f"💰 Net Amount: ${net_amount:.2f}\n"
             f"{wallet_info}\n\n"
             f"Please confirm your withdrawal:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Send", callback_data="withdraw_confirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="withdraw_cancel")]
        ])
    )
    
    return WAITING_FOR_CONFIRM_WITHDRAW

# ==================== ADMIN HANDLERS ====================
async def admin_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin bot statistics"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT COUNT(*) FROM users 
    WHERE joined_date > datetime('now', '-1 day')
    ''')
    active_today = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1')
    banned_users = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(balance) FROM users')
    total_balance = cursor.fetchone()[0] or 0
    
    pending_withdrawals = get_pending_withdrawals()
    
    conn.close()
    
    await update.message.reply_text(
        text=f"📊 Bot Statistics\n\n"
             f"👥 Users:\n"
             f"• Total Users: {get_total_users()}\n"
             f"• Active Today: {active_today}\n"
             f"• Banned Users: {banned_users}\n\n"
             f"💰 Financials:\n"
             f"• Total Balance: ${total_balance:.2f}\n"
             f"• Total Withdrawn: ${get_total_withdrawn():.2f}\n"
             f"• Pending Withdrawals: {pending_withdrawals}\n\n"
             f"⚙️ Settings:\n"
             f"• Refer Bonus: ${get_setting('refer_bonus')}\n"
             f"• Min Withdraw: ${get_setting('min_withdraw')}\n"
             f"• Daily Bonus: ${get_setting('daily_bonus')}\n"
             f"• Welcome Bonus: ${get_setting('welcome_bonus')}\n"
             f"• Withdraw Fee: {get_setting('withdraw_fee')}%\n"
             f"• Currency: {get_setting('currency')}\n"
             f"• Main Channel: {get_setting('main_channel')}\n"
             f"• Payment Channel: {get_setting('payment_channel')}\n"
             f"• Support Chat: {get_setting('support_chat')}",
        reply_markup=get_admin_keyboard()
    )

async def admin_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    """Show all users with pagination"""
    limit = 10
    offset = (page - 1) * limit
    
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT user_id, username, first_name, balance, total_earned, joined_date 
    FROM users 
    WHERE is_banned = 0
    ORDER BY user_id 
    LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    users = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 0')
    total_users = cursor.fetchone()[0] or 0
    total_pages = (total_users + limit - 1) // limit
    
    conn.close()
    
    if not users:
        await update.message.reply_text("No users found!")
        return
    
    message = f"👥 All Users (Page {page}/{total_pages})\n\n"
    
    for user in users:
        user_id, username, first_name, balance, total_earned, joined_date = user
        
        conn = sqlite3.connect('earnx_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
        ref_count = cursor.fetchone()[0] or 0
        conn.close()
        
        message += f"👤 ID: {user_id}\n"
        message += f"📛 Name: {first_name}\n"
        message += f"📧 Username: @{username if username else 'N/A'}\n"
        message += f"💰 Balance: ${balance:.2f}\n"
        message += f"💵 Earned: ${total_earned:.2f}\n"
        message += f"👥 Refs: {ref_count}\n"
        message += f"📅 Joined: {joined_date[:10]}\n"
        message += "─" * 20 + "\n"
    
    keyboard = []
    if page > 1:
        keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_users_{page-1}"))
    
    keyboard.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        keyboard.append(InlineKeyboardButton("Next ➡️", callback_data=f"admin_users_{page+1}"))
    
    reply_markup = InlineKeyboardMarkup([keyboard])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text=message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=message, reply_markup=reply_markup)

async def admin_withdraw_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending withdrawal requests"""
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT w.id, w.user_id, u.username, w.amount, w.fee, w.net_amount, 
           w.wallet_address, w.wallet_type, w.mobile_bank, w.phone_number, w.created_at
    FROM withdrawals w
    JOIN users u ON w.user_id = u.user_id
    WHERE w.status = 'pending'
    ORDER BY w.created_at
    LIMIT 10
    ''')
    
    withdrawals = cursor.fetchall()
    conn.close()
    
    if not withdrawals:
        await update.message.reply_text("No pending withdrawals!")
        return
    
    for withdraw in withdrawals:
        (withdraw_id, user_id, username, amount, fee, net_amount, 
         wallet_addr, wallet_type, mobile_bank, phone, created_at) = withdraw
        
        if wallet_type == 'USDT':
            truncated = wallet_addr[:6] + "..." + wallet_addr[-4:] if wallet_addr else "N/A"
            wallet_info = f"💳 Wallet: {truncated} (USDT TRC20)"
        else:
            wallet_info = f"💳 Wallet: {phone} ({mobile_bank})"
        
        await update.message.reply_text(
            text=f"💸 Withdrawal Request #{withdraw_id}\n\n"
                 f"👤 User: @{username or 'N/A'} (ID: {user_id})\n"
                 f"💸 Amount: ${amount:.2f}\n"
                 f"📉 Fee: ${fee:.2f}\n"
                 f"💰 Net: ${net_amount:.2f}\n"
                 f"{wallet_info}\n"
                 f"📅 Requested: {created_at[:16]}\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{withdraw_id}"),
                 InlineKeyboardButton("❎ Deny", callback_data=f"deny_{withdraw_id}")]
            ])
        )

async def admin_bot_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot settings menu"""
    await update.message.reply_text(
        text="⚙️ Bot Settings - Click any button to change:",
        reply_markup=get_settings_keyboard()
    )

async def admin_view_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show banned users"""
    banned_users = get_banned_users()
    
    if not banned_users:
        await update.message.reply_text("No banned users!")
        return
    
    message = "🚫 Banned Users:\n\n"
    
    for user in banned_users:
        user_id, username, first_name, ban_reason = user
        
        message += f"👤 ID: {user_id}\n"
        message += f"📛 Name: {first_name}\n"
        message += f"📧 Username: @{username if username else 'N/A'}\n"
        message += f"📝 Reason: {ban_reason or 'Not specified'}\n"
        message += "─" * 20 + "\n"
    
    await update.message.reply_text(text=message)

# ==================== ADMIN CONVERSATION HANDLERS ====================
async def admin_add_balance_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin add balance - user ID input"""
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID! Please enter a number:")
        return ADMIN_ADD_BALANCE_USER
    
    user = get_user_dict(user_id)
    if not user:
        await update.message.reply_text("❌ User not found! Please enter a valid user ID:")
        return ADMIN_ADD_BALANCE_USER
    
    context.user_data['add_balance_user'] = user_id
    
    await update.message.reply_text(
        text=f"👤 User: {user['first_name']}\n"
             f"💰 Current Balance: ${user['balance']:.2f}\n\n"
             f"Enter amount to add:"
    )
    
    return ADMIN_ADD_BALANCE_AMOUNT

async def admin_add_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin add balance - amount input"""
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Please enter a number:")
        return ADMIN_ADD_BALANCE_AMOUNT
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive! Please enter a valid amount:")
        return ADMIN_ADD_BALANCE_AMOUNT
    
    user_id = context.user_data.get('add_balance_user')
    user = get_user_dict(user_id)
    
    new_balance = user['balance'] + amount
    
    await update.message.reply_text(
        text=f"📋 Add Balance Preview:\n\n"
             f"👤 User: {user['first_name']} (ID: {user_id})\n"
             f"💰 Current: ${user['balance']:.2f}\n"
             f"💵 Add: ${amount:.2f}\n"
             f"💳 New: ${new_balance:.2f}\n\n"
             f"Confirm adding balance?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data=f"admin_confirm_add_{amount}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel_action")]
        ])
    )
    
    return ConversationHandler.END

async def admin_cut_balance_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin cut balance - user ID input"""
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID! Please enter a number:")
        return ADMIN_CUT_BALANCE_USER
    
    user = get_user_dict(user_id)
    if not user:
        await update.message.reply_text("❌ User not found! Please enter a valid user ID:")
        return ADMIN_CUT_BALANCE_USER
    
    context.user_data['cut_balance_user'] = user_id
    
    await update.message.reply_text(
        text=f"👤 User: {user['first_name']}\n"
             f"💰 Current Balance: ${user['balance']:.2f}\n\n"
             f"Enter amount to cut:"
    )
    
    return ADMIN_CUT_BALANCE_AMOUNT

async def admin_cut_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin cut balance - amount input"""
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Please enter a number:")
        return ADMIN_CUT_BALANCE_AMOUNT
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive! Please enter a valid amount:")
        return ADMIN_CUT_BALANCE_AMOUNT
    
    user_id = context.user_data.get('cut_balance_user')
    user = get_user_dict(user_id)
    
    if amount > user['balance']:
        await update.message.reply_text(
            text=f"❌ Amount exceeds user's balance!\n"
                 f"Balance: ${user['balance']:.2f}\n"
                 f"Please enter a smaller amount:"
        )
        return ADMIN_CUT_BALANCE_AMOUNT
    
    new_balance = user['balance'] - amount
    
    await update.message.reply_text(
        text=f"📋 Cut Balance Preview:\n\n"
             f"👤 User: {user['first_name']} (ID: {user_id})\n"
             f"💰 Current: ${user['balance']:.2f}\n"
             f"💵 Cut: ${amount:.2f}\n"
             f"💳 New: ${new_balance:.2f}\n\n"
             f"Confirm cutting balance?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data=f"admin_confirm_cut_{amount}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel_action")]
        ])
    )
    
    return ConversationHandler.END

async def admin_ban_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin ban - user ID input"""
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID! Please enter a number:")
        return ADMIN_BAN_USER_ID
    
    user = get_user_dict(user_id)
    if not user:
        await update.message.reply_text("❌ User not found! Please enter a valid user ID:")
        return ADMIN_BAN_USER_ID
    
    if user['is_banned']:
        await update.message.reply_text("❌ User is already banned!")
        return ConversationHandler.END
    
    context.user_data['ban_user_id'] = user_id
    
    await update.message.reply_text("Enter ban reason:")
    return ADMIN_BAN_REASON

async def admin_ban_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin ban - reason input"""
    reason = update.message.text.strip()
    user_id = context.user_data.get('ban_user_id')
    
    update_user(user_id, is_banned=1, ban_reason=reason)
    
    await update.message.reply_text(f"✅ User {user_id} has been banned!")
    return ConversationHandler.END

async def admin_unban_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin unban - user ID input"""
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID! Please enter a number:")
        return ADMIN_UNBAN_USER_ID
    
    user = get_user_dict(user_id)
    if not user:
        await update.message.reply_text("❌ User not found! Please enter a valid user ID:")
        return ADMIN_UNBAN_USER_ID
    
    if not user['is_banned']:
        await update.message.reply_text("❌ User is not banned!")
        return ConversationHandler.END
    
    update_user(user_id, is_banned=0, ban_reason=None)
    
    await update.message.reply_text(f"✅ User {user_id} has been unbanned!")
    return ConversationHandler.END

async def admin_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin broadcast message input"""
    message = update.message.text.strip()
    
    if message.lower() == "/cancel":
        await update.message.reply_text(
            text="❌ Broadcast cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END
    
    if not message or len(message.strip()) == 0:
        await update.message.reply_text("❌ Message cannot be empty! Please enter a valid message:")
        return ADMIN_BROADCAST_MESSAGE
    
    total_users = get_total_users()
    context.user_data['broadcast_message'] = message
    
    await update.message.reply_text(
        text=f"📢 Broadcast Preview\n\n"
             f"📊 Message will be sent to {total_users} users.\n\n"
             f"📝 Content:\n{message}\n\n"
             f"✅ Send this broadcast?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Send", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")]
        ])
    )
    
    return ConversationHandler.END

async def broadcast_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and send broadcast"""
    query = update.callback_query
    await query.answer()
    
    message = context.user_data.get('broadcast_message', '')
    
    if not message:
        await query.edit_message_text("❌ No message to broadcast!")
        return
    
    conn = sqlite3.connect('earnx_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE is_banned = 0')
    users = cursor.fetchall()
    conn.close()
    
    total = len(users)
    sent = 0
    failed = 0
    
    await query.edit_message_text(f"📤 Broadcasting to {total} users...\n\nSent: 0/{total}")
    
    for user_tuple in users:
        user_id = user_tuple[0]
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            sent += 1
            if sent % 10 == 0:
                await query.edit_message_text(
                    f"📤 Broadcasting to {total} users...\n\nSent: {sent}/{total}"
                )
        except Exception as e:
            failed += 1
            print(f"Failed to send to {user_id}: {e}")
    
    await query.edit_message_text(
        f"✅ Broadcast completed!\n\n"
        f"📊 Results:\n"
        f"• Total Users: {total}\n"
        f"• Successfully Sent: {sent}\n"
        f"• Failed: {failed}"
    )
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Broadcast completed. Returning to admin panel...",
        reply_markup=get_admin_keyboard()
    )
    
    context.user_data.pop('broadcast_message', None)

async def broadcast_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel broadcast"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="❌ Broadcast cancelled."
    )
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Returning to admin panel...",
        reply_markup=get_admin_keyboard()
    )
    
    context.user_data.pop('broadcast_message', None)

# ==================== SETTINGS CONVERSATION HANDLERS ====================
async def setting_ref_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting referral bonus"""
    try:
        value = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Please enter a number:")
        return SETTING_REF_BONUS
    
    if value <= 0:
        await update.message.reply_text("❌ Amount must be positive! Please enter a valid amount:")
        return SETTING_REF_BONUS
    
    current = get_setting('refer_bonus')
    context.user_data['setting_type'] = 'refer_bonus'
    context.user_data['setting_value'] = str(value)
    context.user_data['setting_current'] = current
    
    await update.message.reply_text(
        text=f"📋 Preview Setting Change:\n\n"
             f"🎁 Referral Bonus\n"
             f"📊 Current Value: ${current}\n"
             f"📈 New Value: ${value:.2f}\n\n"
             f"Confirm change?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_setting")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setting")]
        ])
    )
    
    return ConversationHandler.END

async def setting_min_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting minimum withdrawal"""
    try:
        value = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Please enter a number:")
        return SETTING_MIN_WITHDRAW
    
    if value <= 0:
        await update.message.reply_text("❌ Amount must be positive! Please enter a valid amount:")
        return SETTING_MIN_WITHDRAW
    
    current = get_setting('min_withdraw')
    context.user_data['setting_type'] = 'min_withdraw'
    context.user_data['setting_value'] = str(value)
    context.user_data['setting_current'] = current
    
    await update.message.reply_text(
        text=f"📋 Preview Setting Change:\n\n"
             f"💵 Minimum Withdrawal\n"
             f"📊 Current Value: ${current}\n"
             f"📈 New Value: ${value:.2f}\n\n"
             f"Confirm change?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_setting")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setting")]
        ])
    )
    
    return ConversationHandler.END

async def setting_daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting daily bonus"""
    try:
        value = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Please enter a number:")
        return SETTING_DAILY_BONUS
    
    if value <= 0:
        await update.message.reply_text("❌ Amount must be positive! Please enter a valid amount:")
        return SETTING_DAILY_BONUS
    
    current = get_setting('daily_bonus')
    context.user_data['setting_type'] = 'daily_bonus'
    context.user_data['setting_value'] = str(value)
    context.user_data['setting_current'] = current
    
    await update.message.reply_text(
        text=f"📋 Preview Setting Change:\n\n"
             f"🎁 Daily Bonus\n"
             f"📊 Current Value: ${current}\n"
             f"📈 New Value: ${value:.2f}\n\n"
             f"Confirm change?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_setting")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setting")]
        ])
    )
    
    return ConversationHandler.END

async def setting_welcome_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting welcome bonus"""
    try:
        value = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Please enter a number:")
        return SETTING_WELCOME_BONUS
    
    if value <= 0:
        await update.message.reply_text("❌ Amount must be positive! Please enter a valid amount:")
        return SETTING_WELCOME_BONUS
    
    current = get_setting('welcome_bonus')
    context.user_data['setting_type'] = 'welcome_bonus'
    context.user_data['setting_value'] = str(value)
    context.user_data['setting_current'] = current
    
    await update.message.reply_text(
        text=f"📋 Preview Setting Change:\n\n"
             f"🎁 Welcome Bonus\n"
             f"📊 Current Value: ${current}\n"
             f"📈 New Value: ${value:.2f}\n\n"
             f"Confirm change?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_setting")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setting")]
        ])
    )
    
    return ConversationHandler.END

async def setting_withdraw_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting withdrawal fee"""
    try:
        value = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid percentage! Please enter a number:")
        return SETTING_WITHDRAW_FEE
    
    if value < 0 or value > 100:
        await update.message.reply_text("❌ Percentage must be between 0-100! Please enter a valid percentage:")
        return SETTING_WITHDRAW_FEE
    
    current = get_setting('withdraw_fee')
    context.user_data['setting_type'] = 'withdraw_fee'
    context.user_data['setting_value'] = str(value)
    context.user_data['setting_current'] = current
    
    await update.message.reply_text(
        text=f"📋 Preview Setting Change:\n\n"
             f"💵 Withdrawal Fee\n"
             f"📊 Current Value: {current}%\n"
             f"📈 New Value: {value:.1f}%\n\n"
             f"Confirm change?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_setting")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setting")]
        ])
    )
    
    return ConversationHandler.END

async def setting_support_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting support chat"""
    value = update.message.text.strip()
    
    if not value.startswith('@'):
        await update.message.reply_text("❌ Username must start with @! Please enter a valid username:")
        return SETTING_SUPPORT_CHAT
    
    current = get_setting('support_chat')
    context.user_data['setting_type'] = 'support_chat'
    context.user_data['setting_value'] = value
    context.user_data['setting_current'] = current
    
    await update.message.reply_text(
        text=f"📋 Preview Setting Change:\n\n"
             f"📞 Support Chat\n"
             f"📊 Current Value: {current}\n"
             f"📈 New Value: {value}\n\n"
             f"Confirm change?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_setting")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setting")]
        ])
    )
    
    return ConversationHandler.END

async def setting_payment_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting payment channel"""
    value = update.message.text.strip()
    
    if not value.startswith('@'):
        await update.message.reply_text("❌ Channel username must start with @! Please enter a valid channel username:")
        return SETTING_PAYMENT_CHANNEL
    
    current = get_setting('payment_channel')
    context.user_data['setting_type'] = 'payment_channel'
    context.user_data['setting_value'] = value
    context.user_data['setting_current'] = current
    
    await update.message.reply_text(
        text=f"📋 Preview Setting Change:\n\n"
             f"💬 Payment Channel\n"
             f"📊 Current Value: {current}\n"
             f"📈 New Value: {value}\n\n"
             f"Confirm change?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_setting")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setting")]
        ])
    )
    
    return ConversationHandler.END

async def setting_main_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting main channel"""
    value = update.message.text.strip()
    
    if not value.startswith('@'):
        await update.message.reply_text("❌ Channel username must start with @! Please enter a valid channel username:")
        return SETTING_MAIN_CHANNEL
    
    current = get_setting('main_channel')
    context.user_data['setting_type'] = 'main_channel'
    context.user_data['setting_value'] = value
    context.user_data['setting_current'] = current
    
    await update.message.reply_text(
        text=f"📋 Preview Setting Change:\n\n"
             f"🏠 Main Channel\n"
             f"📊 Current Value: {current}\n"
             f"📈 New Value: {value}\n\n"
             f"Confirm change?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_setting")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setting")]
        ])
    )
    
    return ConversationHandler.END

# ==================== CALLBACK QUERY HANDLERS ====================
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    data = query.data
    
    try:
        await query.answer()
        
        if data == "check_join":
            await check_join_callback(update, context)
        elif data == "check_payment_channel":
            await check_payment_channel_callback(update, context)
        elif data == "agree_terms":
            await agree_terms_callback(update, context)
        elif data == "share_link":
            await share_link_callback(update, context)
        elif data.startswith("wallet_"):
            result = await wallet_type_callback(update, context)
            if result:
                return result
        elif data.startswith("bank_"):
            result = await bank_provider_callback(update, context)
            if result:
                return result
        elif data == "wallet_back":
            result = await wallet_back_callback(update, context)
            if result:
                return result
        elif data in ["withdraw_confirm", "withdraw_cancel"]:
            result = await withdraw_confirm_callback(update, context)
            if result:
                return result
        elif data.startswith("approve_"):
            await admin_approve_withdraw(update, context)
        elif data.startswith("deny_"):
            await admin_deny_withdraw(update, context)
        elif data.startswith("admin_users_"):
            page = int(data.split('_')[2])
            await admin_all_users(update, context, page=page)
        elif data.startswith("admin_confirm_add_"):
            amount = float(data.split('_')[3])
            user_id = context.user_data.get('add_balance_user')
            add_balance(user_id, amount)
            await query.edit_message_text(f"✅ Added ${amount:.2f} to user {user_id}")
            context.user_data.pop('add_balance_user', None)
        elif data.startswith("admin_confirm_cut_"):
            amount = float(data.split('_')[3])
            user_id = context.user_data.get('cut_balance_user')
            add_balance(user_id, -amount)
            await query.edit_message_text(f"✅ Cut ${amount:.2f} from user {user_id}")
            context.user_data.pop('cut_balance_user', None)
        elif data == "admin_cancel_action":
            await query.edit_message_text("❌ Action cancelled.")
            context.user_data.pop('add_balance_user', None)
            context.user_data.pop('cut_balance_user', None)
        elif data == "broadcast_confirm":
            await broadcast_confirm_callback(update, context)
        elif data == "broadcast_cancel":
            await broadcast_cancel_callback(update, context)
        elif data == "confirm_setting":
            setting_type = context.user_data.get('setting_type')
            setting_value = context.user_data.get('setting_value')
            setting_current = context.user_data.get('setting_current')
            
            if setting_type and setting_value:
                update_setting(setting_type, setting_value)
                
                if setting_type in ['refer_bonus', 'min_withdraw', 'daily_bonus', 'welcome_bonus']:
                    message = f"✅ {setting_type.replace('_', ' ').title()} updated!\n\n"
                    message += f"📊 Old Value: ${setting_current}\n"
                    message += f"📈 New Value: ${float(setting_value):.2f}"
                elif setting_type == 'withdraw_fee':
                    message = f"✅ {setting_type.replace('_', ' ').title()} updated!\n\n"
                    message += f"📊 Old Value: {setting_current}%\n"
                    message += f"📈 New Value: {float(setting_value):.1f}%"
                else:
                    message = f"✅ {setting_type.replace('_', ' ').title()} updated!\n\n"
                    message += f"📊 Old Value: {setting_current}\n"
                    message += f"📈 New Value: {setting_value}"
                
                await query.edit_message_text(text=message)
                
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="Returning to settings menu...",
                    reply_markup=get_settings_keyboard()
                )
                
                context.user_data.pop('setting_type', None)
                context.user_data.pop('setting_value', None)
                context.user_data.pop('setting_current', None)
            else:
                await query.edit_message_text("❌ Error: Setting data not found!")
                
        elif data == "cancel_setting":
            setting_type = context.user_data.get('setting_type', 'Unknown')
            
            await query.edit_message_text(
                text=f"❌ {setting_type.replace('_', ' ').title()} change cancelled."
            )
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Returning to settings menu...",
                reply_markup=get_settings_keyboard()
            )
            
            context.user_data.pop('setting_type', None)
            context.user_data.pop('setting_value', None)
            context.user_data.pop('setting_current', None)
            
        elif data == "admin_panel_back":
            await query.edit_message_text(
                text="Admin Panel",
                reply_markup=get_admin_keyboard()
            )
        elif data == "noop":
            await query.answer()
    
    except Exception as e:
        print(f"Error in handle_callback_query: {e}")
        await query.answer("An error occurred. Please try again.")

# ==================== CANCEL HANDLER ====================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any conversation"""
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            text="❌ Operation cancelled.",
            reply_markup=get_admin_keyboard()
        )
    else:
        await update.message.reply_text(
            text="❌ Operation cancelled.",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot"""
    init_db()
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    
    wallet_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔐 Set Wallet$"), set_wallet_start)],
        states={
            WAITING_FOR_WALLET_TYPE: [
                CallbackQueryHandler(wallet_type_callback, pattern="^wallet_"),
                CallbackQueryHandler(wallet_back_callback, pattern="^wallet_back$")
            ],
            WAITING_FOR_USDT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_usdt_address),
                CallbackQueryHandler(wallet_back_callback, pattern="^wallet_back$")
            ],
            WAITING_FOR_BANK_PROVIDER: [
                CallbackQueryHandler(bank_provider_callback, pattern="^bank_"),
                CallbackQueryHandler(wallet_back_callback, pattern="^wallet_back$")
            ],
            WAITING_FOR_PHONE_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number),
                CallbackQueryHandler(wallet_back_callback, pattern="^wallet_back$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern="^wallet_back$")
        ]
    )
    application.add_handler(wallet_conv_handler)
    
    withdraw_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💸 Withdraw$"), withdraw_start)],
        states={
            WAITING_FOR_WITHDRAW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_amount)
            ],
            WAITING_FOR_CONFIRM_WITHDRAW: [
                CallbackQueryHandler(withdraw_confirm_callback, pattern="^withdraw_")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(withdraw_conv_handler)
    
    admin_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Add Balance$"), 
                         lambda u, c: admin_add_balance_user(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^➖ Cut Balance$"), 
                         lambda u, c: admin_cut_balance_user(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^🚫 Ban User$"), 
                         lambda u, c: admin_ban_user_id(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^🔐 UnBan User$"), 
                         lambda u, c: admin_unban_user_id(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^📢 Broadcast$"), 
                         lambda u, c: admin_broadcast_message(u, c) if u.effective_user.id == ADMIN_ID else None)
        ],
        states={
            ADMIN_ADD_BALANCE_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_balance_user)
            ],
            ADMIN_ADD_BALANCE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_balance_amount)
            ],
            ADMIN_CUT_BALANCE_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_cut_balance_user)
            ],
            ADMIN_CUT_BALANCE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_cut_balance_amount)
            ],
            ADMIN_BAN_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_user_id)
            ],
            ADMIN_BAN_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_reason)
            ],
            ADMIN_UNBAN_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_unban_user_id)
            ],
            ADMIN_BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_message)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(admin_conv_handler)
    
    deny_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_deny_withdraw, pattern="^deny_")
        ],
        states={
            WAITING_FOR_DENY_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deny_reason)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(deny_conv_handler)
    
    settings_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🎁Set Refer Bonus$"), 
                         lambda u, c: setting_ref_bonus(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^💵Set Min Withdraw$"), 
                         lambda u, c: setting_min_withdraw(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^🎁Set Daily Bonus$"), 
                         lambda u, c: setting_daily_bonus(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^🎁Set Welcome Bonus$"), 
                         lambda u, c: setting_welcome_bonus(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^💵Set Withdraw Fee$"), 
                         lambda u, c: setting_withdraw_fee(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^📞Set Support Chat$"), 
                         lambda u, c: setting_support_chat(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^💬Set Payment Channel$"), 
                         lambda u, c: setting_payment_channel(u, c) if u.effective_user.id == ADMIN_ID else None),
            MessageHandler(filters.Regex("^🏠Set Main Channel$"), 
                         lambda u, c: setting_main_channel(u, c) if u.effective_user.id == ADMIN_ID else None)
        ],
        states={
            SETTING_REF_BONUS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setting_ref_bonus)
            ],
            SETTING_MIN_WITHDRAW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setting_min_withdraw)
            ],
            SETTING_DAILY_BONUS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setting_daily_bonus)
            ],
            SETTING_WELCOME_BONUS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setting_welcome_bonus)
            ],
            SETTING_WITHDRAW_FEE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setting_withdraw_fee)
            ],
            SETTING_SUPPORT_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setting_support_chat)
            ],
            SETTING_PAYMENT_CHANNEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setting_payment_channel)
            ],
            SETTING_MAIN_CHANNEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setting_main_channel)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(settings_conv_handler)
    
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 EarnX Pro Bot is running...")
    print("⚠️ IMPORTANT: Make sure bot is admin in both channels!")
    print(f"1. Main Channel: {MAIN_CHANNEL}")
    print(f"2. Payment Channel: {PAYMENT_CHANNEL}")
    print(f"3. Support Chat: {SUPPORT_CHAT}")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"🤖 Bot Username: @{BOT_USERNAME}")
    print(f"🎁 Default Bonuses from .env:")
    print(f"   • Referral Bonus: ${REFERRAL_BONUS}")
    print(f"   • Daily Bonus: ${DAILY_BONUS}")
    print(f"   • Welcome Bonus: ${WELCOME_BONUS}")
    print(f"   • Min Withdraw: ${MIN_WITHDRAW}")
    print(f"   • Withdraw Fee: {WITHDRAW_FEE}%")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    main()
