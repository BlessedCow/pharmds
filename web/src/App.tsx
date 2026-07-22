import { useEffect, useState } from "react";

import { fetchMetadata } from "./api/client";
import type { MetadataResponse } from "./api/types";

function App() {
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchMetadata()
      .then(setMetadata)
      .catch((caught: unknown) => {
        const message =
          caught instanceof Error
            ? caught.message
            : "Failed to load PharmDS metadata.";

        setError(message);
      });
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <section className="mx-auto flex max-w-5xl flex-col gap-8">
        <header className="space-y-3">
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-cyan-300">
            PharmDS
          </p>
          <div className="space-y-4">
            <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-white md:text-6xl">
              Medication interaction analysis with timing context.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-300">
              A professional frontend shell for the PharmDS API. The next phase
              will add structured drug input and analysis results.
            </p>
          </div>
        </header>

        <section className="grid gap-4 rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl shadow-slate-950/50 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
            <p className="text-sm font-medium text-slate-400">Backend</p>
            <p className="mt-2 text-2xl font-semibold text-white">
              FastAPI ready
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              The frontend proxies API requests through Vite at /api.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
            <p className="text-sm font-medium text-slate-400">Input model</p>
            <p className="mt-2 text-2xl font-semibold text-white">
              Structured drugs
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              Route and release type can be captured per medication.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
            <p className="text-sm font-medium text-slate-400">PK timing</p>
            <p className="mt-2 text-2xl font-semibold text-white">
              Context aware
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              Half-life, peak timing, and steady-state context are available
              from the API.
            </p>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="flex flex-col gap-2">
            <h2 className="text-xl font-semibold text-white">
              API metadata check
            </h2>
            <p className="text-sm leading-6 text-slate-400">
              This panel confirms the React app can reach the PharmDS API
              metadata endpoint.
            </p>
          </div>

          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950 p-5">
            {error ? (
              <p className="text-sm text-red-300">{error}</p>
            ) : metadata ? (
              <dl className="grid gap-5 md:grid-cols-4">
                <MetadataStat label="Domains" value={metadata.domains.length} />
                <MetadataStat
                  label="Patient flags"
                  value={metadata.patient_flags.length}
                />
                <MetadataStat label="Routes" value={metadata.routes.length} />
                <MetadataStat
                  label="Release types"
                  value={metadata.release_types.length}
                />
              </dl>
            ) : (
              <p className="text-sm text-slate-400">Loading metadata...</p>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function MetadataStat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className="mt-1 text-3xl font-semibold text-cyan-200">{value}</dd>
    </div>
  );
}

export default App;
