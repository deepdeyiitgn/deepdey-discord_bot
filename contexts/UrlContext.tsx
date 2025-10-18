
import React, { createContext, useState, useEffect, ReactNode, useMemo } from 'react';
import type { ShortenedUrl, PaymentRecord, UrlContextType } from '../types';
import { api } from '../api';

export const UrlContext = createContext<UrlContextType | undefined>(undefined);

export const UrlProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [allUrls, setAllUrls] = useState<ShortenedUrl[]>([]);
  const [paymentHistory, setPaymentHistory] = useState<PaymentRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const [urls, payments] = await Promise.all([
        api.getUrls(),
        api.getPaymentHistory()
      ]);
      setAllUrls(urls);
      setPaymentHistory(payments);
      setLoading(false);
    };

    loadData();
  }, []);

  const { activeUrls, expiredUrls } = useMemo(() => {
    const now = Date.now();
    const active: ShortenedUrl[] = [];
    const expired: ShortenedUrl[] = [];
    for (const url of allUrls) {
      if (url.expiresAt === Infinity || url.expiresAt > now) {
        active.push(url);
      } else {
        expired.push(url);
      }
    }
    return { activeUrls: active, expiredUrls: expired };
  }, [allUrls]);
  

  const addUrl = async (newUrl: ShortenedUrl): Promise<void> => {
    const existingUrl = allUrls.find(url => url.alias === newUrl.alias);

    if (existingUrl) {
        const isExistingActive = existingUrl.expiresAt === Infinity || existingUrl.expiresAt > Date.now();

        if (isExistingActive) {
            // If an active URL with the same alias exists, block the creation.
            throw new Error('This alias is already taken. Please choose another one.');
        } else {
            // If the existing URL is expired, allow overwriting it by replacing it.
            const updatedUrls = [...allUrls.filter(url => url.id !== existingUrl.id), newUrl];
            setAllUrls(updatedUrls);
            await api.saveUrls(updatedUrls);
        }
    } else {
        // If no URL with the same alias exists, add the new one.
        const updatedUrls = [...allUrls, newUrl];
        setAllUrls(updatedUrls);
        await api.saveUrls(updatedUrls);
    }
  };

  const deleteUrl = async (urlId: string): Promise<void> => {
    const updatedUrls = allUrls.filter(u => u.id !== urlId);
    setAllUrls(updatedUrls);
    await api.saveUrls(updatedUrls);
  };
  
  const deleteUrlsByUserId = async (userId: string): Promise<void> => {
    const updatedUrls = allUrls.filter(u => u.userId !== userId);
    setAllUrls(updatedUrls);
    await api.saveUrls(updatedUrls);
  };
  
  // Fix: Implement the `extendUrls` function to update the expiration dates of specified URLs.
  const extendUrls = async (urlIds: string[], newExpiresAt: number): Promise<void> => {
    const updatedUrls = allUrls.map(url => {
        if (urlIds.includes(url.id)) {
            return { ...url, expiresAt: newExpiresAt };
        }
        return url;
    });
    setAllUrls(updatedUrls);
    await api.saveUrls(updatedUrls);
  };

  const addPaymentRecord = async (record: PaymentRecord): Promise<void> => {
    const updatedHistory = [...paymentHistory, record];
    setPaymentHistory(updatedHistory);
    await api.savePaymentHistory(updatedHistory);
  };

  const clearAllDynamicUrls = async (): Promise<void> => {
    const updatedUrls = allUrls.filter(u => u.id.startsWith('static-'));
    setAllUrls(updatedUrls);
    await api.saveUrls(updatedUrls);
  };

  const value: UrlContextType = {
    allUrls,
    activeUrls,
    expiredUrls,
    paymentHistory,
    addUrl,
    deleteUrl,
    deleteUrlsByUserId,
    extendUrls,
    addPaymentRecord,
    clearAllDynamicUrls,
    loading
  };

  return <UrlContext.Provider value={value}>{children}</UrlContext.Provider>;
};
