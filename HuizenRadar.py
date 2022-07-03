import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import yaml  # used for the config.yaml file
import logging
# import all plugins
from plugins import *


def start_bot():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.getLogger('apscheduler.executors.default').propagate = False

    # load config.yaml
    with open('config.yaml', 'r') as f:
        config = yaml.full_load(f)

    api_key = config['TELEGRAM']['API_KEY']

    updater = Updater(token=api_key, use_context=True)
    dispatcher = updater.dispatcher

    # Command Handlers

    updater.job_queue.run_repeating(funda.check_funda, interval=3600, first=1)
    updater.job_queue.run_repeating(schakel.check_schakel, interval=3600, first=1)
    #updater.job_queue.run_repeating(teamsanders.teamsanders, interval=3600, first=0)
    updater.job_queue.run_repeating(weusthuis.check_weusthuis, interval=3600, first=1)
    updater.job_queue.run_repeating(marcel_kon.check_marcel_kon, interval=3600, first=1)
    updater.job_queue.run_repeating(hoitink.check_hoitink, interval=3600, first=1)

    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == '__main__':
    start_bot()
