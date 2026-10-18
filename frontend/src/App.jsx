import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './layouts';
import Landing from './pages/Landing';
import RoleLogin from './pages/RoleLogin';
import RoleRegister from './pages/RoleRegister';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Patients from './pages/Patients';
import Hospitals from './pages/Hospitals';
import Chat from './pages/Chat';
import Directory from './pages/Directory';
import Appointments from './pages/Appointments';
import Messages from './pages/Messages';
import Consultations from './pages/Consultations';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import Family from './pages/Family';
import Medicines from './pages/Medicines';
import MedicalReports from './pages/MedicalReports';
import BedBooking from './pages/BedBooking';
import PatientDashboard from './pages/PatientDashboard';
import DoctorDashboard from './pages/DoctorDashboard';
import EmergencyHelp from './pages/EmergencyHelp';
import HealthAssistant, { AssistantChat } from './pages/HealthAssistant';
import DoctorProfile from './pages/DoctorProfile';
import AdminLogin from './pages/AdminLogin';
import AdminVerification from './pages/AdminVerification';
import DoctorAppointments from './pages/DoctorAppointments';

export default function App() {
  const { user, ready } = useAuth();
  if (!ready) return <div className="startup"><span className="loader" />Preparing your secure session</div>;
  return <Routes>
    <Route path="/" element={<Landing />} />
    <Route path="/patient/login" element={user ? <Navigate to={user.role === 'doctor' ? '/doctor/dashboard' : user.role === 'admin' ? '/admin/verification' : '/dashboard'} replace /> : <RoleLogin role="patient" />} />
    <Route path="/doctor/login" element={user ? <Navigate to={user.role === 'doctor' ? '/doctor/dashboard' : user.role === 'admin' ? '/admin/verification' : '/dashboard'} replace /> : <RoleLogin role="doctor" />} />
    <Route path="/patient/register" element={user ? <Navigate to={user.role === 'doctor' ? '/doctor/dashboard' : '/dashboard'} replace /> : <RoleRegister />} />
    <Route path="/admin/login" element={user?.role === 'admin' ? <Navigate to="/admin/verification" replace /> : <AdminLogin />} />
    <Route path="/admin/verification" element={user?.role === 'admin' ? <AdminVerification /> : <Navigate to="/admin/login" replace />} />
    <Route path="/login" element={<Navigate to="/patient/login" replace />} />
    <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <AuthPage register />} />
    <Route element={user ? <Layout /> : <Navigate to="/" replace />}>
      <Route path="/dashboard" element={user?.role === 'doctor' ? <Navigate to="/doctor/dashboard" replace /> : user?.role === 'patient' ? <PatientDashboard /> : <Navigate to="/" replace />} />
      <Route path="/doctor/dashboard" element={user?.role === 'doctor' ? <DoctorDashboard /> : <Navigate to="/dashboard" replace />} />
      <Route path="/doctor/profile" element={user?.role === 'doctor' ? <DoctorProfile /> : <Navigate to="/dashboard" replace />} />
      <Route path="/doctor/appointments" element={user?.role === 'doctor' ? <DoctorAppointments /> : <Navigate to="/dashboard" replace />} />
      <Route path="assistant" element={user?.role === 'patient' ? <HealthAssistant /> : <Navigate to="/dashboard" replace />}>
        <Route index element={<AssistantChat />} />
        <Route path="reports" element={<MedicalReports />} />
        <Route path="medicines" element={<Medicines />} />
        <Route path="prescriptions" element={<Consultations />} />
        <Route path="history" element={<Settings />} />
      </Route>
      <Route path="doctors" element={user?.role === 'patient' ? <Directory kind="doctors" /> : <Navigate to="/dashboard" replace />} />
      <Route path="hospitals" element={user?.role === 'patient' ? <BedBooking /> : <Hospitals />} />
      <Route path="appointments" element={user?.role === 'doctor' ? <DoctorAppointments /> : <Appointments />} />
      <Route path="patients" element={user?.role === 'doctor' && user.doctor_verified ? <Patients /> : user?.role === 'doctor' ? <Navigate to="/doctor/profile" replace /> : <Navigate to="/dashboard" replace />} />
      <Route path="family" element={user?.role === 'patient' ? <Family /> : <Navigate to="/dashboard" replace />} />
      <Route path="medicines" element={user?.role === 'doctor' && !user.doctor_verified ? <Navigate to="/doctor/profile" replace /> : <Medicines />} />
      <Route path="messages" element={user?.role === 'doctor' && !user.doctor_verified ? <Navigate to="/doctor/profile" replace /> : <Messages />} />
      <Route path="consultations" element={user?.role === 'doctor' && !user.doctor_verified ? <Navigate to="/doctor/profile" replace /> : <Consultations />} />
      <Route path="reports" element={user?.role === 'patient' ? <MedicalReports /> : user?.role === 'doctor' && user.doctor_verified ? <Reports /> : <Navigate to="/doctor/profile" replace />} />
      <Route path="emergency" element={<EmergencyHelp />} />
      <Route path="settings" element={<Settings />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
