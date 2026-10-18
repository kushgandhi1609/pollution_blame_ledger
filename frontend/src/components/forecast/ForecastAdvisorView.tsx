import React from 'react';
import { Card } from '../common/Card';
import {
  AdviceGroup,
  BacktestComparisonRow,
  BacktestSummary,
  ForecastEvaluationRow,
  ForecastHourlyPoint,
  PrecautionRow,
} from '../../types';
import { ForecastChart } from './ForecastChart';
import { ForecastEvaluationTable } from './ForecastEvaluationTable';
import { PrecautionAdvisor } from './PrecautionAdvisor';
import { BacktestComparisonTable } from './BacktestComparisonTable';
import { HealthImpactCard } from './HealthImpactCard';

interface ForecastAdvisorViewProps {
  forecastPoints: ForecastHourlyPoint[];
  forecastEval: ForecastEvaluationRow[];
  advice: PrecautionRow[];
  adviceGroups: AdviceGroup[];
  backtestSummary: BacktestSummary | null;
  backtestComparisons: BacktestComparisonRow[];
  healthData: any;
}

export const ForecastAdvisorView: React.FC<ForecastAdvisorViewProps> = ({
  forecastPoints,
  forecastEval,
  advice,
  adviceGroups,
  backtestSummary,
  backtestComparisons,
  healthData,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. 72H Forecast Projection */}
      <Card
        title="Predictive Intelligence & Early Warning"
        subtitle="Gradient boosted particulate forecasts predicting 24h, 48h, and 72h atmospheric concentrations with uncertainty boundaries."
      >
        <ForecastChart forecastPoints={forecastPoints} />
        <div style={{ marginTop: '20px' }}>
          <ForecastEvaluationTable evaluation={forecastEval} />
        </div>
      </Card>

      {/* 2. Bilingual Precaution Advisor */}
      <Card
        title="Public Health Action Guidance"
        subtitle="Targeted exposure minimization guidelines structured for high-risk demographic cohorts and educational institutions."
      >
        <PrecautionAdvisor advice={advice} groups={adviceGroups} />
      </Card>

      {/* 3. Scientific Backtesting & Peer-Reviewed Literature Validation */}
      <Card
        title="Scientific Transparency & Literature Backtesting"
        subtitle="Transparent evaluation comparing AerTrace attribution ranges against 63 published peer-reviewed studies (IIT Kanpur, SAFAR, TERI, NEERI)."
      >
        <BacktestComparisonTable
          summary={backtestSummary}
          comparisons={backtestComparisons}
        />
      </Card>

      {/* 4. WHO GEMM Health Impact Burden */}
      <HealthImpactCard healthData={healthData} />
    </div>
  );
};
