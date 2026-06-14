import asyncio
import logging
from asyncio import sleep
from pathlib import Path

from bilibili_api import sync, video_uploader, Credential, user, channel_series, video
from bilibili_api.utils.network import Api

from config import credential,cover_img_url


async def list_all_my_series():
    # 1. 认证
    credential = Credential(
        sessdata="e35e940a%2C1796701790%2Cf657a%2A62CjDo4ZTHqe_im7o2GTvVCOFuhq6Q9nogBxwSXHBAwQDpBur1ebWUonTK9r43GjU7sgYSVmFTZ1owU2d5dlQwYnNud2NCTG9fVHZnZlRHYlVjMmRrX1dVdEZVSEZjQVlKSXREQVNIeUszUS1FYVBaOXdJMndwSGoyWnpWNGJzVmpIT1JSai1uMmxRIIEC",
        bili_jct="f43703674f1c47995c218f600a45099b",
        # buvid3="你的 buvid3" # 有时需要，可选
    )

    """
    获取当前用户的所有合集（新版 Season）
    """
    try:
        # 从你的 upload.py 中获取全局 credential 对象
        # 如果你的 upload.py 中没有定义 credential，在这里定义

        # 使用正确的 API 接口（注意是 x2/creative/web/seasons，不是 x/creative/web/season/list）
        api = Api(
            method="GET",
            url="https://api.bilibili.com/x2/creative/web/seasons",
            credential=credential
        )

        params = {
            "pn": 1,      # 页码
            "ps": 50      # 每页数量
        }

        result = await api.update_params(**params).result

        if result.get('code') != 0:
            print(f"获取合集失败: {result.get('message')}")
            return []

        data = result.get('data', {})
        seasons = data.get('seasons', [])

        series_list = []
        for item in seasons:
            season = item.get('season', {})
            series_info = {
                'id': season.get('id'),           # 合集ID（重要）
                'title': season.get('title'),     # 合集标题
                'desc': season.get('desc', ''),   # 合集描述
                'cover': season.get('cover'),     # 封面URL
                'ep_num': season.get('ep_num', 0) # 视频数量
            }
            series_list.append(series_info)

            print(f"✅ 合集ID: {series_info['id']}")
            print(f"   标题: {series_info['title']}")
            print(f"   视频数: {series_info['ep_num']}")
            print("-" * 40)

        print(f"共找到 {len(series_list)} 个合集")
        return series_list

    except Exception as e:
        print(f"获取合集列表失败: {e}")
        return []

async def wait_for_video_ready(bvid: str, credential: Credential, check_interval: int = 5, max_wait: int = 600):
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
                logging.info(f"视频审核通过！bvid: {bvid}")
                return True
            elif state == -1:  # 审核中
                logging.info(f"审核中... 等待 {check_interval} 秒")
            elif state == -2:  # 审核不通过
                logging.info("审核未通过")
                return False
            elif state == 1:  # 已删除
                logging.info("视频已被删除")
                return False
            else:
                logging.info(f"视频状态: {state}")

            await asyncio.sleep(check_interval)

        except Exception as e:
            # logging.info(f"获取视频状态失败: {e}")
            logging.info(f"审核中... 等待 {check_interval} 秒")
            await asyncio.sleep(check_interval)

    return False

# 添加至合集中
async def add_to_series(aid,series_id, credential: Credential):
    # 3. 视频就绪后，添加到合集
    result = await channel_series.add_aids_to_series(
        series_id=series_id,  # 改参数名
        aids=[aid],
        credential=credential
    )
    print(f"添加合集结果: {result}")

# 上传
async def upload(video_path):
    # 1. 设置认证信息


    # 2. 设置视频元信息
    time = Path(video_path).name[6:25]
    # 2. 【重点】根据官方文档，创建 VideoMeta 对象
    #    下面的参数是我根据你之前的需求和通用API知识猜测的，
    #    **请务必替换成官方文档中列出的正确参数名和值**。
    vu_meta = video_uploader.VideoMeta(
        title="【OK林仔】"+time+"直播精彩片段",
        tid=3,  # 分区ID，比如 17 是“单机游戏”
        tags=["Dota2", "刀塔2","OK林仔","林仔"],  # 注意参数名可能是 tags
        desc="【OK林仔】"+time+"直播精彩片段",  # 注意参数名可能是 desc 或 description
        cover=cover_img_url,
        # season_id=8319296      # 合集ID的准确参数名，请务必查阅文档确认！
    )

    series_id = 8319296
    # 3. 创建视频文件页
    page = video_uploader.VideoUploaderPage(path=video_path,title="这是标题")
    uploader = video_uploader.VideoUploader([page], vu_meta, credential)
    upload_result = await uploader.start()
    logging.info(f"上传结果: {upload_result}")

    # 获取视频的 aid（注意是 aid，不是 bvid）
    aid = upload_result.get('aid')
    bvid = upload_result.get('bvid')
    logging.info([aid])
    logging.info(bvid)
  # 2. 等待视频审核完成（智能检测，而不是固定等待）
    logging.info("等待视频审核完成...")
    is_ready = await wait_for_video_ready(bvid, credential)


    # if not is_ready:
    #     print("视频未就绪，放弃添加到合集")
    #     return

    # logging.info("开始等待")
    # await asyncio.sleep(10)  # 暂停 10 秒
    # logging.info("等待完成")

    # await add_to_series(aid,series_id,credential)
    # result = await channel_series.add_aids_to_series(
    #     series_id=series_id,  # 改参数名
    #     aids=[aid],
    #     credential=credential
    # )
    # print(f"添加合集结果: {result}")
