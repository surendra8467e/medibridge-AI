const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api').replace(/\/$/, '');

async function request(path, options = {}) {
  const token = sessionStorage.getItem(path.startsWith('/admin/') ? 'medibridge_admin_token' : 'medibridge_token');
  const isFormData = options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

const json = (method, body) => ({ method, body: JSON.stringify(body) });
export const api = {
  health: () => request('/health'),
  login: (body) => request('/auth/login', json('POST', body)),
  adminLogin: (body) => request('/admin/login', json('POST', body)),
  register: (body) => request('/auth/register', json('POST', body)),
  me: () => request('/auth/me'),
  adminMe: () => request('/admin/me'),
  logout: () => request('/auth/logout', json('POST', {})),
  language: (language) => request('/auth/language', json('PATCH', { language })),
  doctors: () => request('/doctors'),
  messageDoctors: () => request('/patients/me/doctors'),
  doctorProfile: () => request('/doctors/me'),
  adminDoctors: () => request('/admin/doctors'),
  setDoctorVerification: (id, status, note) => request(`/admin/doctors/${id}/verification`, json('PATCH', { status, note })),
  verificationEvents: (id) => request(`/admin/doctors/${id}/verification-events`),
  patients: () => request('/doctors/patients/assigned'),
  patient: (id) => request(`/patients/${id}`),
  profile: () => request('/patients/me'),
  saveProfile: (history) => request('/patients/me', json('PUT', { history })),
  sessions: () => request('/chat/sessions'),
  newSession: () => request('/chat/sessions', json('POST', {})),
  chatMessages: (id) => request(`/chat/sessions/${id}/messages`),
  sendChat: (id, content) => request(`/chat/sessions/${id}/messages`, json('POST', { content })),
  appointments: () => request('/appointments'),
  book: (body) => request('/appointments', json('POST', body)),
  updateAppointment: (id, status) => request(`/appointments/${id}`, json('PATCH', { status })),
  cancelAppointment: (id) => request(`/appointments/${id}/cancel`, json('POST', {})),
  videoRoom: (id) => request(`/appointments/${id}/video-room`),
  messages: (patientId, doctorId) => request(`/patients/${patientId}/messages${doctorId ? `?doctor_id=${doctorId}` : ''}`),
  sendMessage: (patientId, body) => request(`/patients/${patientId}/messages`, json('POST', body)),
  consultations: () => request('/consultations'),
  saveConsultation: (body) => request('/consultations', json('POST', body)),
  approveConsultation: (id) => request(`/consultations/${id}/approve`, json('POST', {})),
  reports: () => request('/reports'),
  hospitals: () => request('/hospitals'),
  bedRequest: (id, note) => request(`/hospitals/${id}/requests`, json('POST', { note })),
  bedRequests: () => request('/hospitals/requests'),
  updateBeds: (id, available) => request(`/hospitals/${id}/beds`, json('PATCH', { available })),
  family: () => request('/family'),
  addFamilyMember: (body) => request('/family', json('POST', body)),
  updateFamilyMember: (id, body) => request(`/family/${id}`, json('PUT', body)),
  deleteFamilyMember: (id) => request(`/family/${id}`, { method: 'DELETE' }),
  medicines: (patientId) => request(`/medicines${patientId ? `?patient_id=${patientId}` : ''}`),
  addMedicine: (body) => request('/medicines', json('POST', body)),
  createPrescription: (body) => request('/medicines/prescriptions', json('POST', body)),
  setMedicineActive: (id, active) => request(`/medicines/${id}`, json('PATCH', { active })),
  markMedicineTaken: (id) => request(`/medicines/${id}/taken`, json('POST', {})),
  uploads: () => request('/reports/uploads'),
  uploadReport: (formData) => request('/reports/uploads', { method: 'POST', body: formData }),
  reportFile: async (id) => {
    const token = sessionStorage.getItem('medibridge_token');
    const response = await fetch(`${API_URL}/reports/uploads/${id}/file`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!response.ok) throw new Error('Report is unavailable or inaccessible.');
    return response.blob();
  },
  bedBookings: () => request('/hospitals/bookings'),
  createBedBooking: (body) => request('/hospitals/bookings', json('POST', body)),
  cancelBedBooking: (reference) => request(`/hospitals/bookings/${encodeURIComponent(reference)}`, json('PATCH', {})),
};
