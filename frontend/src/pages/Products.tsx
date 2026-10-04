import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { fetchProducts } from "../api";
import type { Product } from "../api";
import { CATEGORY_ORDER, categorize } from "../categories";
import ProductCard from "../components/ProductCard";
import "./Products.css";

export default function Products() {
  const location = useLocation();
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState(() => {
    const requested = new URLSearchParams(location.search).get("category");
    return requested && CATEGORY_ORDER.includes(requested) ? requested : "All";
  });

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("Couldn't load the catalogue right now."));
  }, []);

  const categories = useMemo(() => {
    const present = new Set(products.map((p) => categorize(p.garment_type)));
    return ["All", ...CATEGORY_ORDER.filter((c) => present.has(c))];
  }, [products]);

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return products.filter((p) => {
      const matchesCategory = category === "All" || categorize(p.garment_type) === category;
      const matchesSearch =
        !needle ||
        p.name.toLowerCase().includes(needle) ||
        p.description.toLowerCase().includes(needle) ||
        p.search_tags.some((tag) => tag.toLowerCase().includes(needle));
      return matchesCategory && matchesSearch;
    });
  }, [products, search, category]);

  return (
    <div className="products-page">
      <h1>Shop All Products</h1>
      {error && <p>{error}</p>}

      <div className="products-toolbar">
        <input
          type="text"
          className="products-search"
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="products-filter"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <p className="products-count">
        {filtered.length} of {products.length} products
      </p>

      {filtered.length === 0 && products.length > 0 ? (
        <p className="products-empty">No products match your search.</p>
      ) : (
        <div className="product-grid">
          {filtered.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      )}
    </div>
  );
}
