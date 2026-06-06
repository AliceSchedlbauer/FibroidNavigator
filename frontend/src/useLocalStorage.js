import { useEffect, useState } from "react";

export function readStoredValue(key, fallback) {
  if (typeof window === "undefined") {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function writeStoredValue(key, value) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore quota or privacy-mode errors.
  }
}

export function usePersistedState(key, initialValue) {
  const [state, setState] = useState(() => readStoredValue(key, initialValue));

  useEffect(() => {
    writeStoredValue(key, state);
  }, [key, state]);

  return [state, setState];
}
