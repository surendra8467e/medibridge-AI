import { NavLink, Outlet } from 'react-router-dom';
import { Activity, FileHeart, History, Pill, Sparkles } from 'lucide-react';
import Chat from './Chat';
import './health-assistant.css';

const tabs = [
  { to: '/assistant', label: 'AI Health Assistant', icon: Sparkles, end: true },
  { to: '/assistant/reports', label: 'Medical Reports', icon: FileHeart },
  { to: '/assistant/medicines', label: 'Medicines', icon: Pill },
  { to: '/assistant/prescriptions', label: 'Prescriptions', icon: Activity },
  { to: '/assistant/history', label: 'Health History', icon: History },
];
export default function HealthAssistant() {
  return <div className="health-hub"><nav className="health-tabs" aria-label="Healthcare assistant tools">{tabs.map(({ to, label, icon: Icon, end }) => <NavLink end={end} key={to} to={to}><Icon size={15}/>{label}</NavLink>)}</nav><Outlet/></div>;
}
export function AssistantChat() { return <Chat/>; }
