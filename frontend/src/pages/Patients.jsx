import { useEffect, useMemo, useState } from 'react';
import { Search, UserRound } from 'lucide-react';
import { api } from '../services/api';
import './patients.css';

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { api.patients().then((result) => { setPatients(result.patients); setSelected(result.patients[0] || null); }).catch((problem) => setError(problem.message)); }, []);
  const filtered = useMemo(() => patients.filter((patient) => `${patient.name} ${patient.email}`.toLowerCase().includes(query.toLowerCase())), [patients, query]);
  const select = async (patient) => { try { const result = await api.patient(patient.id); setSelected(result.patient); setError(''); } catch (problem) { setError(problem.message); } };
  return <div className="page-standard"><div className="page-title-row"><div><span className="eyebrow">AUTHORIZED CARE ONLY</span><h1>My patients</h1><p>Only patients explicitly assigned to your account are listed.</p></div></div>{error && <div className="error-banner">{error}</div>}<div className="patient-workspace"><aside className="patient-directory"><label className="search-field"><Search size={15}/><input placeholder="Search assigned patients" aria-label="Search assigned patients" value={query} onChange={(event) => setQuery(event.target.value)}/></label>{filtered.map((patient) => <button key={patient.id} className={`patient-select ${selected?.id === patient.id ? 'selected' : ''}`} onClick={() => select(patient)}><span className="person-avatar">{patient.name.slice(0, 1)}</span><span><strong>{patient.name}</strong><small>{patient.email}</small></span></button>)}{filtered.length === 0 && <p className="empty-small">No assigned patients.</p>}</aside><section className="patient-detail">{selected ? <><div className="patient-profile-head"><span className="patient-large-avatar"><UserRound size={25}/></span><div><span className="eyebrow">PATIENT PROFILE</span><h2>{selected.name}</h2><p>{selected.email}</p></div></div><div className="patient-field"><span>Patient-shared health history</span><p>{selected.history || 'No history has been shared.'}</p></div><div className="privacy-note"><UserRound size={18}/><span><strong>Assigned relationship</strong><small>This profile is available because this patient is assigned to you. Handle all information as confidential.</small></span></div></> : <div className="empty-state">No assigned patient is selected.</div>}</section></div></div>;
}
