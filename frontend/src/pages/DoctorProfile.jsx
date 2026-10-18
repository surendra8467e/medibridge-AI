import { useEffect, useState } from 'react';
import { BriefcaseMedical, Mail, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import VerificationBadge from '../components/VerificationBadge';
import './doctor-profile.css';

const guidance = {
  pending: 'Your profile is pending review by the demo administrator. Patient-record tools remain restricted until an authorized reviewer updates this status.',
  verified: 'This is a verified demo profile only. No real-world license or credential check is connected to this prototype.',
  rejected: 'The demo administrator rejected this profile. Contact the project administrator for review; you cannot change your own verification status.',
};
export default function DoctorProfile() {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { api.doctorProfile().then((result) => setProfile(result.profile)).catch((problem) => setError(problem.message)); }, []);
  if (error) return <div className="page-standard"><div className="error-banner" role="alert">{error}</div></div>;
  if (!profile) return <div className="startup"><span className="loader"/>Loading doctor profile</div>;
  return <div className="page-standard doctor-profile-page"><div className="page-title-row"><div><span className="eyebrow">CLINICIAN ACCOUNT</span><h1>Doctor profile</h1><p>Your profile information and administrator review status.</p></div><VerificationBadge status={profile.verification_status}/></div><section className="doctor-profile-card"><div className="doctor-profile-icon"><BriefcaseMedical size={24}/></div><h2>{profile.name}</h2><span className="doctor-profile-specialty">{profile.specialty}</span><dl><div><dt><Mail size={14}/> Account email</dt><dd>{profile.email}</dd></div><div><dt>Qualification</dt><dd>{profile.qualification}</dd></div><div><dt>Experience</dt><dd>{profile.experience} years</dd></div><div><dt>Demo consultation fee</dt><dd>₹{profile.fee}</dd></div></dl><div className={`verification-guidance guidance-${profile.verification_status}`}><ShieldCheck size={18}/><div><strong>Verification status</strong><p>{guidance[profile.verification_status] || guidance.pending}</p>{profile.verification_note && <small>Reviewer note: {profile.verification_note}</small>}</div></div><p className="tiny-note">A registration ID or self-entered profile detail is not proof of credentials. Only the separate authorized admin review flow can change this status.</p></section></div>;
}
