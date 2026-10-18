import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  action,
  className = '',
  style = {},
  noPadding = false,
}) => {
  return (
    <div
      className={className}
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border-card)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        ...style,
      }}
    >
      {(title || subtitle || action) && (
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--color-border-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
          }}
        >
          <div>
            {title && (
              <h3
                style={{
                  fontSize: '15px',
                  fontWeight: 600,
                  color: 'var(--color-heading)',
                  margin: 0,
                }}
              >
                {title}
              </h3>
            )}
            {subtitle && (
              <p
                style={{
                  fontSize: '12px',
                  color: 'var(--color-text-muted)',
                  marginTop: '2px',
                  marginBottom: 0,
                }}
              >
                {subtitle}
              </p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div style={{ padding: noPadding ? '0' : '20px', flex: 1 }}>{children}</div>
    </div>
  );
};
