#!/usr/bin/env python3
"""安装器的回归测试：按平台跑 install.sh / install.ps1，全部在沙箱 HOME 里跑。

它管两件事：装学习预设（并把引擎的 skill 目录写进预设）、建学习工作区并写配置文件。
这里钉住的是**踩过的与容易踩的**：
  · 预设装到 `$DSH_HOME/.agent-presets/learning/`，占位符换成引擎的 skills 路径
  · 工作区路径写进配置，且**一律是绝对路径**（会话在任意目录启动，配置是机器全局的）
  · 重复跑沿用已有工作区、`root`/skills 按当前引擎位置重写（项目被搬走过）
  · 仓库不完整（缺 `.dsh/skills`）时**报错退出**，而不是装出一个指不到技能的空预设

用法：python3 scripts/tests/test_install.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INSTALL = REPO / ('install.ps1' if os.name == 'nt' else 'install.sh')

failures = 0
total = 0


def check(label, ok, extra=''):
    global failures, total
    total += 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f'  — {extra}' if extra and not ok else ''))
    if not ok and extra:
        print('      ' + str(extra).strip().replace('\n', '\n      '))
    failures += not ok


def run(home, workspace=None, script=None, env_extra=None, cwd=None,
        dsh_version='0.1.5-rc.2', profile=None):
    """在沙箱 HOME / USERPROFILE 里跑本平台安装器，返回 CompletedProcess。

    cwd 只在测「相对路径」那条时要给：install.sh 是按**进程当前目录**解析相对
    工作区路径的（PWD 环境变量只是它自己带的一个变量，改它没用），不给 cwd 就会
    把 relws/ 建到仓库根目录里——本测试曾经真的这么漏过。
    """
    env = dict(os.environ, HOME=home, USERPROFILE=home, DSH_HOME=os.path.join(home, '.dsh'))
    # 只探测假命令，避免本机 DSH 版本或配置影响回归测试。
    fake_bin = Path(home, 'bin')
    fake_bin.mkdir(exist_ok=True)
    fake_dsh = fake_bin / ('dsh.cmd' if os.name == 'nt' else 'dsh')
    fake_dsh.write_text(
        '@echo off\necho %STUDYMATE_TEST_DSH_VERSION%\n' if os.name == 'nt'
        else '#!/bin/sh\nprintf "%s\\n" "$STUDYMATE_TEST_DSH_VERSION"\n', encoding='utf-8')
    fake_dsh.chmod(0o755)
    env['STUDYMATE_TEST_DSH_VERSION'] = dsh_version
    env['PATH'] = os.pathsep.join((str(fake_bin), str(Path(sys.executable).parent), env['PATH']))
    env.pop('LEARN_WORKSPACE', None)
    if workspace:
        env['LEARN_WORKSPACE'] = workspace
    env.update(env_extra or {})
    command = ([shutil.which('pwsh') or 'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File']
               if os.name == 'nt' else ['bash'])
    arguments = [('-Profile' if os.name == 'nt' else '--profile'), profile] if profile else []
    return subprocess.run([*command, str(script or INSTALL), *arguments], env=env,
                          capture_output=True, text=True, encoding='utf-8', cwd=cwd)


def config_of(home):
    """读回配置里的 workspace / root。"""
    path = os.path.join(home, '.dsh', 'studymate-config.yaml')
    import yaml
    with open(path, encoding='utf-8') as handle:
        return {key: os.path.normpath(value) for key, value in yaml.safe_load(handle).items()}


def same_path(actual, expected):
    """路径须为绝对路径；Windows 的 8.3 短名与完整名称视为同一路径。"""
    return (isinstance(actual, str) and os.path.isabs(actual)
            and os.path.normcase(os.path.realpath(actual))
            == os.path.normcase(os.path.realpath(expected)))


def preset_skills(home):
    """读回预设里写死的 skill 目录。"""
    path = os.path.join(home, '.dsh', '.agent-presets', 'learning', 'agent.cordis.yml')
    text = open(path, encoding='utf-8').read()
    import re
    match = re.search(r"^\s*-\s*'((?:[^']|'')*\.dsh/skills)'", text, re.M)
    return os.path.normpath(match.group(1).replace("''", "'")) if match else None


def preset_tool_rows(home):
    """读回预设里按 id 索引的工具行。

    `disabled: !!js …` 是 DSH 自己的 JS 表达式标签（按平台禁用 bash/pwsh），
    标准 SafeLoader 认不出来，所以把该标签原样当字符串收下——这里只关心
    委派工具那两行的字面配置，不求值。
    """
    import yaml

    class Tolerant(yaml.SafeLoader):
        pass

    Tolerant.add_multi_constructor(
        'tag:yaml.org,2002:js',
        lambda loader, suffix, node: loader.construct_scalar(node))

    path = os.path.join(home, '.dsh', '.agent-presets', 'learning', 'agent.cordis.yml')
    with open(path, encoding='utf-8') as handle:
        data = yaml.load(handle, Loader=Tolerant)

    rows = {}

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get('id'), str):
                rows[node['id']] = node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    return rows


def main():
    tmp = tempfile.mkdtemp(prefix='smtest-install-')
    home = os.path.join(tmp, 'home')
    os.makedirs(home)

    # ① 全新安装
    proc = run(home, workspace=os.path.join(tmp, 'ws'))
    check('全新安装退出码 0', proc.returncode == 0, proc.stderr)
    check('预设装到 $DSH_HOME/.agent-presets/learning/',
          os.path.isfile(os.path.join(home, '.dsh', '.agent-presets', 'learning', 'agent.cordis.yml')))
    check('预设里的 skill 目录 = 引擎的 .dsh/skills',
          same_path(preset_skills(home), REPO / '.dsh' / 'skills'), preset_skills(home))
    check('配置写的是绝对路径',
          same_path(config_of(home)['workspace'], os.path.join(tmp, 'ws')), config_of(home))
    check('工作区建出 .learning/subjects',
          os.path.isdir(os.path.join(tmp, 'ws', '.learning', 'subjects')))
    check('配置里的 root = 当前引擎位置', same_path(config_of(home)['root'], REPO), config_of(home))

    # ①a 同时钉住两个安装器的关键动作，防止只改了一边。
    ps1_path = REPO / 'install.ps1'
    check('Windows 安装脚本 install.ps1 在', ps1_path.is_file())
    ps1 = ps1_path.read_text(encoding='utf-8') if ps1_path.is_file() else ''
    for label, needle in (
        ('装预设到 .agent-presets\\learning', '.agent-presets\\learning'),
        ('替换 skill 目录占位符', '__STUDYMATE_SKILLS__'),
        ('写 studymate-config.yaml', 'studymate-config.yaml'),
        ('支持 LEARN_WORKSPACE 覆盖', 'LEARN_WORKSPACE'),
        ('配置里落 workspace 行', 'workspace: $Workspace'),
        ('配置里落 root 行', 'root: $RootPosix'),
        ('UTF-8 不带 BOM 写盘', 'UTF8Encoding($false)'),
    ):
        check(f'install.ps1 与 install.sh 对齐：{label}', needle in ps1)
    # 脚本自己被 PowerShell 5.1 读时也要按 UTF-8 解码：没有 BOM 时它按系统 ANSI（中文 Windows 是GBK）解码，中文注释与提示串错乱，整个脚本变成语法错误（issue #8）。
    check('install.ps1 带 UTF-8 BOM',
          ps1_path.read_bytes()[:3] == b'\xef\xbb\xbf',
          ps1_path.read_bytes()[:3])
    # ①b 委派工具的口径：角色跑全新上下文，且角色不得再往下派。    # 这两条是"角色反过来当总控"那次的修复（fork 会把总控已完成的回合注进角色），
    # 行被改回去就等于把那个故障放回来——所以钉在安装产物上。
    parse_detail = ''
    try:
        rows = preset_tool_rows(home)
    except Exception as exc:                      # YAML 语法错、行缺失都算失败
        rows, parse_detail = {}, f'{type(exc).__name__}: {exc}'
    check('装出来的预设能整份解析成 YAML（含 !!js 行）', bool(rows), parse_detail)
    check('fork 工具被禁用：tool-subagent-fork disabled',
          (rows.get('tool-subagent-fork') or {}).get('disabled') is True,
          rows.get('tool-subagent-fork'))
    check('subagent 深度封顶 1 层：角色不能再派角色',
          ((rows.get('tool-subagent') or {}).get('config') or {}).get('maxDepth') == 1,
          (rows.get('tool-subagent') or {}).get('config'))

    # ② 重复跑：沿用已有工作区
    proc = run(home)
    check('重复跑退出码 0', proc.returncode == 0, proc.stderr)
    check('重复跑沿用已有工作区（没有被重置回 <root>/workspace）',
          same_path(config_of(home)['workspace'], os.path.join(tmp, 'ws')), config_of(home))

    # ③ 首课流程要用的：工作区能生成主页（用沙箱配置，不碰真实 ~/.dsh）
    env = dict(os.environ, HOME=home, DSH_HOME=os.path.join(home, '.dsh'))
    gen = subprocess.run([sys.executable, str(REPO / 'scripts' / 'gen_home.py')], env=env,
                         capture_output=True, text=True)
    check('装完能跑 gen_home 生成空状态主页', gen.returncode == 0, gen.stdout + gen.stderr)
    check('根主页与共享层就位（含抬头看板娘）',
          os.path.isfile(os.path.join(tmp, 'ws', 'index.html')) and
          os.path.isdir(os.path.join(tmp, 'ws', '.learning', 'assets', 'sayo')) and
          os.path.isfile(os.path.join(tmp, 'ws', '.learning', 'assets', 'learn-mascot.png')))

    # ④ 路径写法：~ 展开、相对路径变绝对（配置是机器全局的，留相对路径就找不到工作区）
    proc = run(home, workspace='~/tilde')
    check('`~/x` 展开成家目录下的绝对路径',
          same_path(config_of(home)['workspace'], os.path.join(home, 'tilde')), config_of(home))
    proc = run(home, workspace='relws', env_extra={'PWD': tmp}, cwd=tmp)
    check('相对路径落成绝对路径（且落在当时的当前目录下，不落到仓库里）',
          same_path(config_of(home)['workspace'], os.path.join(tmp, 'relws')), config_of(home))

    # ⑤ 引擎被搬走：root 与预设里的 skills 路径都按当前位置重写
    moved = os.path.join(tmp, "moved [repo] O'Brien #1")
    os.makedirs(moved)
    shutil.copy(INSTALL, moved)
    os.makedirs(os.path.join(moved, 'scripts'))
    shutil.copy(REPO / 'scripts' / 'install_preset.py', os.path.join(moved, 'scripts'))
    shutil.copytree(REPO / 'preset', os.path.join(moved, 'preset'))
    shutil.copytree(REPO / '.dsh' / 'skills', os.path.join(moved, '.dsh', 'skills'))
    proc = run(home, script=os.path.join(moved, INSTALL.name))
    check('引擎搬走后重跑退出码 0', proc.returncode == 0, proc.stderr)
    check('root 重写为新位置', same_path(config_of(home)['root'], moved), config_of(home))
    check('预设里的 skills 路径也重写', same_path(preset_skills(home), os.path.join(moved, '.dsh', 'skills')),
          preset_skills(home))
    try:
        moved_rows = preset_tool_rows(home)
        skill_dirs = moved_rows['skill-filesystem']['config']['customSkillDirs']
        check('含单引号的引擎路径写入后预设仍是合法 YAML',
              isinstance(skill_dirs, list) and len(skill_dirs) == 1
              and same_path(skill_dirs[0], Path(moved, '.dsh', 'skills')), skill_dirs)
    except Exception as exc:
        check('含单引号的引擎路径写入后预设仍是合法 YAML', False, exc)

    special_workspace = os.path.join(tmp, "work [1] O'Brien # notes")
    proc = run(home, workspace=special_workspace)
    check('特殊字符工作区可创建且配置可解析',
          proc.returncode == 0 and same_path(config_of(home)['workspace'], special_workspace), proc.stderr)
    proc = run(home)
    check('再次安装保留特殊字符工作区',
          proc.returncode == 0 and same_path(config_of(home)['workspace'], special_workspace), proc.stderr)

    # ⑥ 仓库不完整：宁可报错，也不要装出一个指不到技能的空预设
    broken = os.path.join(tmp, 'broken-repo')
    os.makedirs(broken)
    shutil.copy(INSTALL, broken)
    shutil.copytree(REPO / 'preset', os.path.join(broken, 'preset'))
    proc = run(home, script=os.path.join(broken, INSTALL.name))
    check('缺 .dsh/skills 时报错退出', proc.returncode != 0 and 'skills' in proc.stderr,
          f'exit={proc.returncode} stderr={proc.stderr.strip()[:120]}')

    # ⑦ 工作流插件改名早于声明式预设，分别验证两个版本边界。
    check('旧 DSH 保留 worker-thread 插件',
          'workflow-worker-thread' in preset_tool_rows(home))
    proc = run(home, dsh_version='0.1.6-alpha.1')
    patch = Path(home, '.dsh', 'profiles', 'web', 'cordis.patch.yml')
    check('DSH 0.1.6 使用 ptc，但仍沿用目录扫描',
          proc.returncode == 0 and 'workflow-ptc' in preset_tool_rows(home)
          and not patch.exists(), proc.stderr)
    patch.parent.mkdir(parents=True, exist_ok=True)
    patch.write_text('# 原有配置\n[]\n', encoding='utf-8')
    proc = run(home, dsh_version='0.1.7-alpha.1')
    registered = patch.read_text(encoding='utf-8')
    check('DSH 0.1.7 注册学习模式并保留原配置注释',
          proc.returncode == 0 and '@deepseek-ai/dsh-agent-preset' in registered
          and '# 原有配置' in registered and 'workflow-ptc' in preset_tool_rows(home), proc.stderr)
    proc = run(home, dsh_version='0.1.7-alpha.1')
    check('声明式预设重复安装不产生重复声明',
          proc.returncode == 0 and patch.read_text(encoding='utf-8') == registered, proc.stderr)
    proc = run(home, dsh_version='0.1.7-alpha.1', profile='headless')
    check('可指定 headless profile，web 配置不变',
          proc.returncode == 0 and Path(home, '.dsh', 'profiles', 'headless', 'cordis.patch.yml').exists()
          and patch.read_text(encoding='utf-8') == registered, proc.stderr)

    preset_path = Path(home, '.dsh', '.agent-presets', 'learning', 'agent.cordis.yml')
    original_preset = preset_path.read_bytes()
    config_path = Path(home, '.dsh', 'studymate-config.yaml')
    original_config = config_path.read_bytes()
    patch.write_text('invalid: [\n', encoding='utf-8')
    proc = run(home, dsh_version='0.1.7-alpha.1', workspace=os.path.join(tmp, 'should-not-create'))
    check('profile YAML 错误时原预设和工作区配置保持不变',
          proc.returncode != 0 and preset_path.read_bytes() == original_preset
          and config_path.read_bytes() == original_config
          and patch.read_text(encoding='utf-8') == 'invalid: [\n', proc.stderr)
    check('安装失败后清理临时目录', not list(Path(home, '.dsh').glob('.studymate-install-*')))
    patch.write_text(registered, encoding='utf-8')
    proc = run(home)
    check('降级 DSH 时移除管理的声明并还原旧工作流',
          proc.returncode == 0 and '@deepseek-ai/dsh-agent-preset' not in patch.read_text(encoding='utf-8')
          and '# 原有配置' in patch.read_text(encoding='utf-8')
          and 'workflow-worker-thread' in preset_tool_rows(home), proc.stderr)

    print(f'\n{total - failures}/{total} 通过')
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
