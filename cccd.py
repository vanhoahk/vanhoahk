import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import telebot
import re
import time
from threading import Timer
import datetime
import random
from datetime import datetime, timedelta
import schedule

API_TOKEN = '7258792120:AAEkZyMDXmPK8IxHrDyPA84a9bvEWowKlZA'
bot = telebot.TeleBot(API_TOKEN)

spam_count = {}
group_id = [-1002239701736, -1002248999618, -1002236223520]
usage_limits = {}
admins = set(['vanhoa08', 'admin_username2'])  # Thêm tên admin của bạn vào đây

def load_and_process_image(url):
    response = requests.get(url)
    response.raise_for_status()
    if 'image' not in response.headers['Content-Type']:
        print(f"Error: URL {url} does not contain an image.")
        return None
    image = Image.open(BytesIO(response.content)).convert("RGBA")
    r, g, b, a = image.split()
    mask = Image.eval(a, lambda x: 255 if x > 128 else 0)
    image = Image.composite(image, Image.new("RGBA", image.size), mask)
    return image

def create_outfit_collage(clothes_urls, external_items_urls):
    equipped_skins_image = Image.open('/storage/emulated/0/Download/background.jpg').convert("RGBA")
    images = [load_and_process_image(url) for url in clothes_urls]
    images = [img.resize((300, 300), Image.Resampling.LANCZOS) for img in images if img is not None]
    positions = [(19, 140), (319, 140), (628, 140), (18, 550), (319, 550), (628, 550), (19, 628), (319, 628), (628, 628)]
    for img, pos in zip(images, positions):
        equipped_skins_image.paste(img, pos, img)
    external_images = [load_and_process_image(url) for url in external_items_urls]
    external_images = [img.resize((300, 300), Image.Resampling.LANCZOS) for img in external_images if img is not None]
    external_positions = [(19, 900), (319, 900), (628, 900)]
    for img, pos in zip(external_images, external_positions):
        equipped_skins_image.paste(img, pos, img)
    return equipped_skins_image

def create_avatar_banner_collage(data, font_size):
    avatar_url = data.get('Account Avatar Image', '')
    banner_url = data.get('Account Banner Image', '')
    name = data.get('Account Name', 'N/A')
    level = data.get('Account Level', 'N/A')

    avatar = load_and_process_image(avatar_url)
    if avatar:
        avatar = avatar.resize((120, 120), Image.Resampling.LANCZOS)
    banner = load_and_process_image(banner_url)
    if banner:
        banner = banner.resize((300, 120), Image.Resampling.LANCZOS)
    
    collage = Image.new('RGBA', (450, 120), (255, 255, 255, 0))
    if avatar:
        collage.paste(avatar, (0, 0), avatar)
    if banner:
        collage.paste(banner, (120, 0), banner)

    draw = ImageDraw.Draw(collage)
    try:
        font = ImageFont.truetype("/storage/emulated/0/Download/arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    draw.text((135, 10), name, fill="White", font=font)
    draw.text((355, 90), f"Lv {level}", fill="White", font=font)

    return collage

def mute_user(chat_id, user_id, duration):
    try:
        bot.restrict_chat_member(chat_id, user_id, until_date=time.time() + duration, can_send_messages=False)
        print(f"User {user_id} has been muted for {duration / 3600} hours.")
    except Exception as e:
        print(f"Failed to mute user {user_id}: {e}")

def unmute_user(chat_id, user_id):
    try:
        bot.restrict_chat_member(chat_id, user_id, can_send_messages=True)
        print(f"User {user_id} has been unmuted.")
    except Exception as e:
        print(f"Failed to unmute user {user_id}: {e}")

def kick_user(chat_id, user_id):
    try:
        bot.kick_chat_member(chat_id, user_id)
        print(f"User {user_id} has been kicked from the chat.")
    except Exception as e:
        print(f"Failed to kick user {user_id}: {e}")

def revoke_admin(chat_id, user_id):
    try:
        bot.promote_chat_member(chat_id, user_id, can_change_info=False, can_delete_messages=False,
                                can_invite_users=False, can_restrict_members=False, can_pin_messages=False,
                                can_promote_members=False)
        print(f"User {user_id} has been revoked admin rights.")
    except Exception as e:
        print(f"Failed to revoke admin rights from user {user_id}: {e}")

def handle_spam(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id in spam_count:
        spam_count[user_id] += 1
    else:
        spam_count[user_id] = 1

    if spam_count[user_id] == 3:
        bot.send_message(chat_id, "Bạn đã bị cấm chat trong 10 giây vì spam.")
        mute_user(chat_id, user_id, 10)  # Mute for 10 seconds
    elif spam_count[user_id] == 4:
        bot.send_message(chat_id, f"Sau 10 giây, bạn sẽ mất vị trí admin vì spam quá nhiều.")
        Timer(10, revoke_admin, args=(chat_id, user_id)).start()
    elif spam_count[user_id] == 5:
        if message.from_user.username in admins:  # Replace with actual admin usernames
            bot.send_message(chat_id, f"Đây là nhắc nhở spam quá lần. Bạn cần cân nhắc vị trí admin này.")
        else:
            bot.send_message(chat_id, f"Sau 10 giây, {message.from_user.username} sẽ bị đá khỏi nhóm vì spam quá nhiều.")
            Timer(10, kick_user, args=(chat_id, user_id)).start()

def delete_message_after_delay(chat_id, message_id, delay):
    Timer(delay, lambda: bot.delete_message(chat_id, message_id)).start()

@bot.message_handler(commands=['scan'])
def send_account_info(message):
    user_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    username = message.from_user.username
    
    if not user_id or not re.match(r'^\d+$', user_id):
        msg = bot.send_message(message.chat.id, "Vui lòng cung cấp một ID hợp lệ.")
        delete_message_after_delay(message.chat.id, msg.message_id, 15)
        handle_spam(message)
        return
    
    if username not in admins and (username not in usage_limits or usage_limits[username] <= 0):
        msg = bot.send_message(message.chat.id, "Bạn đã hết lượt sử dụng. Vui lòng liên hệ admin để được cấp thêm.")
        delete_message_after_delay(message.chat.id, msg.message_id, 15)
        return
    
    if username not in admins:
        usage_limits[username] -= 1

    waiting_message = bot.send_message(message.chat.id, "⌨️")

    api_url = f'https://www.public.freefireinfo.site/api/info/sg/{user_id}?key=profile_account'
    
    response = requests.get(api_url)
    if response.status_code == 404:
        bot.edit_message_text("ID không tồn tại.", chat_id=waiting_message.chat.id, message_id=waiting_message.message_id)
        delete_message_after_delay(waiting_message.chat.id, waiting_message.message_id, 15)
        return

    data = response.json()

    if not data:
        bot.edit_message_text("Vui lòng cung cấp một ID hợp lệ.", chat_id=waiting_message.chat.id, message_id=waiting_message.message_id)
        delete_message_after_delay(waiting_message.chat.id, waiting_message.message_id, 15)
        return

    external_items = data.get('Equipped Items', {}).get('profile', {}).get('External Items', [])
    external_item_ids = ['N/A'] * 3
    for i in range(min(3, len(external_items))):
        external_item_ids[i] = external_items[i].get('Item ID', 'N/A')

    account_info = f"""
THÔNG TIN TÀI KHOẢN:
┌ 👤 THÔNG TIN CƠ BẢN
├─ Tên: {data.get('Account Name', 'N/A')}
├─ UID: {data.get('Account UID', 'N/A')}
├─ Cấp độ: {data.get('Account Level', 'N/A')}
├─ Khu vực: {data.get('Account Region', 'N/A')}
├─ Lượt thích: {data.get('Account Likes', 'N/A')}
├─ Điểm danh dự: {data.get('Account Honor Score', 'N/A')}
├─ Huy hiệu tiến hoá: {data.get('Account Badge', 'N/A')}
└─Chữ ký: {data.get('Account Signature', 'N/A')}

┌ 🛡️ THÔNG TIN XẾP HẠNG
├─ BR: {data.get('BR Rank Points', 'N/A')}
├─ Điểm CS: {data.get('CS Rank Points', 'N/A')}
├─ Ngày tạo: {data.get('Account Creation Time (GMT 0530)', 'N/A')}
└─ Đăng nhập lần cuối: {data.get('Account Last Login (GMT 0530)', 'N/A')}

┌ 🐾 CHI TIẾT THÚ CƯNG
├─ Đã trang bị?: {data.get('Equipped Pet Information', {}).get('Selected?', 'N/A')}
├─ Tên thú cưng: {data.get('Equipped Pet Information', {}).get('Pet Name', 'N/A')}
├─ Loại thú cưng: {data.get('Equipped Pet Information', {}).get('Pet Type', 'N/A')}
├─ XP thú cưng: {data.get('Equipped Pet Information', {}).get('Pet XP', 'N/A')}
└─ Cấp độ thú cưng: {data.get('Equipped Pet Information', {}).get('Pet Level', 'N/A')}

┌ 🛡️ THÔNG TIN HỘI
├─ Tên hội: {data.get('Guild Information', {}).get('Guild Name', 'N/A')}
├─ ID hội: {data.get('Guild Information', {}).get('Guild ID', 'N/A')}
├─ Cấp độ hội: {data.get('Guild Information', {}).get('Guild Level', 'N/A')}
├─ Thành viên: {data.get('Guild Information', {}).get('Guild Current Members', 'N/A')}
└─ Thông tin lãnh đạo hội:
    ├─ Tên: {data.get('Guild Leader Information', {}).get('Leader Name', 'N/A')}
    ├─ UID: {data.get('Guild Leader Information', {}).get('Leader UID', 'N/A')}
    ├─ Cấp độ: {data.get('Guild Leader Information', {}).get('Leader Level', 'N/A')}
    ├─ Huy hiệu: {data.get('Guild Leader Information', {}).get('Leader Title', 'N/A')}
    └─ Chữ ký: {data.get('Guild Leader Information', {}).get('Leader Ac Title', 'N/A')}
    """

    bot.delete_message(chat_id=waiting_message.chat.id, message_id=waiting_message.message_id)
    sent_message = bot.send_message(message.chat.id, account_info)
    delete_message_after_delay(message.chat.id, sent_message.message_id, 15)

    equipped_items = data.get('Equipped Items', {}).get('profile', {}).get('Clothes', [])
    if not equipped_items:
        sent_message = bot.send_message(message.chat.id, "No clothes equipped.")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
        return

    external_item_urls = [item.get('Image URL') for item in external_items]
    outfit_collage = create_outfit_collage(equipped_items, external_item_urls)

    if outfit_collage:
        final_image = BytesIO()
        outfit_collage.save(final_image, format='PNG')
        final_image.seek(0)
        sent_photo = bot.send_photo(message.chat.id, final_image, caption="Trang phục của ID trên")
        delete_message_after_delay(message.chat.id, sent_photo.message_id, 15)
    else:
        sent_message = bot.send_message(message.chat.id, "Unable to create outfit collage. Please try again later.")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)

    avatar_banner_collage = create_avatar_banner_collage(data, font_size=30)
    if avatar_banner_collage:
        sticker_image = BytesIO()
        avatar_banner_collage.save(sticker_image, format='PNG')
        sticker_image.seek(0)
        sent_sticker = bot.send_sticker(message.chat.id, sticker_image, reply_to_message_id=message.message_id)
        delete_message_after_delay(message.chat.id, sent_sticker.message_id, 15)
    else:
        sent_message = bot.send_message(message.chat.id, "Unable to create avatar and banner collage. Please try again later.")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)

@bot.message_handler(commands=['addqtv'])
def add_admin(message):
    if message.chat.type != "supergroup":
        sent_message = bot.reply_to(message, "Lệnh này chỉ sử dụng trong nhóm siêu cấp.")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
        return
    
    if not bot.get_chat_member(message.chat.id, message.from_user.id).status in ['administrator', 'creator']:
        sent_message = bot.reply_to(message, "Bạn không có quyền thực hiện lệnh này.")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
        return

    if len(message.text.split()) != 2:
        sent_message = bot.reply_to(message, "Vui lòng chỉ định người dùng: /addqtv @username")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
        return
    
    username = message.text.split()[1]
    try:
        user = bot.get_chat_member(message.chat.id, username)
        if user.status not in ['member']:
            sent_message = bot.reply_to(message, "Người dùng này không thể được cấp quyền admin.")
            delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
            return

        bot.promote_chat_member(message.chat.id, user.user.id,
                                can_change_info=True,
                                can_delete_messages=True,
                                can_invite_users=True,
                                can_restrict_members=True,
                                can_pin_messages=True,
                                can_promote_members=True)
        sent_message = bot.send_message(message.chat.id, f"Đã cấp quyền admin cho {username}.")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
    except Exception as e:
        sent_message = bot.reply_to(message, f"Không thể tìm thấy hoặc cấp quyền admin cho người dùng: {e}")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)

@bot.message_handler(commands=['allowid'])
def allow_id(message):
    if message.chat.type != "supergroup":
        sent_message = bot.reply_to(message, "Lệnh này chỉ sử dụng trong nhóm siêu cấp.")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
        return
    
    if not bot.get_chat_member(message.chat.id, message.from_user.id).status in ['administrator', 'creator']:
        sent_message = bot.reply_to(message, "Bạn không có quyền thực hiện lệnh này.")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
        return

    parts = message.text.split()
    if len(parts) != 3 or not re.match(r'^\d+$', parts[2]):
        sent_message = bot.reply_to(message, "Cú pháp không hợp lệ. Sử dụng: /allowid @username số_lần_sử_dụng")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
        return

    username = parts[1].lstrip('@')
    usage_count = int(parts[2])

    if username not in usage_limits:
        usage_limits[username] = usage_count
    else:
        usage_limits[username] += usage_count

    sent_message = bot.send_message(message.chat.id, f"Đã cấp {usage_count} lượt sử dụng cho {username}.")
    delete_message_after_delay(message.chat.id, sent_message.message_id, 15)

@bot.message_handler(commands=['top'])
def top_users(message):
    sorted_users = sorted(usage_limits.items(), key=lambda item: item[1], reverse=True)
    top_users_text = "\n".join([f"@{username}: {count} lượt" for username, count in sorted_users])
    sent_message = bot.send_message(message.chat.id, f"Xếp hạng thành viên theo số lượt sử dụng:\n{top_users_text}")
    delete_message_after_delay(message.chat.id, sent_message.message_id, 15)

@bot.message_handler(commands=['tracuu'])
def tra_cuu(message):
    if len(message.text.split()) != 2:
        sent_message = bot.reply_to(message, "Cú pháp không hợp lệ. Sử dụng: /tracuu @username")
        delete_message_after_delay(message.chat.id, sent_message.message_id, 15)
        return

    username = message.text.split()[1].lstrip('@')

    if username in usage_limits:
        sent_message = bot.send_message(message.chat.id, f"@{username} có {usage_limits[username]} lượt sử dụng.")
    else:
        sent_message = bot.send_message(message.chat.id, f"@{username} chưa được cấp lượt sử dụng.")
    delete_message_after_delay(message.chat.id, sent_message.message_id, 15)

@bot.message_handler(commands=['play'])
def play_game(message):
    sent_message = bot.send_message(message.chat.id, "Trò chơi bắt đầu! Vui lòng chọn một số từ 1 đến 6 trong 60 giây tới.")
    delete_message_after_delay(message.chat.id, sent_message.message_id, 15)

    selected_numbers = {}

    def collect_responses(message):
        try:
            number = int(message.text)
            if 1 <= number <= 6:
                selected_numbers[message.from_user.username] = number
        except ValueError:
            pass

    # Đăng ký handler để thu thập phản hồi từ người chơi
    bot.register_message_handler(collect_responses, content_types=['text'], func=lambda msg: msg.chat.id == message.chat.id)

    # Bắt đầu timer để kết thúc trò chơi sau 60 giây
    Timer(60, determine_winner, args=(message.chat.id, selected_numbers)).start()

def determine_winner(chat_id, selected_numbers):
    chosen_number = random.randint(1, 6)
    winners = [username for username, number in selected_numbers.items() if number == chosen_number]

    if winners:
        bot.send_message(chat_id, f"Số được chọn là {chosen_number}. Các người chơi sau đã chọn đúng số:")
        for winner in winners:
            bot.send_message(chat_id, f"@{winner}")

        if len(winners) > 1:
            final_winner = random.choice(winners)
            bot.send_message(chat_id, f"Người chiến thắng cuối cùng là @{final_winner}. Bạn nhận được 10 lượt sử dụng!")
            if final_winner in usage_limits:
                usage_limits[final_winner] += 10
            else:
                usage_limits[final_winner] = 10
        else:
            final_winner = winners[0]
            bot.send_message(chat_id, f"Người chiến thắng là @{final_winner}. Bạn nhận được 10 lượt sử dụng!")
            if final_winner in usage_limits:
                usage_limits[final_winner] += 10
            else:
                usage_limits[final_winner] = 10
    else:
        bot.send_message(chat_id, f"Số được chọn là {chosen_number}. Không có người chơi nào chọn đúng số.")
        
bot.polling()
