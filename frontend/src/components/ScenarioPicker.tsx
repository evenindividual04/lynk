import type { Channel, Scenario } from "../types/api";

const SCENARIO_LABELS: Record<Scenario, string> = {
  ps_outreach: "Practice School outreach",
  research_gsoc: "Research / GSoC",
  referral_request: "Referral request",
  info_call: "Informational call",
  alumni: "Alumni outreach",
  founder: "Founder / early-stage",
};

const CHANNEL_LABELS: Record<Channel, string> = {
  li_connection_note: "LI connection note (≤300 chars)",
  li_dm: "LinkedIn DM",
  cold_email: "Cold email",
};

interface Props {
  scenario: Scenario;
  channel: Channel;
  onScenarioChange: (s: Scenario) => void;
  onChannelChange: (c: Channel) => void;
}

export default function ScenarioPicker({ scenario, channel, onScenarioChange, onChannelChange }: Props) {
  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Scenario</label>
        <div className="grid grid-cols-2 gap-2">
          {(Object.keys(SCENARIO_LABELS) as Scenario[]).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onScenarioChange(s)}
              className={`text-left px-3 py-2 rounded border text-sm ${
                scenario === s
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 hover:border-gray-300 text-gray-600"
              }`}
            >
              {SCENARIO_LABELS[s]}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Channel</label>
        <div className="flex gap-2 flex-wrap">
          {(Object.keys(CHANNEL_LABELS) as Channel[]).map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => onChannelChange(c)}
              className={`px-3 py-1.5 rounded border text-sm ${
                channel === c
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 hover:border-gray-300 text-gray-600"
              }`}
            >
              {CHANNEL_LABELS[c]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
