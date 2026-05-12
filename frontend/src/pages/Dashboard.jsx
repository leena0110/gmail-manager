import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import EmailList from '../components/EmailList';
import EmailView from '../components/EmailView';
import AddAccount from '../components/AddAccount';
import ComposeModal from '../components/ComposeModal';

const API_BASE = 'http://127.0.0.1:8000';

export default function Dashboard() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [emails, setEmails] = useState([]);
  const [isLoadingEmails, setIsLoadingEmails] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [composeAccount, setComposeAccount] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => { fetchAccounts(); }, []);
  useEffect(() => {
    const id = setInterval(() => { fetchAccounts(); if (selectedAccount && selectedFolder) fetchEmails(selectedAccount, selectedFolder, true); }, 30000);
    return () => clearInterval(id);
  }, [selectedAccount, selectedFolder]);
  useEffect(() => { if (toast) { const t = setTimeout(() => setToast(null), 3000); return () => clearTimeout(t); } }, [toast]);

  const fetchAccounts = async () => { try { const r = await fetch(`${API_BASE}/accounts/`); const d = await r.json(); setAccounts(d.accounts || []); } catch(e) { console.error(e); } };
  
  const fetchEmails = async (email, folder, silent=false) => { 
    if (!silent) setIsLoadingEmails(true); 
    try { 
      const r = await fetch(`${API_BASE}/emails/${email}/${folder}`); 
      const d = await r.json(); 
      console.log(`[DEBUG] Received ${d.emails?.length || 0} emails for ${email}`);
      setEmails(d.emails || []); 
    } catch(e) { console.error("Fetch error:", e); } finally { if (!silent) setIsLoadingEmails(false); } 
  };
  
  const handleSelectFolder = (email, folder) => { setSelectedAccount(email); setSelectedFolder(folder); setSelectedEmail(null); fetchEmails(email, folder); };
  
  const handleDeleteAccount = async (email) => { 
    try { 
      const r = await fetch(`${API_BASE}/accounts/${email}`, {method:'DELETE'}); 
      if(r.ok){
        setToast({message:'Account removed',type:'success'});
        setAccounts(accounts.filter(a=>a.email!==email));
        if(selectedAccount===email){setSelectedAccount(null);setSelectedFolder(null);setEmails([]);setSelectedEmail(null);}
      } 
    } catch(e){setToast({message:'Error',type:'error'});} 
  };
  
  const handleSendEmail = async (account, to, subject, body, attachments = [], cc = '', bcc = '') => {
    try {
      console.log(`[SEND] Sending email from ${account} to ${to}...`);
      const r = await fetch(`${API_BASE}/emails/${account}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to, subject, body, attachments, cc, bcc })
      });
      
      const data = await r.json();
      console.log("[SEND] Response:", data);

      if (r.ok) {
        setToast({ message: 'Email sent successfully!', type: 'success' });
        setComposeAccount(null);
      } else {
        setToast({ message: `Failed: ${data.detail || 'Unknown error'}`, type: 'error' });
      }
    } catch (e) {
      console.error("[SEND] Critical Error:", e);
      setToast({ message: 'Connection error while sending', type: 'error' });
    }
  };

  const getFolderName = () => { 
    if(!selectedAccount) return ''; 
    if(selectedFolder === 'junk') return 'Junk Folder';
    if(selectedFolder === 'sent') return 'Sent Mail';
    return 'Inbox'; 
  };

  const handleSelectEmail = async (email) => {
    setSelectedEmail(email);
    if (email.is_unread) {
      // Mark as read locally for immediate feedback
      setEmails(prev => prev.map(e => e.id === email.id ? { ...e, is_unread: false } : e));
      try {
        await fetch(`${API_BASE}/emails/${selectedAccount}/read/${email.id}`, { method: 'POST' });
        // Update local accounts state immediately for instant feedback
        setAccounts(prev => prev.map(a => 
          a.email === selectedAccount 
          ? { ...a, unread_count: Math.max(0, (a.unread_count || 0) - 1) } 
          : a
        ));
      } catch (e) { console.error(e); }
    }
  };

  const handleSync = async () => {
    setToast({ message: 'AI Junk classification started...', type: 'success' });
    try {
      const r = await fetch(`${API_BASE}/emails/sync`, { method: 'POST' });
      if (r.ok) {
        setToast({ message: 'AI Re-scan complete!', type: 'success' });
        fetchAccounts();
        if (selectedAccount && selectedFolder) fetchEmails(selectedAccount, selectedFolder);
      }
    } catch (e) {
      setToast({ message: 'Sync failed', type: 'error' });
    }
  };

  return (
    <div className="app-layout">
      <Sidebar 
        accounts={accounts} 
        selectedAccount={selectedAccount} 
        selectedFolder={selectedFolder} 
        onSelectFolder={handleSelectFolder} 
        onAddAccount={() => setShowAddModal(true)} 
        onDeleteAccount={handleDeleteAccount} 
        onCompose={setComposeAccount}
        onSync={handleSync}
      />
      {selectedAccount && selectedFolder ? (
        <div className="main-content">
          <EmailList 
            folderName={getFolderName()} 
            emails={emails} 
            isLoading={isLoadingEmails} 
            selectedEmailId={selectedEmail?.id} 
            onSelectEmail={handleSelectEmail} 
          />
          <EmailView email={selectedEmail} />
        </div>
      ) : (
        <div className="main-content">
        </div>
      )}
      {showAddModal && <AddAccount onClose={() => setShowAddModal(false)} />}
      {composeAccount && <ComposeModal account={composeAccount} onClose={() => setComposeAccount(null)} onSend={handleSendEmail} />}
      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  );
}
