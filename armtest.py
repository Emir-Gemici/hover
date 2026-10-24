"""PERVANELER SÖKÜLÜ çalıştır. Kalkış yok: sadece GUIDED + ARM zincirini doğrular."""
import asyncio
import json
from mavsdk import System
from mavsdk.action import ActionError
from hover import set_guided

ARM_SURESI = 5  # saniye motor rölantide dönsün


async def run():
    drone = System(sysid=255, compid=190)
    print("Bağlanılıyor...")
    await drone.connect(system_address="serial://COM7:57600")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Bağlandı.")
            break

    print("GPS/EKF bekleniyor...")
    async for h in drone.telemetry.health():
        print(f"  global_pos={h.is_global_position_ok} home={h.is_home_position_ok}")
        if h.is_global_position_ok and h.is_home_position_ok:
            print("GPS Fix tamam.")
            break

    if not await set_guided(drone):
        return

    print("ARM ediliyor (pervaneler sökülü olmalı!)...")
    try:
        await drone.action.arm()
    except ActionError as e:
        print(f"ARM BAŞARISIZ: {e}")
        async def _st():
            async for m in drone.mavlink_direct.message("STATUSTEXT"):
                print("  FC>", json.loads(m.fields_json).get("text"))
        try:
            await asyncio.wait_for(_st(), timeout=8)
        except asyncio.TimeoutError:
            pass
        return

    print(f"ARM OK. {ARM_SURESI} sn bekleniyor...")
    await asyncio.sleep(ARM_SURESI)

    print("DISARM ediliyor...")
    try:
        await drone.action.disarm()
        print("DISARM OK. Zincir çalışıyor.")
    except ActionError as e:
        print(f"DISARM hatası: {e}  -> kumandadan disarm et!")


if __name__ == "__main__":
    asyncio.run(run())
