import ReactDOM from 'react-dom/client';
import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { useLocation } from 'react-router-dom';
import Register from './component/register';
import Login from './component/login';
import ImageGenerator from './component/imageGenerator';

class App extends React.Component {
    render() {
      return (
        <BrowserRouter>
          <div>
            <ul>
              <li>
                {' '}
                <Link to="/register">Register</Link>{' '}
              </li>
              <li>
                {' '}
                <Link to="/login">Login</Link>{' '}
              </li>
              <li>
                {' '}
                <Link to="/imageGenerator">Image Generator</Link>{' '}
              </li>
            </ul>
          </div>
  
          <hr />
  
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/imageGenerator" element={<ImageGenerator />}/>
            <Route path="*" element={<NoMatch />} />
          </Routes>
        </BrowserRouter>
      );
    }
  }

  function NoMatch() {
    let location = useLocation();
    return (
      <div>
        <h3>
          No Match for <code>{location.pathname}</code>
        </h3>
      </div>
    );
  }

  const root = ReactDOM.createRoot(document.getElementById('app'));
  root.render(<App />);