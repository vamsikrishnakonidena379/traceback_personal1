#!/usr/bin/env python3
"""
Script to grant or revoke moderator access for users
"""
import sqlite3
import sys

DB_PATH = 'traceback_100k.db'

def grant_moderator(email):
    """Grant moderator access to a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT email, full_name, is_moderator FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User not found: {email}")
            conn.close()
            return False
        
        if user[2] == 1:
            print(f"ℹ️  User {user[1]} ({email}) is already a moderator")
            conn.close()
            return True
        
        # Grant moderator access
        cursor.execute('UPDATE users SET is_moderator = 1 WHERE email = ?', (email,))
        conn.commit()
        conn.close()
        
        print(f"✅ Granted moderator access to: {user[1]} ({email})")
        return True
        
    except Exception as e:
        print(f"❌ Error granting moderator access: {e}")
        return False


def revoke_moderator(email):
    """Revoke moderator access from a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT email, full_name, is_moderator FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User not found: {email}")
            conn.close()
            return False
        
        if user[2] == 0:
            print(f"ℹ️  User {user[1]} ({email}) is not a moderator")
            conn.close()
            return True
        
        # Revoke moderator access
        cursor.execute('UPDATE users SET is_moderator = 0 WHERE email = ?', (email,))
        conn.commit()
        conn.close()
        
        print(f"✅ Revoked moderator access from: {user[1]} ({email})")
        return True
        
    except Exception as e:
        print(f"❌ Error revoking moderator access: {e}")
        return False


def list_moderators():
    """List all users with moderator access"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, full_name, first_name, last_name, created_at
            FROM users 
            WHERE is_moderator = 1
            ORDER BY email
        ''')
        
        moderators = cursor.fetchall()
        conn.close()
        
        if not moderators:
            print("\n📋 No moderators found in the system")
            return
        
        print(f"\n📋 Current Moderators ({len(moderators)}):")
        print("-" * 80)
        for mod in moderators:
            print(f"  👤 {mod[1]} ({mod[0]})")
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error listing moderators: {e}")


def list_all_users():
    """List all users in the system"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, full_name, is_moderator, created_at
            FROM users 
            ORDER BY email
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            print("\n📋 No users found in the system")
            return
        
        print(f"\n📋 All Users ({len(users)}):")
        print("-" * 80)
        for user in users:
            mod_badge = "🔧 MODERATOR" if user[2] == 1 else ""
            print(f"  👤 {user[1]} ({user[0]}) {mod_badge}")
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")


def main():
    print("\n🔧 TraceBack Moderator Access Management")
    print("=" * 80)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python grant_moderator_access.py grant <email>     - Grant moderator access")
        print("  python grant_moderator_access.py revoke <email>    - Revoke moderator access")
        print("  python grant_moderator_access.py list              - List all moderators")
        print("  python grant_moderator_access.py list-all          - List all users")
        print("\nExample:")
        print("  python grant_moderator_access.py grant vkoniden@kent.edu")
        print()
        list_all_users()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_moderators()
    elif command == 'list-all':
        list_all_users()
    elif command == 'grant' and len(sys.argv) == 3:
        email = sys.argv[2]
        grant_moderator(email)
        print()
        list_moderators()
    elif command == 'revoke' and len(sys.argv) == 3:
        email = sys.argv[2]
        revoke_moderator(email)
        print()
        list_moderators()
    else:
        print("❌ Invalid command or missing email")
        print("\nUse: python grant_moderator_access.py [grant|revoke|list|list-all] [email]")


if __name__ == '__main__':
    main()
