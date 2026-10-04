import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";
import type { Product } from "./api";

interface ChatResultsValue {
  products: Product[];
  setProducts: (products: Product[]) => void;
  clear: () => void;
}

const ChatResultsContext = createContext<ChatResultsValue | undefined>(undefined);

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [products, setProducts] = useState<Product[]>([]);

  return (
    <ChatResultsContext.Provider value={{ products, setProducts, clear: () => setProducts([]) }}>
      {children}
    </ChatResultsContext.Provider>
  );
}

export function useChatResults() {
  const ctx = useContext(ChatResultsContext);
  if (!ctx) throw new Error("useChatResults must be used within a ChatResultsProvider");
  return ctx;
}
