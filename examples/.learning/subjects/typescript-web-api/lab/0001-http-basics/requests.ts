/* ═══════════════════════════════════════════════════════════════
   StudyMate · 实操 0001-http-basics（与课件 0001 对齐）
   节点：http.basics　载体：源码 + 测试（零依赖，Node 原生跑 TypeScript）
   ═══════════════════════════════════════════════════════════════
   怎么用：
   1. 先跑一遍看结果   →  cd lab/0001-http-basics && npm test
      教程部分（narrative / explainStatus / quizOptions）是全的，那几条断言直接通过；
      任务部分（带 ▸ 你的任务 标记的四个函数）此刻还是空的，测试用 test.skip 放着不跑。
   2. 逐个实现四个任务函数：把下面的 throw 换成实现。
   3. 回 requests.test.ts，把对应的 test.skip( 改成 test(（一次改一个，改完就跑一次）。
   4. 卡住了别硬扛：把报错原文贴回会话，我们从错误信息开始看。
      做完想对照 → ../solutions/0001-http-basics/requests.ts（别提前看）。
   ═══════════════════════════════════════════════════════════════ */

/** HTTP 请求里我们关心的那几样东西（文本已经替你先解析成对象了）。 */
export interface HttpRequest {
  /** 请求行里的方法，如 "GET" */
  method: string;
  /** 请求行里的路径，如 "/menu" */
  path: string;
  /** 请求行里的协议版本，如 "HTTP/1.1" */
  version: string;
  /** 全部请求头，按名字小写存放（HTTP 头名不区分大小写） */
  headers: Record<string, string>;
}

/** HTTP 响应里我们关心的那几样东西。 */
export interface HttpResponse {
  /** 协议版本，如 "HTTP/1.1" */
  version: string;
  /** 状态码，如 200 */
  status: number;
  /** 状态码后面那句人话，如 "OK" */
  reason: string;
  /** 响应头 */
  headers: Record<string, string>;
  /** 响应正文（可能为空串） */
  body: string;
}

/* ───────────────────────────────────────────────────────────────
   一、教程：我带你做一遍（这部分写全了，跑测试能看见结果）
   ─────────────────────────────────────────────────────────────── */

/** 请求头名不比大小写，统一转小写后比较。 */
function normalizeName(name: string): string {
  return name.trim().toLowerCase();
}

/**
 * 把一个请求对象念成一句人话。
 *
 * 手工拆文本这件事到底在做什么？只要拿到三样东西——方法/路径、目标主机、
 * 客户端自称是谁——就能回答"谁、向哪儿、要什么"。这里刻意不依赖任何框架。
 */
export function narrative(request: HttpRequest): string {
  const host = request.headers['host'] ?? '（没有 Host）';
  const accept = request.headers['accept'] ?? '（没说自己想要什么格式）';
  const agent = request.headers['user-agent'] ?? '（没说是什么客户端）';
  return `${agent} 向 ${host} 发起 ${request.method} ${request.path}，期望拿到 ${accept}，用的是 ${request.version}`;
}

/**
 * 把状态码翻译成"接下来该干什么"。
 *
 * 状态码不是要背的数字表：首位定责任方（4xx 你错了 / 5xx 我错了），
 * 后两位才是具体原因。这张小表就是 404 与 500 的分界线。
 */
export function explainStatus(status: number): string {
  if (status === 200) return '成功：正文就是你要的东西';
  if (status === 404) return '东西不存在：检查路径拼写与资源 id';
  if (status === 500) return '服务端出错：去看服务端日志，不是改请求';
  return '未收录的状态码：先看首位数字判断责任方';
}

/**
 * 课件 0001 那两道题的选项，原样放在这里。
 *
 * 用来演示出题规范：三条选项长度差 0（最长 5 字符、最短 4 字符），
 * 长度不泄露答案——只能靠懂内容来选。
 */
export function quizOptions(index: number): string[] {
  const quiz: string[][] = [
    ['东西不存在', '服务器坏了', '网络太慢了'],
    ['读取资源', '提交数据', '删除资源'],
  ];
  return quiz[index] ?? [];
}

/* ───────────────────────────────────────────────────────────────
   二、任务：轮到你了（实现完把请求测试里的 .skip 去掉）
   ─────────────────────────────────────────────────────────────── */

/**
 * ▸ 你的任务 1：拼出请求行。
 *
 * 做什么：返回请求行的原文，形如 "GET /menu HTTP/1.1"
 *         —— 方法、路径、协议版本三部分，用一个空格隔开。
 * 怎么算过：npm test 里"任务 1"的两条断言转绿。
 */
export function requestLineText(request: HttpRequest): string {
  throw new Error('▸ 任务 1 未实现：requestLineText');
}

/**
 * ▸ 你的任务 2：按名字取一个请求头。
 *
 * 做什么：在 request.headers 里找这个头，返回值；找不到返回 undefined。
 *         头名不区分大小写——找 'Host' 要能取到存成 'host' 的那条，
 *         也就是说传进来的名字要先规范化再比。
 * 怎么算过：npm test 里"任务 2"的三条断言转绿。
 * 提示：先确认 request.headers 的键是什么形态，再决定要不要处理入参。
 */
export function headerValue(request: HttpRequest, name: string): string | undefined {
  throw new Error('▸ 任务 2 未实现：headerValue');
}

/**
 * ▸ 你的任务 3：解析状态行。
 *
 * 做什么：把 "HTTP/1.1 404 Not Found" 拆成 { version, status, reason }：
 *         version = "HTTP/1.1"，status = 404（是 number，不是字符串），
 *         reason = "Not Found"。
 * 怎么算过：npm test 里"任务 3"的三条断言转绿。
 * 边界：reason 里可能有空格（"Not Found"、"Internal Server Error"），
 *       但状态行只切成三段——想清楚用什么切、切几刀。
 */
export function parseStatusLine(line: string): { version: string; status: number; reason: string } {
  throw new Error('▸ 任务 3 未实现：parseStatusLine');
}

/**
 * ▸ 你的任务 4：判断"这次请求算不算成功"。
 *
 * 做什么：状态码在 200-299 之间时返回 true，否则 false；
 *         返回类型写成类型守卫（把 boolean 换成 status is 200 那一类写法），
 *         让调用方在 if 里能收窄类型。
 * 怎么算过：npm test 里"任务 4"的四条断言转绿
 *           （有一条会传 199 和 300 这两个边界值）。
 */
export function isSuccess(status: number): boolean {
  throw new Error('▸ 任务 4 未实现：isSuccess');
}
