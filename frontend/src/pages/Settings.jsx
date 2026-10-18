import { useEffect, useState } from 'react';
import { Languages, ShieldCheck, UserRound } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

export default function Settings() {
  const { user } = useAuth();
  const { language, setLanguage } = useLanguage();
  const [history, setHistory] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  useEffect(() => { if (user.role === 'patient') api.profile().then((result) => setHistory(result.profile.history)).catch((problem) => setError(problem.message)); }, [user]);
  const changeLanguage = async (next) => { try { await api.language(next); setLanguage(next); setNotice('Language preference saved.'); } catch (problem) { setError(problem.message); } };
  const saveHistory = async (event) => { event.preventDefault(); try { await api.saveProfile(history); setNotice('Health history saved to your patient profile.'); } catch (problem) { setError(problem.message); } };
  return <div className="page-standard"><div className="page-title-row"><div><span className="eyebrow">PERSONAL PREFERENCES</span><h1>Settings</h1><p>Manage language and the profile information you choose to share.</p></div></div>{notice && <div className="success-banner">{notice}</div>}{error && <div className="error-banner">{error}</div>}<section className="settings-section"><div className="settings-heading"><Languages size={20}/><div><h2>Language</h2><p>Choose the interface and assistant response language.</p></div></div><div className="language-options"><button className={`language-option ${language === 'en' ? 'chosen' : ''}`} onClick={() => changeLanguage('en')}><strong>English</strong><span>English</span></button><button className={`language-option ${language === 'hi' ? 'chosen' : ''}`} onClick={() => changeLanguage('hi')}><strong>हिन्दी</strong><span>Hindi</span></button></div></section>{user.role === 'patient' && <section className="settings-section"><div className="settings-heading"><UserRound size={20}/><div><h2>Shared health history</h2><p>This information is visible only to your assigned doctor.</p></div></div><form className="form-stack" onSubmit={saveHistory}><label>Health history<textarea rows="5" maxLength="4000" value={history} onChange={(event) => setHistory(event.target.value)} placeholder="Share relevant information you want your assigned doctor to see."/></label><button className="button button-primary">Save profile</button></form></section>}<section className="privacy-note"><ShieldCheck size={19}/><span><strong>Demo privacy</strong><small>Authentication uses signed session tokens and hashed passwords. Data is stored in your local SQLite demo database. Do not enter real sensitive medical information.</small></span></section></div>;
}
