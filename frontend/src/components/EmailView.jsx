import { format } from 'date-fns';
import { Mail, ShieldAlert } from 'lucide-react';

export default function EmailView({ email }) {
  if (!email) {
    return (
      <div className="email-view-panel">
        <div className="email-placeholder">
          <Mail className="email-placeholder-icon" />
          <h2>Select an email to read</h2>
        </div>
      </div>
    );
  }

  const getSenderInitial = (sender) => {
    const name = sender.split('<')[0].trim();
    return name ? name.charAt(0).toUpperCase() : '?';
  };

  const getSenderName = (sender) => sender.split('<')[0].trim();
  
  const getSenderEmail = (sender) => {
    const match = sender.match(/<([^>]+)>/);
    return match ? match[1] : sender;
  };

  return (
    <div className="email-view-panel">
      <div className="email-view-header">
        <h1 className="email-view-subject">{email.subject}</h1>
        
        <div className="email-view-meta">
          <div className="email-view-sender">
            <div className="email-view-avatar">{getSenderInitial(email.sender)}</div>
            <div className="email-view-sender-info">
              <span className="email-view-sender-name">{getSenderName(email.sender)}</span>
              <span className="email-view-sender-email">{getSenderEmail(email.sender)}</span>
            </div>
          </div>
          
          {email.is_junk && (
            <div className="email-view-junk-badge">
              <ShieldAlert size={14} /> AI Flagged as Junk
            </div>
          )}

          <div className="email-view-date">
            {email.received_at ? format(new Date(email.received_at.endsWith('Z') ? email.received_at : email.received_at + 'Z'), 'MMM d, yyyy • h:mm a') : 'Unknown date'}
          </div>
        </div>
      </div>

      <div className="email-view-body">
        <div className="email-view-body-text">
          {email.body || '(No text content)'}
        </div>
      </div>
    </div>
  );
}
