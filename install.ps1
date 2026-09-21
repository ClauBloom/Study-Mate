# StudyMate 安装脚本（Windows / PowerShell 5.1+）
# 与 install.sh 等价：装「学习模式」预设到 <DSH_HOME 或 %USERPROFILE%\.dsh>\ + 建学习工作区
#
# 用法（在项目根目录）：
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   想换工作区位置：$env:LEARN_WORKSPACE = 'D:\study'; .\install.ps1
#   想换 DSH 目录：  $env:DSH_HOME = 'D:\dsh';        .\install.ps1
$ErrorActionPreference = 'Stop'

# 写文件一律 UTF-8 **不带 BOM**：配置和预设都要被 YAML 解析器读，
# 少一个 BOM 少一类"只有 Windows 上才复现"的怪问题。
function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}
function Read-Utf8([string]$Path) {
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Dsh  = if ($env:DSH_HOME) { $env:DSH_HOME } else { Join-Path $env:USERPROFILE '.dsh' }

# ── 1) 学习模式预设 → <DSH>\.agent-presets\learning\，并把引擎的 skill 目录写进去
$SkillsSrc = Join-Path $Root '.dsh\skills'
if (-not (Test-Path $SkillsSrc)) {
    [Console]::Error.WriteLine("找不到 $SkillsSrc —— 引擎目录不完整（仓库要整个克隆，别只拷 install.ps1）")
    exit 1
}
$DestPreset = Join-Path $Dsh '.agent-presets\learning'
New-Item -ItemType Directory -Force -Path $DestPreset | Out-Null
Copy-Item -Path (Join-Path $Root 'preset\learning\*') -Destination $DestPreset -Recurse -Force

$AgentYml    = Join-Path $DestPreset 'agent.cordis.yml'
$SkillsPosix = $SkillsSrc -replace '\\', '/'      # YAML 里用正斜杠：反斜杠是转义字符
$text = Read-Utf8 $AgentYml
if ($text.Contains('__STUDYMATE_SKILLS__')) {
    Write-Utf8NoBom $AgentYml ($text.Replace('__STUDYMATE_SKILLS__', $SkillsPosix))
} elseif (-not $text.Contains($SkillsPosix)) {
    [Console]::Error.WriteLine('预设里既没有占位符 __STUDYMATE_SKILLS__，也没有已写入的 skill 路径')
    exit 1
}
Write-Host "① 预设 → $DestPreset（skill 目录：$SkillsPosix）"

# ── 2) 学习工作区：默认 <root>\workspace\，路径写进配置
#     已有配置里的 workspace 默认沿用（学生可能已把工作区放到别处）。
$Config      = Join-Path $Dsh 'studymate-config.yaml'
$Workspace   = $env:LEARN_WORKSPACE
$KeptExisting = $false
if (-not $Workspace -and (Test-Path $Config)) {
    $hit = Select-String -Path $Config -Pattern '^workspace:\s*(.+?)\s*$' | Select-Object -First 1
    if ($hit) {
        $Workspace = $hit.Matches[0].Groups[1].Value
        $KeptExisting = $true
    }
}
if (-not $Workspace) { $Workspace = Join-Path $Root 'workspace' }

# 路径统一成绝对路径：开头的 ~ 展开成家目录，相对路径按当前目录解析。
# 配置是机器全局的（会话在任意目录启动时按它定位工作区），留相对路径换个目录就找不到。
if ($Workspace.StartsWith('~')) {
    $Workspace = Join-Path $env:USERPROFILE $Workspace.Substring(1).TrimStart('\', '/')
}
if (-not [System.IO.Path]::IsPathRooted($Workspace)) {
    $Workspace = Join-Path (Get-Location).Path $Workspace
}
New-Item -ItemType Directory -Force -Path (Join-Path $Workspace '.learning\subjects') | Out-Null
$Workspace = (Resolve-Path $Workspace).Path -replace '\\', '/'
$RootPosix = $Root -replace '\\', '/'

Write-Utf8NoBom $Config @"
# StudyMate 学习工作区与引擎项目定位
workspace: $Workspace
root: $RootPosix
"@
if ($KeptExisting) {
    Write-Host "② 学习工作区 → $Workspace（沿用已有工作区；配置在 $Config）"
} else {
    Write-Host "② 学习工作区 → $Workspace（配置在 $Config）"
}

Write-Host "完成（StudyMate v0.1）。现在可在任意目录开会话，选'学习模式'预设开始学习。"
