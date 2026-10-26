// Konfiguracja dashboardu. Parametry testowe w adresie: ?data=<url-katalogu-danych>  ?nofb=1 (bez Firebase).
export const REPO = { owner: 'miszyszka', name: 'IA5', dataBranch: 'data' };
export const FIREBASE_SDK = 'https://www.gstatic.com/firebasejs/10.14.1';
export const firebaseConfig = {
  apiKey: 'AIzaSyC9_cgFy2GykfR-2SMkg8ytulxCNl-IANE', // publiczny z natury (S3) — chronią go reguły i ograniczenie do domeny
  authDomain: 'project-ia5.firebaseapp.com',
  projectId: 'project-ia5',
  storageBucket: 'project-ia5.firebasestorage.app',
  messagingSenderId: '709647016808',
  appId: '1:709647016808:web:ebc00f88dcfc626215ecdd',
};
const q = new URLSearchParams(location.search);
export const DATA_OVERRIDE = q.get('data');
export const NO_FIREBASE = q.has('nofb');
export const HEARTBEAT_OK_S = 90;
