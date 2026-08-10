param(
  [Parameter(Mandatory=$true)][string]$SkillName,
  [Parameter(Mandatory=$true)][ValidateSet("claude-code","openclaw","codex","generic")][string]$Agent,
  [ValidateSet("user","project")][string]$Scope = "user",
  [string]$Dest = "",
  [switch]$Bundle
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")

function Locate-SkillDir([string]$Name) {
  $dir = ""
  $reg = Join-Path $RootDir "registry.json"
  if (Test-Path $reg) {
    try {
      $r = Get-Content -Raw -Path $reg | ConvertFrom-Json
      foreach ($s in @($r.skills)) {
        if ($s.name -eq $Name) { $dir = Join-Path $RootDir $s.path; break }
      }
    } catch { Write-Warning "Could not read registry.json: $_" }
  }
  if ($dir -eq "") {
    $sr = Join-Path $RootDir "skills"
    if (Test-Path $sr) {
      foreach ($cat in Get-ChildItem -Directory $sr) {
        $cand = Join-Path $cat.FullName $Name
        if (Test-Path (Join-Path $cand "SKILL.md")) { $dir = $cand; break }
      }
    }
  }
  if ($dir -ne "" -and (Test-Path (Join-Path $dir "SKILL.md"))) { return $dir } else { return "" }
}

function Resolve-Dest {
  if ($Dest -ne "") { return $Dest }
  switch ($Agent) {
    "claude-code" {
      if ($Scope -eq "project") { ".claude\skills" }
      else { if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME ".claude\skills" } }
    }
    "openclaw" {
      if ($Scope -eq "project") { ".openclaw\skills" }
      else { if ($env:OPENCLAW_SKILLS_DIR) { $env:OPENCLAW_SKILLS_DIR } else { Join-Path $HOME ".openclaw\skills" } }
    }
    "codex" {
      if ($Scope -eq "project") { ".codex\skills" }
      else { if ($env:CODEX_SKILLS_DIR) { $env:CODEX_SKILLS_DIR } else { Join-Path $HOME ".codex\skills" } }
    }
    "generic" {
      if ($env:SKILL_DEST_DIR) { $env:SKILL_DEST_DIR } else { ".\skills-installed" }
    }
  }
}

function Install-Skill([string]$Name, [string]$DestRoot) {
  $src = Locate-SkillDir $Name
  if ($src -eq "") { Write-Error "Skill not found: $Name"; return $false }
  New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null
  $target = Join-Path $DestRoot $Name
  if (Test-Path $target) {
    $backup = "$target.bak.$(Get-Date -Format yyyyMMddHHmmss)"
    Move-Item $target $backup
    Write-Host "Backed up existing $Name to $backup"
  }
  Copy-Item -Recurse -Path $src -Destination $target
  Write-Host "Installed $Name for $Agent at $target"
  return $true
}

# 递归读 skill.json dependencies，自身在前、依赖在后，去重防循环
function Resolve-Bundle([string]$Name) {
  $script:bundleVisited = @{}
  $script:bundleOrder = New-Object System.Collections.Generic.List[string]
  function Walk([string]$n) {
    if ($script:bundleVisited.ContainsKey($n)) { return }
    $dir = Locate-SkillDir $n
    if ($dir -eq "") { return }
    $script:bundleVisited[$n] = $true
    [void]$script:bundleOrder.Add($n)
    $sj = Join-Path $dir "skill.json"
    if (Test-Path $sj) {
      try {
        $d = Get-Content -Raw -Path $sj | ConvertFrom-Json
        foreach ($dep in ($d.dependencies)) { Walk $dep }
      } catch {}
    }
  }
  Walk $Name
  return $script:bundleOrder
}

$DestRoot = Resolve-Dest

if ($Bundle) {
  $list = @(Resolve-Bundle $SkillName)
  if ($list.Count -eq 0) { Write-Error "No bundle resolved for $SkillName (skill.json 无 dependencies 或未在 registry)"; exit 1 }
  Write-Host "== Bundle 安装：$SkillName 及其 dependencies =="
  $list | ForEach-Object { Write-Host $_ }
  Write-Host "----"
  $failed = $false
  foreach ($s in $list) { if (-not (Install-Skill $s $DestRoot)) { $failed = $true } }
  if ($failed) { Write-Error "部分 skill 安装失败，见上"; exit 1 }
  Write-Host "== Bundle 完成 =="
} else {
  $ok = Install-Skill $SkillName $DestRoot
  if (-not $ok) { exit 1 }
}
