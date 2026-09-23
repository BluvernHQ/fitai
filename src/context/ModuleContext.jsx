import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useAuth } from "./authContext";
import { getMe, getModules } from "../api/backend";
import { MODULE_REGISTRY, REGISTRY_BY_ID, navigableModules } from "../modules/registry";

const ModuleContext = createContext(null);

export function ModuleProvider({ children }) {
  const { user } = useAuth();
  const [coach, setCoach] = useState(null);
  const [remoteModules, setRemoteModules] = useState([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!user) {
      setCoach(null);
      setRemoteModules([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [me, modPayload] = await Promise.all([getMe(), getModules()]);
      setCoach(me);
      setRemoteModules(modPayload?.modules || []);
    } catch (err) {
      console.error("ModuleProvider load failed", err);
      setRemoteModules([]);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const modules = useMemo(() => {
    const byId = Object.fromEntries(remoteModules.map((m) => [m.id, m]));
    return MODULE_REGISTRY.map((spec) => {
      const remote = byId[spec.id];
      return {
        ...spec,
        enabled: remote ? remote.enabled : true,
        version: remote?.version || "1.0.0",
        config: remote?.config || {},
      };
    });
  }, [remoteModules]);

  const isAdmin = Boolean(coach?.is_admin);
  const coachNav = useMemo(() => navigableModules(modules, { admin: false }), [modules]);
  const adminNav = useMemo(() => navigableModules(modules, { admin: true }), [modules, isAdmin]);

  const isEnabled = useCallback(
    (id) => modules.find((m) => m.id === id)?.enabled ?? false,
    [modules],
  );

  const getModule = useCallback((id) => modules.find((m) => m.id === id) || REGISTRY_BY_ID[id], [modules]);

  return (
    <ModuleContext.Provider
      value={{
        coach,
        modules,
        loading,
        isAdmin,
        isEnabled,
        getModule,
        coachNav,
        adminNav,
        refresh,
      }}
    >
      {children}
    </ModuleContext.Provider>
  );
}

export function useModules() {
  const ctx = useContext(ModuleContext);
  if (!ctx) throw new Error("useModules must be used within ModuleProvider");
  return ctx;
}
