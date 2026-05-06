import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle, XCircle } from 'lucide-react';

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const isSuccess = searchParams.get('success') === 'true';
  const errorMsg = searchParams.get('error');

  useEffect(() => {
    // Redirect back to dashboard after 3 seconds
    const timer = setTimeout(() => {
      navigate('/');
    }, 3000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="oauth-callback-page">
      <div className="oauth-callback-card">
        {isSuccess ? (
          <>
            <CheckCircle className="oauth-status-icon" style={{ color: 'var(--accent-secondary)' }} />
            <h1 className="oauth-title">Account Connected!</h1>
            <p className="oauth-subtitle">
              Your Gmail account was successfully linked. We're redirecting you back to your dashboard to fetch your emails...
            </p>
          </>
        ) : (
          <>
            <XCircle className="oauth-status-icon" style={{ color: 'var(--accent-danger)' }} />
            <h1 className="oauth-title">Connection Failed</h1>
            <p className="oauth-subtitle">
              We couldn't connect your Gmail account. {errorMsg && `Error: ${errorMsg}`}
            </p>
          </>
        )}
        <button className="btn-primary" onClick={() => navigate('/')}>
          Return to Dashboard
        </button>
      </div>
    </div>
  );
}
