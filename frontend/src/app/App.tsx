import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "@/features/auth/AuthProvider";
import { RealtimeProvider } from "@/features/realtime/RealtimeProvider";
import { AppRouter } from "@/routes/AppRouter";

function App() {
  return (
    <AuthProvider>
      <RealtimeProvider>
        <BrowserRouter>
          <AppRouter />
        </BrowserRouter>
      </RealtimeProvider>
    </AuthProvider>
  );
}

export default App;
