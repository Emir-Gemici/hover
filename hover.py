import asyncio
import json
import time
from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.mavlink_direct import MavlinkMessage, MavlinkDirectError

TARGET_ALT = 5.0    # metre - alçak hover testi
HOVER_TIME = 180    # saniye

GUIDED_MODE = 4    # ArduCopter GUIDED (mode_mapping_acm)
MAV_CMD_DO_SET_MODE = 176
CUSTOM_MODE_ENABLED = 1   # MAV_MODE_FLAG_CUSTOM_MODE_ENABLED


async def set_guided(drone, timeout=15):
    """ArduPilot'u yazilimla GUIDED moduna alir. Basarili olursa True."""
    print("GUIDED moduna geciliyor...")
    fields = json.dumps({
        "target_system": 1,
        "target_component": 1,
        "command": MAV_CMD_DO_SET_MODE,
        "confirmation": 0,
        "param1": CUSTOM_MODE_ENABLED,
        "param2": GUIDED_MODE,
        "param3": 0, "param4": 0, "param5": 0, "param6": 0, "param7": 0,
    })

    async def _confirm():
        # HEARTBEAT.custom_mode == 4 olana kadar bekle (ArduPilot 1 Hz yollar)
        async for msg in drone.mavlink_direct.message("HEARTBEAT"):
            try:
                if json.loads(msg.fields_json).get("custom_mode") == GUIDED_MODE:
                    return True
            except (ValueError, AttributeError):
                continue
        return False

    start = time.time()
    while time.time() - start < timeout:
        try:
            await drone.mavlink_direct.send_message(MavlinkMessage(
                message_name="COMMAND_LONG",
                system_id=0, component_id=0,
                target_system_id=1, target_component_id=1,
                fields_json=fields,
            ))
        except MavlinkDirectError as e:
            print(f"Mod komutu gonderilemedi: {e}")
            return False

        try:
            if await asyncio.wait_for(_confirm(), timeout=3):
                print("GUIDED aktif!")
                return True
        except asyncio.TimeoutError:
            print("  GUIDED teyidi bekleniyor...")

    print("GUIDED moduna gecilemedi. (Pre-Arm / EKF / GPS kontrol et.)")
    return False

async def run():
    # sysid=255 -> ArduPilot bunu SYSID_MYGCS olarak taniyip GCS failsafe'i besler
    drone = System(sysid=255, compid=190)
    print("İHA'ya bağlanılıyor...")
    await drone.connect(system_address="serial://COM7:57600")

    print("Telemetri bağlantısı bekleniyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("İHA bağlantısı kuruldu!")
            break

    print("GPS Fix bekleniyor...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("GPS Fix tamam!")
            break

    # >>> ArduPilot: takeoff SADECE GUIDED modda çalışır. MAVSDK otomatik yapmaz.
    # Modu GUIDED'a aldığından emin ol, yoksa takeoff() COMMAND_DENIED fırlatır.

    if not await set_guided(drone):
        return

    print("ARM ediliyor...")
    try:
        await drone.action.arm()
        print("Motorlar çalıştırıldı!")
    except ActionError as e:
        print(f"ARM Başarısız: {e}")
        print("TAVSİYE: Safety switch + Pre-Arm kontrol et.")
        return

    try:
        print(f"{TARGET_ALT} metreye kalkış...")
        await drone.action.set_takeoff_altitude(TARGET_ALT)
        await drone.action.takeoff()

        # Komut kabul edilince döner; gerçekten yükseldiğini teyit et
        start = time.time()
        async for pos in drone.telemetry.position():
            print(f"  Yükseklik: {pos.relative_altitude_m:.1f} m")
            if pos.relative_altitude_m >= TARGET_ALT - 0.15:
                print(f"{TARGET_ALT} metreye ulaşıldı!")
                break
            if time.time() - start > 30:
                print("Uyarı: 30 sn'de hedefe ulaşılamadı.")
                break

        print(f"{HOVER_TIME} saniye hover testi...")
        await asyncio.sleep(HOVER_TIME)

    except ActionError as e:
        print(f"Kalkış/uçuş hatası: {e}")

    finally:
        print("İniş (LAND)...")
        try:
            await drone.action.land()

            async def _inis_bekle():
                async for in_air in drone.telemetry.in_air():
                    if not in_air:
                        return True
                return False

            try:
                await asyncio.wait_for(_inis_bekle(), timeout=60)
                print("İniş tamamlandı, motorlar disarm.")
            except asyncio.TimeoutError:
                print("Uyarı: 60 sn'de iniş teyidi alınamadı (LAND komutu gönderildi).")
        except ActionError as e:
            print(f"İniş hatası: {e}")

if __name__ == "__main__":
    asyncio.run(run())
