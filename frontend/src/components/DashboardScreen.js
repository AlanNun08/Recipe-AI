import React, { useState, useEffect } from 'react';
import { authService } from '../services/auth';

const DashboardScreen = ({ 
  user, 
  userPreferences, 
  onLogout, 
  showNotification, 
  setCurrentScreen 
}) => {
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    if (!user?.id) {
      setLoading(false);
      return;
    }

    try {
      // Load user stats and recent activity
      const response = await fetch(`${API}/api/user/dashboard/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setDashboardStats(data);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Continue without stats if API fails
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      id: 'recipe-generator',
      title: '🍳 Generate Recipe',
      description: 'Create AI-powered recipes with Walmart shopping',
      gradient: 'from-orange-500 to-red-600',
      action: () => setCurrentScreen('recipe-generation')
    },
    {
      id: 'weekly-planner',
      title: '📅 Weekly Planner',
      description: 'Plan your entire week with AI meal planning',
      gradient: 'from-green-500 to-blue-600',
      action: () => setCurrentScreen('weekly-recipes')
    },
    {
      id: 'starbucks-generator',
      title: '☕ Starbucks Drinks',
      description: 'Generate secret menu drinks with ordering scripts',
      gradient: 'from-green-600 to-green-700',
      action: () => setCurrentScreen('starbucks-generator')
    },
    {
      id: 'recipe-history',
      title: '📚 Recipe History',
      description: 'Browse your saved recipes and favorites',
      gradient: 'from-purple-500 to-pink-600',
      action: () => setCurrentScreen('recipe-history')
    },
    {
      id: 'tutorial',
      title: '📖 How to Use',
      description: 'Learn all features with interactive tutorials',
      gradient: 'from-blue-500 to-indigo-600',
      action: () => setCurrentScreen('tutorial')
    },
    {
      id: 'settings',
      title: '⚙️ Settings',
      description: 'Manage your account and preferences',
      gradient: 'from-gray-500 to-gray-600',
      action: () => setCurrentScreen('settings')
    }
  ];

  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: 'white', fontSize: '18px' }}>
          🔄 Loading your dashboard...
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* Welcome Header */}
        <div style={{
          background: 'white',
          borderRadius: '20px',
          padding: '30px',
          marginBottom: '30px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <h1 style={{ 
            fontSize: '3rem',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '10px'
          }}>
            🤖 Welcome to BuildYourSmartCart!
          </h1>
          <p style={{ color: '#666', fontSize: '1.2rem', marginBottom: '10px' }}>
            Your AI-powered recipe and grocery companion
          </p>
          {user && (
            <p style={{ color: '#888', fontSize: '1rem' }}>
              👋 Hello, {user.email}! Ready to cook something amazing?
            </p>
          )}
        </div>

        {/* Quick Stats */}
        {dashboardStats && (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '20px', 
            marginBottom: '30px' 
          }}>
            <div style={{
              background: 'white',
              borderRadius: '15px',
              padding: '20px',
              textAlign: 'center',
              boxShadow: '0 5px 20px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '10px' }}>🍳</div>
              <h3 style={{ color: '#333', marginBottom: '5px' }}>
                {dashboardStats.total_recipes || 0}
              </h3>
              <p style={{ color: '#666', margin: 0 }}>Recipes Generated</p>
            </div>
            
            <div style={{
              background: 'white',
              borderRadius: '15px',
              padding: '20px',
              textAlign: 'center',
              boxShadow: '0 5px 20px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '10px' }}>☕</div>
              <h3 style={{ color: '#333', marginBottom: '5px' }}>
                {dashboardStats.total_starbucks || 0}
              </h3>
              <p style={{ color: '#666', margin: 0 }}>Starbucks Drinks</p>
            </div>
            
            <div style={{
              background: 'white',
              borderRadius: '15px',
              padding: '20px',
              textAlign: 'center',
              boxShadow: '0 5px 20px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '10px' }}>🛒</div>
              <h3 style={{ color: '#333', marginBottom: '5px' }}>
                {dashboardStats.total_shopping_lists || 0}
              </h3>
              <p style={{ color: '#666', margin: 0 }}>Shopping Lists</p>
            </div>
            
            <div style={{
              background: 'white',
              borderRadius: '15px',
              padding: '20px',
              textAlign: 'center',
              boxShadow: '0 5px 20px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '10px' }}>⭐</div>
              <h3 style={{ color: '#333', marginBottom: '5px' }}>
                {user?.subscription?.status === 'trialing' ? 'Trial' : 'Premium'}
              </h3>
              <p style={{ color: '#666', margin: 0 }}>Account Status</p>
            </div>
          </div>
        )}

        {/* User Info Card */}
        {user && (
          <div style={{ 
            background: 'white',
            borderRadius: '15px',
            padding: '25px',
            marginBottom: '30px',
            boxShadow: '0 5px 20px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#333', marginBottom: '15px' }}>👤 Account Information</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
              <div>
                <strong>📧 Email:</strong> {user.email}
              </div>
              <div>
                <strong>✅ Verified:</strong> {user.is_verified ? 'Yes' : 'No'}
              </div>
              <div>
                <strong>💳 Subscription:</strong> {user.subscription?.status || 'Unknown'}
              </div>
              <div>
                <strong>📅 Joined:</strong> {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
              </div>
            </div>
          </div>
        )}

        {/* Preferences Card */}
        {userPreferences && (
          <div style={{ 
            background: 'white',
            borderRadius: '15px',
            padding: '25px',
            marginBottom: '30px',
            boxShadow: '0 5px 20px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#333', marginBottom: '15px' }}>🎯 Your Preferences</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
              {userPreferences.dietaryRestrictions?.length > 0 && (
                <div>
                  <strong>🥗 Dietary:</strong> {userPreferences.dietaryRestrictions.join(', ')}
                </div>
              )}
              {userPreferences.cuisinePreferences?.length > 0 && (
                <div>
                  <strong>🍽️ Cuisines:</strong> {userPreferences.cuisinePreferences.join(', ')}
                </div>
              )}
              {userPreferences.cookingSkillLevel && (
                <div>
                  <strong>👨‍🍳 Skill Level:</strong> {userPreferences.cookingSkillLevel}
                </div>
              )}
              {userPreferences.householdSize && (
                <div>
                  <strong>🏠 Household:</strong> {userPreferences.householdSize} people
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick Actions Grid */}
        <div style={{ 
          background: 'white',
          borderRadius: '20px',
          padding: '30px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
          marginBottom: '30px'
        }}>
          <h3 style={{ color: '#333', marginBottom: '25px', textAlign: 'center', fontSize: '1.5rem' }}>
            🚀 What would you like to do today?
          </h3>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
            gap: '20px' 
          }}>
            {quickActions.map((action) => (
              <button
                key={action.id}
                onClick={action.action}
                style={{
                  background: `linear-gradient(135deg, var(--tw-gradient-stops))`,
                  backgroundImage: `linear-gradient(135deg, ${action.gradient.split(' ')[1]}, ${action.gradient.split(' ')[3]})`,
                  color: 'white',
                  border: 'none',
                  borderRadius: '15px',
                  padding: '25px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  textAlign: 'left',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 5px 15px rgba(0,0,0,0.1)'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-5px)';
                  e.target.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0px)';
                  e.target.style.boxShadow = '0 5px 15px rgba(0,0,0,0.1)';
                }}
              >
                <div style={{ fontSize: '1.4rem', fontWeight: 'bold', marginBottom: '10px' }}>
                  {action.title}
                </div>
                <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
                  {action.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Logout Button */}
        <div style={{ textAlign: 'center' }}>
          <button 
            onClick={onLogout}
            style={{
              padding: '15px 30px',
              background: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '10px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              boxShadow: '0 5px 15px rgba(220, 53, 69, 0.3)',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 8px 20px rgba(220, 53, 69, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0px)';
              e.target.style.boxShadow = '0 5px 15px rgba(220, 53, 69, 0.3)';
            }}
          >
            🚪 Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardScreen;
