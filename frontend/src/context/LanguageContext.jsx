import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useAuth } from './AuthContext';

const LanguageContext = createContext(null);
const words = {
  en: { dashboard: 'Overview', doctorProfile: 'Doctor profile', assistant: 'AI health assistant', doctors: 'Find a doctor', hospitals: 'Hospitals & beds', appointments: 'Appointments', family: 'My family', medicines: 'Medicines', patients: 'My patients', messages: 'Messages', consultations: 'Consultation notes', reports: 'Reports', emergencyHelp: 'Emergency help', settings: 'Settings', emergency: 'SOS emergency', logout: 'Sign out', demo: 'Demo mode · simulated data', welcome: 'Care, connected.', subtitle: 'Your health journey, in one calm place.', chat: 'Tell me what is bothering you', patient: 'Patient', doctor: 'Doctor' },
  hi: { dashboard: 'डैशबोर्ड', doctorProfile: 'डॉक्टर प्रोफ़ाइल', assistant: 'AI स्वास्थ्य सहायक', doctors: 'डॉक्टर खोजें', hospitals: 'अस्पताल और बेड', appointments: 'अपॉइंटमेंट', family: 'मेरा परिवार', medicines: 'दवाइयाँ', patients: 'मेरे मरीज़', messages: 'संदेश', consultations: 'परामर्श नोट्स', reports: 'रिपोर्ट', emergencyHelp: 'आपातकालीन सहायता', settings: 'सेटिंग्स', emergency: 'आपातकालीन SOS', logout: 'साइन आउट', demo: 'डेमो मोड · सिम्युलेटेड डेटा', welcome: 'जुड़ी हुई देखभाल।', subtitle: 'आपकी स्वास्थ्य यात्रा, एक ही जगह।', chat: 'बताएं आपको क्या परेशानी है', patient: 'मरीज़', doctor: 'डॉक्टर' },
};
export function LanguageProvider({ children }) {
  const { user, updateLanguage } = useAuth();
  const [language, setLanguage] = useState(user?.language || 'en');
  useEffect(() => { if (user?.language && user.language !== language) setLanguage(user.language); }, [user?.language, language]);
  const value = useMemo(() => ({ language, t: (key) => words[language]?.[key] || words.en[key] || key, setLanguage: (next) => { setLanguage(next); updateLanguage(next); } }), [language, updateLanguage]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}
export function useLanguage() { return useContext(LanguageContext); }
