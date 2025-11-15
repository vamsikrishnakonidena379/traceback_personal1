'use client';

import { useState, useEffect } from 'react';
import { Star, StarHalf, User, Calendar, Award } from 'lucide-react';

export default function Reviews() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReviews();
  }, []);

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/reviews');
      
      if (!response.ok) {
        throw new Error('Failed to fetch reviews');
      }
      
      const data = await response.json();
      setReviews(data.reviews || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching reviews:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <Star key={`full-${i}`} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
      );
    }

    if (hasHalfStar) {
      stars.push(
        <StarHalf key="half" className="w-5 h-5 fill-yellow-400 text-yellow-400" />
      );
    }

    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(
        <Star key={`empty-${i}`} className="w-5 h-5 text-gray-300" />
      );
    }

    return stars;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getAverageRating = () => {
    if (reviews.length === 0) return 0;
    const sum = reviews.reduce((acc, review) => acc + review.rating, 0);
    return (sum / reviews.length).toFixed(1);
  };

  const getRatingDistribution = () => {
    const distribution = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    reviews.forEach(review => {
      distribution[review.rating]++;
    });
    return distribution;
  };

  if (loading) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="border rounded-lg p-4">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6">
        <div className="text-center text-red-600">
          <p className="font-semibold">Error loading reviews</p>
          <p className="text-sm mt-1">{error}</p>
          <button 
            onClick={fetchReviews}
            className="mt-3 px-4 py-2 bg-gray-900 hover:bg-black text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const avgRating = getAverageRating();
  const distribution = getRatingDistribution();

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6">
      {/* Header with Stats */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Award className="w-7 h-7 text-yellow-500" />
            User Reviews & Success Stories
          </h2>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900">{avgRating}</div>
            <div className="flex items-center gap-1 justify-end">
              {renderStars(parseFloat(avgRating))}
            </div>
            <div className="text-sm text-gray-500 mt-1">{reviews.length} reviews</div>
          </div>
        </div>

        {/* Rating Distribution */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <p className="text-sm font-semibold text-gray-700 mb-2">Rating Distribution</p>
          <div className="space-y-1">
            {[5, 4, 3, 2, 1].map(stars => {
              const count = distribution[stars];
              const percentage = reviews.length > 0 ? (count / reviews.length) * 100 : 0;
              return (
                <div key={stars} className="flex items-center gap-2 text-sm">
                  <span className="w-12 text-gray-600">{stars} stars</span>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-yellow-400 transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                  <span className="w-8 text-gray-500 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Reviews List */}
      {reviews.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg">No reviews yet</p>
          <p className="text-sm mt-1">Be the first to share your experience!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div 
              key={review.id} 
              className="border border-gray-200 rounded-lg p-5 hover:shadow-lg transition-shadow duration-200"
            >
              {/* Review Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-gray-700 to-gray-900 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {review.user_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{review.user_name}</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <User className="w-3 h-3" />
                      <span className="text-xs">{review.user_email}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-1 mb-1">
                    {renderStars(review.rating)}
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Calendar className="w-3 h-3" />
                    <span>{formatDate(review.created_at)}</span>
                  </div>
                </div>
              </div>

              {/* Item Found Badge */}
              {review.item_found && (
                <div className="mb-3">
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                    <Award className="w-4 h-4" />
                    Found: {review.item_found}
                  </span>
                </div>
              )}

              {/* Review Text */}
              <p className="text-gray-700 leading-relaxed mb-3">
                {review.review_text}
              </p>

              {/* Review Image */}
              {review.image_url && (
                <div className="mt-3">
                  <img 
                    src={review.image_url} 
                    alt="Review"
                    className="rounded-lg max-w-xs max-h-48 object-cover border border-gray-200"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Call to Action */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600 mb-3">
          Found your lost item? Share your experience!
        </p>
        <button 
          onClick={() => window.location.href = '/review'}
          className="px-6 py-3 bg-gray-900 hover:bg-black text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          Write a Review
        </button>
      </div>
    </div>
  );
}
