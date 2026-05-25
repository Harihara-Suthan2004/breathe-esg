import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, Lock, RefreshCw, BarChart3, Building } from 'lucide-react';

export default function App() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterStatus, setFilterStatus] = useState('ALL');

  // Fetch normalized data rows from our Django API REST endpoint
  const fetchRecords = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/records/');
      if (!response.ok) throw new Error('Failed to communicate with ESG backend services.');
      const data = await response.json();
      setRecords(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  // Custom API trigger action to trigger a record-lock sequence inside the database via Django actions
  const handleLockRecord = async (id) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/records/${id}/lock_record/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        // Instantly reload local state to mirror database locks
        fetchRecords();
      }
    } catch (err) {
      alert("Error processing audit freeze request.");
    }
  };

  // Compute live analytical dashboard card summaries
  const totalEmissions = records.reduce((sum, r) => sum + parseFloat(r.co2e_emissions_mt || 0), 0);
  const suspiciousCount = records.filter(r => r.status === 'SUSPICIOUS').length;
  const pendingCount = records.filter(r => r.status === 'PENDING').length;

  const filteredRecords = records.filter(r => filterStatus === 'ALL' || r.status === filterStatus);

  if (loading) return (
    <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
      <div className="text-center">
        <RefreshCw className="mx-auto h-10 w-10 animate-spin text-emerald-600" />
        <p className="mt-4 text-slate-600 font-medium">Syncing with carbon ledger database...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Top Main Navigation Header */}
      <header className="border-b border-slate-200 bg-white px-8 py-5 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-emerald-600 p-2 text-white shadow-md">
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900">Breathe ESG</h1>
              <p className="text-xs font-medium text-slate-500">Enterprise Carbon Accounting & Data Audit Platform</p>
            </div>
          </div>
          <button 
            onClick={fetchRecords} 
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 shadow-sm transition"
          >
            <RefreshCw className="h-4 w-4" /> Refresh Ledger
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl p-8">
        {/* Error Flag Alert */}
        {error && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700 shadow-sm flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-600" /> {error}
          </div>
        )}

        {/* High-Level Executive Metric Aggregate Cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3 mb-8">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Aggregate Footprint</p>
              <h3 className="mt-2 text-3xl font-black text-slate-900">{totalEmissions.toFixed(3)} <span className="text-sm font-semibold text-slate-500">MT CO₂e</span></h3>
            </div>
            <div className="rounded-xl bg-emerald-50 p-4 text-emerald-600"><BarChart3 className="h-6 w-6" /></div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Suspicious Anomalies</p>
              <h3 className="mt-2 text-3xl font-black text-amber-600">{suspiciousCount} <span className="text-sm font-semibold text-slate-500">Records</span></h3>
            </div>
            <div className="rounded-xl bg-amber-50 p-4 text-amber-600"><AlertTriangle className="h-6 w-6" /></div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Awaiting Validation</p>
              <h3 className="mt-2 text-3xl font-black text-blue-600">{pendingCount} <span className="text-sm font-semibold text-slate-500">Pending</span></h3>
            </div>
            <div className="rounded-xl bg-blue-50 p-4 text-blue-600"><CheckCircle className="h-6 w-6" /></div>
          </div>
        </div>

        {/* Filter Toolbar System */}
        <div className="mb-6 flex items-center gap-2 border-b border-slate-200 pb-4">
          {['ALL', 'PENDING', 'SUSPICIOUS', 'APPROVED'].map((statusOption) => (
            <button
              key={statusOption}
              onClick={() => setFilterStatus(statusOption)}
              className={`rounded-lg px-4 py-2 text-xs font-bold uppercase tracking-wider transition ${
                filterStatus === statusOption 
                  ? 'bg-slate-900 text-white shadow-sm' 
                  : 'bg-transparent text-slate-500 hover:bg-slate-100 hover:text-slate-800'
              }`}
            >
              {statusOption}
            </button>
          ))}
        </div>

        {/* Core Consolidated Unified Emission Ledger Table */}
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-500">
                <th className="px-6 py-4">Source Platform</th>
                <th className="px-6 py-4">Scope Classification</th>
                <th className="px-6 py-4">Asset Label / Category</th>
                <th className="px-6 py-4 text-right">Inflow Quantity</th>
                <th className="px-6 py-4 text-right">Calculated Footprint</th>
                <th className="px-6 py-4 text-center">Audit Status</th>
                <th className="px-6 py-4 text-right">Governance Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm font-medium text-slate-700">
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-slate-400 font-medium">No records match the current filter state.</td>
                </tr>
              ) : (
                filteredRecords.map((record) => (
                  <tr key={record.id} className="hover:bg-slate-50/70 transition">
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-2 font-bold text-slate-900">
                        <Building className="h-4 w-4 text-slate-400" />
                        {record.source_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold border ${
                        record.ghg_scope === 'SCOPE_1' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                        record.ghg_scope === 'SCOPE_2' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                        'bg-teal-50 text-teal-700 border-teal-200'
                      }`}>
                        {record.ghg_scope}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-semibold text-slate-800">{record.category_label}</div>
                        <div className="text-xs text-slate-400 font-normal">{record.start_date} to {record.end_date}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-slate-600">
                      {parseFloat(record.original_quantity).toLocaleString()} <span className="text-xs font-sans font-semibold text-slate-400">{record.original_unit}</span>
                    </td>
                    <td className="px-6 py-4 text-right font-mono font-bold text-slate-900">
                      {parseFloat(record.co2e_emissions_mt).toFixed(4)} <span className="text-xs font-sans font-semibold text-slate-400">MT</span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold ${
                          record.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700' :
                          record.status === 'SUSPICIOUS' ? 'bg-amber-50 text-amber-700' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          {record.status === 'APPROVED' && <CheckCircle className="h-3.5 w-3.5" />}
                          {record.status === 'SUSPICIOUS' && <AlertTriangle className="h-3.5 w-3.5" />}
                          {record.status}
                        </span>
                        {record.analyst_notes && (
                          <span className="mt-1 max-w-[200px] text-[11px] font-normal leading-tight text-amber-600 text-center">
                            {record.analyst_notes}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {record.is_locked ? (
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-400 bg-slate-50 px-2.5 py-1 rounded border border-slate-200/60 shadow-sm">
                          <Lock className="h-3.5 w-3.5 text-slate-400" /> Locked (Audit Safe)
                        </span>
                      ) : (
                        <button
                          onClick={() => handleLockRecord(record.id)}
                          className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 transition"
                        >
                          Approve & Freeze
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}