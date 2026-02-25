param(
  [Parameter(Mandatory = $true)]
  [string]$json
)

# 解析 JSON（Codex 把一段 JSON 作为 argv[1] 传进来）
try {
  $payload = $json | ConvertFrom-Json
} catch {
  $payload = @{}
}

$title = 'Codex'
$msg   = $payload.'last-assistant-message'
if (-not $msg) {
  if ($payload.type) {
    $msg = "Event: $($payload.type)"
  } else {
    $msg = 'Codex has an update.'
  }
}

# 可选：截断过长文本，注意只用 ASCII 的三点号，避免乱码
if ($msg -and $msg.Length -gt 240) {
  $msg = $msg.Substring(0,240) + '...'
}

# 只用 Toast，不要任何 Popup 兜底
Import-Module BurntToast -ErrorAction Stop
New-BurntToastNotification -Text $title, $msg | Out-Null
