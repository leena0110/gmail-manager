import { format, isToday, isYesterday } from 'date-fns';
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
          {emails.filter(e => e.is_unread).length}
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
                <div className="email-row-sender" style={{ fontWeight: email.is_unread ? 700 : 500, color: email.is_unread ? 'var(--accent)' : 'var(--text-dark)' }}>
                  {email.is_unread && <span style={{ display: 'inline-block', width: 6, height: 6, background: 'var(--accent)', borderRadius: '50%', marginRight: 6, marginBottom: 1 }}></span>}
                  {email.sender.split('<')[0].trim()}
                </div>
                <div className="email-row-date">
                  {(() => {
                    try {
                      if (!email.received_at) return '';
                      // Let the browser handle the ISO string with offset correctly
                      const date = new Date(email.received_at);
                      
                      if (isNaN(date.getTime())) return 'Recently';
                      
                      if (isToday(date)) return format(date, 'h:mm a');
                      if (isYesterday(date)) return 'Yesterday';
                      return format(date, 'MMM d, h:mm a');
                    } catch (e) {
                      return 'Recently';
                    }
                  })()}
                </div>
              </div>
              <div className="email-row-subject">
                {email.subject}
                {email.is_junk && folderName !== 'Junk' && <span className="junk-tag" style={{ marginLeft: 6 }}>JUNK</span>}
              </div>
              <div className="email-row-preview">
                {email.body.replace(/<[^>]*>?/gm, '').substring(0, 60)}...
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
