/**
 * Competitor Analysis Context
 * Manages state for competitor analysis features
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Product, ProductFormData, CompetitiveAnalysis, AnalysisHistoryItem } from '../types/competitor';
import api from '../lib/api';

interface CompetitorContextType {
  // Products state
  products: Product[];
  currentProduct: Product | null;
  productsLoading: boolean;
  productsError: string | null;

  // Analysis state
  currentAnalysis: CompetitiveAnalysis | null;
  analysisLoading: boolean;
  analysisError: string | null;
  analysisProgress: number;

  // History state
  analysisHistory: AnalysisHistoryItem[];
  historyLoading: boolean;

  // Product operations
  fetchProducts: () => Promise<void>;
  fetchProductById: (productId: string) => Promise<void>;
  createProduct: (data: ProductFormData) => Promise<Product>;
  updateProduct: (productId: string, data: Partial<ProductFormData>) => Promise<Product>;
  deleteProduct: (productId: string) => Promise<void>;

  // Analysis operations
  startAnalysis: (productId: string) => Promise<CompetitiveAnalysis>;
  fetchAnalysisResult: (analysisId: string) => Promise<void>;
  pollAnalysisStatus: (analysisId: string) => Promise<void>;
  stopPolling: () => void;

  // History operations
  fetchAnalysisHistory: (productId: string) => Promise<void>;

  // Clear operations
  clearCurrentProduct: () => void;
  clearCurrentAnalysis: () => void;
  clearErrors: () => void;
}

const CompetitorContext = createContext<CompetitorContextType | undefined>(undefined);

export function CompetitorProvider({ children }: { children: ReactNode }) {
  // Products state
  const [products, setProducts] = useState<Product[]>([]);
  const [currentProduct, setCurrentProduct] = useState<Product | null>(null);
  const [productsLoading, setProductsLoading] = useState(false);
  const [productsError, setProductsError] = useState<string | null>(null);

  // Analysis state
  const [currentAnalysis, setCurrentAnalysis] = useState<CompetitiveAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);

  // History state
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Product operations
  const fetchProducts = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setProducts([]);
      setProductsLoading(false);
      return;
    }

    setProductsLoading(true);
    setProductsError(null);
    try {
      const data = await api.products.getAll();
      setProducts(data as Product[]);
    } catch (error: any) {
      setProductsError(error.message || 'Failed to fetch products');
    } finally {
      setProductsLoading(false);
    }
  }, []);

  const fetchProductById = useCallback(async (productId: string) => {
    setProductsLoading(true);
    setProductsError(null);
    try {
      const data = await api.products.getById(productId);
      setCurrentProduct(data as Product);
    } catch (error: any) {
      setProductsError(error.message || 'Failed to fetch product');
    } finally {
      setProductsLoading(false);
    }
  }, []);

  const createProduct = useCallback(async (data: ProductFormData): Promise<Product> => {
    setProductsLoading(true);
    setProductsError(null);
    try {
      const newProduct = await api.products.create(data);
      setProducts((prev) => [newProduct as Product, ...prev]);
      setCurrentProduct(newProduct as Product);
      return newProduct as Product;
    } catch (error: any) {
      setProductsError(error.message || 'Failed to create product');
      throw error;
    } finally {
      setProductsLoading(false);
    }
  }, []);

  const updateProduct = useCallback(async (productId: string, data: Partial<ProductFormData>): Promise<Product> => {
    setProductsLoading(true);
    setProductsError(null);
    try {
      // TODO: Implement API call
      const updatedProduct = currentProduct!;
      setProducts((prev) => prev.map((p) => (p.id === productId ? updatedProduct : p)));
      setCurrentProduct(updatedProduct);
      return updatedProduct;
    } catch (error: any) {
      setProductsError(error.message || 'Failed to update product');
      throw error;
    } finally {
      setProductsLoading(false);
    }
  }, [currentProduct]);

  const deleteProduct = useCallback(async (productId: string) => {
    setProductsLoading(true);
    setProductsError(null);
    try {
      await api.products.delete(productId);
      setProducts((prev) => prev.filter((p) => p.id !== productId));
      if (currentProduct?.id === productId) {
        setCurrentProduct(null);
      }
    } catch (error: any) {
      setProductsError(error.message || 'Failed to delete product');
      throw error;
    } finally {
      setProductsLoading(false);
    }
  }, [currentProduct]);

  // Analysis operations
  const startAnalysis = useCallback(async (productId: string): Promise<CompetitiveAnalysis> => {
    setAnalysisLoading(true);
    setAnalysisError(null);
    setAnalysisProgress(0);
    try {
      const analysis = await api.competitorAnalyses.start(productId);
      setCurrentAnalysis(analysis as CompetitiveAnalysis);
      return analysis as CompetitiveAnalysis;
    } catch (error: any) {
      setAnalysisError(error.message || 'Failed to start analysis');
      throw error;
    } finally {
      setAnalysisLoading(false);
    }
  }, []);

  const fetchAnalysisResult = useCallback(async (analysisId: string) => {
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      // TODO: Implement API call
    } catch (error: any) {
      setAnalysisError(error.message || 'Failed to fetch analysis result');
    } finally {
      setAnalysisLoading(false);
    }
  }, []);

  const pollAnalysisStatus = useCallback(async (analysisId: string) => {
    // TODO: Implement polling logic similar to ValidationContext
  }, []);

  const stopPolling = useCallback(() => {
    // TODO: Implement stop polling
  }, []);

  const fetchAnalysisHistory = useCallback(async (productId: string) => {
    setHistoryLoading(true);
    try {
      // TODO: Implement API call
      setAnalysisHistory([]);
    } catch (error: any) {
      console.error('Error fetching analysis history:', error);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Clear operations
  const clearCurrentProduct = useCallback(() => {
    setCurrentProduct(null);
  }, []);

  const clearCurrentAnalysis = useCallback(() => {
    setCurrentAnalysis(null);
    setAnalysisProgress(0);
    stopPolling();
  }, [stopPolling]);

  const clearErrors = useCallback(() => {
    setProductsError(null);
    setAnalysisError(null);
  }, []);

  const value: CompetitorContextType = {
    products,
    currentProduct,
    productsLoading,
    productsError,
    currentAnalysis,
    analysisLoading,
    analysisError,
    analysisProgress,
    analysisHistory,
    historyLoading,
    fetchProducts,
    fetchProductById,
    createProduct,
    updateProduct,
    deleteProduct,
    startAnalysis,
    fetchAnalysisResult,
    pollAnalysisStatus,
    stopPolling,
    fetchAnalysisHistory,
    clearCurrentProduct,
    clearCurrentAnalysis,
    clearErrors,
  };

  return <CompetitorContext.Provider value={value}>{children}</CompetitorContext.Provider>;
}

export function useCompetitor() {
  const context = useContext(CompetitorContext);
  if (context === undefined) {
    throw new Error('useCompetitor must be used within a CompetitorProvider');
  }
  return context;
}
