import { useState } from 'react';
import { Plus, ShieldAlert, ChevronRight, Trash2, Mailbox, Send, PenLine } from 'lucide-react';

export default function Sidebar({ accounts, selectedAccount, selectedFolder, onSelectFolder, onAddAccount, onDeleteAccount, onCompose, onSync }) {
  const [expandedAccounts, setExpandedAccounts] = useState({});
  
  // Folders are hidden by default, so we only expand if explicitly set to true
  const toggleAccount = (email) => setExpandedAccounts(prev => ({ ...prev, [email]: !prev[email] }));
  
  const handleDelete = (e, email) => { 
    e.stopPropagation(); 
    if (window.confirm(`Remove ${email}?`)) onDeleteAccount(email); 
  };
  
  const handleCompose = (e, email) => {
    e.stopPropagation();
    onCompose(email);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">✉</div>
          <div className="sidebar-logo-text">Gmail Manager</div>
        </div>
        <button className="btn-add-account" onClick={onAddAccount}><Plus size={14} /> Add Account</button>
      </div>
      <div className="sidebar-section-label">Connected Accounts</div>
      <div className="sidebar-accounts">
        {accounts.length === 0 ? (
          <div className="sidebar-empty">No accounts connected yet.</div>
        ) : accounts.map(account => {
          // Hidden by default
          const isExpanded = expandedAccounts[account.email] === true;
          return (
            <div key={account.email} className="account-item">
              <div className={`account-folder ${selectedAccount === account.email && !isExpanded ? 'active' : ''}`} onClick={() => toggleAccount(account.email)}>
                <div className="account-avatar">{account.email.charAt(0).toUpperCase()}</div>
                <div className="account-info" title={account.email}>
                  <div className="account-email-text" title={account.email}>{account.email}</div>
                </div>
                <button className="btn-icon compose-btn-small" onClick={(e) => handleCompose(e, account.email)} title="Compose"><PenLine size={13} /></button>
                <button className="btn-delete-account" onClick={(e) => handleDelete(e, account.email)} title="Remove Account"><Trash2 size={12} /></button>
                <ChevronRight size={12} className={`account-chevron ${isExpanded ? 'open' : ''}`} />
              </div>
              {isExpanded && (
                <div className="account-subfolders">
                  <div className={`subfolder-item ${selectedAccount === account.email && selectedFolder === 'inbox' ? 'active' : ''}`} onClick={() => onSelectFolder(account.email, 'inbox')}>
                    <div className="subfolder-icon-text"><Mailbox size={13} /> Inbox</div>
                    {account.unread_count > 0 && <div className="unread-badge">{account.unread_count}</div>}
                  </div>
                  <div className={`subfolder-item ${selectedAccount === account.email && selectedFolder === 'sent' ? 'active' : ''}`} onClick={() => onSelectFolder(account.email, 'sent')}>
                    <div className="subfolder-icon-text"><Send size={13} /> Sent</div>
                  </div>
                  <div className={`subfolder-item junk ${selectedAccount === account.email && selectedFolder === 'junk' ? 'active' : ''}`} onClick={() => onSelectFolder(account.email, 'junk')}>
                    <div className="subfolder-icon-text"><ShieldAlert size={13} /> Junk</div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
