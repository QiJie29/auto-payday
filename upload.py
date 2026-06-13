import asyncio
import logging
from asyncio import sleep
from pathlib import Path

from bilibili_api import sync, video_uploader, Credential, user, channel_series, video
from bilibili_api.channel_series import ChannelSeriesType


async def list_all_my_series():
    # 1. 认证
    credential = Credential(
        sessdata="e35e940a%2C1796701790%2Cf657a%2A62CjDo4ZTHqe_im7o2GTvVCOFuhq6Q9nogBxwSXHBAwQDpBur1ebWUonTK9r43GjU7sgYSVmFTZ1owU2d5dlQwYnNud2NCTG9fVHZnZlRHYlVjMmRrX1dVdEZVSEZjQVlKSXREQVNIeUszUS1FYVBaOXdJMndwSGoyWnpWNGJzVmpIT1JSai1uMmxRIIEC",
        bili_jct="f43703674f1c47995c218f600a45099b",
        # buvid3="你的 buvid3" # 有时需要，可选
    )

    # 获取自己的 UID
    my_info = await user.get_self_info(credential=credential)
    uid = my_info.get('mid')
    print(f"当前用户UID: {uid}")

    # 方法1：使用 channel_series 模块获取所有 Series（旧版视频列表）
    # 注意：这个函数可能需要传入 uid
    try:
        # 尝试不同的参数名
        series_list = await channel_series.get_series_list(uid=uid)
        print("\n---【视频列表 (Series)】---")
        for s in series_list:
            print(f"  名称: {s.get('name')}, series_id: {s.get('id')}")
    except AttributeError:
        print("get_series_list 不存在，尝试其他方法...")
    except Exception as e:
        print(f"方法1失败: {e}")

    # 方法2：直接列出 my_user 的所有可用方法，找到正确的函数
    my_user = user.User(uid=uid, credential=credential)
    print("\n---【User 对象中与 series/season 相关的方法】---")
    methods = [m for m in dir(my_user) if 'series' in m.lower() or 'season' in m.lower() or 'list' in m.lower()]
    for m in methods:
        print(f"  {m}")

async def wait_for_video_ready(bvid: str, credential: Credential, check_interval: int = 5, max_wait: int = 300):
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
async def add_to_series(aid: int, season_id: int, credential: Credential):
    # 3. 视频就绪后，添加到合集
    series = channel_series.ChannelSeries(
        id_=season_id,  # 你的合集ID（8319296）
        type_=ChannelSeriesType.SEASON,  # 指定为新版合集
        credential=credential
    )

    result = await channel_series.set_follow_channel_season(
        season_id=season_id,
        aid=[aid],  # 或 aids=[aid]
        credential=credential
    )

    # 查看可用方法
    print([m for m in dir(series) if not m.startswith('_')])

# 上传
async def upload(video_path):
    # 1. 设置认证信息
    credential = Credential(
        sessdata="e35e940a%2C1796701790%2Cf657a%2A62CjDo4ZTHqe_im7o2GTvVCOFuhq6Q9nogBxwSXHBAwQDpBur1ebWUonTK9r43GjU7sgYSVmFTZ1owU2d5dlQwYnNud2NCTG9fVHZnZlRHYlVjMmRrX1dVdEZVSEZjQVlKSXREQVNIeUszUS1FYVBaOXdJMndwSGoyWnpWNGJzVmpIT1JSai1uMmxRIIEC",
        bili_jct="f43703674f1c47995c218f600a45099b",
        # buvid3="你的 buvid3" # 有时需要，可选
    )

    # 2. 设置视频元信息
    time = Path(video_path).name[6:25]
    # 2. 【重点】根据官方文档，创建 VideoMeta 对象
    #    下面的参数是我根据你之前的需求和通用API知识猜测的，
    #    **请务必替换成官方文档中列出的正确参数名和值**。
    vu_meta = video_uploader.VideoMeta(
        title="【OK林仔】"+time+"直播录像",
        tid=3,  # 分区ID，比如 17 是“单机游戏”
        tags=["Dota2", "刀塔2","OK林仔","林仔"],  # 注意参数名可能是 tags
        desc="【OK林仔】"+time+"直播录像",  # 注意参数名可能是 desc 或 description
        cover=r"C:\Users\JQJ\Downloads\斗鱼\ok林仔\80979114-df2e-4733-87e8-9068b5d4b391.png",
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


    if not is_ready:
        print("视频未就绪，放弃添加到合集")
        return

    logging.info("开始等待")
    await asyncio.sleep(10)  # 暂停 10 秒
    logging.info("等待完成")

    await add_to_series(aid,8319296,credential)