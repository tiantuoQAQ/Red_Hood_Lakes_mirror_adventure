# 启动游戏 → 定位窗口 → 截取该窗口区域
param([string]$Out = "E:\UserDATAxtmr\Documents\DSH\mirror-jam\tmp\window_cap.png")
$godot = 'E:\UserDATAxtmr\下载\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64.exe'
$p = Start-Process -FilePath $godot -ArgumentList @('--path','E:\UserDATAxtmr\Documents\DSH\mirror-jam','--rendering-method','gl_compatibility') -PassThru
Start-Sleep -Seconds 6
$p.Refresh()
$h = $p.MainWindowHandle
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int n);
}
"@
[W]::ShowWindow($h, 9) | Out-Null
[W]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 800
$r = New-Object W+RECT
[W]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.Right - $r.Left; $hh = $r.Bottom - $r.Top
"窗口尺寸: ${w}x${hh} @ ($($r.Left),$($r.Top))"
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap $w, $hh
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.Left, $r.Top, 0, 0, (New-Object System.Drawing.Size $w, $hh))
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
"截图: $Out"
$p.Kill()
