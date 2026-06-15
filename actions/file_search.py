"""
File Search Action — Bilgisayar genelinde dosya arama.
Kullanım: "Ödev.pdf dosyasını bul", "Son indirilen dosyaları göster", "Masaüstündeki resimleri bul"
"""
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def _search_with_everything(query: str, max_results: int = 15) -> list[dict]:
    """Everything Search Engine CLI ile ara (çok hızlı)."""
    try:
        result = subprocess.run(
            ["es.exe", "-n", str(max_results), "-sort", "date-modified", query],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            files = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line and os.path.exists(line):
                    stat = os.stat(line)
                    files.append({
                        "path": line,
                        "name": os.path.basename(line),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
            return files
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return []


def _search_with_walk(query: str, search_dirs: list[Path] = None, max_results: int = 15) -> list[dict]:
    """OS walk ile dosya ara (Everything yoksa fallback)."""
    if search_dirs is None:
        home = Path.home()
        search_dirs = [
            home / "Desktop",
            home / "Downloads",
            home / "Documents",
            home / "OneDrive",
        ]
        # OneDrive Desktop
        onedrive_desktop = home / "OneDrive" / "Desktop"
        if onedrive_desktop.exists():
            search_dirs.append(onedrive_desktop)
        onedrive_masaustu = home / "OneDrive" / "Masaüstü"
        if onedrive_masaustu.exists():
            search_dirs.append(onedrive_masaustu)

    query_lower = query.lower()
    results = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        try:
            for root, dirs, files in os.walk(search_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git")]

                for f in files:
                    if query_lower in f.lower():
                        full_path = os.path.join(root, f)
                        try:
                            stat = os.stat(full_path)
                            results.append({
                                "path": full_path,
                                "name": f,
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                            })
                        except Exception:
                            pass

                        if len(results) >= max_results:
                            return results
        except PermissionError:
            continue

    results.sort(key=lambda x: x["modified"], reverse=True)
    return results[:max_results]


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _recent_files(directory: Path, hours: int = 24, max_results: int = 10) -> list[dict]:
    """Son X saat içinde değiştirilen dosyaları bul."""
    cutoff = datetime.now() - timedelta(hours=hours)
    results = []

    if not directory.exists():
        return results

    try:
        for item in directory.rglob("*"):
            if item.is_file() and not item.name.startswith("."):
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime > cutoff:
                        results.append({
                            "path": str(item),
                            "name": item.name,
                            "size": item.stat().st_size,
                            "modified": mtime.strftime("%Y-%m-%d %H:%M"),
                        })
                except Exception:
                    pass
    except PermissionError:
        pass

    results.sort(key=lambda x: x["modified"], reverse=True)
    return results[:max_results]


def file_search_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "search")
    query = params.get("query", "")
    directory = params.get("directory", "")
    max_results = int(params.get("max_results", 10))

    if player:
        player.write_log(f"[FileSearch] {action}: {query}")

    if action == "search":
        if not query:
            return "Ne aramami istersiniz efendim?"

        # Önce Everything ile dene
        results = _search_with_everything(query, max_results)
        if not results:
            results = _search_with_walk(query, max_results=max_results)

        if not results:
            return f"'{query}' ile eşleşen dosya bulunamadı efendim."

        lines = [f"🔍 '{query}' için {len(results)} sonuç:"]
        for i, r in enumerate(results, 1):
            lines.append(f"  {i}. {r['name']} ({_format_size(r['size'])})")
            lines.append(f"     📁 {r['path']}")
            lines.append(f"     📅 {r['modified']}")
        return "\n".join(lines)

    elif action == "recent":
        search_dir = Path(directory) if directory else Path.home() / "Downloads"
        hours = int(params.get("hours", 24))
        results = _recent_files(search_dir, hours, max_results)

        if not results:
            return f"Son {hours} saatte yeni dosya bulunamadı."

        lines = [f"📂 Son {hours} saatteki dosyalar ({search_dir.name}):"]
        for i, r in enumerate(results, 1):
            lines.append(f"  {i}. {r['name']} ({_format_size(r['size'])}) — {r['modified']}")
        return "\n".join(lines)

    elif action == "open":
        if not query:
            return "Hangi dosyayı açmamı istersiniz?"
        results = _search_with_everything(query, 1) or _search_with_walk(query, max_results=1)
        if results:
            os.startfile(results[0]["path"])
            return f"Açılıyor: {results[0]['name']}"
        return f"'{query}' bulunamadı."

    return "Geçersiz dosya arama komutu. Kullanılabilir: search, recent, open"
