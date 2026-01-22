import React, { useState, useEffect } from 'react';
import { authService } from '../services/auth';

const VerificationPage = ({ email, onVerificationSuccess, onBackToLogin }) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  // Auto-send verification code when component mounts with email
  useEffect(() => {
    if (email) {
      sendVerificationCode();
    }
  }, [email]);

  const sendVerificationCode = async () => {
    if (!email) return;
    
    try {
      await authService.resendVerificationCode(email);
      setCodeSent(true);
      setError('');
    } catch (error) {
      console.error('Failed to send verification code:', error);
      setError('Failed to send verification code. Please try again.');
    }
  };

  const handleVerification = async (e) => {
    e.preventDefault();
    
    if (!email) {
      setError('Email not found. Please login again.');
      return;
    }

    if (verificationCode.length !== 6) {
      setError('Please enter a valid 6-digit code.');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const result = await authService.verifyCode(email, verificationCode);
      console.log('Verification successful:', result);
      
      // Call success callback with user data
      if (onVerificationSuccess) {
        onVerificationSuccess(result);
      } else {
        alert('Account verified successfully! You are now logged in.');
        window.location.href = '/dashboard';
      }
      
    } catch (error) {
      console.error('Verification error:', error);
      setError(error.message || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!email) {
      setError('Email not found. Please login again.');
      return;
    }

    setResendLoading(true);
    setError('');
    
    try {
      await sendVerificationCode();
    } catch (error) {
      console.error('Resend error:', error);
      setError('Failed to resend code. Please try again.');
    } finally {
      setResendLoading(false);
    }
  };

  const handleBackToLogin = () => {
    if (onBackToLogin) {
      onBackToLogin();
    } else {
      window.location.href = '/login';
    }
  };

  if (!email) {
    return (
      <div style={{ maxWidth: '400px', margin: '0 auto', padding: '20px', textAlign: 'center' }}>
        <h2>Verification Required</h2>
        <p style={{ color: 'red' }}>No email found. Please login again.</p>
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
          {email}
        </p>
      </div>
      
      {codeSent && (
        <div style={{ 
          color: '#28a745',
          marginBottom: '15px',
          backgroundColor: '#d4edda',
          padding: '12px',
          borderRadius: '5px',
          border: '1px solid #c3e6cb'
        }}>
          ✅ Verification code sent! Check your email.
        </div>
      )}
      
      {error && (
        <div style={{ 
          color: '#dc3545', 
          marginBottom: '15px',
          backgroundColor: '#f8d7da',
          padding: '12px',
          borderRadius: '5px',
          border: '1px solid #f5c6cb'
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
          disabled={resendLoading || loading}
          style={{ 
            padding: '8px 16px', 
            marginRight: '10px',
            backgroundColor: resendLoading || loading ? '#ccc' : '#17a2b8',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: resendLoading || loading ? 'not-allowed' : 'pointer',
            fontSize: '14px'
          }}
        >
          {resendLoading ? 'Sending...' : 'Resend Code'}
        </button>
        
        <button 
          onClick={handleBackToLogin}
          disabled={loading || resendLoading}
          style={{ 
            padding: '8px 16px',
            backgroundColor: 'transparent',
            color: '#6c757d',
            border: '1px solid #6c757d',
            borderRadius: '5px',
            cursor: loading || resendLoading ? 'not-allowed' : 'pointer',
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
          Code expires in 15 minutes.
        </p>
      </div>
    </div>
  );
};

export default VerificationPage;
