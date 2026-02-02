# 💎 EarnX Pro Bot - Complete Telegram Earning Bot

A fully-featured Telegram earning bot with channel membership verification, referral system, daily bonuses, and withdrawal functionality.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🌟 Features

- **Channel Membership Verification** - Users must join channels to use the bot
- **Referral System** - Earn from referrals with bonus rewards
- **Daily Bonuses** - Claim bonuses every 24 hours
- **Withdrawal System** - Support for USDT (TRC20) and BDT (Mobile Banking)
- **Admin Panel** - Complete admin control with statistics
- **Wallet Management** - Secure wallet setup and management
- **Real-time Statistics** - Track earnings and referrals

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Telegram Account with Admin privileges

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/EarnX-Pro-Bot.git
cd EarnX-Pro-Bot

Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Step 3: Configure Environment

```bash
cp .env.example .env
```

Step 4: Edit Environment File

Edit .env file with your credentials:

```env
# ==================== BOT CONFIGURATION ====================
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_user_id
BOT_USERNAME=@your_bot_username

# ==================== CHANNEL SETTINGS ====================
MAIN_CHANNEL=@your_main_channel
PAYMENT_CHANNEL=@your_payment_channel
SUPPORT_CHAT=@your_support_chat

# ==================== FINANCIAL SETTINGS ====================
REFERRAL_BONUS=10.00
DAILY_BONUS=5.00
WELCOME_BONUS=2.00
MIN_WITHDRAW=50.00
WITHDRAW_FEE=1
CURRENCY=USDT
```

Step 5: Run the Bot

```bash
python bot.py
```

🎯 User Commands

Basic Commands

Command Description
/start Start the bot and join channels
💰 Balance Check your balance and earnings
🎁 Daily Bonus Claim daily bonus every 24 hours
👥 Referral Get referral link and earn bonuses
💸 Withdraw Withdraw earnings to wallet
🔐 Set Wallet Configure withdrawal wallet
📊 Statistics View your statistics
🆘 Help Get help and support
ℹ️ About About the bot information

Referral System

· Referral Bonus: $10.00 per user
· Multi-level Referral: Earn from referrals' earnings
· Shareable Link: Easy sharing on Telegram
· Real-time Tracking: Monitor referral statistics

👑 Admin Commands

Admin Panel Features

Feature Description
📈 Bot Stats View comprehensive bot statistics
👥 All Users Browse all registered users with pagination
➕ Add Balance Add balance to any user
➖ Cut Balance Cut balance from any user
💸 Withdraw Request Manage pending withdrawal requests
📢 Broadcast Send messages to all users
🚫 Ban Manager Ban/Unban users and view banned list
⚙️ Bot Settings Configure all bot settings

Settings Management

· Referral Bonus: Adjust referral bonus amount
· Daily Bonus: Set daily bonus value
· Welcome Bonus: Configure welcome bonus
· Min Withdraw: Change minimum withdrawal amount
· Withdraw Fee: Set withdrawal fee percentage
· Channel Settings: Update channel usernames
· Support Chat: Modify support chat link

🏗️ Database Structure

Users Table

```sql
CREATE TABLE users (
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
```

Withdrawals Table

```sql
CREATE TABLE withdrawals (
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
```

💳 Supported Payment Methods

Cryptocurrency

· USDT (TRC20) - Tron network wallet
  · Format: Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (34 characters)
  · Network: TRC20
  · Fast transactions

Mobile Banking (Bangladesh)

Method Format Network
bKash 01XXXXXXXXX (11 digits) Bangladesh
Nagad 01XXXXXXXXX (11 digits) Bangladesh
Rocket 01XXXXXXXXX (11 digits) Bangladesh
Upay 01XXXXXXXXX (11 digits) Bangladesh

🔒 Security Features

Multi-layer Security

· Channel Verification: Must join required channels
· Admin-Only Access: Critical functions admin-only
· Input Validation: All inputs are validated
· Wallet Validation: USDT and phone number validation
· Anti-Spam: Rate limiting and abuse prevention
· Data Encryption: Secure database handling

Withdrawal Security

· Minimum withdrawal amount check
· Balance verification before withdrawal
· Payment channel membership verification
· Admin approval for all withdrawals
· Secure wallet address storage

📊 Statistics & Analytics

User Statistics

· Current balance and total earned
· Daily bonus claim history
· Referral count and earnings
· Withdrawal history and pending requests
· Account creation date and activity

Admin Statistics

· Total users and active users
· Total system balance
· Total withdrawn amount
· Pending withdrawal count
· Banned users statistics
· Daily new user registrations

🛠️ Technical Details

Built With

· Python 3.8+ - Programming language
· python-telegram-bot - Telegram Bot API wrapper
· SQLite3 - Database management
· python-dotenv - Environment variable management







