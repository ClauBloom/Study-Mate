#!/usr/bin/env bash
# StudyMate 安装脚本：装学习预设到用户级 ~/.dsh/ + 建学习工作区
# 会话可在任意目录启动：预设带着 skill 目录，学习数据由配置文件定位。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DSH="${DSH_HOME:-$HOME/.dsh}"

# 1) 学习模式预设 → ~/.dsh/.agent-presets/learning/，并把引擎的 skill 目录写进去
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
WORKSPACE="${LEARN_WORKSPACE:-$ROOT/workspace}"
mkdir -p "$WORKSPACE/.learning/subjects"
cat > "$DSH/studymate-config.yaml" <<EOF
# StudyMate 学习工作区与引擎项目定位
workspace: $WORKSPACE
root: $ROOT
EOF
echo "② 学习工作区 → $WORKSPACE（配置在 $DSH/studymate-config.yaml）"

echo "完成。现在可在任意目录开会话，选'学习模式'预设开始学习。"
