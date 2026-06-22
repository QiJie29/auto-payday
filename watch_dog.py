import asyncio
import subprocess
import time
import os
import logging
from datetime import datetime, timedelta

from pathlib import Path
from autosv import slice_video_by_danmaku


import upload
import utils

# 配置日志（便于排查问题）
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


async def custom_process(xml_url):
    """
    自定义处理函数：视频文件写入完成后执行的操作
    请根据实际需求修改此函数内容
    """
    logging.info(f"开始处理视频文件: {xml_url}")
    # 示例：打印文件大小
    file_size = os.path.getsize(xml_url) / (1024 * 1024)
    logging.info(f"文件大小: {file_size:.2f} MB")

    # 获取主播名称
    up = utils.get_up(xml_url)

    # 2、录制完成后将弹幕从xml转换为ass格式
    logging.info(f"生成ass文件开始")
    ass_url = utils.parse_douyu_danmaku(xml_url)
    # ass_url = f'{Path(xml_url).parent}\\2026-06-16 01-42-23-397 顶级一号位教学，五黑有位置 by bililive_tools.ass'
    logging.info(f"生成ass文件结束{ass_url}")

    video_url = os.path.splitext(xml_url)[0] + '.mp4'
    press_video_url = video_url
    config = utils.load_json_config('config.json')
    if utils.get_value_by_key_recursive(config,"up",up,"press_danmu_to_video") :
        # 3、调用 FFmpeg 压制视频
        logging.info(f"压制弹幕视频开始")
        video_danmu_url = utils.press_danmu_to_video(video_url,ass_url)
        logging.info(f"压制弹幕视频结束")
        # 如果需要压制，则将压制完成的视频传入函数进行切片
        press_video_url = video_danmu_url

    # 4、利用auto-slice-video自动完成切片功能
    # 传入视频及弹幕文件进行智能切片,对一段视频提取 3 条高能片段，每个片段 300 秒，允许最大重叠 60 秒。
    logging.info("切片开始")
    output_video_path = slice_video_by_danmaku(ass_url, press_video_url, 300, 3, 60, 1)
    logging.info("切片结束")

    # 获取封面
    cover_url = os.path.splitext(xml_url)[0] + '.jpg'
    # 5、上传自媒体网站
    if utils.get_value_by_key_recursive(config, "up", up, "upload"):
        for path in output_video_path:
            logging.info(path)
            await upload.upload_to_bilibili("猪小杰123",path,cover_url)

    logging.info("清理文件开始")
    # 6、检测上传成功后，删除源文件释放空间
    remove_original_file = utils.get_value_by_key_recursive(config, "up", up, "remove_original_file")
    utils.delete_files_containing_keyword(Path(xml_url).parent,Path(xml_url).stem,False,not remove_original_file)
    logging.info("清理文件结束")
    logging.info(f"处理完成: {xml_url}")
    # input("按回车键退出...")

# 检测xml文件最后修改时间，如果大于5分钟，则开始执行切片上传操作
async def check_and_process(directory, interval=60, delay_minutes=5):
    """
    监控单个目录
    """
    processed = set()

    while True:
        try:
            # 查找所有XML文件
            xml_files = Path(directory).rglob("*.xml")

            for file_path in xml_files:
                if not file_path.is_file():
                    continue

                # 检查修改时间
                mtime = os.path.getmtime(file_path)
                file_time = datetime.fromtimestamp(mtime)

                if datetime.now() - file_time >= timedelta(minutes=delay_minutes):
                    if str(file_path) not in processed:
                        print(f"[{datetime.now()}] 处理: {file_path}")

                        # ===== 你的自定义代码 =====
                        # 在这里写你要执行的操作
                        await custom_process(file_path)
                        # 例如：读取XML、调用API等
                        # =========================

                        processed.add(str(file_path))

            await asyncio.sleep(interval)

        except Exception as e:
            print(f"错误: {e}")
            await asyncio.sleep(interval)