import { useEffect, useState } from 'react';
import { CalendarDays, Check, Clock3, Video, X } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Appointments() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const refresh = () => api.appointments().then((result) => setItems(result.appointments)).catch((problem) => setError(problem.message));
  useEffect(() => { refresh(); }, []);
  const update = async (id, status) => { try { await api.updateAppointment(id, status); setNotice(`Appointment ${status}.`); refresh(); } catch (problem) { setError(problem.message); } };
  const cancel = async (id) => { try { await api.cancelAppointment(id); setNotice('Appointment cancelled.'); await refresh(); } catch (problem) { setError(problem.message); } };
  const joinVideo = async (id) => { const tab = window.open('about:blank', '_blank'); try { const room = await api.videoRoom(id); if (tab) tab.location = room.url; else window.location.assign(room.url); } catch (problem) { tab?.close(); setError(problem.message); } };
  return <div className="page-standard"><div className="page-title-row"><div><span className="eyebrow">YOUR CARE SCHEDULE</span><h1>Appointments</h1><p>Requests and consultations are kept in the local demo database.</p></div></div>{notice && <div className="success-banner">{notice}</div>}{error && <div className="error-banner">{error}</div>}<section className="list-section">{items.map((item) => <article className="appointment-row" key={item.id}><div className="appointment-icon"><CalendarDays size={19}/></div><div className="appointment-info"><strong>{user.role === 'patient' ? item.doctor_name : item.patient_name}</strong><span>{item.reason}</span><small><Clock3 size={13}/> {item.scheduled_at}</small></div><span className={`status-pill status-${item.status}`}>{item.status}</span>{item.status === 'accepted' && <button className="button button-outline small-button" onClick={() => joinVideo(item.id)}><Video size={14}/> Join video</button>}{user.role === 'patient' && ['requested', 'accepted'].includes(item.status) && <button className="button button-outline small-button" onClick={() => cancel(item.id)}>Cancel</button>}{user.role === 'doctor' && item.status === 'requested' && <div className="inline-actions"><button className="icon-button accept" aria-label="Accept appointment" onClick={() => update(item.id, 'accepted')}><Check size={17}/></button><button className="icon-button decline" aria-label="Decline appointment" onClick={() => update(item.id, 'declined')}><X size={17}/></button></div>}{user.role === 'doctor' && item.status === 'accepted' && <button className="button button-outline small-button" onClick={() => update(item.id, 'completed')}>Mark complete</button>}</article>)}{items.length === 0 && <div className="empty-state">No appointments yet. {user.role === 'patient' ? 'Browse the doctor directory to make a request.' : 'New patient requests will appear here.'}</div>}</section>{user.role === 'patient' && <div className="inline-hint">Need care sooner? Use the <a href="/assistant">health assistant</a> for preliminary guidance, or call emergency services for urgent symptoms.</div>}</div>;
}
