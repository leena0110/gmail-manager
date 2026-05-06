import { useState } from 'react';
import { Plus, ShieldAlert, ChevronRight, Trash2, Mailbox } from 'lucide-react';

export default function Sidebar({ accounts, selectedAccount, selectedFolder, onSelectFolder, onAddAccount, onDeleteAccount }) {
  const [expandedAccounts, setExpandedAccounts] = useState({});
  const toggleAccount = (email) => setExpandedAccounts(prev => ({ ...prev, [email]: !prev[email] }));
  const handleDelete = (e, email) => { e.stopPropagation(); if (window.confirm(`Remove ${email}?`)) onDeleteAccount(email); };

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
          const isExpanded = expandedAccounts[account.email] !== false;
          return (
            <div key={account.email} className="account-item">
              <div className={`account-folder ${selectedAccount === account.email ? 'active' : ''}`} onClick={() => toggleAccount(account.email)}>
                <div className="account-avatar">{account.email.charAt(0)}</div>
                <div className="account-info"><div className="account-email-text">{account.email}</div></div>
                <button className="btn-delete-account" onClick={(e) => handleDelete(e, account.email)}><Trash2 size={12} /></button>
                <ChevronRight size={12} className={`account-chevron ${isExpanded ? 'open' : ''}`} />
              </div>
              {isExpanded && (
                <div className="account-subfolders">
                  <div className={`subfolder-item ${selectedAccount === account.email && selectedFolder === 'inbox' ? 'active' : ''}`} onClick={() => onSelectFolder(account.email, 'inbox')}><Mailbox size={13} /> Inbox</div>
                  <div className={`subfolder-item junk ${selectedAccount === account.email && selectedFolder === 'junk' ? 'active' : ''}`} onClick={() => onSelectFolder(account.email, 'junk')}><ShieldAlert size={13} /> Junk</div>
                </div>
              )}
            </div>
          );
        })}
      </div>

    </div>
  );
}
