import re
import traceback
import typing as T

import pixiv_api
from bot_utils import *
from settings import settings

trigger = settings["illust"]["trigger"]

if isinstance(trigger, str):
    trigger = [trigger]


def __check_triggered__(message: MessageChain) -> bool:
    content = plain_str(message)
    for x in trigger:
        if x in content:
            return True
    return False


def __findall_illust_ids__(message: MessageChain) -> T.Generator[int, None, None]:
    content = plain_str(message)
    regex = re.compile("[1-9][0-9]*")
    for match_result in regex.finditer(content):
        yield int(match_result.group())


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
    try:
        if __check_triggered__(message):
            for illust_id in __findall_illust_ids__(message):
                print(f"pixiv illust {illust_id} asked.")

                result = pixiv_api.api().illust_detail(illust_id)
                if "error" in result:
                    await reply(bot, source, subject, [Plain(result["error"]["user_message"])])
                else:
                    await reply(bot, source, subject, pixiv_api.illust_to_message(result["illust"]))
    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
