import { useEffect, useMemo, useState } from 'react';
import { BedDouble, MapPin, Search } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Hospitals() {
  const { user } = useAuth();
  const [hospitals, setHospitals] = useState([]);
  const [requests, setRequests] = useState([]);
  const [query, setQuery] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const refresh = async () => {
    try {
      const result = await api.hospitals();
      setHospitals(result.hospitals);
      if (user.role === 'patient') setRequests((await api.bedRequests()).requests);
    } catch (problem) { setError(problem.message); }
  };
  useEffect(() => { refresh(); }, []);
  const filtered = useMemo(() => hospitals.filter((hospital) => `${hospital.name} ${hospital.location} ${hospital.services}`.toLowerCase().includes(query.toLowerCase())), [hospitals, query]);
  const requestBed = async (hospital) => {
    try { const result = await api.bedRequest(hospital.id, 'Patient initiated demo availability inquiry'); setNotice(result.message); await refresh(); }
    catch (problem) { setError(problem.message); }
  };
  const updateBeds = async (hospital) => {
    const raw = window.prompt('Set simulated available bed count', String(hospital.available ?? 0));
    if (raw === null) return;
    const available = Number(raw);
    if (!Number.isInteger(available) || available < 0) { setError('Enter a non-negative whole number.'); return; }
    try { await api.updateBeds(hospital.id, available); setNotice('Simulated bed count updated.'); await refresh(); }
    catch (problem) { setError(problem.message); }
  };
  return <div className="directory-page"><div className="page-title-row"><div><span className="eyebrow">LOCAL DEMO DIRECTORY</span><h1>Hospitals & bed availability</h1><p>All facilities and bed counts are simulated, not live or reserved.</p></div></div><label className="search-field"><Search size={17}/><input aria-label="Search hospitals" placeholder="Search hospital or location" value={query} onChange={(event) => setQuery(event.target.value)}/></label>{notice && <div className="success-banner">{notice}<button onClick={() => setNotice('')}>Dismiss</button></div>}{error && <div className="error-banner">{error}<button onClick={() => setError('')}>Dismiss</button></div>}<div className="directory-grid">{filtered.map((hospital) => <article className="directory-card" key={hospital.id}><div className="directory-card-top"><span className="hospital-mark"><MapPin size={19}/></span><span className="demo-tag">SIMULATED</span></div><h2>{hospital.name}</h2><p className="card-detail"><MapPin size={14}/>{hospital.location}</p><p className="card-detail">{hospital.services}</p><div className="bed-status"><BedDouble size={17}/><span><strong>{hospital.available ?? '—'} demo beds</strong><small>Updated {hospital.updated_at || 'on startup'} · not live</small></span></div><div className="doctor-card-footer"><span className="emergency-label">{hospital.emergency ? 'Emergency facility (demo)' : 'General care (demo)'}</span>{user.role === 'patient' ? <button className="button button-primary" onClick={() => requestBed(hospital)}>Send inquiry</button> : <button className="button button-outline" onClick={() => updateBeds(hospital)}>Update beds</button>}</div></article>)}{filtered.length === 0 && <div className="empty-state">No matching hospitals. Try another search.</div>}</div>{user.role === 'patient' && <section className="records-list"><h2>My bed inquiries</h2>{requests.map((item) => <article className="appointment-row" key={item.id}><div className="appointment-icon"><BedDouble size={18}/></div><div className="appointment-info"><strong>{item.hospital_name}</strong><small>{item.created_at}</small></div><span className="status-pill status-requested">{item.status}</span></article>)}{requests.length === 0 && <div className="empty-state">No bed inquiries submitted.</div>}</section>}</div>;
}
