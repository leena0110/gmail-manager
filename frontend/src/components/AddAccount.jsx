import { X, Plus, LogIn } from 'lucide-react';

export default function AddAccount({ onClose }) {
  const handleGoogleLogin = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/auth/login');
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend error:", errorText);
        alert(`Backend Error: ${response.status}\nMake sure your .env file is correct.`);
        return;
      }

      const data = await response.json();
      if (data.auth_url) {
        // Redirect user to Google Login URL
        window.location.href = data.auth_url;
      } else {
        alert('Error: Backend did not return a valid Google login URL.');
      }
    } catch (error) {
      console.error('Failed to get login URL:', error);
      alert('Could not connect to backend!\n\nPlease open a terminal and run:\ncd backend\nuvicorn main:app --reload');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          <X size={20} />
        </button>
        
        <div className="modal-icon">
          <Plus size={32} color="white" />
        </div>
        
        <h2 className="modal-title">Connect Gmail Account</h2>
        <p className="modal-subtitle">
          Add a new Gmail account to manage your inbox and automatically detect junk emails.
        </p>

        <div className="modal-steps">
          <div className="modal-step">
            <div className="modal-step-num">1</div>
            <div className="modal-step-text">Sign in securely with your Google Account</div>
          </div>
          <div className="modal-step">
            <div className="modal-step-num">2</div>
            <div className="modal-step-text">Grant read-only access to your emails</div>
          </div>
          <div className="modal-step">
            <div className="modal-step-num">3</div>
            <div className="modal-step-text">Our AI instantly starts sorting your inbox</div>
          </div>
        </div>

        <button className="btn-google-signin" onClick={handleGoogleLogin}>
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" className="google-icon" />
          Continue with Google
        </button>
      </div>
    </div>
  );
}
