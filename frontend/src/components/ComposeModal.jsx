import { useState, useRef } from 'react';
import { X, Minus, Maximize2, Paperclip, Image as ImageIcon, Link2, Smile, Lock, PenTool, MoreVertical, Trash2, Type, Bold, Italic, Underline, List, ListOrdered, AlignLeft, AlignCenter, AlignRight, ShieldCheck, Triangle, Check, Printer, FileText, CheckCircle2, Calendar } from 'lucide-react';

export default function ComposeModal({ account, onClose, onSend }) {
  const [to, setTo] = useState('');
  const [cc, setCc] = useState('');
  const [bcc, setBcc] = useState('');
  const [showCcBcc, setShowCcBcc] = useState(false);
  const [subject, setSubject] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showFormatting, setShowFormatting] = useState(false);
  const [showEmojis, setShowEmojis] = useState(false);
  const [showLinkPopover, setShowLinkPopover] = useState(false);
  const [linkText, setLinkText] = useState('');
  const [linkUrl, setLinkUrl] = useState('');
  const [showSignatureMenu, setShowSignatureMenu] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [isConfidential, setIsConfidential] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [isPlainText, setIsPlainText] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const editorRef = useRef(null);
  const fileInputRef = useRef(null);

  const execCommand = (command, value = null) => {
    editorRef.current?.focus();
    document.execCommand(command, false, value);
  };

  const handleLinkApply = () => {
    if (linkUrl) {
      if (linkText) {
        const html = `<a href="${linkUrl}" target="_blank">${linkText}</a>`;
        execCommand('insertHTML', html);
      } else {
        execCommand('createLink', linkUrl);
      }
      setShowLinkPopover(false);
      setLinkText('');
      setLinkUrl('');
    }
  };

  const [showLinkPreview, setShowLinkPreview] = useState(null);

  const handleEditorClick = (e) => {
    const node = e.target.closest('a');
    if (node) {
      const rect = node.getBoundingClientRect();
      const parentRect = editorRef.current.getBoundingClientRect();
      setShowLinkPreview({ 
        url: node.href, 
        node, 
        top: rect.bottom - parentRect.top + 5, 
        left: rect.left - parentRect.left 
      });
    } else {
      setShowLinkPreview(null);
    }
  };

  const removeLink = () => {
    if (showLinkPreview) {
      const { node } = showLinkPreview;
      const parent = node.parentNode;
      while (node.firstChild) {
        parent.insertBefore(node.firstChild, node);
      }
      parent.removeChild(node);
      setShowLinkPreview(null);
    }
  };

  const editLink = () => {
    if (showLinkPreview) {
      setLinkText(showLinkPreview.node.innerText);
      setLinkUrl(showLinkPreview.url);
      setShowLinkPopover(true);
      setShowLinkPreview(null);
    }
  };

  const handleAttachment = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      if (file.size > 2 * 1024 * 1024) {
        alert(`File ${file.name} is too large (max 2MB).`);
        return;
      }
      const blobUrl = URL.createObjectURL(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setAttachments(prev => [...prev, { 
          name: file.name, 
          size: (file.size / 1024).toFixed(0) + 'K', 
          previewUrl: blobUrl,
          data: event.target.result 
        }]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const togglePlainText = () => {
    if (!isPlainText) {
      // Convert HTML to plain text
      const text = editorRef.current.innerText;
      editorRef.current.innerText = text;
      setShowFormatting(false);
    }
    setIsPlainText(!isPlainText);
    setShowMoreMenu(false);
  };

  const insertSignature = () => {
    const sig = `<br/><br/>--<br/><b>${account.split('@')[0]}</b><br/>Sent via Gmail Manager AI`;
    execCommand('insertHTML', sig);
    setShowSignatureMenu(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    let body = editorRef.current?.innerHTML || '';
    if (!to || !subject || !body) return;
    
    setIsSending(true);
    await onSend(account, to, subject, body, attachments, cc, bcc);
    setIsSending(false);
  };

  const emojis = ['😊', '😂', '❤️', '👍', '🙏', '🙌', '🔥', '✨', '🎉', '✅', '🚀', '⭐'];

  return (
    <div className={`compose-dock ${isMaximized ? 'maximized' : ''}`}>
      <div className={`compose-window ${isMinimized ? 'minimized' : ''}`}>
        <div className="compose-header" onClick={() => isMinimized && setIsMinimized(false)}>
          <div className="compose-title">New Message</div>
          <div className="compose-actions">
            <button type="button" className="btn-icon-light" onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }} title={isMinimized ? 'Restore' : 'Minimize'}>
              <Minus size={16} />
            </button>
            <button type="button" className="btn-icon-light" onClick={(e) => { e.stopPropagation(); setIsMaximized(!isMaximized); }} title={isMaximized ? 'Exit full screen' : 'Full screen'}>
              <Maximize2 size={14} />
            </button>
            <button type="button" className="btn-icon-light" onClick={onClose}><X size={16} /></button>
          </div>
        </div>
        
        {!isMinimized && (
          <>
            <form onSubmit={handleSubmit} className="compose-form-gmail">
              <div className="compose-input-row-gmail">
                <div className="label-gmail">To</div>
                <input
                  type="email"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  disabled={isSending}
                  className="input-field-gmail"
                />
                <div className="compose-cc-bcc-gmail" onClick={() => setShowCcBcc(!showCcBcc)}>Cc Bcc</div>
              </div>
              
              {showCcBcc && (
                <>
                  <div className="compose-input-row-gmail">
                    <div className="label-gmail">Cc</div>
                    <input type="email" value={cc} onChange={(e) => setCc(e.target.value)} className="input-field-gmail" />
                  </div>
                  <div className="compose-input-row-gmail">
                    <div className="label-gmail">Bcc</div>
                    <input type="email" value={bcc} onChange={(e) => setBcc(e.target.value)} className="input-field-gmail" />
                  </div>
                </>
              )}

              <div className="compose-input-row-gmail">
                <input
                  type="text"
                  placeholder="Subject"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  disabled={isSending}
                  className="input-field-gmail subject-input"
                />
              </div>
              
              <div className="editor-container-gmail">
                <div 
                  ref={editorRef}
                  contentEditable={!isSending}
                  spellCheck="true"
                  className={`rich-editor-gmail ${isPlainText ? 'plain-text-mode' : ''}`}
                  onFocus={() => { setShowEmojis(false); setShowSignatureMenu(false); setShowMoreMenu(false); }}
                  onClick={handleEditorClick}
                ></div>
                
                {showLinkPreview && (
                  <div className="link-preview-box" style={{ top: showLinkPreview.top, left: showLinkPreview.left }}>
                    <span>Go to link: </span>
                    <a href={showLinkPreview.url} target="_blank" rel="noreferrer" className="preview-url">{showLinkPreview.url}</a>
                    <span className="preview-divider"> - </span>
                    <span className="preview-action" onClick={editLink}>Change</span>
                    <span className="preview-divider"> | </span>
                    <span className="preview-action" onClick={removeLink}>Remove</span>
                  </div>
                )}

                {attachments.length > 0 && (
                  <div className="attachment-list-gmail">
                    {attachments.map((file, i) => (
                      <div key={i} className="attachment-item-gmail">
                        <Paperclip size={14} color="#1a73e8" />
                        <a href={file.previewUrl} target="_blank" rel="noreferrer" className="attachment-name">
                          {file.name}
                        </a>
                        <span className="attachment-size">({file.size})</span>
                        <X size={14} className="attachment-remove" onClick={() => removeAttachment(i)} />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {showFormatting && (
                <div className="gmail-formatting-bar">
                  <div className="format-group">
                    <button type="button" onClick={() => execCommand('undo')} className="format-btn"><AlignLeft size={14} style={{transform: 'scaleX(-1)'}} /></button>
                    <button type="button" onClick={() => execCommand('redo')} className="format-btn"><AlignLeft size={14} /></button>
                  </div>
                  <div className="format-divider"></div>
                  <div className="format-group">
                    <select className="format-select" onChange={(e) => execCommand('fontName', e.target.value)}>
                      <option value="sans-serif">Sans Serif</option>
                      <option value="serif">Serif</option>
                      <option value="monospace">Fixed Width</option>
                    </select>
                  </div>
                  <div className="format-divider"></div>
                  <div className="format-group">
                    <button type="button" onClick={() => execCommand('bold')} className="format-btn"><Bold size={16} /></button>
                    <button type="button" onClick={() => execCommand('italic')} className="format-btn"><Italic size={16} /></button>
                    <button type="button" onClick={() => execCommand('underline')} className="format-btn"><Underline size={16} /></button>
                    <button type="button" onClick={() => execCommand('foreColor', '#ff0000')} className="format-btn"><Type size={16} /></button>
                  </div>
                  <div className="format-divider"></div>
                  <div className="format-group">
                    <button type="button" onClick={() => execCommand('justifyLeft')} className="format-btn"><AlignLeft size={16} /></button>
                    <button type="button" onClick={() => execCommand('insertUnorderedList')} className="format-btn"><List size={16} /></button>
                    <button type="button" onClick={() => execCommand('insertOrderedList')} className="format-btn"><ListOrdered size={16} /></button>
                  </div>
                </div>
              )}
              
              <div className="compose-footer-gmail-new">
                <div className="footer-left">
                  <div className="send-btn-container">
                    <button type="submit" className="btn-send-main" disabled={isSending}>
                      {isSending ? 'Sending...' : 'Send'}
                    </button>
                    <div className="send-more">▼</div>
                  </div>
                  
                  <div className="footer-icons">
                    {!isPlainText && (
                      <button type="button" className={`icon-btn ${showFormatting ? 'active' : ''}`} onClick={() => setShowFormatting(!showFormatting)} title="Formatting options">
                        <Type size={20} />
                      </button>
                    )}
                    
                    <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={handleAttachment} multiple />
                    
                    <button type="button" className="icon-btn" onClick={() => fileInputRef.current.click()} title="Attach files">
                      <Paperclip size={20} />
                    </button>
                    
                    <div className="emoji-picker-container">
                      <button type="button" className={`icon-btn ${showLinkPopover ? 'active' : ''}`} onClick={() => { setShowLinkPopover(!showLinkPopover); setShowEmojis(false); setShowMoreMenu(false); }}>
                        <Link2 size={20} />
                      </button>
                      {showLinkPopover && (
                        <div className="popover-menu link-popover">
                          <div className="link-input-group">
                            <div className="link-input-wrapper">
                              <Type size={14} color="#70757a" />
                              <input placeholder="Text to display" value={linkText} onChange={e => setLinkText(e.target.value)} />
                            </div>
                            <div className="link-input-wrapper">
                              <Link2 size={14} color="#70757a" />
                              <input placeholder="To what URL should this link go?" value={linkUrl} onChange={e => setLinkUrl(e.target.value)} autoFocus />
                            </div>
                          </div>
                          <div className="link-popover-footer">
                            <button type="button" className="btn-link-cancel" onClick={() => setShowLinkPopover(false)}>Cancel</button>
                            <button type="button" className="btn-link-apply" onClick={handleLinkApply} disabled={!linkUrl}>Apply</button>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="emoji-picker-container">
                      <button type="button" className={`icon-btn ${showEmojis ? 'active' : ''}`} onClick={() => { setShowEmojis(!showEmojis); setShowLinkPopover(false); setShowMoreMenu(false); }}>
                        <Smile size={20} />
                      </button>
                      {showEmojis && (
                        <div className="emoji-picker-popover">
                          {emojis.map(emoji => (
                            <span key={emoji} className="emoji-item" onClick={() => { execCommand('insertHTML', emoji); setShowEmojis(false); }}>{emoji}</span>
                          ))}
                        </div>
                      )}
                    </div>

                    <button type="button" className="icon-btn" onClick={() => { alert('Connecting to Google Drive...'); fileInputRef.current.click(); }} title="Insert files using Drive">
                      <Triangle size={20} style={{transform: 'rotate(180deg)'}} />
                    </button>
                    
                    <button type="button" className="icon-btn" onClick={() => fileInputRef.current.click()} title="Insert photo">
                      <ImageIcon size={20} />
                    </button>
                    
                    <button type="button" className={`icon-btn ${isConfidential ? 'active' : ''}`} onClick={() => setIsConfidential(!isConfidential)} title="Confidential mode">
                      <Lock size={20} />
                    </button>
                    
                    <div className="emoji-picker-container">
                      <button type="button" className={`icon-btn ${showMoreMenu ? 'active' : ''}`} onClick={() => { setShowMoreMenu(!showMoreMenu); setShowLinkPopover(false); setShowEmojis(false); }}>
                        <MoreVertical size={20} />
                      </button>
                      {showMoreMenu && (
                        <div className="popover-menu" style={{ left: 'auto', right: 0 }}>
                          <div className="popover-item" onClick={() => { setIsMaximized(!isMaximized); setShowMoreMenu(false); }}>
                            <Maximize2 size={14} /> {isMaximized ? 'Exit full screen' : 'Full screen'}
                          </div>
                          <div className={`popover-item ${isPlainText ? 'active' : ''}`} onClick={togglePlainText}>
                            <FileText size={14} /> Plain text mode {isPlainText && <Check size={12} style={{marginLeft: 'auto'}} />}
                          </div>
                          <div className="popover-divider"></div>
                          <div className="popover-item" onClick={() => { window.print(); setShowMoreMenu(false); }}>
                            <Printer size={14} /> Print
                          </div>
                          <div className="popover-item" style={{opacity: 0.7, cursor: 'default'}}>
                            <CheckCircle2 size={14} /> Spell check active
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="footer-right">
                  <button type="button" className="icon-btn delete-btn" onClick={onClose} title="Discard draft">
                    <Trash2 size={20} />
                  </button>
                </div>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
