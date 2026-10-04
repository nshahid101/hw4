import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./AuthContext";
import { ChatResultsProvider } from "./ChatResultsContext";
import NavBar from "./components/NavBar";
import ChatWidget from "./components/ChatWidget";
import ChatResultsPanel from "./components/ChatResultsPanel";
import Home from "./pages/Home";
import Products from "./pages/Products";
import ProductDetail from "./pages/ProductDetail";
import About from "./pages/About";
import Login from "./pages/Login";
import CreateAccount from "./pages/CreateAccount";

function App() {
  return (
    <AuthProvider>
      <ChatResultsProvider>
        <BrowserRouter>
          <NavBar />
          <ChatResultsPanel />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<Products />} />
              <Route path="/products/:productId" element={<ProductDetail />} />
              <Route path="/about" element={<About />} />
              <Route path="/login" element={<Login />} />
              <Route path="/create-account" element={<CreateAccount />} />
            </Routes>
          </main>
          <ChatWidget />
        </BrowserRouter>
      </ChatResultsProvider>
    </AuthProvider>
  );
}

export default App;
