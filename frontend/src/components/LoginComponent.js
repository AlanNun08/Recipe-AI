import React, { useState } from 'react';
import { authService } from '../services/auth';

const LoginComponent = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showVerification, setShowVerification] = useState(false);
  const [verificationData, setVerificationData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    
    try {
      const result = await authService.login({ email, password });
      
      if (result.status === 'verification_required') {
        // Password was correct but account needs verification
        setVerificationData(result);
        setShowVerification(true);
        alert('Account not verified. Please check your email for verification code.');
      } else if (result.status === 'success') {
        // Login successful
        alert('Login successful!');
        // Redirect to dashboard or update app state
      }
    } catch (error) {
      alert('Login failed: ' + error.message);
    }
  };

  const handleVerification = async (e) => {
    e.preventDefault();
    
    try {
      await authService.verifyEmailAndLogin(verificationData.user_id, verificationCode);
      alert('Account verified successfully!');
      setShowVerification(false);
      // Redirect to dashboard or update app state
    } catch (error) {
      alert('Verification failed: ' + error.message);
    }
  };

  const handleResendCode = async () => {
    try {
      await authService.resendCode(verificationData.email);
      alert('New verification code sent to your email!');
    } catch (error) {
      alert('Failed to resend code: ' + error.message);
    }
  };

  if (showVerification) {
    return (
      <div>
        <h2>Verify Your Account</h2>
        <p>We sent a verification code to {verificationData.email}</p>
        <form onSubmit={handleVerification}>
          <input
            type="text"
            placeholder="Enter verification code"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value)}
            required
          />
          <button type="submit">Verify Account</button>
        </form>
        <button onClick={handleResendCode}>Resend Code</button>
        <button onClick={() => setShowVerification(false)}>Back to Login</button>
      </div>
    );
  }

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Login</button>
      </form>
    </div>
  );
};

export default LoginComponent;
