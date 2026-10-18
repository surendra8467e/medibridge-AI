import { useState } from 'react';
import { Activity, ArrowLeft, ArrowRight, UsersRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './role-login.css';

export default function RoleRegister() {
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const { authenticate } = useAuth();
  const navigate = useNavigate();
  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await authenticate('register', { ...form, role: 'patient' }); navigate('/dashboard'); }
    catch (problem) { setError(problem.message); }
    finally { setBusy(false); }
  };
  return <main className="role-login family-login"><div className="login-aside"><Link className="landing-brand" to="/"><span><Activity size={21}/></span>MediBridge <b>AI</b></Link><div className="login-aside-copy"><span className="section-kicker">FAMILY HEALTH SPACE</span><h1>A clearer home for your family’s health details.</h1><p>Create a patient account to keep profiles, records, and care requests together.</p></div><Link to="/" className="back-home"><ArrowLeft size={15}/> Back to MediBridge</Link></div><section className="login-form-side"><div className="role-login-card"><div className="role-login-icon"><UsersRound size={22}/></div><span className="section-kicker">PATIENT REGISTRATION</span><h2>Create your account</h2><p>Accounts are stored in the local demo database.</p><form onSubmit={submit}><label>Full name<input autoComplete="name" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })}/></label><label>Email address<input autoComplete="email" type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })}/></label><label>Phone number, optional<input autoComplete="tel" type="tel" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })}/></label><label>Password<input autoComplete="new-password" type="password" minLength={8} required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })}/></label>{error && <div className="error-banner" role="alert">{error}</div>}<button className="role-submit" disabled={busy}>{busy ? 'Creating account…' : 'Create patient account'}<ArrowRight size={16}/></button></form><Link className="switch-role" to="/patient/login">Already registered? Sign in</Link></div></section></main>;
}
