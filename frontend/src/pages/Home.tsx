import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProducts } from "../api";
import type { Product } from "../api";
import { CATEGORY_ORDER, categorize } from "../categories";
import ProductCard from "../components/ProductCard";
import LocationMap from "../components/LocationMap";
import "./Home.css";

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("Couldn't load products from the shop right now."));
  }, []);

  const snapshot = products.slice(0, 4);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const p of products) {
      const c = categorize(p.garment_type);
      counts[c] = (counts[c] ?? 0) + 1;
    }
    return CATEGORY_ORDER.filter((c) => c !== "Other" && counts[c] > 0).map((c) => ({
      name: c,
      count: counts[c],
    }));
  }, [products]);

  return (
    <div className="home">
      <section className="hero">
        <h1>Casual comfort, classic Bulldog pride.</h1>
        <p className="hero-sub">
          Custom apparel and accessories for the Yale community, made right here in New Haven.
        </p>
      </section>

      <section className="home-section category-section">
        <h2>Shop by Category</h2>
        <div className="category-grid">
          {categoryCounts.map((c) => (
            <Link
              key={c.name}
              to={`/products?category=${encodeURIComponent(c.name)}`}
              className="category-tile"
            >
              <span className="category-tile-name">{c.name}</span>
              <span className="category-tile-count">{c.count} items</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="home-section">
        <h2>Shop the Collection</h2>
        {error && <p>{error}</p>}
        <div className="product-grid">
          {snapshot.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-text">
          <h2>Come Visit Us</h2>
          <p>57 Broadway, New Haven, Connecticut</p>
        </div>
        <div className="cta-map">
          <LocationMap />
        </div>
      </section>
    </div>
  );
}
