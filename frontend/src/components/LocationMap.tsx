import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./LocationMap.css";

// 57 Broadway, New Haven, CT
const SHOP_LOCATION: [number, number] = [41.3111, -72.9317];

export default function LocationMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: SHOP_LOCATION,
      zoom: 16,
      scrollWheelZoom: false,
    });
    mapRef.current = map;

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 19,
    }).addTo(map);

    L.marker(SHOP_LOCATION)
      .addTo(map)
      .bindPopup("Campus Customs<br/>57 Broadway, New Haven, CT");

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  return <div className="location-map" ref={containerRef} />;
}
