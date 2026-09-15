import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Article from "./pages/Article";
import Categories from "./pages/Categories";
import History from "./pages/History";
import Home from "./pages/Home";
import Latest from "./pages/Latest";
import Preferences from "./pages/Preferences";
import Saved from "./pages/Saved";
import Search from "./pages/Search";
import Trending from "./pages/Trending";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="latest" element={<Latest />} />
        <Route path="trending" element={<Trending />} />
        <Route path="categories" element={<Categories />} />
        <Route path="search" element={<Search />} />
        <Route path="saved" element={<Saved />} />
        <Route path="history" element={<History />} />
        <Route path="preferences" element={<Preferences />} />
        <Route path="articles/:id" element={<Article />} />
      </Route>
    </Routes>
  );
}
