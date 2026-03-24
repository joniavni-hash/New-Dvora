#!/usr/bin/env python3
"""
Villa Lithos Publishing Example - Demo of Postiz integration
"""

import os
from integrations.social.postiz_integration import PostizPublishingIntegration

def demo_villa_lithos_posting():
    """Demonstrate Villa Lithos posting workflow"""
    
    print("🏖️ Villa Lithos Publishing Demo")
    print("=" * 50)
    
    # Initialize integration
    integration = PostizPublishingIntegration()
    
    # Demo content
    villa_content = """וילה ליתוס - חופשה חלומית בפורטו רפטי! 🏖️

4 חדרי שינה מרווחים
בריכה פרטית עם נוף לים
מטבח מאובזר במלואו
5 דקות הליכה לחוף

זמין לקיץ 2026 📅
הזמינו עכשיו! 🌟"""
    
    platforms = ["tiktok", "instagram"]
    
    print(f"📝 Content: {villa_content[:50]}...")
    print(f"🎯 Target platforms: {', '.join(platforms)}")
    print()
    
    # Check system status first
    print("1. 📊 Checking system status...")
    status = integration.get_publishing_status()
    
    print(f"   Gateway health: {status.get('overall_health', 'unknown')}")
    print(f"   Postiz connected: {status['postiz']['connected']}")
    
    if not status['postiz']['connected']:
        print("   ❌ Postiz not connected")
        print("   Fix steps:")
        for step in ["Sign up at https://app.postiz.com", 
                    "Generate API key: Settings → API Keys", 
                    "Set POSTIZ_API_KEY environment variable"]:
            print(f"     • {step}")
        print()
    else:
        print(f"   ✅ Connected accounts: {status['postiz']['connected_platforms']}")
        print()
    
    # Simulate posting (will fail without credentials, but shows workflow)
    print("2. 🚀 Creating Villa Lithos post...")
    
    # This will fail gracefully without credentials
    result = integration.create_villa_lithos_post(
        content=villa_content,
        platforms=platforms,
        media_paths=[]  # Would include villa photos/videos
    )
    
    if result["success"]:
        print("   ✅ Post created successfully!")
        print(f"   Draft ID: {result['draft_id']}")
        print(f"   Postiz ID: {result['postiz_post_id']}")
        print(f"   Platforms: {', '.join(result['platforms'])}")
        print(f"   URL: {result['postiz_url']}")
    else:
        print("   📋 Post workflow demonstrated (would work with proper credentials)")
        print(f"   Expected error: {result['error']}")
        
        if "fix_instructions" in result:
            print("   Next steps to enable:")
            for instruction in result["fix_instructions"]:
                print(f"     • {instruction}")
    
    print()
    print("3. 📈 What happens after setup:")
    print("   ✅ Villa content automatically branded with hashtags")
    print("   ✅ Multi-platform validation (Instagram + TikTok)")
    print("   ✅ Auto-approval for Villa Lithos content") 
    print("   ✅ Instant publishing via Postiz")
    print("   ✅ Performance tracking and analytics")
    print()
    
    # Show branded content
    branded = integration._add_villa_branding(villa_content)
    print("4. 🏷️ Branded content preview:")
    print(f"   {branded}")
    print()
    
    print("🎯 Ready for production with Postiz credentials!")

if __name__ == "__main__":
    demo_villa_lithos_posting()