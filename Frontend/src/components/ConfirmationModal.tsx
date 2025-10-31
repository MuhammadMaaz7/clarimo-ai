import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from './ui/button';

interface ConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'danger' | 'warning' | 'info';
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'danger'
}) => {
    if (!isOpen) return null;

    const variantStyles = {
        danger: {
            icon: 'text-red-400',
            iconBg: 'bg-red-500/20',
            confirmBtn: 'bg-red-500/80 hover:bg-red-500/90 text-white border border-red-500/50'
        },
        warning: {
            icon: 'text-yellow-400',
            iconBg: 'bg-yellow-500/20',
            confirmBtn: 'bg-yellow-600 hover:bg-yellow-700 text-white'
        },
        info: {
            icon: 'text-blue-400',
            iconBg: 'bg-blue-500/20',
            confirmBtn: 'bg-blue-600 hover:bg-blue-700 text-white'
        }
    };

    const styles = variantStyles[variant];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative bg-gray-900/95 backdrop-blur-xl border border-white/10 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
                {/* Close button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-1 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                    <X className="h-4 w-4" />
                </button>

                {/* Icon */}
                <div className={`w-12 h-12 ${styles.iconBg} rounded-lg flex items-center justify-center mb-4`}>
                    <AlertTriangle className={`h-6 w-6 ${styles.icon}`} />
                </div>

                {/* Content */}
                <div className="mb-6">
                    <h3 className="text-lg font-semibold text-white mb-2">
                        {title}
                    </h3>
                    <p className="text-gray-300 leading-relaxed">
                        {message}
                    </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 justify-end">
                    <Button
                        variant="ghost"
                        onClick={onClose}
                        className="text-gray-400 hover:text-white hover:bg-white/10"
                    >
                        {cancelText}
                    </Button>
                    <Button
                        onClick={() => {
                            onConfirm();
                            onClose();
                        }}
                        className={styles.confirmBtn}
                    >
                        {confirmText}
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmationModal;