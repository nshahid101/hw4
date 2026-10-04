import { useNavigate } from "react-router-dom";
import type { Product } from "../api";
import { API_BASE } from "../api";
import "./ProductCard.css";

const LOW_STOCK_THRESHOLD = 15;

export default function ProductCard({ product }: { product: Product }) {
  const navigate = useNavigate();

  const badge =
    product.total_stock === 0
      ? "Out of Stock"
      : product.total_stock <= LOW_STOCK_THRESHOLD
        ? `Only ${product.total_stock} left`
        : null;

  return (
    <article
      className="product-card"
      onClick={() => navigate(`/products/${product.product_id}`)}
    >
      <div className="product-card-image">
        <img src={`${API_BASE}${product.image_url}`} alt={product.name} loading="lazy" />
        {badge && (
          <span className={`product-card-badge${product.total_stock === 0 ? " sold-out" : ""}`}>
            {badge}
          </span>
        )}
      </div>
      <div className="product-card-body">
        <h3>{product.name}</h3>
        <p className="product-card-desc">{product.description}</p>
        <p className="product-card-price">${product.price.toFixed(2)}</p>
      </div>
    </article>
  );
}
