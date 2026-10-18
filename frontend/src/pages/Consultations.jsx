import { useEffect, useState } from 'react';
import { ClipboardPlus, FileCheck2 } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Consultations() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [records, setRecords] = useState([]);
  const [selected, setSelected] = useState('');
  const [form, setForm] = useState({ notes: '', assessment: '', advice: '' });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const refresh = async () => {
    try { const [a, c] = await Promise.all([api.appointments(), api.consultations()]); setAppointments(a.appointments); setRecords(c.consultations); }
    catch (problem) { setError(problem.message); }
  };
  useEffect(() => { refresh(); }, []);
  const save = async (event) => { event.preventDefault(); try { const result = await api.saveConsultation({ appointment_id: Number(selected), ...form }); setNotice(`Draft saved. ${result.message}`); await refresh(); } catch (problem) { setError(problem.message); } };
  const approve = async (id) => { try { await api.approveConsultation(id); setNotice('Summary approved and shared with the authorized patient.'); await refresh(); } catch (problem) { setError(problem.message); } };
  return <div className="page-standard"><div className="page-title-row"><div><span className="eyebrow">CLINICAL RECORDS</span><h1>Consultation summaries</h1><p>Doctor-entered content only. Drafts require clinician review before sharing.</p></div></div>{notice && <div className="success-banner">{notice}</div>}{error && <div className="error-banner">{error}</div>}{user.role === 'doctor' && <section className="consult-form-panel"><div className="panel-heading"><ClipboardPlus size={20}/><div><h2>Create a consultation draft</h2><p>Only appointments assigned to your account are available.</p></div></div><form className="form-stack" onSubmit={save}><label>Appointment<select required value={selected} onChange={(event) => setSelected(event.target.value)}><option value="">Choose an appointment</option>{appointments.filter((item) => item.status === 'accepted' || item.status === 'completed').map((item) => <option value={item.id} key={item.id}>#{item.id} · {item.patient_name} · {item.scheduled_at}</option>)}</select></label><div className="form-grid"><label>Patient-reported concerns<textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })}/></label><label>Doctor-entered assessment<textarea value={form.assessment} onChange={(event) => setForm({ ...form, assessment: event.target.value })}/></label><label>Advice and follow-up<textarea value={form.advice} onChange={(event) => setForm({ ...form, advice: event.target.value })}/></label></div><button className="button button-primary" disabled={!selected}>Save draft</button></form></section>}<section className="records-list"><h2>{user.role === 'doctor' ? 'Your consultation drafts' : 'Approved consultation summaries'}</h2>{records.map((record) => <article className="record-card" key={record.id}><div className="record-heading"><FileCheck2 size={19}/><strong>Consultation · {record.scheduled_at}</strong><span className={`status-pill ${record.approved ? 'status-accepted' : 'status-requested'}`}>{record.approved ? 'approved' : 'draft'}</span></div><div className="record-copy">{record.summary || 'No summary content.'}</div>{user.role === 'doctor' && !record.approved && <button className="button button-primary" onClick={() => approve(record.appointment_id)}>Review and approve</button>}</article>)}{records.length === 0 && <div className="empty-state">No consultation records available.</div>}</section></div>;
}
