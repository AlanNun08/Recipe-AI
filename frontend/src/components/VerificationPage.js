import React, { useState, useEffect } from 'react';
import { authService } from '../services/auth';

const VerificationPage = ({ onVerificationSuccess, onBackToLogin }) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [verificationData, setVerificationData] = useState(null);

  useEffect(() => {
    // Get pending verification data from localStorage
    const pendingData = authService.getPendingVerification();
    if (pendingData) {
      setVerificationData(pendingData);
    } else {
      // No pending verification, redirect back to login
      setError('No pending verification found. Please login again.');
    }
  }, []);

  const handleVerification = async (e) => {
    e.preventDefault();
    
    if (!verificationData) {
      setError('No verification data found. Please login again.');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const result = await authService.verifyEmailAndLogin(
        verificationData.user_id, 
        verificationCode
      );
      
      console.log('Verification successful:', result);
      
      // Clear verification data
      authService.clearPendingVerification();
      
      // Call success callback
      if (onVerificationSuccess) {
        onVerificationSuccess(result);
      } else {
        alert('Account verified successfully! You are now logged in.');
        // Default redirect or action
        window.location.href = '/dashboard';
      }
      
    } catch (error) {
      console.error('Verification error:', error);
      setError('Verification failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!verificationData) {
      setError('No verification data found. Please login again.');
      return;
    }

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
    authService.clearPendingVerification();
    if (onBackToLogin) {
      onBackToLogin();
    } else {
      // Default back to login
      window.location.href = '/login';
    }
  };

  if (!verificationData) {
    return (
      <div style={{ maxWidth: '400px', margin: '0 auto', padding: '20px', textAlign: 'center' }}>
        <h2>Verification Required</h2>
        <p style={{ color: 'red' }}>No pending verification found. Please login again.</p>
        <button 
          onClick={handleBackToLogin}
          style={{ 
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Back to Login
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '400px', margin: '0 auto', padding: '20px' }}>
      <h2>Verify Your Account</h2>
      
      <div style={{ 
        backgroundColor: '#e7f3ff', 
        padding: '15px', 
        borderRadius: '5px', 
        marginBottom: '20px',
        border: '1px solid #b3d9ff'
      }}>
        <p style={{ margin: 0, fontSize: '14px' }}>
          We sent a 6-digit verification code to:
        </p>
        <p style={{ margin: '5px 0 0 0', fontWeight: 'bold', fontSize: '16px' }}>
          {verificationData.email}
        </p>
      </div>
      
      {error && (
        <div style={{ 
          color: 'red', 
          marginBottom: '15px',
          backgroundColor: '#ffe6e6',
          padding: '10px',
          borderRadius: '5px',
          border: '1px solid #ffb3b3'
        }}>
          {error}
        </div>
      )}
      
      <form onSubmit={handleVerification}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '5px', 
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            Verification Code
          </label>
          <input
            type="text"
            placeholder="Enter 6-digit code"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            maxLength="6"
            required
            style={{ 
              width: '100%', 
              padding: '12px', 
              fontSize: '18px',
              textAlign: 'center',
              letterSpacing: '2px',
              border: '2px solid #ddd',
              borderRadius: '5px',
              outline: 'none'
            }}
            onFocus={(e) => e.target.style.borderColor = '#007bff'}
            onBlur={(e) => e.target.style.borderColor = '#ddd'}
          />
          <small style={{ color: '#666', fontSize: '12px' }}>
            Enter the 6-digit code from your email
          </small>
        </div>
        
        <button 
          type="submit" 
          disabled={loading || verificationCode.length !== 6}
          style={{ 
            width: '100%', 
            padding: '12px', 
            fontSize: '16px',
            fontWeight: 'bold',
            backgroundColor: loading || verificationCode.length !== 6 ? '#ccc' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading || verificationCode.length !== 6 ? 'not-allowed' : 'pointer',
            marginBottom: '15px'
          }}
        >
          {loading ? 'Verifying...' : 'Verify Account'}
        </button>
      </form>
      
      <div style={{ textAlign: 'center', borderTop: '1px solid #eee', paddingTop: '20px' }}>
        <p style={{ margin: '0 0 15px 0', fontSize: '14px', color: '#666' }}>
          Didn't receive the code?
        </p>
        
        <button 
          onClick={handleResendCode}
          disabled={loading}
          style={{ 
            padding: '8px 16px', 
            marginRight: '10px',
            backgroundColor: loading ? '#ccc' : '#17a2b8',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px'
          }}
        >
          {loading ? 'Sending...' : 'Resend Code'}
        </button>
        
        <button 
          onClick={handleBackToLogin}
          disabled={loading}
          style={{ 
            padding: '8px 16px',
            backgroundColor: 'transparent',
            color: '#6c757d',
            border: '1px solid #6c757d',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px'
          }}
        >
          Back to Login
        </button>
      </div>
      
      <div style={{ 
        marginTop: '20px', 
        fontSize: '12px', 
        color: '#666', 
        textAlign: 'center' 
      }}>
        <p>
          Check your spam folder if you don't see the email.
          <br />
          Code expires in 24 hours.
        </p>
      </div>
    </div>
  );
};

export default VerificationPage;
