import { formatDistanceToNow } from 'date-fns';
import { Mail, Loader2, ShieldAlert } from 'lucide-react';

export default function EmailList({ folderName, emails, isLoading, selectedEmailId, onSelectEmail }) {
  if (isLoading) {
    return (
      <div className="email-list-panel">
        <div className="email-list-header">
          <div className="email-list-title">{folderName}</div>
        </div>
        <div className="loading-wrapper">
          <Loader2 className="spinner" />
          Fetching emails...
        </div>
      </div>
    );
  }

  return (
    <div className="email-list-panel">
      <div className="email-list-header">
        <div className="email-list-title">{folderName}</div>
        <div className={`email-count-badge ${folderName.toLowerCase() === 'junk' ? 'junk-badge' : ''}`}>
          {emails.length}
        </div>
      </div>

      <div className="email-list-scroll">
        {emails.length === 0 ? (
          <div className="no-emails">
            <Mail className="no-emails-icon" style={{ margin: '0 auto' }} />
            No emails found in this folder.
          </div>
        ) : (
          emails.map(email => (
            <div 
              key={email.id} 
              className={`email-row ${selectedEmailId === email.id ? 'selected' : ''}`}
              onClick={() => onSelectEmail(email)}
            >
              <div className="email-row-meta">
                <div className="email-row-sender">{email.sender.split('<')[0].trim()}</div>
                <div className="email-row-date">
                  {email.received_at ? formatDistanceToNow(new Date(email.received_at.endsWith('Z') ? email.received_at : email.received_at + 'Z'), { addSuffix: true }) : ''}
                </div>
              </div>
              <div className="email-row-subject">
                {email.subject}
                {email.is_junk && folderName !== 'Junk' && <span className="junk-tag" style={{ marginLeft: 6 }}>JUNK</span>}
              </div>
              <div className="email-row-preview">
                {email.body.substring(0, 60)}...
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
