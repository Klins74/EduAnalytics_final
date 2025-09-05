import React from 'react';
import { Clock, Database, Wifi, WifiOff, AlertTriangle } from 'lucide-react';

const DataSourceBadge = ({ 
  source = 'local', 
  lastUpdated = null, 
  isConnected = true,
  className = '' 
}) => {
  const getSourceIcon = () => {
    switch (source) {
      case 'canvas':
        return isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />;
      case 'local':
        return <Database className="w-3 h-3" />;
      case 'cache':
        return <Clock className="w-3 h-3" />;
      default:
        return <Database className="w-3 h-3" />;
    }
  };

  const getSourceLabel = () => {
    switch (source) {
      case 'canvas':
        return 'Canvas';
      case 'local':
        return 'Local';
      case 'cache':
        return 'Cached';
      default:
        return 'Unknown';
    }
  };

  const getStatusColor = () => {
    if (source === 'canvas' && !isConnected) {
      return 'bg-red-100 text-red-700 border-red-200';
    }
    
    // Check staleness if lastUpdated is provided
    if (lastUpdated) {
      const now = new Date();
      const updated = new Date(lastUpdated);
      const hoursOld = (now - updated) / (1000 * 60 * 60);
      
      if (hoursOld > 24) {
        return 'bg-orange-100 text-orange-700 border-orange-200';
      } else if (hoursOld > 6) {
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      }
    }
    
    return 'bg-green-100 text-green-700 border-green-200';
  };

  const getStalenessText = () => {
    if (!lastUpdated) return '';
    
    const now = new Date();
    const updated = new Date(lastUpdated);
    const hoursOld = (now - updated) / (1000 * 60 * 60);
    
    if (hoursOld < 1) {
      const minutesOld = Math.floor((now - updated) / (1000 * 60));
      return `${minutesOld}m ago`;
    } else if (hoursOld < 24) {
      return `${Math.floor(hoursOld)}h ago`;
    } else {
      const daysOld = Math.floor(hoursOld / 24);
      return `${daysOld}d ago`;
    }
  };

  const isStale = () => {
    if (!lastUpdated) return false;
    const now = new Date();
    const updated = new Date(lastUpdated);
    const hoursOld = (now - updated) / (1000 * 60 * 60);
    return hoursOld > 6;
  };

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium ${getStatusColor()} ${className}`}>
      {getSourceIcon()}
      <span>{getSourceLabel()}</span>
      {lastUpdated && (
        <>
          <span className="text-gray-400">•</span>
          <span className="flex items-center gap-1">
            {isStale() && <AlertTriangle className="w-3 h-3" />}
            {getStalenessText()}
          </span>
        </>
      )}
      {source === 'canvas' && !isConnected && (
        <>
          <span className="text-gray-400">•</span>
          <span>Offline</span>
        </>
      )}
    </div>
  );
};

export default DataSourceBadge;
