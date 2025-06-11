
param (
    [string]$action = "minimize",  # Default action is minimize
    [string]$windowHandle = ""     # Optional window handle for specific targeting
)

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Drawing;
public class WindowHelper {
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    
    [DllImport("user32.dll")]
    public static extern bool IsWindow(IntPtr hWnd);
    
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    
    [DllImport("user32.dll")]
    public static extern bool BringWindowToTop(IntPtr hWnd);
    
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern IntPtr SendMessage(IntPtr hWnd, UInt32 Msg, IntPtr wParam, IntPtr lParam);
    
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool GetCursorPos(out POINT lpPoint);
    
    [DllImport("user32.dll")]
    public static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo);
    
    [DllImport("user32.dll", SetLastError = true)]
    public static extern int GetWindowLong(IntPtr hWnd, int nIndex);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
    
    [StructLayout(LayoutKind.Sequential)]
    public struct POINT
    {
        public int X;
        public int Y;
    }
    
    // Constants for mouse_event
    public const int MOUSEEVENTF_LEFTDOWN = 0x02;
    public const int MOUSEEVENTF_LEFTUP = 0x04;
    
    // Constants for SendMessage
    public const int WM_ACTIVATE = 0x0006;
    public const int WA_ACTIVE = 1;
    
    // Constants for GetWindowLong
    public const int GWL_STYLE = -16;
    public const int WS_CAPTION = 0x00C00000;
}
"@

# If no specific window handle provided, use the currently active window
$hwnd = $null
if ($windowHandle -eq "") {
    $hwnd = [WindowHelper]::GetForegroundWindow()
    # Save current window handle to file for later reference
    if ($action -eq "save") {
        # Also save cursor position
        $cursorPos = New-Object WindowHelper+POINT
        [WindowHelper]::GetCursorPos([ref]$cursorPos)
        
        "$($hwnd.ToInt64())|$($cursorPos.X)|$($cursorPos.Y)" | Out-File -FilePath "$PSScriptRoot\prev_window_handle.txt"
        exit
    }
} else {
    $hwnd = [IntPtr]::new([long]$windowHandle)
}

switch ($action) {
    "minimize" { [WindowHelper]::ShowWindow($hwnd, 6) }  # SW_MINIMIZE = 6
    "maximize" { [WindowHelper]::ShowWindow($hwnd, 3) }  # SW_MAXIMIZE = 3
    "restore"  { [WindowHelper]::ShowWindow($hwnd, 9) }  # SW_RESTORE = 9
    "hide"     { [WindowHelper]::ShowWindow($hwnd, 0) }  # SW_HIDE = 0
    "focus"    { 
        if ([WindowHelper]::IsWindow($hwnd)) {
            # Try multiple focus methods
            [WindowHelper]::SetForegroundWindow($hwnd)
            [WindowHelper]::BringWindowToTop($hwnd)
            [WindowHelper]::SendMessage($hwnd, [WindowHelper]::WM_ACTIVATE, [IntPtr][WindowHelper]::WA_ACTIVE, [IntPtr]::Zero)
            
            # Get window position for clicking
            $rect = New-Object WindowHelper+RECT
            [WindowHelper]::GetWindowRect($hwnd, [ref]$rect)
            
            # Save current cursor position
            $cursorPos = New-Object WindowHelper+POINT
            [WindowHelper]::GetCursorPos([ref]$cursorPos)
            
            # Add Forms assembly for cursor control
            Add-Type -AssemblyName System.Windows.Forms
            
            # Click on title bar area - specifically in the middle of left third of title bar
            # This avoids close, minimize, maximize buttons on the right
            $titleBarX = $rect.Left + ($rect.Right - $rect.Left) / 6  # 1/6 of the way from left
            $titleBarY = $rect.Top + 15  # Approximately in the middle of the title bar
            
            # Move cursor and click
            [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($titleBarX, $titleBarY)
            [WindowHelper]::mouse_event([WindowHelper]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            [WindowHelper]::mouse_event([WindowHelper]::MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            # Return cursor to original position
            [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($cursorPos.X, $cursorPos.Y)
        }
    }
    "restoreFocus" {
        if (Test-Path "$PSScriptRoot\prev_window_handle.txt") {
            $savedData = Get-Content "$PSScriptRoot\prev_window_handle.txt"
            $parts = $savedData.Split('|')
            
            if ($parts.Length -ge 1) {
                $prevHandle = [IntPtr]::new([long]$parts[0])
                
                if ([WindowHelper]::IsWindow($prevHandle)) {
                    # Try multiple focus methods
                    [WindowHelper]::SetForegroundWindow($prevHandle)
                    [WindowHelper]::BringWindowToTop($prevHandle)
                    [WindowHelper]::SendMessage($prevHandle, [WindowHelper]::WM_ACTIVATE, [IntPtr][WindowHelper]::WA_ACTIVE, [IntPtr]::Zero)
                    
                    # Get window position
                    $rect = New-Object WindowHelper+RECT
                    [WindowHelper]::GetWindowRect($prevHandle, [ref]$rect)
                    
                    # Save current cursor position first
                    $cursorPos = New-Object WindowHelper+POINT
                    [WindowHelper]::GetCursorPos([ref]$cursorPos)
                    
                    # Add Forms assembly for cursor control
                    Add-Type -AssemblyName System.Windows.Forms
                    
                    # Click on title bar area - specifically the left third of the title bar
                    # to avoid any control buttons (close, minimize, maximize)
                    $titleBarX = $rect.Left + ($rect.Right - $rect.Left) / 6  # 1/6 of the way from left
                    $titleBarY = $rect.Top + 15  # Approximately in the middle of the title bar
                    
                    # Move cursor and click
                    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($titleBarX, $titleBarY)
                    [WindowHelper]::mouse_event([WindowHelper]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    [WindowHelper]::mouse_event([WindowHelper]::MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    
                    # Return cursor to original position
                    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($cursorPos.X, $cursorPos.Y)
                }
            }
        }
    }
    default    { [WindowHelper]::ShowWindow($hwnd, 6) }  # Default to minimize
}
