import { useState } from 'react';
import { Activity, ArrowRight, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AuthPage({ register = false }) {
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'patient' });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const { authenticate } = useAuth();
  const navigate = useNavigate();
  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await authenticate(register ? 'register' : 'login', form); navigate('/'); }
    catch (problem) { setError(problem.message); }
    finally { setBusy(false); }
  };
  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));
  return <main className="auth-screen"><section className="auth-visual"><div className="auth-brand"><Activity size={24} /> MediBridge <b>AI</b></div><div className="visual-copy"><span className="eyebrow">CARE THAT MEETS YOU HERE</span><h1>Right care.<br />Less waiting.</h1><p>Thoughtful tools for patients and care teams, built around a more connected healthcare journey.</p><div className="visual-stat"><ShieldCheck size={19} /><span>Private by design <small>Your information stays in your local demo database.</small></span></div></div><div className="visual-foot">HACKSHIFT 2026 <span>·</span> SILENT REVOLUTION</div></section><section className="auth-panel"><div className="auth-form-wrap"><div className="mobile-auth-brand"><Activity size={21} /> MediBridge <b>AI</b></div><span className="eyebrow">{register ? 'GET STARTED' : 'WELCOME BACK'}</span><h2>{register ? 'Create your account' : 'Sign in to continue'}</h2><p className="muted">{register ? 'Join a connected care experience.' : 'Pick up where your care journey left off.'}</p><form onSubmit={submit} className="form-stack">{register && <label>Full name<input autoComplete="name" value={form.name} onChange={set('name')} required /></label>}<label>Email address<input type="email" autoComplete="email" value={form.email} onChange={set('email')} required /></label><label>Password<div className="password-wrap"><input type={showPassword ? 'text' : 'password'} autoComplete={register ? 'new-password' : 'current-password'} minLength={register ? 8 : undefined} value={form.password} onChange={set('password')} required /><button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password visibility">{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>{register && <label>Account type<select value={form.role} onChange={set('role')}><option value="patient">Patient</option><option value="doctor">Doctor</option></select></label>}{error && <div className="error-banner" role="alert">{error}</div>}<button className="button button-primary auth-submit" disabled={busy}>{busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'} <ArrowRight size={17} /></button></form><div className="demo-credentials"><strong>Demo access</strong><span>Patient: patient@medibridge.demo</span><span>Doctor: doctor@medibridge.demo</span><span>Password for both: DemoPatient123! / DemoDoctor123!</span></div><p className="auth-switch">{register ? 'Already have an account?' : 'New to MediBridge?'} <Link to={register ? '/login' : '/register'}>{register ? 'Sign in' : 'Create an account'}</Link></p><p className="tiny-note">Demo environment only. This application does not provide medical diagnosis or emergency dispatch.</p></div></section></main>;
}
