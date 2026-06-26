import asyncio
import logging
import os
from asyncio import sleep
from pathlib import Path

from bilibili_api import sync, video_uploader, Credential, user, channel_series, video
from bilibili_api.channel_series import ChannelSeries
from bilibili_api.utils.network import Api

import utils


async def wait_for_video_ready(cut_video_url: str,bvid: str, credential: Credential, check_interval: int = 5, max_wait: int = 3600):
    """等待视频审核通过"""
    v = video.Video(bvid=bvid, credential=credential)

    start_time = asyncio.get_event_loop().time()

    while True:
        if asyncio.get_event_loop().time() - start_time > max_wait:
            logging.info(f"等待超时（{max_wait}秒）")
            return False

        try:
            # 关键：必须 await
            info = await v.get_info()

            # info 现在是一个字典，可以安全使用 .get()
            state = info.get('state')

            if state == 0:  # 审核通过
                logging.info(f"{cut_video_url}视频审核通过！bvid: {bvid}")
                return True
            elif state == -1:  # 审核中
                logging.info(f"{cut_video_url}审核中... 等待 {check_interval} 秒")
            elif state == -2:  # 审核不通过
                logging.info(f"{cut_video_url}审核未通过")
                return False
            elif state == 1:  # 已删除
                logging.info(f"{cut_video_url}视频已被删除")
                return False
            else:
                logging.info(f"{cut_video_url}视频状态: {state}")

            await asyncio.sleep(check_interval)

        except Exception as e:
            # logging.info(f"获取视频状态失败: {e}")
            logging.info(f"{cut_video_url}审核中... 等待 {check_interval} 秒")
            await asyncio.sleep(check_interval)

# 添加至合集中
# async def add_to_series(aid,series_id, credential: Credential):
#     # 3. 视频就绪后，添加到合集
#     result = await channel_series.add_aids_to_series(
#         series_id=series_id,  # 改参数名
#         aids=[aid],
#         credential=credential
#     )
#     print(f"添加合集结果: {result}")

# 上传
async def upload_to_bilibili(uname: str,cut_video_url: str,cover_url: str):
    # 1. 设置认证信息
    # B站用户cookie等数据
    config = utils.load_json_config('config.json')
    credential = utils.get_credential(uname)

    # 2. 设置视频元信息
    # 从视频路径中提取时间信息
    time = Path(cut_video_url).stem.split('_', 1)[1]
    # 从视频路径中的父目录提取主播名称
    up = utils.get_value_by_key_recursive(config,"xml_url",os.path.dirname(cut_video_url),"up")
    tid = utils.get_value_by_key_recursive(config,"xml_url",os.path.dirname(cut_video_url),"tid")
    tags = utils.get_value_by_key_recursive(config, "xml_url", os.path.dirname(cut_video_url), "tags")

    title = f"【{up}】{time}直播精彩片段"
    logging.info(f"开始上传{cut_video_url}")
    vu_meta = video_uploader.VideoMeta(
        title = title,
        tid = tid,  # 分区ID，比如 17 是“单机游戏”
        tags = tags,  # 注意参数名可能是 tags
        desc = title,  # 注意参数名可能是 desc 或 description
        cover = cover_url,
        # season_id=8319296      # 合集ID的准确参数名，请务必查阅文档确认！
    )

    # 3. 创建视频文件页
    page = video_uploader.VideoUploaderPage(path=cut_video_url,title="这是标题")
    uploader = video_uploader.VideoUploader([page], vu_meta, credential)
    upload_result = await uploader.start()
    logging.info(f"上传结果: {upload_result}")

    # 获取视频的 aid（注意是 aid，不是 bvid）
    aid = upload_result.get('aid')
    bvid = upload_result.get('bvid')
    logging.info(aid)
    logging.info(bvid)
    # 2. 等待视频审核完成（智能检测，而不是固定等待）
    logging.info("等待视频审核完成...")
    is_ready = await wait_for_video_ready(cut_video_url,bvid, credential)

    # 将视频添加到合集
    if is_ready:
        season_id = utils.get_value_by_key_recursive(config, "xml_url", os.path.dirname(cut_video_url), "season_id")
        # 当json中存有合集id，才会执行加入合集的代码
        if season_id != 0:
            section_id = utils.get_value_by_key_recursive(config, "xml_url", os.path.dirname(cut_video_url), "section_id")
            sessdata = utils.get_cookies(uname).get('SESSDATA')
            bili_jct = utils.get_cookies(uname).get('bili_jct')

            cid = utils.get_video_info(aid).get('cid')
            utils.add_video_to_season(season_id,section_id,aid,cid,sessdata,bili_jct)