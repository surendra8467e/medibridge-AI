import { useEffect, useState } from 'react';
import { ArrowUpRight, CalendarDays, HeartPulse, Hospital, MessageCircle, ShieldCheck, Sparkles, Stethoscope } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

export default function Dashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [counts, setCounts] = useState({ appointments: 0, hospitals: 0 });
  const [status, setStatus] = useState('Checking API connection…');
  useEffect(() => {
    Promise.all([api.appointments(), api.hospitals(), api.health()]).then(([a, h, health]) => {
      setCounts({ appointments: a.appointments.length, hospitals: h.hospitals.length }); setStatus(health.status === 'ok' ? 'API connected' : 'API unavailable');
    }).catch(() => setStatus('Backend unavailable · start Flask on port 5000'));
  }, []);
  const patientCards = [
    { to: '/assistant', icon: HeartPulse, title: t('assistant'), desc: 'Talk through symptoms with preliminary, safety-first guidance.', tint: 'mint' },
    { to: '/doctors', icon: Stethoscope, title: t('doctors'), desc: 'Browse fictional demo profiles and request an appointment.', tint: 'blue' },
    { to: '/hospitals', icon: Hospital, title: t('hospitals'), desc: 'Explore simulated facilities and submit a demo inquiry.', tint: 'coral' },
  ];
  return <div className="dashboard-page"><div className="welcome-row"><div><span className="eyebrow">YOUR CARE, IN ONE PLACE</span><h1>{t('welcome')} <span className="welcome-name">{user.name.split(' ')[0]}.</span></h1><p>{t('subtitle')}</p></div><div className="connection-pill"><span className={`connection-dot ${status.startsWith('API connected') ? 'connected' : ''}`} />{status}</div></div><section className="welcome-banner"><div><div className="banner-kicker"><Sparkles size={15} /> MEDIBRIDGE AI</div><h2>A little more clarity,<br />at every step.</h2><p>Find support, keep your care organized, and stay connected to your healthcare team.</p><Link className="button button-light" to={user.role === 'patient' ? '/assistant' : '/appointments'}>{user.role === 'patient' ? 'Open health assistant' : 'Review appointments'} <ArrowUpRight size={16} /></Link></div><div className="banner-art" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="health-mark"><HeartPulse size={47} strokeWidth={1.5}/></div><span className="orbit-point point-one"/><span className="orbit-point point-two"/><span className="orbit-point point-three"/></div></section><div className="section-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h2>Quick access</h2></div><span className="data-badge"><ShieldCheck size={14} /> Local demo data</span></div><div className="quick-grid">{user.role === 'patient' ? patientCards.map(({ to, icon: Icon, title, desc, tint }) => <Link to={to} className="quick-card" key={to}><span className={`quick-icon ${tint}`}><Icon size={20}/></span><span className="quick-card-title">{title}<ArrowUpRight size={15}/></span><span className="quick-card-desc">{desc}</span></Link>) : <><Link to="/appointments" className="quick-card"><span className="quick-icon blue"><CalendarDays size={20}/></span><span className="quick-card-title">Appointments <ArrowUpRight size={15}/></span><span className="quick-card-desc">Review requests and update appointment status.</span></Link><Link to="/messages" className="quick-card"><span className="quick-icon mint"><MessageCircle size={20}/></span><span className="quick-card-title">Patient messages <ArrowUpRight size={15}/></span><span className="quick-card-desc">Message explicitly assigned patients.</span></Link><Link to="/consultations" className="quick-card"><span className="quick-icon coral"><HeartPulse size={20}/></span><span className="quick-card-title">Consultation notes <ArrowUpRight size={15}/></span><span className="quick-card-desc">Prepare and approve patient-facing summaries.</span></Link></>}</div><div className="stats-row"><div className="stat-panel"><CalendarDays size={19}/><span><strong>{counts.appointments}</strong><small>Appointments</small></span></div><div className="stat-panel"><Hospital size={19}/><span><strong>{counts.hospitals}</strong><small>Demo hospitals</small></span></div><div className="stat-panel"><MessageCircle size={19}/><span><strong>{user.role === 'patient' ? 'Private' : 'Assigned'}</strong><small>Care conversations</small></span></div></div><p className="safety-footnote"><ShieldCheck size={15}/> Health guidance is preliminary and does not replace a qualified clinician. For a medical emergency, call 112 in India or your local emergency number.</p></div>;
}
