import React, { useState } from 'react';
import { Users, Wind, AlertCircle, ShieldCheck, Calendar, BookOpen } from 'lucide-react';
import { AdviceGroup, PrecautionRow } from '../../types';
import { Badge } from '../common/Badge';

interface PrecautionAdvisorProps {
  advice: PrecautionRow[];
  groups: AdviceGroup[];
}

const defaultGroupNames: Record<string, { en: string; hi: string }> = {
  general_public: { en: 'General Public', hi: 'आम जनता' },
  children_schools: { en: 'Children & Schools', hi: 'बच्चे एवं स्कूल' },
  older_adults: { en: 'Older Adults (60+)', hi: 'वरिष्ठ नागरिक (60+)' },
  cardiopulmonary_patients: { en: 'Cardiopulmonary Patients', hi: 'हृदय व फेफड़ों के मरीज' },
  outdoor_workers: { en: 'Outdoor Workers', hi: 'बाहर काम करने वाले श्रमिक' },
};

export const PrecautionAdvisor: React.FC<PrecautionAdvisorProps> = ({ advice, groups }) => {
  const [selectedGroup, setSelectedGroup] = useState<string>('children_schools');
  const [lang, setLang] = useState<'en' | 'hi'>('en');

  const filtered = advice.filter(
    (a) => (a.group || '').toLowerCase() === selectedGroup.toLowerCase()
  );

  const displayGroups =
    groups.length > 0
      ? groups
      : Object.entries(defaultGroupNames).map(([id, n]) => ({
          id,
          name: n.en,
          name_hi: n.hi,
        }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header with Bilingual Toggle */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-heading)', margin: 0 }}>
            {lang === 'en' ? 'Bilingual Health & Precaution Advisor' : 'द्विभाषी स्वास्थ्य एवं सावधानी सलाहकार'}
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px', marginBottom: 0 }}>
            {lang === 'en'
              ? 'CPCB & WHO graded protective guidance tailored to vulnerable cohorts and forecasted particulate tiers.'
              : 'सीपीसीबी और डब्ल्यूएचओ के मानकों पर आधारित स्वास्थ्य सुरक्षा परामर्श।'}
          </p>
        </div>

        {/* Language Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: 'var(--color-surface-alt)', padding: '3px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <button
            onClick={() => setLang('en')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 600,
              borderRadius: 'var(--radius-xs)',
              backgroundColor: lang === 'en' ? 'var(--color-primary)' : 'transparent',
              color: lang === 'en' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            English
          </button>
          <button
            onClick={() => setLang('hi')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 600,
              borderRadius: 'var(--radius-xs)',
              backgroundColor: lang === 'hi' ? 'var(--color-primary)' : 'transparent',
              color: lang === 'hi' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            हिन्दी (Hindi)
          </button>
        </div>
      </div>

      {/* Demographic Cohort Selector */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
        {displayGroups.map((g) => (
          <button
            key={g.id}
            onClick={() => setSelectedGroup(g.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              fontSize: '12px',
              fontWeight: selectedGroup === g.id ? 600 : 500,
              borderRadius: 'var(--radius-sm)',
              border: selectedGroup === g.id ? '1px solid var(--color-primary)' : '1px solid var(--color-border)',
              backgroundColor: selectedGroup === g.id ? 'var(--color-onboard-bg)' : 'var(--color-surface)',
              color: selectedGroup === g.id ? 'var(--color-primary)' : 'var(--color-text-secondary)',
              whiteSpace: 'nowrap',
            }}
          >
            <Users size={13} />
            <span>{lang === 'en' ? g.name : g.name_hi}</span>
          </button>
        ))}
      </div>

      {/* Advice Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
        {filtered.map((row, idx) => {
          const groupName = defaultGroupNames[row.group]
            ? lang === 'en'
              ? defaultGroupNames[row.group].en
              : defaultGroupNames[row.group].hi
            : row.group;

          const currentAdvice = lang === 'en' ? row.current_advice_en : row.current_advice_hi;
          const tomorrowAdvice = lang === 'en' ? row.tomorrow_advice_en : row.tomorrow_advice_hi;
          const contextMsg = lang === 'en' ? row.source_context_en : row.source_context_hi;

          return (
            <div
              key={idx}
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border-card)',
                borderRadius: 'var(--radius-md)',
                padding: '18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              {/* Card Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Badge variant={row.current_aqi_band === 'poor' || row.current_aqi_band === 'very_poor' ? 'warning' : 'onboard'} size="sm">
                  AQI: {(row.current_aqi_band || 'standard').toUpperCase()} ({row.current_pm25} µg/m³)
                </Badge>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  {groupName}
                </span>
              </div>

              {/* Current Immediate Guidance */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                  {lang === 'en' ? 'Today / Current Exposure Guidance:' : 'आज के लिए दिशा-निर्देश:'}
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-heading)', lineHeight: 1.5 }}>
                  {currentAdvice}
                </div>
              </div>

              {/* Tomorrow 24h Outlook Guidance */}
              {tomorrowAdvice && (
                <div
                  style={{
                    backgroundColor: 'var(--color-surface-alt)',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '11px',
                    lineHeight: 1.4,
                  }}
                >
                  <div style={{ fontWeight: 600, color: 'var(--color-primary)', marginBottom: '2px' }}>
                    {lang === 'en' ? 'Tomorrow Outlook' : 'कल का पूर्वानुमान'}{' '}
                    {row.tomorrow_pm25_range && `(${row.tomorrow_pm25_range})`}:
                  </div>
                  <div style={{ color: 'var(--color-text-secondary)' }}>{tomorrowAdvice}</div>
                </div>
              )}

              {/* Atmospheric Context & Source Citation */}
              {(contextMsg || row.source_citation) && (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    fontSize: '11px',
                    paddingTop: '8px',
                    borderTop: '1px solid var(--color-border-light)',
                    color: 'var(--color-text-dim)',
                  }}
                >
                  {contextMsg && <div>{contextMsg}</div>}
                  {row.source_citation && (
                    <div style={{ fontStyle: 'italic' }}>Citation: {row.source_citation}</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
