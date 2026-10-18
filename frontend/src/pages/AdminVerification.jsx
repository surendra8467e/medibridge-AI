import { useEffect, useState } from 'react';
import { Check, Clock3, LogOut, ShieldCheck, UserRound, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import VerificationBadge from '../components/VerificationBadge';
import './admin-verification.css';

export default function AdminVerification() {
  const { user, logout } = useAuth();
  const [doctors, setDoctors] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [note, setNote] = useState('');
  const [events, setEvents] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const selected = doctors.find((doctor) => doctor.id === selectedId) || doctors[0] || null;
  const refresh = async (doctorId = selectedId) => {
    const result = await api.adminDoctors();
    setDoctors(result.doctors);
    const nextId = doctorId || result.doctors[0]?.id || null;
    setSelectedId(nextId);
    if (nextId) setEvents((await api.verificationEvents(nextId)).events);
  };
  useEffect(() => { refresh().catch((problem) => setError(problem.message)); }, []);
  const chooseDoctor = async (doctorId) => {
    setSelectedId(doctorId); setError('');
    try { setEvents((await api.verificationEvents(doctorId)).events); }
    catch (problem) { setError(problem.message); }
  };
  const setStatus = async (status) => {
    if (!selected) return;
    setBusy(true); setError(''); setNotice('');
    try { await api.setDoctorVerification(selected.id, status, note); setNotice(`Doctor verification status set to ${status}.`); await refresh(selected.id); }
    catch (problem) { setError(problem.message); }
    finally { setBusy(false); }
  };
  const signOut = async () => { await logout(); navigate('/'); };
  return <main className="admin-verification-page"><header className="admin-topbar"><span className="admin-brand"><ShieldCheck size={19}/> MediBridge <b>AI</b><small>ADMIN REVIEW</small></span><div><span>{user.email}</span><button className="button button-outline" onClick={signOut}><LogOut size={14}/> Sign out</button></div></header><section className="admin-content"><div className="admin-page-heading"><div><span className="eyebrow">DEMO ADMIN CONSOLE</span><h1>Doctor verification</h1><p>Review fictional profile details. Changes are saved in SQLite and recorded in the audit history.</p></div><span className="demo-tag">PROTOTYPE ONLY</span></div>{notice && <div className="success-banner">{notice}</div>}{error && <div className="error-banner" role="alert">{error}</div>}<div className="verification-workspace"><aside className="verification-doctor-list"><div className="history-title">DOCTOR PROFILES · {doctors.length}</div>{doctors.map((doctor) => <button key={doctor.id} className={`verification-doctor-option ${doctor.id === selected?.id ? 'selected' : ''}`} onClick={() => chooseDoctor(doctor.id)}><span className="person-avatar"><UserRound size={15}/></span><span><strong>{doctor.name}</strong><small>{doctor.specialty}</small></span><VerificationBadge status={doctor.verification_status}/></button>)}{doctors.length === 0 && <div className="empty-small">No doctor profiles found.</div>}</aside><section className="verification-review-panel">{selected ? <><div className="review-profile-heading"><div><span className="doctor-profile-icon"><UserRound size={21}/></span><div><h2>{selected.name}</h2><p>{selected.email}</p></div></div><VerificationBadge status={selected.verification_status}/></div><dl className="review-profile-details"><div><dt>Specialty</dt><dd>{selected.specialty}</dd></div><div><dt>Qualification entered</dt><dd>{selected.qualification}</dd></div><div><dt>Experience entered</dt><dd>{selected.experience} years</dd></div></dl><div className="review-caution"><ShieldCheck size={16}/><p>These details are self-entered demo profile information. A registration ID or this local review does not establish real-world medical credentials.</p></div><label className="review-note">Reviewer note<textarea rows="3" maxLength="1000" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Record the reason for this demo status change"/></label><div className="verification-actions"><button disabled={busy} className="button status-action verified-action" onClick={() => setStatus('verified')}><Check size={15}/> Mark verified</button><button disabled={busy} className="button status-action pending-action" onClick={() => setStatus('pending')}><Clock3 size={15}/> Keep pending</button><button disabled={busy} className="button status-action rejected-action" onClick={() => setStatus('rejected')}><X size={15}/> Reject</button></div><section className="verification-audit"><h3>Review history</h3>{events.map((event) => <article key={event.id}><span>{event.previous_status} → {event.new_status}</span><small>{event.reviewed_by} · {event.created_at}</small>{event.note && <p>{event.note}</p>}</article>)}{events.length === 0 && <p className="tiny-note">No review actions recorded.</p>}</section></> : <div className="empty-state">Select a doctor profile to review.</div>}</section></div><p className="admin-legal-note">MediBridge’s demo admin action is not a substitute for licensing-board or identity verification. Do not use this prototype to grant real clinical privileges.</p></section></main>;
}
