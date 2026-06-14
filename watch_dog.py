import asyncio
import subprocess
import time
import os
import logging
from datetime import datetime, timedelta

from bilibili_api import Credential
from bilibili_api.channel_series import add_aids_to_series
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import parse
from pathlib import Path
from autosv import slice_video_by_danmaku

import upload
from config import get_value_by_key_recursive

# 配置日志（便于排查问题）
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


async def custom_process(file_path):
    """
    自定义处理函数：视频文件写入完成后执行的操作
    请根据实际需求修改此函数内容
    """
    logging.info(f"开始处理视频文件: {file_path}")
    # 示例：打印文件大小
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    logging.info(f"文件大小: {file_size:.2f} MB")

    # 2、录制完成后将弹幕从xml转换为ass格式
    video_file = os.path.splitext(file_path)[0] + '.flv'
    ass_file = os.path.splitext(file_path)[0] + '.ass'
    events = parse.parse_douyu_danmaku(file_path)
    logging.info("生成ass文件开始")
    parse.events_to_ass(events, ass_file)
    logging.info("生成ass文件结束")
    # 3、调用 FFmpeg 压制视频
    # video_danmu_file = os.path.splitext(file_path)[0] + '弹幕版.mp4'
    #
    # work_dir = Path(file_path).parent
    # original_dir = os.getcwd()
    # try:
    #     os.chdir(work_dir)
    #     # 相对路径（仅文件名，不含目录）
    #     video_name = Path(video_file).name
    #     ass_name = Path(ass_file).name
    #     output_name = Path(video_danmu_file).name
    #     cmd = f'ffmpeg -i "{video_name}" -vf "ass={ass_name}" -c:a copy "{output_name}"'
    #     subprocess.run(cmd, shell=True, check=True)
    #     logging.info(f"弹幕压制成功: {video_danmu_file}")
    # except subprocess.CalledProcessError as e:
    #     logging.error(f"FFmpeg 执行失败: {e}")
    # finally:
    #     os.chdir(original_dir)  # 恢复原工作目录

    # 4、利用auto-slice-video自动完成切片功能
    ass_path = ass_file
    video_path = video_file
    # 传入视频及弹幕文件进行智能切片,对一段视频提取 3 条高能片段，每个片段 300 秒，允许最大重叠 60 秒。
    logging.info("切片开始")
    output_video_path = slice_video_by_danmaku(ass_path, video_path, 300, 3, 60, 1)
    logging.info("切片结束")

    cover_url = os.path.splitext(file_path)[0] + '.jpg'
    # 5、上传自媒体网站
    for path in output_video_path:
        logging.info(path)
        await upload.upload_to_bilibili("猪小杰123",path,cover_url)

    logging.info("开始清理文件")
    # 6、检测上传成功后，删除源文件释放空间
    os.remove(file_path)
    logging.info(f"文件已清理：{file_path}" )
    os.remove(ass_path)
    logging.info(f"文件已清理：{ass_path}")
    os.remove(video_path)
    logging.info(f"文件已清理：{video_path}")


    for path in output_video_path:
        os.remove(Path(path))
        logging.info(f"文件已清理：{path}")
    os.remove(cover_url)
    logging.info(f"文件已清理：{cover_url}")

    logging.info(f"处理完成: {file_path}")
    # input("按回车键退出...")

# 检测xml文件最后修改时间，如果大于5分钟，则开始执行切片上传操作
async def check_files(directory_path, interval=60):
    """
    定时检查目录下所有XML文件的最后修改时间

    参数:
        directory_path: 要监控的目录路径
        interval: 检查间隔（秒），默认60秒
    """
    while True:
        try:
            current_time = datetime.now()
            # 计算5分钟前的时间点
            five_minutes_ago = current_time - timedelta(minutes=5)

            # 遍历目录下所有XML文件
            for filename in os.listdir(directory_path):
                if filename.lower().endswith('.xml'):
                    file_path = os.path.join(directory_path, filename)

                    # 获取文件的最后修改时间
                    if os.path.isfile(file_path):
                        mod_timestamp = os.path.getmtime(file_path)
                        mod_time = datetime.fromtimestamp(mod_timestamp)

                        # 判断是否早于5分钟前
                        if mod_time < five_minutes_ago:
                            custom_process(file_path)

        except Exception as e:
            print(f"扫描过程中出错: {e}")

        # 等待设定的间隔时间后再次检查
        time.sleep(interval)


# def start_timer(directory_path, interval=60, daemon=False):
#     """
#     启动定时器线程
#
#     参数:
#         directory_path: 要监控的目录路径
#         interval: 检查间隔（秒），默认60秒
#         daemon: 是否作为守护线程运行
#     """
#     timer_thread = threading.Thread(
#         target=check_files,
#         args=(directory_path, interval),
#         daemon=daemon
#     )
#     timer_thread.start()
#     return timer_thread

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