import React, { useState, useEffect } from 'react';
import LoginComponent from './components/LoginComponent';
import VerificationPage from './components/VerificationPage';
import { authService } from './services/auth';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('login'); // 'login', 'verify', 'dashboard'
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
        setCurrentPage('dashboard');
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('user');
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

  const handleVerificationRequired = (verificationData) => {
    console.log('Navigating to verification page:', verificationData);
    setCurrentPage('verify');
  };

  const handleLoginSuccess = (loginData) => {
    console.log('Login successful, navigating to dashboard:', loginData);
    setUser(loginData.user);
    setCurrentPage('dashboard');
  };

  const handleVerificationSuccess = (verificationData) => {
    console.log('Verification successful, navigating to dashboard:', verificationData);
    // You might want to fetch updated user data here
    setCurrentPage('dashboard');
  };

  const handleBackToLogin = () => {
    console.log('Navigating back to login');
    setCurrentPage('login');
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setCurrentPage('login');
  };

  if (loading) {
    return (
      <div className="App" style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  // Render current page
  return (
    <div className="App">
      {currentPage === 'verify' && (
        <VerificationPage
          onVerificationSuccess={handleVerificationSuccess}
          onBackToLogin={handleBackToLogin}
        />
      )}
      
      {currentPage === 'dashboard' && (
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
          <h1>Welcome to BuildYourSmartCart!</h1>
          {user && (
            <div style={{ 
              backgroundColor: '#f8f9fa', 
              padding: '20px', 
              borderRadius: '8px', 
              marginBottom: '20px' 
            }}>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>Account verified:</strong> {user.is_verified ? 'Yes' : 'No'}</p>
              <p><strong>Subscription:</strong> {user.subscription?.status || 'Unknown'}</p>
            </div>
          )}
          <button 
            onClick={handleLogout}
            style={{
              padding: '12px 24px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Logout
          </button>
        </div>
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