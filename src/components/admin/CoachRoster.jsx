import { useEffect, useState } from "react";
import { getAdminCoaches, patchAdminCoach } from "../../api/backend";

export function CoachRoster() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(null);

  const load = () =>
    getAdminCoaches()
      .then(setRows)
      .catch((err) => setError(err.message || "Failed to load coaches"));

  useEffect(() => {
    load();
  }, []);

  const toggleAdmin = async (row) => {
    setBusy(row.id);
    try {
      await patchAdminCoach(row.id, { is_admin: !row.is_admin });
      await load();
    } catch (err) {
      setError(err.message || "Update failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-1">Coaches</h2>
        <p className="text-sm text-zinc-400">Promote coaches to admin or revoke access.</p>
      </div>
      {error && <p className="text-red-300 text-sm">{error}</p>}
      <div className="overflow-x-auto rounded-2xl border border-white/8">
        <table className="w-full text-sm text-left">
          <thead className="text-xs uppercase tracking-widest text-zinc-500 bg-white/3">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Students</th>
              <th className="px-4 py-3">Admin</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-white/5">
                <td className="px-4 py-3">{row.name || "—"}</td>
                <td className="px-4 py-3 text-zinc-400">{row.email || "—"}</td>
                <td className="px-4 py-3">{row.student_count}</td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    disabled={busy === row.id}
                    onClick={() => toggleAdmin(row)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                      row.is_admin
                        ? "bg-lime-400/20 text-lime-300"
                        : "bg-white/5 text-zinc-500 hover:text-white"
                    }`}
                  >
                    {busy === row.id ? "…" : row.is_admin ? "Admin" : "Coach"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
