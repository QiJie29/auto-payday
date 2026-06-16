import asyncio
import logging
import os
import subprocess
from pathlib import Path

import upload
import utils

if __name__ == '__main__':
    # 出现故障后单点上传
    base_path = r"C:\Users\JQJ\Downloads\斗鱼\debug"
    path = f"{base_path}\\3474s_2026-06-15 21-12-10-249 顶级一号位教学，五黑有位置弹幕版.flv"
    cover_url = f"{base_path}\\2026-06-15 21-12-10-249 顶级一号位教学，五黑有位置.jpg"
    # asyncio.run(upload.upload_to_bilibili("猪小杰123",path,cover_url))
    utils.delete_files_containing_keyword(Path(cover_url).parent, Path(cover_url).stem, False, False)
