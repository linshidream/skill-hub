param(
  [Parameter(Mandatory=$true)][string]$SkillName,
  [Parameter(Mandatory=$true)][ValidateSet("claude-code","openclaw","codex","generic")][string]$Agent,
  [ValidateSet("user","project")][string]$Scope = "user",
  [string]$Dest = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
$SkillDir = ""

$RegistryPath = Join-Path $RootDir "registry.json"
if (Test-Path $RegistryPath) {
  try {
    $Registry = Get-Content -Raw -Path $RegistryPath | ConvertFrom-Json
    foreach ($Skill in @($Registry.skills)) {
      if ($Skill.name -eq $SkillName) {
        $SkillDir = Join-Path $RootDir $Skill.path
        break
      }
    }
  } catch {
    Write-Warning "Could not read registry.json: $_"
  }
}

if ($SkillDir -eq "") {
  $SkillsRoot = Join-Path $RootDir "skills"
  if (Test-Path $SkillsRoot) {
    foreach ($Category in Get-ChildItem -Directory $SkillsRoot) {
      $Candidate = Join-Path $Category.FullName $SkillName
      if (Test-Path (Join-Path $Candidate "SKILL.md")) {
        $SkillDir = $Candidate
        break
      }
    }
  }
}

if ($SkillDir -eq "" -or !(Test-Path (Join-Path $SkillDir "SKILL.md"))) {
  Write-Error "Skill not found: $SkillName"
  exit 1
}

if ($Dest -eq "") {
  switch ($Agent) {
    "claude-code" {
      if ($Scope -eq "project") {
        $Dest = ".claude\skills"
      } else {
        $Dest = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME ".claude\skills" }
      }
    }
    "openclaw" {
      if ($Scope -eq "project") {
        $Dest = ".openclaw\skills"
      } else {
        $Dest = if ($env:OPENCLAW_SKILLS_DIR) { $env:OPENCLAW_SKILLS_DIR } else { Join-Path $HOME ".openclaw\skills" }
      }
    }
    "codex" {
      if ($Scope -eq "project") {
        $Dest = ".codex\skills"
      } else {
        $Dest = if ($env:CODEX_SKILLS_DIR) { $env:CODEX_SKILLS_DIR } else { Join-Path $HOME ".codex\skills" }
      }
    }
    "generic" {
      $Dest = if ($env:SKILL_DEST_DIR) { $env:SKILL_DEST_DIR } else { ".\skills-installed" }
    }
  }
}

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$Target = Join-Path $Dest $SkillName

if (Test-Path $Target) {
  $Backup = "$Target.bak.$(Get-Date -Format yyyyMMddHHmmss)"
  Move-Item $Target $Backup
  Write-Host "Backed up existing skill to $Backup"
}

Copy-Item -Recurse -Path $SkillDir -Destination $Target
Write-Host "Installed $SkillName for $Agent at $Target"
