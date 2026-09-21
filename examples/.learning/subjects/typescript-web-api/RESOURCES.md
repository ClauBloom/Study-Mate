# TypeScript Web API Resources

> 定位：**延伸阅读 + 易变内容的核对来源**，不是"知识来源清单"。
> 稳定知识节点可以不在这里留条目；易变/版本相关内容必须在这里有核对过的官方来源。

## Knowledge

- [MDN: HTTP 概览](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Overview)
  一行说明：请求／响应报文与状态码的权威解释；用于核对状态码语义（301/302/304 的区别容易记混）。
- [Node.js 官方文档](https://nodejs.org/docs/latest/api/)
  一行说明：`http` / `fs` / `crypto` 等核心模块的现行 API；用于核对**当前 LTS 版本**的行为（模块 API 在小版本间会变）。
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/current/)
  一行说明：SQL 语法与事务隔离级别；用于核对「版本差异」——`ON CONFLICT`、`GENERATED` 列都是较新版本才有的。

## Wisdom (Communities)

- [Node.js 官方论坛](https://github.com/nodejs/help)
  一行说明：问"这段代码为什么这样报错"这类实践问题；官方仓库的 Discussions 里能看到维护者的解释。
- [Stack Overflow: node.js 标签](https://stackoverflow.com/questions/tagged/node.js)
  一行说明：查具体错误信息。回答质量参差，先看有没有官方文档引用。

## Gaps

- 缺一份"HTTP 缓存（Cache-Control / ETag）"的中文权威资料，目前只有 MDN 英文页。
