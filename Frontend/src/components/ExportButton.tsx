/**
 * ExportButton Component
 * 
 * Provides export functionality for validation reports in JSON and PDF formats.
 * Handles download of exported files with proper error handling.
 * 
 * Requirements: 15.1, 15.2, 15.3
 */

import React, { useState } from 'react';
import { Button } from './ui/button';
import { Download, FileJson, FileText, Loader2 } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogCancel,
} from './ui/alert-dialog';
import api from '../lib/api';

interface ExportButtonProps {
  validationId: string;
  validationTitle?: string;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  showLabel?: boolean;
  className?: string;
}

type ExportFormat = 'json' | 'pdf';

const ExportButton: React.FC<ExportButtonProps> = ({
  validationId,
  validationTitle = 'validation-report',
  variant = 'outline',
  size = 'default',
  showLabel = true,
  className = '',
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);

  const sanitizeFilename = (filename: string): string => {
    return filename.replace(/[^a-z0-9_-]/gi, '_').toLowerCase();
  };

  const handleExportJson = async () => {
    setIsExporting(true);
    setExportFormat('json');
    setError(null);

    try {
      const data = await api.validations.exportJson(validationId);
      
      // Create blob and download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${sanitizeFilename(validationTitle)}_${validationId.slice(0, 8)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Failed to export JSON:', err);
      setError(err.message || 'Failed to export validation report as JSON');
      setShowErrorDialog(true);
    } finally {
      setIsExporting(false);
      setExportFormat(null);
    }
  };

  const handleExportPdf = async () => {
    setIsExporting(true);
    setExportFormat('pdf');
    setError(null);

    try {
      const blob = await api.validations.exportPdf(validationId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${sanitizeFilename(validationTitle)}_${validationId.slice(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Failed to export PDF:', err);
      setError(err.message || 'Failed to export validation report as PDF');
      setShowErrorDialog(true);
    } finally {
      setIsExporting(false);
      setExportFormat(null);
    }
  };

  return (
    <>
      <div className={`flex gap-2 ${className}`}>
        {/* JSON Export Button */}
        <Button
          variant={variant}
          size={size}
          onClick={handleExportJson}
          disabled={isExporting}
          className="gap-2"
        >
          {isExporting && exportFormat === 'json' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <FileJson className="h-4 w-4" />
          )}
          {showLabel && (
            <span>
              {isExporting && exportFormat === 'json' ? 'Exporting...' : 'Export JSON'}
            </span>
          )}
        </Button>

        {/* PDF Export Button */}
        <Button
          variant={variant}
          size={size}
          onClick={handleExportPdf}
          disabled={isExporting}
          className="gap-2"
        >
          {isExporting && exportFormat === 'pdf' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <FileText className="h-4 w-4" />
          )}
          {showLabel && (
            <span>
              {isExporting && exportFormat === 'pdf' ? 'Exporting...' : 'Export PDF'}
            </span>
          )}
        </Button>
      </div>

      {/* Error Dialog */}
      <AlertDialog open={showErrorDialog} onOpenChange={setShowErrorDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Export Failed</AlertDialogTitle>
            <AlertDialogDescription>
              {error || 'An error occurred while exporting the validation report.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Close</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default ExportButton;
