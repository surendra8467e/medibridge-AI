import { ArrowLeft, Hospital, PhoneCall, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import './emergency-help.css';

export default function EmergencyHelp() {
  return <div className="page-standard emergency-help-page"><div className="page-title-row"><div><span className="eyebrow danger-text">IMMEDIATE HELP</span><h1>Emergency help</h1><p>If someone may be in immediate danger, get emergency help now.</p></div><span className="emergency-symbol"><ShieldAlert size={24}/></span></div><section className="emergency-help-banner"><ShieldAlert size={23}/><div><strong>Do not wait for an online consultation or bed request.</strong><p>MediBridge does not dispatch an ambulance. Call emergency services directly.</p></div></section><a className="emergency-call-link" href="tel:112"><PhoneCall size={21}/><span><strong>Call 112</strong><small>India emergency number · use your local emergency number outside India</small></span></a><div className="emergency-help-actions"><Link className="button button-outline" to="/hospitals"><Hospital size={16}/> View demo hospitals</Link><Link className="button button-outline" to="/dashboard"><ArrowLeft size={15}/> Back to dashboard</Link></div><p className="tiny-note">Hospital and bed data in this prototype is simulated and must not be used to coordinate emergency care.</p></div>;
}
