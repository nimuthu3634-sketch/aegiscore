import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "@/features/auth/AuthProvider";
import { AppRouter } from "@/routes/AppRouter";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
