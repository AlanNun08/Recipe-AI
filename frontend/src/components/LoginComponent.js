import React, { useState } from 'react';
import { authService } from '../services/auth';

const LoginComponent = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showVerification, setShowVerification] = useState(false);
  const [verificationData, setVerificationData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const result = await authService.login({ email, password });
      
      console.log('Login result:', result); // Debug log
      
      if (result.status === 'verification_required') {
        // Password was correct but account needs verification
        console.log('Verification required, showing verification form');
        setVerificationData(result);
        setShowVerification(true);
        setError('Account not verified. A new verification code has been sent to your email.');
      } else if (result.status === 'success') {
        // Login successful
        console.log('Login successful:', result);
        alert('Login successful!');
        // TODO: Redirect to dashboard or update app state
        // window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerification = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const result = await authService.verifyEmailAndLogin(verificationData.user_id, verificationCode);
      console.log('Verification successful:', result);
      alert('Account verified successfully! You are now logged in.');
      setShowVerification(false);
      setVerificationData(null);
      setVerificationCode('');
      // TODO: Redirect to dashboard or update app state
      // window.location.href = '/dashboard';
    } catch (error) {
      console.error('Verification error:', error);
      setError('Verification failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    setLoading(true);
    setError('');
    
    try {
      await authService.resendCode(verificationData.email);
      alert('New verification code sent to your email!');
    } catch (error) {
      console.error('Resend error:', error);
      setError('Failed to resend code: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    setShowVerification(false);
    setVerificationData(null);
    setVerificationCode('');
    setError('');
  };

  // Show verification form if verification is required
  if (showVerification && verificationData) {
    return (
      <div style={{ maxWidth: '400px', margin: '0 auto', padding: '20px' }}>
        <h2>Verify Your Account</h2>
        <p>We sent a verification code to <strong>{verificationData.email}</strong></p>
        
        {error && (
          <div style={{ color: 'red', marginBottom: '10px' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleVerification}>
          <div style={{ marginBottom: '10px' }}>
            <input
              type="text"
              placeholder="Enter 6-digit verification code"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value)}
              maxLength="6"
              required
              style={{ width: '100%', padding: '10px', fontSize: '16px' }}
            />
          </div>
          <button 
            type="submit" 
            disabled={loading || verificationCode.length !== 6}
            style={{ 
              width: '100%', 
              padding: '10px', 
              fontSize: '16px',
              backgroundColor: loading ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Verifying...' : 'Verify Account'}
          </button>
        </form>
        
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <button 
            onClick={handleResendCode}
            disabled={loading}
            style={{ 
              padding: '8px 16px', 
              marginRight: '10px',
              backgroundColor: loading ? '#ccc' : '#28a745',
              color: 'white',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Sending...' : 'Resend Code'}
          </button>
          
          <button 
            onClick={handleBackToLogin}
            disabled={loading}
            style={{ 
              padding: '8px 16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  // Show login form
  return (
    <div style={{ maxWidth: '400px', margin: '0 auto', padding: '20px' }}>
      <h2>Login</h2>
      
      {error && (
        <div style={{ color: 'red', marginBottom: '10px' }}>
          {error}
        </div>
      )}
      
      <form onSubmit={handleLogin}>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', fontSize: '16px' }}
          />
        </div>
        
        <div style={{ marginBottom: '10px' }}>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', fontSize: '16px' }}
          />
        </div>
        
        <button 
          type="submit" 
          disabled={loading}
          style={{ 
            width: '100%', 
            padding: '10px', 
            fontSize: '16px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default LoginComponent;
