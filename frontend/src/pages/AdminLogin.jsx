import { useState } from 'react';
import { ArrowRight, LockKeyhole, ShieldCheck } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './admin-verification.css';

export default function AdminLogin() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const { authenticate } = useAuth();
  const navigate = useNavigate();
  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await authenticate('adminLogin', form); navigate('/admin/verification'); }
    catch (problem) { setError(problem.message); }
    finally { setBusy(false); }
  };
  return <main className="admin-login-screen"><Link className="landing-brand" to="/"><span><ShieldCheck size={21}/></span>MediBridge <b>AI</b></Link><section className="admin-login-card"><span className="admin-login-icon"><LockKeyhole size={21}/></span><span className="eyebrow">AUTHORIZED DEMO ADMIN</span><h1>Doctor verification</h1><p>Sign in to review demo doctor profiles and update their verification status.</p><form className="form-stack" onSubmit={submit}><label>Admin email<input type="email" required autoComplete="username" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })}/></label><label>Password<input type="password" required autoComplete="current-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })}/></label>{error && <div className="error-banner" role="alert">{error}</div>}<button className="button button-primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in as demo admin'} <ArrowRight size={15}/></button></form><div className="admin-demo-credentials"><strong>Local prototype admin</strong><span>admin@medibridge.demo</span><span>DemoAdmin123!</span></div><p className="tiny-note">This demo workflow is not real-world credential verification. Admin credentials are for local prototype use only.</p></section></main>;
}
