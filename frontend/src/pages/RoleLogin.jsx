import { useState } from 'react';
import { Activity, ArrowLeft, ArrowRight, Eye, EyeOff, ShieldCheck, Stethoscope, UsersRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './role-login.css';

export default function RoleLogin({ role }) {
  const isDoctor = role === 'doctor';
  const [form, setForm] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const { authenticate } = useAuth();
  const navigate = useNavigate();
  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await authenticate('login', { ...form, role }); navigate(role === 'doctor' ? '/doctor/dashboard' : '/dashboard'); }
    catch (problem) { setError(problem.message); }
    finally { setBusy(false); }
  };
  return <main className={`role-login ${isDoctor ? 'clinician-login' : 'family-login'}`}><div className="login-aside"><Link className="landing-brand" to="/"><span><Activity size={21}/></span>MediBridge <b>AI</b></Link><div className="login-aside-copy"><span className="section-kicker">{isDoctor ? 'CLINICIAN WORKSPACE' : 'FAMILY HEALTH SPACE'}</span><h1>{isDoctor ? 'A clearer view of every care relationship.' : 'Your family’s care, gathered in one place.'}</h1><p>{isDoctor ? 'Secure access to assigned patients, appointment requests, and clinician-authored notes.' : 'Keep important health details, appointments, and reports close at hand.'}</p><div className="login-aside-badge"><ShieldCheck size={18}/><span>{isDoctor ? 'Access is role restricted' : 'Profiles remain private to your account'}</span></div></div><Link to="/" className="back-home"><ArrowLeft size={15}/> Back to MediBridge</Link></div><section className="login-form-side"><div className="role-login-card"><div className="role-login-icon">{isDoctor ? <Stethoscope size={22}/> : <UsersRound size={22}/>}</div><span className="section-kicker">{isDoctor ? 'DOCTOR SIGN IN' : 'PATIENT SIGN IN'}</span><h2>{isDoctor ? 'Welcome, care professional' : 'Welcome back'}</h2><p>{isDoctor ? 'Sign in with the email linked to your demo doctor account.' : 'Sign in to continue to your family health dashboard.'}</p><form onSubmit={submit}><label>{isDoctor ? 'Doctor email or registration ID' : 'Email or phone number'}<input autoComplete="username" type={isDoctor ? 'text' : 'text'} required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} placeholder={isDoctor ? 'doctor@medibridge.demo' : 'Email address or phone number'}/></label><label>Password<div className="role-password"><input autoComplete="current-password" type={showPassword ? 'text' : 'password'} required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })}/><button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={17}/> : <Eye size={17}/>}</button></div></label><div className="form-links"><Link to="#forgot" onClick={(event) => { event.preventDefault(); setError('Password reset is not configured in this local demo. Contact your administrator.'); }}>Forgot password?</Link>{!isDoctor && <Link to="/patient/register">Create account</Link>}</div>{error && <div className="error-banner" role="alert">{error}</div>}<button className="role-submit" disabled={busy}>{busy ? 'Checking your account…' : isDoctor ? 'Sign in to doctor workspace' : 'Sign in to patient portal'}<ArrowRight size={17}/></button></form>{isDoctor && <div className="doctor-verification"><ShieldCheck size={15}/><span><strong>Verification status</strong><small>Demo doctor profile status is shown after sign-in. A registration ID alone does not verify credentials.</small></span></div>}<div className="role-demo"><strong>DEMO ACCESS</strong><span>{isDoctor ? 'doctor@medibridge.demo' : 'patient@medibridge.demo'}</span><span>Password: {isDoctor ? 'DemoDoctor123!' : 'DemoPatient123!'}</span></div><Link className="switch-role" to={isDoctor ? '/patient/login' : '/doctor/login'}>{isDoctor ? 'Patient login instead' : 'Doctor login instead'}</Link></div></section></main>;
}
