import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";

const Plot = createPlotlyComponent(Plotly);

const PHASE_COLORS = {
  Menstrual: "#e53e3e",
  Follicular: "#63b3ed",
  Ovulation: "#9f7aea",
  Luteal: "#ed8936",
  "Pre-menstrual": "#dd6b20",
};

const HEAVY_THRESHOLD = 7;

function BleedingChart({ data, title = "Menstrual Bleeding Pattern (28-day cycle)" }) {
  if (!data?.length) {
    return (
      <div className="bleeding-chart-empty">
        No bleeding data available for this patient.
      </div>
    );
  }

  const days = data.map((point) => point.day);
  const flows = data.map((point) => point.flow);
  const colors = data.map((point) => PHASE_COLORS[point.phase] ?? "#6b21a8");
  const phases = data.map((point) => point.phase);

  return (
    <div className="bleeding-chart">
      <Plot
        className="plotly-chart"
        data={[
          {
            x: days,
            y: flows,
            type: "bar",
            marker: { color: colors, line: { color: "#ffffff", width: 1 } },
            hovertemplate:
              "Day %{x}<br>Flow intensity: %{y}/10<br>Phase: %{customdata}<extra></extra>",
            customdata: phases,
          },
          {
            x: days,
            y: days.map(() => HEAVY_THRESHOLD),
            type: "scatter",
            mode: "lines",
            name: "Heavy threshold",
            line: { color: "#e53e3e", width: 2, dash: "dash" },
            hoverinfo: "skip",
          },
        ]}
        layout={{
          title: { text: title, font: { size: 14, color: "#1e293b" } },
          autosize: true,
          height: 280,
          margin: { t: 44, r: 16, b: 44, l: 44 },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          showlegend: true,
          legend: { orientation: "h", y: -0.24, font: { size: 10 } },
          xaxis: {
            title: "Cycle day",
            dtick: 4,
            range: [0.5, 28.5],
            gridcolor: "#f1f5f9",
          },
          yaxis: {
            title: "Flow",
            range: [0, 10],
            dtick: 2,
            gridcolor: "#f1f5f9",
          },
        }}
        config={{ displayModeBar: false, responsive: true }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
      <p className="chart-caption">
        Interactive Plotly chart. Flow intensity scale 0–10. Days above the dashed line indicate heavy
        bleeding.
      </p>
    </div>
  );
}

export default BleedingChart;
