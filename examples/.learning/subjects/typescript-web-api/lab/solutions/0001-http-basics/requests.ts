/* ═══════════════════════════════════════════════════════════════
   StudyMate · 实操 0001-http-basics 参考答案（做完再看）
   ═══════════════════════════════════════════════════════════════
   用法：把这份整个覆盖到 lab/0001-http-basics/requests.ts，再回
   requests.test.ts 把四条 test.skip( 改成 test(，
   然后 npm test——应该全绿。
   这份文件与 requests.ts 的接口完全一致，只是把四个 ▸ 你的任务 实现了。
   ═══════════════════════════════════════════════════════════════ */

/** HTTP 请求里我们关心的那几样东西。 */
export interface HttpRequest {
  method: string;
  path: string;
  version: string;
  headers: Record<string, string>;
}

/** HTTP 响应里我们关心的那几样东西。 */
export interface HttpResponse {
  version: string;
  status: number;
  reason: string;
  headers: Record<string, string>;
  body: string;
}

/* ── 教程部分（与 requests.ts 相同）────────────────────────────── */

/** 请求头名不比大小写，统一转小写后比较。 */
function normalizeName(name: string): string {
  return name.trim().toLowerCase();
}

export function narrative(request: HttpRequest): string {
  const host = request.headers['host'] ?? '（没有 Host）';
  const accept = request.headers['accept'] ?? '（没说自己想要什么格式）';
  const agent = request.headers['user-agent'] ?? '（没说是什么客户端）';
  return `${agent} 向 ${host} 发起 ${request.method} ${request.path}，期望拿到 ${accept}，用的是 ${request.version}`;
}

export function explainStatus(status: number): string {
  if (status === 200) return '成功：正文就是你要的东西';
  if (status === 404) return '东西不存在：检查路径拼写与资源 id';
  if (status === 500) return '服务端出错：去看服务端日志，不是改请求';
  return '未收录的状态码：先看首位数字判断责任方';
}

export function quizOptions(index: number): string[] {
  const quiz: string[][] = [
    ['东西不存在', '服务器坏了', '网络太慢了'],
    ['读取资源', '提交数据', '删除资源'],
  ];
  return quiz[index] ?? [];
}

/* ── 任务 1：拼出请求行 ──────────────────────────────────────── */

export function requestLineText(request: HttpRequest): string {
  return `${request.method} ${request.path} ${request.version}`;
}

/* ── 任务 2：按名字取一个请求头 ──────────────────────────────── */

export function headerValue(request: HttpRequest, name: string): string | undefined {
  return request.headers[normalizeName(name)];
}

/* ── 任务 3：解析状态行 ─────────────────────────────────────── */

export function parseStatusLine(line: string): { version: string; status: number; reason: string } {
  // 只切三刀中的前两刀：reason 里可能带空格（"Not Found"），所以第三段要原样留下。
  const [version = '', rawStatus = '0', ...rest] = line.trim().split(' ');
  return { version, status: Number(rawStatus), reason: rest.join(' ') };
}

/* ── 任务 4：判断成功 ────────────────────────────────────────── */

export function isSuccess(status: number): boolean {
  // 接受整个 2xx 区间，不能把调用方的值收窄成 200 / 201 / 204。
  return status >= 200 && status < 300;
}
