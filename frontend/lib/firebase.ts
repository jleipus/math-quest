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

const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

export async function signInWithGoogle(): Promise<User> {
  const provider = new GoogleAuthProvider();
  const result = await signInWithPopup(auth, provider);
  return result.user;
}

export async function signOut(): Promise<void> {
  await _signOut(auth);
}

export async function getIdToken(): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken();
}

export function onAuthStateChanged(callback: (user: User | null) => void): () => void {
  return _onAuthStateChanged(auth, callback);
}

/**
 * Ensures the user is signed in. If already signed in (anonymously or with
 * Google), does nothing. Otherwise signs in anonymously so we always have a
 * stable UID for survey correlation and user model tracking.
 */
export async function ensureSignedIn(): Promise<User> {
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
}

export type SurveyAnswers = Record<string, number>;

export type SurveyPayload = {
  answers: SurveyAnswers;
  schema_version: number;

  // Performance context
  grade: string;
  floor: number;
  turn: number;
  cards_played: number;
  help_requests: number;

  // Auth context
  uid: string | null;
  is_anonymous: boolean;
};

export async function submitSurvey(payload: SurveyPayload): Promise<void> {
  await addDoc(collection(db, "survey_responses"), {
    ...payload,
    submitted_at: serverTimestamp(),
  });
}
