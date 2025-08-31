import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import SetupScreen from "./pages/SetupScreen";
import SessionScreen from "./pages/SessionScreen";
import ResultsScreen from "./pages/ResultsScreen";

const App = () => (
  <TooltipProvider>
    <Sonner />
    <Routes>
      <Route path="/" element={<SetupScreen />} />
      <Route path="/session" element={<SessionScreen />} />
      <Route path="/results" element={<ResultsScreen />} />
      {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  </TooltipProvider>
);

export default App;
