import { useMemo, useState } from "react";
import AssessmentPanel from "./AssessmentPanel";
import BleedingChart from "./BleedingChart";
import DevicePreview from "./DevicePreview";
import { calculateCycleInfo, formatDisplayDate } from "./cycleUtils";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

const REGIONS = ["Germany", "UK", "USA"];
const CITY_OPTIONS = {
  Germany: [
    "Berlin",
    "Hamburg",
    "Munich",
    "Cologne",
    "Frankfurt",
    "Stuttgart",
    "Dusseldorf",
    "Dresden",
    "Hannover",
    "Bremen",
    "Wiesbaden",
    "Mainz",
    "Potsdam",
    "Kiel",
    "Erfurt",
    "Magdeburg",
    "Saarbrucken",
    "Schwerin",
  ],
  UK: ["London", "Manchester"],
  USA: ["New York", "Los Angeles"],
};
const STRESS_EMOJIS = ["😌", "🙂", "😐", "😟", "😰"];
const ACTION_ICONS = ["🍵", "🚶", "🥦"];

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

const INITIAL_SHIELD = {
  last_period_start: "2026-05-18",
  previous_period_start: "2026-04-19",
  cycle_day: 20,
  stress_level: 4,
  food_log: "",
  vitamin_d_supplement: false,
  region: "Germany",
  city: "Hamburg",
};

const CATEGORY_COLORS = {
  High: { bg: "#fde8e8", border: "#e53e3e", text: "#9b1c1c" },
  Moderate: { bg: "#fef3c7", border: "#d97706", text: "#92400e" },
  Low: { bg: "#d1fae5", border: "#059669", text: "#065f46" },
};

const SHIELD_COLORS = {
  HIGH: { bg: "#fde8e8", border: "#e53e3e", text: "#9b1c1c", bar: "#e53e3e" },
  MEDIUM: { bg: "#fef3c7", border: "#d97706", text: "#92400e", bar: "#d97706" },
  LOW: { bg: "#d1fae5", border: "#059669", text: "#065f46", bar: "#059669" },
};

function WombWiseLogo() {
  return (
    <div className="brand-lockup" aria-label="WombWise">
      <div className="logo-mark" aria-hidden="true">
        <svg viewBox="0 0 64 64" role="img" focusable="false">
          <path
            className="logo-shield"
            d="M32 5l20 8v15c0 14.4-8.3 25.2-20 31-11.7-5.8-20-16.6-20-31V13l20-8z"
          />
          <path
            className="logo-womb"
            d="M20 25c0 8 5.2 14 12 14s12-6 12-14"
          />
          <path
            className="logo-leaf"
            d="M32 38c0-9 5-15 13-17-1 8-6 14-13 17z"
          />
          <path className="logo-stem" d="M32 38c0-7-4-12-10-15" />
        </svg>
      </div>
      <div>
        <span className="brand-name">WombWise</span>
        <span className="brand-tagline">Fibroid prevention shield</span>
      </div>
    </div>
  );
}

function FibroidConcierge() {
  const [activeTab, setActiveTab] = useState("shield");
  const [previewMode, setPreviewMode] = useState("desktop");

  const [form, setForm] = useState(INITIAL_FORM);
  const [region, setRegion] = useState("Germany");
  const [city, setCity] = useState("Berlin");
  const [result, setResult] = useState(null);
  const [flow, setFlow] = useState(null);
  const [bleedingData, setBleedingData] = useState(null);
  const [demoLabel, setDemoLabel] = useState(null);

  const [shieldForm, setShieldForm] = useState(INITIAL_SHIELD);
  const [shieldResult, setShieldResult] = useState(null);
  const [shieldCycleInfo, setShieldCycleInfo] = useState(null);
  const [shieldDemoLabel, setShieldDemoLabel] = useState(null);

  const localCycleInfo = useMemo(
    () =>
      calculateCycleInfo({
        lastPeriodStart: shieldForm.last_period_start,
        previousPeriodStart: shieldForm.previous_period_start,
      }),
    [shieldForm.last_period_start, shieldForm.previous_period_start]
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const updateShieldField = (field, value) => {
    setShieldForm((prev) => ({ ...prev, [field]: value }));
  };

  const updateRegion = (nextRegion) => {
    setRegion(nextRegion);
    setCity(CITY_OPTIONS[nextRegion]?.[0] ?? "");
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

  const analyzeShield = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setShieldResult(null);
    setShieldCycleInfo(null);
    setShieldDemoLabel(null);

    try {
      const payload = {
        ...shieldForm,
        cycle_day: localCycleInfo?.cycle_day ?? shieldForm.cycle_day,
      };

      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Request failed (${res.status})`);
      }

      setShieldResult(await res.json());
      if (localCycleInfo && !localCycleInfo.error) {
        setShieldCycleInfo(localCycleInfo);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadShieldDemo = async () => {
    setLoading(true);
    setError(null);
    setShieldResult(null);
    setShieldCycleInfo(null);
    setShieldDemoLabel(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/shield/demo`);
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Demo load failed (${res.status})`);
      }

      const data = await res.json();
      setShieldForm(data.input);
      setShieldResult(data.result);
      setShieldCycleInfo(data.cycle_info ?? null);
      setShieldDemoLabel(data.label);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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
        body: JSON.stringify({ patient: form, region, city }),
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
      setCity(data.flow?.city ?? "Berlin");
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

  const shieldStyle = shieldResult
    ? SHIELD_COLORS[shieldResult.risk_level] ?? SHIELD_COLORS.LOW
    : null;

  const activeCycleInfo = shieldCycleInfo ?? localCycleInfo;

  const appContent = (
    <>
      <header className="header">
        <div className="header-inner">
          <div className="hero-copy">
            <WombWiseLogo />
            <span className="eyebrow">Fibroid prevention, personalized daily</span>
            <h1>WombWise</h1>
            <p className="subtitle">
              Cycle-based prevention + AI risk calculator · AUC 0.95 model
            </p>
            <div className="hero-pills" aria-label="Core app capabilities">
              <span>Personalized cycle tracking</span>
              <span>Blood marker insights</span>
              <span>Doctolib-ready booking</span>
            </div>
            <div className="preview-toggle" role="group" aria-label="Layout preview">
              <button
                type="button"
                className={`preview-btn ${previewMode === "desktop" ? "preview-active" : ""}`}
                onClick={() => setPreviewMode("desktop")}
              >
                Desktop
              </button>
              <button
                type="button"
                className={`preview-btn ${previewMode === "mobile" ? "preview-active" : ""}`}
                onClick={() => setPreviewMode("mobile")}
              >
                Mobile
              </button>
            </div>
          </div>
          <div className="hero-stats" aria-label="WombWise feature highlights">
            <div>
              <strong>30 sec</strong>
              <span>daily check-in</span>
            </div>
            <div>
              <strong>87%</strong>
              <span>demo risk</span>
            </div>
            <div>
              <strong>2 min</strong>
              <span>voice booking</span>
            </div>
          </div>
        </div>
      </header>

      <nav className="tab-nav">
        <button
          type="button"
          className={`tab-btn ${activeTab === "shield" ? "tab-active" : ""}`}
          onClick={() => setActiveTab("shield")}
        >
          Daily Check-in
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "risk" ? "tab-active" : ""}`}
          onClick={() => setActiveTab("risk")}
        >
          Risk Assessment
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "assessment" ? "tab-active" : ""}`}
          onClick={() => setActiveTab("assessment")}
        >
          Full Assessment
        </button>
      </nav>

      <main className="main">
        {activeTab === "shield" ? (
          <>
            <section className="card form-card">
              <h2>Daily Check-in</h2>
              <p className="card-desc">
                Tell us where you are in your cycle, how stressed you feel, and
                what you ate today — get 3 science-backed micro-actions.
              </p>

              <form onSubmit={analyzeShield}>
                <div className="cycle-tracker-card">
                  <h3>Your cycle</h3>
                  <p className="card-desc">
                    Enter when your last period started and the one before it.
                    WombWise calculates your personal cycle length automatically.
                  </p>
                  <div className="form-grid">
                    <label>
                      Last period started
                      <input
                        type="date"
                        value={shieldForm.last_period_start}
                        onChange={(e) =>
                          updateShieldField("last_period_start", e.target.value)
                        }
                        required
                      />
                    </label>
                    <label>
                      Previous period started
                      <input
                        type="date"
                        value={shieldForm.previous_period_start}
                        onChange={(e) =>
                          updateShieldField("previous_period_start", e.target.value)
                        }
                      />
                    </label>
                  </div>

                  {activeCycleInfo?.error && (
                    <div className="alert alert-error">{activeCycleInfo.error}</div>
                  )}

                  {activeCycleInfo && !activeCycleInfo.error && (
                    <div className="cycle-summary">
                      <div>
                        <span>Cycle length</span>
                        <strong>{activeCycleInfo.cycle_length} days</strong>
                      </div>
                      <div>
                        <span>Today</span>
                        <strong>
                          Day {activeCycleInfo.cycle_day} · {activeCycleInfo.cycle_phase}
                        </strong>
                      </div>
                      <div>
                        <span>Next period</span>
                        <strong>In ~{activeCycleInfo.days_until_next_period} days</strong>
                      </div>
                    </div>
                  )}
                </div>

                <label className="shield-stress-label">
                  Stress level
                  <div className="stress-picker">
                    {STRESS_EMOJIS.map((emoji, i) => (
                      <button
                        key={emoji}
                        type="button"
                        className={`stress-btn ${
                          shieldForm.stress_level === i + 1 ? "stress-active" : ""
                        }`}
                        onClick={() => updateShieldField("stress_level", i + 1)}
                        title={`Stress ${i + 1}/5`}
                      >
                        {emoji}
                      </button>
                    ))}
                  </div>
                </label>

                <label>
                  What did you eat today?
                  <textarea
                    rows={3}
                    value={shieldForm.food_log}
                    onChange={(e) => updateShieldField("food_log", e.target.value)}
                    placeholder="e.g. Coffee, steak with fries, glass of wine…"
                    required
                  />
                </label>

                <label className="checkbox-label vitamin-label">
                  <input
                    type="checkbox"
                    checked={shieldForm.vitamin_d_supplement}
                    onChange={(e) =>
                      updateShieldField("vitamin_d_supplement", e.target.checked)
                    }
                  />
                  Taking Vitamin D supplement today
                </label>

                <div className="form-grid booking-grid">
                  <label className="region-select">
                    Region for specialist booking
                    <select
                      value={shieldForm.region}
                      onChange={(e) => {
                        updateShieldField("region", e.target.value);
                        updateShieldField(
                          "city",
                          CITY_OPTIONS[e.target.value]?.[0] ?? ""
                        );
                      }}
                    >
                      {REGIONS.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="region-select">
                    {shieldForm.region === "Germany"
                      ? "German city for gynecology booking"
                      : "City"}
                    <select
                      value={shieldForm.city}
                      onChange={(e) => updateShieldField("city", e.target.value)}
                    >
                      {(CITY_OPTIONS[shieldForm.region] ?? []).map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="actions">
                  <button type="submit" className="btn-primary" disabled={loading}>
                    {loading ? "Analyzing…" : "Get My WombWise Plan"}
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={loadShieldDemo}
                    disabled={loading}
                  >
                    Load Demo Check-in
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
              <h2>Your WombWise Plan</h2>

              {shieldDemoLabel && (
                <div className="demo-banner">
                  <strong>{shieldDemoLabel}</strong>
                  <span>Luteal phase + stress + red meat scenario</span>
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

              {!shieldResult && !error && (
                <p className="placeholder">
                  Complete your daily check-in or load the demo to see your
                  estrogen risk, 3 micro-actions, and weekly WombWise score.
                </p>
              )}

              {shieldResult && (
                <div className="result">
                  <div
                    className="risk-badge shield-badge"
                    style={{
                      background: shieldStyle.bg,
                      borderColor: shieldStyle.border,
                      color: shieldStyle.text,
                    }}
                  >
                    <span className="risk-percent">{shieldResult.risk_level}</span>
                    <span className="risk-category">
                      {shieldResult.estrogen_risk_label}
                    </span>
                    <span className="cycle-phase">
                      {shieldResult.cycle_phase} phase · Day{" "}
                      {shieldResult.cycle_day} of {shieldResult.cycle_length}
                    </span>
                    {activeCycleInfo?.last_period_start && (
                      <span className="cycle-phase">
                        Last period: {formatDisplayDate(shieldForm.last_period_start)}
                      </span>
                    )}
                  </div>

                  <div className="shield-score-section">
                    <div className="shield-score-header">
                      <span>Weekly WombWise Score</span>
                      <strong>{shieldResult.shield_score}/100</strong>
                    </div>
                    <div className="shield-progress-track">
                      <div
                        className="shield-progress-fill"
                        style={{
                          width: `${shieldResult.shield_score}%`,
                          background: shieldStyle.bar,
                        }}
                      />
                    </div>
                  </div>

                  <p className="shield-explanation">{shieldResult.explanation}</p>

                  <div className="action-cards">
                    <h3>Your 3 Micro-Actions for Today</h3>
                    {shieldResult.three_actions.map((action, i) => (
                      <div key={action} className="action-card">
                        <span className="action-icon">{ACTION_ICONS[i]}</span>
                        <p>{action}</p>
                      </div>
                    ))}
                  </div>

                  {shieldResult.food_analysis && (
                    <div className="food-analysis">
                      <h3>Food Analysis</h3>
                      <p>{shieldResult.food_analysis.assessment}</p>
                      {shieldResult.food_analysis.risk_items?.length > 0 && (
                        <ul className="food-list food-risk">
                          {shieldResult.food_analysis.risk_items.map((item) => (
                            <li key={item.food}>
                              ⚠️ {item.food}: {item.reason}
                            </li>
                          ))}
                        </ul>
                      )}
                      {shieldResult.food_analysis.protective_items?.length > 0 && (
                        <ul className="food-list food-protect">
                          {shieldResult.food_analysis.protective_items.map(
                            (item) => (
                              <li key={item.food}>
                                ✅ {item.food}: {item.reason}
                              </li>
                            )
                          )}
                        </ul>
                      )}
                    </div>
                  )}

                  {shieldResult.appointment_recommendation &&
                    !shieldResult.appointment_recommendation.error && (
                      <div className="appointment-section">
                        <h3>Book a Specialist Now</h3>
                        <p className="shield-explanation">
                          {shieldResult.book_specialist_prompt}
                        </p>
                        <dl className="appointment-details">
                          <div>
                            <dt>Specialist</dt>
                            <dd>{shieldResult.appointment_recommendation.specialist}</dd>
                          </div>
                          <div>
                            <dt>City</dt>
                            <dd>{shieldResult.appointment_recommendation.city}</dd>
                          </div>
                          <div>
                            <dt>Wait time</dt>
                            <dd>{shieldResult.appointment_recommendation.wait_time}</dd>
                          </div>
                          <div>
                            <dt>Provider</dt>
                            <dd>{shieldResult.appointment_recommendation.booking_provider}</dd>
                          </div>
                        </dl>
                        {shieldResult.appointment_recommendation.appointment_options?.length >
                          0 && (
                          <div className="slot-list">
                            <span>Available demo slots</span>
                            <div>
                              {shieldResult.appointment_recommendation.appointment_options.map(
                                (slot) => (
                                  <button key={slot} type="button" className="slot-chip">
                                    {slot}
                                  </button>
                                )
                              )}
                            </div>
                          </div>
                        )}
                        {shieldResult.appointment_recommendation.voicing_script && (
                          <div className="voice-booking-card">
                            <span className="voice-label">Voice booking demo</span>
                            <blockquote className="voicing-script">
                              {shieldResult.appointment_recommendation.voicing_script}
                            </blockquote>
                            <a
                              className="booking-link"
                              href={shieldResult.appointment_recommendation.booking_link}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Open{" "}
                              {shieldResult.appointment_recommendation.booking_provider}
                            </a>
                          </div>
                        )}
                      </div>
                    )}
                </div>
              )}
            </section>
          </>
        ) : activeTab === "assessment" ? (
          <AssessmentPanel />
        ) : (
          <>
            <section className="card form-card">
              <h2>Patient Assessment</h2>
              <p className="card-desc">
                Enter clinical data to estimate fibroid-related risk and clinical
                priority. Includes specialist appointment matching.
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
                    onChange={(e) => updateRegion(e.target.value)}
                  >
                    {REGIONS.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="region-select">
                  {region === "Germany"
                    ? "German city / state capital for gynecology specialist"
                    : "City"}
                  <select
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                  >
                    {(CITY_OPTIONS[region] ?? []).map((option) => (
                      <option key={option} value={option}>
                        {option}
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
                            <dt>Booking</dt>
                            <dd>{flow.appointment.booking_provider}</dd>
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
                      {flow.appointment?.appointment_options?.length > 0 && (
                        <div className="slot-list">
                          <span>Available demo slots</span>
                          <div>
                            {flow.appointment.appointment_options.map((slot) => (
                              <button key={slot} type="button" className="slot-chip">
                                {slot}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      {flow.appointment?.voicing_script && (
                        <div className="voice-booking-card">
                          <span className="voice-label">Voice booking demo</span>
                          <blockquote className="voicing-script">
                            {flow.appointment.voicing_script}
                          </blockquote>
                          <a
                            className="booking-link"
                            href={flow.appointment.booking_link}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Open {flow.appointment.booking_provider}
                          </a>
                        </div>
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
          </>
        )}
      </main>

      <footer className="footer">
        <p>
          For wellness and clinical decision support only. Not a substitute for
          professional medical advice.
        </p>
      </footer>
    </>
  );

  return (
    <div className={`app app-${previewMode}`}>
      <DevicePreview mode={previewMode}>{appContent}</DevicePreview>
    </div>
  );
}

export default FibroidConcierge;
