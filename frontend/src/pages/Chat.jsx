import { useEffect, useRef, useState } from 'react';
import { AlertTriangle, ArrowUp, Bot, LoaderCircle, Mic, Plus, Volume2 } from 'lucide-react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
export { default } from './ChatExperience';

function LegacyChat() {
  const { language, t } = useLanguage();
  const [sessions, setSessions] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [emergency, setEmergency] = useState(false);
  const endRef = useRef(null);
  const loadSessions = async () => { const data = await api.sessions(); setSessions(data.sessions); };
  const openSession = async (id) => { setActive(id); setError(''); setEmergency(false); const data = await api.chatMessages(id); setMessages(data.messages); };
  useEffect(() => { loadSessions().catch((problem) => setError(problem.message)); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  const newChat = async () => { try { const data = await api.newSession(); await loadSessions(); await openSession(data.session.id); } catch (problem) { setError(problem.message); } };
  const send = async (event) => {
    event?.preventDefault(); if (!draft.trim() || busy) return;
    try {
      setError(''); setBusy(true);
      let sessionId = active;
      if (!sessionId) { const data = await api.newSession(); sessionId = data.session.id; setActive(sessionId); }
      const sent = draft.trim(); setDraft('');
      setMessages((current) => [...current, { sender: 'patient', content: sent }, { sender: 'assistant', content: 'Reviewing your message…', loading: true }]);
      const result = await api.sendChat(sessionId, sent);
      const history = await api.chatMessages(sessionId); setMessages(history.messages); setEmergency(result.reply.stage === 3); await loadSessions();
    } catch (problem) { setMessages((current) => current.filter((item) => !item.loading)); setError(problem.message); }
    finally { setBusy(false); }
  };
  const speak = (text) => { if ('speechSynthesis' in window) { window.speechSynthesis.cancel(); const utterance = new SpeechSynthesisUtterance(text); utterance.lang = language === 'hi' ? 'hi-IN' : 'en-IN'; window.speechSynthesis.speak(utterance); } };
  const listen = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) { setError('Voice input is not supported by this browser.'); return; }
    const recognition = new Recognition(); recognition.lang = language === 'hi' ? 'hi-IN' : 'en-IN'; recognition.onresult = (event) => setDraft(event.results[0][0].transcript); recognition.onerror = () => setError('Microphone access was unavailable.'); recognition.start();
  };
  return <div className="chat-page"><div className="page-title-row"><div><span className="eyebrow">PRIVATE HEALTH CONVERSATIONS</span><h1>{t('assistant')}</h1><p>Rule-based demo guidance · Your chat history is saved to this demo database.</p></div><button className="button button-outline" onClick={newChat}><Plus size={17}/> New chat</button></div><div className="chat-workspace"><aside className="chat-history"><div className="history-title">Recent conversations</div>{sessions.map((session) => <button key={session.id} className={`history-item ${active === session.id ? 'selected' : ''}`} onClick={() => openSession(session.id)}>{session.title}</button>)}{sessions.length === 0 && <p className="empty-small">No conversations yet.</p>}</aside><section className="chat-panel"><div className="chat-panel-head"><div className="assistant-avatar"><Bot size={19}/></div><span><strong>MediBridge Health Assistant</strong><small>Preliminary guidance · not a diagnosis</small></span><span className="demo-tag">DEMO</span></div><div className="chat-thread">{messages.length === 0 ? <div className="chat-welcome"><div className="chat-welcome-icon"><Bot size={25}/></div><h2>What would you like help with?</h2><p>Describe your concern in your own words. I may ask follow-up questions when I need more context.</p><div className="suggestion-row"><button onClick={() => setDraft('I have had a mild headache since this morning')}>Mild headache</button><button onClick={() => setDraft('I have been feeling unwell for two days')}>Feeling unwell</button></div></div> : messages.map((message, index) => <div key={message.id || `${message.sender}-${index}`} className={`message-row ${message.sender === 'patient' ? 'mine' : ''}`}><div className={`message-avatar ${message.sender === 'patient' ? 'patient-avatar' : ''}`}>{message.sender === 'patient' ? 'You' : <Bot size={15}/>}</div><div className="message-body"><div className={`bubble ${message.sender === 'patient' ? 'bubble-mine' : ''}`}>{message.loading ? <LoaderCircle size={16} className="spin"/> : message.content}</div>{message.sender === 'assistant' && !message.loading && <button className="read-aloud" onClick={() => speak(message.content)}><Volume2 size={13}/> Read aloud</button>}</div></div>)}<div ref={endRef}/></div>{emergency && <div className="emergency-inline"><AlertTriangle size={20}/><div><strong>Potential emergency symptoms</strong><p>Call 112 in India or your local emergency number now. Seek immediate emergency care; do not wait for an online consultation.</p><a href="tel:112">Call 112</a></div></div>}{error && <div className="error-banner" role="alert">{error}</div>}<form className="chat-compose" onSubmit={send}><textarea aria-label={t('chat')} placeholder={t('chat')} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} rows="1"/><button type="button" className="icon-button" aria-label="Voice input" title="Voice input" onClick={listen}><Mic size={17}/></button><button className="send-button" aria-label="Send message" disabled={!draft.trim() || busy}><ArrowUp size={19}/></button></form><p className="chat-disclaimer">Not a diagnosis. If you may be having an emergency, call 112 in India or your local emergency service.</p></section></div></div>;
}
