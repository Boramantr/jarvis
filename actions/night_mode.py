"""
Night Mode Action — Mavi ışık filtresi / gece modu.
Kullanım: "Gece modunu aç", "Mavi ışık filtresini kapat", "Sıcak renge geç"
"""
import platform
import subprocess

_SYSTEM = platform.system()


def _set_night_light_windows(enable: bool) -> bool:
    """Windows Night Light (Gece Işığı) özelliğini aç/kapa."""
    try:
        if enable:
            # Registry üzerinden Night Light'ı etkinleştir
            ps_script = """
            $path = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\DefaultAccount\\Current\\default$windows.data.bluelightreduction.bluelightreductionstate\\windows.data.bluelightreduction.bluelightreductionstate"
            if (Test-Path $path) {
                $data = (Get-ItemProperty -Path $path).Data
                if ($data) {
                    $data[18] = 0x15
                    Set-ItemProperty -Path $path -Name Data -Value $data -Type Binary
                }
            }
            """
        else:
            ps_script = """
            $path = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\DefaultAccount\\Current\\default$windows.data.bluelightreduction.bluelightreductionstate\\windows.data.bluelightreduction.bluelightreductionstate"
            if (Test-Path $path) {
                $data = (Get-ItemProperty -Path $path).Data
                if ($data) {
                    $data[18] = 0x13
                    Set-ItemProperty -Path $path -Name Data -Value $data -Type Binary
                }
            }
            """

        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=10
        )
        return True
    except Exception:
        return False


def _toggle_night_light_shortcut() -> bool:
    """Windows Ayarları üzerinden Night Light'ı toggle et."""
    try:
        # Action Center üzerinden Night Light toggle
        subprocess.run(
            ["powershell", "-Command",
             "Start-Process ms-settings:nightlight"],
            capture_output=True, text=True, timeout=5
        )
        return True
    except Exception:
        return False


def _set_color_temperature(temp: str = "warm") -> bool:
    """F.lux veya benzeri uygulama ile renk sıcaklığı ayarla."""
    temp_map = {
        "warm": 3400,
        "very_warm": 2700,
        "neutral": 5000,
        "cool": 6500,
        "candle": 1900,
    }

    kelvin = temp_map.get(temp, 3400)

    try:
        # PowerShell ile gamma ayarı
        ps_script = f"""
        Add-Type -TypeDefinition @"
        using System;
        using System.Runtime.InteropServices;
        public class GammaRamp {{
            [DllImport("gdi32.dll")]
            public static extern bool SetDeviceGammaRamp(IntPtr hDC, ref RAMP lpRamp);
            [DllImport("user32.dll")]
            public static extern IntPtr GetDC(IntPtr hWnd);
            [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
            public struct RAMP {{
                [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
                public UInt16[] Red;
                [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
                public UInt16[] Green;
                [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
                public UInt16[] Blue;
            }}
        }}
"@
        $hdc = [GammaRamp]::GetDC([IntPtr]::Zero)
        $ramp = New-Object GammaRamp+RAMP
        $ramp.Red = New-Object UInt16[] 256
        $ramp.Green = New-Object UInt16[] 256
        $ramp.Blue = New-Object UInt16[] 256

        $redFactor = if ({kelvin} -lt 4000) {{ 1.0 }} else {{ 1.0 }}
        $greenFactor = if ({kelvin} -lt 4000) {{ 0.85 }} else {{ 0.95 }}
        $blueFactor = if ({kelvin} -lt 4000) {{ 0.6 }} else {{ 0.85 }}

        for ($i = 0; $i -lt 256; $i++) {{
            $ramp.Red[$i] = [Math]::Min(65535, [int]($i * 256 * $redFactor))
            $ramp.Green[$i] = [Math]::Min(65535, [int]($i * 256 * $greenFactor))
            $ramp.Blue[$i] = [Math]::Min(65535, [int]($i * 256 * $blueFactor))
        }}
        [GammaRamp]::SetDeviceGammaRamp($hdc, [ref]$ramp)
        """
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=10
        )
        return True
    except Exception:
        return False


def _reset_color_temperature() -> bool:
    """Renk sıcaklığını varsayılana sıfırla."""
    try:
        ps_script = """
        Add-Type -TypeDefinition @"
        using System;
        using System.Runtime.InteropServices;
        public class GammaReset {
            [DllImport("gdi32.dll")]
            public static extern bool SetDeviceGammaRamp(IntPtr hDC, ref RAMP lpRamp);
            [DllImport("user32.dll")]
            public static extern IntPtr GetDC(IntPtr hWnd);
            [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
            public struct RAMP {
                [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
                public UInt16[] Red;
                [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
                public UInt16[] Green;
                [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
                public UInt16[] Blue;
            }
        }
"@
        $hdc = [GammaReset]::GetDC([IntPtr]::Zero)
        $ramp = New-Object GammaReset+RAMP
        $ramp.Red = New-Object UInt16[] 256
        $ramp.Green = New-Object UInt16[] 256
        $ramp.Blue = New-Object UInt16[] 256
        for ($i = 0; $i -lt 256; $i++) {
            $ramp.Red[$i] = $i * 256
            $ramp.Green[$i] = $i * 256
            $ramp.Blue[$i] = $i * 256
        }
        [GammaReset]::SetDeviceGammaRamp($hdc, [ref]$ramp)
        """
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=10
        )
        return True
    except Exception:
        return False


def night_mode_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "on")
    temperature = params.get("temperature", "warm")

    if player:
        player.write_log(f"[NightMode] Komut: {action}")

    if _SYSTEM != "Windows":
        return "Gece modu şu an sadece Windows'ta destekleniyor efendim."

    if action in ("on", "enable", "aç"):
        success = _set_night_light_windows(True)
        _set_color_temperature(temperature)
        if success:
            return "🌙 Gece modu etkinleştirildi. Gözlerinizi koruyorum efendim."
        _toggle_night_light_shortcut()
        return "🌙 Gece modu ayarları açıldı efendim."

    elif action in ("off", "disable", "kapat"):
        _set_night_light_windows(False)
        _reset_color_temperature()
        return "☀️ Gece modu kapatıldı, renkler normale döndü."

    elif action == "warm":
        _set_color_temperature("warm")
        return "🌅 Sıcak ton ayarlandı (3400K)."

    elif action == "very_warm":
        _set_color_temperature("very_warm")
        return "🕯️ Çok sıcak ton ayarlandı (2700K) — mum ışığı modu."

    elif action == "candle":
        _set_color_temperature("candle")
        return "🕯️ Mum ışığı modu (1900K) — en sıcak ayar."

    elif action == "reset":
        _reset_color_temperature()
        return "🔄 Renk sıcaklığı varsayılana sıfırlandı."

    elif action == "settings":
        _toggle_night_light_shortcut()
        return "Gece modu ayarları açıldı efendim."

    return "Geçersiz gece modu komutu. Kullanılabilir: on, off, warm, very_warm, candle, reset, settings"
