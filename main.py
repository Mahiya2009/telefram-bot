import time
import requests
import threading
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7750210181:AAG0mJEmQ5M_b9IILqylyLZK-tw0Vvta_wg"
CHAT_ID = "-1002256384134"

# Initialize Telegram Bot
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Database setup
conn = sqlite3.connect("trades.db", check_same_thread=False)
cursor = conn.cursor()

# Check if the columns exist and add them if necessary
cursor.execute("PRAGMA table_info(trades);")
columns = [column[1] for column in cursor.fetchall()]

# Add missing columns for tp1_hit, tp2_hit, tp3_hit, ..., tp10_hit if they don't exist
for i in range(1, 11):
    if f"tp{i}_hit" not in columns:
        cursor.execute(f"ALTER TABLE trades ADD COLUMN tp{i}_hit INTEGER DEFAULT 0;")
conn.commit()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pair TEXT, 
        trade_type TEXT, 
        order_type TEXT, 
        entry_price REAL, 
        stop_loss REAL, 
        take_profits TEXT, 
        live_price REAL, 
        status TEXT DEFAULT 'Active',
        tp1_hit INTEGER DEFAULT 0, 
        tp2_hit INTEGER DEFAULT 0, 
        tp3_hit INTEGER DEFAULT 0,
        tp4_hit INTEGER DEFAULT 0, 
        tp5_hit INTEGER DEFAULT 0, 
        tp6_hit INTEGER DEFAULT 0,
        tp7_hit INTEGER DEFAULT 0, 
        tp8_hit INTEGER DEFAULT 0, 
        tp9_hit INTEGER DEFAULT 0, 
        tp10_hit INTEGER DEFAULT 0
    )
""")
conn.commit()

# Active trade storage
active_trade = {}

# Fetch live price from Binance
def get_live_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data["price"])
    except:
        return None  # API error

# Send message to Telegram
def send_to_telegram(message):
    telegram_bot.send_message(chat_id=CHAT_ID, text=message)

# Start command
def start(update, context):
    update.message.reply_text("Welcome! Use /create_trade to set up a trade signal.")

# Trade setup initiation
def create_trade(update, context):
    update.message.reply_text("📋 Enter trading pair (e.g., BTCUSDT):")
    return "WAITING_FOR_PAIR"

# Validate trading pair
def handle_pair(update, context):
    pair = update.message.text.upper()
    live_price = get_live_price(pair)

    if live_price is None:
        update.message.reply_text("⚠️ Invalid pair or API error. Try again.")
        return "WAITING_FOR_PAIR"

    active_trade['pair'] = pair
    active_trade['live_price'] = live_price

    update.message.reply_text(f"✅ Pair: {pair}\n📊 Live Price: {live_price}\nEnter Trade Type (Long/Short):")
    return "WAITING_FOR_TYPE"

# Validate trade type
def handle_type(update, context):
    trade_type = update.message.text.upper()
    if trade_type not in ["LONG", "SHORT"]:
        update.message.reply_text("⚠️ Invalid input. Enter Long or Short.")
        return "WAITING_FOR_TYPE"

    active_trade['trade_type'] = trade_type
    update.message.reply_text("✅ Enter Order Type (Limit/Market):")
    return "WAITING_FOR_ORDER_TYPE"

# Validate order type
def handle_order_type(update, context):
    order_type = update.message.text.lower()
    if order_type not in ["limit", "market"]:
        update.message.reply_text("⚠️ Enter 'Limit' or 'Market'.")
        return "WAITING_FOR_ORDER_TYPE"

    active_trade['order_type'] = order_type
    update.message.reply_text("✅ Enter Entry Price:")
    return "WAITING_FOR_ENTRY"

# Validate entry price
def handle_entry(update, context):
    try:
        entry_price = float(update.message.text)
        active_trade['entry_price'] = entry_price
        update.message.reply_text("✅ Enter Stop Loss Price:")
        return "WAITING_FOR_SL"
    except ValueError:
        update.message.reply_text("⚠️ Enter a valid price.")
        return "WAITING_FOR_ENTRY"

# Validate stop loss
def handle_stop_loss(update, context):
    try:
        stop_loss = float(update.message.text)
        active_trade['stop_loss'] = stop_loss
        update.message.reply_text("✅ Enter Take Profit Prices (separate multiple TPs with commas, e.g., 50000,51000,52000):")
        return "WAITING_FOR_TP"
    except ValueError:
        update.message.reply_text("⚠️ Enter a valid price.")
        return "WAITING_FOR_SL"

# Validate take profit (multiple TPs)
def handle_tp(update, context):
    try:
        tp_text = update.message.text
        tp_list = [float(tp.strip()) for tp in tp_text.split(",") if tp.strip()]

        if len(tp_list) < 1 or len(tp_list) > 10:
            update.message.reply_text("⚠️ You must enter between 1 and 10 take profit prices.")
            return "WAITING_FOR_TP"

        active_trade['take_profits'] = tp_list

        # Generate TP display
        tp_display = "\n".join([f"📈 TP{i+1}: {tp}" for i, tp in enumerate(tp_list)])

        trade_summary = (
            f"📢 *Trade Confirmation*\n"
            f"📌 Pair: {active_trade['pair']}\n"
            f"📊 Live Price: {active_trade['live_price']}\n"
            f"🔄 Type: {active_trade['trade_type']}\n"
            f"💰 Entry: {active_trade['entry_price']}\n"
            f"📉 SL: {active_trade['stop_loss']}\n"
            f"{tp_display}\n"
            f"📝 Order Type: {active_trade['order_type'].capitalize()}\n\n"
            f"✅ Confirm Trade? (Yes/No)"
        )
        update.message.reply_text(trade_summary)
        return "WAITING_FOR_CONFIRMATION"

    except ValueError:
        update.message.reply_text("⚠️ Enter valid prices separated by commas.")
        return "WAITING_FOR_TP"

# Confirm trade
def handle_confirmation(update, context):
    user_input = update.message.text.lower()
    if user_input == "yes":
        send_trade_signal(update)
        return ConversationHandler.END
    elif user_input == "no":
        update.message.reply_text("❌ Trade canceled.")
        return ConversationHandler.END
    else:
        update.message.reply_text("⚠️ Enter Yes or No.")
        return "WAITING_FOR_CONFIRMATION"

# Send trade signal
def send_trade_signal(update):
    tp_display = "\n".join([f"📈 TP{i+1}: {tp}" for i, tp in enumerate(active_trade['take_profits'])])

    trade_details = (
        f"📢 *New Trade Signal*\n"
        f"📌 Pair: {active_trade['pair']}\n"
        f"📊 Live Price: {active_trade['live_price']}\n"
        f"🔄 Type: {active_trade['trade_type']}\n"
        f"💰 Entry: {active_trade['entry_price']}\n"
        f"📉 SL: {active_trade['stop_loss']}\n"
        f"{tp_display}\n"
        f"📝 Order Type: {active_trade['order_type'].capitalize()}"
    )

    send_to_telegram(trade_details)
    update.message.reply_text("✅ Trade signal sent!")

    # Monitor trades for TP hits or SL
    def monitor_trades():
        while True:
            cursor.execute("SELECT id, pair, trade_type, stop_loss, take_profits, tp1_hit, tp2_hit, tp3_hit, tp4_hit, tp5_hit, tp6_hit, tp7_hit, tp8_hit, tp9_hit, tp10_hit FROM trades WHERE status = 'Active'")
            trades = cursor.fetchall()

            for trade in trades:
                trade_id, pair, trade_type, stop_loss, take_profits, *tp_hits = trade
                live_price = get_live_price(pair)

                if live_price is None:
                    continue  # Skip if API fails

                # Check for Stop Loss (SL) hit
                if (trade_type == "LONG" and live_price <= stop_loss) or (trade_type == "SHORT" and live_price >= stop_loss):
                    send_to_telegram(f"❌ {pair} trade has hit stop loss at {live_price}.")
                    cursor.execute("UPDATE trades SET status = 'Closed' WHERE id = ?", (trade_id,))
                    conn.commit()
                    continue

                # Check for TP hits
                take_profits = eval(take_profits)  # Convert string back to list
                all_tps_hit = True
                tp_hit_index = -1  # Track the last TP hit

                for idx, tp in enumerate(take_profits):
                    if (trade_type == "LONG" and live_price >= tp and not tp_hits[idx]) or \
                       (trade_type == "SHORT" and live_price <= tp and not tp_hits[idx]):
                        # Update TP hit status
                        cursor.execute(f"UPDATE trades SET tp{idx+1}_hit = 1 WHERE id = ?", (trade_id,))
                        conn.commit()
                        send_to_telegram(f"🎯 {pair} TP{idx+1} hit at {live_price}!")
                        tp_hit_index = idx  # Update to the last TP hit
                        break  # Exit the loop after hitting one TP

                # If all TPs are hit
                if all(t > 0 for t in tp_hits):
                    send_to_telegram(f"🎉 {pair} All TPs hit! Congratulations!")
                    cursor.execute("UPDATE trades SET status = 'Closed' WHERE id = ?", (trade_id,))
                    conn.commit()

            time.sleep(60)  # Check every minute

    import sqlite3
    import time

    # Function to get the live price of the trade pair (dummy function, replace with real API call)
    def get_live_price(pair):
        # Replace this with actual API call to get live price
        return 100.0  # Dummy value

    # Database setup
    conn = sqlite3.connect("trades.db", check_same_thread=False)
    cursor = conn.cursor()

    # Check if the columns exist and add them if necessary
    cursor.execute("PRAGMA table_info(trades);")
    columns = [column[1] for column in cursor.fetchall()]

    # Add missing columns for tp1_hit, tp2_hit, tp3_hit, ..., tp10_hit if they don't exist
    for i in range(1, 11):
        if f"tp{i}_hit" not in columns:
            cursor.execute(f"ALTER TABLE trades ADD COLUMN tp{i}_hit INTEGER DEFAULT 0;")
    conn.commit()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT, 
            trade_type TEXT, 
            order_type TEXT, 
            entry_price REAL, 
            stop_loss REAL, 
            take_profits TEXT, 
            live_price REAL, 
            status TEXT DEFAULT 'Active',
            tp1_hit INTEGER DEFAULT 0, 
            tp2_hit INTEGER DEFAULT 0, 
            tp3_hit INTEGER DEFAULT 0,
            tp4_hit INTEGER DEFAULT 0, 
            tp5_hit INTEGER DEFAULT 0, 
            tp6_hit INTEGER DEFAULT 0,
            tp7_hit INTEGER DEFAULT 0, 
            tp8_hit INTEGER DEFAULT 0, 
            tp9_hit INTEGER DEFAULT 0, 
            tp10_hit INTEGER DEFAULT 0
        )
    """)
    conn.commit()

    # Save trade to database automatically when trade is created
    def save_trade_to_db(pair, trade_type, order_type, entry_price, stop_loss, take_profits, live_price):
        cursor.execute("""
            INSERT INTO trades (pair, trade_type, order_type, entry_price, stop_loss, take_profits, live_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pair, trade_type, order_type, entry_price, stop_loss, str(take_profits), live_price, "Active"))
        conn.commit()

    # Monitor trades for TP hits or SL
    def monitor_trades():
        while True:
            cursor.execute("SELECT id, pair, trade_type, stop_loss, take_profits, tp1_hit, tp2_hit, tp3_hit, tp4_hit, tp5_hit, tp6_hit, tp7_hit, tp8_hit, tp9_hit, tp10_hit FROM trades WHERE status = 'Active'")
            trades = cursor.fetchall()

            for trade in trades:
                trade_id, pair, trade_type, stop_loss, take_profits, *tp_hits = trade
                take_profits = eval(take_profits)  # Convert the string back into a list of TP values

                live_price = get_live_price(pair)
                if live_price is None:
                    continue  # Skip if price data is unavailable

                # Check for stop loss hit
                if (trade_type == "LONG" and live_price <= stop_loss) or (trade_type == "SHORT" and live_price >= stop_loss):
                    cursor.execute(f"UPDATE trades SET status = 'Stop Loss Hit' WHERE id = ?", (trade_id,))
                    conn.commit()

                # Check for TP hits
                for i, tp in enumerate(take_profits):
                    if tp_hits[i] == 0 and ((trade_type == "LONG" and live_price >= tp) or (trade_type == "SHORT" and live_price <= tp)):
                        cursor.execute(f"UPDATE trades SET tp{i+1}_hit = 1 WHERE id = ?", (trade_id,))
                        conn.commit()

            time.sleep(10)  # Check every 10 seconds

    # Example trade to save (Replace this with your real trade creation logic)
    save_trade_to_db("BTC/USDT", "LONG", "LIMIT", 9500.0, 9000.0, [9800.0, 10000.0, 10200.0], 9500.0)

    # Start monitoring the trades
    monitor_trades()


    # Save trade to database
    cursor.execute("""
        INSERT INTO trades (pair, trade_type, order_type, entry_price, stop_loss, take_profits, live_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (active_trade['pair'], active_trade['trade_type'], active_trade['order_type'],
          active_trade['entry_price'], active_trade['stop_loss'], str(active_trade['take_profits']), 
          active_trade['live_price'], "Active"))
    conn.commit()

# Monitor trades for TP hits or SL
def monitor_trades():
    while True:
        cursor.execute("SELECT id, pair, trade_type, stop_loss, take_profits, tp1_hit, tp2_hit, tp3_hit, tp4_hit, tp5_hit, tp6_hit, tp7_hit, tp8_hit, tp9_hit, tp10_hit FROM trades WHERE status = 'Active'")
        trades = cursor.fetchall()

        for trade in trades:
            trade_id, pair, trade_type, stop_loss, take_profits, *tp_hits = trade
            live_price = get_live_price(pair)

            if live_price is None:
                continue  # Skip if API fails

            # Check for Stop Loss (SL) hit
            if (trade_type == "LONG" and live_price <= stop_loss) or (trade_type == "SHORT" and live_price >= stop_loss):
                send_to_telegram(f"❌ {pair} trade has hit stop loss at {live_price}.")
                cursor.execute("UPDATE trades SET status = 'Closed' WHERE id = ?", (trade_id,))
                conn.commit()
                continue

            # Check for TP hits
            take_profits = eval(take_profits)  # Convert string back to list
            all_tps_hit = True

            for idx, tp in enumerate(take_profits):
                if (trade_type == "LONG" and live_price >= tp and not tp_hits[idx]) or \
                   (trade_type == "SHORT" and live_price <= tp and not tp_hits[idx]):
                    # Update TP hit status
                    cursor.execute(f"UPDATE trades SET tp{idx+1}_hit = 1 WHERE id = ?", (trade_id,))
                    conn.commit()
                    send_to_telegram(f"🎯 {pair} TP{idx+1} hit at {live_price}!")
                    break
                if not tp_hits[idx]:  # If any TP hasn't been hit
                    all_tps_hit = False

            # If all TPs are hit
            if all_tps_hit:
                send_to_telegram(f"🎉 {pair} All TPs hit! Congratulations!")
                cursor.execute("UPDATE trades SET status = 'Closed' WHERE id = ?", (trade_id,))
                conn.commit()

        time.sleep(60)  # Check every minute

# Monitor trades for TP hits or SL
def monitor_trades():
    while True:
        cursor.execute("SELECT id, pair, trade_type, stop_loss, take_profits, tp1_hit, tp2_hit, tp3_hit, tp4_hit, tp5_hit, tp6_hit, tp7_hit, tp8_hit, tp9_hit, tp10_hit FROM trades WHERE status = 'Active'")
        trades = cursor.fetchall()

        for trade in trades:
            trade_id, pair, trade_type, stop_loss, take_profits, *tp_hits = trade
            live_price = get_live_price(pair)

            if live_price is None:
                continue  # Skip if API fails

            # Check for Stop Loss (SL) hit
            if (trade_type == "LONG" and live_price <= stop_loss) or (trade_type == "SHORT" and live_price >= stop_loss):
                send_to_telegram(f"❌ {pair} trade has hit stop loss at {live_price}.")
                cursor.execute("UPDATE trades SET status = 'Closed' WHERE id = ?", (trade_id,))
                conn.commit()
                continue

            # Check for TP hits
            take_profits = eval(take_profits)  # Convert string back to list
            all_tps_hit = True

            for idx, tp in enumerate(take_profits):
                if (trade_type == "LONG" and live_price >= tp and not tp_hits[idx]) or \
                   (trade_type == "SHORT" and live_price <= tp and not tp_hits[idx]):
                    # Update TP hit status
                    cursor.execute(f"UPDATE trades SET tp{idx+1}_hit = 1 WHERE id = ?", (trade_id,))
                    conn.commit()
                    send_to_telegram(f"🎯 {pair} TP{idx+1} hit at {live_price}!")
                    tp_hits[idx] = 1  # Update the local list to reflect the hit TP

            # Check if all TP levels are hit
            if all(tp_hits[:len(take_profits)]):  # Only check TP slots that were used
                send_to_telegram(f"🎉 {pair} All TP levels hit! Trade successfully completed!")
                cursor.execute("UPDATE trades SET status = 'Closed' WHERE id = ?", (trade_id,))
                conn.commit()

        time.sleep(60)  # Check every minute


# Start monitoring trades
monitor_thread = threading.Thread(target=monitor_trades, daemon=True)
monitor_thread.start()

# Telegram bot command handlers
updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
dp = updater.dispatcher

# Conversation handler for creating trade
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('create_trade', create_trade)],
    states={
        "WAITING_FOR_PAIR": [MessageHandler(Filters.text & ~Filters.command, handle_pair)],
        "WAITING_FOR_TYPE": [MessageHandler(Filters.text & ~Filters.command, handle_type)],
        "WAITING_FOR_ORDER_TYPE": [MessageHandler(Filters.text & ~Filters.command, handle_order_type)],
        "WAITING_FOR_ENTRY": [MessageHandler(Filters.text & ~Filters.command, handle_entry)],
        "WAITING_FOR_SL": [MessageHandler(Filters.text & ~Filters.command, handle_stop_loss)],
        "WAITING_FOR_TP": [MessageHandler(Filters.text & ~Filters.command, handle_tp)],
        "WAITING_FOR_CONFIRMATION": [MessageHandler(Filters.text & ~Filters.command, handle_confirmation)],
    },
    fallbacks=[]
)

dp.add_handler(conv_handler)

# Start the bot
updater.start_polling()
updater.idle()
