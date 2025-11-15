
"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Protected from "@/components/Protected";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ItemCard from "@/components/ItemCard";
import PotentialMatchCard from "@/components/PotentialMatchCard";
import Reviews from "@/components/Reviews";
import { findPotentialMatches } from "@/utils/matching";
import apiService from "@/utils/apiService";

export default function Dashboard() {
  const router = useRouter();
  const [lostItems, setLostItems] = useState([]);
  const [foundItems, setFoundItems] = useState([]);
  const [claimsAsClaimer, setClaimsAsClaimer] = useState([]);
  const [claimsAsFinder, setClaimsAsFinder] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({});

  useEffect(() => {
    loadDashboardData();
    loadClaims();
  }, []);

  const startConversation = async (otherUserId, otherUserName, otherUserEmail, itemId, itemType, itemTitle) => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      
      if (!user.id) {
        alert('Please log in to send messages');
        return;
      }
      
      // Send an initial message to create the conversation
      const response = await fetch('http://localhost:5000/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender_id: user.id,
          sender_name: user.name,
          sender_email: user.email,
          receiver_id: otherUserId,
          receiver_name: otherUserName,
          receiver_email: otherUserEmail,
          message_text: `Hi, I'm contacting you about: ${itemTitle}`,
          item_id: itemId,
          item_type: itemType,
          item_title: itemTitle
        })
      });

      if (response.ok) {
        router.push('/messages');
      } else {
        const data = await response.json();
        alert(`Failed to start conversation: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      alert('Failed to start conversation');
    }
  };

  const loadClaims = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      if (!user.email) return;

      // Load claims where user is the claimer (they verified ownership)
      const claimerResponse = await fetch(`http://localhost:5000/api/claims?user_email=${encodeURIComponent(user.email)}&type=claimer`);
      const claimerData = await claimerResponse.json();
      
      if (claimerResponse.ok) {
        setClaimsAsClaimer(claimerData.claims || []);
      }

      // Load claims where user is the finder (someone verified their found item)
      const finderResponse = await fetch(`http://localhost:5000/api/claims?user_email=${encodeURIComponent(user.email)}&type=finder`);
      const finderData = await finderResponse.json();
      
      if (finderResponse.ok) {
        setClaimsAsFinder(finderData.claims || []);
      }
    } catch (error) {
      console.error('Failed to load claims:', error);
    }
  };

  const handleClaimStatusUpdate = async (claimId, status, claim) => {
    try {
      // If marking as NOT_CLAIMED (False Claim), automatically report it
      if (status === 'NOT_CLAIMED') {
        const confirmFalseClaim = window.confirm(
          `⚠️ Mark this as a FALSE CLAIM?\n\n` +
          `This will:\n` +
          `• Mark the claim as invalid\n` +
          `• Report the user for false verification\n` +
          `• Prevent them from claiming this item again\n\n` +
          `Click OK to confirm, or Cancel to go back.`
        );
        
        if (!confirmFalseClaim) {
          return; // User cancelled
        }

        // Update claim status to NOT_CLAIMED
        const response = await fetch(`http://localhost:5000/api/claims/${claimId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            claimed_status: 'NOT_CLAIMED',
            notes: 'Marked as false claim - User reported for false verification'
          })
        });

        if (response.ok) {
          // Automatically create abuse report
          const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
          
          const reportData = {
            type: 'CLAIM',
            target_id: claimId,
            target_title: `False Claim: ${claim.item_title}`,
            reported_by_id: currentUser.id || null,
            reported_by_name: currentUser.name || 'Anonymous',
            reported_by_email: currentUser.email || '',
            category: 'False Claim',
            reason: 'False ownership verification',
            description: `User ${claim.claimer_name} (${claim.claimer_email}) falsely verified ownership of item: ${claim.item_title}`
          };

          // Submit abuse report
          await fetch('http://localhost:5000/api/reports', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(reportData)
          });

          alert('✅ Claim marked as false and reported to administrators.');
          loadClaims(); // Reload claims
        } else {
          alert('❌ Failed to update claim');
        }
        return;
      }
      
      // If marking as CLAIMED, show confirmation
      if (status === 'CLAIMED') {
        const confirmed = window.confirm(
          `✓ Confirm that the item was successfully returned?\n\n` +
          `After confirming, you can scroll down to leave a review about your experience.`
        );
        
        if (!confirmed) {
          return;
        }
      }

      const response = await fetch(`http://localhost:5000/api/claims/${claimId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          claimed_status: status,
          notes: status === 'CLAIMED' ? 'Item successfully retrieved' : 'Item not claimed'
        })
      });

      if (response.ok) {
        if (status === 'CLAIMED') {
          alert('✅ Item marked as claimed! Scroll down to the reviews section to share your experience.');
          loadClaims(); // Reload claims
          // Scroll to reviews section after a short delay
          setTimeout(() => {
            const reviewsSection = document.querySelector('section[class*="reviews"]') || 
                                 document.querySelector('h2:has-text("Reviews")') ||
                                 document.querySelector('[class*="Reviews"]');
            if (reviewsSection) {
              reviewsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
              // If can't find reviews, just scroll to bottom
              window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            }
          }, 1000);
        } else {
          alert(`✅ Claim marked as ${status.toLowerCase()}`);
          loadClaims(); // Reload claims
        }
      } else {
        alert('❌ Failed to update claim');
      }
    } catch (error) {
      console.error('Error updating claim:', error);
      alert('Error updating claim');
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load recent items and stats in parallel
      // For dashboard matching, include all items (include_private=true) regardless of age
      const [lostResponse, foundResponse, statsResponse] = await Promise.all([
        apiService.getFormattedLostItems({ limit: 6 }),
        apiService.getFormattedFoundItems({ limit: 6, include_private: 'true' }), // Include all items for matching
        apiService.getStats().catch(() => ({})) // Don't fail if stats unavailable
      ]);

      console.log('🔴 Dashboard lost items response:', lostResponse);
      console.log('🔴 Lost items array:', lostResponse.items?.slice(0,1)); // Show first item structure
      console.log('🔴 First lost item image_url:', lostResponse.items?.[0]?.image_url);
      console.log('🟢 Dashboard found items response:', foundResponse);
      console.log('🟢 Found items array:', foundResponse.items?.slice(0,1)); // Show first 2 items

      setLostItems(lostResponse.items || []);
      setFoundItems(foundResponse.items || []);
      
      // CRITICAL DEBUG: Check what's actually in the state after setting
      setTimeout(() => {
        console.log('🔥 CRITICAL DEBUG - Lost items state after setting:');
        console.log('First item in state:', lostResponse.items?.[0]);
        console.log('Image URL in first item:', lostResponse.items?.[0]?.image_url);
      }, 100);
      setStats(statsResponse || {});

    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Find potential matches for all lost items
  const allPotentialMatches = lostItems.flatMap(lostItem => {
    const matches = findPotentialMatches(lostItem, foundItems, 40); // 40% minimum threshold
    return matches.map(match => ({
      ...match,
      lostItemId: lostItem.id,
      lostItemTitle: lostItem.title
    }));
  }).sort((a, b) => b.matchScore - a.matchScore);

  if (loading) {
    return (
      <Protected>
        <Navbar />
        <div className="flex min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
          <Sidebar />
          <main className="mx-auto w-full max-w-7xl flex-1 p-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading dashboard...</p>
            </div>
          </main>
        </div>
      </Protected>
    );
  }

  if (error) {
    return (
      <Protected>
        <Navbar />
        <div className="flex min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
          <Sidebar />
          <main className="mx-auto w-full max-w-7xl flex-1 p-6">
            <div className="text-center py-12">
              <div className="text-red-500 text-xl mb-4">⚠️ Connection Error</div>
              <p className="text-gray-600 mb-4">{error}</p>
              <button 
                onClick={loadDashboardData}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
              >
                Try Again
              </button>
              <p className="text-sm text-gray-500 mt-4">
                Make sure the MySQL backend is running on port 5000
              </p>
            </div>
          </main>
        </div>
      </Protected>
    );
  }

  return (
    <Protected>
      <Navbar />
      <div className="flex min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
        <Sidebar />
        <main className="mx-auto w-full max-w-7xl flex-1 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              {Object.keys(stats).length > 0 && (
                <p className="text-sm text-gray-600 mt-1">
                  {stats.active_lost_items || 0} active lost items • {stats.unclaimed_found_items || 0} unclaimed found items
                </p>
              )}
            </div>
            <div className="flex gap-3 items-center">
              <a href="/lost" className="bg-white/90 hover:bg-white text-gray-900 px-4 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl">
                Report Lost Item
              </a>
              <a href="/found" className="bg-gray-900 hover:bg-black text-white px-4 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
                Report Found Item
              </a>
            </div>
          </div>

          {/* Stats Overview */}
          {Object.keys(stats).length > 0 && (
            <div className="grid grid-cols-2 gap-4 mb-6 md:grid-cols-4">
              <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-4">
                <div className="text-2xl font-bold text-gray-900">{stats.active_lost_items || 0}</div>
                <div className="text-sm text-gray-600">Active Lost Items</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-4">
                <div className="text-2xl font-bold text-gray-900">{stats.unclaimed_found_items || 0}</div>
                <div className="text-sm text-gray-600">Unclaimed Found</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-4">
                <div className="text-2xl font-bold text-gray-900">{stats.items_claimed || 0}</div>
                <div className="text-sm text-gray-600">Items Claimed</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-4">
                <div className="text-2xl font-bold text-gray-900">{stats.recent_found_items || 0}</div>
                <div className="text-sm text-gray-600">Found This Week</div>
              </div>
            </div>
          )}

          {/* Claims Sections Side by Side */}
          {(claimsAsClaimer.length > 0 || claimsAsFinder.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Verified Claims Section - Items You're Claiming */}
              {claimsAsClaimer.length > 0 && (
                <section className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-lg font-semibold text-gray-900">Items You're Claiming</div>
                      <div className="text-sm text-gray-600">Items you've verified ownership for</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="bg-gray-900 text-white px-3 py-1 rounded-full text-sm font-medium">
                        {claimsAsClaimer.filter(c => c.claimed_status === 'PENDING').length}
                      </span>
                      {claimsAsClaimer.length > 2 && (
                        <a 
                          href="/claims?type=claimer"
                          className="text-sm text-blue-600 hover:text-blue-800 font-medium underline"
                        >
                          See All
                        </a>
                      )}
                    </div>
                  </div>
                  <div className="space-y-4 max-h-[600px] overflow-y-auto">
                    {claimsAsClaimer.slice(0, 2).map((claim) => (
                      <div key={claim.claim_id} className="bg-gradient-to-br from-gray-50 to-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="font-semibold text-gray-900 text-lg">{claim.item_title}</h3>
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                claim.claimed_status === 'CLAIMED' ? 'bg-gray-900 text-white' :
                                claim.claimed_status === 'NOT_CLAIMED' ? 'bg-gray-300 text-gray-700' :
                                'bg-gray-100 text-gray-900 border border-gray-300'
                              }`}>
                                {claim.claimed_status}
                              </span>
                            </div>
                            
                            <div className="text-sm text-gray-600 mb-4">
                              <p className="flex items-center gap-2">
                                <span className="text-gray-900">✓</span>
                                Verified: {new Date(claim.verification_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                              </p>
                            </div>

                            <div className="bg-white rounded-lg p-4 mb-4 border border-gray-200">
                              <h4 className="font-semibold text-gray-900 mb-3 text-sm uppercase tracking-wide">Finder Contact</h4>
                              <div className="space-y-2 text-sm">
                                <p className="flex items-start">
                                  <span className="text-gray-600 w-16">Name:</span>
                                  <span className="font-medium text-gray-900">{claim.finder_name}</span>
                                </p>
                                <p className="flex items-start">
                                  <span className="text-gray-600 w-16">Email:</span>
                                  <a href={`mailto:${claim.finder_email}`} className="font-medium text-gray-900 hover:text-black underline">{claim.finder_email}</a>
                                </p>
                                {claim.finder_phone && (
                                  <p className="flex items-start">
                                    <span className="text-gray-600 w-16">Phone:</span>
                                    <a href={`tel:${claim.finder_phone}`} className="font-medium text-gray-900 hover:text-black underline">{claim.finder_phone}</a>
                                  </p>
                                )}
                              </div>
                              <button
                                onClick={() => startConversation(
                                  claim.finder_id,
                                  claim.finder_name,
                                  claim.finder_email,
                                  claim.item_id,
                                  claim.item_type,
                                  claim.item_title
                                )}
                                className="mt-3 w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center justify-center gap-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                                Message Finder
                              </button>
                            </div>

                            {claim.claimed_status === 'PENDING' && (
                              <div className="flex gap-3">
                                <button
                                  onClick={() => handleClaimStatusUpdate(claim.claim_id, 'CLAIMED', claim)}
                                  className="flex-1 bg-gray-900 hover:bg-black text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 shadow-lg hover:shadow-xl"
                                >
                                  ✓ Mark as Claimed
                                </button>
                                <button
                                  onClick={() => handleClaimStatusUpdate(claim.claim_id, 'NOT_CLAIMED', claim)}
                                  className="px-4 py-2.5 border-2 border-gray-300 text-gray-700 hover:border-gray-900 hover:text-gray-900 rounded-lg text-sm font-semibold transition-all duration-200"
                                >
                                  Not Claimed
                                </button>
                              </div>
                            )}

                            {claim.claimed_status === 'CLAIMED' && claim.claimed_date && (
                              <div className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium">
                                ✓ Item claimed on {new Date(claim.claimed_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Claims for Your Found Items */}
              {claimsAsFinder.length > 0 && (
                <section className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-lg font-semibold text-gray-900">Claims on Your Found Items</div>
                      <div className="text-sm text-gray-600">People who verified ownership of items you found</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="bg-gray-900 text-white px-3 py-1 rounded-full text-sm font-medium">
                        {claimsAsFinder.filter(c => c.claimed_status === 'PENDING').length}
                      </span>
                      {claimsAsFinder.length > 2 && (
                        <a 
                          href="/claims?type=finder"
                          className="text-sm text-blue-600 hover:text-blue-800 font-medium underline"
                        >
                          See All
                        </a>
                      )}
                    </div>
                  </div>
                  <div className="space-y-4 max-h-[600px] overflow-y-auto">
                    {claimsAsFinder.slice(0, 2).map((claim) => (
                      <div key={claim.claim_id} className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-5 border border-gray-700 shadow-lg">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="font-semibold text-white text-lg">{claim.item_title}</h3>
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                claim.claimed_status === 'CLAIMED' ? 'bg-white text-gray-900' :
                                claim.claimed_status === 'NOT_CLAIMED' ? 'bg-gray-600 text-gray-200' :
                                'bg-gray-700 text-white border border-gray-500'
                              }`}>
                                {claim.claimed_status}
                              </span>
                            </div>
                            
                            <div className="text-sm text-gray-300 mb-4">
                              <p className="flex items-center gap-2">
                                <span className="text-white">📋</span>
                                Someone verified ownership: {new Date(claim.verification_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                              </p>
                            </div>

                            <div className="bg-white rounded-lg p-4 mb-4">
                              <h4 className="font-semibold text-gray-900 mb-3 text-sm uppercase tracking-wide">Owner Contact (Claimer)</h4>
                              <div className="space-y-2 text-sm">
                                <p className="flex items-start">
                                  <span className="text-gray-600 w-16">Name:</span>
                                  <span className="font-medium text-gray-900">{claim.claimer_name}</span>
                                </p>
                                <p className="flex items-start">
                                  <span className="text-gray-600 w-16">Email:</span>
                                  <a href={`mailto:${claim.claimer_email}`} className="font-medium text-gray-900 hover:text-black underline">{claim.claimer_email}</a>
                                </p>
                                {claim.claimer_phone && (
                                  <p className="flex items-start">
                                    <span className="text-gray-600 w-16">Phone:</span>
                                    <a href={`tel:${claim.claimer_phone}`} className="font-medium text-gray-900 hover:text-black underline">{claim.claimer_phone}</a>
                                  </p>
                                )}
                              </div>
                              <button
                                onClick={() => startConversation(
                                  claim.claimer_id,
                                  claim.claimer_name,
                                  claim.claimer_email,
                                  claim.item_id,
                                  claim.item_type,
                                  claim.item_title
                                )}
                                className="mt-3 w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center justify-center gap-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                                Message Claimer
                              </button>
                            </div>

                            <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 mb-4">
                              <p className="text-sm text-gray-200">
                                <span className="text-white font-semibold">💡 Action needed:</span> Contact the claimer to arrange item return. Once the item is returned, mark it as claimed below.
                              </p>
                            </div>

                            {claim.claimed_status === 'PENDING' && (
                              <div className="flex gap-3">
                                <button
                                  onClick={() => handleClaimStatusUpdate(claim.claim_id, 'CLAIMED', claim)}
                                  className="flex-1 bg-white hover:bg-gray-100 text-gray-900 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 shadow-lg hover:shadow-xl"
                                >
                                  ✓ Item Returned to Owner
                                </button>
                                <button
                                  onClick={() => handleClaimStatusUpdate(claim.claim_id, 'NOT_CLAIMED', claim)}
                                  className="px-4 py-2.5 border-2 border-gray-600 text-gray-200 hover:border-white hover:text-white rounded-lg text-sm font-semibold transition-all duration-200"
                                >
                                  False Claim
                                </button>
                              </div>
                            )}

                            {claim.claimed_status === 'CLAIMED' && claim.claimed_date && (
                              <div className="bg-white text-gray-900 rounded-lg px-4 py-2 text-sm font-medium">
                                ✓ Item returned on {new Date(claim.claimed_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}

          {/* Potential Matches */}
          {allPotentialMatches.length > 0 && (
            <section className="mb-6 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-lg font-semibold text-gray-900">Potential Matches Found</div>
                  <div className="text-sm text-gray-600">Found items that might match your lost items</div>
                </div>
                <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-sm font-medium">
                  {allPotentialMatches.length}
                </span>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {allPotentialMatches.slice(0, 6).map((match, index) => (
                  <PotentialMatchCard 
                    key={`${match.id}-${match.lostItemId}-${index}`}
                    foundItem={match}
                    matchScore={match.matchScore}
                    lostItemId={match.lostItemId}
                  />
                ))}
              </div>
              {allPotentialMatches.length > 6 && (
                <div className="mt-4 text-center">
                  <button className="text-amber-700 hover:text-amber-800 font-medium text-sm">
                    View {allPotentialMatches.length - 6} more matches →
                  </button>
                </div>
              )}
            </section>
          )}

          {/* Reviews Section */}
          <section className="mt-6">
            <Reviews />
          </section>
        </main>
      </div>
    </Protected>
  );
}
