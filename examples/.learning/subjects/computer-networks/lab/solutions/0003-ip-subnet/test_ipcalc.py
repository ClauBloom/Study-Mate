#!/usr/bin/env python3
"""StudyMate · 实操 0003-ip-subnet 的自检（只用标准库：unittest + ipaddress）
═══════════════════════════════════════════════════════════════
跑法：cd lab/0003-ip-subnet && python3 -m unittest -v

- 教程部分（Tutorial）：现在就是绿的，跑一遍能看见这套断言长什么样。
- 任务部分（Task1 / Task2 / Task3）：交付状态下是红的——三个函数还没实现。
  一次只放一个：实现完一个函数，跑一次测试，看对应的那几条转绿。

为什么用 ipaddress 做对照：它是标准库，算网段的结果可信，
正好拿来当"答案册"。你的实现不许调用它——那等于把要练的算术外包出去；
它只出现在测试里，负责核对。
═══════════════════════════════════════════════════════════════
"""
import unittest
from ipaddress import ip_network

from ipcalc import int_to_ip, ip_to_int, mask_of, parse_cidr, same_subnet, split_subnet


class Tutorial(unittest.TestCase):
    """教程：这几个函数已经写好了，用它们看清 32 位整数与点分十进制的关系。"""

    def test_教程_地址与整数来回转(self):
        self.assertEqual(ip_to_int("192.168.1.70"), 3232235846)
        self.assertEqual(int_to_ip(3232235846), "192.168.1.70")
        self.assertEqual(int_to_ip(0), "0.0.0.0")
        self.assertEqual(int_to_ip(2 ** 32 - 1), "255.255.255.255")

    def test_教程_掩码写出来(self):
        self.assertEqual(mask_of(24), "255.255.255.0")
        self.assertEqual(mask_of(26), "255.255.255.192")
        self.assertEqual(mask_of(30), "255.255.255.252")
        self.assertEqual(mask_of(32), "255.255.255.255")

    def test_教程_每往右一段权重缩小256倍(self):
        # 第一段在高位：每往右一段，权重是前一段的 1/256
        self.assertEqual(ip_to_int("192.0.0.0") - ip_to_int("191.0.0.0"), 256 ** 3)
        self.assertEqual(ip_to_int("192.168.2.0") - ip_to_int("192.168.1.0"), 256)
        with self.assertRaises(ValueError):
            ip_to_int("192.168.1")
        with self.assertRaises(ValueError):
            ip_to_int("192.168.1.256")


class Task1ParseCidr(unittest.TestCase):
    """任务 1：parse_cidr —— 一个网段的网络地址、广播地址与可用范围。"""

    def test_任务1_斜杠24(self):
        self.assertEqual(
            parse_cidr("192.168.1.10/24"),
            {
                "network": "192.168.1.0",
                "broadcast": "192.168.1.255",
                "first": "192.168.1.1",
                "last": "192.168.1.254",
                "usable": 254,
            },
        )

    def test_任务1_斜杠30只有两个可用地址(self):
        self.assertEqual(
            parse_cidr("10.0.0.6/30"),
            {
                "network": "10.0.0.4",
                "broadcast": "10.0.0.7",
                "first": "10.0.0.5",
                "last": "10.0.0.6",
                "usable": 2,
            },
        )

    def test_任务1_斜杠31与斜杠32的边界(self):
        # 规则按 ipcalc.py 的说明：前缀 31 / 32 时可用主机数记 0，first 与 last 都取网络地址
        self.assertEqual(parse_cidr("10.0.0.0/31")["usable"], 0)
        self.assertEqual(parse_cidr("10.0.0.0/31")["network"], "10.0.0.0")

        only_host = parse_cidr("203.0.113.7/32")
        self.assertEqual(only_host["network"], "203.0.113.7")
        self.assertEqual(only_host["broadcast"], "203.0.113.7")
        self.assertEqual(only_host["first"], "203.0.113.7")
        self.assertEqual(only_host["last"], "203.0.113.7")
        self.assertEqual(only_host["usable"], 0)

    def test_任务1_与标准库逐条对照(self):
        for cidr in ("192.168.1.70/26", "172.16.8.200/26", "10.0.0.14/30", "8.8.8.8/32", "1.2.3.4/12"):
            with self.subTest(cidr=cidr):
                net = ip_network(cidr, strict=False)
                got = parse_cidr(cidr)
                self.assertEqual(got["network"], str(net.network_address))
                self.assertEqual(got["broadcast"], str(net.broadcast_address))
                self.assertEqual(got["usable"], max(0, net.num_addresses - 2))
                if got["usable"]:
                    self.assertEqual(got["first"], str(net.network_address + 1))
                    self.assertEqual(got["last"], str(net.broadcast_address - 1))

    def test_任务1_非法输入一律抛异常(self):
        for bad in ("192.168.1.0", "192.168.1.0/", "/24", "192.168.1.0/33", "192.168.1.0/-1",
                    "192.168.1.256/24", "192.168.1/24", "abc/24", "192.168.1.0/24/24"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_cidr(bad)


class Task2SameSubnet(unittest.TestCase):
    """任务 2：same_subnet —— 两个地址在给定前缀下是否同网段。"""

    def test_任务2_同网段与跨网段(self):
        self.assertTrue(same_subnet("192.168.1.10", "192.168.1.200", 24))
        self.assertFalse(same_subnet("192.168.1.10", "192.168.2.10", 24))

    def test_任务2_同一段地址被掩码切开(self):
        # 前 24 位完全相同，但 /26 把它们分在两个子网里
        self.assertTrue(same_subnet("192.168.1.70", "192.168.1.120", 26))
        self.assertFalse(same_subnet("192.168.1.70", "192.168.1.130", 26))

    def test_任务2_点对点链路的边界(self):
        self.assertTrue(same_subnet("10.0.0.5", "10.0.0.6", 30))
        self.assertFalse(same_subnet("10.0.0.3", "10.0.0.4", 30))

    def test_任务2_与逐位与运算的结果一致(self):
        def masked(ip, prefix):
            bits = ((1 << prefix) - 1) << (32 - prefix)
            return ip_to_int(ip) & bits

        for ip1, ip2, prefix in (("10.1.2.3", "10.1.9.9", 20), ("10.1.2.3", "10.1.9.9", 21),
                                 ("172.16.0.1", "172.31.255.254", 12), ("1.2.3.4", "9.9.9.9", 0)):
            with self.subTest(ip1=ip1, ip2=ip2, prefix=prefix):
                self.assertEqual(same_subnet(ip1, ip2, prefix), masked(ip1, prefix) == masked(ip2, prefix))

    def test_任务2_非法输入一律抛异常(self):
        with self.assertRaises(ValueError):
            same_subnet("192.168.1.10", "192.168.1.20", 33)
        with self.assertRaises(ValueError):
            same_subnet("192.168.1.10", "192.168.1.20", -1)
        with self.assertRaises(ValueError):
            same_subnet("192.168.1.10", "999.168.1.20", 24)
        with self.assertRaises(ValueError):
            same_subnet("192.168.1", "192.168.1.20", 24)


class Task3SplitSubnet(unittest.TestCase):
    """任务 3：split_subnet —— 把一个网段按更长的前缀等分。"""

    def test_任务3_斜杠24切成四个斜杠26(self):
        self.assertEqual(
            split_subnet("192.168.1.0/24", 26),
            ["192.168.1.0/26", "192.168.1.64/26", "192.168.1.128/26", "192.168.1.192/26"],
        )

    def test_任务3_切出64个斜杠30(self):
        got = split_subnet("10.0.0.0/24", 30)
        self.assertEqual(len(got), 64)
        self.assertEqual(got[0], "10.0.0.0/30")
        self.assertEqual(got[-1], "10.0.0.252/30")

    def test_任务3_子网都落在原网段里且互不重叠(self):
        for cidr, new_prefix in (("172.16.8.0/24", 28), ("192.168.0.0/22", 24)):
            with self.subTest(cidr=cidr, new_prefix=new_prefix):
                parent = ip_network(cidr, strict=False)
                children = [ip_network(item, strict=False) for item in split_subnet(cidr, new_prefix)]
                self.assertEqual(len(children), 2 ** (new_prefix - parent.prefixlen))
                self.assertEqual(sum(child.num_addresses for child in children), parent.num_addresses)
                for child in children:
                    self.assertTrue(child.subnet_of(parent))

    def test_任务3_非法前缀一律抛异常(self):
        with self.assertRaises(ValueError):
            split_subnet("192.168.1.0/24", 24)
        with self.assertRaises(ValueError):
            split_subnet("192.168.1.0/24", 23)
        with self.assertRaises(ValueError):
            split_subnet("192.168.1.0/24", 33)
        with self.assertRaises(ValueError):
            split_subnet("192.168.1.0/33", 26)


if __name__ == "__main__":
    unittest.main(verbosity=2)
