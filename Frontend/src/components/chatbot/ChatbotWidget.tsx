import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, Send, Bot, User, Loader2, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '../ui/button';
import { ChatService } from '../../services/chatService';
import { useAuth } from '../../contexts/AuthContext';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
  isError?: boolean;
};

export default function ChatbotWidget() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial_1",
      role: 'assistant',
      content: "Hi there! I'm the Clarimo AI assistant. I can guide you through our startup acceleration tools, modules, and platform strategy. How can I help you build your startup today?",
      isStreaming: false
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    const text = inputValue.trim();
    if (!text || isTyping) return;

    setInputValue("");
    
    const newMessage: Message = { id: Date.now().toString(), role: 'user', content: text };
    setMessages(prev => [...prev, newMessage]);
    
    setIsTyping(true);
    
    const assistantMessageId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: assistantMessageId, role: 'assistant', content: '', isStreaming: true }]);

    const historyPayload = [
      ...messages.filter(m => !m.isError && m.content),
      newMessage
    ].map(m => ({ role: m.role, content: m.content }));

    try {
      await ChatService.streamResponse(historyPayload, (chunk: string) => {
        setIsTyping(false);
        setMessages(prev => 
          prev.map(msg => 
            msg.id === assistantMessageId 
              ? { ...msg, content: msg.content + chunk } 
              : msg
          )
        );
      });
      
      setMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, isStreaming: false } 
            : msg
        )
      );
    } catch (error) {
      setIsTyping(false);
      setMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? { 
                ...msg, 
                content: "Oops! Our AI services are temporarily unavailable or a network error occurred. Please try again later.", 
                isStreaming: false, 
                isError: true 
              } 
            : msg
        )
      );
    }
  };

  if (!user) return null;

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="fixed bottom-24 right-6 sm:right-8 z-50 w-[350px] sm:w-[400px] h-[550px] max-h-[80vh] flex flex-col rounded-3xl border border-white/10 glass bg-[#0a0a0f]/90 backdrop-blur-2xl shadow-[0_0_50px_-12px_hsl(var(--primary)_/_0.4)] overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-gradient-to-r from-primary/10 to-transparent">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center glow-sm">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="text-[15px] font-bold text-white tracking-tight leading-tight">Clarimo Assistant</h3>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Online</span>
                  </div>
                </div>
              </div>
              <button 
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/10 text-muted-foreground hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-4 py-5 space-y-5 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
              {messages.map((msg) => (
                <div 
                  key={msg.id} 
                  className={`flex items-start gap-3 max-w-[90%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
                >
                  <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-white/10 border border-white/10' : 'bg-primary/20 border border-primary/30 text-primary'}`}>
                    {msg.role === 'user' ? <User className="w-3.5 h-3.5 text-white/70" /> : <Bot className="w-4 h-4" />}
                  </div>
                  
                  <div className={`p-3.5 rounded-2xl text-[14px] leading-relaxed shadow-sm flex flex-col gap-2 ${
                    msg.role === 'user' 
                      ? 'bg-gradient-to-br from-white/10 to-white/5 border border-white/10 text-white rounded-tr-sm' 
                      : msg.isError
                        ? 'bg-destructive/10 border border-destructive/20 text-destructive-foreground rounded-tl-sm'
                        : 'bg-[#14141a] border border-white/5 text-gray-200 rounded-tl-sm'
                  }`}>
                    {msg.isError && <AlertCircle className="w-4 h-4 text-destructive mb-1" />}
                    <div className={`markdown-content ${msg.isStreaming ? 'opacity-90' : ''}`}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                      {msg.isStreaming && <span className="inline-block w-1.5 h-4 ml-1 bg-primary align-middle animate-pulse rounded-sm" />}
                    </div>
                  </div>
                </div>
              ))}

              {/* Loading State */}
              {isTyping && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 max-w-[80%]"
                >
                  <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/20 border border-primary/30 text-primary flex items-center justify-center">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="p-3.5 rounded-2xl rounded-tl-sm bg-[#14141a] border border-white/5 flex items-center gap-1.5">
                    <Loader2 className="w-4 h-4 text-primary animate-spin" />
                    <span className="text-[13px] text-muted-foreground font-medium text-nowrap">Clarimo is thinking...</span>
                  </div>
                </motion.div>
              )}
              
              <div ref={bottomRef} className="h-2" />
            </div>

            {/* Input Form */}
            <div className="p-4 border-t border-white/5 bg-black/20">
              <form 
                onSubmit={handleSendMessage}
                className="flex items-center gap-2 bg-[#14141a] border border-white/10 rounded-full p-1 pl-4 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/50 transition-all shadow-inner"
              >
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask anything about Clarimo..."
                  disabled={isTyping}
                  className="flex-1 bg-transparent border-none focus:outline-none text-[14px] text-white placeholder:text-muted-foreground/50 py-2 disabled:opacity-50"
                  autoComplete="off"
                />
                <Button 
                  type="submit" 
                  size="icon" 
                  disabled={!inputValue.trim() || isTyping}
                  className="w-10 h-10 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-50 transition-transform active:scale-95 shrink-0 shadow-md"
                >
                  <Send className="w-4 h-4 ml-0.5" />
                </Button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div 
        initial={{ opacity: 0, scale: 0.5 }} 
        animate={{ opacity: 1, scale: 1 }} 
        transition={{ delay: 0.5, type: 'spring', bounce: 0.5 }}
        className="fixed bottom-6 xl:bottom-8 right-6 xl:right-8 z-50"
      >
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="relative group w-14 h-14 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-white shadow-[0_0_30px_-5px_hsl(var(--primary)_/_0.6)] hover:shadow-[0_0_40px_-5px_hsl(var(--primary)_/_0.8)] transition-all hover:scale-105 active:scale-95 border border-white/20"
        >
          <AnimatePresence mode="wait">
            {isOpen ? (
              <motion.div key="close" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.2 }}>
                <X className="w-6 h-6" />
              </motion.div>
            ) : (
              <motion.div key="chat" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.2 }}>
                <MessageSquare className="w-6 h-6" fill="currentColor" fillOpacity={0.2} />
              </motion.div>
            )}
          </AnimatePresence>
          
          {!isOpen && (
            <span className="absolute top-0 right-0 flex w-3.5 h-3.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full w-3.5 h-3.5 bg-red-500 border-2 border-background"></span>
            </span>
          )}
        </button>
      </motion.div>
    </>
  );
}
