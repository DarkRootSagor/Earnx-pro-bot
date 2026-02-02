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
git clone https://github.com/DarkRootSagor/Earnx-pro-bot.git
cd EarnX-Pro-Bot
```

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

```

🐛 Troubleshooting

Common Issues & Solutions

Issue 1: Bot not responding

```bash
# Check bot token
echo $BOT_TOKEN

# Check Python version
python3 --version

# Check dependencies
pip3 list | grep telegram
```

Issue 2: Channel membership not detected

```markdown
1. Make sure bot is admin in the channel
2. Check channel username format (without @ in .env)
3. Verify user has actually joined the channel
4. Test with another account
```

Issue 3: Database errors

```bash
# Check database permissions
ls -la database/

# Check disk space
df -h

# Repair database (if needed)
sqlite3 database/earnx_bot.db ".schema"
```

Issue 4: Withdrawal not working

```markdown
1. Check user's wallet is set
2. Verify minimum withdrawal amount
3. Check payment channel membership
4. Ensure sufficient balance
5. Check admin approval system
```

Logs

The bot provides detailed console logs:

· User registration and activities
· Withdrawal requests and processing
· Error messages and debugging info
· Admin actions and modifications

📝 FAQ

Q: How do I get my Telegram User ID?

A: Use @userinfobot on Telegram to get your user ID.

Q: How to add bot as admin to channel?

A:

1. Go to your channel
2. Add the bot as member
3. Go to channel settings > Administrators
4. Add the bot as admin with all permissions

Q: Can I change the currency?

A: Yes, edit CURRENCY in .env file.

Q: Is this bot free to use?

A: Yes, this bot is completely free and open-source under MIT License.

Q: Can I customize the bot?

A: Absolutely! The code is open-source and you can modify it as needed.

Q: How to update the bot?

A:

```bash
git pull origin main
pip install -r requirements.txt
```

🤝 Contributing

We love your input! We want to make contributing to EarnX Pro Bot as easy and transparent as possible.

How to Contribute

1. Fork the repository
2. Create your feature branch (git checkout -b feature/AmazingFeature)
3. Commit your changes (git commit -m 'Add some AmazingFeature')
4. Push to the branch (git push origin feature/AmazingFeature)
5. Open a Pull Request

Development Setup

```bash
# Clone your fork
git clone https://github.com/DarkRootSagor/EarnX-Pro-Bot.git
cd EarnX-Pro-Bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Make changes and test
python bot.py
```

Pull Request Guidelines

· Update README.md with details of changes
· Update .env.example if adding new environment variables
· Add tests if applicable
· Ensure your code follows Python best practices

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

```
MIT License

Copyright (c) 2026 Sagor Sheikh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

👥 Support

Need Help?

· 📖 Documentation: Read this README carefully
· 🐛 Bug Reports: Open an Issue
· 💡 Feature Requests: Suggest a Feature
· 💬 Community: Join our support chat (configured in .env)

Quick Support

```
1. Check the Troubleshooting section
2. Search existing issues
3. Create a new issue with details:
   - Error message
   - Steps to reproduce
   - Screenshots if possible
   - Your .env configuration (without sensitive data)
```

⭐ Show Your Support

If you find this project helpful, please give it a star! ⭐

https://api.star-history.com/svg?repos=DarkRootSagor/EarnX-Pro-Bot&type=Date

🙏 Acknowledgments

Thanks to

· python-telegram-bot team for the amazing library
· All contributors who have helped improve this project
· The Telegram community for support and feedback
· Open source community for inspiration

Special Thanks

· You for using this bot!
· All testers who helped find bugs
· Everyone who submitted feature requests
· The open-source community

📞 Contact

Project Maintainer: Sagor Sheikh
Email: sagors8899@gmail.com
Telegram: @TheSagorOfficial
GitHub: @DarkRootSagor

Project Link: https://github.com/DarkRootSagor/EarnX-Pro-Bot

🔗 Useful Links

· Telegram Bot API Documentation
· Python Telegram Bot Library
· Create Telegram Bot
· Get Telegram User ID
· SQLite Documentation
· Python Documentation

📊 Project Status

https://img.shields.io/github/last-commit/DarkRootSagor/EarnX-Pro-Bot
https://img.shields.io/github/issues/DarkRootSagor/EarnX-Pro-Bot
https://img.shields.io/github/issues-pr/DarkRootSagor/EarnX-Pro-Bot
https://img.shields.io/github/contributors/DarkRootSagor/EarnX-Pro-Bot

Current Version: v1.0.0
Last Updated: October 2024
Active Development: Yes
Maintenance: Regular updates and bug fixes

---

<div align="center">

Made with ❤️ for the Telegram Community

If you like this project, don't forget to give it a star! ⭐

https://img.shields.io/github/stars/DarkRootSagor/EarnX-Pro-Bot?style=for-the-badge
https://img.shields.io/github/forks/DarkRootSagor/EarnX-Pro-Bot?style=for-the-badge
https://img.shields.io/github/issues/DarkRootSagor/EarnX-Pro-Bot?style=for-the-badge

</div>

---

Disclaimer: This bot is for educational purposes. Users are responsible for complying with all applicable laws and Telegram's Terms of Service. The developers are not responsible for any misuse or damages caused by this software.

```






