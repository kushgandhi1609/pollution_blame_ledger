import React from 'react';

export type BadgeVariant = 'active' | 'warning' | 'expired' | 'onboard' | 'neutral' | 'source';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  size?: 'sm' | 'md';
  className?: string;
  sourceKey?: string;
}

const sourceColors: Record<string, { bg: string; text: string }> = {
  stubble_burning: { bg: '#F5ECE7', text: '#8C5032' },
  vehicular: { bg: '#EAF1F9', text: '#1B3A5C' },
  dust: { bg: '#F8F4EA', text: '#967848' },
  industry: { bg: '#EEF1F5', text: '#455060' },
  other: { bg: '#F0F4F8', text: '#506680' },
};

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  children,
  size = 'md',
  className = '',
  sourceKey,
}) => {
  let bg = 'var(--color-surface-alt)';
  let color = 'var(--color-text-secondary)';
  let border = '1px solid var(--color-border)';

  if (sourceKey && sourceColors[sourceKey]) {
    bg = sourceColors[sourceKey].bg;
    color = sourceColors[sourceKey].text;
    border = `1px solid ${color}33`;
  } else {
    switch (variant) {
      case 'active':
        bg = 'var(--color-active-bg)';
        color = 'var(--color-active-text)';
        border = '1px solid #C8E5D5';
        break;
      case 'warning':
        bg = 'var(--color-warning-bg)';
        color = 'var(--color-warning-text)';
        border = '1px solid var(--color-warning-border)';
        break;
      case 'expired':
        bg = 'var(--color-expired-bg)';
        color = 'var(--color-expired-text)';
        border = '1px solid #F5C7C7';
        break;
      case 'onboard':
        bg = 'var(--color-onboard-bg)';
        color = 'var(--color-onboard-text)';
        border = '1px solid var(--color-secondary-navy)';
        break;
      case 'neutral':
      default:
        bg = 'var(--color-surface-alt)';
        color = 'var(--color-text-secondary)';
        border = '1px solid var(--color-border)';
        break;
    }
  }

  const padding = size === 'sm' ? '2px 8px' : '4px 10px';
  const fontSize = size === 'sm' ? '11px' : '12px';

  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding,
        fontSize,
        fontWeight: 600,
        lineHeight: 1.2,
        borderRadius: 'var(--radius-full)',
        backgroundColor: bg,
        color,
        border,
        whiteSpace: 'nowrap',
        textTransform: 'none',
      }}
    >
      {children}
    </span>
  );
};
