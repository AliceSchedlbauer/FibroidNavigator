import { useState } from "react";
import BleedingChart from "./BleedingChart";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

const REGIONS = ["Germany", "UK", "USA"];

const INITIAL_FORM = {
  age: 42,
  bmi: 29.5,
  family_history: true,
  heavy_bleeding: true,
  pelvic_pain_severity: 7,
  anemia: true,
  fibroid_count: 3,
  largest_fibroid_cm: 6.2,
  african_ancestry: true,
  nulliparity: false,
};

const CATEGORY_COLORS = {
  High: { bg: "#fde8e8", border: "#e53e3e", text: "#9b1c1c" },
  Moderate: { bg: "#fef3c7", border: "#d97706", text: "#92400e" },
  Low: { bg: "#d1fae5", border: "#059669", text: "#065f46" },
};

function FibroidConcierge() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [region, setRegion] = useState("Germany");
  const [result, setResult] = useState(null);
  const [flow, setFlow] = useState(null);
  const [bleedingData, setBleedingData] = useState(null);
  const [demoLabel, setDemoLabel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (!res.ok) throw new Error(`Health check failed (${res.status})`);
      const data = await res.json();
      setApiStatus(data);
      setError(null);
    } catch (err) {
      setApiStatus(null);
      setError(err.message);
    }
  };

  const calculateRisk = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setFlow(null);
    setBleedingData(null);
    setDemoLabel(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/flow`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient: form, region }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Request failed (${res.status})`);
      }

      const data = await res.json();
      setFlow(data);
      setResult({
        risk_percent: data.risk.risk_percent,
        risk_score: data.risk.risk_score,
        risk_category: data.risk.risk_category,
        priority: data.risk.priority,
        recommendation: data.risk.recommendation,
        model_auc: data.risk.model_auc,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadDemoPatient = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setFlow(null);
    setBleedingData(null);
    setDemoLabel(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/demo`);
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Demo load failed (${res.status})`);
      }

      const data = await res.json();
      setForm(data.patient);
      setRegion("Germany");
      setResult(data.risk);
      setFlow(data.flow ?? null);
      setBleedingData(data.bleeding_chart);
      setDemoLabel(data.label);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const categoryStyle = result
    ? CATEGORY_COLORS[result.risk_category] ?? CATEGORY_COLORS.Low
    : null;

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <h1>Fibroid Navigator</h1>
          <p className="subtitle">AI Risk Calculator · AUC 0.95 Model</p>
        </div>
      </header>

      <main className="main">
        <section className="card form-card">
          <h2>Patient Assessment</h2>
          <p className="card-desc">
            Enter clinical data to estimate fibroid-related risk and clinical
            priority.
          </p>

          <form onSubmit={calculateRisk}>
            <div className="form-grid">
              <label>
                Age (years)
                <input
                  type="number"
                  min={18}
                  max={65}
                  value={form.age}
                  onChange={(e) => updateField("age", Number(e.target.value))}
                  required
                />
              </label>

              <label>
                BMI
                <input
                  type="number"
                  min={15}
                  max={50}
                  step={0.1}
                  value={form.bmi}
                  onChange={(e) => updateField("bmi", Number(e.target.value))}
                  required
                />
              </label>

              <label>
                Pelvic pain severity (0–10)
                <input
                  type="range"
                  min={0}
                  max={10}
                  value={form.pelvic_pain_severity}
                  onChange={(e) =>
                    updateField("pelvic_pain_severity", Number(e.target.value))
                  }
                />
                <span className="range-value">{form.pelvic_pain_severity}</span>
              </label>

              <label>
                Fibroid count
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={form.fibroid_count}
                  onChange={(e) =>
                    updateField("fibroid_count", Number(e.target.value))
                  }
                  required
                />
              </label>

              <label>
                Largest fibroid (cm)
                <input
                  type="number"
                  min={0}
                  max={25}
                  step={0.1}
                  value={form.largest_fibroid_cm}
                  onChange={(e) =>
                    updateField("largest_fibroid_cm", Number(e.target.value))
                  }
                  required
                />
              </label>
            </div>

            <label className="region-select">
              Region
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              >
                {REGIONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </label>

            <fieldset className="checkbox-group">
              <legend>Clinical factors</legend>
              {[
                ["family_history", "Family history of fibroids"],
                ["heavy_bleeding", "Heavy or prolonged bleeding"],
                ["anemia", "Diagnosed anemia"],
                ["african_ancestry", "African ancestry"],
                ["nulliparity", "Nulliparity (no prior birth)"],
              ].map(([key, label]) => (
                <label key={key} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={form[key]}
                    onChange={(e) => updateField(key, e.target.checked)}
                  />
                  {label}
                </label>
              ))}
            </fieldset>

            <div className="actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Calculating…" : "Calculate Risk"}
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={loadDemoPatient}
                disabled={loading}
              >
                Load Demo Patient
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={checkHealth}
              >
                Check API
              </button>
            </div>
          </form>
        </section>

        <section className="card result-card">
          <h2>Risk Assessment</h2>

          {demoLabel && (
            <div className="demo-banner">
              <strong>{demoLabel}</strong>
              <span>87% risk · showcase case with bleeding chart</span>
            </div>
          )}

          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
              <p className="hint">
                Make sure the backend is running:{" "}
                <code>python api.py</code>
              </p>
            </div>
          )}

          {apiStatus && (
            <div className="alert alert-ok">
              API online · Model AUC: {apiStatus.model_auc}
            </div>
          )}

          {!result && !error && (
            <p className="placeholder">
              Submit patient data or load the demo patient to see risk score,
              category, and clinical recommendation.
            </p>
          )}

          {result && (
            <div className="result">
              <div
                className="risk-badge"
                style={{
                  background: categoryStyle.bg,
                  borderColor: categoryStyle.border,
                  color: categoryStyle.text,
                }}
              >
                <span className="risk-percent">{result.risk_percent}%</span>
                <span className="risk-category">{result.risk_category} Risk</span>
              </div>

              <dl className="result-details">
                <div>
                  <dt>Priority</dt>
                  <dd>{result.priority}</dd>
                </div>
                <div>
                  <dt>Risk score</dt>
                  <dd>{result.risk_score}</dd>
                </div>
                <div>
                  <dt>Model AUC</dt>
                  <dd>{result.model_auc}</dd>
                </div>
              </dl>

              <div className="recommendation">
                <h3>Recommendation</h3>
                <p>{result.recommendation}</p>
              </div>

              {flow && (
                <div className="appointment-section">
                  <h3>Specialist Appointment</h3>
                  {flow.appointment?.error ? (
                    <p className="appointment-error">{flow.appointment.error}</p>
                  ) : (
                    <dl className="appointment-details">
                      <div>
                        <dt>Specialist</dt>
                        <dd>{flow.appointment.specialist}</dd>
                      </div>
                      <div>
                        <dt>City</dt>
                        <dd>{flow.appointment.city}</dd>
                      </div>
                      <div>
                        <dt>Specialty</dt>
                        <dd>{flow.appointment.specialty}</dd>
                      </div>
                      <div>
                        <dt>Wait time</dt>
                        <dd>{flow.appointment.wait_time}</dd>
                      </div>
                      <div>
                        <dt>Priority</dt>
                        <dd>{flow.appointment.priority}</dd>
                      </div>
                    </dl>
                  )}
                  {flow.appointment?.voicing_script && (
                    <blockquote className="voicing-script">
                      {flow.appointment.voicing_script}
                    </blockquote>
                  )}
                  <p className="combined-action">
                    <strong>Next step:</strong> {flow.action}
                  </p>
                </div>
              )}

              {bleedingData && (
                <div className="bleeding-section">
                  <h3>Bleeding Pattern</h3>
                  <BleedingChart data={bleedingData} />
                </div>
              )}
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        <p>
          For clinical decision support only. Not a substitute for professional
          medical advice.
        </p>
      </footer>
    </div>
  );
}

export default FibroidConcierge;
