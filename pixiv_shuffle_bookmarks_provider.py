import traceback
import typing as T

import pixiv_api
from bot_utils import *
from settings import settings

trigger = settings["shuffle_bookmarks"]["trigger"]

if isinstance(trigger, str):
    trigger = [trigger]

user_id: int = settings["shuffle_bookmarks"]["user_id"]
search_r18: bool = settings["shuffle_bookmarks"]["search_r18"]
search_r18g: bool = settings["shuffle_bookmarks"]["search_r18g"]
not_found_message: str = settings["shuffle_bookmarks"]["not_found_message"]
shuffle_method: str = settings["shuffle_bookmarks"]["shuffle_method"]
search_cache_filename: str = settings["shuffle_bookmarks"]["search_cache_filename"]
search_cache_outdated_time: T.Optional[int] = settings["shuffle_bookmarks"]["search_cache_outdated_time"] \
    if "search_cache_outdated_time" in settings["shuffle_bookmarks"] else None  # nullable
search_item_limit: T.Optional[int] = settings["shuffle_bookmarks"]["search_item_limit"] \
    if "search_item_limit" in settings["shuffle_bookmarks"] else None  # nullable
search_page_limit: T.Optional[int] = settings["shuffle_bookmarks"]["search_page_limit"] \
    if "search_page_limit" in settings["shuffle_bookmarks"] else None  # nullable


def __get_bookmarks__() -> T.Sequence[dict]:
    import os

    def illust_fliter(illust: dict) -> bool:
        # R-18/R-18G规避
        if pixiv_api.has_tag(illust, "R-18") and not search_r18:
            return False
        if pixiv_api.has_tag(illust, "R-18G") and not search_r18g:
            return False
        return True

    def load_from_pixiv() -> T.Sequence[dict]:
        illusts = list(pixiv_api.iter_illusts(search_func=pixiv_api.api().user_bookmarks_illust,
                                              illust_filter=illust_fliter,
                                              init_qs=dict(user_id=pixiv_api.api().user_id),
                                              search_item_limit=search_item_limit,
                                              search_page_limit=search_page_limit))
        print(f"{len(illusts)} illust were found in user [{user_id}]'s bookmarks.")
        return illusts

    # 缓存文件路径
    dirpath = os.path.curdir
    filename = f"{user_id}_{search_cache_filename}"
    cache_file = os.path.join(dirpath, filename)

    illusts = pixiv_api.get_illusts_cached(load_from_pixiv_func=load_from_pixiv,
                                           cache_file=cache_file,
                                           cache_outdated_time=search_cache_outdated_time)
    return illusts


def __check_triggered__(message: MessageChain) -> bool:
    content = plain_str(message)
    for x in trigger:
        if x in content:
            return True
    return False


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
    try:
        if __check_triggered__(message):
            print(f"pixiv shuffle bookmarks asked.")
            illusts = __get_bookmarks__()
            if len(illusts) > 0:
                illust = pixiv_api.shuffle_illust(illusts, shuffle_method)
                print(f"""illust {illust["id"]} selected.""")
                await reply(bot, source, subject, pixiv_api.illust_to_message(illust))
            else:
                await reply(bot, source, subject, [Plain(not_found_message)])

    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
