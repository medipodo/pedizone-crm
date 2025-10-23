import React from 'react';

const PageHeader = ({ title, subtitle, action }) => {
  return (
    <div className="space-y-4">
      {/* Top Brand */}
      <div className="text-center py-2 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-[#E50019]">PediZone İş Takip ve Saha Satış Sistemi</h1>
      </div>
      
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">{title}</h2>
          {subtitle && <p className="text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
    </div>
  );
};

export default PageHeader;
