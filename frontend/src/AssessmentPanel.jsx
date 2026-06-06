import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

const INITIAL_ASSESSMENT = {
  symptoms: {
    heavy_bleeding: true,
    period_longer_than_7_days: true,
    pad_or_tampon_hourly: false,
    blood_clots: true,
    bleeding_between_periods: false,
    pelvic_pressure: true,
    back_pain: false,
    pain_with_sex: false,
    constipation: false,
    bloated_or_hard_belly: true,
    frequent_urination: true,
    urinary_urgency: false,
    urinary_retention: false,
    chronic_fatigue: true,
    racing_heart: false,
    infertility_or_miscarriage: false,
  },
  profile: {
    african_ancestry: true,
    mother_or_sister_fibroids: true,
    age: 32,
    menarche_before_12: false,
    nulliparity: false,
  },
  lifestyle: {
    bmi: 28.5,
    vitamin_d_low_or_unknown: true,
    hypertension: true,
    chronic_stress: true,
    red_meat_or_alcohol: true,
    low_vegetable_intake: false,
    endocrine_disruptor_exposure: true,
  },
  blood_markers: {
    hemoglobin: 10.8,
    ferritin: 9,
    vitamin_d: 21,
    estrogen_e2: "",
    tsh: "",
    crp: 7.2,
    tyg_index: "",
    systolic_bp: 136,
    diastolic_bp: 86,
  },
};

const SYMPTOM_FIELDS = [
  ["heavy_bleeding", "Heavy or prolonged periods"],
  ["period_longer_than_7_days", "Periods longer than 7 days"],
  ["pad_or_tampon_hourly", "More than 1 pad/tampon per hour"],
  ["blood_clots", "Blood clots"],
  ["bleeding_between_periods", "Bleeding between cycles"],
  ["pelvic_pressure", "Pelvic pressure"],
  ["back_pain", "Back pain"],
  ["pain_with_sex", "Pain with sex"],
  ["constipation", "Constipation"],
  ["bloated_or_hard_belly", "Bloated or hard belly"],
  ["frequent_urination", "Frequent urination"],
  ["urinary_urgency", "Urinary urgency"],
  ["urinary_retention", "Urinary retention"],
  ["chronic_fatigue", "Chronic fatigue"],
  ["racing_heart", "Racing heart"],
  ["infertility_or_miscarriage", "Infertility or repeated miscarriage"],
];

const PROFILE_FIELDS = [
  ["african_ancestry", "African ancestry"],
  ["mother_or_sister_fibroids", "Mother or sister had fibroids"],
  ["menarche_before_12", "First period before age 12"],
  ["nulliparity", "No prior birth"],
];

const LIFESTYLE_FIELDS = [
  ["vitamin_d_low_or_unknown", "Vitamin D low or unknown"],
  ["hypertension", "High blood pressure"],
  ["chronic_stress", "Chronic stress"],
  ["red_meat_or_alcohol", "Frequent red meat or alcohol"],
  ["low_vegetable_intake", "Low vegetable intake"],
  ["endocrine_disruptor_exposure", "Plastic/cosmetic endocrine disruptor exposure"],
];

const BLOOD_FIELDS = [
  ["hemoglobin", "Hemoglobin (Hb)", "g/dl", "< 12 alarm"],
  ["ferritin", "Ferritin", "ng/ml", "< 15 alarm"],
  ["vitamin_d", "Vitamin D", "ng/ml", "< 30 alarm"],
  ["estrogen_e2", "Estrogen E2", "pg/ml", "elevated risk"],
  ["tsh", "TSH", "mIU/L", "abnormal risk"],
  ["crp", "CRP", "mg/l", "> 5 alarm"],
  ["tyg_index", "TyG index", "", "elevated risk"],
  ["systolic_bp", "Systolic BP", "mmHg", "> 130 alarm"],
  ["diastolic_bp", "Diastolic BP", "mmHg", "> 80 alarm"],
];

const LEVEL_COLORS = {
  HIGH: { bg: "#fde8e8", border: "#e53e3e", text: "#9b1c1c", bar: "#e53e3e" },
  MEDIUM: { bg: "#fef3c7", border: "#d97706", text: "#92400e", bar: "#d97706" },
  LOW: { bg: "#d1fae5", border: "#059669", text: "#065f46", bar: "#059669" },
};

function cleanAssessmentPayload(assessment) {
  const bloodMarkers = Object.fromEntries(
    Object.entries(assessment.blood_markers).map(([key, value]) => [
      key,
      value === "" ? null : Number(value),
    ])
  );

  return {
    ...assessment,
    profile: {
      ...assessment.profile,
      age: Number(assessment.profile.age),
    },
    lifestyle: {
      ...assessment.lifestyle,
      bmi: Number(assessment.lifestyle.bmi),
    },
    blood_markers: bloodMarkers,
  };
}

function AssessmentPanel() {
  const [assessment, setAssessment] = useState(INITIAL_ASSESSMENT);
  const [result, setResult] = useState(null);
  const [demoLabel, setDemoLabel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const updateNested = (section, field, value) => {
    setAssessment((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }));
  };

  const submitAssessment = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setDemoLabel(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/assessment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cleanAssessmentPayload(assessment)),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Assessment failed (${res.status})`);
      }
      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadDemo = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/assessment/demo`);
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Demo load failed (${res.status})`);
      }
      const data = await res.json();
      setAssessment(data.input);
      setResult(data.result);
      setDemoLabel(data.label);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const style = result ? LEVEL_COLORS[result.risk_level] ?? LEVEL_COLORS.LOW : null;

  return (
    <>
      <section className="card form-card assessment-form-card">
        <h2>Interactive Assessment</h2>
        <p className="card-desc">
          Three-layer WombWise assessment: one-time profile, daily symptoms and
          modifiable risks, plus optional blood markers.
        </p>

        <form onSubmit={submitAssessment}>
          <div className="assessment-section">
            <h3>1. Symptoms you can feel</h3>
            <div className="assessment-checkbox-grid">
              {SYMPTOM_FIELDS.map(([key, label]) => (
                <label key={key} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={assessment.symptoms[key]}
                    onChange={(e) => updateNested("symptoms", key, e.target.checked)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          <div className="assessment-section">
            <h3>2. One-time profile</h3>
            <label>
              Age
              <input
                type="number"
                min={18}
                max={65}
                value={assessment.profile.age}
                onChange={(e) => updateNested("profile", "age", Number(e.target.value))}
              />
            </label>
            <div className="assessment-checkbox-grid compact">
              {PROFILE_FIELDS.map(([key, label]) => (
                <label key={key} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={assessment.profile[key]}
                    onChange={(e) => updateNested("profile", key, e.target.checked)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          <div className="assessment-section">
            <h3>3. Modifiable daily risks</h3>
            <label>
              BMI
              <input
                type="number"
                min={15}
                max={55}
                step={0.1}
                value={assessment.lifestyle.bmi}
                onChange={(e) => updateNested("lifestyle", "bmi", Number(e.target.value))}
              />
            </label>
            <div className="assessment-checkbox-grid compact">
              {LIFESTYLE_FIELDS.map(([key, label]) => (
                <label key={key} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={assessment.lifestyle[key]}
                    onChange={(e) => updateNested("lifestyle", key, e.target.checked)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          <div className="assessment-section">
            <h3>4. Bring your blood test</h3>
            <div className="blood-grid">
              {BLOOD_FIELDS.map(([key, label, unit, hint]) => (
                <label key={key}>
                  {label}
                  <input
                    type="number"
                    step={0.1}
                    value={assessment.blood_markers[key] ?? ""}
                    onChange={(e) =>
                      updateNested("blood_markers", key, e.target.value)
                    }
                    placeholder={unit}
                  />
                  <span className="field-hint">{hint}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="actions">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Assessing..." : "Run Full Assessment"}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={loadDemo}
              disabled={loading}
            >
              Load Full Demo
            </button>
          </div>
        </form>
      </section>

      <section className="card result-card">
        <h2>Assessment Result</h2>

        {demoLabel && (
          <div className="demo-banner">
            <strong>{demoLabel}</strong>
            <span>Symptoms + profile + lifestyle + blood markers</span>
          </div>
        )}

        {error && (
          <div className="alert alert-error">
            <strong>Error:</strong> {error}
            <p className="hint">
              Make sure the backend is running: <code>python api.py</code>
            </p>
          </div>
        )}

        {!result && !error && (
          <p className="placeholder">
            Complete the assessment to see your explainable WombWise risk level,
            Shield Score, category drivers and recommended next actions.
          </p>
        )}

        {result && (
          <div className="result">
            <div
              className="risk-badge shield-badge"
              style={{
                background: style.bg,
                borderColor: style.border,
                color: style.text,
              }}
            >
              <span className="risk-percent">{result.risk_level}</span>
              <span className="risk-category">
                Assessment Score: {result.assessment_score}/100
              </span>
              <span className="cycle-phase">
                WombWise Shield Score: {result.shield_score}/100
              </span>
            </div>

            <div className="category-score-grid">
              {Object.entries(result.category_scores).map(([key, value]) => (
                <div key={key} className="category-score-card">
                  <span>{key.replace("_", " ")}</span>
                  <strong>{value}/100</strong>
                  <div className="mini-progress">
                    <div style={{ width: `${value}%`, background: style.bar }} />
                  </div>
                </div>
              ))}
            </div>

            <p className="shield-explanation">{result.explanation}</p>

            {result.urgent_flags.length > 0 && (
              <div className="urgent-card">
                <h3>Urgent Flags</h3>
                <ul>
                  {result.urgent_flags.map((flag) => (
                    <li key={flag}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="food-analysis">
              <h3>Key Drivers</h3>
              <ul className="food-list">
                {result.key_drivers.map((driver) => (
                  <li key={driver}>{driver}</li>
                ))}
              </ul>
            </div>

            <div className="action-cards">
              <h3>Recommended Actions</h3>
              {result.recommended_actions.map((action, index) => (
                <div key={action} className="action-card">
                  <span className="action-icon">{index + 1}</span>
                  <p>{action}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </>
  );
}

export default AssessmentPanel;
