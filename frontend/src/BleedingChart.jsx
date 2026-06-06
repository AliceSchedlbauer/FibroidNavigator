import { useEffect, useRef } from "react";

const PHASE_COLORS = {
  Menstrual: "#e53e3e",
  Follicular: "#63b3ed",
  Ovulation: "#9f7aea",
  Luteal: "#ed8936",
  "Pre-menstrual": "#dd6b20",
};

const HEAVY_THRESHOLD = 7;

function BleedingChart({ data, title = "Menstrual Bleeding Pattern (28-day cycle)" }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data?.length) return;

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const padding = { top: 28, right: 16, bottom: 36, left: 44 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    const maxFlow = 10;
    const barWidth = chartW / data.length - 2;

    ctx.clearRect(0, 0, width, height);

    ctx.fillStyle = "#1e293b";
    ctx.font = "600 13px Segoe UI, system-ui, sans-serif";
    ctx.fillText(title, padding.left, 18);

    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, padding.top + chartH);
    ctx.lineTo(padding.left + chartW, padding.top + chartH);
    ctx.stroke();

    for (let i = 0; i <= 5; i++) {
      const y = padding.top + chartH - (i / 5) * chartH;
      ctx.strokeStyle = "#f1f5f9";
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartW, y);
      ctx.stroke();

      ctx.fillStyle = "#94a3b8";
      ctx.font = "11px Segoe UI, system-ui, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(String(i * 2), padding.left - 8, y + 4);
    }

    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "#e53e3e";
    ctx.beginPath();
    const thresholdY =
      padding.top + chartH - (HEAVY_THRESHOLD / maxFlow) * chartH;
    ctx.moveTo(padding.left, thresholdY);
    ctx.lineTo(padding.left + chartW, thresholdY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = "#e53e3e";
    ctx.font = "10px Segoe UI, system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Heavy threshold", padding.left + 4, thresholdY - 4);

    data.forEach((point, index) => {
      const barH = (point.flow / maxFlow) * chartH;
      const x = padding.left + index * (chartW / data.length) + 1;
      const y = padding.top + chartH - barH;
      const color = PHASE_COLORS[point.phase] ?? "#6b21a8";

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barH, [3, 3, 0, 0]);
      ctx.fill();

      if (index % 4 === 0 || index === data.length - 1) {
        ctx.fillStyle = "#64748b";
        ctx.font = "10px Segoe UI, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(String(point.day), x + barWidth / 2, padding.top + chartH + 14);
      }
    });

    const legendX = padding.left;
    const legendY = height - 8;
    let offset = 0;
    ctx.font = "10px Segoe UI, system-ui, sans-serif";
    Object.entries(PHASE_COLORS).forEach(([phase, color]) => {
      ctx.fillStyle = color;
      ctx.fillRect(legendX + offset, legendY - 8, 8, 8);
      ctx.fillStyle = "#64748b";
      ctx.textAlign = "left";
      ctx.fillText(phase, legendX + offset + 12, legendY);
      offset += ctx.measureText(phase).width + 24;
    });
  }, [data, title]);

  if (!data?.length) {
    return (
      <div className="bleeding-chart-empty">
        No bleeding data available for this patient.
      </div>
    );
  }

  return (
    <div className="bleeding-chart">
      <canvas ref={canvasRef} className="bleeding-canvas" />
      <p className="chart-caption">
        Flow intensity scale 0–10. Days above the dashed line indicate heavy
        bleeding.
      </p>
    </div>
  );
}

export default BleedingChart;
