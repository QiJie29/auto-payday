import xml.etree.ElementTree as ET
import pysubs2
from pysubs2 import SSAFile, SSAEvent, Color

def parse_douyu_danmaku(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    events = []
    for d in root.findall('d'):
        # 获取 p 属性，按逗号拆分
        p_attr = d.get('p', '')
        if not p_attr:
            continue
        parts = p_attr.split(',')
        if len(parts) < 1:
            continue
        # 第一个是出现时间（秒）
        start_sec = float(parts[0])
        # 弹幕文本
        text = d.text or ''
        # 可选：提取颜色（第4个参数，默认白色）
        # color_decimal = int(parts[3]) if len(parts) > 3 else 16777215
        # 将十进制颜色转换为 ASS 的 &HBBGGRR 格式（这里略）
        events.append({
            'start': start_sec,
            'text': text,
            # 可以加样式、颜色等
        })
    return events

def events_to_ass(events, output_path, video_width=1920, video_height=1080):
    subs = SSAFile()
    # 设置一个滚动弹幕样式
    subs.styles['Danmaku'] = pysubs2.SSAStyle(
        fontname='Microsoft YaHei',
        fontsize=25,
        primarycolor=pysubs2.Color(255, 255, 255, 255),
        backcolor=pysubs2.Color(0, 0, 0, 0),
        outline=1,
        shadow=0,
        alignment=pysubs2.Alignment.BOTTOM_CENTER,  # 或其他你需要的对齐方式
        marginl=0,
        marginr=0,
        marginv=0,  # 替代原来的 margint 和 marginb
        # 注意：不再有 margint 和 marginb
    )
    for ev in events:
        start_ms = int(ev['start'] * 1000)
        # 滚动弹幕一般持续 4~6 秒，这里设 5 秒
        end_ms = start_ms + 5000
        # 使用 \move 让字幕从右向左滚动（经典滚动弹幕）
        # \move(1920, y, 0, y, 0, duration) 但 pysubs2 需要用 Drawing 或直接用 \move
        # 简便起见，不写复杂特效，仅做普通底部固定字幕（显示在底部中央）
        # 如果要滚动，需要自制绘制（略复杂）。先做固定样式。
        # 这里演示固定位置：底部居中
        event = SSAEvent(
            start=start_ms,
            end=end_ms,
            text=ev['text'],
            style='Danmaku'
        )
        # 如果需要滚动，可以设置 event.effect = 'Banner;10' 但效果一般
        # 更精确的方式：修改 event.text = '{\\move(1920, y, 0, y, 0, 5000)}' + text
        # 为了简单，保留纯文本，用户可自行调整
        subs.append(event)
    subs.save(output_path, encoding='utf-8')
    print(f"已生成 {len(events)} 条弹幕 -> {output_path}")