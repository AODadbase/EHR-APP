import React from 'react';

interface CardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export const DataCard: React.FC<CardProps> = ({ title, children, className = '', action }) => (
  <div className={`bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden ${className}`}>
    <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/30">
        <h3 className="font-semibold text-slate-800">{title}</h3>
        {action}
    </div>
    <div className="p-6">
        {children}
    </div>
  </div>
);

interface ListCardProps {
    title: string;
    items: React.ReactNode[];
    count?: number;
}

export const ListCard: React.FC<ListCardProps> = ({ title, items, count }) => (
    <DataCard title={title} action={count !== undefined && <span className="text-xs bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full">{count}</span>}>
        <div className="space-y-3">
            {items.length > 0 ? (
                items.map((item, idx) => (
                    <div key={idx} className="flex items-start p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-2 mr-3 flex-shrink-0" />
                        <div className="flex-1 text-sm">{item}</div>
                    </div>
                ))
            ) : (
                <div className="text-sm text-slate-400 italic text-center py-2">No items found</div>
            )}
        </div>
    </DataCard>
);
