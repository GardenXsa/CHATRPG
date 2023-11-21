import asyncio
import random
import string

from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async, run_js

chat_msgs = []
online_users = {}
teams = {}
world_events = []  # Список событий в мире

MAX_MESSAGES_COUNT = 100

async def main():
    global chat_msgs
    
    put_markdown("## 🗡️ Добро пожаловать в RPG Чат!\nИсходный код данного чата укладывается в 100 строк кода!")

    msg_box = output()
    put_scrollable(msg_box, height=300, keep_bottom=True)

    nickname = await input("⚔️ Войти в чат", required=True, placeholder="Ваше имя", validate=lambda n: "Такой ник уже используется!" if n in online_users or n == '📢' else None)
    online_users[nickname] = {
        'team': None,
        'is_leader': False
    }

    chat_msgs.append(('📢', f'{nickname} присоединился к чату!'))
    msg_box.append(put_markdown(f'📢 {nickname} присоединился к чату'))

    refresh_task = run_async(refresh_msg(nickname, msg_box))

    while True:
        data = await input_group("💬 Новое сообщение", [
            input(placeholder="Текст сообщения ...", name="msg"),
            actions(name="cmd", buttons=["Отправить 📩", {'label': "Выйти из чата", 'type': 'cancel'}])
        ], validate = lambda m: ('msg', "Введите текст сообщения!") if m["cmd"] == "Отправить 📩" and not m['msg'] else None)

        if data is None:
            break

        if data['msg'].lower().startswith('/battle '):
            battle_cmd = data['msg'].split()

            try:
                team_size = int(battle_cmd[1])
                team_count = int(battle_cmd[2])
                if team_size < 1 or team_count < 1 or team_count > 7:
                    raise ValueError
            except (IndexError, ValueError):
                msg_box.append(put_markdown(f"⚔️ {nickname}: Некорректная команда для битвы!"))
                continue

            if len(online_users) - len(teams) < team_size * team_count:
                msg_box.append(put_markdown(f"⚔️ {nickname}: Недостаточно участников для битвы!"))
                continue

            if online_users[nickname]['team']:
                msg_box.append(put_markdown(f"⚔️ {nickname}: Вы уже находитесь в команде!"))
                continue

            team_name = await input("⚔️ Название команды", required=True, placeholder="Введите название")
            team_color = ''.join(random.choices(string.hexdigits[:-6], k=6))
            team_num = len(teams) + 1
            teams[team_num] = {
                'name': team_name,
                'color': team_color,
                'leader': nickname
            }
            online_users[nickname]['team'] = team_num
            online_users[nickname]['is_leader'] = True

            msg_box.append(put_markdown(f"⚔️ {nickname}: Создана команда {team_num} - {team_name}!"))

            if len(teams) == team_count * team_size:
                battle_teams = [[] for _ in range(team_count)]
                for name, user_data in online_users.items():
                    team_num = user_data['team']
                    if team_num:
                        battle_teams[(team_num - 1) % team_count].append(name)
                
                random.shuffle(battle_teams)
                msg_box.append(put_markdown(f"⚔️ Битва началась!"))
                for i, team in enumerate(battle_teams, 1):
                    team_name = teams[i]['name']
                    team_color = teams[i]['color']
                    msg_box.append(put_markdown(f'<span style="color: #{team_color}">⚔️ Команда {i} - {team_name}: {", ".join(team)}</span>'))
                teams.clear()
                online_users.clear()
                continue

        if data['msg'].lower().startswith('/world'):
            await add_world_event(nickname, msg_box)

        msg_box.append(put_markdown(f"{nickname}: {data['msg']}"))
        chat_msgs.append((nickname, data['msg']))

    refresh_task.close()

async def refresh_msg(nickname, msg_box):
    last_idx = len(chat_msgs)
    while True:
        msgs = chat_msgs[last_idx:]
        last_idx = len(chat_msgs)
        for role, msg in msgs:
            if role == '📢':
                msg_box.append(put_markdown(f'📢 {msg}'))
            elif role == '🌍':
                msg_box.append(put_markdown(f'🌍 {msg}'))
            else:
                msg_box.append(put_markdown(f'{role}: {msg}'))
        await asyncio.sleep(0.1)

async def add_world_event(nickname, msg_box):
    event_name = await input("🌍 Название события", required=True, placeholder="Введите название события")
    event_description = await textarea("📝 Описание события", required=True, placeholder="Введите описание события")
    
    world_events.append((event_name, event_description))
    msg_box.append(put_markdown(f"🌍 {event_name}: {event_description}"))
    chat_msgs.append(('🌍', f"{event_name}: {event_description}"))

start_server(main, port=8080)