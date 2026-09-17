const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const ASSET = path.join(__dirname, '..', '..', 'templates', 'assets', 'quiz.js');

function makeEl(tag) {
  const el = {
    tagName: tag, className: '', textContent: '', hidden: false, type: '', _data: null,
    children: [], _handlers: {},
    classList: {
      _set: new Set(),
      toggle(name, force) {
        const on = force === undefined ? !this._set.has(name) : !!force;
        if (on) this._set.add(name); else this._set.delete(name);
      },
      contains(n) { return this._set.has(n); },
      add(n) { this._set.add(n); },
      remove(n) { this._set.delete(n); },
    },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(t, fn) { (this._handlers[t] = this._handlers[t] || []).push(fn); },
    click() { (this._handlers.click || []).forEach(fn => fn()); },
    getAttribute(n) { return n === 'data-quiz' ? this._data : null; },
  };
  return el;
}

function makeBlock(items) {
  const b = makeEl('div');
  b._data = JSON.stringify(items);
  return b;
}

function run(blocks) {
  const sandbox = {
    console,
    window: {},
    document: {
      readyState: 'complete',
      addEventListener() {},
      querySelectorAll() { return blocks; },
      createElement: makeEl,
    },
  };
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(ASSET, 'utf8'), sandbox);
}

// 在渲染树里找类名匹配的元素（深度优先，返回全部）
function findAll(root, cls, out = []) {
  if ((root.className || '').split(/\s+/).includes(cls)) out.push(root);
  (root.children || []).forEach(c => findAll(c, cls, out));
  return out;
}

let failures = 0;
function check(label, ok, extra = '') {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${extra ? '  — ' + extra : ''}`);
  if (!ok) failures++;
}

// ── 场景一：1 选择 + 1 开放 ─────────────────────────────────────
const b1 = makeBlock([
  { q: '哪层要真跑代码？', opts: ['L1 理解', 'L4 应用', 'L2 改造'], ans: 1, why: 'L4 要求代码跑通加测试通过。' },
  { q: '为什么查询串不参与路由？', answer: '它只说明这次想怎么看。', criteria: '说出与资源身份的区别即算过' },
]);
run([b1]);

const qs = findAll(b1, 'quiz__q');
check('两道题都渲染出题面', qs.length === 2, `实际 ${qs.length}`);
check('题面带序号', qs[0].textContent.startsWith('1. ') && qs[1].textContent.startsWith('2. '), qs.map(q => q.textContent).join(' | '));

const optsWrap = findAll(b1, 'quiz__opts')[0];
check('选择题渲染 3 个选项', optsWrap && optsWrap.children.length === 3);

const feedback = findAll(b1, 'feedback')[0];
check('选择题反馈初始隐藏', feedback && feedback.hidden === true);

optsWrap.children[1].click();
check('点对选项 → 反馈可见且带 why', feedback.hidden === false && feedback.textContent.includes('✓ 对') && feedback.textContent.includes('L4 要求'));
check('点对选项 → 标 is-correct', optsWrap.children[1].classList.contains('is-correct'));
check('点对选项 → 错误选项不标红', !optsWrap.children[0].classList.contains('is-wrong'));

const reveal = findAll(b1, 'quiz__reveal')[0];
const answerBox = findAll(b1, 'quiz__answer')[0];
check('开放题有展开按钮', !!reveal && reveal.textContent === '想好了，看参考答案');
check('答案块初始收起', answerBox && answerBox.hidden === true);
reveal.click();
check('点开 → 显示参考答案与算过标准', answerBox.hidden === false &&
  answerBox.children.some(c => c.textContent === '参考答案') &&
  answerBox.children.some(c => c.textContent === '它只说明这次想怎么看。') &&
  answerBox.children.some(c => c.textContent === '算过标准') &&
  answerBox.children.some(c => c.textContent === '说出与资源身份的区别即算过'));
check('点开 → 按钮变成收起', reveal.textContent === '收起，再自己答一遍');
reveal.click();
check('再点 → 收起且按钮复原', answerBox.hidden === true && reveal.textContent === '想好了，看参考答案');
check('只有 1 道选择题时不显示计分（choiceCount=1）', findAll(b1, 'quiz__score').length === 0);

// ── 场景二：2 选择题 → 计分 ─────────────────────────────────────
const b2 = makeBlock([
  { q: 'A？', opts: ['对', '错'], ans: 0, why: '因为 A。' },
  { q: 'B？', opts: ['对', '错'], ans: 0, why: '因为 B。' },
]);
run([b2]);
const score = findAll(b2, 'quiz__score')[0];
check('两道选择题 → 有计分元素且初始隐藏', !!score && score.hidden === true);
const optWraps = findAll(b2, 'quiz__opts');
optWraps[0].children[0].click();   // 对
optWraps[1].children[1].click();   // 错
check('两题答完 → 计分显示 答对 1 / 2', score.hidden === false && score.textContent === '本题组：答对 1 / 2', score.textContent);

// ── 场景三：全开放题不出现计分 ──────────────────────────────────
const b3 = makeBlock([{ q: '开放题', answer: '答', criteria: '标准' }]);
run([b3]);
check('全开放题 → 不出现计分元素', findAll(b3, 'quiz__score').length === 0);

// ── 场景四：坏数据兜底 ──────────────────────────────────────────
const b4 = makeBlock([{ q: '既不是选择题也不是开放题' }]);
run([b4]);
const hint = findAll(b4, 'feedback')[0];
check('坏数据 → 显示数据不完整提示', !!hint && hint.textContent.includes('数据不完整'));

// ── 场景五：非法 JSON ───────────────────────────────────────────
const b5 = makeEl('div'); b5._data = '{不是 JSON';
run([b5]);
check('非法 JSON → 显示解析失败', b5.textContent.includes('解析失败'), b5.textContent);

console.log(failures === 0 ? '\n全部通过' : `\n${failures} 项失败`);
process.exit(failures === 0 ? 0 : 1);
