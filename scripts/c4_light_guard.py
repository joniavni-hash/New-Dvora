#!/usr/bin/env python3
"""
Control4 Light Guard — monitors specific lights and turns them OFF immediately if turned on.
Used to prevent a faulty exterior light from tripping the breaker.

Usage: python3 c4_light_guard.py [--interval 15]
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pyControl4.account import C4Account
from pyControl4.director import C4Director

# Lights to guard (item IDs)
GUARDED_LIGHTS = {
    70: "קיר בריכה",
    72: "קיר חוץ דרום",
    78: "קיר חוץ דרומי",
}

C4_EMAIL = "Yoni-a@telefire.co.il"
C4_PASSWORD = "control4u"
CONTROLLER_IP = "192.168.1.240"

async def get_director():
    account = C4Account(C4_EMAIL, C4_PASSWORD)
    await account.get_account_bearer_token()
    controllers = await account.get_account_controllers()
    cn = controllers["controllerCommonName"]
    data = await account.get_director_bearer_token(cn)
    return C4Director(CONTROLLER_IP, data["token"])

async def guard_loop(interval: int):
    director = await get_director()
    token_refresh = 0
    print(f"[{datetime.now():%H:%M:%S}] Light guard started. Monitoring {len(GUARDED_LIGHTS)} lights every {interval}s.")
    
    while True:
        try:
            # Refresh token every 30 minutes
            token_refresh += interval
            if token_refresh >= 1800:
                director = await get_director()
                token_refresh = 0
                print(f"[{datetime.now():%H:%M:%S}] Token refreshed.")
            
            for item_id, name in GUARDED_LIGHTS.items():
                try:
                    state = await director.get_item_variable_value(item_id, "LIGHT_STATE")
                    if state == 1 or state == "1" or state is True:
                        print(f"[{datetime.now():%H:%M:%S}] ⚠️  {name} (ID {item_id}) is ON — sending OFF!")
                        await director.send_post_request(
                            "/api/v1/items/{}/commands".format(item_id),
                            {"async": True},
                            {"command": "OFF", "tParams": {}}
                        )
                        print(f"[{datetime.now():%H:%M:%S}] ✅ OFF sent to {name}")
                except Exception as e:
                    print(f"[{datetime.now():%H:%M:%S}] Error checking {name}: {e}")
            
            await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            print("\nGuard stopped.")
            break
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] Loop error: {e}. Retrying in 60s...")
            await asyncio.sleep(60)
            try:
                director = await get_director()
                token_refresh = 0
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Control4 Light Guard")
    parser.add_argument("--interval", type=int, default=15, help="Check interval in seconds (default: 15)")
    args = parser.parse_args()
    asyncio.run(guard_loop(args.interval))

if __name__ == "__main__":
    main()
