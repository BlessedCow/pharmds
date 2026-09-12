import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import { analyzeDrugs, fetchMetadata } from "./api/client";
import type { AnalyzeResponse, MetadataResponse } from "./api/types";

type DrugFormState = {
  name: string;
  route: string;
  releaseType: string;
};

const DEFAULT_DRUGS: DrugFormState[] = [
  {
    name: "propranolol",
    route: "oral",
    releaseType: "er",
  },
  {
    name: "vortioxetine",
    route: "oral",
    releaseType: "ir",
  },
];

const EMPTY_DRUG: DrugFormState = {
  name: "",
  route: "oral",
  releaseType: "ir",
};

function App() {
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [drugs, setDrugs] = useState<DrugFormState[]>(DEFAULT_DRUGS);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    void fetchMetadata()
      .then(setMetadata)
      .catch((caught: unknown) => {
        const message =
          caught instanceof Error
            ? caught.message
            : "Failed to load PharmDS metadata.";

        setMetadataError(message);
      });
  }, []);

  const canSubmit = useMemo(
    () =>
      drugs.length >= 2 && drugs.every((drug) => drug.name.trim().length > 0),
    [drugs],
  );

  function updateDrug(index: number, nextDrug: DrugFormState) {
    setDrugs((currentDrugs) =>
      currentDrugs.map((drug, currentIndex) =>
        currentIndex === index ? nextDrug : drug,
      ),
    );
  }

  function addDrug() {
    setDrugs((currentDrugs) => [...currentDrugs, { ...EMPTY_DRUG }]);
  }

  function removeDrug(index: number) {
    setDrugs((currentDrugs) => {
      if (currentDrugs.length <= 2) {
        return currentDrugs;
      }

      return currentDrugs.filter((_, currentIndex) => currentIndex !== index);
    });
  }

  async function handleAnalyze() {
    setAnalysis(null);
    setAnalysisError(null);
    setIsAnalyzing(true);

    try {
      const result = await analyzeDrugs({
        drugs: drugs.map((drug) => ({
          name: drug.name.trim(),
          route: drug.route || null,
          release_type: drug.releaseType || null,
        })),
        domain: "all",
        qt_risk: false,
        bleeding_risk: false,
      });

      setAnalysis(result);
    } catch (caught: unknown) {
      const message =
        caught instanceof Error
          ? caught.message
          : "Failed to analyze medications.";

      setAnalysisError(message);
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <section className="mx-auto flex max-w-7xl flex-col gap-8">
        <header className="space-y-3">
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-cyan-300">
            PharmDS
          </p>

          <div className="space-y-4">
            <h1 className="max-w-4xl text-4xl font-bold tracking-tight text-white md:text-6xl">
              Medication interaction analysis with timing context.
            </h1>

            <p className="max-w-3xl text-lg leading-8 text-slate-300">
              Analyze medication combinations with structured interaction,
              mechanism, and pharmacokinetic timing context.
            </p>
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
          <AnalyzeForm
            canSubmit={canSubmit}
            drugs={drugs}
            isAnalyzing={isAnalyzing}
            metadata={metadata}
            metadataError={metadataError}
            onAddDrug={addDrug}
            onAnalyze={() => {
              void handleAnalyze();
            }}
            onRemoveDrug={removeDrug}
            onUpdateDrug={updateDrug}
          />

          <ResultsPanel analysis={analysis} error={analysisError} />
        </section>
      </section>
    </main>
  );
}

function AnalyzeForm({
  canSubmit,
  drugs,
  isAnalyzing,
  metadata,
  metadataError,
  onAddDrug,
  onAnalyze,
  onRemoveDrug,
  onUpdateDrug,
}: {
  canSubmit: boolean;
  drugs: DrugFormState[];
  isAnalyzing: boolean;
  metadata: MetadataResponse | null;
  metadataError: string | null;
  onAddDrug: () => void;
  onAnalyze: () => void;
  onRemoveDrug: (index: number) => void;
  onUpdateDrug: (index: number, drug: DrugFormState) => void;
}) {
  return (
    <section className="h-fit rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-slate-950/50">
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold text-white">Medications</h2>
        <p className="text-sm leading-6 text-slate-400">
          Enter each medication with its route and release type.
        </p>
      </div>

      {metadataError ? <ErrorBanner message={metadataError} /> : null}

      <div className="mt-6 space-y-4">
        {drugs.map((drug, index) => (
          <DrugInputCard
            canRemove={drugs.length > 2}
            drug={drug}
            index={index}
            key={index}
            metadata={metadata}
            onChange={(nextDrug) => onUpdateDrug(index, nextDrug)}
            onRemove={() => onRemoveDrug(index)}
          />
        ))}
      </div>

      <button
        className="mt-4 w-full rounded-2xl border border-slate-700 bg-slate-950 px-5 py-3 text-sm font-semibold text-slate-300 transition hover:border-cyan-300 hover:text-cyan-200"
        onClick={onAddDrug}
        type="button"
      >
        Add medication
      </button>

      <button
        className="mt-4 w-full rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
        disabled={!canSubmit || isAnalyzing}
        onClick={onAnalyze}
        type="button"
      >
        {isAnalyzing ? "Analyzing..." : "Analyze medications"}
      </button>
    </section>
  );
}

function DrugInputCard({
  canRemove,
  drug,
  index,
  metadata,
  onChange,
  onRemove,
}: {
  canRemove: boolean;
  drug: DrugFormState;
  index: number;
  metadata: MetadataResponse | null;
  onChange: (drug: DrugFormState) => void;
  onRemove: () => void;
}) {
  const routes = metadata?.routes ?? ["oral", "unknown"];
  const releaseTypes = metadata?.release_types ?? ["ir", "unknown"];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-white">Drug {index + 1}</h3>
          <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
            structured
          </span>
        </div>

        <button
          className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 transition hover:bg-red-950/50 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-30"
          disabled={!canRemove}
          onClick={onRemove}
          type="button"
        >
          Remove
        </button>
      </div>

      <label className="block text-sm font-medium text-slate-300">
        Medication name
        <input
          className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300"
          onChange={(event) =>
            onChange({
              ...drug,
              name: event.target.value,
            })
          }
          placeholder="vortioxetine"
          value={drug.name}
        />
      </label>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-300">
          Route
          <select
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
            onChange={(event) =>
              onChange({
                ...drug,
                route: event.target.value,
              })
            }
            value={drug.route}
          >
            {routes.map((route) => (
              <option key={route} value={route}>
                {route}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm font-medium text-slate-300">
          Release type
          <select
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
            onChange={(event) =>
              onChange({
                ...drug,
                releaseType: event.target.value,
              })
            }
            value={drug.releaseType}
          >
            {releaseTypes.map((releaseType) => (
              <option key={releaseType} value={releaseType}>
                {releaseType}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}

function ResultsPanel({
  analysis,
  error,
}: {
  analysis: AnalyzeResponse | null;
  error: string | null;
}) {
  if (error) {
    return (
      <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-2xl font-semibold text-white">Analysis output</h2>
        <ErrorBanner message={error} />
      </section>
    );
  }

  if (!analysis) {
    return (
      <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-2xl font-semibold text-white">Analysis output</h2>
        <div className="mt-6 rounded-2xl border border-dashed border-slate-700 bg-slate-950/50 p-10 text-center text-sm text-slate-500">
          Run an analysis to see interaction findings.
        </div>
      </section>
    );
  }

  const payload = analysis.payload;
  const timingSummaries = payload.pk_timing_interpretation ?? [];
  const pairCount = payload.pairs?.length ?? 0;
  const publicSummaryCount = payload.public_result_summaries?.length ?? 0;

  return (
    <section className="space-y-5">
      <SummaryHeader
        drugCount={payload.input.drug_names.length}
        pairCount={pairCount}
        publicSummaryCount={publicSummaryCount}
      />

      <ResultCard
        description="Human-readable timing interpretation for each medication."
        title="PK timing"
      >
        <div className="space-y-3">
          {timingSummaries.length ? (
            timingSummaries.map((summary) => (
              <div
                className="rounded-xl border border-slate-800 bg-slate-950/70 p-4"
                key={summary.drug_id}
              >
                <p className="text-sm font-semibold text-cyan-200">
                  {summary.drug_id}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {summary.summary ?? "No timing summary available."}
                </p>
              </div>
            ))
          ) : (
            <EmptyResult message="No PK timing summaries available." />
          )}
        </div>
      </ResultCard>

      <ResultCard
        description="Public-facing interaction and mechanism summaries."
        title="Clinical summaries"
      >
        {publicSummaryCount ? (
          <div className="space-y-3">
            {payload.public_result_summaries.map((summary, index) => (
              <SummaryObjectCard key={index} summary={summary} />
            ))}
          </div>
        ) : (
          <EmptyResult message="No public interaction summaries returned." />
        )}
      </ResultCard>

      <ResultCard
        description="Pair-level findings returned by the current analysis engine."
        title="Pair findings"
      >
        {pairCount ? (
          <div className="space-y-3">
            {payload.pairs.map((pair, index) => (
              <SummaryObjectCard key={index} summary={pair} />
            ))}
          </div>
        ) : (
          <EmptyResult message="No pair findings returned." />
        )}
      </ResultCard>

      <details className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <summary className="cursor-pointer font-semibold text-white">
          Developer payload
        </summary>

        <pre className="mt-4 max-h-[36rem] overflow-auto rounded-xl bg-slate-950 p-4 text-xs leading-5 text-slate-300">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </details>
    </section>
  );
}

function SummaryHeader({
  drugCount,
  pairCount,
  publicSummaryCount,
}: {
  drugCount: number;
  pairCount: number;
  publicSummaryCount: number;
}) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold text-white">Analysis complete</h2>
        <p className="text-sm text-slate-400">
          PharmDS returned structured interaction and timing results.
        </p>
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-3">
        <Metric label="Drugs" value={drugCount} />
        <Metric label="Pair findings" value={pairCount} />
        <Metric label="Clinical summaries" value={publicSummaryCount} />
      </dl>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className="mt-2 text-3xl font-semibold text-cyan-200">{value}</dd>
    </div>
  );
}

function ResultCard({
  children,
  description,
  title,
}: {
  children: ReactNode;
  description: string;
  title: string;
}) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-white">{title}</h2>
        <p className="text-sm leading-6 text-slate-400">{description}</p>
      </div>

      <div className="mt-5">{children}</div>
    </section>
  );
}

function SummaryObjectCard({ summary }: { summary: Record<string, unknown> }) {
  const entries = Object.entries(summary);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <dl className="space-y-3">
        {entries.map(([key, value]) => (
          <div key={key}>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
              {formatLabel(key)}
            </dt>
            <dd className="mt-1 break-words text-sm leading-6 text-slate-300">
              {formatValue(value)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function EmptyResult({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/50 p-5 text-sm text-slate-500">
      {message}
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <p className="mt-5 rounded-2xl border border-red-900/60 bg-red-950/50 p-4 text-sm text-red-200">
      {message}
    </p>
  );
}

function formatLabel(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter: string) => letter.toUpperCase());
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "None";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return JSON.stringify(value);
}

export default App;
