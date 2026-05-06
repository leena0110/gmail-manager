import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import EmailList from '../components/EmailList';
import EmailView from '../components/EmailView';
import AddAccount from '../components/AddAccount';

const API_BASE = 'http://localhost:8000';

export default function Dashboard() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [emails, setEmails] = useState([]);
  const [isLoadingEmails, setIsLoadingEmails] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => { fetchAccounts(); }, []);
  useEffect(() => {
    const id = setInterval(() => { fetchAccounts(); if (selectedAccount && selectedFolder) fetchEmails(selectedAccount, selectedFolder, true); }, 30000);
    return () => clearInterval(id);
  }, [selectedAccount, selectedFolder]);
  useEffect(() => { if (toast) { const t = setTimeout(() => setToast(null), 3000); return () => clearTimeout(t); } }, [toast]);

  const fetchAccounts = async () => { try { const r = await fetch(`${API_BASE}/accounts/`); const d = await r.json(); setAccounts(d.accounts || []); } catch(e) { console.error(e); } };
  const fetchEmails = async (email, folder, silent=false) => { if (!silent) setIsLoadingEmails(true); try { const r = await fetch(`${API_BASE}/emails/${email}/${folder}`); const d = await r.json(); setEmails(d.emails || []); } catch(e) { console.error(e); } finally { if (!silent) setIsLoadingEmails(false); } };
  const handleSelectFolder = (email, folder) => { setSelectedAccount(email); setSelectedFolder(folder); setSelectedEmail(null); fetchEmails(email, folder); };
  const handleDeleteAccount = async (email) => { try { const r = await fetch(`${API_BASE}/accounts/${email}`, {method:'DELETE'}); if(r.ok){setToast({message:'Account removed',type:'success'});setAccounts(accounts.filter(a=>a.email!==email));if(selectedAccount===email){setSelectedAccount(null);setSelectedFolder(null);setEmails([]);setSelectedEmail(null);}} } catch(e){setToast({message:'Error',type:'error'});} };
  const getFolderName = () => { if(!selectedAccount) return ''; return selectedFolder === 'junk' ? 'Junk Folder' : 'Inbox'; };

  return (
    <div className="app-layout">
      <Sidebar accounts={accounts} selectedAccount={selectedAccount} selectedFolder={selectedFolder} onSelectFolder={handleSelectFolder} onAddAccount={() => setShowAddModal(true)} onDeleteAccount={handleDeleteAccount} />
      {selectedAccount && selectedFolder ? (
        <div className="main-content">
          <EmailList folderName={getFolderName()} emails={emails} isLoading={isLoadingEmails} selectedEmailId={selectedEmail?.id} onSelectEmail={setSelectedEmail} />
          <EmailView email={selectedEmail} />
        </div>
      ) : (
        <div className="main-content">
        </div>
      )}
      {showAddModal && <AddAccount onClose={() => setShowAddModal(false)} />}
      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  );
}
