/**
 * Firebase JS SDK initialisation + auth helpers.
 *
 * Required environment variables (set in .env.local):
 *   NEXT_PUBLIC_FIREBASE_API_KEY
 *   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
 *   NEXT_PUBLIC_FIREBASE_PROJECT_ID
 *   NEXT_PUBLIC_FIREBASE_APP_ID
 */

import { initializeApp, getApps } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInAnonymously as _signInAnonymously,
  signOut as _signOut,
  onAuthStateChanged as _onAuthStateChanged,
  type User,
} from "firebase/auth";
import { getFirestore, collection, addDoc, serverTimestamp } from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = process.env.NEXT_PUBLIC_FIREBASE_API_KEY
  ? (getApps().length ? getApps()[0] : initializeApp(firebaseConfig))
  : null;

// auth and db are null during SSR/build (no credentials); only used client-side.
export const auth = app ? getAuth(app) : (null as any);
export const db = app ? getFirestore(app) : (null as any);

export async function signInWithGoogle(): Promise<User> {
  const provider = new GoogleAuthProvider();
  const result = await signInWithPopup(auth, provider);
  return result.user;
}

export async function signOut(): Promise<void> {
  _signInPromise = null;
  if (auth) await _signOut(auth);
}

export async function getIdToken(): Promise<string | null> {
  if (!auth) return null;
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken();
}

export function onAuthStateChanged(callback: (user: User | null) => void): () => void {
  if (!auth) { callback(null); return () => {}; }
  return _onAuthStateChanged(auth, callback);
}

let _signInPromise: Promise<User> | null = null;

/**
 * Ensures the user is signed in. If already signed in (anonymously or with
 * Google), does nothing. Otherwise signs in anonymously.
 */
export async function ensureSignedIn(): Promise<User> {
  if (!auth) throw new Error("Firebase is not configured. Set NEXT_PUBLIC_FIREBASE_* env vars.");
  if (_signInPromise) return _signInPromise;
  _signInPromise = (async () => {
    // Wait for the first auth state event, which signals Firebase has finished
    // restoring the persisted session from IndexedDB/localStorage.
    const resolvedUser = await new Promise<User | null>((resolve) => {
      const unsub = _onAuthStateChanged(auth, (user) => {
        unsub();
        resolve(user);
      });
    });

    if (resolvedUser) return resolvedUser;
    const result = await _signInAnonymously(auth);
    return result.user;
  })();
  return _signInPromise;
}

export type SurveyAnswers = Record<string, number | string>;

export type SurveyPayload = {
  uid: string;
  schema_version: number;
  answers: SurveyAnswers;
};

export async function submitSurvey(payload: SurveyPayload): Promise<void> {
  await addDoc(collection(db, "survey_responses"), {
    ...payload,
    submitted_at: serverTimestamp(),
  });
}
