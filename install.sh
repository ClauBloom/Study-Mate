#!/usr/bin/env bash
# StudyMate 安装脚本：装学习预设到用户级 ~/.dsh/ + 建学习工作区
# 会话可在任意目录启动：预设带着 skill 目录，学习数据由配置文件定位。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DSH="${DSH_HOME:-$HOME/.dsh}"

# 1) 学习模式预设 → ~/.dsh/.agent-presets/learning/，并把引擎的 skill 目录写进去
if [ ! -d "$ROOT/.dsh/skills" ]; then
  echo "找不到 $ROOT/.dsh/skills——引擎目录不完整（仓库要整个克隆，别只拷 install.sh）" >&2
  exit 1
fi
DEST_PRESET="$DSH/.agent-presets/learning"
mkdir -p "$DEST_PRESET"
cp -r "$ROOT/preset/learning/." "$DEST_PRESET/"
python3 - "$DEST_PRESET/agent.cordis.yml" "$ROOT/.dsh/skills" <<'PY'
import pathlib, sys
path, skills = sys.argv[1], sys.argv[2]
p = pathlib.Path(path)
t = p.read_text(encoding='utf-8')
if '__STUDYMATE_SKILLS__' in t:
    p.write_text(t.replace('__STUDYMATE_SKILLS__', skills), encoding='utf-8')
elif skills not in t:
    raise SystemExit('预设里既没有占位符 __STUDYMATE_SKILLS__，也没有已写入的 skill 路径')
PY
echo "① 预设 → $DEST_PRESET（skill 目录：$ROOT/.dsh/skills）"

# 2) 学习工作区：默认 <root>/workspace/，路径写入配置
#    已有配置里的 workspace 默认沿用（学生可能已把工作区放到别处）；
#    想换位置：改配置里那一行，或跑一次 LEARN_WORKSPACE=<新路径> ./install.sh。
#    root 每次都按当前引擎路径重写（项目可能被移动过）。
CONFIG="$DSH/studymate-config.yaml"
WORKSPACE="${LEARN_WORKSPACE:-}"
KEPT_EXISTING=""
if [ -z "$WORKSPACE" ] && [ -f "$CONFIG" ]; then
  WORKSPACE="$(sed -n '/^workspace:/{s/^workspace:[[:space:]]*//;s/[[:space:]]*$//;p;q;}' "$CONFIG")"
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
cat > "$CONFIG" <<EOF
# StudyMate 学习工作区与引擎项目定位
workspace: $WORKSPACE
root: $ROOT
EOF
if [ -n "$KEPT_EXISTING" ]; then
  echo "② 学习工作区 → $WORKSPACE（沿用已有工作区；配置在 $CONFIG）"
else
  echo "② 学习工作区 → $WORKSPACE（配置在 $CONFIG）"
fi

echo "完成。现在可在任意目录开会话，选'学习模式'预设开始学习。"
