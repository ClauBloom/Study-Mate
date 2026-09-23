#!/usr/bin/env python3
"""StudyMate · 实操 0003-ip-subnet（与课件 0003 对齐）
节点：net.ip　载体：源码 + 测试（只用标准库：unittest + ipaddress）
═══════════════════════════════════════════════════════════════
怎么用：
1. 先跑一遍看结果   →  cd lab/0003-ip-subnet && python3 -m unittest -v
   教程部分（ip_to_int / int_to_ip / mask_of）是全的，那几条断言直接通过；
   任务部分（带 ▸ 你的任务 标记的三个函数）此刻抛 NotImplementedError，测试是红的。
2. 一次只做一个任务：把函数体里的 TODO 换成实现，再跑一次测试。
3. 卡住了别硬扛：先读测试里的断言与报错原文，把报错贴回会话再问。
   做完想对照 → ../solutions/0003-ip-subnet/（别提前看）。
═══════════════════════════════════════════════════════════════

约定：本文件里「地址」既可能指字符串（"192.168.1.70"），也可能指 32 位整数。
两个教程函数负责这两种写法之间的转换，任务函数可以放心用它们。
"""


# ─────────────────────────────────────────────────────────────
# 一、教程：我带你做一遍（这部分写全了，跑测试能看见结果）
# ─────────────────────────────────────────────────────────────

def ip_to_int(text):
    """把点分十进制的 IPv4 地址转成 32 位整数。

    "192.168.1.70" → 3232235846。四段各占 8 位，第一段是最高位那一段，
    所以每读一段就把已有结果乘 256 再加上这一段——三十多年前的路由器就是这么做的。
    不是四段、某一段不是数字、某一段超出 0~255 时抛 ValueError。
    """
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
    """把 32 位整数转回点分十进制的 IPv4 地址：3232235846 → "192.168.1.70"。

    每次取最低 8 位（与 255 做与运算）就是最后一段，然后右移 8 位继续取，
    取四次正好取完。超出 0 ~ 2^32-1 时抛 ValueError。
    """
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < 2 ** 32:
        raise ValueError(f"要转换的整数必须落在 0 ~ 2^32-1：{value!r}")
    parts = []
    for _ in range(4):
        parts.append(str(value & 255))
        value >>= 8
    return ".".join(reversed(parts))


def mask_of(prefix):
    """把前缀长度写成点分十进制的掩码：26 → "255.255.255.192"。

    做法：先造出 prefix 个 1（即 2^prefix - 1），再左移到最高位那一侧。
    左移 32 - prefix 位之后，低位的 0 就是主机位。
    """
    if not isinstance(prefix, int) or isinstance(prefix, bool) or not 0 <= prefix <= 32:
        raise ValueError(f"前缀长度必须在 0 ~ 32 之间：{prefix!r}")
    return int_to_ip(((1 << prefix) - 1) << (32 - prefix))


# ─────────────────────────────────────────────────────────────
# 二、任务：轮到你了（实现完再跑测试）
# ─────────────────────────────────────────────────────────────

def parse_cidr(s):
    """▸ 你的任务 1：把一个 CIDR 写法拆成一个网段的四样事实。

    输入形如 "192.168.1.70/26"（地址 + 斜杠 + 前缀长度）。

    返回 dict，键固定为这五个：
        "network"    网络地址（主机位全 0），字符串
        "broadcast"  广播地址（主机位全 1），字符串
        "first"      第一个可用主机地址，字符串
        "last"       最后一个可用主机地址，字符串
        "usable"     可用主机数，整数

    规则：
        · 前缀 0 ~ 30：usable = 2 ** (32 - prefix) - 2，
          first = network + 1，last = broadcast - 1
        · 前缀 31 或 32：usable = 0，first 与 last 都取网络地址
        · 地址不合法（不是四段、某段超出 0~255）、没有斜杠、
          前缀不是 0~32 的整数：一律抛 ValueError

    算过的标准：python3 -m unittest -v 里「任务 1」的几条断言转绿。
    提示：先找出块大小（主机位的容量），网络地址是块大小的整数倍；
          广播地址 = 网络地址 + 块大小 - 1。
    """
    # TODO: 在这里实现。先用 split("/") 拆开，再算出块大小与两个边界地址。
    raise NotImplementedError("▸ 任务 1 未实现：parse_cidr")


def same_subnet(ip1, ip2, prefix):
    """▸ 你的任务 2：判断两个地址在前缀 prefix 下是否属于同一网段。

    返回 True / False。地址不合法或前缀不在 0 ~ 32 时抛 ValueError。
    例：same_subnet("192.168.1.70", "192.168.1.120", 26) → True
        same_subnet("192.168.1.70", "192.168.1.130", 26) → False

    算过的标准：python3 -m unittest -v 里「任务 2」的几条断言转绿。
    提示：两个地址各自与掩码做与运算，比较结果是否相等；
          右移 32 - prefix 位也能把主机位丢掉，等价于与掩码做与运算。
    """
    # TODO: 在这里实现。注意前缀要先检查范围，再拿去移位。
    raise NotImplementedError("▸ 任务 2 未实现：same_subnet")


def split_subnet(cidr, new_prefix):
    """▸ 你的任务 3：把一个网段按更长的前缀等分成若干子网。

    返回字符串列表，每项形如 "192.168.1.64/26"（网络地址 + 新前缀），按地址从小到大。
    例：split_subnet("192.168.1.0/24", 26)
        → ["192.168.1.0/26", "192.168.1.64/26", "192.168.1.128/26", "192.168.1.192/26"]

    规则：
        · new_prefix 必须大于原前缀且不超过 32，否则抛 ValueError
        · 原 CIDR 不合法时抛 ValueError（可以复用任务 1 里拆地址的那套检查）

    算过的标准：python3 -m unittest -v 里「任务 3」的几条断言转绿。
    提示：子网个数是 2 ** (new_prefix - 原前缀)，相邻两个子网的网络地址相差
          2 ** (32 - new_prefix)——先把这两个数算出来，再用循环拼。
    """
    # TODO: 在这里实现。子网个数 = 2 ** (new_prefix - 原前缀)。
    raise NotImplementedError("▸ 任务 3 未实现：split_subnet")
