import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import { analyzeDrugs, fetchDrugCatalog, fetchMetadata } from "./api/client";
import type {
  AnalyzeResponse,
  DrugCatalogEntry,
  DrugDosageOption,
  MetadataResponse,
  PairFinding,
  RuleHit,
} from "./api/types";

type DrugFormState = {
  name: string;
  route: string;
  releaseType: string;
  selectedDrugId: string | null;
  strengthValue: number | null;
  strengthUnit: string | null;
  dosageForm: string | null;
};

type Page = "analyzer" | "drug-database";

const DEFAULT_DRUGS: DrugFormState[] = [
  {
    name: "propranolol",
    route: "oral",
    releaseType: "er",
    selectedDrugId: "propranolol",
    strengthValue: null,
    strengthUnit: null,
    dosageForm: null,
  },
  {
    name: "vortioxetine",
    route: "oral",
    releaseType: "ir",
    selectedDrugId: "vortioxetine",
    strengthValue: null,
    strengthUnit: null,
    dosageForm: null,
  },
];

const EMPTY_DRUG: DrugFormState = {
  name: "",
  route: "oral",
  releaseType: "unknown",
  selectedDrugId: null,
  strengthValue: null,
  strengthUnit: null,
  dosageForm: null,
};

function App() {
  const [page, setPage] = useState<Page>("analyzer");
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [drugCatalog, setDrugCatalog] = useState<DrugCatalogEntry[]>([]);
  const [drugCatalogError, setDrugCatalogError] = useState<string | null>(null);
  const [isDrugCatalogLoading, setIsDrugCatalogLoading] = useState(true);
  const [drugs, setDrugs] = useState<DrugFormState[]>(DEFAULT_DRUGS);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [domain, setDomain] = useState("all");
  const [qtRisk, setQtRisk] = useState(false);
  const [bleedingRisk, setBleedingRisk] = useState(false);
  const [pdEffectMode, setPdEffectMode] = useState<"all" | "specific">("all");
  const [selectedPdEffects, setSelectedPdEffects] = useState<string[]>([]);

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

  useEffect(() => {
    void fetchDrugCatalog()
      .then((response) => {
        setDrugCatalog(response.drugs);
      })
      .catch((caught: unknown) => {
        const message =
          caught instanceof Error
            ? caught.message
            : "Failed to load PharmDS drug catalog.";

        setDrugCatalogError(message);
      })
      .finally(() => {
        setIsDrugCatalogLoading(false);
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
          name: drug.selectedDrugId ?? drug.name.trim(),
          route: drug.route || null,
          release_type: drug.releaseType || null,
          strength_value: drug.strengthValue,
          strength_unit: drug.strengthUnit,
          dosage_form: drug.dosageForm,
        })),
        domain,
        qt_risk: qtRisk,
        bleeding_risk: bleedingRisk,
        pd_effects:
          pdEffectMode === "all"
            ? null
            : selectedPdEffects,
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
        <header className="space-y-6">
          <div className="space-y-3">
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
          </div>

          <nav
            aria-label="Primary"
            className="flex w-fit gap-2 rounded-2xl border border-slate-800 bg-slate-900 p-1.5"
          >
            <NavButton
              active={page === "analyzer"}
              label="Analyzer"
              onClick={() => setPage("analyzer")}
            />
            <NavButton
              active={page === "drug-database"}
              label="Drug Database"
              onClick={() => setPage("drug-database")}
            />
          </nav>
        </header>

        {page === "analyzer" ? (
          <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
            <AnalyzeForm
              bleedingRisk={bleedingRisk}
              canSubmit={canSubmit}
              domain={domain}
              drugCatalog={drugCatalog}
              drugs={drugs}
              isAnalyzing={isAnalyzing}
              metadata={metadata}
              metadataError={metadataError}
              onAddDrug={addDrug}
              onAnalyze={() => {
                void handleAnalyze();
              }}
              onBleedingRiskChange={setBleedingRisk}
              onDomainChange={setDomain}
              onPdEffectModeChange={(mode) => {
                setPdEffectMode(mode);

                if (mode === "all") {
                  setSelectedPdEffects([]);
                }
              }}
              onQtRiskChange={setQtRisk}
              onRemoveDrug={removeDrug}
              onResetPdSelection={() => {
                setPdEffectMode("all");
                setSelectedPdEffects([]);
                setQtRisk(false);
                setBleedingRisk(false);
              }}
              onSelectedPdEffectsChange={setSelectedPdEffects}
              onUpdateDrug={updateDrug}
              pdEffectMode={pdEffectMode}
              qtRisk={qtRisk}
              selectedPdEffects={selectedPdEffects}
            />

            <ResultsPanel analysis={analysis} error={analysisError} />
          </section>
        ) : (
          <DrugDatabasePage
            drugs={drugCatalog}
            error={drugCatalogError}
            isLoading={isDrugCatalogLoading}
          />
        )}
      </section>
    </main>
  );
}

function NavButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className={
        active
          ? "rounded-xl bg-cyan-300 px-4 py-2 text-sm font-bold text-slate-950"
          : "rounded-xl px-4 py-2 text-sm font-semibold text-slate-400 transition hover:bg-slate-800 hover:text-white"
      }
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  );
}

function DrugDatabasePage({
  drugs,
  error,
  isLoading,
}: {
  drugs: DrugCatalogEntry[];
  error: string | null;
  isLoading: boolean;
}) {
  const [query, setQuery] = useState("");
  const [drugClassFilter, setDrugClassFilter] = useState("all");
  const [releaseTypeFilter, setReleaseTypeFilter] = useState("all");

  const drugClasses = useMemo(
    () =>
      Array.from(
        new Set(
          drugs
            .map((drug) => drug.drug_class)
            .filter((drugClass): drugClass is string => Boolean(drugClass)),
        ),
      ).sort((a, b) => a.localeCompare(b)),
    [drugs],
  );

  const releaseTypes = useMemo(
    () =>
      Array.from(new Set(drugs.flatMap((drug) => drug.release_types))).sort(
        (a, b) => a.localeCompare(b),
      ),
    [drugs],
  );

  const filteredDrugs = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return drugs.filter((drug) => {
      const searchableValues = [
        drug.id,
        drug.generic_name,
        drug.drug_class ?? "",
        ...drug.aliases,
      ];

      const matchesText =
        !normalizedQuery ||
        searchableValues.some((value) =>
          value.toLowerCase().includes(normalizedQuery),
        );

      const matchesDrugClass =
        drugClassFilter === "all" || drug.drug_class === drugClassFilter;

      const matchesReleaseType =
        releaseTypeFilter === "all" ||
        drug.release_types.includes(releaseTypeFilter);

      return matchesText && matchesDrugClass && matchesReleaseType;
    });
  }, [drugClassFilter, drugs, query, releaseTypeFilter]);

  const hasActiveFilters =
    query.trim().length > 0 ||
    drugClassFilter !== "all" ||
    releaseTypeFilter !== "all";

  function clearFilters() {
    setQuery("");
    setDrugClassFilter("all");
    setReleaseTypeFilter("all");
  }

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold text-white">Drug Database</h2>
            <p className="max-w-3xl text-sm leading-6 text-slate-400">
              Browse the medications currently available to the PharmDS analysis
              engine, including aliases, formulations, and curated strengths.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 px-5 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Drugs
            </p>
            <p className="mt-1 text-2xl font-semibold text-cyan-200">
              {drugs.length}
            </p>
          </div>
        </div>

        <label className="mt-6 block text-sm font-medium text-slate-300">
          Search drugs
          <input
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by generic name, class, ID, or alias"
            value={query}
          />
        </label>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <label className="block text-sm font-medium text-slate-300">
            Drug class
            <select
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
              onChange={(event) => setDrugClassFilter(event.target.value)}
              value={drugClassFilter}
            >
              <option value="all">All drug classes</option>
              {drugClasses.map((drugClass) => (
                <option key={drugClass} value={drugClass}>
                  {formatDrugClass(drugClass)}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-medium text-slate-300">
            Release type
            <select
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
              onChange={(event) => setReleaseTypeFilter(event.target.value)}
              value={releaseTypeFilter}
            >
              <option value="all">All release types</option>
              {releaseTypes.map((releaseType) => (
                <option key={releaseType} value={releaseType}>
                  {formatReleaseType(releaseType)}
                </option>
              ))}
            </select>
          </label>
        </div>

        {hasActiveFilters ? (
          <div className="mt-4 flex justify-end">
            <button
              className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-400 transition hover:border-slate-500 hover:text-white"
              onClick={clearFilters}
              type="button"
            >
              Clear filters
            </button>
          </div>
        ) : null}
      </div>

      {error ? <ErrorBanner message={error} /> : null}

      {isLoading ? (
        <div className="rounded-3xl border border-slate-800 bg-slate-900 p-10 text-center text-sm text-slate-500">
          Loading drug catalog...
        </div>
      ) : null}

      {!isLoading && !error ? (
        <>
          <div className="flex items-center justify-between px-1">
            <p className="text-sm text-slate-400">
              Showing {filteredDrugs.length} of {drugs.length} drugs
            </p>
          </div>

          {filteredDrugs.length ? (
            <div className="grid gap-4 lg:grid-cols-2">
              {filteredDrugs.map((drug) => (
                <DrugCatalogCard drug={drug} key={drug.id} />
              ))}
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-700 bg-slate-900/50 p-10 text-center text-sm text-slate-500">
              No drugs match the current search and filters.
            </div>
          )}
        </>
      ) : null}
    </section>
  );
}

function DrugCatalogCard({ drug }: { drug: DrugCatalogEntry }) {
  return (
    <article className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="space-y-1">
        <h3 className="text-xl font-semibold text-white">
          {formatDrugName(drug.generic_name)}
        </h3>
        <p className="text-sm text-slate-500">{drug.id}</p>
      </div>

      <dl className="mt-5 space-y-4">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Drug class
          </dt>
          <dd className="mt-1 text-sm text-slate-300">
            {drug.drug_class
              ? formatDrugClass(drug.drug_class)
              : "Not specified"}
          </dd>
        </div>

        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Aliases
          </dt>
          <dd className="mt-2 flex flex-wrap gap-2">
            {drug.aliases.length ? (
              drug.aliases.map((alias) => (
                <span
                  className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300"
                  key={alias}
                >
                  {alias}
                </span>
              ))
            ) : (
              <span className="text-sm text-slate-500">None</span>
            )}
          </dd>
        </div>

        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Release types
          </dt>
          <dd className="mt-2 flex flex-wrap gap-2">
            {drug.release_types.map((releaseType) => (
              <span
                className="rounded-full bg-cyan-950/70 px-3 py-1 text-xs font-semibold text-cyan-200"
                key={releaseType}
              >
                {formatReleaseType(releaseType)}
              </span>
            ))}
          </dd>
        </div>

        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Curated strengths
          </dt>
          <dd className="mt-2 flex flex-wrap gap-2">
            {drug.dosage_options.length ? (
              drug.dosage_options.map((option) => (
                <span
                  className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300"
                  key={dosageOptionKey(option)}
                >
                  {formatDosageOption(option)}
                </span>
              ))
            ) : (
              <span className="text-sm text-slate-500">Not curated</span>
            )}
          </dd>
        </div>
      </dl>
    </article>
  );
}

function AnalyzeForm({
  bleedingRisk,
  canSubmit,
  domain,
  drugCatalog,
  drugs,
  isAnalyzing,
  metadata,
  metadataError,
  onAddDrug,
  onAnalyze,
  onBleedingRiskChange,
  onDomainChange,
  onPdEffectModeChange,
  onQtRiskChange,
  onRemoveDrug,
  onResetPdSelection,
  onSelectedPdEffectsChange,
  onUpdateDrug,
  pdEffectMode,
  qtRisk,
  selectedPdEffects,
}: {
  bleedingRisk: boolean;
  canSubmit: boolean;
  domain: string;
  drugCatalog: DrugCatalogEntry[];
  drugs: DrugFormState[];
  isAnalyzing: boolean;
  metadata: MetadataResponse | null;
  metadataError: string | null;
  onAddDrug: () => void;
  onAnalyze: () => void;
  onBleedingRiskChange: (value: boolean) => void;
  onDomainChange: (value: string) => void;
  onPdEffectModeChange: (value: "all" | "specific") => void;
  onQtRiskChange: (value: boolean) => void;
  onRemoveDrug: (index: number) => void;
  onResetPdSelection: () => void;
  onSelectedPdEffectsChange: (value: string[]) => void;
  onUpdateDrug: (index: number, drug: DrugFormState) => void;
  pdEffectMode: "all" | "specific";
  qtRisk: boolean;
  selectedPdEffects: string[];
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
            drugCatalog={drugCatalog}
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

      <AnalysisControls
        domain={domain}
        metadata={metadata}
        onDomainChange={onDomainChange}
      />

      <PdEffectControls
        bleedingRisk={bleedingRisk}
        metadata={metadata}
        mode={pdEffectMode}
        onBleedingRiskChange={onBleedingRiskChange}
        onModeChange={onPdEffectModeChange}
        onQtRiskChange={onQtRiskChange}
        onReset={onResetPdSelection}
        onSelectedEffectsChange={onSelectedPdEffectsChange}
        qtRisk={qtRisk}
        selectedEffects={selectedPdEffects}
      />

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

function AnalysisControls({
  domain,
  metadata,
  onDomainChange,
}: {
  domain: string;
  metadata: MetadataResponse | null;
  onDomainChange: (value: string) => void;
}) {
  const domains = metadata?.domains ?? ["all"];

  return (
    <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
      <div className="space-y-2">
        <h3 className="font-semibold text-white">Analysis controls</h3>
        <p className="text-sm leading-6 text-slate-400">
          Narrow the interaction domain included in the analysis.
        </p>
      </div>

      <label className="mt-4 block text-sm font-medium text-slate-300">
        Interaction domain
        <select
          className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
          onChange={(event) => onDomainChange(event.target.value)}
          value={domain}
        >
          {domains.map((domainOption) => (
            <option key={domainOption} value={domainOption}>
              {formatLabel(domainOption)}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}

function PdEffectControls({
  bleedingRisk,
  metadata,
  mode,
  onBleedingRiskChange,
  onModeChange,
  onQtRiskChange,
  onReset,
  onSelectedEffectsChange,
  qtRisk,
  selectedEffects,
}: {
  bleedingRisk: boolean;
  metadata: MetadataResponse | null;
  mode: "all" | "specific";
  onBleedingRiskChange: (value: boolean) => void;
  onModeChange: (value: "all" | "specific") => void;
  onQtRiskChange: (value: boolean) => void;
  onReset: () => void;
  onSelectedEffectsChange: (value: string[]) => void;
  qtRisk: boolean;
  selectedEffects: string[];
}) {
  const effects = metadata?.pd_effects ?? [];

  function toggleEffect(effectId: string, checked: boolean) {
    onModeChange("specific");

    if (checked) {
      onSelectedEffectsChange(
        Array.from(new Set([...selectedEffects, effectId])),
      );
      return;
    }

    onSelectedEffectsChange(
      selectedEffects.filter((selected) => selected !== effectId),
    );
  }

  return (
    <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
      <div className="space-y-2">
        <h3 className="font-semibold text-white">PD Effects</h3>
        <p className="text-sm leading-6 text-slate-400">
          Analyze all supported pharmacodynamic effects or limit the analysis
          to specific effects.
        </p>
      </div>

      <label className="mt-4 block text-sm font-medium text-slate-300">
        Effect selection
        <select
          className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
          onChange={(event) =>
            onModeChange(event.target.value as "all" | "specific")
          }
          value={mode}
        >
          <option value="all">All Effects</option>
          <option value="specific">Specific Effects</option>
        </select>
      </label>

      <div className="mt-5">
        <p className="text-sm font-medium text-slate-300">
          Specific PD effects
        </p>

        <div className="mt-3 grid max-h-80 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
          {effects.map((effect) => (
            <label
              className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 px-3 py-3"
              key={effect.id}
            >
              <input
                checked={selectedEffects.includes(effect.id)}
                className="h-4 w-4 rounded border-slate-600 bg-slate-950 text-cyan-300 focus:ring-cyan-300"
                onChange={(event) =>
                  toggleEffect(effect.id, event.target.checked)
                }
                type="checkbox"
              />
              <span className="text-sm text-slate-300">
                {effect.label}
              </span>
            </label>
          ))}
        </div>

        {!effects.length ? (
          <p className="mt-3 text-sm text-slate-500">
            PD effect metadata is not available.
          </p>
        ) : null}
      </div>

      <div className="mt-6 space-y-3 border-t border-slate-800 pt-5">
        <div>
          <p className="text-sm font-medium text-slate-300">
            Patient-specific risk context
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            These modifiers add patient context and do not filter the selected
            PD effects.
          </p>
        </div>

        <RiskToggle
          checked={qtRisk}
          description="Include patient-specific QT risk context in the analysis."
          label="QT risk"
          onChange={onQtRiskChange}
        />

        <RiskToggle
          checked={bleedingRisk}
          description="Include patient-specific bleeding risk context in the analysis."
          label="Bleeding risk"
          onChange={onBleedingRiskChange}
        />
      </div>

      <button
        className="mt-5 w-full rounded-xl border border-slate-700 px-4 py-2.5 text-sm font-semibold text-slate-400 transition hover:border-slate-500 hover:text-white"
        onClick={onReset}
        type="button"
      >
        Reset Selection
      </button>
    </section>
  );
}

function RiskToggle({
  checked,
  description,
  label,
  onChange,
}: {
  checked: boolean;
  description: string;
  label: string;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
      <input
        checked={checked}
        className="mt-1 h-4 w-4 rounded border-slate-600 bg-slate-950 text-cyan-300 focus:ring-cyan-300"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />

      <span>
        <span className="block text-sm font-semibold text-slate-200">
          {label}
        </span>
        <span className="mt-1 block text-xs leading-5 text-slate-500">
          {description}
        </span>
      </span>
    </label>
  );
}

function DrugInputCard({
  canRemove,
  drug,
  drugCatalog,
  index,
  metadata,
  onChange,
  onRemove,
}: {
  canRemove: boolean;
  drug: DrugFormState;
  drugCatalog: DrugCatalogEntry[];
  index: number;
  metadata: MetadataResponse | null;
  onChange: (drug: DrugFormState) => void;
  onRemove: () => void;
}) {
  const selectedCatalogDrug =
    drug.selectedDrugId === null
      ? null
      : (drugCatalog.find((entry) => entry.id === drug.selectedDrugId) ?? null);

  const formulations = selectedCatalogDrug?.formulations ?? [];

  const routes = formulations.length
    ? formulations.map((formulation) => formulation.route)
    : ["unknown"];

  const selectedFormulation =
    formulations.find((formulation) => formulation.route === drug.route) ??
    null;

  const releaseTypes = selectedFormulation?.release_types.length
    ? selectedFormulation.release_types
    : ["unknown"];

  const dosageOptions = (selectedCatalogDrug?.dosage_options ?? []).filter(
    (option) =>
      option.route === drug.route && option.release_type === drug.releaseType,
  );

  const selectedDosageKey =
    drug.strengthValue === null ||
    drug.strengthUnit === null ||
    drug.dosageForm === null
      ? ""
      : dosageOptionKey({
          route: drug.route,
          release_type: drug.releaseType,
          dosage_form: drug.dosageForm,
          strength_value: drug.strengthValue,
          strength_unit: drug.strengthUnit,
        });

  const suggestions = getDrugSuggestions(drug.name, drugCatalog);

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

      <div className="relative">
        <label className="block text-sm font-medium text-slate-300">
          Medication name
          <input
            autoComplete="off"
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300"
            onChange={(event) => {
              const nextName = event.target.value;

              onChange({
                ...drug,
                name: nextName,
                route: "unknown",
                releaseType: "unknown",
                selectedDrugId: null,
                strengthValue: null,
                strengthUnit: null,
                dosageForm: null,
              });
            }}
            placeholder="vortioxetine"
            value={drug.name}
          />
        </label>

        {drug.name.trim() && drug.selectedDrugId === null ? (
          <DrugSuggestions
            onSelect={(entry) => {
              const selectedFormulation =
                entry.formulations.find(
                  (formulation) => formulation.route === drug.route,
                ) ??
                entry.formulations[0] ??
                null;

              const route = selectedFormulation?.route ?? "unknown";
              const releaseTypes = selectedFormulation?.release_types ?? [
                "unknown",
              ];

              const releaseType = releaseTypes.includes(drug.releaseType)
                ? drug.releaseType
                : (releaseTypes[0] ?? "unknown");

              onChange({
                ...drug,
                name: entry.generic_name,
                route,
                releaseType,
                selectedDrugId: entry.id,
                strengthValue: null,
                strengthUnit: null,
                dosageForm: null,
              });
            }}
            suggestions={suggestions}
          />
        ) : null}

        {selectedCatalogDrug ? (
          <p className="mt-2 text-xs text-slate-500">
            Selected: {formatDrugName(selectedCatalogDrug.generic_name)}
            {selectedCatalogDrug.drug_class
              ? ` · ${selectedCatalogDrug.drug_class}`
              : ""}
          </p>
        ) : null}
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-300">
          Route
          <select
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
            onChange={(event) => {
              const nextRoute = event.target.value;
              const nextFormulation = formulations.find(
                (formulation) => formulation.route === nextRoute,
              );
              const nextReleaseTypes = nextFormulation?.release_types ?? [
                "unknown",
              ];

              onChange({
                ...drug,
                route: nextRoute,
                releaseType: nextReleaseTypes.includes(drug.releaseType)
                  ? drug.releaseType
                  : (nextReleaseTypes[0] ?? "unknown"),
                strengthValue: null,
                strengthUnit: null,
                dosageForm: null,
              });
            }}
            value={drug.route}
          >
            {routes.map((route) => (
              <option key={route} value={route}>
                {formatRoute(route)}
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
                strengthValue: null,
                strengthUnit: null,
                dosageForm: null,
              })
            }
            value={drug.releaseType}
          >
            {releaseTypes.map((releaseType) => (
              <option key={releaseType} value={releaseType}>
                {formatReleaseType(releaseType)}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm font-medium text-slate-300">
          Strength (optional)
          <select
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
            disabled={!dosageOptions.length}
            onChange={(event) => {
              const option = dosageOptions.find(
                (candidate) => dosageOptionKey(candidate) === event.target.value,
              );

              onChange({
                ...drug,
                strengthValue: option?.strength_value ?? null,
                strengthUnit: option?.strength_unit ?? null,
                dosageForm: option?.dosage_form ?? null,
              });
            }}
            value={selectedDosageKey}
          >
            <option value="">
              {dosageOptions.length ? "Not specified" : "Not curated"}
            </option>
            {dosageOptions.map((option) => (
              <option key={dosageOptionKey(option)} value={dosageOptionKey(option)}>
                {formatDosageOption(option)}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}

function DrugSuggestions({
  onSelect,
  suggestions,
}: {
  onSelect: (drug: DrugCatalogEntry) => void;
  suggestions: DrugCatalogEntry[];
}) {
  if (!suggestions.length) {
    return (
      <div className="absolute z-20 mt-1 w-full rounded-xl border border-slate-800 bg-slate-950 p-3 text-sm text-slate-500 shadow-2xl">
        No matching drugs found.
      </div>
    );
  }

  return (
    <div className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-xl border border-slate-800 bg-slate-950 shadow-2xl">
      {suggestions.map((suggestion) => (
        <button
          className="block w-full border-b border-slate-900 px-4 py-3 text-left transition last:border-b-0 hover:bg-slate-900"
          key={suggestion.id}
          onMouseDown={(event) => {
            event.preventDefault();
            onSelect(suggestion);
          }}
          type="button"
        >
          <span className="block text-sm font-semibold text-white">
            {formatDrugName(suggestion.generic_name)}
          </span>

          <span className="mt-1 block text-xs text-slate-500">
            {suggestion.drug_class ?? "Class not specified"}
          </span>

          {suggestion.aliases.length ? (
            <span className="mt-1 block text-xs text-slate-600">
              Also: {suggestion.aliases.join(", ")}
            </span>
          ) : null}
        </button>
      ))}
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
          <div className="space-y-4">
            {payload.pairs.map((pair, index) => (
              <PairFindingCard key={index} pair={pair} />
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

function SummaryObjectCard({
  summary,
}: {
  summary: Record<string, unknown>;
}) {
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
              {formatSummaryValue(key, value)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function PairFindingCard({ pair }: { pair: PairFinding }) {
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/70">
      <header className="border-b border-slate-800 bg-slate-900/70 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Medication pair
            </p>
            <h3 className="mt-1 text-lg font-semibold text-white">
              {formatDrugName(pair.drug_1.name)}{" "}
              <span className="font-normal text-slate-500">+</span>{" "}
              {formatDrugName(pair.drug_2.name)}
            </h3>
          </div>

          <div className="flex flex-wrap gap-2">
            <ResultBadge
              label={`Severity: ${formatLabel(pair.overall.severity)}`}
            />
            <ResultBadge
              label={`Action: ${formatLabel(pair.overall.class)}`}
            />
          </div>
        </div>
      </header>

      <div className="space-y-5 p-5">
        <PairDomainSection
          emptyMessage="No PK findings for this medication pair."
          hits={pair.pk.hits}
          summary={pair.pk.summary}
          title="Pharmacokinetic findings"
        />

        <PairDomainSection
          emptyMessage="No PD findings for this medication pair."
          hits={pair.pd.hits}
          summary={pair.pd.summary}
          title="Pharmacodynamic findings"
        />
      </div>
    </article>
  );
}

function PairDomainSection({
  emptyMessage,
  hits,
  summary,
  title,
}: {
  emptyMessage: string;
  hits: RuleHit[];
  summary?: string | null;
  title: string;
}) {
  return (
    <section>
      <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
        {title}
      </h4>

      {summary ? (
        <p className="mt-2 text-sm leading-6 text-slate-300">{summary}</p>
      ) : null}

      {hits.length ? (
        <div className="mt-3 space-y-3">
          {hits.map((hit) => (
            <RuleHitCard hit={hit} key={hit.rule_id} />
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-slate-500">{emptyMessage}</p>
      )}
    </section>
  );
}

function RuleHitCard({ hit }: { hit: RuleHit }) {
  const effectId =
    typeof hit.inputs.effect_id === "string" ? hit.inputs.effect_id : null;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h5 className="font-semibold text-white">{hit.name}</h5>
          <p className="mt-1 text-xs text-slate-500">
            Rule {hit.rule_id}
            {effectId ? ` · ${formatLabel(effectId)}` : ""}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <ResultBadge label={formatLabel(hit.severity)} />
          <ResultBadge label={formatLabel(hit.class)} />
        </div>
      </div>

      {hit.explanation ? (
        <div className="mt-4">
          <ResultSectionLabel>Explanation</ResultSectionLabel>
          <p className="mt-1 text-sm leading-6 text-slate-300">
            {hit.explanation}
          </p>
        </div>
      ) : null}

      {hit.rationale.length ? (
        <div className="mt-4">
          <ResultSectionLabel>Why this matters</ResultSectionLabel>
          <ResultList items={hit.rationale} />
        </div>
      ) : null}

      {hit.actions.length ? (
        <div className="mt-4">
          <ResultSectionLabel>Suggested actions</ResultSectionLabel>
          <ResultList items={hit.actions} />
        </div>
      ) : null}

      {hit.references.length ? (
        <div className="mt-4">
          <ResultSectionLabel>References</ResultSectionLabel>
          <div className="mt-2 space-y-2">
            {hit.references.map((reference, index) => (
              <div
                className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2"
                key={`${reference.source}-${index}`}
              >
                <p className="text-xs font-semibold text-cyan-200">
                  {reference.source}
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-400">
                  {reference.citation}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {hit.severity_rationale || hit.action_rationale ? (
        <details className="mt-4 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2">
          <summary className="cursor-pointer text-xs font-semibold text-slate-400">
            Scoring rationale
          </summary>

          <div className="mt-2 space-y-2 text-xs leading-5 text-slate-500">
            {hit.severity_rationale ? (
              <p>{hit.severity_rationale}</p>
            ) : null}
            {hit.action_rationale ? (
              <p>{hit.action_rationale}</p>
            ) : null}
          </div>
        </details>
      ) : null}
    </div>
  );
}

function ResultBadge({ label }: { label: string }) {
  return (
    <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs font-medium text-slate-300">
      {label}
    </span>
  );
}

function ResultSectionLabel({ children }: { children: ReactNode }) {
  return (
    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
      {children}
    </p>
  );
}

function ResultList({ items }: { items: string[] }) {
  return (
    <ul className="mt-2 space-y-1.5 text-sm leading-6 text-slate-300">
      {items.map((item, index) => (
        <li className="flex gap-2" key={`${item}-${index}`}>
          <span aria-hidden="true" className="text-cyan-300">
            •
          </span>
          <span>{stripLeadingBullet(item)}</span>
        </li>
      ))}
    </ul>
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

function formatSummaryValue(key: string, value: unknown): string {
  if (value === null || value === undefined) {
    return "None";
  }

  if (key === "source" && typeof value === "string") {
    if (value === "aggregate_summary") {
      return "Mechanism pipeline";
    }

    if (value === "rule_hit") {
      return "Rule engine";
    }
  }

  if (key === "evidence_label" && typeof value === "string") {
    if (value === "rule_engine") {
      return "Rule engine";
    }

    return formatLabel(value);
  }

  if (key === "drugs" && Array.isArray(value)) {
    return value.map((item) => formatDrugName(String(item))).join(", ");
  }

  if (key === "concern_type" && typeof value === "string") {
    return value === "PD" || value === "PK" ? value : formatLabel(value);
  }

  if (
    (key === "severity_label" || key === "class") &&
    typeof value === "string"
  ) {
    return formatLabel(value);
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return JSON.stringify(value);
}

function stripLeadingBullet(value: string): string {
  return value.replace(/^\s*[-•]\s*/, "");
}

function getDrugSuggestions(
  query: string,
  drugCatalog: DrugCatalogEntry[],
): DrugCatalogEntry[] {
  const normalizedQuery = query.trim().toLowerCase();

  if (!normalizedQuery) {
    return [];
  }

  const scored = drugCatalog
    .map((drug) => {
      const genericName = drug.generic_name.toLowerCase();
      const id = drug.id.toLowerCase();
      const aliases = drug.aliases.map((alias) => alias.toLowerCase());

      let score = 0;

      if (genericName === normalizedQuery || id === normalizedQuery) {
        score = 100;
      } else if (aliases.includes(normalizedQuery)) {
        score = 95;
      } else if (
        genericName.startsWith(normalizedQuery) ||
        id.startsWith(normalizedQuery)
      ) {
        score = 80;
      } else if (aliases.some((alias) => alias.startsWith(normalizedQuery))) {
        score = 75;
      } else if (
        genericName.includes(normalizedQuery) ||
        id.includes(normalizedQuery)
      ) {
        score = 60;
      } else if (aliases.some((alias) => alias.includes(normalizedQuery))) {
        score = 55;
      }

      return {
        drug,
        score,
      };
    })
    .filter((result) => result.score > 0)
    .sort(
      (a, b) =>
        b.score - a.score ||
        a.drug.generic_name.localeCompare(b.drug.generic_name),
    );

  return scored.slice(0, 8).map((result) => result.drug);
}

function formatDrugClass(value: string): string {
  const preserved: Record<string, string> = {
    ssri: "SSRI",
    snri: "SNRI",
    nassa: "NaSSA",
  };

  const words = value.trim().split(/\s+/);

  return words
    .map((word) => {
      const normalized = word.toLowerCase();

      if (preserved[normalized]) {
        return preserved[normalized];
      }

      if (normalized === "spari") {
        return "SPARI";
      }

      return word
        .split(/([/-])/)
        .map((part) => {
          if (part === "/" || part === "-") {
            return part;
          }

          if (!part) {
            return part;
          }

          const lowered = part.toLowerCase();

          return lowered.charAt(0).toUpperCase() + lowered.slice(1);
        })
        .join("");
    })
    .join(" ");
}

function formatDrugName(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter: string) => letter.toUpperCase());
}

function dosageOptionKey(option: DrugDosageOption): string {
  return [
    option.route,
    option.release_type,
    option.dosage_form,
    String(option.strength_value),
    option.strength_unit,
  ].join("|");
}

function formatDosageOption(option: DrugDosageOption): string {
  return `${option.strength_value} ${option.strength_unit} ${option.dosage_form} · ${formatRoute(option.route)} ${formatReleaseType(option.release_type)}`;
}

function formatRoute(value: string): string {
  const labels: Record<string, string> = {
    oral: "Oral",
    iv: "IV",
    im: "IM",
    sc: "SC",
    transdermal: "Transdermal",
    inhaled: "Inhaled",
    intranasal: "Intranasal",
    sublingual: "Sublingual",
    buccal: "Buccal",
    rectal: "Rectal",
    topical: "Topical",
    ophthalmic: "Ophthalmic",
    otic: "Otic",
    epidural: "Epidural",
    intrathecal: "Intrathecal",
    vaginal: "Vaginal",
    unknown: "Unknown",
  };

  return labels[value] ?? formatLabel(value);
}

function formatReleaseType(value: string): string {
  const labels: Record<string, string> = {
    ir: "IR",
    sr: "SR",
    er: "ER",
    xr: "XR",
    dr: "DR",
    la: "LA",
    depot: "Depot",
    unknown: "Unknown",
  };

  return labels[value] ?? formatLabel(value);
}

export default App;
