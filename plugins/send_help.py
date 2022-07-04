"""
*help* - Shows information about all of the plugins.
Usage: /help
"""
from telegram import BotCommand
import plugins


def send_help(update, context):
    plugins.new_message.new_message(update)

    if plugins.enable_check.enable_check(__name__):
        return

    if not context.args:

        helptext = ''

        for item in plugins.__all__:
            if text := getattr(plugins, item).__doc__:
                helptext += text

        context.bot.send_message(chat_id=update.message.chat_id, parse_mode='markdown', text=helptext)

    # todo define proper command scopes to only show commands in relevant areas
    # todo maybe move this somewhere so it's automatically run after every reboot / update
    elif context.args[0] == 'setcommandlist':
        commandlist = []
        for item in plugins.__all__:
            if text := getattr(plugins, item).__doc__:
                if text.count('\n') == 3:
                    text = text.split('\n')[1]
                    command = text.split('-')[0].replace('*', '').strip()
                    description = text.split('-')[1].strip()
                    commandlist.append(BotCommand(command, description))

        context.bot.set_my_commands(commands=commandlist)
