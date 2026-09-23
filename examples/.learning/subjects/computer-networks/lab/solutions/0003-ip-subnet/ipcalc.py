#!/usr/bin/env python3
"""StudyMate · 实操 0003-ip-subnet —— 参考解（做完自己的版本再对照）
节点：net.ip　载体：源码 + 测试（只用标准库：unittest + ipaddress）
═══════════════════════════════════════════════════════════════
怎么用这份参考解：
  cp ../solutions/0003-ip-subnet/ipcalc.py ipcalc.py && python3 -m unittest -v
（在 0003-ip-subnet/ 里执行；先备份你自己写的那份，或者先做完再看。）

本目录里也放了一份 test_ipcalc.py 的副本，所以可以直接在这里跑：
  cd ../solutions/0003-ip-subnet && python3 -m unittest -v     # 应全绿

三个任务函数的实现思路：
  · 块大小 1 << (32 - prefix)：主机位的容量，网络地址一定是它的整数倍
  · network   = address & ~(block - 1)   把主机位清零
  · broadcast = network | (block - 1)    把主机位全置 1
  · 同网段的判断就是"两个地址右移掉主机位之后相等"
  · 等分网段：子网个数 2 ** (new_prefix - prefix)，相邻子网网络地址相差 1 << (32 - new_prefix)
═══════════════════════════════════════════════════════════════
"""


# ─────────────────────────────────────────────────────────────
# 一、教程部分（与任务目录里的版本一致）
# ─────────────────────────────────────────────────────────────

def ip_to_int(text):
    """把点分十进制的 IPv4 地址转成 32 位整数："192.168.1.70" → 3232235846。"""
    parts = text.split(".")
    if len(parts) != 4:
        raise ValueError(f"IPv4 地址要写成四段（a.b.c.d）：{text!r}")
    value = 0
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"这一段不是十进制数字：{part!r}（地址 {text!r}）")
        number = int(part)
        if not 0 <= number <= 255:
            raise ValueError(f"这一段超出 0~255：{part!r}（地址 {text!r}）")
        value = value * 256 + number
    return value


def int_to_ip(value):
    """把 32 位整数转回点分十进制的 IPv4 地址：3232235846 → "192.168.1.70"。"""
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < 2 ** 32:
        raise ValueError(f"要转换的整数必须落在 0 ~ 2^32-1：{value!r}")
    parts = []
    for _ in range(4):
        parts.append(str(value & 255))
        value >>= 8
    return ".".join(reversed(parts))


def mask_of(prefix):
    """把前缀长度写成点分十进制的掩码：26 → "255.255.255.192"。"""
    if not isinstance(prefix, int) or isinstance(prefix, bool) or not 0 <= prefix <= 32:
        raise ValueError(f"前缀长度必须在 0 ~ 32 之间：{prefix!r}")
    return int_to_ip(((1 << prefix) - 1) << (32 - prefix))


# ─────────────────────────────────────────────────────────────
# 二、任务部分（参考实现）
# ─────────────────────────────────────────────────────────────

def _split_cidr(text):
    """内部工具：把 "192.168.1.70/26" 拆成 (地址整数, 前缀长度)，不合法就抛 ValueError。

    只允许恰好一个斜杠；前缀必须写成 0~32 的十进制整数（"-1"、"3.5"、"abc" 都不行）。
    """
    if not isinstance(text, str) or text.count("/") != 1:
        raise ValueError(f"CIDR 要写成 地址/前缀 的形式：{text!r}")
    address_text, prefix_text = text.split("/")
    prefix_text = prefix_text.strip()
    if not prefix_text.isdigit():
        raise ValueError(f"前缀长度要写成 0~32 的整数：{text!r}")
    prefix = int(prefix_text)
    if not 0 <= prefix <= 32:
        raise ValueError(f"前缀长度要在 0~32 之间：{text!r}")
    return ip_to_int(address_text), prefix


def parse_cidr(s):
    """把一个 CIDR 写法拆成一个网段的网络地址、广播地址与可用范围。"""
    address, prefix = _split_cidr(s)
    block = 1 << (32 - prefix)              # 主机位的容量，也就是块大小
    network = address & ~(block - 1)        # 主机位清零
    broadcast = network | (block - 1)       # 主机位全 1

    if prefix <= 30:
        first, last, usable = network + 1, broadcast - 1, block - 2
    else:
        # /31 与 /32：主机位不足两位，没有"去掉首尾还能用"的地址
        first = last = network
        usable = 0

    return {
        "network": int_to_ip(network),
        "broadcast": int_to_ip(broadcast),
        "first": int_to_ip(first),
        "last": int_to_ip(last),
        "usable": usable,
    }


def same_subnet(ip1, ip2, prefix):
    """两个地址在前缀 prefix 下是否属于同一网段。"""
    if not isinstance(prefix, int) or isinstance(prefix, bool) or not 0 <= prefix <= 32:
        raise ValueError(f"前缀长度要在 0~32 之间：{prefix!r}")
    shift = 32 - prefix
    # 右移掉主机位再比：等价于各自与掩码做与运算
    return (ip_to_int(ip1) >> shift) == (ip_to_int(ip2) >> shift)


def split_subnet(cidr, new_prefix):
    """把一个网段按更长的前缀等分成若干子网，返回 "网络地址/新前缀" 的列表。"""
    if not isinstance(new_prefix, int) or isinstance(new_prefix, bool):
        raise ValueError(f"新前缀要写成整数：{new_prefix!r}")
    address, prefix = _split_cidr(cidr)
    if not prefix < new_prefix <= 32:
        raise ValueError(f"新前缀要大于原前缀 {prefix} 且不超过 32：{new_prefix!r}")

    block = 1 << (32 - prefix)
    network = address & ~(block - 1)
    step = 1 << (32 - new_prefix)           # 相邻子网的网络地址之差
    count = 1 << (new_prefix - prefix)      # 子网个数
    return [f"{int_to_ip(network + index * step)}/{new_prefix}" for index in range(count)]
