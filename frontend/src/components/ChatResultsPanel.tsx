import { useChatResults } from "../ChatResultsContext";
import ProductCard from "./ProductCard";
import "./ChatResultsPanel.css";

/**
 * Shows whatever products the chat assistant's search_products/get_product_info
 * tools most recently matched, as real product cards on the page itself (not
 * just inside the chat bubble) — the same ProductCard used everywhere else,
 * so clicking one opens the normal single-item detail page.
 */
export default function ChatResultsPanel() {
  const { products, clear } = useChatResults();

  if (products.length === 0) return null;

  return (
    <section className="chat-results-panel">
      <div className="chat-results-header">
        <h2>From your chat</h2>
        <button className="chat-results-clear" onClick={clear}>
          Clear
        </button>
      </div>
      <div className="chat-results-grid">
        {products.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
    </section>
  );
}
