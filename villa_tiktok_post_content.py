#!/usr/bin/env python3
"""
Villa Lithos TikTok Content - טלי's Larry-Style Posts
"""

import sys
import os
sys.path.append('integrations/social')

from postiz_real import publish_villa_lithos_post, check_connection
from datetime import datetime

# Larry-style TikTok content variations
LARRY_HOOKS = [
    {
        "hook": "Villa that costs LESS per person than a hotel room",
        "caption": """Villa that costs LESS per person than a hotel room! 🏖️

When 22 friends split Villa Lithos:
✨ Luxury for LESS than hotels  
✨ 15 min from Athens airport
✨ Private infinity pool & sea views
✨ Padel court + gym included

Book your Greek paradise! 🇬🇷

#VillaLithos #PortoRafti #Greece #GroupTravel #LuxuryVilla #GreekIslands #VillaRental #TravelHack #LuxuryTravel #GreekVacation""",
        "time": "prime" # 21:30 IST
    },
    {
        "hook": "POV: Your group trip costs less than everyone thinks", 
        "caption": """POV: Your group trip costs less than everyone thinks 😍

Villa Lithos breakdown:
🏖️ 22 friends = €35/person/night
🏨 Athens hotel = €80/person/night

You get:
• Private infinity pool
• 15 min from airport
• Padel court & gym
• Sea views & privacy

Villa > Hotel EVERY TIME! ✈️

#POV #GroupTravel #VillaLithos #TravelMath #LuxuryForLess #Greece #PortoRafti #TravelHack""",
        "time": "afternoon" # 14:00 IST
    },
    {
        "hook": "This luxury villa has a PRIVATE padel court",
        "caption": """This luxury villa has a PRIVATE padel court! 🎾

Villa Lithos features:
🎾 Private padel court
🏊‍♀️ Infinity pool overlooking sea
🏋️‍♂️ Fully equipped gym
🛏️ 11 bedrooms (up to 22 guests)
✈️ 15 minutes from Athens airport

When your villa has better amenities than a resort! 🏖️

#PadelCourt #LuxuryVilla #VillaLithos #GreekVilla #PortoRafti #VillaAmenities #GroupTravel #LuxuryTravel""",
        "time": "prime"
    },
    {
        "hook": "15 minutes from Athens airport but feels like paradise",
        "caption": """15 minutes from Athens airport but feels like paradise! ✈️🏖️

Villa Lithos location advantage:
✈️ Quick airport transfer (no long drives!)
🏖️ Private beach access Porto Rafti
🏛️ Day trips to Athens (15 min)
🚗 Easy rental car pickup
🛍️ Shopping in Rafina (10 min)

Convenience meets paradise! 🇬🇷

#Athens #PortoRafti #VillaLithos #GreekVilla #AirportClose #ConvenientLuxury #GreekIslands""",
        "time": "afternoon"
    },
    {
        "hook": "When your Airbnb has an infinity pool AND private beach access",
        "caption": """When your Airbnb has an infinity pool AND private beach access! 🏊‍♀️🏖️

Villa Lithos vibes:
🌅 Infinity pool with sunrise views
🏖️ Private beach path (2 min walk)  
🍷 Pool bar & outdoor dining
🛥️ Boat trips from Porto Rafti
🌊 Crystal clear Aegean waters

This is NOT your average rental! ✨

#InfinityPool #PrivateBeach #VillaLithos #LuxuryVibes #AegeanSea #GreekParadise #NotYourAverage""",
        "time": "prime"
    },
    {
        "hook": "22 friends split this Greek paradise",
        "caption": """22 friends split this Greek paradise! 👥🏖️

The math that makes luxury affordable:
🏖️ Villa Lithos total: €770/night
👥 Split 22 ways = €35/person
🏨 Athens hotel = €80/person minimum

You save €45/person while getting:
• Private villa experience
• Infinity pool & padel court
• Sea views & beach access
• Group memories for LIFE! 🇬🇷

#GroupTravel #SplitTheCost #VillaLithos #TravelMath #LuxuryForLess #FriendsTrip #GreekVacation""",
        "time": "afternoon" 
    }
]

def create_tali_tiktok_post(hook_index: int = 0, post_now: bool = True):
    """Create and post Villa Lithos TikTok content as טלי"""
    
    print("🏖️ טלי Creating Villa Lithos TikTok Content!")
    print("=" * 50)
    
    # Check Postiz connection
    connection = check_connection()
    print(f"📡 Postiz Status: {connection['status']}")
    
    if not connection['connected']:
        print("❌ Postiz not connected!")
        for error in connection['errors']:
            print(f"   • {error}")
        return False
    
    # Get platforms info
    platforms_info = connection['platforms']
    print(f"🔗 Connected Platforms: {list(platforms_info.keys())}")
    
    # Select content variation
    if hook_index >= len(LARRY_HOOKS):
        hook_index = 0
    
    selected_content = LARRY_HOOKS[hook_index]
    print(f"🎯 Selected Hook: {selected_content['hook']}")
    print(f"⏰ Target Time: {selected_content['time']}")
    
    # Prepare image paths (Larry slides)
    image_paths = []
    slides_dir = "integrations/social/villa_slides_test/"
    
    for i in range(1, 7):  # 6 Larry slides
        slide_path = f"{slides_dir}larry-slide-{i:02d}.png"
        if os.path.exists(slide_path):
            image_paths.append(slide_path)
    
    if not image_paths:
        print("❌ No Larry slides found!")
        return False
    
    print(f"📸 Found {len(image_paths)} Larry slides")
    
    # Publish content
    result = publish_villa_lithos_post(
        content=selected_content['caption'],
        platforms=["tiktok", "instagram"],  # Cross-platform posting
        image_paths=image_paths,
        schedule_time=None if post_now else None,  # Post immediately
        use_clean_images=True,
        skip_tiktok=False
    )
    
    print("\n📊 Posting Results:")
    print(f"Success: {result.get('success', False)}")
    
    if result['success']:
        print("✅ TikTok content posted successfully!")
        print(f"📈 Platform Results:")
        for platform, data in result['platform_results'].items():
            if data['success']:
                print(f"   ✅ {platform}: Posted")
            else:
                print(f"   ❌ {platform}: {data.get('error', 'Failed')}")
    else:
        print("❌ Posting failed!")
        for error in result.get('errors', []):
            print(f"   • {error}")
    
    return result['success']

def show_content_calendar():
    """Show טלי's content calendar"""
    
    print("📅 טלי's Villa Lithos Content Calendar")
    print("=" * 50)
    
    schedule = {
        "Monday": {"time": "21:30", "hook": 0, "focus": "Monday motivation"},
        "Tuesday": {"time": "14:00", "hook": 5, "focus": "Cost-splitting"},  
        "Wednesday": {"time": "21:30", "hook": 3, "focus": "Location selling"},
        "Thursday": {"time": "14:00", "hook": 2, "focus": "Amenities showcase"},
        "Friday": {"time": "21:30", "hook": 4, "focus": "Weekend vibes"},
        "Saturday": {"time": "14:00", "hook": 1, "focus": "Visual storytelling"},
        "Sunday": {"time": "21:30", "hook": 4, "focus": "Sunday serenity"}
    }
    
    for day, info in schedule.items():
        hook_text = LARRY_HOOKS[info['hook']]['hook']
        print(f"{day:>9} {info['time']} | {hook_text[:40]}... | {info['focus']}")

def tali_daily_automation():
    """טלי's daily automation - post based on day of week"""
    
    day_index = datetime.now().weekday()  # 0=Monday, 6=Sunday
    hook_mapping = [0, 5, 3, 2, 4, 1, 4]  # Monday to Sunday hook indexes
    
    selected_hook = hook_mapping[day_index]
    
    print(f"🗓️ Today's automated post (hook #{selected_hook})")
    return create_tali_tiktok_post(hook_index=selected_hook, post_now=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="טלי's Villa Lithos TikTok Marketing")
    parser.add_argument("--hook", type=int, default=0, help="Hook index (0-5)")
    parser.add_argument("--calendar", action="store_true", help="Show content calendar")
    parser.add_argument("--auto", action="store_true", help="Auto-post based on day")
    parser.add_argument("--test", action="store_true", help="Test Postiz connection")
    
    args = parser.parse_args()
    
    if args.calendar:
        show_content_calendar()
    elif args.auto:
        tali_daily_automation()
    elif args.test:
        connection = check_connection()
        print(f"Connection Status: {connection}")
    else:
        create_tali_tiktok_post(hook_index=args.hook)