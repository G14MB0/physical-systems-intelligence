export const demoSystem = {
  id: "DRN-INSPECT-01",
  name: "Inspection Drone 01",
  type: "Quadcopter inspection drone",
  location: "North bridge span",
  status: "Degraded",
};

export const demoSignals = [
  { label: "Battery health", value: "71%", state: "warning" },
  { label: "State of charge", value: "38%", state: "warning" },
  { label: "ESC temperature", value: "82 C", state: "warning" },
  { label: "Motor vibration", value: "5.7 mm/s", state: "warning" },
  { label: "GPS drift", value: "2.4 m", state: "nominal" },
  { label: "Wind speed", value: "9.1 m/s", state: "nominal" },
];

export const demoEvents = [
  {
    code: "E-204",
    severity: "medium",
    message: "Battery voltage sag under climb load.",
  },
  {
    code: "ESC-TEMP-WARN",
    severity: "medium",
    message: "Electronic speed controller temperature exceeded threshold.",
  },
];

export const demoDiagnosis = {
  text:
    "Risk is medium. Current telemetry shows E-204 and ESC-TEMP-WARN; battery health is 71%, ESC temperature is 82 C, and vibration is 5.7 mm/s. Return to launch and create a maintenance ticket before the next inspection.",
  sources: [
    {
      path: "maintenance_manual.md",
      title: "Battery Health and Error E-204",
      excerpt:
        "Error E-204 indicates battery voltage sag under load. When battery health is below 75 percent, end the mission and schedule a battery internal-resistance check.",
    },
    {
      path: "operating_limits.md",
      title: "Mission Continuation Limits",
      excerpt:
        "The drone may continue only when ESC temperature is below 78 C and motor vibration is below 5 mm/s.",
    },
  ],
  actions: [
    "Pause autonomous inspection and return to launch point if safe.",
    "Create a maintenance ticket with telemetry snapshot and event codes.",
    "Inspect ESC cooling path and motor load before next flight.",
  ],
  ticket: {
    id: "PSI-1007",
    title: "Investigate E-204 and ESC temperature warning",
    status: "open",
  },
};
