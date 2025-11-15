'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Protected from '@/components/Protected';
import Navbar from '@/components/Navbar';
import Link from 'next/link';
import { CheckCircle, XCircle, AlertTriangle, ArrowLeft, ArrowRight } from 'lucide-react';

export default function VerifyOwnershipPage() {
  const params = useParams();
  const router = useRouter();
  const foundItemId = params.id;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [itemTitle, setItemTitle] = useState('');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [attempts, setAttempts] = useState(0);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [finderDetails, setFinderDetails] = useState(null);
  const [finderProfile, setFinderProfile] = useState(null);

  const maxAttempts = 3;

  useEffect(() => {
    fetchSecurityQuestions();
  }, [foundItemId]);

  const fetchFinderProfile = async (userId) => {
    try {
      const response = await fetch(`http://localhost:5000/api/profile/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setFinderProfile(data.profile);
      }
    } catch (error) {
      console.error('Error fetching finder profile:', error);
    }
  };

  const fetchSecurityQuestions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:5000/api/security-questions/${foundItemId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch security questions');
      }
      
      const data = await response.json();
      setQuestions(data.questions || []);
      setItemTitle(data.item?.title || 'Unknown Item');
      setError(null);
    } catch (err) {
      console.error('Error fetching security questions:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (questionId, choice) => {
    setAnswers({
      ...answers,
      [questionId]: choice
    });
  };

  const handleNext = () => {
    const currentQuestion = questions[currentQuestionIndex];
    if (!answers[currentQuestion.id]) {
      alert('Please select an answer before continuing.');
      return;
    }

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handleBack = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmit = async () => {
    // Check all questions are answered
    for (const question of questions) {
      if (!answers[question.id]) {
        alert('Please answer all questions before submitting.');
        return;
      }
    }

    try {
      setVerifying(true);
      
      // Get current user info
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      
      const response = await fetch('http://localhost:5000/api/verify-ownership', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          found_item_id: parseInt(foundItemId),
          answers: answers,
          claimer_user_id: currentUser.id || null,
          claimer_name: currentUser.name || 'Unknown',
          claimer_email: currentUser.email || '',
          claimer_phone: currentUser.phone || ''
        })
      });

      const data = await response.json();

      if (data.verified) {
        setVerificationResult({
          success: true,
          message: data.message,
          successRate: data.success_rate,
          claimId: data.claim_id
        });
        setFinderDetails(data.finder_details);
        
        // Fetch full finder profile
        if (data.finder_details?.user_id) {
          await fetchFinderProfile(data.finder_details.user_id);
        }
      } else {
        setAttempts(attempts + 1);
        setVerificationResult({
          success: false,
          message: data.message || 'Verification failed. Please try again.',
          attemptsRemaining: maxAttempts - (attempts + 1)
        });

        if (attempts + 1 >= maxAttempts) {
          setTimeout(() => {
            router.push('/found');
          }, 5000);
        } else {
          setTimeout(() => {
            setVerificationResult(null);
            setCurrentQuestionIndex(0);
            setAnswers({});
          }, 4000);
        }
      }
    } catch (err) {
      console.error('Verification error:', err);
      setVerificationResult({
        success: false,
        message: 'Failed to verify ownership. Please try again.'
      });
    } finally {
      setVerifying(false);
    }
  };

  if (loading) {
    return (
      <Protected>
        <Navbar />
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 py-12 px-4">
          <div className="max-w-3xl mx-auto">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-12 text-center">
              <div className="w-12 h-12 border-4 border-gray-300 border-t-gray-600 rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Loading security questions...</p>
            </div>
          </div>
        </div>
      </Protected>
    );
  }

  if (error || !questions || questions.length === 0) {
    return (
      <Protected>
        <Navbar />
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 py-12 px-4">
          <div className="max-w-3xl mx-auto">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-12 text-center">
              <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Verification Unavailable</h2>
              <p className="text-gray-600 mb-6">
                {error || 'This item doesn\'t have security questions set up.'}
              </p>
              <Link
                href="/found"
                className="inline-block bg-gray-900 hover:bg-black text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Back to Found Items
              </Link>
            </div>
          </div>
        </div>
      </Protected>
    );
  }

  // Show verification result
  if (verificationResult) {
    if (verificationResult.success && finderDetails) {
      const startConversation = async () => {
        try {
          const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
          
          console.log('Starting conversation with:', {
            currentUser,
            finderDetails,
            foundItemId,
            itemTitle
          });
          
          if (!currentUser.id) {
            alert('Please log in to send messages');
            return;
          }
          
          // Use a placeholder ID if finder doesn't have an account (email-only user)
          const receiverId = finderDetails.user_id || 0;
          
          const messagePayload = {
            sender_id: currentUser.id,
            sender_name: currentUser.name,
            sender_email: currentUser.email,
            receiver_id: receiverId,
            receiver_name: finderDetails.name,
            receiver_email: finderDetails.email,
            message_text: `Hi ${finderDetails.name}! I just verified ownership of ${itemTitle}. Thank you for finding it!`,
            item_id: parseInt(foundItemId),
            item_type: 'found',
            item_title: itemTitle
          };
          
          console.log('Sending message payload:', messagePayload);
          
          const response = await fetch('http://localhost:5000/api/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(messagePayload)
          });

          const responseData = await response.json();
          console.log('Message API response:', responseData);

          if (response.ok) {
            router.push('/messages');
          } else {
            alert(`Failed to start conversation: ${responseData.error || 'Unknown error'}`);
          }
        } catch (error) {
          console.error('Error starting conversation:', error);
          alert(`Failed to start conversation: ${error.message}`);
        }
      };

      return (
        <Protected>
          <Navbar />
          <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 py-12 px-4">
            <div className="max-w-4xl mx-auto">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-12">
                <div className="text-center mb-8">
                  <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-4" />
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Verification Successful! 🎉</h2>
                  <p className="text-lg text-green-600 mb-4">{verificationResult.message}</p>
                  <div className="inline-block bg-green-100 text-green-800 px-4 py-2 rounded-lg font-semibold">
                    Success Rate: {verificationResult.successRate}%
                  </div>
                </div>

                {/* Finder Profile Card */}
                <div className="bg-gradient-to-br from-gray-50 to-white rounded-xl border-2 border-gray-200 overflow-hidden mb-6">
                  <div className="bg-gray-900 text-white px-6 py-4">
                    <h3 className="text-xl font-bold">Finder Profile</h3>
                    <p className="text-sm text-gray-300">The person who found your item</p>
                  </div>

                  <div className="p-6">
                    {/* Profile Image and Basic Info */}
                    <div className="flex items-start gap-6 mb-6">
                      <div className="flex-shrink-0">
                        {finderProfile?.profile_image ? (
                          <img 
                            src={finderProfile.profile_image} 
                            alt={finderDetails.name}
                            className="w-24 h-24 rounded-full object-cover border-4 border-gray-900"
                          />
                        ) : (
                          <div className="w-24 h-24 rounded-full bg-gray-900 text-white flex items-center justify-center text-3xl font-bold">
                            {finderDetails.name.charAt(0)}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <h4 className="text-2xl font-bold text-gray-900 mb-2">{finderDetails.name}</h4>
                        {finderProfile?.bio && (
                          <p className="text-gray-600 mb-3 italic">"{finderProfile.bio}"</p>
                        )}
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {finderProfile?.year_of_study && (
                            <div className="flex items-center gap-2 text-sm">
                              <span className="text-gray-600">📚 Year:</span>
                              <span className="font-semibold text-gray-900">{finderProfile.year_of_study}</span>
                            </div>
                          )}
                          {finderProfile?.major && (
                            <div className="flex items-center gap-2 text-sm">
                              <span className="text-gray-600">🎓 Major:</span>
                              <span className="font-semibold text-gray-900">{finderProfile.major}</span>
                            </div>
                          )}
                          {finderProfile?.building_preference && (
                            <div className="flex items-center gap-2 text-sm">
                              <span className="text-gray-600">📍 Building:</span>
                              <span className="font-semibold text-gray-900">{finderProfile.building_preference}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Contact Information */}
                    <div className="bg-gray-50 rounded-lg p-5 mb-4">
                      <h5 className="font-bold text-gray-900 mb-3 text-sm uppercase tracking-wide">Contact Information</h5>
                      <div className="space-y-3">
                        <div className="flex items-start gap-3">
                          <span className="text-gray-600 font-medium w-20">Email:</span>
                          <a href={`mailto:${finderDetails.email}`} className="text-gray-900 hover:text-black underline font-semibold">
                            {finderDetails.email}
                          </a>
                        </div>
                        {finderDetails.phone && (
                          <div className="flex items-start gap-3">
                            <span className="text-gray-600 font-medium w-20">Phone:</span>
                            <a href={`tel:${finderDetails.phone}`} className="text-gray-900 hover:text-black underline font-semibold">
                              {finderDetails.phone}
                            </a>
                          </div>
                        )}
                        {finderProfile?.phone_number && !finderDetails.phone && (
                          <div className="flex items-start gap-3">
                            <span className="text-gray-600 font-medium w-20">Phone:</span>
                            <a href={`tel:${finderProfile.phone_number}`} className="text-gray-900 hover:text-black underline font-semibold">
                              {finderProfile.phone_number}
                            </a>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Message Button */}
                    <button
                      onClick={startConversation}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      Message {finderDetails.name}
                    </button>
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-blue-800">
                    � Use the messaging feature to coordinate pickup details. Please be respectful and thank them for their help!
                  </p>
                  {verificationResult.claimId && (
                    <p className="text-xs text-blue-600 mt-2">
                      Claim ID: {verificationResult.claimId} - Check your dashboard to track this claim.
                    </p>
                  )}
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={startConversation}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-center py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    💬 Send Message
                  </button>
                  <Link
                    href="/dashboard"
                    className="flex-1 bg-gray-900 hover:bg-black text-white text-center py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    Back to Dashboard
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </Protected>
      );
    } else {
      return (
        <Protected>
          <Navbar />
          <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 py-12 px-4">
            <div className="max-w-3xl mx-auto">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-12 text-center">
                <XCircle className="w-20 h-20 text-red-500 mx-auto mb-4" />
                <h2 className="text-3xl font-bold text-gray-900 mb-2">Verification Failed</h2>
                <p className="text-lg text-red-600 mb-4">{verificationResult.message}</p>
                {verificationResult.attemptsRemaining > 0 ? (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                    <p className="text-amber-800">
                      You have <strong>{verificationResult.attemptsRemaining}</strong> attempt{verificationResult.attemptsRemaining !== 1 ? 's' : ''} remaining.
                    </p>
                    <p className="text-sm text-amber-700 mt-2">Resetting questions...</p>
                  </div>
                ) : (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                    <p className="text-red-800">
                      No more attempts remaining. If this is your item, please contact campus security.
                    </p>
                    <p className="text-sm text-red-700 mt-2">Redirecting...</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Protected>
      );
    }
  }

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
  const isLastQuestion = currentQuestionIndex === questions.length - 1;
  const allQuestionsAnswered = questions.every(q => answers[q.id]);

  return (
    <Protected>
      <Navbar />
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 py-12 px-4">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link
              href="/found"
              className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Found Items
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Verify Ownership</h1>
            <p className="text-gray-600">Answer security questions to prove you own this item</p>
          </div>

          {/* Item Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              <strong>Item:</strong> {itemTitle}
            </p>
            <p className="text-xs text-blue-700 mt-1">
              These questions were set by the person who found your item.
            </p>
          </div>

          {/* Main Card */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8">
            {/* Progress */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-700">
                  Question {currentQuestionIndex + 1} of {questions.length}
                </span>
                <span className="text-xs bg-amber-100 text-amber-800 px-3 py-1 rounded-full font-medium">
                  Attempt {attempts + 1}/{maxAttempts}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-gray-900 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Question */}
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">{currentQuestion.question}</h2>
              
              {/* Multiple Choice Options */}
              <div className="space-y-3">
                {['A', 'B', 'C', 'D'].map((choice) => {
                  const choiceKey = `choice_${choice.toLowerCase()}`;
                  const choiceText = currentQuestion[choiceKey];
                  
                  if (!choiceText) return null;

                  const isSelected = answers[currentQuestion.id] === choice;

                  return (
                    <button
                      key={choice}
                      onClick={() => handleAnswerSelect(currentQuestion.id, choice)}
                      className={`w-full text-left p-4 rounded-lg border-2 transition-all duration-200 ${
                        isSelected
                          ? 'border-gray-900 bg-gray-900 text-white shadow-lg'
                          : 'border-gray-200 bg-white hover:border-gray-400 hover:shadow-md'
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                          isSelected
                            ? 'bg-white text-gray-900'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {choice}
                        </div>
                        <span className="flex-1 font-medium">{choiceText}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Navigation */}
            <div className="flex gap-4">
              {currentQuestionIndex > 0 && (
                <button
                  onClick={handleBack}
                  className="px-6 py-3 bg-white/90 hover:bg-white text-gray-900 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </button>
              )}
              
              {!isLastQuestion ? (
                <button
                  onClick={handleNext}
                  disabled={!answers[currentQuestion.id]}
                  className="flex-1 px-6 py-3 bg-gray-900 hover:bg-black text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  Next Question
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!allQuestionsAnswered || verifying}
                  className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {verifying ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      Verifying...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      Submit Answers
                    </>
                  )}
                </button>
              )}
            </div>

            {/* Help Text */}
            <div className="mt-6 text-center text-sm text-gray-500">
              You need to answer at least 67% of questions correctly to verify ownership.
            </div>
          </div>
        </div>
      </div>
    </Protected>
  );
}
