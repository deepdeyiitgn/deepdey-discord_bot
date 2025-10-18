import React, { useState, useEffect, useContext } from 'react';
import { AuthProvider, AuthContext } from './contexts/AuthContext';
import { UrlProvider, UrlContext } from './contexts/UrlContext';
import { QrProvider } from './contexts/QrContext';
import Header from './components/Header';
import UrlShortener from './components/UrlShortener';
import UrlStats from './components/UrlStats';
import About from './components/About';
import HowToUse from './components/HowToUse';
import SocialLinks from './components/SocialLinks';
import RecentLinks from './components/RecentLinks';
import Dashboard from './components/Dashboard';
import AuthModal from './components/AuthModal';
import SubscriptionModal from './components/SubscriptionModal';
import ApiSubscriptionModal from './components/ApiSubscriptionModal';
import RedirectPage from './components/RedirectPage';
import BackToTopButton from './components/BackToTopButton';
import QrCodeGenerator from './components/QrCodeGenerator';
import StatusPage from './components/StatusPage';
import OwnerDashboard from './components/OwnerDashboard';
import ApiAccessPage from './components/ApiAccessPage';
import Watermark from './components/Watermark';
import NotFoundPage from './components/NotFoundPage';
import type { User } from './types';

interface AppContentProps {
  currentUser: User | null;
  isAuthModalOpen: boolean;
  isSubscriptionModalOpen: boolean;
  isApiSubscriptionModalOpen: boolean;
  closeSubscriptionModal: () => void;
  closeApiSubscriptionModal: () => void;
}

const getCleanPath = (hash: string) => {
    // Remove the leading '#' and then any leading slashes that might remain.
    return hash.substring(1).replace(/^\/+/, '');
};

const AppContent: React.FC<AppContentProps> = ({ isAuthModalOpen, isSubscriptionModalOpen, isApiSubscriptionModalOpen, closeSubscriptionModal, closeApiSubscriptionModal }) => {
    const urlContext = useContext(UrlContext);
    const [path, setPath] = useState(getCleanPath(window.location.hash));

    useEffect(() => {
        const handleHashChange = () => {
            setPath(getCleanPath(window.location.hash));
        };
        window.addEventListener('hashchange', handleHashChange);
        return () => window.removeEventListener('hashchange', handleHashChange);
    }, []);

    if (urlContext?.loading) {
        return <div className="min-h-screen bg-brand-dark" />;
    }

    const renderView = () => {
        // Fix: Replaced `JSX.Element` with `React.ReactNode` to resolve the 'Cannot find namespace JSX' error. `React.ReactNode` is a more robust type for renderable content and is available via the existing `React` import.
        const specialRoutes: Record<string, React.ReactNode> = {
            '': (
                <>
                    <UrlShortener />
                    <UrlStats />
                    <RecentLinks />
                    <div className="mt-16 grid gap-12 md:grid-cols-2">
                        <About />
                        <HowToUse />
                    </div>
                </>
            ),
            'dashboard': <Dashboard />,
            'qr-generator': <QrCodeGenerator />,
            'status': <StatusPage />,
            'owner': <OwnerDashboard />,
            'api': <ApiAccessPage />,
        };

        if (specialRoutes.hasOwnProperty(path)) {
            return specialRoutes[path];
        }

        const urlToRedirect = urlContext?.allUrls.find(u => u.alias === path);
        
        if (urlToRedirect) {
            const isExpired = urlToRedirect.expiresAt !== Infinity && urlToRedirect.expiresAt < Date.now();
            if (isExpired) {
                return <NotFoundPage />;
            }
            return <RedirectPage longUrl={urlToRedirect.longUrl} shortUrl={urlToRedirect.shortUrl} />;
        }

        return <NotFoundPage />;
    };

    return (
        <div className="gradient-bg min-h-screen text-white font-sans selection:bg-brand-primary selection:text-brand-dark">
            <div className="relative z-10">
                <Header currentView={path} />
                <main className="container mx-auto px-4 py-12 md:py-20">
                    {renderView()}
                </main>
                <footer className="py-12 border-t border-white/10">
                    <div className="container mx-auto px-4 text-center">
                        <div className="flex justify-center mb-4">
                            <a href="#/status" className="text-sm text-gray-400 hover:text-brand-primary transition-colors">Status</a>
                        </div>
                        <SocialLinks />
                        <Watermark />
                    </div>
                </footer>
            </div>
            {isAuthModalOpen && <AuthModal />}
            {isSubscriptionModalOpen && <SubscriptionModal onClose={closeSubscriptionModal} />}
            {isApiSubscriptionModalOpen && <ApiSubscriptionModal onClose={closeApiSubscriptionModal} />}
            <BackToTopButton />
        </div>
    );
};

const App: React.FC = () => {
    return (
        <AuthProvider>
            <UrlProvider>
                <QrProvider>
                    <AuthContext.Consumer>
                        {auth => auth ? (
                            <AppContent 
                                currentUser={auth.currentUser}
                                isAuthModalOpen={auth.isAuthModalOpen}
                                isSubscriptionModalOpen={auth.isSubscriptionModalOpen}
                                isApiSubscriptionModalOpen={auth.isApiSubscriptionModalOpen}
                                closeSubscriptionModal={auth.closeSubscriptionModal}
                                closeApiSubscriptionModal={auth.closeApiSubscriptionModal}
                            />
                        ) : null}
                    </AuthContext.Consumer>
                </QrProvider>
            </UrlProvider>
        </AuthProvider>
    );
};

export default App;