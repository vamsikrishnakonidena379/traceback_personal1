"""
TraceBack Finder Decision Notification Scheduler
Checks hourly for items that have completed their 3-day competition window
and notifies finders to make a decision
"""

import sqlite3
import schedule
import time
from datetime import datetime, timedelta
import pytz

# Eastern Time
ET = pytz.timezone('America/New_York')

def get_et_now():
    """Get current time in Eastern Time"""
    return datetime.now(ET)

DB_PATH = 'traceback_100k.db'

# Track items we've already notified finders about
notified_finders = set()


def check_and_notify_finders():
    """
    Check for items where 3-day competition window has ended and notify finders
    """
    try:
        print(f"\n🔍 [{get_et_now().strftime('%Y-%m-%d %H:%M:%S ET')}] Checking for items needing finder decisions...")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find items where:
        # 1. Have at least one potential claimer (success=1)
        # 2. First claim was made more than 3 days ago
        # 3. Finder hasn't been notified yet
        cursor.execute("""
            SELECT 
                f.id,
                f.title,
                f.finder_email,
                MIN(ca.marked_as_potential_at) as first_claim_time,
                COUNT(DISTINCT ca.user_email) as claimer_count
            FROM found_items f
            INNER JOIN claim_attempts ca ON f.id = ca.found_item_id AND ca.success = 1
            LEFT JOIN email_notifications en 
                ON f.id = en.found_item_id 
                AND f.finder_email = en.user_email 
                AND en.notification_type = 'decision_time'
            WHERE en.notification_id IS NULL
            AND datetime(ca.marked_as_potential_at) <= datetime('now', 'localtime', '-3 days')
            GROUP BY f.id
            HAVING claimer_count > 0
            ORDER BY first_claim_time ASC
        """)
        
        items = cursor.fetchall()
        conn.close()
        
        new_items_to_notify = []
        for item in items:
            if item['id'] not in notified_finders:
                new_items_to_notify.append(item)
                notified_finders.add(item['id'])
        
        if new_items_to_notify:
            print(f"📧 Found {len(new_items_to_notify)} items with expired competition windows:")
            
            from email_notification_service import EmailNotificationService
            notification_service = EmailNotificationService()
            
            for item in new_items_to_notify:
                try:
                    # Calculate how long ago the window expired
                    claim_time = datetime.strptime(item['first_claim_time'], '%Y-%m-%d %H:%M:%S')
                    days_since_first_claim = (get_et_now().replace(tzinfo=None) - claim_time).days
                    
                    print(f"   - Item #{item['id']}: '{item['title']}' ({item['claimer_count']} claimer(s), {days_since_first_claim} days since first claim)")
                    
                    # Send notification to finder
                    notification_service.notify_finder_decision_time(item['id'])
                    
                except Exception as e:
                    print(f"   ❌ Failed to notify finder for item {item['id']}: {e}")
            
            print(f"✅ Finder notification process completed for {len(new_items_to_notify)} items")
        else:
            print("✓ No items need finder decision notifications")
            
    except Exception as e:
        print(f"❌ Error in check_and_notify_finders: {e}")
        import traceback
        traceback.print_exc()


def load_already_notified_finders():
    """
    Load items that have already been notified so we don't send duplicates on startup
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all items where finder has already been notified about decision time
        cursor.execute("""
            SELECT DISTINCT found_item_id 
            FROM email_notifications 
            WHERE notification_type = 'decision_time'
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            notified_finders.add(row[0])
        
        print(f"📋 Loaded {len(notified_finders)} already-notified finder items from database")
        
    except Exception as e:
        print(f"⚠️  Error loading notified finders: {e}")


def run_scheduler():
    """Run the scheduler continuously"""
    print("=" * 60)
    print("TraceBack Finder Decision Notification Scheduler")
    print("=" * 60)
    print(f"Started at: {get_et_now().strftime('%Y-%m-%d %H:%M:%S ET')}")
    print("Checking every hour for items needing finder decisions...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Load items that have already been notified
    load_already_notified_finders()
    
    # Schedule the check to run every hour
    schedule.every().hour.do(check_and_notify_finders)
    
    # Run immediately on startup
    print("\n🚀 Running initial check...")
    check_and_notify_finders()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute if a job is due
    except KeyboardInterrupt:
        print("\n\n👋 Scheduler stopped by user")


if __name__ == '__main__':
    run_scheduler()
