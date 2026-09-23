#!/usr/bin/env bash
# StudyMate 安装脚本：装学习预设到用户级 ~/.dsh/ + 建学习工作区
# 会话可在任意目录启动：预设带着 skill 目录，学习数据由配置文件定位。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DSH="${DSH_HOME:-$HOME/.dsh}"
PROFILE=web
if [ "${1:-}" = '--profile' ] && [ "$#" -eq 2 ]; then
  PROFILE="$2"
elif [ "$#" -ne 0 ]; then
  echo "用法：./install.sh [--profile web]" >&2
  exit 1
fi

# 1) 学习模式预设 → ~/.dsh/.agent-presets/learning/，并把引擎的 skill 目录写进去
if [ ! -d "$ROOT/.dsh/skills" ]; then
  echo "找不到 $ROOT/.dsh/skills——引擎目录不完整（仓库要整个克隆，别只拷 install.sh）" >&2
  exit 1
fi
DEST_PRESET="$DSH/.agent-presets/learning"
PYTHON=''
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -X utf8 -c 'import sys, yaml; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "需要 Python 3.9+ 和 PyYAML（python3 -m pip install pyyaml）" >&2
  exit 1
fi
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
mkdir -p "$DSH"
STAGE="$(mktemp -d "$DSH/.studymate-install.XXXXXX")"
trap 'rm -rf -- "$STAGE"' EXIT
mkdir -p "$STAGE/preset"
cp -r "$ROOT/preset/learning/." "$STAGE/preset/"
"$PYTHON" - "$STAGE/preset/agent.cordis.yml" "$ROOT/.dsh/skills" <<'PY'
import pathlib, sys
path, skills = sys.argv[1], sys.argv[2]
p = pathlib.Path(path)
t = p.read_text(encoding='utf-8')
if '__STUDYMATE_SKILLS__' in t:
    p.write_text(t.replace('__STUDYMATE_SKILLS__', skills.replace("'", "''")), encoding='utf-8')
elif skills not in t:
    raise SystemExit('预设里既没有占位符 __STUDYMATE_SKILLS__，也没有已写入的 skill 路径')
PY
"$PYTHON" "$ROOT/scripts/install_preset.py" \
  --preset-dir "$STAGE/preset" --preset-target "$DEST_PRESET" \
  --dsh-home "$DSH" --profile "$PROFILE" \
  --patch-output "$STAGE/cordis.patch.yml" > "$STAGE/result.json"
mkdir -p "$DEST_PRESET"
cp -r "$STAGE/preset/." "$DEST_PRESET/"
if [ -f "$STAGE/cordis.patch.yml" ]; then
  mkdir -p "$DSH/profiles/$PROFILE"
  mv "$STAGE/cordis.patch.yml" "$DSH/profiles/$PROFILE/cordis.patch.yml"
fi
echo "① 预设 → ${DEST_PRESET}（skill 目录：${ROOT}/.dsh/skills）"

# 2) 学习工作区：默认 <root>/workspace/，路径写入配置
#    已有配置里的 workspace 默认沿用（学生可能已把工作区放到别处）；
#    想换位置：改配置里那一行，或跑一次 LEARN_WORKSPACE=<新路径> ./install.sh。
#    root 每次都按当前引擎路径重写（项目可能被移动过）。
CONFIG="$DSH/studymate-config.yaml"
WORKSPACE="${LEARN_WORKSPACE:-}"
KEPT_EXISTING=""
if [ -z "$WORKSPACE" ] && [ -f "$CONFIG" ]; then
  WORKSPACE="$("$PYTHON" - "$CONFIG" <<'PY'
import pathlib, sys, yaml
config = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')) or {}
workspace = config.get('workspace') if isinstance(config, dict) else None
if workspace is not None and not isinstance(workspace, str):
    raise SystemExit('配置里的 workspace 必须是路径字符串')
print(workspace or '')
PY
)"
  if [ -n "$WORKSPACE" ]; then
    KEPT_EXISTING=1
  fi
fi
if [ -z "$WORKSPACE" ]; then
  WORKSPACE="$ROOT/workspace"
fi
# 路径统一成绝对路径：开头一个 ~ 展开成家目录，相对路径按当前目录解析。
# 配置是机器全局的（会话在任意目录启动时按它定位工作区），留相对路径的话
# 换个目录开会话就找不到工作区了——所以这里就把它钉成绝对路径。
WORKSPACE="${WORKSPACE/#\~/$HOME}"
mkdir -p "$WORKSPACE/.learning/subjects"
WORKSPACE="$(cd "$WORKSPACE" && pwd)"
"$PYTHON" - "$CONFIG" "$WORKSPACE" "$ROOT" <<'PY'
import json, pathlib, sys
path, workspace, root = sys.argv[1:]
pathlib.Path(path).write_text(
    '# StudyMate 学习工作区与引擎项目定位\n'
    f'workspace: {json.dumps(workspace, ensure_ascii=False)}\n'
    f'root: {json.dumps(root, ensure_ascii=False)}\n', encoding='utf-8')
PY
if [ -n "$KEPT_EXISTING" ]; then
  echo "② 学习工作区 → ${WORKSPACE}（沿用已有工作区；配置在 ${CONFIG}）"
else
  echo "② 学习工作区 → ${WORKSPACE}（配置在 ${CONFIG}）"
fi

echo "完成（StudyMate v0.1）。现在可在任意目录开会话，选'学习模式'预设开始学习。"
