# 实操：0001-http-basics

对应节点 `http.basics`。
把一次 HTTP 请求与响应拆开看，并且**自己写代码把那段文本解析成对象**。
项目线索：订单 API 以后每一次排错都从这里开始，所以这段代码要亲手写一遍，不调用现成库。

## 载体

**源码 + 测试**：`0001-http-basics/` 里是一份 TypeScript 源码 `requests.ts` 加一份测试 `requests.test.ts`，
用 Node 自带的测试运行器跑，**零依赖、不联网、不装 npm 包**。

| 文件 | 是什么 |
| --- | --- |
| `0001-http-basics/requests.ts` | 你要读和写的源码：教程部分已完成，四个函数留白（标了 `▸ 你的任务`） |
| `0001-http-basics/requests.test.ts` | 自检脚本：教程断言 + 四个任务断言（任务部分此刻用 `test.skip` 放着） |
| `0001-http-basics/package.json` | 只有一个 `test` 脚本：`node --test` |
| `solutions/0001-http-basics/requests.ts` | 参考答案（做完再对照，别提前看） |

## 环境

- Node.js **≥ 22.18（或 ≥ 23.6）**（本机 v24.15）：Node 原生 type stripping 从这两个版本起默认开启，22.6–22.17 需要加 `--experimental-strip-types` 才能跑。这里靠 Node 原生跑 TypeScript，**不需要装 typescript、jest、ts-node**。
- 不需要数据库、不需要网络；`npm install` 也不用跑（没有依赖）。

## 怎么跑

```bash
# 先进入本文件所在的科目目录（.learning/subjects/typescript-web-api/），然后：
cd lab/0001-http-basics
npm test
```

交付状态下应该看到：**教程 3 条通过、任务 4 条跳过、`fail 0`**（绿色退出码）。
这就是"教程带结果"：你还没动手，先看见这套环境是活的、断言长什么样。

## 教程部分（已完成，跑一遍就能看见结果）

- `narrative(request)`：把一次请求念成一句人话，看清"方法/路径 + Host + Accept 就够判断谁在要什么"。
- `explainStatus(status)`：把 `200 / 404 / 500` 翻译成"接下来该干什么"，演示状态码是**分类**不是编号。
- `quizOptions(index)`：课件两道题的选项，用来验证"选项等长"（长度差 ≤ 4，不泄露答案）。

## ▸ 你的任务

一次只做一个：实现函数 → 回 `requests.test.ts` 把那一条 `test.skip(` 改成 `test(` → 再 `npm test`。
四条都改完（四个任务都实现完）后 `npm test` 应全绿。

| # | 函数 | 做什么 | 算过的标准（`npm test` 里对应的断言转绿） |
| --- | --- | --- | --- |
| 1 | `requestLineText(request)` | 拼出请求行原文，如 `GET /menu HTTP/1.1` | "任务 1"2 条断言 |
| 2 | `headerValue(request, name)` | 按名字取请求头；**头名不区分大小写**，找不到返回 `undefined` | "任务 2"3 条断言 |
| 3 | `parseStatusLine(line)` | 把 `HTTP/1.1 404 Not Found` 拆成 `{version, status, reason}`，`status` 是数字 | "任务 3"3 条断言 |
| 4 | `isSuccess(status)` | 2xx 才算成功；返回布尔值 | "任务 4"4 条断言（含 199/300 两个边界） |

卡住了按这个顺序来：**先读报错原文** → 再看函数上方注释里的"边界/提示" → 还不行就把报错原样贴回会话。
我不直接给答案，会先问你觉得哪一行不对。

## 答案

- `solutions/0001-http-basics/requests.ts`：四个任务的完整实现（相对于本文件所在目录）。
- 对照方式：把那份整个覆盖到 `0001-http-basics/requests.ts`，再把四条 `test.skip(` 改成 `test(`，`npm test` 应全绿。
  可用的命令：

  ```bash
  cp ../solutions/0001-http-basics/requests.ts requests.ts && npm test   # 在 0001-http-basics/ 下运行；先确认自己的版本已经提交/备份
  ```

## 做完之后

回课件答那两道题，然后接着上 `http.routing`（路由）——下一课就用你今天解析出来的方法和路径，
决定"请求该交给哪个处理函数"。
