import { useEffect, useRef, useState } from 'react';
import { Download, Eye, FileHeart, FilePlus2, X } from 'lucide-react';
import { api } from '../services/api';
import './medical-reports.css';

export default function MedicalReports() {
  const [uploads, setUploads] = useState([]);
  const [shared, setShared] = useState([]);
  const [members, setMembers] = useState([]);
  const [query, setQuery] = useState('');
  const [file, setFile] = useState(null);
  const fileInput = useRef(null);
  const [form, setForm] = useState({ title: '', category: 'lab', family_member_id: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [preview, setPreview] = useState(null);
  const refresh = async () => { const [u, r, f] = await Promise.all([api.uploads(), api.reports(), api.family()]); setUploads(u.uploads); setShared(r.reports); setMembers(f.members); };
  useEffect(() => { refresh().catch((problem) => setError(problem.message)); }, []);
  const submit = async (event) => {
    event.preventDefault(); if (!file) { setError('Select a PDF or image report first.'); return; }
    if (file.size > 10 * 1024 * 1024) { setError('Report files must be 10 MB or smaller.'); return; }
    setBusy(true); setError(''); setNotice('');
    const data = new FormData(); data.append('file', file); data.append('title', form.title); data.append('category', form.category); data.append('family_member_id', form.family_member_id);
    try { await api.uploadReport(data); setFile(null); setForm({ title: '', category: 'lab', family_member_id: '' }); if (fileInput.current) fileInput.current.value = ''; setNotice('Report uploaded to private storage.'); await refresh(); }
    catch (problem) { setError(problem.message); }
    finally { setBusy(false); }
  };
  const getFile = async (report, download = false) => {
    try { const blob = await api.reportFile(report.id); const url = URL.createObjectURL(blob); if (download) { const link = document.createElement('a'); link.href = url; link.download = report.original_name; link.click(); URL.revokeObjectURL(url); } else setPreview({ url, report }); }
    catch (problem) { setError(problem.message); }
  };
  const visibleUploads = uploads.filter((item) => `${item.title} ${item.category} ${item.family_member_name || ''}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="page-standard"><div className="page-title-row"><div><span className="eyebrow">PRIVATE DOCUMENT LIBRARY</span><h1>Medical reports</h1><p>PDF and image uploads stay in private backend storage and are accessible only to your account.</p></div><span className="quick-icon mint"><FileHeart size={20}/></span></div>{notice && <div className="success-banner">{notice}</div>}{error && <div className="error-banner" role="alert">{error}</div>}<section className="upload-panel"><div className="panel-heading"><FilePlus2 size={20}/><div><h2>Upload a report</h2><p>PDF, PNG, or JPEG · up to 10 MB</p></div></div><form className="form-stack" onSubmit={submit}><div className="form-grid"><label>Report title<input required maxLength="160" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })}/></label><label>Category<select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}><option value="lab">Lab results</option><option value="imaging">Imaging</option><option value="consultation">Consultation</option><option value="other">Other</option></select></label><label>Family member<select value={form.family_member_id} onChange={(event) => setForm({ ...form, family_member_id: event.target.value })}><option value="">Account holder</option>{members.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}</select></label></div><label className="file-input-label">Choose report file<input type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" required onChange={(event) => setFile(event.target.files?.[0] || null)}/></label>{file && <span className="picked-file">{file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB</span>}<button className="button button-primary" disabled={busy}>{busy ? 'Uploading…' : 'Upload privately'}</button></form></section><div className="report-filter-row"><h2>Your uploads</h2><input aria-label="Search reports" placeholder="Search reports" value={query} onChange={(event) => setQuery(event.target.value)}/></div><div className="report-list">{visibleUploads.map((report) => <article className="report-card" key={`upload-${report.id}`}><span className="report-icon"><FileHeart size={20}/></span><div><strong>{report.title}</strong><small>{report.category} · {report.family_member_name || 'Account holder'} · {new Date(`${report.created_at}Z`).toLocaleDateString()}</small><p>{report.original_name}</p></div><div className="report-actions"><button className="icon-button" aria-label={`Preview ${report.title}`} title="Preview" onClick={() => getFile(report)}><Eye size={15}/></button><button className="icon-button" aria-label={`Download ${report.title}`} title="Download" onClick={() => getFile(report, true)}><Download size={15}/></button></div></article>)}{visibleUploads.length === 0 && <div className="empty-state">No uploaded reports match this search.</div>}</div>{shared.length > 0 && <section className="shared-reports"><h2>Clinician-shared records</h2>{shared.map((report) => <article className="report-card" key={`shared-${report.id}`}><span className="report-icon"><FileHeart size={20}/></span><div><strong>{report.title}</strong><small>{new Date(`${report.created_at}Z`).toLocaleDateString()} · approved</small><p>{report.content}</p></div></article>)}</section>}{preview && <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && (URL.revokeObjectURL(preview.url), setPreview(null))}><section className="report-preview-modal" role="dialog" aria-modal="true"><header><strong>{preview.report.title}</strong><button className="icon-button" aria-label="Close preview" onClick={() => { URL.revokeObjectURL(preview.url); setPreview(null); }}><X size={16}/></button></header>{preview.report.mime_type === 'application/pdf' ? <iframe title={preview.report.title} src={preview.url}/> : <img src={preview.url} alt={preview.report.title}/>}</section></div>}</div>;
}
