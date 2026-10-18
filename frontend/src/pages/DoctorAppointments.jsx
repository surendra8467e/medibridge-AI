import { Link } from 'react-router-dom';
import { ArrowRight, ShieldAlert } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import VerificationBadge from '../components/VerificationBadge';
import Appointments from './Appointments';
import './doctor-appointments.css';

export default function DoctorAppointments() {
  const { user } = useAuth();
  const status = user.verificationStatus || 'pending';
  return <div className="page-standard doctor-appointment-management"><div className="page-title-row"><div><span className="eyebrow">CLINICIAN SCHEDULE</span><h1>Appointment management</h1><p>Patient appointments are available after administrator verification.</p></div><VerificationBadge status={status}/></div>{status === 'verified' ? <div className="doctor-appointment-content"><Appointments/></div> : <section className={`verification-appointment-notice notice-${status}`}><ShieldAlert size={20}/><div><strong>{status === 'rejected' ? 'Doctor verification was rejected' : 'Verification is pending'}</strong><p>{status === 'rejected' ? (user.verificationNote || 'Please contact the demo administrator for review.') : 'Appointment requests and patient records are restricted until an authorized administrator reviews your profile.'}</p><Link to="/doctor/profile">View doctor profile <ArrowRight size={14}/></Link></div></section>}</div>;
}
