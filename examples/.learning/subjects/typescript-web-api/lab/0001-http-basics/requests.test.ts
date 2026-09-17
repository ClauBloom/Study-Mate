/* ═══════════════════════════════════════════════════════════════
   StudyMate · 实操 0001-http-basics 的自检（node --test，零依赖）
   ═══════════════════════════════════════════════════════════════
   跑法：cd lab/0001-http-basics && npm test
   - 教程部分：直接跑，现在的输出就是它们的结果（这就是"教程带结果"）。
   - 任务部分：此刻是字面量 test.skip，放着不跑，所以交付状态下整套是绿的；
     你实现完一个函数，就把对应的那一条 test.skip( 改成 test(，再跑一次。
   - 想一次全放出来：把四条都改完（四个任务都实现完了再改，否则会红）。
   ═══════════════════════════════════════════════════════════════ */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  narrative,
  explainStatus,
  quizOptions,
  requestLineText,
  headerValue,
  parseStatusLine,
  isSuccess,
  type HttpRequest,
} from './requests.ts';

/* 四个任务全实现完了就把下面的 test.skip( 都改成 test(，一次放开所有任务测试 */

/**
 * 课件里那次 curl -v 收到的请求，手工转成对象——
 * 让你看清"解析"这一步之前，原始信息本来长什么样。
 * 注意键全是小写：这是本文件的约定（HTTP 头名不区分大小写）。
 */
const sampleRequest: HttpRequest = {
  method: 'GET',
  path: '/menu',
  version: 'HTTP/1.1',
  headers: {
    host: 'example.com',
    accept: '*/*',
    'accept-encoding': 'gzip',
    'user-agent': 'curl/8.7.1',
  },
};

/* ── 教程：这几条现在就是绿的，看它们的输出 ───────────────────── */

test('教程：一次请求念成人话', () => {
  const sentence = narrative(sampleRequest);
  assert.equal(sentence, 'curl/8.7.1 向 example.com 发起 GET /menu，期望拿到 */*，用的是 HTTP/1.1');
});

test('教程：状态码讲清责任方', () => {
  assert.match(explainStatus(200), /正文/);
  assert.match(explainStatus(404), /不存在/);
  assert.match(explainStatus(500), /服务端日志/);
  assert.match(explainStatus(302), /责任方/);
});

test('教程：课件两道题的选项等长', () => {
  for (const opts of [quizOptions(0), quizOptions(1)]) {
    assert.equal(opts.length, 3);
    const lengths = opts.map((opt) => [...opt].length);
    assert.ok(Math.max(...lengths) - Math.min(...lengths) <= 4, `选项长度差过大：${opts.join(' / ')}`);
  }
});

/* ── 任务 1：拼出请求行（未实现，先跳过；实现完把 test.skip 改成 test）── */

test.skip('任务 1：拼出请求行', () => {
  assert.equal(requestLineText(sampleRequest), 'GET /menu HTTP/1.1');
  assert.equal(
    requestLineText({ method: 'POST', path: '/orders', version: 'HTTP/1.1', headers: {} }),
    'POST /orders HTTP/1.1',
  );
});

/* ── 任务 2：按名字取一个请求头（未实现，先跳过；实现完把 test.skip 改成 test）── */

test.skip('任务 2：按名字取请求头，大小写不敏感', () => {
  assert.equal(headerValue(sampleRequest, 'host'), 'example.com');
  assert.equal(headerValue(sampleRequest, 'Host'), 'example.com');
  assert.equal(headerValue(sampleRequest, 'authorization'), undefined);
});

/* ── 任务 3：解析状态行（未实现，先跳过；实现完把 test.skip 改成 test）── */

test.skip('任务 3：解析状态行', () => {
  assert.deepEqual(parseStatusLine('HTTP/1.1 200 OK'), { version: 'HTTP/1.1', status: 200, reason: 'OK' });
  assert.deepEqual(parseStatusLine('HTTP/1.1 404 Not Found'), {
    version: 'HTTP/1.1',
    status: 404,
    reason: 'Not Found',
  });
  assert.deepEqual(parseStatusLine('HTTP/1.1 500 Internal Server Error'), {
    version: 'HTTP/1.1',
    status: 500,
    reason: 'Internal Server Error',
  });
});

/* ── 任务 4：判断成功（未实现，先跳过；实现完把 test.skip 改成 test）── */

test.skip('任务 4：2xx 才算成功', () => {
  assert.equal(isSuccess(200), true);
  assert.equal(isSuccess(404), false);
  assert.equal(isSuccess(199), false);
  assert.equal(isSuccess(300), false);
});
