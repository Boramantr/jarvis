"""
Analytics Action — Kullanım analitiği ve raporlama.
Kullanım: "Günlük raporum", "Bu hafta ne kadar komut kullandım?", "Verimlilik skorum"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.usage_tracker import get_daily_stats, get_productivity_score, get_weekly_stats


def analytics_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "daily_report")

    if player:
        player.write_log(f"[Analytics] Komut: {action}")

    if action == "daily_report":
        data = get_daily_stats()
        total = data.get("total_commands", 0)
        errors = data.get("errors", 0)
        first = data.get("first_active", "?")
        last = data.get("last_active", "?")
        commands = data.get("commands", {})

        top_cmds = sorted(commands.items(), key=lambda x: x[1], reverse=True)[:5]

        lines = [
            f"📊 Günlük Rapor ({data.get('date', 'Bugün')}):",
            f"  📋 Toplam komut: {total}",
            f"  ❌ Hata: {errors}",
            f"  ⏰ Aktif süre: {first} → {last}",
        ]

        if top_cmds:
            lines.append("  🏆 En çok kullanılan komutlar:")
            for cmd, count in top_cmds:
                lines.append(f"    {cmd}: {count}x")

        apps = data.get("apps_used", {})
        if apps:
            top_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)[:5]
            lines.append("  💻 En çok kullanılan uygulamalar:")
            for app, secs in top_apps:
                if secs < 60:
                    t = f"{int(secs)}sn"
                elif secs < 3600:
                    t = f"{int(secs // 60)}dk"
                else:
                    t = f"{int(secs // 3600)}s {int((secs % 3600) // 60)}dk"
                lines.append(f"    {app}: {t}")

        return "\n".join(lines)

    elif action == "weekly_report":
        stats = get_weekly_stats()
        lines = [
            "📊 Haftalık Rapor:",
            f"  📅 Aktif gün: {stats['days_active']}/7",
            f"  📋 Toplam komut: {stats['total_commands']}",
            f"  📈 Günlük ortalama: {stats['avg_commands_per_day']:.1f} komut",
            f"  ❌ Toplam hata: {stats['total_errors']}",
        ]

        if stats["top_commands"]:
            lines.append("  🏆 Haftalık en çok komut:")
            for cmd, count in stats["top_commands"][:5]:
                lines.append(f"    {cmd}: {count}x")

        return "\n".join(lines)

    elif action == "productivity_score":
        result = get_productivity_score()
        score = result["score"]
        grade = result["grade"]

        # Score bar
        filled = int(score / 10)
        bar = "█" * filled + "░" * (10 - filled)

        lines = [
            f"🎯 Verimlilik Skoru: {score}/100 ({grade})",
            f"  [{bar}]",
        ]
        for reason in result["reasons"]:
            lines.append(f"  ✅ {reason}")

        return "\n".join(lines)

    elif action == "command_stats":
        data = get_daily_stats()
        commands = data.get("commands", {})
        if not commands:
            return "Bugün henüz komut kullanılmadı."
        sorted_cmds = sorted(commands.items(), key=lambda x: x[1], reverse=True)
        lines = [f"📊 Komut İstatistikleri (Bugün — {data.get('total_commands', 0)} toplam):"]
        for cmd, count in sorted_cmds:
            lines.append(f"  {cmd}: {count}x")
        return "\n".join(lines)

    elif action == "most_used_apps":
        data = get_daily_stats()
        apps = data.get("apps_used", {})
        if not apps:
            return "Bugün henüz uygulama kullanım verisi yok."
        sorted_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)
        lines = ["📊 Uygulama Kullanımı (Bugün):"]
        for app, secs in sorted_apps[:10]:
            if secs < 60:
                t = f"{int(secs)}sn"
            elif secs < 3600:
                t = f"{int(secs // 60)}dk"
            else:
                t = f"{int(secs // 3600)}s {int((secs % 3600) // 60)}dk"
            lines.append(f"  {app}: {t}")
        return "\n".join(lines)

    return "Geçersiz analitik komutu. Kullanılabilir: daily_report, weekly_report, productivity_score, command_stats, most_used_apps"
