import {
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  createUserWithEmailAndPassword,
  updateProfile,
} from "firebase/auth";
import { auth } from "./config";

export const login = (email, password) => {
  return signInWithEmailAndPassword(auth, email, password);
};

export const logout = () => {
  return signOut(auth);
};

export const subscribeToAuthChanges = (callback) => {
  return onAuthStateChanged(auth, callback);
};

export const getIdToken = async (forceRefresh = false) => {
  if (typeof auth.authStateReady === "function") {
    await auth.authStateReady();
  }
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken(forceRefresh);
};

export const register = async (email, password, name) => {
  const userCredential = await createUserWithEmailAndPassword(
    auth,
    email,
    password,
  );
  await updateProfile(userCredential.user, {
    displayName: name,
  });
  return userCredential;
};
