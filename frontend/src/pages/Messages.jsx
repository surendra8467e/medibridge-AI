import { useEffect, useState } from 'react';
import { ArrowUp, MessageCircle } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
export { default } from './MessagesExperience';

function LegacyMessages() {
  const { user } = useAuth();
  const [people, setPeople] = useState([]);
  const [selected, setSelected] = useState(null);
  const [items, setItems] = useState([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const loadPeople = async () => {
    const result = user.role === 'doctor' ? await api.patients() : await api.messageDoctors();
    setPeople(user.role === 'doctor' ? result.patients : result.doctors);
    const contacts = user.role === 'doctor' ? result.patients : result.doctors;
    if (!selected && contacts.length) setSelected(contacts[0]);
  };
  useEffect(() => { loadPeople().catch((problem) => setError(problem.message)); }, []);
  useEffect(() => {
    if (!selected) return;
    const patientId = user.role === 'patient' ? user.id : selected.id;
    const doctorId = user.role === 'doctor' ? user.id : selected.id;
    let active = true;
    const loadMessages = () => api.messages(patientId, doctorId).then((result) => {
      if (!active) return;
      setItems(result.messages);
      setError('');
    }).catch((problem) => { if (active) setError(problem.message); });
    loadMessages();
    const refreshTimer = window.setInterval(loadMessages, 5000);
    return () => { active = false; window.clearInterval(refreshTimer); };
  }, [selected, user]);
  const send = async (event) => {
    event.preventDefault(); if (!draft.trim() || !selected) return;
    const patientId = user.role === 'patient' ? user.id : selected.id;
    const doctorId = user.role === 'doctor' ? user.id : selected.id;
    try { const result = await api.sendMessage(patientId, { content: draft.trim(), doctor_id: doctorId }); setItems((current) => current.some((item) => item.id === result.message.id) ? current : [...current, result.message].sort((left, right) => left.id - right.id)); setDraft(''); setError(''); }
    catch (problem) { setError(problem.message); }
  };
  const conversationId = selected ? `patient-${user.role === 'patient' ? user.id : selected.id}-doctor-${user.role === 'doctor' ? user.id : selected.id}` : null;
  return <div className="page-standard"><div className="page-title-row"><div><span className="eyebrow">CARE TEAM CONNECTION</span><h1>Messages</h1><p>Private messages are available after a doctor accepts your appointment request. Messages refresh every few seconds; push messaging is not configured.</p></div></div>{error && <div className="error-banner">{error}</div>}<div className="messaging-layout"><aside className="people-list"><div className="history-title">{user.role === 'doctor' ? 'Assigned patients' : 'Accepted care team'}</div>{people.map((person) => <button key={person.id} className={`person-item ${selected?.id === person.id ? 'selected' : ''}`} onClick={() => setSelected(person)}><span className="person-avatar">{person.name.slice(0, 1)}</span><span><strong>{person.name}</strong><small>{person.specialty || person.email}</small></span></button>)}{people.length === 0 && <div className="message-empty-help">{user.role === 'doctor' ? 'No assigned patients yet. Accept a patient appointment request first.' : <>No accepted doctor conversations yet. <a href="/doctors">Find a doctor</a>, request an appointment, and messaging will open after the doctor accepts it.</>}</div>}</aside><section className="message-panel"><div className="message-panel-head"><MessageCircle size={18}/><strong>{selected?.name || 'Select a care team member'}</strong>{conversationId && <small className="conversation-id">{conversationId}</small>}</div><div className="message-list">{items.map((item) => <div className={`message-row ${item.sender_id === user.id ? 'mine' : ''}`} key={item.id}><div className={`bubble ${item.sender_id === user.id ? 'bubble-mine' : ''}`}>{item.content}<small className="message-time">{new Date(`${item.created_at}Z`).toLocaleString()}</small></div></div>)}{items.length === 0 && selected && <div className="empty-state">No messages yet. Send a message to begin.</div>}{items.length === 0 && !selected && <div className="empty-state">Your accepted care conversations will appear here.</div>}</div><form className="message-compose" onSubmit={send}><input placeholder="Write a message…" aria-label="Write a message" value={draft} onChange={(event) => setDraft(event.target.value)} disabled={!selected}/><button className="send-button" aria-label="Send" disabled={!draft.trim() || !selected}><ArrowUp size={18}/></button></form></section></div></div>;
}
