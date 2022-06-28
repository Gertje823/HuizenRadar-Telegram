from datetime import datetime


def new_message(update):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M")}: New message from {update.message.from_user.first_name} (@{update.message.from_user.username})')
    print(f'Message text: {update.message.text}')