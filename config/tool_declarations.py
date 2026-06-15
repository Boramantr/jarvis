"""Gemini Live için araç (tool) tanımlamaları.

main.py'den ayrı tutulur — şişkinliği önler ve düzenli kalır.
Yeni bir araç eklerken:
  1. actions/<isim>.py içine `<isim>_action(parameters, player)` yaz
  2. Buradaki TOOL_DECLARATIONS listesine entry ekle
"""

TOOL_DECLARATIONS = [
    {
        "name": "spotify_control",
        "description": "Full control over Spotify.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "open | play | pause | next | previous | volume_set | like | search_play | shuffle | repeat | current | queue | recently_played"},
                "query": {"type": "STRING"},
                "value": {"type": "STRING"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "youtube_control",
        "description": "Full control over YouTube.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "home | shorts | subscriptions | play | search | pause | fullscreen | volume_set | forward | backward | mute | speed_up | speed_down | like | next_video | previous_video | miniplayer | playlist | channel | stats"},
                "query": {"type": "STRING"},
                "value": {"type": "STRING"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "universal_remote",
        "description": "System and media controller.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "minimize | maximize | restore | play_pause | next | previous | seek_forward | seek_backward | mute"},
                "value": {"type": "STRING"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "task_manager",
        "description": "Controls Windows Task Manager and kills processes.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "kill | open | open_performance | system_info | list_processes | disk_usage | network_info | battery"},
                "target": {"type": "STRING"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "system_power",
        "description": "Controls computer power state.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"action": {"type": "STRING", "description": "shutdown | restart | sleep"}},
            "required": ["action"]
        }
    },
    {
        "name": "shutdown_jarvis",
        "description": "Shuts down JARVIS AI.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "web_search",
        "description": "Search the web for current information using Gemini or DuckDuckGo.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Search query"},
                "mode": {"type": "STRING", "description": "search | compare"},
                "items": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Items to compare"},
                "aspect": {"type": "STRING", "description": "Aspect to compare"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "reminder",
        "description": "Sets a timed reminder that will notify the user at the specified date and time.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "date": {"type": "STRING", "description": "Date in YYYY-MM-DD format"},
                "time": {"type": "STRING", "description": "Time in HH:MM format (24h)"},
                "message": {"type": "STRING", "description": "Reminder message"}
            },
            "required": ["date", "time", "message"]
        }
    },
    {
        "name": "send_message",
        "description": "Sends a message via WhatsApp, Telegram, Discord, Signal or other messaging apps.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver": {"type": "STRING", "description": "Name or contact of the recipient"},
                "message_text": {"type": "STRING", "description": "The message to send"},
                "platform": {"type": "STRING", "description": "whatsapp | telegram | discord | signal | instagram | messenger"}
            },
            "required": ["receiver", "message_text", "platform"]
        }
    },
    {
        "name": "open_app",
        "description": "Opens any application on the computer by name.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {"type": "STRING", "description": "Name of the application to open (e.g. Chrome, Spotify, VS Code)"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "weather_report",
        "description": "Shows weather information for a given city by opening a browser search.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"},
                "time": {"type": "STRING", "description": "today | tomorrow | this week (default: today)"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "window_minimizer",
        "description": "Minimizes the currently active window.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "screenshot_ocr",
        "description": "Takes a screenshot of the screen and extracts text using OCR, or analyzes/reads screen content.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "capture_and_read | capture"},
                "request": {"type": "STRING", "description": "Specific question or instruction about the screen content"},
                "monitor": {"type": "INTEGER", "description": "Monitor index (0 for primary)"}
            }
        }
    },
    {
        "name": "clipboard_manager",
        "description": "Manages clipboard history - recall past copies, search history, or clear clipboard.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "list | get | clear | copy | search"},
                "index": {"type": "INTEGER", "description": "Index of clipboard history item to recall (1 = most recent)"},
                "text": {"type": "STRING", "description": "Text to copy to clipboard"},
                "query": {"type": "STRING", "description": "Search query for clipboard history"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_search",
        "description": "Search for files across the computer by name, find recent downloads, or open found files.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "search | recent | open"},
                "query": {"type": "STRING", "description": "File name or search term"},
                "directory": {"type": "STRING", "description": "Directory to search in"},
                "hours": {"type": "INTEGER", "description": "Look back hours for recent files (default 24)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "translate",
        "description": "Translates text between any languages, detects language, or explains words.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "translate | detect | explain | multi"},
                "text": {"type": "STRING", "description": "Text to translate"},
                "target_language": {"type": "STRING", "description": "Target language (e.g. English, Japanese, Türkçe)"},
                "source_language": {"type": "STRING", "description": "Source language (optional, auto-detect if empty)"},
                "languages": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Multiple target languages for multi mode"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "calendar_manager",
        "description": "Manages personal calendar - add events, view today/week schedule, delete events.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "add | list | today | week | delete | upcoming | clear_past"},
                "title": {"type": "STRING", "description": "Event title"},
                "date": {"type": "STRING", "description": "Date (YYYY-MM-DD, tomorrow, monday, etc.)"},
                "time": {"type": "STRING", "description": "Time in HH:MM format"},
                "description": {"type": "STRING", "description": "Event description"},
                "id": {"type": "STRING", "description": "Event ID for deletion"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "currency_converter",
        "description": "Converts currencies with live exchange rates, shows gold prices, compares rates.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "convert | rates | gold | compare"},
                "amount": {"type": "STRING", "description": "Amount to convert"},
                "from": {"type": "STRING", "description": "Source currency (USD, EUR, TL, dolar, euro, etc.)"},
                "to": {"type": "STRING", "description": "Target currency"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "brightness_control",
        "description": "Controls screen brightness level.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "get | set | up | down | dim | max"},
                "value": {"type": "STRING", "description": "Brightness level 0-100 (for set action)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "night_mode",
        "description": "Controls blue light filter / night mode for eye comfort.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "on | off | warm | very_warm | candle | reset | settings"},
                "temperature": {"type": "STRING", "description": "Color temperature: warm | very_warm | candle | neutral"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "volume_mixer",
        "description": "Controls per-application volume levels - adjust individual app volumes, mute specific apps.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "list | set | mute | unmute | up | down | master_set | master_mute | master_unmute"},
                "app": {"type": "STRING", "description": "Application name (chrome, spotify, discord, etc.)"},
                "value": {"type": "STRING", "description": "Volume level 0-100"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "daily_briefing",
        "description": "Provides a daily briefing with weather, calendar events, system status, and motivation. Use when user says good morning or asks for daily summary.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "full | weather | motivation | system | calendar"}
            }
        }
    },
    {
        "name": "random_fact",
        "description": "Provides random interesting facts, quotes, riddles, historical events, jokes, or tips.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "fact | quote | word | riddle | today_in_history | joke | tip"},
                "category": {"type": "STRING", "description": "Topic category (science, space, history, nature, etc.)"}
            }
        }
    },
    {
        "name": "analytics",
        "description": "Provides usage analytics, daily/weekly reports, productivity scores, and command statistics.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "daily_report | weekly_report | productivity_score | command_stats | most_used_apps"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "game_mode",
        "description": "Activates gaming mode - kills unnecessary processes, boosts performance, enables DND. Auto-detects running games.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "activate | deactivate | auto_detect | performance_boost | status | session_summary"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "proactive_monitor",
        "description": "Controls the proactive background monitoring system (CPU, RAM, battery alerts).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "status | thresholds"}
            }
        }
    },
    {
        "name": "context_awareness",
        "description": "Checks which application is currently active, lists open windows.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "status | list_windows"}
            }
        }
    },
    {
        "name": "profession_mode",
        "description": "Switches JARVIS profession mode. Modes: normal (general), cyber (cybersecurity), architect (architecture), accountant (accounting/finance).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "mode": {"type": "STRING", "description": "normal | cyber | architect | accountant"}
            },
            "required": ["mode"]
        }
    },
    {
        "name": "password_security",
        "description": "Generates secure passwords, analyzes password strength, creates passphrases.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "generate | generate_passphrase | strength | bulk"},
                "length": {"type": "STRING", "description": "Password length (8-128)"},
                "password": {"type": "STRING", "description": "Password to analyze strength"},
                "words": {"type": "STRING", "description": "Number of words for passphrase (3-8)"},
                "type": {"type": "STRING", "description": "all | alpha | numeric | pin"},
                "count": {"type": "STRING", "description": "Number of passwords to generate (bulk mode)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "process_guard",
        "description": "Scans for suspicious processes, monitors high CPU/RAM usage, checks network connections, audits startup programs.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "scan | high_cpu | high_memory | network | startup | kill"},
                "threshold": {"type": "STRING", "description": "Threshold value for CPU% or RAM in MB"},
                "name": {"type": "STRING", "description": "Process name to kill"},
                "pid": {"type": "STRING", "description": "Process ID to kill"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "gold_tracker",
        "description": "Tracks gold, silver, and commodity prices in Turkish Lira. Shows gram, quarter, half, full gold prices.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "gold | silver | all | portfolio | add_holding | alert"},
                "type": {"type": "STRING", "description": "gram_altin | ceyrek_altin | yarim_altin | tam_altin | cumhuriyet | ons_altin"},
                "amount": {"type": "STRING", "description": "Amount for portfolio"},
                "buy_price": {"type": "STRING", "description": "Purchase price"},
                "target_price": {"type": "STRING", "description": "Alert target price"},
                "direction": {"type": "STRING", "description": "above | below for alerts"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "world_info",
        "description": "Provides country information, visa requirements for Turkish citizens, time zones, plug types, emergency numbers.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "country | time | visa | plug | emergency | safety"},
                "name": {"type": "STRING", "description": "Country or city name"},
                "destination": {"type": "STRING", "description": "Destination country for visa check"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "calorie_tracker",
        "description": "Tracks daily calorie intake with Turkish food database. Logs meals, shows daily totals, calculates BMI.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "lookup | log | today | goal | remaining | compare | bmi"},
                "food": {"type": "STRING", "description": "Food name (Turkish: lahmacun, döner, pide, etc.)"},
                "food1": {"type": "STRING", "description": "First food for comparison"},
                "food2": {"type": "STRING", "description": "Second food for comparison"},
                "portion": {"type": "STRING", "description": "küçük | normal | büyük | çift"},
                "calories": {"type": "STRING", "description": "Daily calorie goal"},
                "weight": {"type": "STRING", "description": "Weight in kg for BMI"},
                "height": {"type": "STRING", "description": "Height in cm for BMI"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "unit_converter",
        "description": "Converts between units: length, weight, volume, temperature, area, speed, data, time, cooking measurements.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "convert | temperature | cooking"},
                "value": {"type": "STRING", "description": "Value to convert"},
                "from_unit": {"type": "STRING", "description": "Source unit (kg, lb, cm, inch, cup, ml, °C, °F, etc.)"},
                "to_unit": {"type": "STRING", "description": "Target unit"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "tts_engine",
        "description": "Text-to-speech engine. Reads text aloud, reads clipboard, saves audio files. Multi-language support.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "speak | read_clipboard | read_file | save_audio | speed | list_voices | set_voice"},
                "text": {"type": "STRING", "description": "Text to speak"},
                "language": {"type": "STRING", "description": "Language code: tr, en, de, fr, es, ja, ko, ar"},
                "file_path": {"type": "STRING", "description": "File path to read"},
                "rate": {"type": "STRING", "description": "Speed: slow | normal | fast"},
                "voice_name": {"type": "STRING", "description": "Voice name to set"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "cyber_tools",
        "description": "Cybersecurity tools: CVE lookup, vulnerability calendar, security news, network scanning, port scanning, DNS check, firewall status, WiFi security.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "cve_lookup | vuln_calendar | security_news | network_scan | port_scan | dns_check | firewall_status | wifi_info | status"},
                "cve_id": {"type": "STRING", "description": "CVE ID (e.g. CVE-2024-3094)"},
                "target": {"type": "STRING", "description": "Target IP for port scan"},
                "domain": {"type": "STRING", "description": "Domain for DNS check"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "architect_tools",
        "description": "Architecture tools: area/volume calculation, material comparison, paint estimation, staircase calculation, color palettes, lighting calculation.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "area | material_compare | paint | stairs | color_palette | light | status"},
                "width": {"type": "STRING", "description": "Width in meters"},
                "length": {"type": "STRING", "description": "Length in meters"},
                "height": {"type": "STRING", "description": "Height in meters"},
                "area": {"type": "STRING", "description": "Area in m²"},
                "material1": {"type": "STRING", "description": "First material name"},
                "material2": {"type": "STRING", "description": "Second material name"},
                "style": {"type": "STRING", "description": "Color palette style: modern | skandinav | minimalist | endüstriyel | akdeniz | japon | boho | lüks"},
                "room_type": {"type": "STRING", "description": "Room type for lighting: ofis | salon | mutfak | yatak odası | banyo"},
                "type": {"type": "STRING", "description": "Paint type: iç cephe | dış cephe | tavan | astar"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "accountant_tools",
        "description": "Accounting tools: VAT/KDV calculation, tax calendar, SSI/SGK premium, payroll (gross-to-net), declaration reminders, late interest, severance pay.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "kdv | vergi_takvimi | sgk_prim | bordro | beyanname_hatirla | gecikme_faizi | kidem | status"},
                "amount": {"type": "STRING", "description": "Amount in TL"},
                "rate": {"type": "STRING", "description": "VAT rate (default 20)"},
                "mode": {"type": "STRING", "description": "dahil | hariç (VAT included or excluded)"},
                "brut": {"type": "STRING", "description": "Gross salary in TL"},
                "days": {"type": "STRING", "description": "Number of days for late interest"},
                "rate_type": {"type": "STRING", "description": "yasal | ticari | vergi (interest rate type)"},
                "years": {"type": "STRING", "description": "Working years for severance"},
                "salary": {"type": "STRING", "description": "Last gross salary for severance"},
                "month": {"type": "STRING", "description": "Month number for tax calendar"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "health_guardian",
        "description": "Tracks user health: water intake, eye rest, sleep analysis, mood trends. Use when user mentions health, water, sleep, or well-being.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "report | water | mood_trend"},
                "ml": {"type": "STRING", "description": "Water amount in ml (default 250)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "creative",
        "description": "Creative companion tools: generate ideas, brainstorm, rubber duck debugging, and journal entries.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "idea | journal_add | journal_read | rubber_duck"},
                "domain": {"type": "STRING", "description": "Domain for ideas (e.g. software, cyber, general)"},
                "text": {"type": "STRING", "description": "Text for journal entry"},
                "mood": {"type": "STRING", "description": "Mood for journal entry"},
                "count": {"type": "INTEGER", "description": "Number of journal entries to read"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "apple_integration",
        "description": "Apple iCloud integrations: AirDrop local server, find iPhone, check battery, add reminders, and login with QR code or email.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "airdrop_local | icloud_qr_auth | icloud_auth | icloud_2fa | find_iphone | find_my_web | list_devices | device_info | battery_status | add_reminder | sync_photos | status"},
                "username": {"type": "STRING", "description": "Apple ID email"},
                "password": {"type": "STRING", "description": "Apple ID password"},
                "code": {"type": "STRING", "description": "2FA code"},
                "text": {"type": "STRING", "description": "Reminder text"},
                "device_query": {"type": "STRING", "description": "Name or index of the device for device_info"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "google_workspace",
        "description": "Google Workspace & Browser tools: Gmail search, YouTube transcript/summary, Chrome tab control, Google Calendar and Drive search.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "gmail_search | youtube_summary | chrome_control | calendar_add | drive_search | translate_clipboard | status"},
                "query": {"type": "STRING", "description": "Search query"},
                "url": {"type": "STRING", "description": "YouTube URL"},
                "control": {"type": "STRING", "description": "Chrome action: new_tab | close_tab | next_tab | scroll_down"},
                "title": {"type": "STRING", "description": "Calendar event title"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "code_runner",
        "description": (
            "JOKER ARAÇ. Önceden tanımlı bir tool yetmediğinde Python/PowerShell/CMD "
            "kodu yaz ve çalıştır. stdout'u döndürür. Örnek kullanımlar: dosya "
            "listeleme, hesap, sistem sorgusu, API çağrısı, mini script. Bir şeyi "
            "'yapamam' demeden önce mutlaka bu aracı dene."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "lang": {"type": "STRING", "description": "python | powershell | cmd"},
                "code": {"type": "STRING", "description": "Çalıştırılacak kod"},
                "timeout": {"type": "INTEGER", "description": "Saniye (varsayılan 30, max 120)"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "web_fetch",
        "description": (
            "Bir URL'i indir ve içeriğini metin olarak döndür. Sayfayı okuman, "
            "özetlemen veya CSS selector ile spesifik veriyi çekmen gerektiğinde kullan. "
            "web_search'ten farkı: belirli bir URL'i gerçekten ziyaret eder."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {"type": "STRING", "description": "Hedef URL (https ile)"},
                "mode": {"type": "STRING", "description": "text | links | raw (varsayılan text)"},
                "selector": {"type": "STRING", "description": "Opsiyonel CSS selector — sadece o elementlerin metni"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "file_write",
        "description": (
            "Dosya oluştur veya mevcut dosyaya yaz. Metin, Markdown, Word (.docx) "
            "destekler. Kullanıcıya rapor, not, taslak hazırlaman gerektiğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING", "description": "Dosya yolu (göreceli ise Desktop'a yazılır)"},
                "content": {"type": "STRING", "description": "Yazılacak içerik"},
                "format": {"type": "STRING", "description": "txt | md | docx (uzantıdan otomatik anlaşılır)"},
                "title": {"type": "STRING", "description": "docx için H1 başlığı (opsiyonel)"},
                "append": {"type": "BOOLEAN", "description": "Sonuna eklemek için true"},
                "overwrite": {"type": "BOOLEAN", "description": "Mevcut dosyanın üstüne yazmak için true"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "plan_and_execute",
        "description": (
            "Çok adımlı karmaşık görevler için meta-tool. Tek bir doğal-dil hedef ver, "
            "JARVIS önce JSON adım planı üretir, sonra adımları sırayla yürütür. Örnek: "
            "'Hava durumuna bak, takvime kaydet ve özet maili yaz'. Sadece tek tool'la "
            "çözülemeyen hedeflerde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal": {"type": "STRING", "description": "Doğal dilde nihai hedef"},
                "max_steps": {"type": "INTEGER", "description": "En fazla adım (varsayılan 5, max 8)"}
            },
            "required": ["goal"]
        }
    },
    {
        "name": "architect",
        "description": (
            "SON ÇARE: Önceden tanımlı tool ve code_runner bile yetmediğinde KENDİ yeni "
            "tool'unu yaz ve sisteme ekle. Sadece kalıcı bir yetenek gerektiğinde kullan "
            "(tek seferlik iş için code_runner). Yazdığın kod ast denetiminden geçer, "
            "eval/exec yasak. Başarılı olursa anında çağırabilirsin."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tool_name": {"type": "STRING", "description": "snake_case, 3-40 karakter, benzersiz"},
                "code": {"type": "STRING", "description": "Fonksiyon GÖVDESİ (return ile). 'params' dict erişilebilir."},
                "libs": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Gerekli pip kütüphaneleri (yüklü mü kontrol edilir)"}
            },
            "required": ["tool_name", "code"]
        }
    },
    {
        "name": "update_memory",
        "description": (
            "Kullanıcının KALICI tercihlerini ve kimlik bilgilerini long_term belleğe "
            "yaz. Bu bellek HER turda prompt'a otomatik enjekte olur — yani burada "
            "kayıtlı şey JARVIS'in davranışını sürekli etkiler. "
            "MUTLAKA kullan: kullanıcı 'şunu unutma', 'bana şöyle seslen', 'şöyle hitap "
            "et', 'benim X tercihim Y', 'adım/yaşım/dilim X' tarzı bir şey dediğinde. "
            "Hitap için: category='identity', key='address_as', value='patron'."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "set | list | delete (varsayılan set)"},
                "category": {"type": "STRING", "description": "identity | preferences | projects | relationships | wishes | notes"},
                "key": {"type": "STRING", "description": "snake_case anahtar (örn. address_as, favorite_food)"},
                "value": {"type": "STRING", "description": "Kaydedilecek değer"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "vector_memory",
        "description": (
            "Semantik (anlam tabanlı) uzun süreli bellek. Geçmişten ilgili kayıtları "
            "bul (recall) veya kalıcı yeni bilgi ekle (remember). Kullanıcı 'unutma', "
            "'şunu hatırla', 'geçen sefer ne demiştik' gibi şeyler dediğinde mutlaka bunu "
            "kullan. recall sorgusu doğal dil ile yazılır."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "remember | recall | stats | clear"},
                "text": {"type": "STRING", "description": "remember için kaydedilecek içerik"},
                "query": {"type": "STRING", "description": "recall için doğal dil sorgu"},
                "kind": {"type": "STRING", "description": "note | preference | conversation | fact (varsayılan note)"},
                "k": {"type": "INTEGER", "description": "recall için sonuç sayısı (varsayılan 5)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "analyze_file",
        "description": (
            "Bir dosyayı Gemini ile multimodal analiz et. Resim (.png/.jpg), PDF, ses "
            "(.mp3/.wav), video (.mp4) veya metin dosyalarını okur ve sorulan soruya "
            "yanıt verir. 'Bu PDF'i özetle', 'Bu resimde ne var', 'Bu ses kaydında ne "
            "söyleniyor' tarzı isteklerde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING", "description": "Dosya yolu (mutlak veya göreceli)"},
                "question": {"type": "STRING", "description": "Dosya hakkındaki soru/talimat. Boşsa özetlenir."},
                "model": {"type": "STRING", "description": "Opsiyonel model adı (varsayılan gemini-2.5-flash)"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "browser_agent",
        "description": (
            "Playwright ile tarayıcıyı kontrol et: sayfaya git, butona tıkla, formu "
            "doldur, içerikten veri çek, ekran görüntüsü al. Etkileşim gerektiren web "
            "işleri için (form gönderme, scroll, login akışı) bunu kullan. Çoklu çağrıda "
            "aynı oturum sürer."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "navigate | click | fill | extract | screenshot | wait | current | close"},
                "url": {"type": "STRING", "description": "navigate için URL"},
                "selector": {"type": "STRING", "description": "CSS selector"},
                "text": {"type": "STRING", "description": "click için metin (selector yoksa)"},
                "value": {"type": "STRING", "description": "fill için değer"},
                "submit": {"type": "BOOLEAN", "description": "fill sonrası Enter bas"},
                "ms": {"type": "INTEGER", "description": "wait için milisaniye"},
                "path": {"type": "STRING", "description": "screenshot dosya yolu"},
                "full_page": {"type": "BOOLEAN", "description": "tam sayfa screenshot"},
                "headless": {"type": "BOOLEAN", "description": "true = arka planda (varsayılan false)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "macro_automator",
        "description": "Advanced PC Macro & Automation: Clicks, typing, coordinates, mouse dragging, scrolling.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "click | double_click | right_click | type | hotkey | scroll | move_to | drag_to | locate | get_position"},
                "x": {"type": "INTEGER", "description": "X coordinate"},
                "y": {"type": "INTEGER", "description": "Y coordinate"},
                "text": {"type": "STRING", "description": "Text to type or hotkey sequence"},
                "amount": {"type": "INTEGER", "description": "Scroll amount"},
                "image_name": {"type": "STRING", "description": "Image name to locate on screen"}
            },
            "required": ["action"]
        }
    }
]
