"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);
  const hide = ["/", "/login", "/signup", "/verify-email"].includes(pathname);
  
  useEffect(() => {
    if (!hide) {
      loadUnreadCount();
      // Poll for unread messages every 10 seconds
      const interval = setInterval(loadUnreadCount, 10000);
      return () => clearInterval(interval);
    }
  }, [hide]);

  const loadUnreadCount = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || 'null');
      if (!user) return;

      const response = await fetch(`http://localhost:5000/api/messages/conversations?user_id=${user.id}`);
      const data = await response.json();
      
      if (data.conversations) {
        const total = data.conversations.reduce((sum, conv) => sum + (conv.unread_count || 0), 0);
        setUnreadCount(total);
      }
    } catch (error) {
      console.error('Error loading unread count:', error);
    }
  };
  
  if (hide) return null;

  const logout = async () => {
    const token = localStorage.getItem("sessionToken");
    
    if (token) {
      try {
        await fetch('http://localhost:5000/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (err) {
        console.error("Logout API call failed:", err);
      }
    }
    
    localStorage.removeItem("sessionToken");
    localStorage.removeItem("user");
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-200 shadow-sm">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-6">
        <Link href="/dashboard" className="flex items-center hover:opacity-80 transition-opacity">
          <Image 
            src="/logo.png" 
            alt="Traceback Logo" 
            width={200} 
            height={60}
            className="h-16 w-auto"
          />
        </Link>

        <div className="flex items-center gap-4">
          {/* Messages Link with Badge */}
          <Link 
            href="/messages"
            className="relative bg-white/90 hover:bg-white text-gray-900 px-4 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Messages
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </Link>

          {/* Profile Dropdown */}
          <div className="relative group">
            <button className="bg-white/90 hover:bg-white text-gray-900 px-4 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2">
              <span>👤</span>
              Profile
              <svg className="w-4 h-4 ml-1 group-hover:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {/* Dropdown Menu */}
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div className="py-2">
                <Link 
                  href="/profile"
                  className="block px-4 py-2 text-gray-800 hover:bg-gray-100 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <span>�️</span>
                    View Profile
                  </span>
                </Link>
                <Link 
                  href="/profile/create"
                  className="block px-4 py-2 text-gray-800 hover:bg-gray-100 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <span>✏️</span>
                    Edit Profile
                  </span>
                </Link>
              </div>
            </div>
          </div>
          
          <button 
            onClick={logout} 
            className="bg-gray-900 hover:bg-gray-800 text-white px-6 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Log Out
          </button>
        </div>
      </div>
    </header>
  );
}
