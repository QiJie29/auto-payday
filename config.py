from bilibili_api import Credential

import json

def load_json_config(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 主播相关数据存储
live_stream_data = [
    {
        "up": "OK林仔",
        "conver_img_url": r"C:\Users\JQJ\Downloads\斗鱼\ok林仔\cover.png",
        "xml_url": r"C:\Users\JQJ\Downloads\斗鱼\ok林仔\test",
        "tag": ""
    },
    {
        "up":""
    }

]

# OK林仔直播封面
cover_img_url = r"C:\Users\JQJ\Downloads\斗鱼\ok林仔\cover.png"

# xml文件路径（实时监控）
xml_directory = r"C:\Users\JQJ\Downloads\斗鱼\ok林仔\test"  # Windows示例

# B站用户cookie等数据
credential = Credential(
    sessdata="e35e940a%2C1796701790%2Cf657a%2A62CjDo4ZTHqe_im7o2GTvVCOFuhq6Q9nogBxwSXHBAwQDpBur1ebWUonTK9r43GjU7sgYSVmFTZ1owU2d5dlQwYnNud2NCTG9fVHZnZlRHYlVjMmRrX1dVdEZVSEZjQVlKSXREQVNIeUszUS1FYVBaOXdJMndwSGoyWnpWNGJzVmpIT1JSai1uMmxRIIEC",
    bili_jct="f43703674f1c47995c218f600a45099b",
    # buvid3="你的buvid3"  # 可选
)