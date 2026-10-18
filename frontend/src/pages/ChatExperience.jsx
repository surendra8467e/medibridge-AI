import { useEffect, useRef, useState } from 'react';
import { AlertTriangle, ArrowUp, Bot, LoaderCircle, Mic, Plus, Square, Volume2 } from 'lucide-react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import './voice-chat.css';

const speechErrors = {
  'not-allowed': 'Microphone permission was denied. Allow microphone access in browser settings, or type your message instead.',
  'service-not-allowed': 'Speech recognition is blocked by this browser. You can continue by typing.',
  'no-speech': 'No speech was detected. Try again or type your message.',
  'audio-capture': 'No working microphone was found. Check your device or type your message.',
  network: 'Speech recognition could not reach the browser speech service. You can type your message instead.',
};

export default function ChatExperience() {
  const { language, t } = useLanguage();
  const [sessions, setSessions] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [emergency, setEmergency] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceLanguage, setVoiceLanguage] = useState(language === 'hi' ? 'hi-IN' : 'en-IN');
  const [speakingId, setSpeakingId] = useState(null);
  const [responseMode, setResponseMode] = useState('rule-based demo');
  const endRef = useRef(null);
  const recognitionRef = useRef(null);
  const speechRef = useRef(null);
  const draftBeforeSpeechRef = useRef('');
  const sendInFlightRef = useRef(false);

  const loadSessions = async () => { const data = await api.sessions(); setSessions(data.sessions); };
  const openSession = async (id) => {
    try {
      setError(''); setActive(id); setEmergency(false); setMessages([]);
      const data = await api.chatMessages(id); setMessages(data.messages);
    } catch (problem) { setError(problem.message); }
  };
  useEffect(() => { loadSessions().catch((problem) => setError(problem.message)); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  useEffect(() => () => {
    if (recognitionRef.current) { recognitionRef.current.onend = null; recognitionRef.current.onerror = null; recognitionRef.current.onresult = null; recognitionRef.current.stop(); recognitionRef.current = null; }
    if (speechRef.current) { speechRef.current.onend = null; speechRef.current.onerror = null; speechRef.current = null; }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }, []);

  const newChat = async () => {
    try { const data = await api.newSession(); await loadSessions(); setActive(data.session.id); setMessages([]); setDraft(''); setError(''); setEmergency(false); setResponseMode('rule-based demo'); }
    catch (problem) { setError(problem.message); }
  };

  const stopListening = () => { recognitionRef.current?.stop(); };
  const listen = () => {
    if (listening) { stopListening(); return; }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) { setError('Voice input is not supported in this browser. Manual typing is still available.'); return; }
    setError('');
    try {
      const recognition = new Recognition();
      recognition.lang = voiceLanguage;
      recognition.continuous = false;
      recognition.interimResults = true;
      draftBeforeSpeechRef.current = draft.trim();
      recognitionRef.current = recognition;
      recognition.onstart = () => setListening(true);
      recognition.onresult = (event) => {
        const transcript = Array.from(event.results).map((result) => result[0]?.transcript || '').join(' ').trim();
        setDraft([draftBeforeSpeechRef.current, transcript].filter(Boolean).join(' '));
      };
      recognition.onerror = (event) => setError(speechErrors[event.error] || `Voice input failed (${event.error || 'unknown error'}). You can type your message instead.`);
      recognition.onend = () => { setListening(false); recognitionRef.current = null; };
      recognition.start();
    } catch {
      setListening(false); recognitionRef.current = null;
      setError('Could not start microphone recognition. Check browser microphone permission or type your message.');
    }
  };

  const stopSpeaking = () => {
    if (speechRef.current) { speechRef.current.onend = null; speechRef.current.onerror = null; speechRef.current = null; }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    setSpeakingId(null);
  };
  const speak = (text, id) => {
    if (!('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) {
      setError('Read aloud is not supported in this browser.'); return;
    }
    if (speakingId === id) { stopSpeaking(); return; }
    if (speechRef.current) { speechRef.current.onend = null; speechRef.current.onerror = null; speechRef.current = null; }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = voiceLanguage;
    utterance.onstart = () => setSpeakingId(id);
    utterance.onend = () => { setSpeakingId(null); speechRef.current = null; };
    utterance.onerror = () => { setSpeakingId(null); speechRef.current = null; setError('Speech playback stopped. You can read the response on screen.'); };
    speechRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const send = async (event) => {
    event?.preventDefault();
    const sent = draft.trim();
    if (!sent || sendInFlightRef.current) return;
    sendInFlightRef.current = true;
    if (listening) stopListening();
    try {
      setError(''); setBusy(true);
      let sessionId = active;
      if (!sessionId) { const data = await api.newSession(); sessionId = data.session.id; setActive(sessionId); }
      setDraft('');
      setMessages((current) => [...current, { sender: 'patient', content: sent }, { sender: 'assistant', content: 'Reviewing your symptoms…', loading: true }]);
      const result = await api.sendChat(sessionId, sent);
      const history = await api.chatMessages(sessionId);
      setMessages(history.messages); setEmergency(result.reply.stage === 3); setResponseMode(result.reply.mode || 'rule-based demo'); await loadSessions();
    } catch (problem) {
      setMessages((current) => current.filter((item) => !item.loading)); setDraft(sent); setError(problem.message);
    } finally { setBusy(false); sendInFlightRef.current = false; }
  };

  return <div className="chat-page"><div className="page-title-row"><div><span className="eyebrow">PRIVATE HEALTH CONVERSATIONS</span><h1>{t('assistant')}</h1><p>Conversational symptom guidance · Not a diagnosis · {responseMode}</p></div><button className="button button-outline" onClick={newChat}><Plus size={17}/> New conversation</button></div><div className="chat-workspace"><aside className="chat-history"><div className="history-title">Recent conversations</div>{sessions.map((session) => <button key={session.id} className={`history-item ${active === session.id ? 'selected' : ''}`} onClick={() => openSession(session.id)}>{session.title}</button>)}{sessions.length === 0 && <p className="empty-small">No conversations yet.</p>}</aside><section className="chat-panel"><div className="chat-panel-head"><div className="assistant-avatar"><Bot size={19}/></div><span><strong>MediBridge Health Assistant</strong><small>Demo guidance · follow-up questions · not a diagnosis</small></span><span className="demo-tag">{responseMode === 'rule-based demo' ? 'DEMO' : 'AI TRIAGE'}</span></div><div className="chat-thread">{messages.length === 0 ? <div className="chat-welcome"><div className="chat-welcome-icon"><Bot size={25}/></div><h2>What would you like help with?</h2><p>Describe your concern in your own words. I’ll ask a small number of follow-up questions when more context is needed.</p><div className="suggestion-row"><button onClick={() => setDraft('I have had a mild headache since this morning')}>Mild headache</button><button onClick={() => setDraft('I have been feeling unwell for two days')}>Feeling unwell</button></div></div> : messages.map((message, index) => <div key={message.id || `${message.sender}-${index}`} className={`message-row ${message.sender === 'patient' ? 'mine' : ''}`}><div className={`message-avatar ${message.sender === 'patient' ? 'patient-avatar' : ''}`}>{message.sender === 'patient' ? 'You' : <Bot size={15}/>}</div><div className="message-body"><div className={`bubble ${message.sender === 'patient' ? 'bubble-mine' : ''}`}>{message.loading ? <LoaderCircle size={16} className="spin"/> : message.content}</div>{message.sender === 'assistant' && !message.loading && <button className="read-aloud" onClick={() => speak(message.content, message.id || index)}>{speakingId === (message.id || index) ? <Square size={12}/> : <Volume2 size={13}/>} {speakingId === (message.id || index) ? 'Stop reading' : 'Read aloud'}</button>}</div></div>)}<div ref={endRef}/></div>{emergency && <div className="emergency-inline"><AlertTriangle size={20}/><div><strong>Potential emergency symptoms</strong><p>Call 112 in India or your local emergency number now. Seek immediate emergency care; do not wait for an online consultation.</p><a href="tel:112">Call 112</a></div></div>}{error && <div className="error-banner" role="alert">{error}</div>}<div className="voice-toolbar"><label>Speech language<select aria-label="Speech recognition language" value={voiceLanguage} onChange={(event) => setVoiceLanguage(event.target.value)} disabled={listening}><option value="en-IN">English (India)</option><option value="hi-IN">Hindi (editable transcript)</option></select></label>{listening && <span className="voice-listening" role="status"><span/> Listening in {voiceLanguage === 'hi-IN' ? 'Hindi' : 'English'}</span>}<button type="button" className={`icon-button voice-button ${listening ? 'is-listening' : ''}`} aria-label={listening ? 'Stop voice input' : 'Start voice input'} title={listening ? 'Stop voice input' : 'Start voice input'} onClick={listen}>{listening ? <Square size={15}/> : <Mic size={17}/>}</button></div><form className="chat-compose" onSubmit={send}><textarea aria-label={t('chat')} placeholder={listening ? 'Listening… recognized words will appear here for editing' : t('chat')} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} rows="1"/><button className="send-button" aria-label="Send message" disabled={!draft.trim() || busy}>{busy ? <LoaderCircle size={17} className="spin"/> : <ArrowUp size={19}/>}</button></form><p className="chat-disclaimer">Not a diagnosis. If you may be having an emergency, call 112 in India or your local emergency service.</p></section></div></div>;
}
