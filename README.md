# Hover

Python ve MAVSDK ile ArduPilot/ArduCopter için GUIDED moduna geçiş, ARM kontrolü ve kısa hover denemeleri.

## İçerik

- `hover.py`: bağlantı ve GPS/home konumunu bekler, GUIDED modunu MAVLink `COMMAND_LONG` ile ister, HEARTBEAT üzerinden doğrular, ARM ve kalkış komutlarını gönderir. Hedef irtifa kontrolünden sonra hover süresini bekler ve LAND komutu gönderir.
- `armtest.py`: aynı GUIDED geçişini kullanarak ARM → 5 saniye bekleme → DISARM zincirini dener. Kalkış komutu göndermez.
- `requirements.txt`: yerel geliştirme ortamındaki MAVSDK sürümü.

## Kurulum

Yerel geliştirme ortamı Python 3.13 ve MAVSDK 3.15.3 kullanır.

```powershell
git clone https://github.com/Emir-Gemici/hover.git
cd hover
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Yapılandırma

Her iki dosyadaki `system_address` değerini bağlantınıza göre düzenleyin. Mevcut değer `serial://COM7:57600` (Windows seri portu, 57600 baud).

`hover.py` içinde:

- `TARGET_ALT = 5.0`: hedef göreli irtifa, metre.
- `HOVER_TIME = 180`: bekleme süresi, saniye.
- `GUIDED_MODE = 4`: ArduCopter GUIDED modu.

`armtest.py` içinde `ARM_SURESI = 5`, motorların ARM durumunda bekleyeceği süredir. MAVLink hedef sistem/bileşen kimlikleri `1/1`, yer istasyonu kimlikleri `255/190` olarak ayarlanmıştır.

## Kullanım

**Bu betikler bağlı araca gerçek ARM, kalkış ve iniş komutları gönderir.** ARM denemesini pervaneler sökülüyken yapın. Hover denemesinden önce bağlantı, GPS/EKF, safety switch ve pre-arm kontrollerini tamamlayın; kumandadan müdahale imkânını koruyun.

Yalnızca ARM/DISARM denemesi:

```powershell
.\.venv\Scripts\python.exe armtest.py
```

Kalkış ve hover denemesi:

```powershell
.\.venv\Scripts\python.exe hover.py
```

## Mevcut sınırlar

Bu depo deneysel kontrol betikleri içerir. Bağlantı ve GPS bekleyişleri zaman aşımına sahip değildir. İrtifa kontrolünde 30 saniyelik eşik yalnızca yeni telemetri geldiğinde değerlendirilir; hedefe ulaşılamasa da betik hover bekleyişine geçer. Bağlantı kaybında veya işlem zorla kapatıldığında yazılımdaki LAND/DISARM komutlarının çalışması garanti edilmez. Araç üzerindeki failsafe yapılandırması ayrıca doğrulanmalıdır.

Araca özel `.param` dosyaları, uçuş kayıtları, sanal ortam ve IDE dosyaları Git'e dahil edilmez. Parametreler her araç için ayrıca hazırlanmalıdır.

## Donanıma bağlanmadan kontrol

```powershell
python -m py_compile hover.py armtest.py
```

Bu komut yalnızca Python sözdizimini denetler; bağlantı veya uçuş testi yapmaz.
