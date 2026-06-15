import sys

try:
    from pyicloud import PyiCloudService
except Exception as e:
    print(f"HATA: pyicloud kütüphanesi yüklenemedi. Sorun: {e}")
    sys.exit(1)

def main():
    email = "boraocaker38@gmail.com"
    password = "HGM6F48fyx@"

    print("========================================")
    print("🍏 JARVIS - iCloud Manuel Test Aracı")
    print("========================================")
    print(f"Giriş yapılıyor: {email} ...")

    try:
        api = PyiCloudService(email, password)
    except Exception as e:
        print(f"❌ Apple sunucularına bağlanırken hata oluştu: {e}")
        return

    if api.requires_2fa:
        print("\n⚠️ Apple, bu giriş için 2 Aşamalı Doğrulama (2FA) istiyor.")
        print("Lütfen iPhone veya iPad'inize bakın. 'İzin Ver' butonuna bastıktan sonra ekranda 6 haneli bir kod göreceksiniz.")

        code = input("Lütfen 6 haneli kodu buraya yazın ve Enter'a basın: ")

        print("\nKod doğrulanıyor...")
        result = api.validate_2fa_code(code)

        if result:
            print("✅ Doğrulama BAŞARILI! Cihazlarınıza erişildi.\n")
        else:
            print("❌ Kod hatalı. Lütfen daha sonra tekrar deneyin.")
            return
    else:
        print("✅ Başarıyla giriş yapıldı. (2FA gerekmedi)\n")

    print("📱 Hesabınıza Bağlı Cihazlar:")
    for device in api.devices:
        name = device.data.get('name', 'Bilinmeyen Cihaz')
        battery_level = device.data.get('batteryLevel')
        percent = int(battery_level * 100) if battery_level is not None else "Bilinmiyor"

        print(f"  • {name} - Batarya: %{percent}")

    print("\nTest tamamlandı. Bu sayfayı kapatıp JARVIS'e dönebilirsiniz.")

if __name__ == "__main__":
    main()
