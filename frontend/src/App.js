import React, { useState, useEffect } from 'react';
import LoginComponent from './components/LoginComponent';
import VerificationPage from './components/VerificationPage';
import WelcomeOnboarding from './components/WelcomeOnboarding';
import DashboardScreen from './components/DashboardScreen';
import { authService } from './services/auth';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('login'); // 'login', 'verify', 'onboarding', 'dashboard'
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userPreferences, setUserPreferences] = useState(null);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Check if user is already logged in
    const storedUser = localStorage.getItem('user');
    const storedPreferences = localStorage.getItem('userPreferences');
    
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
        
        // Check if user has completed onboarding
        if (storedPreferences) {
          setUserPreferences(JSON.parse(storedPreferences));
          setCurrentPage('dashboard');
        } else {
          // User is logged in but hasn't completed onboarding
          setCurrentPage('onboarding');
        }
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('userPreferences');
      }
    } else {
      // Check if there's pending verification
      const pendingVerification = authService.getPendingVerification();
      if (pendingVerification) {
        setCurrentPage('verify');
      }
    }
    setLoading(false);
  }, []);

  const showNotification = (message, type = 'info') => {
    const id = Date.now();
    const notification = { id, message, type };
    setNotifications(prev => [...prev, notification]);
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  const handleVerificationRequired = (verificationData) => {
    console.log('Navigating to verification page:', verificationData);
    setCurrentPage('verify');
  };

  const handleLoginSuccess = (loginData) => {
    console.log('Login successful, navigating to onboarding:', loginData);
    setUser(loginData.user);
    
    // Check if user has existing preferences
    const storedPreferences = localStorage.getItem('userPreferences');
    if (storedPreferences) {
      setUserPreferences(JSON.parse(storedPreferences));
      setCurrentPage('dashboard');
    } else {
      setCurrentPage('onboarding');
    }
  };

  const handleVerificationSuccess = (verificationData) => {
    console.log('Verification successful, navigating to onboarding:', verificationData);
    
    // Check if user has existing preferences
    const storedPreferences = localStorage.getItem('userPreferences');
    if (storedPreferences) {
      setUserPreferences(JSON.parse(storedPreferences));
      setCurrentPage('dashboard');
    } else {
      setCurrentPage('onboarding');
    }
  };

  const handleOnboardingComplete = (preferences) => {
    console.log('Onboarding completed:', preferences);
    setUserPreferences(preferences);
    setCurrentPage('dashboard');
  };

  const handleOnboardingSkip = () => {
    console.log('Onboarding skipped');
    setCurrentPage('dashboard');
  };

  const handleBackToLogin = () => {
    console.log('Navigating back to login');
    setCurrentPage('login');
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setUserPreferences(null);
    localStorage.removeItem('userPreferences');
    setCurrentPage('login');
  };

  if (loading) {
    return (
      <div className="App" style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div style={{ color: 'white', fontSize: '18px' }}>
          🔄 Loading your AI Chef experience...
        </div>
      </div>
    );
  }

  // Render current page
  return (
    <div className="App">
      {/* Notifications */}
      {notifications.length > 0 && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          {notifications.map(notification => (
            <div
              key={notification.id}
              style={{
                padding: '15px 20px',
                borderRadius: '10px',
                color: 'white',
                fontWeight: 'bold',
                background: notification.type === 'error' ? '#dc3545' :
                           notification.type === 'warning' ? '#ffc107' :
                           notification.type === 'success' ? '#28a745' : '#007bff',
                boxShadow: '0 5px 15px rgba(0,0,0,0.2)',
                maxWidth: '300px'
              }}
            >
              {notification.message}
            </div>
          ))}
        </div>
      )}

      {currentPage === 'verify' && (
        <VerificationPage
          onVerificationSuccess={handleVerificationSuccess}
          onBackToLogin={handleBackToLogin}
        />
      )}
      
      {currentPage === 'onboarding' && (
        <WelcomeOnboarding
          onComplete={handleOnboardingComplete}
          onSkip={handleOnboardingSkip}
        />
      )}
      
      {currentPage === 'dashboard' && (
        <DashboardScreen
          user={user}
          userPreferences={userPreferences}
          onLogout={handleLogout}
          showNotification={showNotification}
          setCurrentScreen={setCurrentPage}
        />
      )}
      
      {currentPage === 'login' && (
        <LoginComponent
          onVerificationRequired={handleVerificationRequired}
          onLoginSuccess={handleLoginSuccess}
        />
      )}
    </div>
  );
}

export default App;