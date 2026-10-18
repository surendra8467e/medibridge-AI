import { useEffect, useRef, useState } from 'react';
import { ArrowUp, LoaderCircle, MessageCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import './message-conversations.css';

export default function MessagesExperience() {
  const { user } = useAuth();
  const [people, setPeople] = useState([]);
  const [selected, setSelected] = useState(null);
  const [items, setItems] = useState([]);
  const [conversation, setConversation] = useState(null);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const sendLock = useRef(false);

  const loadPeople = async () => {
    const result = user.role === 'doctor' ? await api.patients() : await api.messageDoctors();
    const contacts = user.role === 'doctor' ? result.patients : result.doctors;
    setPeople(contacts);
    setSelected((current) => current && contacts.some((person) => person.id === current.id) ? current : contacts[0] || null);
  };

  useEffect(() => {
    let active = true;
    const refreshContacts = () => loadPeople().catch((problem) => { if (active) setError(problem.message); });
    refreshContacts();
    const timer = window.setInterval(refreshContacts, 5000);
    return () => { active = false; window.clearInterval(timer); };
  }, [user.role, user.id]);

  useEffect(() => {
    if (!selected) { setItems([]); setConversation(null); return undefined; }
    let active = true;
    const patientId = user.role === 'patient' ? user.id : selected.id;
    const doctorId = user.role === 'doctor' ? user.id : selected.id;
    const refreshMessages = async () => {
      try {
        const result = await api.messages(patientId, doctorId);
        if (active) { setItems(result.messages); setConversation(result); setError(''); }
      } catch (problem) { if (active) setError(problem.message); }
    };
    setItems([]); setConversation(null); setLoading(true);
    refreshMessages().finally(() => { if (active) setLoading(false); });
    const timer = window.setInterval(refreshMessages, 4000);
    return () => { active = false; window.clearInterval(timer); };
  }, [selected, user.role, user.id]);

  const send = async (event) => {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !selected || sendLock.current) return;
    sendLock.current = true; setSending(true); setError('');
    const patientId = user.role === 'patient' ? user.id : selected.id;
    const doctorId = user.role === 'doctor' ? user.id : selected.id;
    try {
      const result = await api.sendMessage(patientId, { content, ...(user.role === 'patient' ? { doctor_id: doctorId } : {}) });
      setConversation(result);
      setItems((current) => current.some((item) => item.id === result.message.id) ? current : [...current, result.message].sort((left, right) => left.id - right.id));
      setDraft('');
    } catch (problem) { setError(problem.message); }
    finally { sendLock.current = false; setSending(false); }
  };

  const refreshContacts = async () => { try { await loadPeople(); setError(''); } catch (problem) { setError(problem.message); } };
  return <div className="page-standard"><div className="page-title-row"><div><span className="eyebrow">CARE TEAM CONNECTION</span><h1>Messages</h1><p>Private, persisted conversations. New replies appear automatically while this page is open.</p></div><button className="button button-outline" onClick={refreshContacts}>Refresh contacts</button></div>{error && <div className="error-banner" role="alert">{error}</div>}<div className="messaging-layout"><aside className="people-list"><div className="history-title">{user.role === 'doctor' ? 'Assigned patients' : 'Accepted care team'}</div>{people.map((person) => <button key={person.id} className={`person-item ${selected?.id === person.id ? 'selected' : ''}`} onClick={() => setSelected(person)}><span className="person-avatar">{person.name.slice(0, 1)}</span><span><strong>{person.name}</strong><small>{person.specialty || person.email}</small></span></button>)}{people.length === 0 && <div className="message-empty-help">{user.role === 'doctor' ? 'No assigned patients yet. Accept an appointment request to create access.' : <>No accepted conversations yet. <Link to="/doctors">Request an appointment</Link>; messaging opens after the doctor accepts it.</>}</div>}</aside><section className="message-panel"><div className="message-panel-head"><MessageCircle size={18}/><strong>{selected?.name || 'No active conversation'}</strong>{conversation?.conversationId && <small className="conversation-id" title={`Accepted appointment ${conversation.appointmentId || 'or explicit assignment'}`}>{conversation.conversationId}</small>}</div><div className="message-list">{items.map((item) => <div className={`message-row ${item.sender_id === user.id ? 'mine' : ''}`} key={item.id}><div className={`bubble ${item.sender_id === user.id ? 'bubble-mine' : ''}`}>{item.content}<small className="message-time">{new Date(`${item.created_at}Z`).toLocaleString()}</small></div></div>)}{loading && items.length === 0 && <div className="message-loading"><LoaderCircle size={15} className="spin"/> Loading conversation…</div>}{items.length === 0 && !loading && selected && <div className="empty-state">No messages yet. Send a message to begin.</div>}{items.length === 0 && !selected && <div className="empty-state">{user.role === 'patient' ? 'Request an appointment and wait for the doctor to accept before messaging.' : 'Accept an appointment request to create an authorized conversation.'}</div>}</div><form className="message-compose" onSubmit={send}><input placeholder="Write a message…" aria-label="Write a message" value={draft} onChange={(event) => setDraft(event.target.value)} disabled={!selected || sending}/><button className="send-button" aria-label="Send" disabled={!draft.trim() || !selected || sending}>{sending ? <LoaderCircle size={16} className="spin"/> : <ArrowUp size={18}/>}</button></form></section></div></div>;
}
