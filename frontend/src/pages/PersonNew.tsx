import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { PersonRead } from "../types/api";

interface FormState {
  linkedin_url: string;
  first_name: string;
  last_name: string;
  headline: string;
  email: string;
  current_position_title: string;
}

const EMPTY: FormState = {
  linkedin_url: "",
  first_name: "",
  last_name: "",
  headline: "",
  email: "",
  current_position_title: "",
};

export default function PersonNew() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (data: FormState) =>
      api.post<PersonRead>("/api/people", {
        ...data,
        full_name: `${data.first_name} ${data.last_name}`.trim(),
      }),
    onSuccess: (person) => {
      qc.invalidateQueries({ queryKey: ["people"] });
      navigate(`/people/${person.id}`);
    },
    onError: (err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to create person");
    },
  });

  const handle = (key: keyof FormState) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    mutation.mutate(form);
  };

  return (
    <div className="max-w-lg space-y-4">
      <div className="flex items-center gap-3">
        <Link to="/people" className="text-gray-400 hover:text-gray-600 text-sm">
          ← People
        </Link>
      </div>
      <h1 className="text-xl font-semibold text-gray-900">Add person</h1>

      <form
        onSubmit={submit}
        className="bg-white rounded-lg border border-gray-200 p-6 space-y-4"
      >
        {error && <p className="text-sm text-red-500">{error}</p>}

        {(
          [
            ["linkedin_url", "LinkedIn URL *", "https://www.linkedin.com/in/…"],
            ["first_name", "First name *", ""],
            ["last_name", "Last name *", ""],
            ["headline", "Headline", ""],
            ["email", "Email", ""],
            ["current_position_title", "Current position", ""],
          ] as [keyof FormState, string, string][]
        ).map(([key, label, placeholder]) => (
          <div key={key}>
            <label className="block text-sm text-gray-600 mb-1">{label}</label>
            <input
              type="text"
              value={form[key]}
              onChange={handle(key)}
              placeholder={placeholder}
              className="border rounded px-3 py-2 text-sm w-full"
              required={label.includes("*")}
            />
          </div>
        ))}

        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full bg-indigo-600 text-white py-2 rounded text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {mutation.isPending ? "Saving…" : "Add person"}
        </button>
      </form>
    </div>
  );
}
