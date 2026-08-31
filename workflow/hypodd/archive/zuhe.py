from pathlib import Path
from datetime import datetime, timedelta

# 你的目录
folder = Path(r"./")

# 输出文件
out_file = folder / "ALL.txt"

events = []

def parse_event_time(parts):
    """
    按你的文件格式解析时间：
    第11~16列分别为 year, month, day, hour, minute, second
    Python索引对应 parts[10] ~ parts[15]
    """
    year = int(parts[10])
    month = int(parts[11])
    day = int(parts[12])
    hour = int(parts[13])
    minute = int(parts[14])
    second_float = float(parts[15])

    sec_int = int(second_float)
    micro = int(round((second_float - sec_int) * 1_000_000))

    # 处理秒可能为 60.00 之类的异常情况
    base = datetime(year, month, day, hour, minute, 0)
    dt = base + timedelta(seconds=second_float)

    return dt

for txt_file in sorted(folder.glob("*.txt")):
    # 避免把输出文件本身再次读进去
    if txt_file.name == out_file.name:
        continue

    with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) < 16:
                print(f"跳过格式异常行: {txt_file.name} -> {line}")
                continue

            try:
                dt = parse_event_time(parts)
                events.append((dt, line))
            except Exception as e:
                print(f"时间解析失败: {txt_file.name} -> {line}")
                print(f"原因: {e}")

# 按时间排序
events.sort(key=lambda x: x[0])

# 写出
with open(out_file, "w", encoding="utf-8") as f:
    for _, line in events:
        f.write(line + "\n")

print(f"合并完成，共 {len(events)} 个事件")
print(f"输出文件: {out_file}")