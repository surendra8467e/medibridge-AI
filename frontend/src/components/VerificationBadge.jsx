import './verification-badge.css';

const labels = { pending: 'Pending verification', verified: 'Verified demo profile', rejected: 'Verification rejected' };
export default function VerificationBadge({ status = 'pending' }) {
  const safeStatus = Object.hasOwn(labels, status) ? status : 'pending';
  return <span className={`verification-badge verification-${safeStatus}`} role="status">{labels[safeStatus]}</span>;
}
