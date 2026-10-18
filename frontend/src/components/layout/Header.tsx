import React from 'react';
import {
  Layers,
  MapPin,
  Sliders,
  TrendingUp,
  BookOpen,
  ExternalLink,
  ShieldCheck,
} from 'lucide-react';
import { Button } from '../common/Button';

export type ActiveTab = 'attribution' | 'sensors' | 'policy' | 'forecast';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  onOpenMethodology: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  onOpenMethodology,
}) => {
  return (
    <header
      style={{
        backgroundColor: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-xs)',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
      }}
    >
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '20px',
        }}
      >
        {/* Brand Lockup with Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <img
            src="/aertrace_logo.png"
            alt="AerTrace Logo"
            style={{
              height: '42px',
              width: 'auto',
              objectFit: 'contain',
              display: 'block',
            }}
          />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '18px',
                  fontWeight: 700,
                  letterSpacing: '0.04em',
                  color: 'var(--color-primary)',
                }}
              >
                AERTRACE
              </span>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: 'var(--color-secondary-navy)',
                  backgroundColor: 'var(--color-primary)',
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                }}
              >
                v1.0
              </span>
            </div>
            <p
              style={{
                fontSize: '11px',
                color: 'var(--color-text-secondary)',
                margin: 0,
                fontWeight: 500,
              }}
            >
              Delhi-NCR Air Quality Attribution & Intelligence Ledger
            </p>
          </div>
        </div>

        {/* Central Core Principle Pill */}
        <div
          style={{
            display: 'none',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--color-onboard-bg)',
            color: 'var(--color-onboard-text)',
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--color-secondary-navy)',
            fontSize: '12px',
            fontWeight: 500,
          }}
          className="desktop-banner"
        >
          <ShieldCheck size={15} color="var(--color-primary)" />
          <span>Attribution is an estimate with uncertainty, not a verdict.</span>
        </div>

        {/* Top Right Utilities */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Button
            variant="outline"
            size="sm"
            icon={<BookOpen size={14} />}
            onClick={onOpenMethodology}
          >
            Methodology & Tracers
          </Button>
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            style={{ textDecoration: 'none' }}
          >
            <Button
              variant="ghost"
              size="sm"
              icon={<ExternalLink size={13} />}
            >
              API Docs
            </Button>
          </a>
        </div>
      </div>

      {/* Primary Navigation Tabs */}
      <div
        style={{
          borderTop: '1px solid var(--color-border-light)',
          backgroundColor: 'var(--color-surface)',
        }}
      >
        <div
          style={{
            maxWidth: '1440px',
            margin: '0 auto',
            padding: '0 24px',
            display: 'flex',
            gap: '8px',
            overflowX: 'auto',
          }}
        >
          <TabButton
            active={activeTab === 'attribution'}
            onClick={() => onTabChange('attribution')}
            icon={<Layers size={15} />}
            label="Attribution Ledger & Episodes"
          />
          <TabButton
            active={activeTab === 'sensors'}
            onClick={() => onTabChange('sensors')}
            icon={<MapPin size={15} />}
            label="Spatial Sensor Network"
          />
          <TabButton
            active={activeTab === 'policy'}
            onClick={() => onTabChange('policy')}
            icon={<Sliders size={15} />}
            label="Policy & Dust Rescheduler"
          />
          <TabButton
            active={activeTab === 'forecast'}
            onClick={() => onTabChange('forecast')}
            icon={<TrendingUp size={15} />}
            label="Forecast & Exposure Advisor"
          />
        </div>
      </div>
    </header>
  );
};

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

const TabButton: React.FC<TabButtonProps> = ({ active, onClick, icon, label }) => {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '12px 16px',
        fontSize: '13px',
        fontWeight: active ? 600 : 500,
        color: active ? 'var(--color-primary)' : 'var(--color-text-secondary)',
        borderBottom: active
          ? '2px solid var(--color-primary)'
          : '2px solid transparent',
        backgroundColor: active ? 'var(--color-surface-alt)' : 'transparent',
        borderTopLeftRadius: 'var(--radius-sm)',
        borderTopRightRadius: 'var(--radius-sm)',
        transition: 'all 0.15s ease',
        whiteSpace: 'nowrap',
      }}
    >
      <span style={{ color: active ? 'var(--color-primary)' : 'var(--color-text-dim)' }}>
        {icon}
      </span>
      {label}
    </button>
  );
};
