import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchProduct, fetchProducts, API_BASE } from "../api";
import type { Product, SizeStock } from "../api";
import ProductCard from "../components/ProductCard";
import "./ProductDetail.css";

const SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"];
const RELATED_COUNT = 4;

function sortSizes(sizes: SizeStock[]): SizeStock[] {
  return [...sizes].sort((a, b) => SIZE_ORDER.indexOf(a.size) - SIZE_ORDER.indexOf(b.size));
}

/** Real, data-backed "you might also like" picks — same garment type first,
 * then topped up with products sharing a search tag, never anything invented. */
function findRelated(current: Product, all: Product[]): Product[] {
  const others = all.filter((p) => p.product_id !== current.product_id);

  const sameType = others.filter((p) => p.garment_type === current.garment_type);

  const tagOverlap = others.filter(
    (p) =>
      !sameType.includes(p) &&
      p.search_tags.some((tag) => current.search_tags.includes(tag))
  );

  return [...sameType, ...tagOverlap].slice(0, RELATED_COUNT);
}

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    fetchProduct(productId)
      .then((p) => {
        setProduct(p);
        const firstInStock = sortSizes(p.inventory).find((s) => s.quantity > 0);
        setSelectedSize(firstInStock ? firstInStock.size : null);
      })
      .catch(() => setError("Couldn't find that product."));
    fetchProducts()
      .then(setAllProducts)
      .catch(() => {
        /* related products are a nice-to-have; fail silently */
      });
  }, [productId]);

  if (error) {
    return (
      <div className="product-detail-page">
        <p>{error}</p>
        <Link to="/products">Back to Products</Link>
      </div>
    );
  }

  if (!product) {
    return <div className="product-detail-page">Loading...</div>;
  }

  const sizes = sortSizes(product.inventory);
  const selected = sizes.find((s) => s.size === selectedSize) ?? null;
  const related = findRelated(product, allProducts);

  return (
    <div className="product-detail-page">
      <Link to="/products" className="back-link">
        &larr; Back to Products
      </Link>
      <div className="product-detail">
        <div className="product-detail-image">
          <img src={`${API_BASE}${product.image_url}`} alt={product.name} />
        </div>
        <div className="product-detail-info">
          <h1>{product.name}</h1>
          <p className="product-detail-price">${product.price.toFixed(2)}</p>
          <p className="product-detail-type">{product.garment_type}</p>
          <p className="product-detail-desc">{product.description}</p>

          <h3>Colors</h3>
          <p>{product.colors.join(", ")}</p>

          <h3>Select a Size</h3>
          <div className="size-picker">
            {sizes.map((s) => {
              const outOfStock = s.quantity === 0;
              const isSelected = s.size === selectedSize;
              return (
                <button
                  key={s.size}
                  type="button"
                  className={`size-swatch${isSelected ? " selected" : ""}${outOfStock ? " out-of-stock" : ""}`}
                  disabled={outOfStock}
                  title={outOfStock ? `${s.size} — out of stock` : `${s.size} — ${s.quantity} in stock`}
                  onClick={() => setSelectedSize(s.size)}
                >
                  {s.size}
                </button>
              );
            })}
          </div>
          <p className="size-status">
            {selected == null
              ? "Select a size to check stock."
              : selected.quantity === 0
                ? `${selected.size} is out of stock.`
                : selected.quantity <= 5
                  ? `Only ${selected.quantity} left in ${selected.size}.`
                  : `${selected.quantity} in stock in ${selected.size}.`}
          </p>
        </div>
      </div>

      {related.length > 0 && (
        <section className="related-section">
          <h2>You Might Also Like</h2>
          <div className="related-grid">
            {related.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
