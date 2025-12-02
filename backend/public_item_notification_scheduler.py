"""
TraceBack Public Item Notification Scheduler
Checks for items that just became public (after 72 hours) and sends email notifications
"""

import sqlite3
import schedule
import time
from datetime import datetime, timedelta
from email_notification_service import EmailNotificationService
import pytz

# ET timezone
ET = pytz.timezone('America/New_York')

def get_et_now():
    """Get current time in ET timezone"""
    return datetime.now(ET)

DB_PATH = 'traceback_100k.db'
notification_service = EmailNotificationService(DB_PATH)

# Track items we've already notified about
notified_items = set()

def check_and_notify_public_items():
    """
    Check for found items that just became public (72 hours passed)
    and send email notifications to all users except the finder
    """
    try:
        print(f"\n🔍 [{get_et_now().strftime('%Y-%m-%d %H:%M:%S ET')}] Checking for newly public items...")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find items that:
        # 1. Are older than 72 hours (3 days) - past privacy period
        # 2. Have NO potential claimers (no claim_attempts with success=1)
        # 3. Became public within the last hour (so we notify once)
        # Only send emails for items that are ACTUALLY visible in public found items page
        # If there's even ONE potential claimer (success=1), item goes to claimed items 3-day window, so NO email
        cursor.execute("""
            SELECT 
                f.id, 
                f.title, 
                f.created_at,
                f.finder_email,
                julianday('now', 'localtime') - julianday(f.created_at) as hours_since_created
            FROM found_items f
            LEFT JOIN claim_attempts ca ON f.id = ca.found_item_id AND ca.success = 1
            WHERE ca.attempt_id IS NULL
            AND datetime(f.created_at) <= datetime('now', 'localtime', '-3 days')
            AND datetime(f.created_at) >= datetime('now', 'localtime', '-3 days', '-1 hours')
            ORDER BY f.created_at DESC
        """)
        
        items = cursor.fetchall()
        conn.close()
        
        new_public_items = []
        for item in items:
            if item['id'] not in notified_items:
                new_public_items.append(item)
                notified_items.add(item['id'])
        
        if new_public_items:
            print(f"📧 Found {len(new_public_items)} newly public items to notify about:")
            
            for item in new_public_items:
                hours = item['hours_since_created'] * 24  # Convert days to hours
                print(f"   - Item #{item['id']}: '{item['title']}' (public for {hours:.1f} hours)")
                
                # Send notifications
                notification_service.notify_users_of_public_item(item['id'])
            
            print(f"✅ Notification process initiated for {len(new_public_items)} items")
        else:
            print("✓ No new public items found")
            
    except Exception as e:
        print(f"❌ Error in check_and_notify_public_items: {e}")
        import traceback
        traceback.print_exc()


def load_already_notified_items():
    """
    Load items that are already public so we don't notify about old items on startup
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all items that are already past 72 hours (so we don't notify about them on startup)
        # Only include items with NO potential claimers (truly public, not in 3-day window)
        cursor.execute("""
            SELECT f.id 
            FROM found_items f
            LEFT JOIN claim_attempts ca ON f.id = ca.found_item_id AND ca.success = 1
            WHERE datetime(f.created_at) <= datetime('now', 'localtime', '-3 days')
            AND ca.attempt_id IS NULL
        """)
        
        items = cursor.fetchall()
        conn.close()
        
        for item in items:
            notified_items.add(item[0])
        
        print(f"📋 Loaded {len(notified_items)} already-public items (will not notify)")
        
    except Exception as e:
        print(f"⚠️  Error loading already notified items: {e}")


def run_scheduler():
    """Run the notification scheduler"""
    print("=" * 80)
    print("🚀 TraceBack Public Item Notification Scheduler")
    print("=" * 80)
    print(f"Started at: {get_et_now().strftime('%Y-%m-%d %H:%M:%S ET')}")
    print(f"Database: {DB_PATH}")
    print(f"Email notifications: {'✅ Enabled' if notification_service.enabled else '❌ Disabled'}")
    print()
    print("Schedule: Check for newly public items every hour")
    print("=" * 80)
    
    # Load existing public items so we don't notify about them
    load_already_notified_items()
    
    # Schedule the check to run every hour
    schedule.every().hour.do(check_and_notify_public_items)
    
    # Also run immediately on startup
    print("\n🔍 Running initial check...")
    check_and_notify_public_items()
    
    print("\n⏰ Scheduler is running. Press Ctrl+C to stop.")
    print()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute if it's time to run scheduled tasks


if __name__ == '__main__':
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("\n\n⏹️  Scheduler stopped by user")
    except Exception as e:
        print(f"\n❌ Scheduler error: {e}")
        import traceback
        traceback.print_exc()
