#!/usr/bin/env python3
"""Register a copied learning preset without rewriting unrelated Cordis patches."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml

BEGIN = '# BEGIN STUDYMATE LEARNING PRESET'
END = '# END STUDYMATE LEARNING PRESET'
PLUGIN = '@deepseek-ai/dsh-agent-preset'
ENTRY_ID = 'studymate-learning-preset'


class PatchLoader(yaml.SafeLoader):
    pass


PatchLoader.add_constructor('tag:yaml.org,2002:js', lambda loader, node: loader.construct_scalar(node))


class PresetLoader(yaml.SafeLoader):
    pass


# This is the Loader's native JSON representation of an unevaluated !!js node.
# Inline plugin definitions keep the profile's module-resolution context; an
# external cordis:include switches it to the preset folder and fails to import
# the host-installed packages on dsh 0.1.7.
PresetLoader.add_constructor('tag:yaml.org,2002:js',
                             lambda loader, node: {'__jsExpr': loader.construct_scalar(node)})


def at_least(version, minimum):
    def parse(value):
        match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:-([\w.-]+))?(?:\+[\w.-]+)?', value)
        if not match:
            raise ValueError(f'无法识别 dsh 版本：{value}')
        release = tuple(map(int, match.group(1, 2, 3)))
        prerelease = match.group(4)
        parts = tuple((0, int(part)) if part.isdigit() else (1, part)
                      for part in prerelease.split('.')) if prerelease else ()
        return release, not bool(prerelease), parts
    return parse(version) >= parse(minimum)


def installed_version():
    try:
        result = subprocess.run(['dsh', '--version'], capture_output=True, text=True,
                                encoding='utf-8', timeout=15, shell=os.name == 'nt')
    except FileNotFoundError:
        return None
    if result.returncode:
        # cmd.exe reports a missing npm shim as a nonzero exit, not ENOENT.
        if os.name == 'nt':
            import shutil
            if shutil.which('dsh') is None:
                return None
        raise ValueError('dsh --version 运行失败，请修复 dsh 或显式传入 --dsh-version')
    return result.stdout.strip()


def read(path):
    if not path.exists():
        return ''
    with path.open(encoding='utf-8', newline='') as handle:
        return handle.read()


def without_managed(text):
    if BEGIN not in text and END not in text:
        return text
    pattern = rf'(?m)^{re.escape(BEGIN)}\r?\n[\s\S]*?^{re.escape(END)}(?:\r?\n|$)'
    stripped, count = re.subn(pattern, '', text)
    if count != 1 or BEGIN in stripped or END in stripped:
        raise ValueError('StudyMate 注册标记不完整或重复，请先检查 cordis.patch.yml')
    return stripped


def parse_patch(text, path):
    try:
        data = yaml.load(text, Loader=PatchLoader)
        node = yaml.compose(text, Loader=PatchLoader)
    except yaml.YAMLError as error:
        raise ValueError(f'无法解析 {path}，不会覆盖原配置：{error}') from error
    if node is not None and not isinstance(node, yaml.SequenceNode):
        raise ValueError(f'{path} 顶层必须是 YAML 列表')
    return data or [], node


def rows(data):
    if isinstance(data, list):
        for value in data:
            yield from rows(value)
    elif isinstance(data, dict):
        yield data
        for value in data.values():
            if isinstance(value, (dict, list)):
                yield from rows(value)


def learning_rows(data):
    return [row for row in rows(data)
            if row.get('name') == PLUGIN and isinstance(row.get('config'), dict)
            and row['config'].get('id') == 'learning']


def insert_managed(text, node, row):
    encoded = json.dumps(row, ensure_ascii=False)
    if node is not None and node.flow_style:
        # Keep the original flow-list text, including comments and !!js tags.
        closing = node.end_mark.index - 1
        prefix = text[:closing]
        # A trailing comma before an optional comment already separates items.
        tokens = list(yaml.scan(text, Loader=PatchLoader))
        from yaml.tokens import FlowSequenceEndToken, FlowEntryToken
        end = next(i for i, token in enumerate(tokens)
                   if isinstance(token, FlowSequenceEndToken) and token.start_mark.index == closing)
        comma = bool(node.value) and not isinstance(tokens[end - 1], FlowEntryToken)
        separator = '' if prefix.endswith('\n') else '\n'
        block = f'{separator}{BEGIN}\n{"," if comma else ""}{encoded}\n{END}\n'
        return prefix + block + text[closing:]
    position = node.end_mark.index if node is not None else len(text)
    prefix = text[:position]
    block = f'{BEGIN}\n- {encoded}\n{END}\n'
    return prefix + ('' if not prefix or prefix.endswith('\n') else '\n') + block + text[position:]


def atomic_write(path, text):
    if path.is_symlink():
        raise ValueError(f'为避免改动其他目录，不覆盖符号链接：{path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=path.parent, prefix='.studymate-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        if path.exists():
            os.chmod(temporary, path.stat().st_mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def install(args):
    version = args.dsh_version if args.dsh_version is not None else installed_version()
    modern = version is not None and at_least(version, '0.1.7-alpha.1')
    workflow = 'ptc' if version is not None and at_least(version, '0.1.6-alpha.1') else 'worker-thread'
    home = Path(args.dsh_home).expanduser().absolute()
    profile = args.profile
    if not profile or '/' in profile or '\\' in profile or '\x00' in profile or profile.lower() in ('.', '..', 'node_modules', 'desktop'):
        raise ValueError('--profile 必须是单个配置名称，不能包含路径分隔符，也不能使用 node_modules 或 desktop')
    preset = Path(args.preset_dir) / 'agent.cordis.yml'
    agent = preset.read_text(encoding='utf-8')
    agent = re.sub(r'(@deepseek-ai/dsh-workflow-|\bid: workflow-)(?:worker-thread|ptc)\b',
                   lambda match: match.group(1) + workflow, agent)
    patch = home / 'profiles' / profile / 'cordis.patch.yml'
    original = read(patch)
    clean = without_managed(original)
    updated = clean
    if modern:
        home_patch = home / 'cordis.patch.yml'
        home_data, _ = parse_patch(read(home_patch), home_patch)
        if learning_rows(home_data):
            raise ValueError(f'{home_patch} 已声明 learning 预设，请先处理该全局声明；未修改配置')
        data, node = parse_patch(clean, patch)
        existing = learning_rows(data)
        if len(existing) > 1:
            raise ValueError(f'{patch} 有多个 learning 声明，请先消除重复；未修改配置')
        if existing and (not isinstance(existing[0].get('id'), str) or not existing[0]['id'].strip()):
            raise ValueError(f'{patch} 的 learning 声明缺少稳定的 Loader id，无法安全复用')
        if not existing and any(row.get('id') == ENTRY_ID for row in rows(data)):
            raise ValueError(f'{patch} 的 {ENTRY_ID} 已被其他配置使用；未修改配置')
        metadata = yaml.safe_load(read(Path(args.preset_dir) / 'preset.yml')) or {}
        config = {key: metadata[key] for key in ('name', 'description', 'order') if key in metadata}
        plugins = yaml.load(agent, Loader=PresetLoader)
        if not isinstance(plugins, list):
            raise ValueError('学习预设必须是插件列表；未修改配置')
        config.update(id='learning', plugins=plugins)
        declaration = {'id': existing[0]['id'] if existing else ENTRY_ID, 'config': config}
        if not existing:
            declaration['name'] = PLUGIN
        row = declaration if existing else {'insert': [declaration]}
        updated = insert_managed(clean, node, row)
        parse_patch(updated, patch)
    # Do not touch active profile configuration when the npm installer stages an update.
    changed = updated != original
    output = Path(args.patch_output) if args.patch_output else patch
    if preset.is_symlink() or changed and output.is_symlink():
        raise ValueError('预设或配置文件是符号链接；未修改配置')
    atomic_write(preset, agent)
    if changed:
        atomic_write(output, updated)
    return {'patchPath': str(output) if changed else None, 'patchChanged': changed,
            'mode': 'declarative' if modern else 'legacy'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset-dir', required=True)
    parser.add_argument('--preset-target', required=True)
    parser.add_argument('--dsh-home', required=True)
    parser.add_argument('--profile', default='web')
    parser.add_argument('--dsh-version')
    parser.add_argument('--patch-output')
    try:
        print(json.dumps(install(parser.parse_args()), ensure_ascii=False))
    except (ValueError, OSError, subprocess.SubprocessError, yaml.YAMLError) as error:
        print(f'StudyMate：{error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
