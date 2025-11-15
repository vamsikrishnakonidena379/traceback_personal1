"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

export default function Protected({ children, requireProfile = true }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [profileComplete, setProfileComplete] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("sessionToken");
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      
      if (!token || !user.id) {
        router.replace("/login");
        return;
      }
      
      setIsAuthenticated(true);
      
      try {
        // Check if profile is complete (if required)
        if (requireProfile && pathname !== "/profile/create") {
          // First check localStorage for quick validation
          if (user.profile_completed === true || user.profile_completed === 1) {
            console.log("✅ Profile marked complete in localStorage");
            setProfileComplete(true);
            setIsLoading(false);
            return;
          }
          
          // If not in localStorage, check backend
          console.log("🔍 Checking profile completion with backend for user:", user.id);
          
          try {
            const profileResponse = await fetch(`http://localhost:5000/api/profile/${user.id}`);
            
            if (!profileResponse.ok) {
              console.error("❌ Failed to fetch profile, status:", profileResponse.status);
              // Don't redirect on fetch error, allow access but show warning
              setProfileComplete(true);
              setIsLoading(false);
              return;
            }
            
            const profileData = await profileResponse.json();
            console.log("📦 Profile data from backend:", profileData);
            
            // Check if profile is complete - prioritize profile_completed flag
            const profile = profileData.profile || profileData;
            const isComplete = profile.profile_completed === true || 
                             profile.profile_completed === 1;
            
            console.log("Profile completion check:", {
              profile_completed: profile.profile_completed,
              isComplete
            });
            
            if (!isComplete) {
              console.log("⚠️ Profile incomplete, redirecting to profile creation");
              router.replace("/profile/create");
              return;
            }
            
            // Update localStorage with complete profile data from backend
            const updatedUser = { 
              ...user, 
              ...profile,
              profile_completed: true 
            };
            localStorage.setItem("user", JSON.stringify(updatedUser));
            console.log("✅ Profile marked complete, updated localStorage with full profile data");
            
            setProfileComplete(true);
          } catch (fetchError) {
            console.error("Network error checking profile:", fetchError);
            // On network error, allow access if we have user data
            setProfileComplete(true);
          }
        } else {
          setProfileComplete(true);
        }
        
      } catch (err) {
        console.error("Profile check failed:", err);
        // Don't redirect to login on profile check failure, just require profile
        if (requireProfile && pathname !== "/profile/create") {
          router.replace("/profile/create");
        } else {
          setProfileComplete(true);
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuth();
  }, [router, pathname, requireProfile]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-100">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-300 border-t-gray-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || (requireProfile && !profileComplete)) {
    return null; // Will redirect
  }

  return <>{children}</>;
}