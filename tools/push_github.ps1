# 一键推送脚本（网络可访问 GitHub 时运行）
# 用法：powershell -ExecutionPolicy Bypass -File tools/push_github.ps1
#       如果需要代理：powershell -ExecutionPolicy Bypass -File tools/push_github.ps1 -Proxy "http://127.0.0.1:7890"

param(
    [string]$Proxy = ""
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if ($Proxy -ne "") {
    Write-Host "使用代理: $Proxy"
    $env:HTTP_PROXY = $Proxy
    $env:HTTPS_PROXY = $Proxy
    git config http.proxy $Proxy
} else {
    git config --unset http.proxy 2>$null
}

# 大仓库推送参数（避免 RPC 失败）
git config http.postBuffer 524288000
git config http.version HTTP/1.1
git config http.lowSpeedLimit 1000
git config http.lowSpeedTime 300

$branch = git branch --show-current
Write-Host "当前分支: $branch"

for ($i = 1; $i -le 5; $i++) {
    Write-Host "第 $i 次尝试推送..."
    git push origin $branch --no-thin
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 推送成功: https://github.com/tiantuoQAQ/Red_Hood_Lakes_mirror_adventure"
        exit 0
    }
    Start-Sleep -Seconds 5
}

Write-Host "❌ 5 次尝试都失败。可选方案："
Write-Host "1) 挂代理后重跑： -Proxy 'http://127.0.0.1:7890'"
Write-Host "2) 用 GitHub Desktop 直接 Publish/Push 本仓库"
Write-Host "3) 用生成的 bundle 文件在别的网络环境 restore 后推送"
exit 1
