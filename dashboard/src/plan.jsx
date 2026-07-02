import { createContext, useContext, useEffect, useState } from 'react';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DEFAULT = { plan: 'community', features: [], isPro: false, isEnterprise: false };

export const PlanContext = createContext(DEFAULT);
export const usePlan = () => useContext(PlanContext);

export function PlanProvider({ children }) {
  const [planData, setPlanData] = useState(DEFAULT);

  useEffect(() => {
    fetch(`${BASE}/plan`)
      .then((r) => r.json())
      .then(setPlanData)
      .catch(() => {});
  }, []);

  return <PlanContext.Provider value={planData}>{children}</PlanContext.Provider>;
}
