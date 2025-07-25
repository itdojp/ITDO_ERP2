import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "@/components/Layout";
import { HomePage } from "@/pages/HomePage";
import { ProductList } from "@/pages/products/ProductList";
import { ProductDetail } from "@/pages/products/ProductDetail";
import { ProductForm } from "@/pages/products/ProductForm";
import { InventoryOverview } from "@/pages/inventory/InventoryOverview";
import { InventoryList } from "@/pages/inventory/InventoryList";
import { StockAdjustmentForm } from "@/pages/inventory/StockAdjustmentForm";
import { StockMovements } from "@/pages/inventory/StockMovements";
import "./App.css";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/products" element={<ProductList />} />
            <Route path="/products/new" element={<ProductForm />} />
            <Route path="/products/:productId" element={<ProductDetail />} />
            <Route path="/products/:productId/edit" element={<ProductForm />} />
            <Route path="/inventory" element={<InventoryOverview />} />
            <Route path="/inventory/list" element={<InventoryList />} />
            <Route path="/inventory/adjust" element={<StockAdjustmentForm />} />
            <Route path="/inventory/movements" element={<StockMovements />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
