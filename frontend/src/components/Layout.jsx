import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Activity, CalendarDays, ClipboardPlus, FileHeart, HeartPulse, Hospital, LayoutDashboard, LogOut, MessageCircle, PhoneCall, Pill, Settings, ShieldAlert, Stethoscope, UserRound, UsersRound, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import './layout.css';

const navigation = [
  { path: '/dashboard', key: 'dashboard', icon: LayoutDashboard, patient: true, doctor: true },
  { path: '/doctor/profile', key: 'doctorProfile', icon: UserRound, doctor: true },
  { path: '/assistant', key: 'assistant', icon: HeartPulse, patient: true },
  { path: '/doctors', key: 'doctors', icon: Stethoscope, patient: true },
  { path: '/hospitals', key: 'hospitals', icon: Hospital, patient: true, doctor: true },
  { path: '/emergency', key: 'emergencyHelp', icon: PhoneCall, patient: true },
  { path: '/appointments', key: 'appointments', icon: CalendarDays, patient: true, doctor: true },
  { path: '/family', key: 'family', icon: UsersRound, patient: true },
  { path: '/medicines', key: 'medicines', icon: Pill, patient: true, doctor: true },
  { path: '/patients', key: 'patients', icon: UserRound, doctor: true, verifiedOnly: true },
  { path: '/messages', key: 'messages', icon: MessageCircle, patient: true, doctor: true, verifiedOnly: true },
  { path: '/consultations', key: 'consultations', icon: ClipboardPlus, patient: true, doctor: true, verifiedOnly: true },
  { path: '/reports', key: 'reports', icon: FileHeart, patient: true, doctor: true, verifiedOnly: true },
  { path: '/settings', key: 'settings', icon: Settings, patient: true, doctor: true },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const [sosOpen, setSosOpen] = useState(false);
  const navigate = useNavigate();
  const signOut = async () => { await logout(); navigate('/'); };
  const changeLanguage = async (event) => { const next = event.target.value; try { await api.language(next); setLanguage(next); } catch { event.target.value = language; } };
  return <div className="app-shell">
    <aside className="sidebar">
      <NavLink to={user.role === 'doctor' ? '/doctor/dashboard' : '/dashboard'} className="brand"><span className="brand-icon"><Activity size={20} /></span><span>MediBridge <b>AI</b><small>RIGHT CARE, LESS WAITING</small></span></NavLink>
      <div className="side-label">WORKSPACE</div>
      <nav className="side-nav">{navigation.filter((item) => item[user.role] && !(user.role === 'doctor' && item.verifiedOnly && !user.doctor_verified)).map(({ path, key, icon: Icon }) => <NavLink key={path} to={path === '/dashboard' && user.role === 'doctor' ? '/doctor/dashboard' : path} end={path === '/dashboard'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={18} /><span>{t(key)}</span></NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="demo-note"><span className="demo-dot" />{t('demo')}</div><button className="nav-item signout" onClick={signOut}><LogOut size={18} />{t('logout')}</button></div>
    </aside>
    <main className="main-column">
      <header className="topbar"><div className="mobile-brand"><Activity size={19} /> MediBridge <b>AI</b></div><div className="topbar-right"><select className="header-language" aria-label="Interface language" value={language} onChange={changeLanguage}><option value="en">EN</option><option value="hi">हिन्दी</option></select><span className="role-chip">{t(user.role)}</span><span className="user-name">{user.name}</span><button className="icon-button top-logout" onClick={signOut} aria-label={t('logout')} title={t('logout')}><LogOut size={16}/></button><button className="sos-button" onClick={() => setSosOpen(true)}><ShieldAlert size={17} /> {t('emergency')}</button></div></header>
      <div className="page-content"><Outlet /></div>
    </main>
    {sosOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setSosOpen(false)}><section className="emergency-modal" role="dialog" aria-modal="true" aria-labelledby="emergency-title"><button className="icon-button modal-close" aria-label="Close" onClick={() => setSosOpen(false)}><X size={18} /></button><div className="emergency-symbol"><ShieldAlert size={25} /></div><p className="eyebrow danger-text">IMMEDIATE HELP</p><h2 id="emergency-title">Are you in immediate danger?</h2><p>If this may be life-threatening, call emergency services now. MediBridge does not dispatch an ambulance.</p><a className="button button-danger call-button" href="tel:112">Call 112</a><p className="tiny-note">In India, call 112. Outside India, contact your local emergency number. Do not wait for an online consultation.</p><button className="text-button" onClick={() => { setSosOpen(false); navigate('/hospitals'); }}>View demo emergency hospitals</button></section></div>}
  </div>;
}
