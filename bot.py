import telebot
import requests
import json
import random
import os
import time
import base64
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime
from threading import Thread
from check_pay import check_url
#from button import generate_markup

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

bot = telebot.TeleBot('7347862137:AAFergERaS22NsSuthowthmdchYE86yuyT0')
MIDTRANS_SERVER_KEY = 'Mid-server-tOgLcriijkzlz9WShqtW7yOS'
bot.session = session

harga_produk = {
    "Nokwa": 100,
    "Noktel": 100,
    "Nokos_Ewallet": 100,
    "Nokos_Apk": 100
}

user_orders = {}
user_states = {}
userid = {}
data_stok=[]

def create_auth_header():
    auth_string = f"{MIDTRANS_SERVER_KEY}:"
    base64_auth_string = base64.b64encode(auth_string.encode()).decode()
    return f"Basic {base64_auth_string}"

def load_stok():
    with open('stok.json', 'r') as file:
        return json.load(file)

def save_stok(stok):
    with open('stok.json', 'w') as file:
        json.dump(stok, file, indent=4)

def create_midtrans_payment_link(user_id, products, quantity, total_price):
    order_id = f"{random.randint(0, 99999)}-{products}-{quantity}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": create_auth_header()
    }
    payload = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": total_price
        },
        "item_details": [
            {
                "id": products,
                "price": total_price // quantity,
                "quantity": quantity,
                "name": products
            }
        ],
        "customer_details": {
            "first_name": f"User {user_id}",
            "email": f"user{user_id}@example.com"
        },
        "usage_limit":  1,
        "expiry": {
            "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S %z'),
            "duration": 20,
            "unit": "minutes"
        }
    }
    response = requests.post("https://api.midtrans.com/v1/payment-links", headers=headers, json=payload)
    return response.json().get("payment_url"), order_id

def main_menu(chat_id, username):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton('Nokwa', callback_data='product-Nokwa'),
        InlineKeyboardButton('Noktel', callback_data='product-Noktel'),
        InlineKeyboardButton('Nokos Ewallet', callback_data='product-Nokos_Ewallet'),
        InlineKeyboardButton('Nokos Apk', callback_data='product-Nokos_Apk'),
        InlineKeyboardButton('Cek Stok', callback_data='cek_stok')
    )
    teks = f"Hai *@{username}*, Kamu mau beli nokos apa?"
    return markup, teks

def generate_markup(count):
    markup = InlineKeyboardMarkup(row_width=4)
    markup.add(
        InlineKeyboardButton("-", callback_data=f"decrease-{count}"),
        InlineKeyboardButton(str(count), callback_data="noop"),
        InlineKeyboardButton("+", callback_data=f"increase-{count}"),
        InlineKeyboardButton("Next", callback_data=f"next-{count}"),
        InlineKeyboardButton("Back", callback_data=f"back")
    )
    return markup

def jumlah_order(count):
    markup = generate_markup(count)
    teks = "Mau pesan berapa?"
    return markup, teks

@bot.message_handler(commands=['start', 'order'])
def welcome_message(message):
    chat_id = message.chat.id
    username = message.from_user.username
    #username = user.first_name
    
    markup, teks = main_menu(chat_id, username)
    bot.send_chat_action(chat_id, 'typing')
    time.sleep(1)
    bot.reply_to(message, teks, reply_markup=markup, parse_mode='MarkdownV2')
    
    
    userid['id']=chat_id
    
    userid['uname']=username
    
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data.split('-')
    action = data[0]
    username = userid['uname']
    #cid = userid['id']
    
    if action == 'product':
        product = data[1]
        stok = load_stok()
        if stok[product] > 0:
            user_orders[chat_id] = {"products": product, "price": harga_produk[product]}
            markup, teks = jumlah_order(1)
            bot.edit_message_text(teks, chat_id, message_id, reply_markup=markup)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('Back to menu', callback_data='back'))
            bot.edit_message_text(f'Maaf, stok {product} habis. Silakan pilih produk lain.', chat_id, message_id, reply_markup=markup)
    
    elif action == "increase":
        count = int(data[1])
        count += 1
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=generate_markup(count))
    
    elif action == "decrease":
        count = int(data[1])
        if count > 1:
            count -= 1
            bot.edit_message_reply_markup(chat_id, message_id, reply_markup=generate_markup(count))
    
    
    elif action == "next":
        count = int(data[1])
        product = user_orders[chat_id]["products"]
        total_price = count * harga_produk[product]
        payment_link, order_id = create_midtrans_payment_link(chat_id, product, count, total_price)
        
        markup = InlineKeyboardMarkup(row_width=4)
        markup.add(
          InlineKeyboardButton("Bayar", url=payment_link),
          InlineKeyboardButton("Cancel", callback_data="cancel"),
        )
        
        bot.edit_message_text(f"Kamu memesan {count} {product.replace('_',' ')} dengan total harga {total_price}.", chat_id, message_id, reply_markup=markup)
        
        teks = f"Detail Pesanan!\n\nStatus: UNPAID\nUsername : @{username}\nProduk: {product.replace('_',' ')}\nJumlah: {count}\nTotal: {total_price}\nPayment url: {payment_link}"
        bot.send_message('-4227551363', teks)
        user_states[chat_id] = "WAIT_PAYMENT"
        
        Thread(target=check_payment_status, args=(chat_id, payment_link, username, product.replace(' ','_'), count, total_price, message_id)).start()
    
    elif call.data in ['cancel','back']:
      markup, teks = main_menu(chat_id, username)
      bot.edit_message_text(teks, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
    
    elif 'cek_stok' in call.data:
      stok = load_stok()
      #print(stok)
      markup = InlineKeyboardMarkup()
      markup.add(InlineKeyboardButton('Back to menu', callback_data='back'))
      for key, value in stok.items():
        if isinstance(value, dict):
          return(f"{key}:")
          for sub_key, sub_value in value.items():
            return(f"  {sub_key}: {sub_value}")
        else:
          data_stok.append(f"{key.replace('_',' ')}: {value}")
      
      #print(data_stok)
      s = '\n'.join(data_stok)
      bot.edit_message_text(s, chat_id, message_id, reply_markup=markup)
      data_stok.clear()
      
def check_payment_status(chat_id, payment_link, username, product, count, total_price, message_id):
  stok = load_stok()
  markup = InlineKeyboardMarkup(row_width=4)
  markup.add(
    InlineKeyboardButton("Get Number", url='t.me/fafadstore'),
    InlineKeyboardButton("Back to menu", callback_data="back"),
  )
  if check_url(payment_link):
    teks = f"Detail Pesanan!\n\nStatus: PAID\nUsername : @{username}\nProduk: {product}\nJumlah: {count}\nTotal: {total_price}\nPayment url: {payment_link}"
    bot.edit_message_text(f'Hai *@{username}*, Pembayaran Telah Selesai!', chat_id, message_id, parse_mode='Markdown', reply_markup=markup)
    bot.send_message('-4227551363', teks)
    user_states[chat_id] = "SELECT_OPTION"
    user_orders.pop(chat_id, None)
    
    stok[product] -= count
    save_stok(stok)
    
if __name__ == "__main__":
    os.system('clear')
    print('Starting bot...')
    bot.infinity_polling()