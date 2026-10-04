import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useLocation } from "react-router-dom";
import { fetchChatHistory, sendChatMessage } from "../api";
import type { PageContext } from "../api";
import { useAuth } from "../AuthContext";
import { useChatResults } from "../ChatResultsContext";
import "./ChatWidget.css";

interface ChatEntry {
  role: "user" | "assistant";
  content: string;
}

const GREETING: ChatEntry = { role: "assistant", content: "Hi! Ask me about Campus Customs products." };

/** What page/product the customer is on, sent with every chat message so the
 * agent can resolve "do you have this in pink?" on a product detail page. */
function usePageContext(): PageContext {
  const location = useLocation();
  const path = location.pathname;

  if (path.startsWith("/products/")) {
    const productId = path.slice("/products/".length).split("/")[0];
    if (productId) return { page: "product_detail", product_id: productId };
  }
  if (path === "/products") return { page: "products" };
  if (path === "/about") return { page: "about" };
  if (path === "/login") return { page: "login" };
  if (path === "/create-account") return { page: "create_account" };
  return { page: "home" };
}

export default function ChatWidget() {
  const { user } = useAuth();
  const { setProducts } = useChatResults();
  const pageContext = usePageContext();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatEntry[]>([GREETING]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  // Reload a logged-in customer's saved conversation whenever who's logged
  // in changes (login, logout, or switching accounts) — guests always just
  // get the plain greeting, since their chats are never saved.
  useEffect(() => {
    if (!user) {
      setMessages([GREETING]);
      return;
    }
    fetchChatHistory(user.id)
      .then((history) => {
        if (history.length > 0) {
          setMessages(history.map((h) => ({ role: h.role, content: h.content })));
        } else {
          setMessages([
            { role: "assistant", content: `Hi ${user.first_name ?? user.name}! Ask me about Campus Customs products.` },
          ]);
        }
      })
      .catch(() => setMessages([GREETING]));
  }, [user]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setSending(true);

    try {
      const response = await sendChatMessage(text, { userId: user?.id, page: pageContext });
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
      if (response.products && response.products.length > 0) {
        setProducts(response.products);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't reach the assistant just now." },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <span>Ask the Bulldog</span>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              &times;
            </button>
          </div>
          <div className="chat-panel-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble chat-bubble-${m.role}`}>
                {m.role === "assistant" ? (
                  <ReactMarkdown>{m.content}</ReactMarkdown>
                ) : (
                  m.content
                )}
              </div>
            ))}
            {sending && <div className="chat-bubble chat-bubble-assistant">...</div>}
          </div>
          <div className="chat-panel-input">
            <input
              type="text"
              value={input}
              placeholder="Type a message..."
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />
            <button onClick={handleSend} disabled={sending}>
              Send
            </button>
          </div>
        </div>
      )}
      <button className="chat-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Close" : "Ask the Bulldog"}
      </button>
    </div>
  );
}
