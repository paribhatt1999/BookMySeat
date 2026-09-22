// Firebase Web SDK configuration and services
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-analytics.js";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  onAuthStateChanged,
  signOut,
} from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyCHEiAIStYdfnOhy0uBjOSF9vuxSDT1vfc",
  authDomain: "bookmyseat-8d477.firebaseapp.com",
  projectId: "bookmyseat-8d477",
  storageBucket: "bookmyseat-8d477.firebasestorage.app",
  messagingSenderId: "998275535843",
  appId: "1:998275535843:web:53f139adf29fd1c61fc6d6",
  measurementId: "G-Q9NGK9ZDKJ",
};

const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export {
  app,
  analytics,
  auth,
  googleProvider,
  signInWithPopup,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  onAuthStateChanged,
  signOut,
};
