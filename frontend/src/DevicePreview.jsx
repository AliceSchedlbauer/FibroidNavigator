function DevicePreview({ mode, children }) {
  if (mode === "mobile") {
    return (
      <div className="device-preview-shell">
        <div className="device-preview-label">Mobile preview</div>
        <div className="device-frame device-frame-mobile">
          <div className="device-notch" aria-hidden="true" />
          <div className="device-screen">{children}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="device-preview-shell">
      <div className="device-preview-label">Desktop preview</div>
      <div className="device-frame device-frame-desktop">
        <div className="device-screen">{children}</div>
      </div>
    </div>
  );
}

export default DevicePreview;
