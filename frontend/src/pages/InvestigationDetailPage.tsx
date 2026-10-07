import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useInvestigation } from '../hooks/useInvestigation';
import { useIncident } from '../hooks/useIncident';
import { usePostmortem } from '../hooks/usePostmortem';
import { useEvaluation } from '../hooks/useEvaluation';
import { InvestigationHeader } from '../components/investigation/InvestigationHeader';
import { InvestigationTimeline } from '../components/investigation/InvestigationTimeline';
import { RootCausePanel } from '../components/investigation/RootCausePanel';
import { RemediationRecommendations } from '../components/investigation/RemediationRecommendations';
import { KnowledgeSources } from '../components/investigation/KnowledgeSources';
import { ToolCallsList } from '../components/investigation/ToolCallsList';
import { EvidenceList } from '../components/investigation/EvidenceList';
import { HypothesisList } from '../components/investigation/HypothesisList';
import { PostmortemSection } from '../components/investigation/PostmortemSection';
import { EvaluationSection } from '../components/investigation/EvaluationSection';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import {
  Clock,
  BookOpen,
  Terminal,
  Activity,
  GitBranch,
  RefreshCw,
  Play,
  Loader2,
} from 'lucide-react';

export const InvestigationDetailPage: React.FC = () => {
  const { incidentId } = useParams<{ incidentId: string }>();
  const [activeTab, setActiveTab] = useState<'timeline' | 'rag' | 'tools' | 'evidence' | 'hypotheses'>('timeline');

  const { incident } = useIncident(incidentId);
  const {
    investigation,
    loading,
    running,
    proposing,
    error,
    refetch,
    startInvestigation,
    proposeRemediations,
  } = useInvestigation(incidentId);

  const {
    postmortem,
    loading: postmortemLoading,
    generating: postmortemGenerating,
    error: postmortemError,
    generate: generatePostmortem,
  } = usePostmortem(investigation?.investigation_id);

  const {
    evaluation,
    loading: evaluationLoading,
    evaluating: evaluationEvaluating,
    error: evaluationError,
    evaluate: evaluateInvestigationAction,
  } = useEvaluation(investigation?.investigation_id);

  if (loading && !investigation) {
    return <LoadingState message="Retrieving investigation telemetry graph..." />;
  }

  if (error && !investigation) {
    return (
      <ErrorState
        title="Failed to Load Investigation"
        message={error}
        onRetry={refetch}
      />
    );
  }

  if (!investigation) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-12 text-center space-y-4">
        <h2 className="text-lg font-bold text-slate-200">No Active Investigation</h2>
        <p className="text-xs font-mono text-slate-400 max-w-md mx-auto">
          An automated LangGraph investigation has not yet been executed for this incident.
        </p>
        <button
          onClick={() => startInvestigation(5)}
          disabled={running}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-950 text-white font-mono text-xs font-bold transition-colors"
        >
          {running ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Starting Orchestration...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              Trigger Investigation Now
            </>
          )}
        </button>
      </div>
    );
  }

  // Derive alternative explanations from hypotheses
  const alternativeHypotheses = investigation.hypotheses
    .filter((h) => h.status !== 'SUPPORTED' && h.status !== 'VERIFIED_STRONG')
    .map((h) => `${h.hypothesis_text} [${h.status}]`);

  const supportingEvidence = investigation.evidence.map(
    (e) => `${e.source_tool}: ${e.summary}`
  );

  return (
    <div className="space-y-6" data-testid="investigation-detail-page">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to={`/incidents/${incidentId}`}
          className="text-xs font-mono text-slate-400 hover:text-slate-200 inline-flex items-center gap-1.5 transition-colors"
        >
          ← Back to Incident Overview
        </Link>

        <div className="flex items-center gap-3">
          {running && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800 text-xs font-mono animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Live Investigation Polling Active
            </span>
          )}

          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Header */}
      <InvestigationHeader
        investigation={investigation}
        incidentTitle={incident?.title}
        serviceName={incident?.service?.name}
        severity={incident?.severity}
      />

      {/* Prominent Root Cause Panel */}
      <RootCausePanel
        status={investigation.status}
        probableRootCause={investigation.probable_root_cause}
        confidenceScore={investigation.confidence_score}
        analysisReasoning={investigation.analysis_reasoning}
        supportingEvidence={supportingEvidence}
        alternativeHypotheses={alternativeHypotheses}
      />

      {/* Recommended Remediation Action Box */}
      <RemediationRecommendations
        recommendations={investigation.recommended_remediation}
        onProposeRemediations={proposeRemediations}
        isProposing={proposing}
      />

      {/* Investigation Exploration Tabs */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800 overflow-x-auto pb-px">
          <button
            onClick={() => setActiveTab('timeline')}
            className={`inline-flex items-center gap-2 px-4 py-2.5 font-mono text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'timeline'
                ? 'border-cyan-400 text-cyan-400 bg-slate-900/50'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/20'
            }`}
            data-testid="tab-timeline"
          >
            <Clock className="w-3.5 h-3.5" />
            Execution Timeline ({investigation.steps.length})
          </button>

          <button
            onClick={() => setActiveTab('hypotheses')}
            className={`inline-flex items-center gap-2 px-4 py-2.5 font-mono text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'hypotheses'
                ? 'border-cyan-400 text-cyan-400 bg-slate-900/50'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/20'
            }`}
            data-testid="tab-hypotheses"
          >
            <GitBranch className="w-3.5 h-3.5" />
            Competing Hypotheses ({investigation.hypotheses.length})
          </button>

          <button
            onClick={() => setActiveTab('evidence')}
            className={`inline-flex items-center gap-2 px-4 py-2.5 font-mono text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'evidence'
                ? 'border-cyan-400 text-cyan-400 bg-slate-900/50'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/20'
            }`}
            data-testid="tab-evidence"
          >
            <Activity className="w-3.5 h-3.5" />
            Empirical Evidence ({investigation.evidence.length})
          </button>

          <button
            onClick={() => setActiveTab('tools')}
            className={`inline-flex items-center gap-2 px-4 py-2.5 font-mono text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'tools'
                ? 'border-cyan-400 text-cyan-400 bg-slate-900/50'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/20'
            }`}
            data-testid="tab-tools"
          >
            <Terminal className="w-3.5 h-3.5" />
            Diagnostic Tool Calls ({investigation.tool_calls.length})
          </button>

          <button
            onClick={() => setActiveTab('rag')}
            className={`inline-flex items-center gap-2 px-4 py-2.5 font-mono text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'rag'
                ? 'border-cyan-400 text-cyan-400 bg-slate-900/50'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/20'
            }`}
            data-testid="tab-rag"
          >
            <BookOpen className="w-3.5 h-3.5" />
            RAG Knowledge Sources ({investigation.retrieved_sources.length})
          </button>
        </div>

        {/* Tab Content Display */}
        <div className="pt-2">
          {activeTab === 'timeline' && <InvestigationTimeline steps={investigation.steps} />}
          {activeTab === 'hypotheses' && <HypothesisList hypotheses={investigation.hypotheses} />}
          {activeTab === 'evidence' && <EvidenceList evidence={investigation.evidence} />}
          {activeTab === 'tools' && <ToolCallsList toolCalls={investigation.tool_calls} />}
          {activeTab === 'rag' && <KnowledgeSources sources={investigation.retrieved_sources} />}
        </div>
      </div>

      {/* AI Investigation Quality Evaluation */}
      <EvaluationSection
        evaluation={evaluation}
        loading={evaluationLoading}
        evaluating={evaluationEvaluating}
        error={evaluationError}
        onEvaluate={evaluateInvestigationAction}
        investigationStatus={investigation.status}
      />

      {/* Incident Postmortem Report */}
      <PostmortemSection
        postmortem={postmortem}
        loading={postmortemLoading}
        generating={postmortemGenerating}
        error={postmortemError}
        onGenerate={generatePostmortem}
        investigationStatus={investigation.status}
      />
    </div>
  );
};
