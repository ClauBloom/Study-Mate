# 计算机网络 Resources

> 定位：**延伸阅读 + 易变内容的核对来源**，不是"知识来源清单"（模型已掌握稳定基础知识）。
> 稳定知识节点可以不在这里留条目；易变/版本相关内容必须在这里有核对过的官方来源。

## Knowledge

- [RFC 9293 · Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293.html)
  一行说明：TCP 的现行标准全文（2022 年取代 RFC 793）；核对三次握手、确认与重传、窗口字段的原文定义时用它，不要背二手教材的说法。
- [RFC 791 · Internet Protocol](https://www.rfc-editor.org/rfc/rfc791.html)
  一行说明：IPv4 首部逐字段的原始定义；核对首部长度、TTL、分片字段的语义时用它。
- [RFC 1918 · 私有网络地址分配](https://www.rfc-editor.org/rfc/rfc1918.html)
  一行说明：`10/8`、`172.16/12`、`192.168/16` 三段私有地址的出处；核对"这个地址能不能出现在公网上"。
- [RFC 826 · ARP](https://www.rfc-editor.org/rfc/rfc826.html)
  一行说明：由 IP 地址找 MAC 地址的原始规范；核对 ARP 请求为什么用广播、应答为什么用单播。
- [RFC 894 · IP over Ethernet](https://www.rfc-editor.org/rfc/rfc894.html)
  一行说明：IP 包怎么装进以太网帧（类型字段、最小帧长）；核对帧格式与 MTU 的来源。
- [MDN · HTTP 概览](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Overview)
  一行说明：应用层那一端的权威中文说明；核对请求/响应报文与状态码的现行语义。
- [Python 官方文档 · ipaddress](https://docs.python.org/zh-cn/3/library/ipaddress.html)
  一行说明：标准库里的地址与网段对象；lab 用它当算网段的对照答案，也是以后写脚本查地址的现成工具。
- [Python 官方文档 · socket](https://docs.python.org/zh-cn/3/library/socket.html)
  一行说明：实验课写 TCP 回显客户端要用的接口；核对 `connect`/`sendall`/`recv` 与超时参数的现行行为。
- [Wireshark 用户指南](https://www.wireshark.org/docs/wsug_html_chunked/)
  一行说明：抓包工具的官方手册（含显示过滤器语法）；核对某个字段在哪一层、过滤器怎么写。
- [tcpdump 手册页](https://www.tcpdump.org/manpages/tcpdump.1.html)
  一行说明：命令行抓包的官方文档；核对抓包过滤表达式与 `-i`、`-w` 这类参数。
- [iproute2 · ip(8) 手册](https://man7.org/linux/man-pages/man8/ip.8.html)
  一行说明：`ip addr` / `ip route` / `ip neigh` 的官方说明；核对本机地址、路由表与 ARP 缓存的读法（发行版之间输出略有差异）。

## Wisdom (Communities)

- [Network Engineering Stack Exchange](https://networkengineering.stackexchange.com/)
  一行说明：问"为什么这里要这样设计"这类实践问题；回答常带抓包与 RFC 引用，先看有没有引用原文。
- [Wireshark 问答（Ask）](https://ask.wireshark.org/)
  一行说明：抓包文件读不懂时问；贴包比贴截图有用，官方开发者会回。

## Gaps

- 缺一份把「家用路由器 + 运营商 + 云厂商」三段链路串起来讲的中文资料；目前只有各厂商自己的帮助页，讲法不一致。
- 缺一套中文的抓包练习包（pcap 样本）：本课先用自己机器上抓到的真实流量，样本不通用。
