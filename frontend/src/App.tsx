import './App.css'
import { ChatContainer } from './components/ChatContainer'

function App() {
  return (
    <div className="app-container">
      <header>
        <h1>AI Chat Interface</h1>
      </header>
      <main>
        <ChatContainer />
      </main>
    </div>
  )
}

export default App
