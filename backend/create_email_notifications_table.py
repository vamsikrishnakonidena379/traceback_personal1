import sqlite3

conn = sqlite3.connect('traceback_100k.db')
cursor = conn.cursor()

# Create email_notifications table to track which users have been notified about which items
cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        found_item_id INTEGER NOT NULL,
        user_email TEXT NOT NULL,
        notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(found_item_id, user_email),
        FOREIGN KEY (found_item_id) REFERENCES found_items(id) ON DELETE CASCADE
    )
""")

print("✅ email_notifications table created successfully!")

# Create index for faster lookups
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_email_notifications_item 
    ON email_notifications(found_item_id)
""")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_email_notifications_user 
    ON email_notifications(user_email)
""")

print("✅ Indexes created for email_notifications!")

# Verify the table
cursor.execute("PRAGMA table_info(email_notifications)")
columns = cursor.fetchall()
print("\n📋 Table structure:")
for col in columns:
    print(f"   {col[1]} ({col[2]})")

conn.commit()
conn.close()

print("\n✅ All done! email_notifications table is ready.")
