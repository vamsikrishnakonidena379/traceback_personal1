
"use client";
import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import Protected from "@/components/Protected";
import Badge from "@/components/Badge";
import ReportButton from "@/components/ReportButton";

export default function ItemDetails() {
  const { id } = useParams();
  const router = useRouter();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadItemDetails();
  }, [id]);

  const loadItemDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to fetch as lost item first
      let response = await fetch(`http://localhost:5000/api/lost-items/${id}`);
      let data = await response.json();
      
      if (response.ok && data.item) {
        setItem({ ...data.item, type: 'LOST' });
      } else {
        // Try as found item
        response = await fetch(`http://localhost:5000/api/found-items/${id}`);
        data = await response.json();
        
        if (response.ok && data.item) {
          setItem({ ...data.item, type: 'FOUND' });
        } else {
          setError("Item not found");
        }
      }
    } catch (err) {
      console.error("Error loading item:", err);
      setError("Failed to load item details");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Protected>
        <Navbar />
        <div className="flex min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
          <Sidebar />
          <main className="mx-auto w-full max-w-7xl flex-1 p-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading item details...</p>
            </div>
          </main>
        </div>
      </Protected>
    );
  }

  if (error || !item) {
    return (
      <Protected>
        <Navbar />
        <div className="flex min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
          <Sidebar />
          <main className="mx-auto w-full max-w-7xl flex-1 p-6">
            <div className="text-center py-12">
              <div className="text-red-500 text-xl mb-4">⚠️ {error || "Item not found"}</div>
              <button
                onClick={() => router.push("/dashboard")}
                className="bg-gray-900 hover:bg-black text-white px-6 py-3 rounded-lg font-medium transition-all duration-200"
              >
                Back to Dashboard
              </button>
            </div>
          </main>
        </div>
      </Protected>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  return (
    <Protected>
      <Navbar />
      <div className="flex min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
        <Sidebar />
        <main className="mx-auto w-full max-w-7xl flex-1 p-6">
          {/* Header */}
          <div className="mb-6">
            <button
              onClick={() => router.back()}
              className="text-gray-600 hover:text-gray-900 font-medium mb-4 inline-flex items-center gap-2"
            >
              ← Back
            </button>
            <h1 className="text-3xl font-bold text-gray-900">Item Details</h1>
          </div>

          {/* Item Details Card */}
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-xl border border-white/20 overflow-hidden">
            <div className="grid md:grid-cols-2 gap-6 p-6">
              {/* Image Section */}
              <div className="space-y-4">
                <div className="aspect-[4/3] rounded-lg border border-gray-200 overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={item.image_alt_text || `Photo of ${item.title}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentNode.classList.add('flex', 'items-center', 'justify-center');
                        e.target.parentNode.innerHTML = `
                          <div class="text-center text-gray-500">
                            <div class="text-4xl mb-2">📷</div>
                            <div class="text-sm">Image not available</div>
                          </div>
                        `;
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center text-gray-500">
                        <div className="text-4xl mb-2">📷</div>
                        <div className="text-sm">No image available</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Details Section */}
              <div className="space-y-6">
                {/* Badges */}
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge type={item.type} />
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700">
                    {item.category}
                  </span>
                  {item.status && (
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      item.status === 'CLAIMED' ? 'bg-green-100 text-green-700' :
                      item.status === 'PENDING' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {item.status}
                    </span>
                  )}
                </div>

                {/* Title */}
                <h2 className="text-2xl font-bold text-gray-900">{item.title}</h2>

                {/* Description */}
                {item.description && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                    <p className="text-gray-600">{item.description}</p>
                  </div>
                )}

                {/* Info Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">📍 Location</div>
                    <div className="font-medium text-gray-900">{item.location_found || item.location_lost || '—'}</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">📅 Date</div>
                    <div className="font-medium text-gray-900">{formatDate(item.date_found || item.date_lost)}</div>
                  </div>
                </div>

                {/* Additional Details */}
                {item.brand && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">🏷️ Brand</div>
                    <div className="font-medium text-gray-900">{item.brand}</div>
                  </div>
                )}

                {item.color && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">🎨 Color</div>
                    <div className="font-medium text-gray-900">{item.color}</div>
                  </div>
                )}

                {/* Owner/Finder Contact Information */}
                {item.type === 'LOST' && (
                  <div className="bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-lg p-5">
                    <h3 className="font-bold text-gray-900 mb-4 text-lg">Owner Contact Information</h3>
                    <div className="space-y-3">
                      {item.user_name && (
                        <div className="flex items-start gap-3">
                          <span className="text-gray-500 text-sm mt-1">👤 Name:</span>
                          <span className="font-semibold text-gray-900 flex-1">{item.user_name}</span>
                        </div>
                      )}
                      {item.user_email && (
                        <div className="flex items-start gap-3">
                          <span className="text-gray-500 text-sm mt-1">📧 Email:</span>
                          <a href={`mailto:${item.user_email}`} className="font-semibold text-gray-900 flex-1 hover:text-blue-600 transition-colors">
                            {item.user_email}
                          </a>
                        </div>
                      )}
                      {item.user_phone && (
                        <div className="flex items-start gap-3">
                          <span className="text-gray-500 text-sm mt-1">📱 Phone:</span>
                          <a href={`tel:${item.user_phone}`} className="font-semibold text-gray-900 flex-1 hover:text-blue-600 transition-colors">
                            {item.user_phone}
                          </a>
                        </div>
                      )}
                    </div>
                    <div className="mt-4 bg-white border border-gray-200 rounded-lg p-3">
                      <p className="text-sm text-gray-600">
                        💡 Contact the owner if you have found their lost item. Please be respectful and provide details about what you found.
                      </p>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  {item.type === 'FOUND' && (
                    <button className="flex-1 bg-gray-900 hover:bg-black text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl">
                      Contact Finder
                    </button>
                  )}
                  <ReportButton type="item" targetId={item.id} />
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </Protected>
  );
}
